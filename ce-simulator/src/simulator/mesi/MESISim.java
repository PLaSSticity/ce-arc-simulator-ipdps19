package simulator.mesi;

import java.io.BufferedInputStream;
import java.io.BufferedWriter;
import java.io.DataInputStream;
import java.io.EOFException;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.io.IOException;
import java.io.StringWriter;
import java.text.DecimalFormat;

import joptsimple.OptionSet;
import simulator.mesi.Machine.SimulationMode;

public class MESISim {

	/** enable checking of computationally expensive asserts */
	public static boolean XASSERTS = true;

	public static final ThreadId INVALID_THREADID = new ThreadId(-1);

	public enum PARSEC_PHASE {
		PRE_ROI, IN_ROI, POST_ROI
	}

	private static PARSEC_PHASE phase = PARSEC_PHASE.PRE_ROI;

	static OptionSet Options;

	private static int maxLiveThreads;
	private static int numSpawnedThreads;
	private static int currentLiveThreads;
	private static long insnsExecuted;
	private static long stackAccesses;

	static long totalEvents = 1;
	private static long basicBlockEvents;

	public static double totalScavengeTime = 0;

	public static final long debugStart = 626000000;
	public static final long debugCurrent = 626057257;
	public static final long debugByteAddress = 22582336L;
	public static final long debugLineAddress = 140637238945664L;

	public static boolean debugPrint() {
		return totalEvents == debugCurrent;
	}

	// http://docs.oracle.com/javase/7/docs/technotes/guides/language/assert.html
	static boolean assertsEnabled = false;

	static {
		assert assertsEnabled = true; // Intentional side effect!!!
	}

	// These checks are expensive
	public static boolean enableXasserts() {
		if (XASSERTS) {
			if ((totalEvents % Options.valueOf(Knobs.AssertPeriod) == 0)
			// && totalEvents > debugStart
			) {
				return true;
			}
		}
		return false;
	}

	public static boolean modelOnlyROI() {
		return Options.valueOf(Knobs.modelOnlyROI);
	}

	public static void setPhase(PARSEC_PHASE p) {
		phase = p;
	}

	public static PARSEC_PHASE getPARSECPhase() {
		return phase;
	}

	public static int numProcessors() {
		return Options.valueOf(Knobs.Cores);
	}

	public static void main(String[] args) throws IOException {
		Options = Knobs.parser.parse(args);
		if (Options.has(Knobs.Help)) {
			Knobs.parser.printHelpOn(System.out);
			return;
		}
		XASSERTS = Options.valueOf(Knobs.Xasserts);

		final SimulationMode simMode;
		if (Options.valueOf(Knobs.SimulationMode).equals("baseline")) {
			simMode = SimulationMode.BASELINE;
		} else if (Options.valueOf(Knobs.SimulationMode).equals("viser")) {
			throw new UnsupportedOperationException("Viser mode not implemented.");
		} else {
			throw new IllegalStateException(
					"Invalid simulation mode: " + Options.valueOf(Knobs.SimulationMode));
		}

		DataInputStream in;
		try {
			FileInputStream fis = new FileInputStream(Options.valueOf(Knobs.ToSimulatorFifo));
			in = new DataInputStream(new BufferedInputStream(fis));
		} catch (FileNotFoundException fnf) {
			fnf.printStackTrace();
			return;
		}

		final long startTime = System.currentTimeMillis();
		SystemConstants.setLineSize(Options.valueOf(Knobs.LineSize));
		SystemConstants.setLLCAccessTimes(numProcessors());

		Machine.MachineParams<MESILine> p = new Machine.MachineParams<MESILine>() {
			SimulationMode simulationMode() {
				return simMode;
			}

			@Override
			int numProcessors() {
				return Options.valueOf(Knobs.Cores);
			}

			@Override
			int numPinThreads() {
				return Options.valueOf(Knobs.PinThreads);
			}

			@Override
			boolean pintool() {
				return Options.valueOf(Knobs.Pintool);
			}

			CacheConfiguration<MESILine> l1config() {
				// NB: be lazy and return a new object each time; shouldn't affect anything since
				// the
				// values are always the same
				return new CacheConfiguration<MESILine>() {
					{
						cacheSize = Options.valueOf(Knobs.L1Size);
						lineSize = SystemConstants.LINE_SIZE();
						assoc = Options.valueOf(Knobs.L1Assoc);
						level = CacheLevel.L1;
					}
				};
			}

			boolean useL2() {
				return Options.valueOf(Knobs.UseL2);
			}

			CacheConfiguration<MESILine> l2config() {
				return new CacheConfiguration<MESILine>() {
					{
						cacheSize = Options.valueOf(Knobs.L2Size);
						lineSize = SystemConstants.LINE_SIZE();
						assoc = Options.valueOf(Knobs.L2Assoc);
						level = CacheLevel.L2;
					}
				};
			}

			CacheConfiguration<MESILine> l3config() {
				return new CacheConfiguration<MESILine>() {
					{
						cacheSize = Options.valueOf(Knobs.L3Size);
						lineSize = SystemConstants.LINE_SIZE();
						assoc = Options.valueOf(Knobs.L3Assoc);
						level = CacheLevel.L3;
					}
				};
			}

			LineFactory<MESILine> lineFactory() {
				return new LineFactory<MESILine>() {
					@Override
					public MESILine create(CpuId id, CacheLevel level) {
						return new MESILine(id, level);
					}

					@Override
					public MESILine create(CpuId id, CacheLevel level, LineAddress la) {
						return new MESILine(id, level, la);
					}

					@Override
					public MESILine create(CpuId id, CacheLevel level, MESILine l) {
						assert l.valid() : "Source line should be valid.";
						MESILine tmp = new MESILine(id, level, l.lineAddress());
						tmp.changeStateTo(l.getState());
						tmp.setDirty(l.dirty());
						tmp.setLastWriters(l.getLastWriters());

						if (conflictExceptions()) {
							tmp.setLocalReads(l.getLocalReads());
							tmp.setLocalWrites(l.getLocalWrites());
							tmp.setRemoteReads(l.getRemoteReads());
							tmp.setRemoteWrites(l.getRemoteWrites());
							tmp.setAIMMD(l.hasAIMMD());
						}
						return tmp;
					}
				};
			}

			@Override
			boolean ignoreStackReferences() {
				return Options.valueOf(Knobs.IgnoreStackRefs);
			}

			@Override
			boolean remoteAccessesAffectLRU() {
				return Options.valueOf(Knobs.RemoteAccessesAffectLRU);
			}

			@Override
			boolean conflictExceptions() {
				return Options.valueOf(Knobs.ConflictExceptions);
			}

			@Override
			boolean printConflictingSites() {
				return false;
			}

			@Override
			boolean reportSites() {
				return Options.valueOf(Knobs.ReportSites);
			}

			@Override
			boolean treatAtomicUpdatesAsRegularAccesses() {
				return Options.valueOf(Knobs.TreatAtomicUpdatesAsRegularAccesses);
			}

			@Override
			boolean usePLRU() {
				return Options.valueOf(Knobs.UsePLRU);
			}

			@Override
			boolean withPacifistBackends() {
				return Options.valueOf(Knobs.WithPacifistBackends);
			}

			@Override
			boolean useAIMCache() {
				return Options.valueOf(Knobs.UseAIMCache);
			}

			@Override
			boolean clearAIMCacheAtRegionBoundaries() {
				return Options.valueOf(Knobs.ClearAIMAtRegionBoundaries);
			}
		};

		Machine<MESILine> sim = new Machine<MESILine>(p);
		if (p.conflictExceptions()) {
			sim.initializeEpochs();
		}

		System.out.println("[mesisim] starting simulation...");

		while (true) {
			try {
				Event e = getNextEvent(in, sim);
				boolean simulationFinished = handleEvent(e, sim);
				if (simulationFinished) {
					break;
				}
			} catch (EOFException eof) {
				break;
			}
		}

		in.close();

		double mins = (System.currentTimeMillis() - startTime) / (double) (1000 * 60);

		if (sim.params.withPacifistBackends()) {
			Processor<MESILine>[] processors = sim.getProcs();
			for (int i = 0; i < numProcessors(); i++) {
				if (processors[i].ignoreEvents()) {
					System.out.println("[mesisim] Non-zero depth counter with P" + i);
				}
			}
		}

		generateStats(mins, sim);

	} // end main()

	private static Event getNextEvent(DataInputStream in, Machine<MESILine> sim)
			throws IOException {
		byte type = in.readByte();
		byte semantics = in.readByte();
		byte tid = (byte) in.readShort();
		Event e = new Event(EventType.fromByte(type), EventType.fromByte(semantics), tid);
		e.addr = in.readLong();
		e.memOpSize = (byte) in.readInt();
		byte bits = in.readByte();
		e.stackRef = (bits & 0x1) == 1;
		e.value = in.readLong();
		e.insnCount = in.readInt();

		// site info
		short lineno = in.readShort();
		short fno = in.readShort();
		short rno = in.readShort();
		in.readInt(); // eventID
		in.readShort(); // lastLineno
		in.readShort(); // lastFno

		SiteInfoEntry siEntry = new SiteInfoEntry(fno, lineno, rno);
		int index = sim.siteInfo.indexOf(siEntry);
		if (index == -1) {
			sim.siteInfo.add(siEntry);
			index = sim.siteInfo.size() - 1;
		}
		e.siteIndex = index;

		boolean debug = false;
		if (debug && totalEvents >= MESISim.debugStart) {
			System.out.println(totalEvents);
			System.out.println("Event type:" + EventType.fromByte(type) /* + " Byte:" + by */);
			System.out.println("Semantics:" + EventType.fromByte(semantics));
			System.out.println("Tid:" + tid);
			System.out.println("Addr:" + e.addr);
			System.out.println("Mem op size:" + e.memOpSize);
			System.out.println("Stack ref:" + e.stackRef);
			System.out.println("Value:" + e.value);
			System.out.println("Insn count:" + e.insnCount);
			System.out.println();
		}
		return e;
	}

	/**
	 * Dispatch the given event to the simulator code.
	 *
	 * @param e
	 *              the next event from the front-end
	 * @return true when the simulation is finished, false otherwise
	 */
	private static boolean handleEvent(final Event e, Machine<MESILine> machine) {
		CpuId cpuid = machine.cpuOfTid(e.tid);

		switch (e.type) {
			case ROI_START: {
				assert phase == PARSEC_PHASE.PRE_ROI;
				phase = PARSEC_PHASE.IN_ROI;
				break;
			}

			case ROI_END: {
				assert phase == PARSEC_PHASE.IN_ROI;
				phase = PARSEC_PHASE.POST_ROI;
				break;
			}

			case MEMORY_ALLOC:
			case MEMORY_FREE:
			case THREAD_BLOCKED:
			case THREAD_UNBLOCKED: {
				assert false : "Impossible event type.";
			}

			case THREAD_JOIN:
			case THREAD_SPAWN: { // Called from the parent thread
				machine.processSyncOp(cpuid, e.tid, e.type, e.semantics);
				break;
			}

			case THREAD_START: { // Called from the child thread
				currentLiveThreads++;
				numSpawnedThreads++;
				maxLiveThreads = Math.max(maxLiveThreads, currentLiveThreads);
				machine.processSyncOp(cpuid, e.tid, e.type, e.semantics);
				break;
			}

			case THREAD_FINISH: { // Called from the child thread
				currentLiveThreads--;
				machine.processSyncOp(cpuid, e.tid, e.type, e.semantics);
				// when main thread exits, tear down simulation
				if (e.tid.get() == 0) {
					return true;
				}
				break;
			}

			case MEMORY_READ: {
				machine.cacheRead(cpuid, e.addr, e.memOpSize, e.siteIndex,
						MemoryAccessType.MEMORY_READ);
				break;
			}

			case MEMORY_WRITE: {
				machine.cacheWrite(cpuid, e.addr, e.memOpSize, e.siteIndex,
						MemoryAccessType.MEMORY_WRITE);
				break;
			}

			case BASIC_BLOCK: {
				insnsExecuted += e.insnCount;
				machine.insnsExecuted(cpuid, e.insnCount);
				basicBlockEvents++;
				break;
			}

			case LOCK_ACQUIRE:
			case LOCK_RELEASE: {
				machine.processSyncOp(cpuid, e.tid, e.type, e.semantics);
				break;
			}

			case ATOMIC_READ: {
				if (machine.params.treatAtomicUpdatesAsRegularAccesses()) {
					machine.cacheRead(cpuid, e.addr, e.memOpSize, e.siteIndex,
							MemoryAccessType.MEMORY_READ);
				} else {
					machine.cacheRead(cpuid, e.addr, e.memOpSize, e.siteIndex,
							MemoryAccessType.ATOMIC_READ);
				}
				break;
			}

			case ATOMIC_WRITE: {
				if (machine.params.treatAtomicUpdatesAsRegularAccesses()) {
					machine.cacheWrite(cpuid, e.addr, e.memOpSize, e.siteIndex,
							MemoryAccessType.MEMORY_WRITE);
				} else {
					machine.cacheWrite(cpuid, e.addr, e.memOpSize, e.siteIndex,
							MemoryAccessType.ATOMIC_WRITE);
				}
				break;
			}

			case LOCK_ACQ_READ: {
				machine.cacheRead(cpuid, e.addr, e.memOpSize, e.siteIndex,
						MemoryAccessType.LOCK_ACQ_READ);
				break;
			}

			case LOCK_ACQ_WRITE: {
				machine.cacheWrite(cpuid, e.addr, e.memOpSize, e.siteIndex,
						MemoryAccessType.LOCK_ACQ_WRITE);
				break;
			}

			case LOCK_REL_WRITE: {
				machine.cacheWrite(cpuid, e.addr, e.memOpSize, e.siteIndex,
						MemoryAccessType.LOCK_REL_WRITE);
				break;
			}

			case INVALID_EVENT: {
				System.out.println("Invalid event found: ");
				System.out.println(e);
				break;
			}

			case CHECK_POINT:
			case TRANS_START:
			case TRANS_END:
			case SERVER_ROI_START:
			case SERVER_ROI_END: {
				// Only Pacifist does experiments with server programs.
				assert (machine.params.withPacifistBackends());
				break;
			}

			default: {
				throw new RuntimeException("Impossible event type:\n" + e);
			}
		}
		totalEvents++;
		if (e.stackRef) {
			stackAccesses++;
		}
		return false; // not done processing events yet

	} // end handleEvent()

	private static void generateStats(double simRuntimeMins, Machine<MESILine> machine)
			throws IOException {
		System.out.println("[mesisim] exiting...");

		// each stat is dumped as a Python dictionary object

		StringWriter prefix = new StringWriter();
		prefix.write("{'MESIStat':True, ");
		Knobs.dumpRegisteredParams(prefix);

		String suffix = "}" + System.getProperty("line.separator");

		// Viser: Overwrite files
		String statsFilename = Options.valueOf(Knobs.StatsFile);
		File f = new File(statsFilename);
		// // check for filename collisions and rename around them
		// while (f.exists()) {
		// statsFilename += ".1";
		// f = new File(statsFilename);
		// }
		BufferedWriter statsFd = new BufferedWriter(new FileWriter(f));

		// dump stats from the caches
		machine.dumpStats(statsFd, prefix.toString(), suffix);

		DecimalFormat fmt = new DecimalFormat("0.000");

		double denom = MaxCounter.globalCounters.get("pc_ExecutionDrivenCycleCount").get();

		double value = DependentCounter.globalCounters.get("pc_MESIMemSystemExecDrivenCycleCount")
				.get() / denom;
		statsFd.write(prefix.toString() + "'ratioMESIMemSystemExecDrivenCycleCount': "
				+ fmt.format(value) + suffix);
		value = DependentCounter.globalCounters.get("pc_MESICoherenceExecDrivenCycleCount").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioMESICoherenceExecDrivenCycleCount': "
				+ fmt.format(value) + suffix);

		denom = MaxCounter.globalCounters.get("pc_BandwidthDrivenCycleCount").get();

		// dump "global" stats

		statsFd.write(prefix.toString() + "'SimulationRunningTimeMins': "
				+ String.format("%.2f", simRuntimeMins) + suffix);
		statsFd.write(prefix.toString() + "'ScavengeRunningTimeMins': "
				+ String.format("%.2f", totalScavengeTime) + suffix);

		double gigs = Runtime.getRuntime().totalMemory() / (double) (1 << 30);
		String memUsage = "'MemUsageGB': " + String.format("%.2f", gigs);
		statsFd.write(prefix.toString() + memUsage + suffix);

		statsFd.write(prefix.toString() + "'MaxLiveThreads': " + maxLiveThreads + suffix);
		statsFd.write(prefix.toString() + "'NumSpawnedThreads': " + numSpawnedThreads + suffix);
		statsFd.write(prefix.toString() + "'StackAccesses': " + stackAccesses + suffix);
		statsFd.write(prefix.toString() + "'Instructions': " + insnsExecuted + suffix);
		statsFd.write(prefix.toString() + "'TotalEvents': " + totalEvents + suffix);
		statsFd.write(prefix.toString() + "'BasicBlocks': " + basicBlockEvents + suffix);
		double totalMemAccesses = SumCounter.globalCounters.get("pc_TotalMemoryAccesses").get();
		double totalRegionBoundaries = SumCounter.globalCounters.get("pc_RegionBoundaries").get();
		double avgRegSize = totalMemAccesses / totalRegionBoundaries;
		statsFd.write(prefix.toString() + "'AverageRegionSize': " + avgRegSize + suffix);

		// Compute proportion of network messages
		fmt = new DecimalFormat("0.000");

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessages").get();

		value = SumCounter.globalCounters.get("pc_MESIMemoryOnChipNetworkMessages").get() / denom;
		statsFd.write(prefix.toString() + "'ratioMESIMemoryOnChipNetworkMessages': "
				+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters.get("pc_MESICoherenceOnChipNetworkMessages").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioMESICoherenceOnChipNetworkMessages': "
				+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSizeBytes").get();

		value = SumCounter.globalCounters.get("pc_MESIMemoryOnChipNetworkMessageSizeBytes").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioMESIMemoryOnChipNetworkMessageSizeBytes': "
				+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters.get("pc_MESICoherenceOnChipNetworkMessageSizeBytes").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioMESICoherenceOnChipNetworkMessageSizeBytes': "
				+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSize4BytesFlits").get();

		value = SumCounter.globalCounters.get("pc_MESIMemoryOnChipNetworkMessageSize4BytesFlits")
				.get() / denom;
		statsFd.write(prefix.toString() + "'ratioMESIMemoryOnChipNetworkMessageSize4BytesFlits': "
				+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters.get("pc_MESICoherenceOnChipNetworkMessageSize4BytesFlits")
				.get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioMESICoherenceOnChipNetworkMessageSize4BytesFlits': "
						+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSize8BytesFlits").get();

		value = SumCounter.globalCounters.get("pc_MESIMemoryOnChipNetworkMessageSize8BytesFlits")
				.get() / denom;
		statsFd.write(prefix.toString() + "'ratioMESIMemoryOnChipNetworkMessageSize8BytesFlits': "
				+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters.get("pc_MESICoherenceOnChipNetworkMessageSize8BytesFlits")
				.get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioMESICoherenceOnChipNetworkMessageSize8BytesFlits': "
						+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSize16BytesFlits").get();

		value = SumCounter.globalCounters.get("pc_MESIMemoryOnChipNetworkMessageSize16BytesFlits")
				.get() / denom;
		statsFd.write(prefix.toString() + "'ratioMESIMemoryOnChipNetworkMessageSize16BytesFlits': "
				+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters
				.get("pc_MESICoherenceOnChipNetworkMessageSize16BytesFlits").get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioMESICoherenceOnChipNetworkMessageSize16BytesFlits': "
						+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSize32BytesFlits").get();

		value = SumCounter.globalCounters.get("pc_MESIMemoryOnChipNetworkMessageSize32BytesFlits")
				.get() / denom;
		statsFd.write(prefix.toString() + "'ratioMESIMemoryOnChipNetworkMessageSize32BytesFlits': "
				+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters
				.get("pc_MESICoherenceOnChipNetworkMessageSize32BytesFlits").get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioMESICoherenceOnChipNetworkMessageSize32BytesFlits': "
						+ fmt.format(value) + suffix);

		statsFd.close();

		System.err.println("[mesisim] finished");
	}
}
