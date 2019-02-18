package simulator.viser;

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
import java.util.HashMap;

import joptsimple.OptionSet;
import simulator.viser.Machine.SimulationMode;

public class ViserSim {

	/** enable checking of computationally expensive asserts */
	public static boolean XASSERTS = true;

	public enum PARSEC_PHASE {
		PRE_ROI, IN_ROI, POST_ROI, IN_SERVER_ROI, POST_SERVER_ROI
	}

	private static PARSEC_PHASE phase = PARSEC_PHASE.PRE_ROI;

	static OptionSet Options;

	private static int maxLiveThreads;
	private static int numSpawnedThreads;
	private static int currentLiveThreads;
	private static long insnsExecuted;
	private static long stackAccesses;
	static long totalEvents = 0;
	private static long basicBlockEvents;
	public static double totalScavengeTime = 0;

	public static final long debugStart = 640000;
	public static final long debugCurrent = 640643;
	public static final long debugByteAddress = 139812783786240L;
	public static final long debugLineAddress = 139812783786240L;

	public static boolean debugPrint() {
		return totalEvents == debugCurrent;
	}

	// http://docs.oracle.com/javase/7/docs/technotes/guides/language/assert.html
	static boolean assertsEnabled = false;

	static {
		assert assertsEnabled = true; // Intentional side effect!!!
	}

	// These checks are expensive
	public static boolean xassertsEnabled() {
		if (XASSERTS) {
			if ((totalEvents % Options.valueOf(Knobs.AssertPeriod) == 0)
					&& totalEvents > debugStart) {
				return true;
			}
		}
		return false;
	}

	public static boolean modelOnlyROI() {
		return Options.valueOf(Knobs.modelOnlyROI);
	}

	public static void setPARSECPhase(PARSEC_PHASE p) {
		phase = p;
	}

	public static PARSEC_PHASE getPARSECPhase() {
		return phase;
	}

	public static boolean useTwoBloomFuncs() {
		return Options.valueOf(Knobs.UseTwoBloomFuncs);
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
			throw new UnsupportedOperationException("Baseline mode not supported.");
		} else if (Options.valueOf(Knobs.SimulationMode).equals("viser")) {
			simMode = SimulationMode.VISER;
		} else {
			throw new IllegalStateException(
					"Invalid simulation mode: " + Options.valueOf(Knobs.SimulationMode));
		}

		if (!BitTwiddle.isPowerOf2(numProcessors())) {
			throw new IllegalArgumentException("Number of cores is not a power of 2.");
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

		Machine.MachineParams<ViserLine> p = new Machine.MachineParams<ViserLine>() {
			@Override
			SimulationMode simulationMode() {
				return simMode;
			}

			@Override
			int numProcessors() {
				return ViserSim.numProcessors();
			}

			@Override
			int numPinThreads() {
				return Options.valueOf(Knobs.PinThreads);
			}

			@Override
			CacheConfiguration<ViserLine> l1config() {
				// NB: be lazy and return a new object each time; shouldn't
				// affect anything since the
				// values are always the same
				return new CacheConfiguration<ViserLine>() {
					{
						cacheSize = Options.valueOf(Knobs.L1Size);
						lineSize = SystemConstants.LINE_SIZE();
						assoc = Options.valueOf(Knobs.L1Assoc);
						level = CacheLevel.L1;
					}
				};
			}

			@Override
			boolean pintool() {
				return Options.valueOf(Knobs.Pintool);
			}

			@Override
			boolean useL2() {
				return Options.valueOf(Knobs.UseL2);
			}

			@Override
			CacheConfiguration<ViserLine> l2config() {
				return new CacheConfiguration<ViserLine>() {
					{
						cacheSize = Options.valueOf(Knobs.L2Size);
						lineSize = SystemConstants.LINE_SIZE();
						assoc = Options.valueOf(Knobs.L2Assoc);
						level = CacheLevel.L2;
					}
				};
			}

			@Override
			CacheConfiguration<ViserLine> l3config() {
				return new CacheConfiguration<ViserLine>() {
					{
						cacheSize = Options.valueOf(Knobs.L3Size);
						lineSize = SystemConstants.LINE_SIZE();
						assoc = Options.valueOf(Knobs.L3Assoc);
						level = CacheLevel.L3;
					}
				};
			}

			@Override
			LineFactory<ViserLine> lineFactory() {
				return new LineFactory<ViserLine>() {

					@Override
					public ViserLine create(Processor<ViserLine> proc, CacheLevel level) {
						ViserLine line = new ViserLine(proc, level);
						line.setEpoch(proc.id, proc.getCurrentEpoch());
						return line;
					}

					@Override
					public ViserLine create(Processor<ViserLine> proc, CacheLevel level,
							LineAddress la) {
						ViserLine line = new ViserLine(proc, level, la);
						line.setEpoch(proc.id, proc.getCurrentEpoch());
						return line;
					}

					@Override
					public ViserLine create(Processor<ViserLine> proc, CacheLevel level,
							ViserLine l) {
						if (!l.valid()) {
							throw new RuntimeException("Source line should be VALID.");
						}
						ViserLine tmp = new ViserLine(proc, level, l.lineAddress());
						tmp.changeStateTo(l.getState());
						tmp.setVersion(l.getVersion());
						tmp.copyAllValues(l);
						tmp.setLastWriters(l.getLastWriters());
						tmp.setLockOwnerID(l.getLockOwnerID());
						tmp.setAIMMD(l.hasAIMMD());
						// We do not update deferred owner id from here.
						if (level.compareTo(proc.llc()) < 0) { // private line
							CpuId cid = proc.id;
							tmp.orWriteEncoding(cid, l.getWriteEncoding(cid));
							tmp.orReadEncoding(cid, l.getReadEncoding(cid));
							tmp.updateWriteSiteInfo(cid, l.getWriteEncoding(cid),
									l.getWriteSiteInfo(cid), l.getWriteLastSiteInfo(cid));
							tmp.updateReadSiteInfo(cid, l.getReadEncoding(cid),
									l.getReadSiteInfo(cid), l.getReadLastSiteInfo(cid));
							tmp.setEpoch(proc.id, proc.getCurrentEpoch());
						} else {
							for (int i = 0; i < proc.params.numProcessors(); i++) {
								CpuId cpuId = new CpuId(i);
								PerCoreLineMetadata tmpMd = l.getPerCoreMetadata(cpuId);
								// We do not bother with epoch here, since it should be
								// taken care of automatically later
								PerCoreLineMetadata md = new PerCoreLineMetadata(tmpMd.epoch,
										tmpMd.writeEncoding, tmpMd.readEncoding,
										tmpMd.writeSiteInfo, tmpMd.readSiteInfo,
										tmpMd.writeLastSiteInfo, tmpMd.readLastSiteInfo);
								tmp.setPerCoreMetadata(cpuId, md);
							}
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
			boolean writebackInMemory() {
				return Options.valueOf(Knobs.WritebackInMemory);
			}

			@Override
			boolean alwaysInvalidateReadOnlyLines() {
				return Options.valueOf(Knobs.AlwaysInvalidateReadOnlyLines);
			}

			@Override
			boolean invalidateWrittenLinesOnlyAfterVersionCheck() {
				return Options.valueOf(Knobs.InvalidateWrittenLinesOnlyAfterVersionCheck);
			}

			@Override
			boolean updateWrittenLinesDuringVersionCheck() {
				return Options.valueOf(Knobs.UpdateWrittenLinesDuringVersionCheck);
			}

			@Override
			boolean invalidateUntouchedLinesOptimization() {
				return Options.valueOf(Knobs.InvalidateUntouchedLinesOptimization);
			}

			@Override
			boolean useSpecialInvalidState() {
				return Options.valueOf(Knobs.UseSpecialInvalidState);
			}

			@Override
			boolean useBloomFilter() {
				return Options.valueOf(Knobs.UseBloomFilter);
			}

			@Override
			boolean useAIMCache() {
				return Options.valueOf(Knobs.UseAIMCache);
			}

			@Override
			boolean clearAIMCacheAtRegionBoundaries() {
				return Options.valueOf(Knobs.ClearAIMAtRegionBoundaries);
			}

			@Override
			boolean deferWriteBacks() {
				return Options.valueOf(Knobs.DeferWritebacks);
			}

			@Override
			boolean areDeferredWriteBacksPrecise() {
				return Options.valueOf(Knobs.DeferredWritebacksPrecise);
			}

			@Override
			boolean skipValidatingReadLines() {
				return Options.valueOf(Knobs.SkipValidatingReadLines);
			}

			@Override
			boolean ignoreFetchingDeferredLinesDuringReadValidation() {
				return Options.valueOf(Knobs.IgnoreFetchingDeferredLinesDuringReadValidation);
			}

			@Override
			boolean ignoreFetchingReadBits() {
				return Options.valueOf(Knobs.IgnoreFetchingReadBits);
			}

			@Override
			boolean validateL1ReadsAlongWithL2() {
				return Options.valueOf(Knobs.ValidateL1ReadsAlongWithL2);
			}

			@Override
			boolean lockstep() {
				return Options.valueOf(Knobs.Lockstep);
			}

			@Override
			boolean siteTracking() {
				return Options.valueOf(Knobs.SiteTracking);
			}

			@Override
			boolean treatAtomicUpdatesAsRegularAccesses() {
				return Options.valueOf(Knobs.TreatAtomicUpdatesAsRegularAccesses);
			}

			@Override
			boolean ignoreFetchingWriteBits() {
				return Options.valueOf(Knobs.IgnoreFetchingWriteBits);
			}

			@Override
			boolean printConflictingSites() {
				return false;
			}

			@Override
			boolean isHttpd() {
				return Options.valueOf(Knobs.IsHttpd);
			}

			@Override
			boolean evictCleanLineFirst() {
				return Options.valueOf(Knobs.EvictCleanLineFirst);
			}

			@Override
			boolean usePLRU() {
				return Options.valueOf(Knobs.UsePLRU);
			}

			@Override
			boolean treatAtomicUpdatesAsRegionBoundaries() {
				return Options.valueOf(Knobs.TreatAtomicUpdatesAsRegionBoundaries);
			}
		};

		Machine<ViserLine> sim = new Machine<ViserLine>(p);
		if (sim.params.lockstep()) {
			sim.openPerThreadFifos();
		}
		sim.initializeEpochs();
		sim.prepareScavengeMap(p.numProcessors());

		String prix = "[arcsim] ";

		System.out.println(prix + "starting simulation...");

		short Cid = 0;
		while (true) {
			try {
				Event e = getNextEvent(in, sim, Cid);
				boolean simulationFinished = handleEvent(e, sim, prix);
				Cid = sim.cpuOfTid(e.tid).get();
				if (simulationFinished)
					break;
			} catch (EOFException eof) {
				break;
			}
		}

		in.close();
		double mins = (System.currentTimeMillis() - startTime) / (double) (1000 * 60);

		if (sim.params.lockstep()) {
			sim.closePerThreadFifos(); // Close per-thread fifos
		}

		if (sim.params.siteTracking()) {
			printConflicts(sim, prix);
		}
		generateStats(mins, sim);
		System.err.println(prix + "finished");
	} // end main()

	private static void printConflicts(Machine<ViserLine> sim, String prex) {
		System.out.println(
				"====================================================================================");
		System.out.println("Total Sites: " + sim.siteInfo.size());
		System.out.println(
				prex + "Conflicts (source_file_index_number:line_number:routine_index_number): ");
		int dynamicConflicts = 0;
		int staticConflicts = 0;
		for (int i = 0; i < sim.conflicts.size(); i++) {
			Conflict conflict = sim.conflicts.get(i);
			if (conflict.getCounter() == 0) { // The conflict was detected outside of ROIs.
				continue;
			}
			if (conflict.lineNumber0 != 0 && conflict.lineNumber1 != 0) {
				dynamicConflicts += conflict.getCounter();
				staticConflicts++;
				System.out.println("\t\t " + conflict);
			} else {
				System.out.println("\t\t\t " + conflict);
			}
		}
		System.out.println("\t\t Static " + staticConflicts + " and dynamic " + dynamicConflicts
				+ " in total (excluding those detected in lib functions).");
		System.out.println(
				"\t*Please see [benchmark].filenames and [benchmark].rtnnames under the Pintool directory for source file paths and routine names.");
		System.out.println(
				"====================================================================================");
	}

	private static Event getNextEvent(DataInputStream in, Machine<ViserLine> sim, short lastCid)
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
		short lastLineno = in.readShort();
		short lastFno = in.readShort();

		if (sim.params.siteTracking()) {
			SiteInfoEntry siEntry = new SiteInfoEntry(fno, lineno, rno);
			int index = sim.siteInfo.indexOf(siEntry);
			if (index == -1) {
				sim.siteInfo.add(siEntry);
				index = sim.siteInfo.size() - 1;
			}
			e.siteIndex = index;

			// last site info
			siEntry = new SiteInfoEntry(lastFno, lastLineno, (short) 0);
			index = sim.siteInfo.indexOf(siEntry);
			if (index == -1) {
				sim.siteInfo.add(siEntry);
				index = sim.siteInfo.size() - 1;
			}
			e.lastSiteIndex = index;
		} else {
			e.siteIndex = -1;
			e.lastSiteIndex = -1;
		}

		totalEvents++;

		boolean debug = false;
		if (debug && totalEvents >= 1355800) {
			System.out.println(totalEvents);
			System.out.println("Event type:" + EventType.fromByte(type) /* + " Byte:" + by */);
			System.out.println("Semantics:" + EventType.fromByte(semantics));
			System.out.println("Tid:" + tid);
			System.out.println("Addr:" + e.addr);
			System.out.println("Mem op size:" + e.memOpSize);
			System.out.println("Stack ref:" + e.stackRef);
			System.out.println("Value:" + e.value);
			System.out.println("Insn count:" + e.insnCount);
			System.out.println("SiteIndex:" + e.siteIndex);
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
	private static boolean handleEvent(final Event e, Machine<ViserLine> machine, String prefix) {
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
				machine.processRegionBoundary(cpuid, e.tid, e.type, e.semantics);
				break;
			}

			case THREAD_START: { // Called from the child thread
				currentLiveThreads++;
				numSpawnedThreads++;
				maxLiveThreads = Math.max(maxLiveThreads, currentLiveThreads);
				machine.processRegionBoundary(cpuid, e.tid, e.type, e.semantics);
				break;
			}

			case THREAD_FINISH: { // Called from the child thread
				currentLiveThreads--;
				machine.processRegionBoundary(cpuid, e.tid, e.type, e.semantics); // when main
																					// thread exits,
																					// tear
																					// down
																					// simulation
				if (e.tid.get() == 0) {
					return true;
				}
				break;
			}

			case MEMORY_READ: {
				machine.cacheRead(cpuid, e.addr, e.memOpSize, e.value, e.tid, e.siteIndex,
						e.lastSiteIndex, MemoryAccessType.MEMORY_READ);
				break;
			}

			case MEMORY_WRITE: {
				machine.cacheWrite(cpuid, e.addr, e.memOpSize, e.value, e.tid, e.siteIndex,
						e.lastSiteIndex, MemoryAccessType.MEMORY_WRITE);
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
				machine.processRegionBoundary(cpuid, e.tid, e.type, e.semantics);
				break;
			}

			case ATOMIC_READ: {
				if (machine.params.treatAtomicUpdatesAsRegularAccesses()) {
					machine.cacheRead(cpuid, e.addr, e.memOpSize, e.value, e.tid, e.siteIndex,
							e.lastSiteIndex, MemoryAccessType.MEMORY_READ);
				} else {
					machine.cacheRead(cpuid, e.addr, e.memOpSize, e.value, e.tid, e.siteIndex,
							e.lastSiteIndex, MemoryAccessType.ATOMIC_READ);
				}
				break;
			}

			case ATOMIC_WRITE: {
				if (machine.params.treatAtomicUpdatesAsRegularAccesses()) {
					machine.cacheWrite(cpuid, e.addr, e.memOpSize, e.value, e.tid, e.siteIndex,
							e.lastSiteIndex, MemoryAccessType.MEMORY_WRITE);
				} else {
					machine.cacheWrite(cpuid, e.addr, e.memOpSize, e.value, e.tid, e.siteIndex,
							e.lastSiteIndex, MemoryAccessType.ATOMIC_WRITE);
				}
				break;
			}

			case LOCK_ACQ_READ: {
				machine.cacheRead(cpuid, e.addr, e.memOpSize, e.value, e.tid, e.siteIndex,
						e.lastSiteIndex, MemoryAccessType.LOCK_ACQ_READ);
				break;
			}

			case LOCK_ACQ_WRITE: {
				machine.cacheWrite(cpuid, e.addr, e.memOpSize, e.value, e.tid, e.siteIndex,
						e.lastSiteIndex, MemoryAccessType.LOCK_ACQ_WRITE);
				break;
			}

			case LOCK_REL_WRITE: {
				machine.cacheWrite(cpuid, e.addr, e.memOpSize, e.value, e.tid, e.siteIndex,
						e.lastSiteIndex, MemoryAccessType.LOCK_REL_WRITE);
				break;
			}

			case SERVER_ROI_START: {
				if (phase == PARSEC_PHASE.PRE_ROI) {
					phase = PARSEC_PHASE.IN_SERVER_ROI;
				}
				break;
			}

			case SERVER_ROI_END: {
				if (phase == PARSEC_PHASE.IN_SERVER_ROI) {
					phase = PARSEC_PHASE.POST_SERVER_ROI;
				}
				break;
			}

			case INVALID_EVENT: {
				throw new RuntimeException("Invalid event type:\n" + e);
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

	private static void generateStats(double simRuntimeMins, Machine<ViserLine> machine)
			throws IOException {
		System.out.println("[arcsim] exiting...");
		// each stat is dumped as a Python dictionary object

		StringWriter prefix = new StringWriter();
		prefix.write("{'ViserStat':True, ");
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
		double value;

		value = DependentCounter.globalCounters.get("pc_ViserRegExecExecDrivenCycleCount").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioViserRegExecExecDrivenCycleCount': "
				+ fmt.format(value) + suffix);
		value = DependentCounter.globalCounters.get("pc_ViserPreCommitExecDrivenCycleCount").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioViserPreCommitExecDrivenCycleCount': "
				+ fmt.format(value) + suffix);
		value = DependentCounter.globalCounters.get("pc_ViserReadValidationExecDrivenCycleCount")
				.get() / denom;
		statsFd.write(prefix.toString() + "'ratioViserReadValidationExecDrivenCycleCount': "
				+ fmt.format(value) + suffix);
		value = DependentCounter.globalCounters.get("pc_ViserPostCommitExecDrivenCycleCount").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioViserPostCommitExecDrivenCycleCount': "
				+ fmt.format(value) + suffix);

		denom = MaxCounter.globalCounters.get("pc_BandwidthDrivenCycleCount").get();

		value = DependentCounter.globalCounters.get("pc_ViserRegExecBWDrivenCycleCount").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioViserRegExecBWDrivenCycleCount': "
				+ fmt.format(value) + suffix);
		value = DependentCounter.globalCounters.get("pc_ViserPreCommitBWDrivenCycleCount").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioViserPreCommitBWDrivenCycleCount': "
				+ fmt.format(value) + suffix);
		value = DependentCounter.globalCounters.get("pc_ViserReadValidationBWDrivenCycleCount")
				.get() / denom;
		statsFd.write(prefix.toString() + "'ratioViserReadValidationBWDrivenCycleCount': "
				+ fmt.format(value) + suffix);
		value = DependentCounter.globalCounters.get("pc_ViserPostCommitBWDrivenCycleCount").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioViserPostCommitBWDrivenCycleCount': "
				+ fmt.format(value) + suffix);

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

		// Compute ratio of the number of memory write backs to the number of cycles
		fmt = new DecimalFormat("0.000000");
		denom = MaxCounter.globalCounters.get("pc_ExecutionDrivenCycleCount").get();
		value = SumCounter.globalCounters.get("pc_ViserLLCToMemoryMetadataWriteback").get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioViserLLCToMemoryMetadataWritebackExecutionCycles': "
						+ fmt.format(value) + suffix);
		denom = MaxCounter.globalCounters.get("pc_BandwidthDrivenCycleCount").get();
		statsFd.write(
				prefix.toString() + "'ratioViserLLCToMemoryMetadataWritebackBandwidthCycles': "
						+ fmt.format(value) + suffix);

		// Compute proportion of network messages
		fmt = new DecimalFormat("0.000");

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessages").get();

		value = SumCounter.globalCounters.get("pc_ViserRegExecOnChipNetworkMessages").get() / denom;
		statsFd.write(prefix.toString() + "'ratioViserRegExecOnChipNetworkMessages': "
				+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters.get("pc_ViserPreCommitOnChipNetworkMessages").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioViserPreCommitOnChipNetworkMessages': "
				+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters.get("pc_ViserReadValidationOnChipNetworkMessages").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioViserReadValidationOnChipNetworkMessages': "
				+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters.get("pc_ViserPostCommitOnChipNetworkMessages").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioViserPostCommitOnChipNetworkMessages': "
				+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSizeBytes").get();

		value = SumCounter.globalCounters.get("pc_ViserRegExecOnChipNetworkMessageSizeBytes").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioViserRegExecOnChipNetworkMessageSizeBytes': "
				+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters.get("pc_ViserPreCommitOnChipNetworkMessageSizeBytes")
				.get() / denom;
		statsFd.write(prefix.toString() + "'ratioViserPreCommitOnChipNetworkMessageSizeBytes': "
				+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters.get("pc_ViserReadValidationOnChipNetworkMessageSizeBytes")
				.get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioViserReadValidationOnChipNetworkMessageSizeBytes': "
						+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters.get("pc_ViserPostCommitOnChipNetworkMessageSizeBytes")
				.get() / denom;
		statsFd.write(prefix.toString() + "'ratioViserPostCommitOnChipNetworkMessageSizeBytes': "
				+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSize4BytesFlits").get();

		value = SumCounter.globalCounters.get("pc_ViserRegExecOnChipNetworkMessageSize4BytesFlits")
				.get() / denom;
		statsFd.write(prefix.toString() + "'ratioViserRegExecOnChipNetworkMessageSize4BytesFlits': "
				+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters
				.get("pc_ViserPreCommitOnChipNetworkMessageSize4BytesFlits").get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioViserPreCommitOnChipNetworkMessageSize4BytesFlits': "
						+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters
				.get("pc_ViserReadValidationOnChipNetworkMessageSize4BytesFlits").get() / denom;
		statsFd.write(prefix.toString()
				+ "'ratioViserReadValidationOnChipNetworkMessageSize4BytesFlits': "
				+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters
				.get("pc_ViserPostCommitOnChipNetworkMessageSize4BytesFlits").get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioViserPostCommitOnChipNetworkMessageSize4BytesFlits': "
						+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSize8BytesFlits").get();

		value = SumCounter.globalCounters.get("pc_ViserRegExecOnChipNetworkMessageSize8BytesFlits")
				.get() / denom;
		statsFd.write(prefix.toString() + "'ratioViserRegExecOnChipNetworkMessageSize8BytesFlits': "
				+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters
				.get("pc_ViserPreCommitOnChipNetworkMessageSize8BytesFlits").get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioViserPreCommitOnChipNetworkMessageSize8BytesFlits': "
						+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters
				.get("pc_ViserReadValidationOnChipNetworkMessageSize8BytesFlits").get() / denom;
		statsFd.write(prefix.toString()
				+ "'ratioViserReadValidationOnChipNetworkMessageSize8BytesFlits': "
				+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters
				.get("pc_ViserPostCommitOnChipNetworkMessageSize8BytesFlits").get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioViserPostCommitOnChipNetworkMessageSize8BytesFlits': "
						+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSize16BytesFlits").get();

		value = SumCounter.globalCounters.get("pc_ViserRegExecOnChipNetworkMessageSize16BytesFlits")
				.get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioViserRegExecOnChipNetworkMessageSize16BytesFlits': "
						+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters
				.get("pc_ViserPreCommitOnChipNetworkMessageSize16BytesFlits").get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioViserPreCommitOnChipNetworkMessageSize16BytesFlits': "
						+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters
				.get("pc_ViserReadValidationOnChipNetworkMessageSize16BytesFlits").get() / denom;
		statsFd.write(prefix.toString()
				+ "'ratioViserReadValidationOnChipNetworkMessageSize16BytesFlits': "
				+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters
				.get("pc_ViserPostCommitOnChipNetworkMessageSize16BytesFlits").get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioViserPostCommitOnChipNetworkMessageSize16BytesFlits': "
						+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSize32BytesFlits").get();

		value = SumCounter.globalCounters.get("pc_ViserRegExecOnChipNetworkMessageSize32BytesFlits")
				.get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioViserRegExecOnChipNetworkMessageSize32BytesFlits': "
						+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters
				.get("pc_ViserPreCommitOnChipNetworkMessageSize32BytesFlits").get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioViserPreCommitOnChipNetworkMessageSize32BytesFlits': "
						+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters
				.get("pc_ViserReadValidationOnChipNetworkMessageSize32BytesFlits").get() / denom;
		statsFd.write(prefix.toString()
				+ "'ratioViserReadValidationOnChipNetworkMessageSize32BytesFlits': "
				+ fmt.format(value) + suffix);
		value = SumCounter.globalCounters
				.get("pc_ViserPostCommitOnChipNetworkMessageSize32BytesFlits").get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioViserPostCommitOnChipNetworkMessageSize32BytesFlits': "
						+ fmt.format(value) + suffix);

		// Viser WAR upgrades

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessages").get();
		value = SumCounter.globalCounters.get("pc_ViserUpgradeMessages").get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioViserUpgradeMessages': " + fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSizeBytes").get();
		value = SumCounter.globalCounters.get("pc_ViserUpgradeMessageSizeBytes").get() / denom;
		statsFd.write(prefix.toString() + "'ratioViserUpgradeMessageSizeBytes': "
				+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSize4BytesFlits").get();
		value = SumCounter.globalCounters.get("pc_ViserUpgradeMessageSize4BytesFlits").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioViserUpgradeMessageSize4BytesFlits': "
				+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSize8BytesFlits").get();
		value = SumCounter.globalCounters.get("pc_ViserUpgradeMessageSize8BytesFlits").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioViserUpgradeMessageSize8BytesFlits': "
				+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSize16BytesFlits").get();
		value = SumCounter.globalCounters.get("pc_ViserUpgradeMessageSize16BytesFlits").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioViserUpgradeMessageSize16BytesFlits': "
				+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSize32BytesFlits").get();
		value = SumCounter.globalCounters.get("pc_ViserUpgradeMessageSize32BytesFlits").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioViserUpgradeMessageSize32BytesFlits': "
				+ fmt.format(value) + suffix);

		// Viser RV deferred lines

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessages").get();
		value = SumCounter.globalCounters.get("pc_ViserRVDeferredLineMessages").get() / denom;
		statsFd.write(prefix.toString() + "'ratioViserRVDeferredLineMessages': " + fmt.format(value)
				+ suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSizeBytes").get();
		value = SumCounter.globalCounters.get("pc_ViserRVDeferredLineMessageSizeBytes").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioViserRVDeferredLineMessageSizeBytes': "
				+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSize4BytesFlits").get();
		value = SumCounter.globalCounters.get("pc_ViserRVDeferredLineMessageSize4ByteFlits").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioViserRVDeferredLineMessageSize4ByteFlits': "
				+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSize8BytesFlits").get();
		value = SumCounter.globalCounters.get("pc_ViserRVDeferredLineMessageSize8ByteFlits").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioViserRVDeferredLineMessageSize8ByteFlits': "
				+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSize16BytesFlits").get();
		value = SumCounter.globalCounters.get("pc_ViserRVDeferredLineMessageSize16ByteFlits").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioViserRVDeferredLineMessageSize16ByteFlits': "
				+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSize32BytesFlits").get();
		value = SumCounter.globalCounters.get("pc_ViserRVDeferredLineMessageSize32ByteFlits").get()
				/ denom;
		statsFd.write(prefix.toString() + "'ratioViserRVDeferredLineMessageSize32ByteFlits': "
				+ fmt.format(value) + suffix);

		// Compute global histograms
		statsFd.write(
				"# Histogram hgramLLCUpdatesInARegion description: 0 -- 0, 1 -- 1-10, 2 -- 11-20, 3 -- 21-30, 4 -- 31-40, 5 -- >=41\n");
		HashMap<Integer, Integer> global = new HashMap<Integer, Integer>();
		for (Processor<ViserLine> p : machine.processors) {
			for (Integer key : p.stats.hgramLLCUpdatesInARegion.keySet()) {
				Integer val = p.stats.hgramLLCUpdatesInARegion.get(key);
				if (val != null) {
					Integer tmp = global.get(key);
					if (tmp == null) {
						tmp = new Integer(val);
					} else {
						tmp += val;
					}
					global.put(key, tmp);
				}
			}
		}
		for (Integer key : global.keySet()) {
			statsFd.write(prefix.toString() + "'histogramKey" + key + "': "
					+ fmt.format(global.get(key)) + suffix);
		}

		statsFd.write(
				"# Histogram hgramLinesValidated description: 0 -- 0, 1 -- 1-10, 2 -- 11-20, 3 -- 21-30, 4 -- 31-40, 5 -- >=41\n");
		global = new HashMap<Integer, Integer>();
		for (Processor<ViserLine> p : machine.processors) {
			for (Integer key : p.stats.hgramLinesValidated.keySet()) {
				Integer val = p.stats.hgramLinesValidated.get(key);
				if (val != null) {
					Integer tmp = global.get(key);
					if (tmp == null) {
						tmp = new Integer(val);
					} else {
						tmp += val;
					}
					global.put(key, tmp);
				}
			}
		}
		for (Integer key : global.keySet()) {
			statsFd.write(prefix.toString() + "'histogramKey" + key + "': "
					+ fmt.format(global.get(key)) + suffix);
		}

		statsFd.write(
				"# Histogram hgramVersionSizes description: 0 -- <= 8 bits, 1 -- <= 9-16 bits, 2 -- <= 17-24 bits, 3 -- <= 25-32 bits \n");
		global = new HashMap<Integer, Integer>();
		for (Processor<ViserLine> p : machine.processors) {
			for (Integer key : p.stats.hgramVersionSizes.keySet()) {
				Integer val = p.stats.hgramVersionSizes.get(key);
				if (val != null) {
					Integer tmp = global.get(key);
					if (tmp == null) {
						tmp = new Integer(val);
					} else {
						tmp += val;
					}
					global.put(key, tmp);
				}
			}
		}
		for (Integer key : global.keySet()) {
			statsFd.write(prefix.toString() + "'histogramKey" + key + "': "
					+ fmt.format(global.get(key)) + suffix);
		}

		// TCC modeling

		denom = SumCounter.globalCounters.get("pc_RegionBoundaries").get();
		value = SumCounter.globalCounters.get("pc_TCCRegionsWBOverflows8K").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCRegionsWBOverflows8K': " + fmt.format(value)
				+ suffix);

		denom = SumCounter.globalCounters.get("pc_RegionBoundaries").get();
		value = SumCounter.globalCounters.get("pc_TCCRegionsWBOverflows16K").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCRegionsWBOverflows16K': " + fmt.format(value)
				+ suffix);

		denom = SumCounter.globalCounters.get("pc_RegionBoundaries").get();
		value = SumCounter.globalCounters.get("pc_TCCRegionsWBOverflows32K").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCRegionsWBOverflows32K': " + fmt.format(value)
				+ suffix);

		denom = SumCounter.globalCounters.get("pc_RegionBoundaries").get();
		value = SumCounter.globalCounters.get("pc_TCCRegionsWBOverflows64K").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCRegionsWBOverflows64K': " + fmt.format(value)
				+ suffix);

		value = SumCounter.globalCounters.get("pc_TCCRegionsCacheOverflows").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCRegionsCacheOverflows': " + fmt.format(value)
				+ suffix);

		value = SumCounter.globalCounters.get("pc_TCCRegionsOverflows8K").get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioTCCRegionsOverflows8K': " + fmt.format(value) + suffix);

		value = SumCounter.globalCounters.get("pc_TCCRegionsOverflows16K").get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioTCCRegionsOverflows16K': " + fmt.format(value) + suffix);

		value = SumCounter.globalCounters.get("pc_TCCRegionsOverflows32K").get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioTCCRegionsOverflows32K': " + fmt.format(value) + suffix);

		value = SumCounter.globalCounters.get("pc_TCCRegionsOverflows64K").get() / denom;
		statsFd.write(
				prefix.toString() + "'ratioTCCRegionsOverflows64K': " + fmt.format(value) + suffix);

		value = SumCounter.globalCounters.get("pc_TCCRegionsFirstCacheOverflows8K").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCRegionsFirstCacheOverflows8K': "
				+ fmt.format(value) + suffix);

		value = SumCounter.globalCounters.get("pc_TCCRegionsFirstCacheOverflows16K").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCRegionsFirstCacheOverflows16K': "
				+ fmt.format(value) + suffix);

		value = SumCounter.globalCounters.get("pc_TCCRegionsFirstCacheOverflows32K").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCRegionsFirstCacheOverflows32K': "
				+ fmt.format(value) + suffix);

		value = SumCounter.globalCounters.get("pc_TCCRegionsFirstCacheOverflows64K").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCRegionsFirstCacheOverflows64K': "
				+ fmt.format(value) + suffix);

		value = SumCounter.globalCounters.get("pc_TCCRegionsFirstWBOverflows8K").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCRegionsFirstWBOverflows8K': "
				+ fmt.format(value) + suffix);

		value = SumCounter.globalCounters.get("pc_TCCRegionsFirstWBOverflows16K").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCRegionsFirstWBOverflows16K': "
				+ fmt.format(value) + suffix);

		value = SumCounter.globalCounters.get("pc_TCCRegionsFirstWBOverflows32K").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCRegionsFirstWBOverflows32K': "
				+ fmt.format(value) + suffix);

		value = SumCounter.globalCounters.get("pc_TCCRegionsFirstWBOverflows64K").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCRegionsFirstWBOverflows64K': "
				+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_TotalMemoryAccesses").get();

		value = SumCounter.globalCounters.get("pc_TCCNumSerializedMemoryAccesses8K").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCNumSerializedMemoryAccesses8K': "
				+ fmt.format(value) + suffix);

		value = SumCounter.globalCounters.get("pc_TCCNumSerializedMemoryAccesses16K").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCNumSerializedMemoryAccesses16K': "
				+ fmt.format(value) + suffix);

		value = SumCounter.globalCounters.get("pc_TCCNumSerializedMemoryAccesses32K").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCNumSerializedMemoryAccesses32K': "
				+ fmt.format(value) + suffix);

		value = SumCounter.globalCounters.get("pc_TCCNumSerializedMemoryAccesses64K").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCNumSerializedMemoryAccesses64K': "
				+ fmt.format(value) + suffix);

		denom = MaxCounter.globalCounters.get("pc_BandwidthDrivenCycleCount").get();

		value = MaxCounter.globalCounters.get("pc_TCCCycleCount8K").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCCycleCount8K': " + fmt.format(value) + suffix);

		value = MaxCounter.globalCounters.get("pc_TCCCycleCount16K").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCCycleCount16K': " + fmt.format(value) + suffix);

		value = MaxCounter.globalCounters.get("pc_TCCCycleCount32K").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCCycleCount32K': " + fmt.format(value) + suffix);

		value = MaxCounter.globalCounters.get("pc_TCCCycleCount64K").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCCycleCount64K': " + fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSizeBytes").get();
		value = SumCounter.globalCounters.get("pc_TCCBroadCastMessagesBytes").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCBroadCastMessagesBytes': " + fmt.format(value)
				+ suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSize4BytesFlits").get();
		value = SumCounter.globalCounters.get("pc_TCCBroadCastMessages4BytesFlits").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCBroadCastMessages4BytesFlits': "
				+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSize8BytesFlits").get();
		value = SumCounter.globalCounters.get("pc_TCCBroadCastMessages8BytesFlits").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCBroadCastMessages8BytesFlits': "
				+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSize16BytesFlits").get();
		value = SumCounter.globalCounters.get("pc_TCCBroadCastMessages16BytesFlits").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCBroadCastMessages16BytesFlits': "
				+ fmt.format(value) + suffix);

		denom = SumCounter.globalCounters.get("pc_OnChipNetworkMessageSize32BytesFlits").get();
		value = SumCounter.globalCounters.get("pc_TCCBroadCastMessages32BytesFlits").get() / denom;
		statsFd.write(prefix.toString() + "'ratioTCCBroadCastMessages32BytesFlits': "
				+ fmt.format(value) + suffix);

		statsFd.close();
	}
}
