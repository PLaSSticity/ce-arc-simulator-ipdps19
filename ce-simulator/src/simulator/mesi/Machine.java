package simulator.mesi;

import java.io.IOException;
import java.io.Writer;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** A class that manages the set of processors in the system. */
public class Machine<Line extends MESILine> {

	private final Processor<Line>[] processors;
	final MachineParams<Line> params;

	public enum SimulationMode {
		BASELINE, VISER
	}

	List<Conflict> conflicts = new ArrayList<>();
	List<SiteInfoEntry> siteInfo = new ArrayList<SiteInfoEntry>();

	/** Simulates CE's global table in main memory. */
	HashMap<Long, CEPerLineMetadata<Line>> globalTable = new HashMap<>();

	/**
	 * Machine-wide epoch. This is per-core and not per-thread. We can just maintain an array of
	 * integers.
	 */
	private Epoch[] epochMap = null;

	/**
	 * Arguments to the Machine ctor. We encode these values as abstract methods so that we can't
	 * forget to initialize one of them. The values get initialized by creating an anonymous
	 * subclass that is forced to override all these methods.
	 */
	static abstract class MachineParams<Line extends MESILine> {
		/** Whether to simulate the Radish processor extensions or not */
		abstract SimulationMode simulationMode();

		/** The number of processors to simulate */
		abstract int numProcessors();

		abstract int numPinThreads();

		abstract boolean pintool();

		/** The cache geometry for the private L1 caches */
		abstract CacheConfiguration<Line> l1config();

		/** Whether to simulate private L2s or not */
		abstract boolean useL2();

		/** The cache geometry for the private L2 caches */
		abstract CacheConfiguration<Line> l2config();

		/** The cache geometry for the shared L3 cache */
		abstract CacheConfiguration<Line> l3config();

		abstract LineFactory<Line> lineFactory();

		abstract boolean ignoreStackReferences();

		abstract boolean remoteAccessesAffectLRU();

		abstract boolean conflictExceptions();

		/** Whether to report sites involved in a conflict detected */
		abstract boolean reportSites();

		abstract boolean printConflictingSites();

		abstract boolean treatAtomicUpdatesAsRegularAccesses();

		abstract boolean usePLRU();

		abstract boolean withPacifistBackends();

		abstract boolean useAIMCache();

		abstract boolean clearAIMCacheAtRegionBoundaries();
	}

	@SuppressWarnings("unchecked")
	public Machine(MachineParams<Line> args) {
		this.params = args;
		Map<LineAddress, Integer> varmap = new HashMap<LineAddress, Integer>();

		if (params.conflictExceptions()) {
			createEpochs(params.numProcessors());
		}

		// construct processors
		processors = new Processor[args.numProcessors()];
		for (int i = 0; i < processors.length; i++) {
			CpuId cpuid = new CpuId(i);
			/* HACK: see Counter.currentCpu for details */
			Counter.currentCpu = cpuid;
			processors[i] = new Processor<Line>(args, this, cpuid, processors, varmap);
		}
		Counter.currentCpu = null;
	}

	/** map from thread id to cpu id */
	public CpuId cpuOfTid(ThreadId tid) {
		// NB: we have a very simple mapping of threads onto caches
		// Take care of the IO thread in Pintool
		if (params.pintool() && tid.get() == 1) {
			throw new RuntimeException("Tid 1 is not expected");
		}
		int pid = (tid.get() > 1) ? tid.get() - 1 : 0;
		return processors[pid % processors.length].id;
	}

	Processor<Line> getProc(CpuId cpuid) {
		Processor<Line> p = processors[cpuid.get()];
		assert p != null;
		return p;
	}

	public void dumpStats(Writer wr, String prefix, String suffix) throws IOException {
		for (Processor<Line> p : processors) {
			p.preFinalizeCounters();
		}

		// the Counter class keeps track of all its instances, so we only need to dump once
		SumCounter.dumpCounters(wr, prefix, suffix);
		MaxCounter.dumpCounters(wr, prefix, suffix);
		DependentCounter.dumpCounters(wr, prefix, suffix);
	}

	public Processor<Line>[] getProcs() {
		return processors;
	}

	public void insnsExecuted(final CpuId cpuid, int n) {
		getProc(cpuid).insnsExecuted(n);
	}

	public void cacheRead(final CpuId cpuid, final long addr, final int size, int siteIndex,
			MemoryAccessType type) {
		cacheAccess(cpuid, false, addr, size, siteIndex, type, true);
	}

	public void testCacheMemoryRead(final CpuId cpuid, final long addr, final int size) {
		cacheAccess(cpuid, false, addr, size, 0, MemoryAccessType.MEMORY_READ, true);
	}

	public void cacheWrite(final CpuId cpuid, final long addr, final int size, int siteIndex,
			MemoryAccessType type) {
		cacheAccess(cpuid, true, addr, size, siteIndex, type, true);
	}

	public void testCacheMemoryWrite(final CpuId cpuid, final long addr, final int size) {
		cacheAccess(cpuid, true, addr, size, 0, MemoryAccessType.MEMORY_WRITE, true);
	}

	public void cacheAccess(final CpuId cpuid, final boolean write, final long addr, final int size,
			int siteIndex, MemoryAccessType type, boolean doMetadataAccess) {
		Processor<Line> proc = getProc(cpuid);

		// We ignore events in the Pacifist simulators, so to be fair, we also do so in the MESI
		// simulator.
		if (params.withPacifistBackends() && (type != MemoryAccessType.LOCK_ACQ_READ
				&& type != MemoryAccessType.LOCK_ACQ_WRITE) && proc.ignoreEvents()) {
			// System.out.println("Access ignored: type " + type + ", core " + cpuid + ", addr " +
			// addr + ", size " + size + ", value " + value);
			return;
		}

		switch (params.simulationMode()) {
			case BASELINE: {
				break;
			}
			case VISER: {
				throw new UnsupportedOperationException("Not yet implemented.");
			}
			default:
				assert false;
		}

		Processor.DataMemoryAccessResult mopResult = new Processor.DataMemoryAccessResult();
		mopResult.remoteCommunicatedHappened = false;
		int remainingSize = size;

		if (type == MemoryAccessType.LOCK_ACQ_READ || type == MemoryAccessType.LOCK_ACQ_WRITE
				|| type == MemoryAccessType.LOCK_REL_WRITE) {
			// Assume a one-word access for each lock operation
			remainingSize = 2;
		}

		for (long a = addr; remainingSize > 0;) {
			DataByteAddress dba = new DataByteAddress(a);
			int data_bytesFromStartOfLine = dba.lineOffset();
			int data_maxSizeAccessWithinThisLine = SystemConstants.LINE_SIZE()
					- data_bytesFromStartOfLine;

			// data access
			int accessSize = Math.min(remainingSize, data_maxSizeAccessWithinThisLine);
			Processor.DataMemoryAccessResult tempMor;
			if (write) {
				tempMor = proc.write(new DataAccess(type, dba, accessSize, siteIndex));
			} else {
				tempMor = proc.read(new DataAccess(type, dba, accessSize, siteIndex));
			}
			mopResult.aggregate(tempMor);

			a += accessSize;
			remainingSize -= accessSize;
		}
	}

	public void processSyncOp(final CpuId performingCpu, ThreadId tid, EventType type,
			EventType semantics) {
		Processor<Line> performingProc = getProc(performingCpu);
		performingProc.processSyncOp(tid);

		// We now split up region boundary events into multiple constituent events.
		if ((type == EventType.LOCK_ACQUIRE && semantics == EventType.REG_END)
				|| (type == EventType.LOCK_RELEASE && semantics == EventType.REG_END)
				|| (type == EventType.THREAD_START) || (type == EventType.THREAD_FINISH)
				|| (type == EventType.THREAD_SPAWN && semantics == EventType.REG_END)
				|| (type == EventType.THREAD_JOIN && semantics == EventType.REG_END)) {
			performingProc.stats.pc_RegionBoundaries.incr();
		}

		// We ignore events in the Pacifist simulators, so to be fair, we also do so in the MESI
		// simulator.
		if (params.withPacifistBackends() && type == EventType.LOCK_ACQUIRE) {
			if (semantics == EventType.REG_END) {
				performingProc.incIgnoreCounter();
			} else {
				performingProc.decIgnoreCounter();
			}
		}
	}

	public void printGlobalTable() {
		for (Long l : globalTable.keySet()) {
			System.out.println("Line address: " + l);
		}
	}

	public void printEpochMap() {
		System.out.println("Printing epoch map:");
		for (int i = 0; i < epochMap.length; i++) {
			Epoch tmp = epochMap[i];
			System.out.println("Core/thread id:" + i + " Region id:" + tmp.getRegionId());
		}
	}

	public void createEpochs(int numProcs) {
		epochMap = new Epoch[numProcs];
		for (int i = 0; i < numProcs; i++) {
			epochMap[i] = new Epoch(0);
		}
	}

	public void initializeEpochs() {
		for (int i = 0; i < epochMap.length; i++) {
			epochMap[i] = new Epoch(Epoch.REGION_ID_START);
		}
	}

	/** Increment epoch for current core id (not thread) */
	public void incrementEpoch(CpuId id) {
		epochMap[id.get()].incrementRegionId();
	}

	public Epoch getEpoch(CpuId id) {
		return epochMap[id.get()];
	}

};
