package simulator.viser;

import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;

import simulator.viser.ViserSim.PARSEC_PHASE;

public class Processor<Line extends ViserLine> implements CacheCallbacks<Line> {

	public enum ExecutionPhase {
		REGION_BODY, PRE_COMMIT, PRE_COMMIT_L1, PRE_COMMIT_L2, READ_VALIDATION, POST_COMMIT,
		REGION_L2_COMMIT, EVICT_L1_READ_VALIDATION, EVICT_L2_READ_VALIDATION
	};

	public enum ConflictType {
		RW, WR, WW
	};

	final CpuId id;
	/** Machine reference is shared by all processors */
	final Machine<Line> machine;

	/** L1 caches are always present, and are private to each processor */
	public final HierarchicalCache<Line> L1cache;
	/** L2 caches are private to each processor */
	public final HierarchicalCache<Line> L2cache;
	/** the L3 cache is shared by all processors */
	public final HierarchicalCache<Line> L3cache;

	// Access information cache
	public final AIMCache<Line> aimcache;

	public final BloomFilter bf;
	public final HashSet<Long> set; // keep track of unique lines written by the
									// LLC in a region

	// Needed if deferred write backs need to be precise
	public final HashMap<Long, Long> wrMdDeferredDirtyLines = new HashMap<Long, Long>();

	private enum TCCPrivateCacheOverflow {
		NO_OVERFLOW, OVERFLOWN
	}

	private enum TCCRegionsWithOverflow {
		NO_OVERFLOW, WB_OVERFLOWN, CACHE_OVERFLOWN
	}

	// Let the buffer grow as much as it wants, we assume a searchable write buffer
	private final HashSet<Long> tccWriteSet = new HashSet<Long>();
	// Use to model the victim cache, the victim cache need not have duplicates
	private final HashSet<Long> tccVictimCache = new HashSet<Long>();
	TCCPrivateCacheOverflow perRegionCacheOverflow = TCCPrivateCacheOverflow.NO_OVERFLOW;
	TCCRegionsWithOverflow perRegionOverflow8K = TCCRegionsWithOverflow.NO_OVERFLOW;
	TCCRegionsWithOverflow perRegionOverflow16K = TCCRegionsWithOverflow.NO_OVERFLOW;
	TCCRegionsWithOverflow perRegionOverflow32K = TCCRegionsWithOverflow.NO_OVERFLOW;
	TCCRegionsWithOverflow perRegionOverflow64K = TCCRegionsWithOverflow.NO_OVERFLOW;
	private long tccPerRegionStalledCycles8K = 0;
	private long tccPerRegionStalledCycles16K = 0;
	private long tccPerRegionStalledCycles32K = 0;
	private long tccPerRegionStalledCycles64K = 0;

	/**
	 * List of all the processors in the system. All processors share the same array object.
	 */
	final Processor<Line>[] allProcessors;
	final Machine.MachineParams<Line> params;
	final ProcessorStats stats = new ProcessorStats();

	// counter flags should be reset when the current region finishes
	boolean hasDirtyEviction = false;
	boolean regionConflicted = false;
	boolean regionWithExceptions = false;
	boolean regionHasDirtyEvictionBeforeFRV = false;

	class ProcessorStats {
		// counters for cache events
		class CacheEventCounter {
			SumCounter pc_ReadHits;
			SumCounter pc_ReadMisses;
			SumCounter pc_WriteHits;
			SumCounter pc_WriteMisses;
			SumCounter pc_LineEvictions;
			SumCounter pc_DirtyLineEvictions;

			// for atomic writes
			SumCounter pc_AtomicReadHits;
			SumCounter pc_AtomicReadMisses;
			SumCounter pc_AtomicWriteHits;
			SumCounter pc_AtomicWriteMisses;

			// for lock accesses
			SumCounter pc_LockReadHits;
			SumCounter pc_LockReadMisses;
			SumCounter pc_LockWriteHits;
			SumCounter pc_LockWriteMisses;

			CacheEventCounter(String prefix) {
				pc_ReadHits = new SumCounter("pc_" + prefix + "ReadHits");
				pc_ReadMisses = new SumCounter("pc_" + prefix + "ReadMisses");
				pc_WriteHits = new SumCounter("pc_" + prefix + "WriteHits");
				pc_WriteMisses = new SumCounter("pc_" + prefix + "WriteMisses");
				pc_LineEvictions = new SumCounter("pc_" + prefix + "LineEvictions");
				pc_DirtyLineEvictions = new SumCounter("pc_" + prefix + "DirtyLineEvictions");
				pc_AtomicWriteHits = new SumCounter("pc_" + prefix + "AtomicWriteHits");
				pc_AtomicWriteMisses = new SumCounter("pc_" + prefix + "AtomicWriteMisses");
				pc_AtomicReadHits = new SumCounter("pc_" + prefix + "AtomicReadHits");
				pc_AtomicReadMisses = new SumCounter("pc_" + prefix + "AtomicReadMisses");
				pc_LockReadHits = new SumCounter("pc_" + prefix + "LockReadHits");
				pc_LockReadMisses = new SumCounter("pc_" + prefix + "LockReadMisses");
				pc_LockWriteHits = new SumCounter("pc_" + prefix + "LockWriteHits");
				pc_LockWriteMisses = new SumCounter("pc_" + prefix + "LockWriteMisses");
			}
		}

		SumCounter pc_ViserWARUpgrades = new SumCounter("pc_ViserWARUpgrades");

		SumCounter pc_OnChipNetworkMessages = new SumCounter("pc_OnChipNetworkMessages");
		SumCounter pc_OnChipNetworkMessageSizeBytes = new SumCounter(
				"pc_OnChipNetworkMessageSizeBytes");
		SumCounter pc_OnChipNetworkMessageSize4BytesFlits = new SumCounter(
				"pc_OnChipNetworkMessageSize4BytesFlits");
		SumCounter pc_OnChipNetworkMessageSize8BytesFlits = new SumCounter(
				"pc_OnChipNetworkMessageSize8BytesFlits");
		SumCounter pc_OnChipNetworkMessageSize16BytesFlits = new SumCounter(
				"pc_OnChipNetworkMessageSize16BytesFlits");
		SumCounter pc_OnChipNetworkMessageSize32BytesFlits = new SumCounter(
				"pc_OnChipNetworkMessageSize32BytesFlits");

		// Compute the proportion of traffic due to read validation including WAR upgrades
		SumCounter pc_ViserUpgradeMessages = new SumCounter("pc_ViserUpgradeMessages");
		SumCounter pc_ViserUpgradeMessageSizeBytes = new SumCounter(
				"pc_ViserUpgradeMessageSizeBytes");
		SumCounter pc_ViserUpgradeMessageSize4BytesFlits = new SumCounter(
				"pc_ViserUpgradeMessageSize4BytesFlits");
		SumCounter pc_ViserUpgradeMessageSize8BytesFlits = new SumCounter(
				"pc_ViserUpgradeMessageSize8BytesFlits");
		SumCounter pc_ViserUpgradeMessageSize16BytesFlits = new SumCounter(
				"pc_ViserUpgradeMessageSize16BytesFlits");
		SumCounter pc_ViserUpgradeMessageSize32BytesFlits = new SumCounter(
				"pc_ViserUpgradeMessageSize32BytesFlits");

		// // Compute traffic if we had incorrectly not used versions for validating reads during
		// // evictions
		// SumCounter pc_OnChipMessagesIncorrect = new SumCounter("pc_OnChipMessagesIncorrect");
		// SumCounter pc_OnChipMessageSizeBytesIncorrect = new SumCounter(
		// "pc_OnChipMessageSizeBytesIncorrect");
		// SumCounter pc_OnChipMessageSize4BytesFlitsIncorrect = new SumCounter(
		// "pc_OnChipMessageSize4BytesFlitsIncorrect");
		// SumCounter pc_OnChipMessageSize8BytesFlitsIncorrect = new SumCounter(
		// "pc_OnChipMessageSize8BytesFlitsIncorrect");
		// SumCounter pc_OnChipMessageSize16BytesFlitsIncorrect = new SumCounter(
		// "pc_OnChipMessageSize16BytesFlitsIncorrect");
		// SumCounter pc_OnChipMessageSize32BytesFlitsIncorrect = new SumCounter(
		// "pc_OnChipMessageSize32BytesFlitsIncorrect");

		// Breakdown of on-chip network traffic
		// Compute the proportion of traffic due to deferring of lines
		SumCounter pc_ViserRVDeferredLineMessages = new SumCounter(
				"pc_ViserRVDeferredLineMessages");
		SumCounter pc_ViserRVDeferredLineMessageSizeBytes = new SumCounter(
				"pc_ViserRVDeferredLineMessageSizeBytes");
		SumCounter pc_ViserRVDeferredLineMessageSize4ByteFlits = new SumCounter(
				"pc_ViserRVDeferredLineMessageSize4ByteFlits");
		SumCounter pc_ViserRVDeferredLineMessageSize8ByteFlits = new SumCounter(
				"pc_ViserRVDeferredLineMessageSize8ByteFlits");
		SumCounter pc_ViserRVDeferredLineMessageSize16ByteFlits = new SumCounter(
				"pc_ViserRVDeferredLineMessageSize16ByteFlits");
		SumCounter pc_ViserRVDeferredLineMessageSize32ByteFlits = new SumCounter(
				"pc_ViserRVDeferredLineMessageSize32ByteFlits");

		// // Compute traffic if we did not compact 14-bit versions in the header
		// SumCounter pc_OnChipNetworkMessagesNoCompactVersions = new SumCounter(
		// "pc_OnChipNetworkMessagesNoCompactVersions");
		// SumCounter pc_OnChipNetworkMessageSizeBytesNoCompactVersions = new SumCounter(
		// "pc_OnChipNetworkMessageSizeBytesNoCompactVersions");
		// SumCounter pc_OnChipNetworkMessageSize4BytesFlitsNoCompactVersions = new SumCounter(
		// "pc_OnChipNetworkMessageSize4BytesFlitsNoCompactVersions");
		// SumCounter pc_OnChipNetworkMessageSize8BytesFlitsNoCompactVersions = new SumCounter(
		// "pc_OnChipNetworkMessageSize8BytesFlitsNoCompactVersions");
		// SumCounter pc_OnChipNetworkMessageSize16BytesFlitsNoCompactVersions = new SumCounter(
		// "pc_OnChipNetworkMessageSize16BytesFlitsNoCompactVersions");
		// SumCounter pc_OnChipNetworkMessageSize32BytesFlitsNoCompactVersions = new SumCounter(
		// "pc_OnChipNetworkMessageSize32BytesFlitsNoCompactVersions");

		// Breakdown of on-chip network traffic
		SumCounter pc_ViserRegExecOnChipNetworkMessages = new SumCounter(
				"pc_ViserRegExecOnChipNetworkMessages");
		SumCounter pc_ViserRegExecOnChipNetworkMessageSizeBytes = new SumCounter(
				"pc_ViserRegExecOnChipNetworkMessageSizeBytes");
		SumCounter pc_ViserRegExecOnChipNetworkMessageSize4BytesFlits = new SumCounter(
				"pc_ViserRegExecOnChipNetworkMessageSize4BytesFlits");
		SumCounter pc_ViserRegExecOnChipNetworkMessageSize8BytesFlits = new SumCounter(
				"pc_ViserRegExecOnChipNetworkMessageSize8BytesFlits");
		SumCounter pc_ViserRegExecOnChipNetworkMessageSize16BytesFlits = new SumCounter(
				"pc_ViserRegExecOnChipNetworkMessageSize16BytesFlits");
		SumCounter pc_ViserRegExecOnChipNetworkMessageSize32BytesFlits = new SumCounter(
				"pc_ViserRegExecOnChipNetworkMessageSize32BytesFlits");

		SumCounter pc_ViserPreCommitOnChipNetworkMessages = new SumCounter(
				"pc_ViserPreCommitOnChipNetworkMessages");
		SumCounter pc_ViserPreCommitOnChipNetworkMessageSizeBytes = new SumCounter(
				"pc_ViserPreCommitOnChipNetworkMessageSizeBytes");
		SumCounter pc_ViserPreCommitOnChipNetworkMessageSize4BytesFlits = new SumCounter(
				"pc_ViserPreCommitOnChipNetworkMessageSize4BytesFlits");
		SumCounter pc_ViserPreCommitOnChipNetworkMessageSize8BytesFlits = new SumCounter(
				"pc_ViserPreCommitOnChipNetworkMessageSize8BytesFlits");
		SumCounter pc_ViserPreCommitOnChipNetworkMessageSize16BytesFlits = new SumCounter(
				"pc_ViserPreCommitOnChipNetworkMessageSize16BytesFlits");
		SumCounter pc_ViserPreCommitOnChipNetworkMessageSize32BytesFlits = new SumCounter(
				"pc_ViserPreCommitOnChipNetworkMessageSize32BytesFlits");

		SumCounter pc_ViserReadValidationOnChipNetworkMessages = new SumCounter(
				"pc_ViserReadValidationOnChipNetworkMessages");
		SumCounter pc_ViserReadValidationOnChipNetworkMessageSizeBytes = new SumCounter(
				"pc_ViserReadValidationOnChipNetworkMessageSizeBytes");
		SumCounter pc_ViserReadValidationOnChipNetworkMessageSize4BytesFlits = new SumCounter(
				"pc_ViserReadValidationOnChipNetworkMessageSize4BytesFlits");
		SumCounter pc_ViserReadValidationOnChipNetworkMessageSize8BytesFlits = new SumCounter(
				"pc_ViserReadValidationOnChipNetworkMessageSize8BytesFlits");
		SumCounter pc_ViserReadValidationOnChipNetworkMessageSize16BytesFlits = new SumCounter(
				"pc_ViserReadValidationOnChipNetworkMessageSize16BytesFlits");
		SumCounter pc_ViserReadValidationOnChipNetworkMessageSize32BytesFlits = new SumCounter(
				"pc_ViserReadValidationOnChipNetworkMessageSize32BytesFlits");

		SumCounter pc_ViserPostCommitOnChipNetworkMessages = new SumCounter(
				"pc_ViserPostCommitOnChipNetworkMessages");
		SumCounter pc_ViserPostCommitOnChipNetworkMessageSizeBytes = new SumCounter(
				"pc_ViserPostCommitOnChipNetworkMessageSizeBytes");
		SumCounter pc_ViserPostCommitOnChipNetworkMessageSize4BytesFlits = new SumCounter(
				"pc_ViserPostCommitOnChipNetworkMessageSize4BytesFlits");
		SumCounter pc_ViserPostCommitOnChipNetworkMessageSize8BytesFlits = new SumCounter(
				"pc_ViserPostCommitOnChipNetworkMessageSize8BytesFlits");
		SumCounter pc_ViserPostCommitOnChipNetworkMessageSize16BytesFlits = new SumCounter(
				"pc_ViserPostCommitOnChipNetworkMessageSize16BytesFlits");
		SumCounter pc_ViserPostCommitOnChipNetworkMessageSize32BytesFlits = new SumCounter(
				"pc_ViserPostCommitOnChipNetworkMessageSize32BytesFlits");

		// // Variable-sized LLC-to-memory message: 48 bits address + (64 + 64)
		// // bits map of which
		// // core's maps are being sent + core's metadata + values if dirty.
		// SumCounter pc_LLCToMemoryMessages = new SumCounter("pc_LLCToMemoryMessages");
		// SumCounter pc_LLCToMemoryMessageSizeBytes = new SumCounter(
		// "pc_LLCToMemoryMessageSizeBytes");
		// SumCounter pc_LLCToMemoryMessageSize4BytesFlits = new SumCounter(
		// "pc_LLCToMemoryMessageSize4BytesFlits");
		// SumCounter pc_LLCToMemoryMessageSize8BytesFlits = new SumCounter(
		// "pc_LLCToMemoryMessageSize8BytesFlits");
		// SumCounter pc_LLCToMemoryMessageSize16BytesFlits = new SumCounter(
		// "pc_LLCToMemoryMessageSize16BytesFlits");
		// SumCounter pc_LLCToMemoryMessageSize32BytesFlits = new SumCounter(
		// "pc_LLCToMemoryMessageSize32BytesFlits");
		// SumCounter pc_LLCToMemoryMessageSize64BytesFlits = new SumCounter(
		// "pc_LLCToMemoryMessageSize64BytesFlits");

		// // Model memory accesses for McPAT
		// SumCounter pc_Memory64BytesAccesses = new SumCounter("pc_Memory64BytesAccesses");
		// SumCounter pc_Memory64BytesReads = new SumCounter("pc_Memory64BytesReads");
		// SumCounter pc_Memory64BytesWrites = new SumCounter("pc_Memory64BytesWrites");

		// This stat tracks the proportion of messages that actually need to be written back due to
		// read and write metadata. If the proportion is low, then we can imagine using a software
		// to convert/encode the data before writing back to memory for Viser.
		SumCounter pc_ViserLLCToMemoryMetadataWriteback = new SumCounter(
				"pc_ViserLLCToMemoryMetadataWriteback");

		SumCounter pc_RegionBoundaries = new SumCounter("pc_RegionBoundaries");
		SumCounter pc_RegionsWithWrites = new SumCounter("pc_RegionsWithWrites");

		SumCounter pc_potentialWrRdValConflicts = new SumCounter("pc_potentialWrRdValConflicts");
		SumCounter pc_ValidationAttempts = new SumCounter("pc_ValidationAttempts");
		SumCounter pc_FailedValidations = new SumCounter("pc_FailedValidations");

		// The following "conflict"-related counters don't count failed validations.
		SumCounter pc_ConflictCheckAttempts = new SumCounter("pc_ConflictCheckAttempts");
		SumCounter pc_PreciseConflicts = new SumCounter("pc_PreciseConflicts");
		SumCounter pc_RegExecPreciseConflicts = new SumCounter("pc_RegExecPreciseConflicts");
		SumCounter pc_PreCommitPreciseConflicts = new SumCounter("pc_PreCommitPreciseConflicts");
		SumCounter pc_PostCommitPreciseConflicts = new SumCounter("pc_PostCommitPreciseConflicts");
		SumCounter pc_ReadValidationPreciseConflicts = new SumCounter(
				"pc_ReadValidationPreciseConflicts");
		SumCounter pc_RegL2CommitPreciseConflicts = new SumCounter(
				"pc_RegL2CommitPreciseConflicts");
		SumCounter pc_RegEvictionRVPreciseConflicts = new SumCounter(
				"pc_RegEvictionRVPreciseConflicts");
		SumCounter pc_RWPreciseConflicts = new SumCounter("pc_RWPreciseConflicts");
		SumCounter pc_WWPreciseConflicts = new SumCounter("pc_WWPreciseConflicts");
		SumCounter pc_WRPreciseConflicts = new SumCounter("pc_WRPreciseConflicts");

		SumCounter pc_RegionsWithFRVs = new SumCounter("pc_RegionsWithFRVs");
		SumCounter pc_RegionsWithFRVsAfterPrecommit = new SumCounter(
				"pc_RegionsWithFRVsAfterPrecommit");
		SumCounter pc_RegionsWithTolerableConflicts = new SumCounter(
				"pc_RegionsWithTolerableConflicts");
		SumCounter pc_RegionsWithExceptions = new SumCounter("pc_RegionsWithExceptions");
		SumCounter pc_RegionHasDirtyEvictionBeforeFRV = new SumCounter(
				"pc_RegionHasDirtyEvictionBeforeFRV");
		SumCounter pc_ExceptionsByFRVs = new SumCounter("pc_ExceptionsByFRVs");
		SumCounter pc_RegionsWithExceptionsByFRVs = new SumCounter(
				"pc_RegionsWithExceptionsByFRVs");

		SumCounter pc_DirtyL2Evictions = new SumCounter("pc_DirtyL2Evictions");
		SumCounter pc_CleanL2DirtyL1OnL2Eviction = new SumCounter("pc_CleanL2DirtyL1OnL2Eviction");

		SumCounter pc_NumScavenges = new SumCounter("pc_NumScavenges");

		CacheEventCounter pc_l1d = new CacheEventCounter("Data_L1");
		CacheEventCounter pc_l2d = new CacheEventCounter("Data_L2");
		CacheEventCounter pc_l3d = new CacheEventCounter("Data_L3");
		CacheEventCounter pc_aim = new CacheEventCounter("AIMCache");

		SumCounter pc_TotalDataReads = new SumCounter("pc_TotalDataReads");
		SumCounter pc_TotalDataWrites = new SumCounter("pc_TotalDataWrites");
		SumCounter pc_TotalMemoryAccesses = new SumCounter("pc_TotalMemoryAccesses");
		SumCounter pc_TotalMemoryAccessesSpecialInvalidState = new SumCounter(
				"pc_TotalMemoryAccessesSpecialInvalidState");

		SumCounter pc_TotalAtomicReads = new SumCounter("pc_TotalAtomicReads");
		SumCounter pc_TotalAtomicWrites = new SumCounter("pc_TotalAtomicWrites");
		SumCounter pc_TotalAtomicAccesses = new SumCounter("pc_TotalAtomicAccesses");

		SumCounter pc_TotalLockReads = new SumCounter("pc_TotalLockReads");
		SumCounter pc_TotalLockWrites = new SumCounter("pc_TotalLockWrites");
		SumCounter pc_TotalLockAccesses = new SumCounter("pc_TotalLockAccesses");

		MaxCounter pc_ExecDrivenCycleCount = new MaxCounter("pc_ExecutionDrivenCycleCount");

		// Break down of the cycle counts. The sum should match pc_ExecDrivenCycleCount.
		DependentCounter pc_ViserRegExecExecDrivenCycleCount = new DependentCounter(
				"pc_ViserRegExecExecDrivenCycleCount", pc_ExecDrivenCycleCount);
		DependentCounter pc_ViserPreCommitExecDrivenCycleCount = new DependentCounter(
				"pc_ViserPreCommitExecDrivenCycleCount", pc_ExecDrivenCycleCount);
		DependentCounter pc_ViserReadValidationExecDrivenCycleCount = new DependentCounter(
				"pc_ViserReadValidationExecDrivenCycleCount", pc_ExecDrivenCycleCount);
		DependentCounter pc_ViserPostCommitExecDrivenCycleCount = new DependentCounter(
				"pc_ViserPostCommitExecDrivenCycleCount", pc_ExecDrivenCycleCount);

		MaxCounter pc_BandwidthDrivenCycleCount = new MaxCounter("pc_BandwidthDrivenCycleCount");
		// Break down of the cycle counts.
		DependentCounter pc_ViserRegExecBWDrivenCycleCount = new DependentCounter(
				"pc_ViserRegExecBWDrivenCycleCount", pc_BandwidthDrivenCycleCount);
		DependentCounter pc_ViserPreCommitBWDrivenCycleCount = new DependentCounter(
				"pc_ViserPreCommitBWDrivenCycleCount", pc_BandwidthDrivenCycleCount);
		DependentCounter pc_ViserReadValidationBWDrivenCycleCount = new DependentCounter(
				"pc_ViserReadValidationBWDrivenCycleCount", pc_BandwidthDrivenCycleCount);
		DependentCounter pc_ViserPostCommitBWDrivenCycleCount = new DependentCounter(
				"pc_ViserPostCommitBWDrivenCycleCount", pc_BandwidthDrivenCycleCount);

		// NOTE: These are not perfect. We want the total network over number of cycles.
		MaxCounter pc_reqdBWInGBWith4BytesFlits = new MaxCounter("pc_reqdBWInGBWith4BytesFlits");
		MaxCounter pc_reqdBWInGBWith8BytesFlits = new MaxCounter("pc_reqdBWInGBWith8BytesFlits");
		MaxCounter pc_reqdBWInGBWith16BytesFlits = new MaxCounter("pc_reqdBWInGBWith16BytesFlits");
		MaxCounter pc_reqdBWInGBWith32BytesFlits = new MaxCounter("pc_reqdBWInGBWith32BytesFlits");

		HashMap<Integer, Integer> hgramLLCUpdatesInARegion = new HashMap<Integer, Integer>();
		HashMap<Integer, Integer> hgramLinesValidated = new HashMap<Integer, Integer>();
		HashMap<Integer, Integer> hgramVersionSizes = new HashMap<Integer, Integer>();

		SumCounter pc_TCCRegionsWBOverflows8K = new SumCounter("pc_TCCRegionsWBOverflows8K");
		SumCounter pc_TCCRegionsWBOverflows16K = new SumCounter("pc_TCCRegionsWBOverflows16K");
		SumCounter pc_TCCRegionsWBOverflows32K = new SumCounter("pc_TCCRegionsWBOverflows32K");
		SumCounter pc_TCCRegionsWBOverflows64K = new SumCounter("pc_TCCRegionsWBOverflows64K");

		SumCounter pc_TCCRegionsCacheOverflows = new SumCounter("pc_TCCRegionsCacheOverflows");

		SumCounter pc_TCCRegionsOverflows8K = new SumCounter("pc_TCCRegionsOverflows8K");
		SumCounter pc_TCCRegionsOverflows16K = new SumCounter("pc_TCCRegionsOverflows16K");
		SumCounter pc_TCCRegionsOverflows32K = new SumCounter("pc_TCCRegionsOverflows32K");
		SumCounter pc_TCCRegionsOverflows64K = new SumCounter("pc_TCCRegionsOverflows64K");

		SumCounter pc_TCCRegionsFirstCacheOverflows8K = new SumCounter(
				"pc_TCCRegionsFirstCacheOverflows8K");
		SumCounter pc_TCCRegionsFirstCacheOverflows16K = new SumCounter(
				"pc_TCCRegionsFirstCacheOverflows16K");
		SumCounter pc_TCCRegionsFirstCacheOverflows32K = new SumCounter(
				"pc_TCCRegionsFirstCacheOverflows32K");
		SumCounter pc_TCCRegionsFirstCacheOverflows64K = new SumCounter(
				"pc_TCCRegionsFirstCacheOverflows64K");

		SumCounter pc_TCCRegionsFirstWBOverflows8K = new SumCounter(
				"pc_TCCRegionsFirstWBOverflows8K");
		SumCounter pc_TCCRegionsFirstWBOverflows16K = new SumCounter(
				"pc_TCCRegionsFirstWBOverflows16K");
		SumCounter pc_TCCRegionsFirstWBOverflows32K = new SumCounter(
				"pc_TCCRegionsFirstWBOverflows32K");
		SumCounter pc_TCCRegionsFirstWBOverflows64K = new SumCounter(
				"pc_TCCRegionsFirstWBOverflows64K");

		SumCounter pc_TCCNumSerializedMemoryAccesses8K = new SumCounter(
				"pc_TCCNumSerializedMemoryAccesses8K");
		SumCounter pc_TCCNumSerializedMemoryAccesses16K = new SumCounter(
				"pc_TCCNumSerializedMemoryAccesses16K");
		SumCounter pc_TCCNumSerializedMemoryAccesses32K = new SumCounter(
				"pc_TCCNumSerializedMemoryAccesses32K");
		SumCounter pc_TCCNumSerializedMemoryAccesses64K = new SumCounter(
				"pc_TCCNumSerializedMemoryAccesses64K");

		// This is all RCC cycles + serialized cycles
		MaxCounter pc_TCCCycleCount8K = new MaxCounter("pc_TCCCycleCount8K");
		MaxCounter pc_TCCCycleCount16K = new MaxCounter("pc_TCCCycleCount16K");
		MaxCounter pc_TCCCycleCount32K = new MaxCounter("pc_TCCCycleCount32K");
		MaxCounter pc_TCCCycleCount64K = new MaxCounter("pc_TCCCycleCount64K");

		SumCounter pc_TCCBroadCastMessagesBytes = new SumCounter("pc_TCCBroadCastMessagesBytes");
		SumCounter pc_TCCBroadCastMessages4BytesFlits = new SumCounter(
				"pc_TCCBroadCastMessages4BytesFlits");
		SumCounter pc_TCCBroadCastMessages8BytesFlits = new SumCounter(
				"pc_TCCBroadCastMessages8BytesFlits");
		SumCounter pc_TCCBroadCastMessages16BytesFlits = new SumCounter(
				"pc_TCCBroadCastMessages16BytesFlits");
		SumCounter pc_TCCBroadCastMessages32BytesFlits = new SumCounter(
				"pc_TCCBroadCastMessages32BytesFlits");

		// Model energy consumption for Bloom filters
		SumCounter pc_BloomFilterTotalEnergy = new SumCounter("pc_BloomFilterTotalEnergy");
		SumCounter pc_BloomFilterWriteEnergy = new SumCounter("pc_BloomFilterWriteEnergy");
		SumCounter pc_BloomFilterReadEnergy = new SumCounter("pc_BloomFilterReadEnergy");

		// FIXME: Take into account the energy cost of line evictions.
		SumCounter pc_AIMReadEnergy = new SumCounter("pc_AIMReadEnergy");
		SumCounter pc_AIMWriteEnergy = new SumCounter("pc_AIMWriteEnergy");
		SumCounter pc_AIMTotalEnergy = new SumCounter("pc_AIMTotalEnergy");
	}

	public Processor(Machine.MachineParams<Line> args, Machine<Line> machine, CpuId cpuid,
			Processor<Line>[] processors, Map<LineAddress, Integer> varmap) {
		this.params = args;
		this.id = cpuid;
		this.machine = machine;
		this.allProcessors = processors;

		/*
		 * NB: hack to get a shared L3. Necessary because we want to have a Processor object handle
		 * L3 cache evictions, and we need to supply a CacheCallbacks object to the cache ctor. So
		 * all the cache construction has to occur inside the Processor ctor.
		 */
		if (this.allProcessors[0] == null) {
			assert cpuid.get() == 0;
			// Processor 0 (us) is being constructed, so let's build the shared
			// L3.
			// NB: processor 0 handles L3 evictions!
			this.L3cache = new HierarchicalCache<Line>(args.l3config(), this, null,
					args.lineFactory(), this);
			if (params.useAIMCache()) {
				this.aimcache = new AIMCache<Line>(L3cache, args.lineFactory(), this);
			} else {
				this.aimcache = null;
			}
		} else {
			// reuse processor 0's L3 reference
			this.L3cache = this.allProcessors[0].L3cache;
			this.aimcache = this.allProcessors[0].aimcache;
		}

		if (args.useL2()) {
			this.L2cache = new HierarchicalCache<Line>(args.l2config(), this, this.L3cache,
					args.lineFactory(), this);
			this.L1cache = new HierarchicalCache<Line>(args.l1config(), this, this.L2cache,
					args.lineFactory(), this);
		} else {
			throw new RuntimeException("L2 is currently required in Viser");
		}

		// Create a per-core bloom filter, which is maintained by the LLC in the
		// design
		bf = new BloomFilter();
		set = new HashSet<Long>();
	}

	@Override
	public String toString() {
		return "Processor:" + id.toString();
	}

	/*
	 * public ExecutionPhase getPhase() { return phase; }
	 */
	/** Update counters that are lazily-computed. */
	public void preFinalizeCounters() {
		// This is per-core and has to be hard-coded. This is not perfect
		// though, since we want to
		// compute the
		// required bandwidth for the whole system. It includes the total
		// traffic upon time.

		// For required bandwidth, we iterate over each core, and find out the
		// required for that.
		// Then we find the max, and set that as the value. We zero out the
		// others so that the sum
		// at the end is reasonable.
		double bwCycles = stats.pc_BandwidthDrivenCycleCount.get();
		// numSecs can actually be zero for smaller input sizes
		double numSecs = bwCycles / (SystemConstants.CLOCK_RATE * Math.pow(10, 9));

		double num4ByteFlits = stats.pc_OnChipNetworkMessageSize4BytesFlits.get();
		double bwRateInGBPerSec = (numSecs > 0)
				? ((num4ByteFlits * SystemConstants.BYTES_IN_FLIT_4) / numSecs) / Math.pow(2, 30)
				: 0;
		stats.pc_reqdBWInGBWith4BytesFlits.set(bwRateInGBPerSec);

		double num8ByteFlits = stats.pc_OnChipNetworkMessageSize8BytesFlits.get();
		bwRateInGBPerSec = (numSecs > 0)
				? ((num8ByteFlits * SystemConstants.BYTES_IN_FLIT_8) / numSecs) / Math.pow(2, 30)
				: 0;
		stats.pc_reqdBWInGBWith8BytesFlits.set(bwRateInGBPerSec);

		double num16ByteFlits = stats.pc_OnChipNetworkMessageSize16BytesFlits.get();
		bwRateInGBPerSec = (numSecs > 0)
				? ((num16ByteFlits * SystemConstants.BYTES_IN_FLIT_16) / numSecs) / Math.pow(2, 30)
				: 0;
		stats.pc_reqdBWInGBWith16BytesFlits.set(bwRateInGBPerSec);

		double num32ByteFlits = stats.pc_OnChipNetworkMessageSize32BytesFlits.get();
		bwRateInGBPerSec = (numSecs > 0)
				? ((num32ByteFlits * SystemConstants.BYTES_IN_FLIT_32) / numSecs) / Math.pow(2, 30)
				: 0;
		stats.pc_reqdBWInGBWith32BytesFlits.set(bwRateInGBPerSec);
	}

	/* Each instruction takes one cycle. */
	public void insnsExecuted(int n) {
		stats.pc_ExecDrivenCycleCount.incr(n);
		updatePhaseExecDrivenCycleCost(ExecutionPhase.REGION_BODY, n);
		stats.pc_BandwidthDrivenCycleCount.incr(n);
		updatePhaseBWDrivenCycleCost(ExecutionPhase.REGION_BODY, n);
		stats.pc_TCCCycleCount8K.incr(n);
		stats.pc_TCCCycleCount16K.incr(n);
		stats.pc_TCCCycleCount32K.incr(n);
		stats.pc_TCCCycleCount64K.incr(n);
	}

	private void memoryCyclesElapsed(int n, DataMemoryAccessResult mor) {
		stats.pc_ExecDrivenCycleCount.incr(n);
		updatePhaseExecDrivenCycleCost(ExecutionPhase.REGION_BODY, n);
		stats.pc_BandwidthDrivenCycleCount.incr(n);
		updatePhaseBWDrivenCycleCost(ExecutionPhase.REGION_BODY, n);

		if (mor != null) {
			mor.latency += n;
		}

		stats.pc_TCCCycleCount8K.incr(n);
		stats.pc_TCCCycleCount16K.incr(n);
		stats.pc_TCCCycleCount32K.incr(n);
		stats.pc_TCCCycleCount64K.incr(n);

		// Model TCC stall cycles since region has overflowed
		if (perRegionOverflow8K != TCCRegionsWithOverflow.NO_OVERFLOW) {
			tccPerRegionStalledCycles8K += n;
		}
		if (perRegionOverflow16K != TCCRegionsWithOverflow.NO_OVERFLOW) {
			tccPerRegionStalledCycles16K += n;
		}
		if (perRegionOverflow32K != TCCRegionsWithOverflow.NO_OVERFLOW) {
			tccPerRegionStalledCycles32K += n;
		}
		if (perRegionOverflow64K != TCCRegionsWithOverflow.NO_OVERFLOW) {
			tccPerRegionStalledCycles64K += n;
		}
	}

	/** Returns which level is the last-level cache in the system. */
	CacheLevel llc() {
		if (L3cache != null) {
			return CacheLevel.L3;
		} else if (L2cache != null) {
			return CacheLevel.L2;
		} else {
			return CacheLevel.L1;
		}
	}

	public void updateTCCBroadcastMessage(double numBytes) {
		stats.pc_TCCBroadCastMessagesBytes.incr(numBytes);

		long num4ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_4);
		stats.pc_TCCBroadCastMessages4BytesFlits.incr(num4ByteFlits);
		long num8ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_8);
		stats.pc_TCCBroadCastMessages8BytesFlits.incr(num8ByteFlits);
		long num16ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_16);
		stats.pc_TCCBroadCastMessages16BytesFlits.incr(num16ByteFlits);
		long num32ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_32);
		stats.pc_TCCBroadCastMessages32BytesFlits.incr(num32ByteFlits);
	}

	public void updateUpgradeTrafficForOneNetworkMessage(int numMsgs, double numBytes) {
		assert numMsgs == 1;
		stats.pc_ViserUpgradeMessages.incr();
		stats.pc_ViserUpgradeMessageSizeBytes.incr(numBytes);

		long num4ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_4);
		stats.pc_ViserUpgradeMessageSize4BytesFlits.incr(num4ByteFlits);
		long num8ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_8);
		stats.pc_ViserUpgradeMessageSize8BytesFlits.incr(num8ByteFlits);
		long num16ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_16);
		stats.pc_ViserUpgradeMessageSize16BytesFlits.incr(num16ByteFlits);
		long num32ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_32);
		stats.pc_ViserUpgradeMessageSize32BytesFlits.incr(num32ByteFlits);
	}

	// public void updateOnChipTrafficForOneNetworkMessageNoCompactVersions(int numMsgs,
	// double numBytes) {
	// assert numMsgs == 1;
	// stats.pc_OnChipNetworkMessagesNoCompactVersions.incr();
	// stats.pc_OnChipNetworkMessageSizeBytesNoCompactVersions.incr(numBytes);
	//
	// long num4ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_4);
	// stats.pc_OnChipNetworkMessageSize4BytesFlitsNoCompactVersions.incr(num4ByteFlits);
	// long num8ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_8);
	// stats.pc_OnChipNetworkMessageSize8BytesFlitsNoCompactVersions.incr(num8ByteFlits);
	// long num16ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_16);
	// stats.pc_OnChipNetworkMessageSize16BytesFlitsNoCompactVersions.incr(num16ByteFlits);
	// long num32ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_32);
	// stats.pc_OnChipNetworkMessageSize32BytesFlitsNoCompactVersions.incr(num32ByteFlits);
	// }

	public void updateRVDeferredLineTrafficForOneNetworkMessage(int numMsgs, double numBytes) {
		assert numMsgs == 1;
		stats.pc_ViserRVDeferredLineMessages.incr();
		stats.pc_ViserRVDeferredLineMessageSizeBytes.incr(numBytes);

		long num4ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_4);
		stats.pc_ViserRVDeferredLineMessageSize4ByteFlits.incr(num4ByteFlits);
		long num8ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_8);
		stats.pc_ViserRVDeferredLineMessageSize8ByteFlits.incr(num8ByteFlits);
		long num16ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_16);
		stats.pc_ViserRVDeferredLineMessageSize16ByteFlits.incr(num16ByteFlits);
		long num32ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_32);
		stats.pc_ViserRVDeferredLineMessageSize32ByteFlits.incr(num32ByteFlits);
	}

	public void updateTrafficForOneNetworkMessage(int numMsgs, double numBytes,
			ExecutionPhase phase) {
		assert numMsgs == 1;
		stats.pc_OnChipNetworkMessages.incr();
		stats.pc_OnChipNetworkMessageSizeBytes.incr(numBytes);
		// stats.pc_CoreLLCNetworkMessages.incr();
		// stats.pc_CoreLLCNetworkMessageSizeBytes.incr(numBytes);
		updateFlitsCountForOneNetworkMessage(numBytes);
		updateExecutionPhaseOnChipNetworkTraffic(numMsgs, numBytes, phase);
	}

	// Don't call this method directly
	// In Viser, there is no core-to-core communication unlike MESI
	private void updateFlitsCountForOneNetworkMessage(double numBytes) {
		long num4ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_4);
		stats.pc_OnChipNetworkMessageSize4BytesFlits.incr(num4ByteFlits);
		// stats.pc_CoreLLCNetworkMessageSize4BytesFlits.incr(num4ByteFlits);
		long num8ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_8);
		stats.pc_OnChipNetworkMessageSize8BytesFlits.incr(num8ByteFlits);
		// stats.pc_CoreLLCNetworkMessageSize8BytesFlits.incr(num8ByteFlits);
		long num16ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_16);
		stats.pc_OnChipNetworkMessageSize16BytesFlits.incr(num16ByteFlits);
		// stats.pc_CoreLLCNetworkMessageSize16BytesFlits.incr(num16ByteFlits);
		long num32ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_32);
		stats.pc_OnChipNetworkMessageSize32BytesFlits.incr(num32ByteFlits);
		// stats.pc_CoreLLCNetworkMessageSize32BytesFlits.incr(num32ByteFlits);
	}

	// Don't call this method directly
	private void updateExecutionPhaseOnChipNetworkTraffic(int numMsgs, double numBytes,
			ExecutionPhase phase) {
		long num4ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_4);
		long num8ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_8);
		long num16ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_16);
		long num32ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_32);

		switch (phase) {
			case REGION_BODY: {
				stats.pc_ViserRegExecOnChipNetworkMessages.incr(numMsgs);
				stats.pc_ViserRegExecOnChipNetworkMessageSizeBytes.incr(numBytes);
				stats.pc_ViserRegExecOnChipNetworkMessageSize4BytesFlits.incr(num4ByteFlits);
				stats.pc_ViserRegExecOnChipNetworkMessageSize8BytesFlits.incr(num8ByteFlits);
				stats.pc_ViserRegExecOnChipNetworkMessageSize16BytesFlits.incr(num16ByteFlits);
				stats.pc_ViserRegExecOnChipNetworkMessageSize32BytesFlits.incr(num32ByteFlits);
				break;
			}
			case POST_COMMIT: {
				stats.pc_ViserPostCommitOnChipNetworkMessages.incr(numMsgs);
				stats.pc_ViserPostCommitOnChipNetworkMessageSizeBytes.incr(numBytes);
				stats.pc_ViserPostCommitOnChipNetworkMessageSize4BytesFlits.incr(num4ByteFlits);
				stats.pc_ViserPostCommitOnChipNetworkMessageSize8BytesFlits.incr(num8ByteFlits);
				stats.pc_ViserPostCommitOnChipNetworkMessageSize16BytesFlits.incr(num16ByteFlits);
				stats.pc_ViserPostCommitOnChipNetworkMessageSize32BytesFlits.incr(num32ByteFlits);
				break;
			}
			case PRE_COMMIT_L1:
			case PRE_COMMIT_L2:
			case PRE_COMMIT: {
				stats.pc_ViserPreCommitOnChipNetworkMessages.incr(numMsgs);
				stats.pc_ViserPreCommitOnChipNetworkMessageSizeBytes.incr(numBytes);
				stats.pc_ViserPreCommitOnChipNetworkMessageSize4BytesFlits.incr(num4ByteFlits);
				stats.pc_ViserPreCommitOnChipNetworkMessageSize8BytesFlits.incr(num8ByteFlits);
				stats.pc_ViserPreCommitOnChipNetworkMessageSize16BytesFlits.incr(num16ByteFlits);
				stats.pc_ViserPreCommitOnChipNetworkMessageSize32BytesFlits.incr(num32ByteFlits);
				break;
			}
			case READ_VALIDATION: {
				stats.pc_ViserReadValidationOnChipNetworkMessages.incr(numMsgs);
				stats.pc_ViserReadValidationOnChipNetworkMessageSizeBytes.incr(numBytes);
				stats.pc_ViserReadValidationOnChipNetworkMessageSize4BytesFlits.incr(num4ByteFlits);
				stats.pc_ViserReadValidationOnChipNetworkMessageSize8BytesFlits.incr(num8ByteFlits);
				stats.pc_ViserReadValidationOnChipNetworkMessageSize16BytesFlits
						.incr(num16ByteFlits);
				stats.pc_ViserReadValidationOnChipNetworkMessageSize32BytesFlits
						.incr(num32ByteFlits);
				break;
			}
			default: {
				System.out.println(phase);
				assert false;
			}
		}
	}

	// // This aims to count all accesses to memory and is used to model memory
	// // accesses in the McPAT
	// // simulator. This should be greater or equal to off-chip traffic.
	// public void updateMemoryAccesses(double numBytes, boolean read) {
	// long num64BytesPkts = (long) Math.ceil(numBytes / 64);
	// stats.pc_Memory64BytesAccesses.incr(num64BytesPkts);
	// if (read) {
	// stats.pc_Memory64BytesReads.incr(num64BytesPkts);
	// } else {
	// stats.pc_Memory64BytesWrites.incr(num64BytesPkts);
	// }
	// }

	// public void updateTrafficForLLCToMemoryMessage(double numBytes, boolean read) {
	// stats.pc_LLCToMemoryMessages.incr();
	// stats.pc_LLCToMemoryMessageSizeBytes.incr(numBytes);
	// updateFlitsCountForLLCToMemoryMessage(numBytes, read);
	// }
	//
	// private void updateFlitsCountForLLCToMemoryMessage(double numBytes, boolean read) {
	// long num4ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_4);
	// stats.pc_LLCToMemoryMessageSize4BytesFlits.incr(num4ByteFlits);
	// long num8ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_8);
	// stats.pc_LLCToMemoryMessageSize8BytesFlits.incr(num8ByteFlits);
	// long num16ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_16);
	// stats.pc_LLCToMemoryMessageSize16BytesFlits.incr(num16ByteFlits);
	// long num32ByteFlits = (long) Math.ceil(numBytes / SystemConstants.BYTES_IN_FLIT_32);
	// stats.pc_LLCToMemoryMessageSize32BytesFlits.incr(num32ByteFlits);
	// long num64BytesPkts = (long) Math.ceil(numBytes / 64);
	// stats.pc_LLCToMemoryMessageSize64BytesFlits.incr(num64BytesPkts);
	// }

	void updatePhaseExecDrivenCycleCost(ExecutionPhase phase, double value) {
		switch (phase) {
			case REGION_BODY: {
				stats.pc_ViserRegExecExecDrivenCycleCount.incr(value);
				break;
			}
			case POST_COMMIT: {
				stats.pc_ViserPostCommitExecDrivenCycleCount.incr(value);
				break;
			}
			case PRE_COMMIT: {
				stats.pc_ViserPreCommitExecDrivenCycleCount.incr(value);
				break;
			}
			case READ_VALIDATION: {
				stats.pc_ViserReadValidationExecDrivenCycleCount.incr(value);
				break;
			}
			default: {
				assert false;
			}
		}
	}

	void updatePhaseBWDrivenCycleCost(ExecutionPhase phase, double value) {
		switch (phase) {
			case REGION_BODY: {
				stats.pc_ViserRegExecBWDrivenCycleCount.incr(value);
				break;
			}
			case POST_COMMIT: {
				stats.pc_ViserPostCommitBWDrivenCycleCount.incr(value);
				break;
			}
			case PRE_COMMIT: {
				stats.pc_ViserPreCommitBWDrivenCycleCount.incr(value);
				break;
			}
			case READ_VALIDATION: {
				stats.pc_ViserReadValidationBWDrivenCycleCount.incr(value);
				break;
			}
			default: {
				assert false;
			}
		}
	}

	void updateAIMEnergy(boolean read) {
		int numCores = params.numProcessors();
		int sizeAIM = ViserSim.Options.valueOf(Knobs.NumAIMLines);

		switch (numCores) {
			case 8: {
				switch (sizeAIM) {
					case 1 << 14: { // 16K
						if (read) {
							stats.pc_AIMReadEnergy.incr(SystemConstants.AIM_8C_16K_READ_ENERGY);
							stats.pc_AIMTotalEnergy.incr(SystemConstants.AIM_8C_16K_READ_ENERGY);
						} else {
							stats.pc_AIMWriteEnergy.incr(SystemConstants.AIM_8C_16K_WRITE_ENERGY);
							stats.pc_AIMTotalEnergy.incr(SystemConstants.AIM_8C_16K_WRITE_ENERGY);
						}
						break;
					}
					case 1 << 15: { // 32K
						if (read) {
							stats.pc_AIMReadEnergy.incr(SystemConstants.AIM_8C_32K_READ_ENERGY);
							stats.pc_AIMTotalEnergy.incr(SystemConstants.AIM_8C_32K_READ_ENERGY);
						} else {
							stats.pc_AIMWriteEnergy.incr(SystemConstants.AIM_8C_32K_WRITE_ENERGY);
							stats.pc_AIMTotalEnergy.incr(SystemConstants.AIM_8C_32K_WRITE_ENERGY);
						}
						break;
					}
					default: {
						throw new RuntimeException("No case to handle the current AIM size!");
					}
				}
				break;
			}
			case 16: {
				switch (sizeAIM) {
					case 1 << 14: { // 16K
						if (read) {
							stats.pc_AIMReadEnergy.incr(SystemConstants.AIM_16C_16K_READ_ENERGY);
							stats.pc_AIMTotalEnergy.incr(SystemConstants.AIM_16C_16K_READ_ENERGY);
						} else {
							stats.pc_AIMWriteEnergy.incr(SystemConstants.AIM_16C_16K_WRITE_ENERGY);
							stats.pc_AIMTotalEnergy.incr(SystemConstants.AIM_16C_16K_WRITE_ENERGY);
						}
						break;
					}
					case 1 << 15: { // 32K
						if (read) {
							stats.pc_AIMReadEnergy.incr(SystemConstants.AIM_16C_32K_READ_ENERGY);
							stats.pc_AIMTotalEnergy.incr(SystemConstants.AIM_16C_32K_READ_ENERGY);
						} else {
							stats.pc_AIMWriteEnergy.incr(SystemConstants.AIM_16C_32K_WRITE_ENERGY);
							stats.pc_AIMTotalEnergy.incr(SystemConstants.AIM_16C_32K_WRITE_ENERGY);
						}
						break;
					}
					default: {
						throw new RuntimeException("No case to handle the current AIM size!");
					}
				}
				break;
			}
			case 32: {
				switch (sizeAIM) {
					case 1 << 14: { // 16K
						if (read) {
							stats.pc_AIMReadEnergy.incr(SystemConstants.AIM_32C_16K_READ_ENERGY);
							stats.pc_AIMTotalEnergy.incr(SystemConstants.AIM_32C_16K_READ_ENERGY);
						} else {
							stats.pc_AIMWriteEnergy.incr(SystemConstants.AIM_32C_16K_WRITE_ENERGY);
							stats.pc_AIMTotalEnergy.incr(SystemConstants.AIM_32C_16K_WRITE_ENERGY);
						}
						break;
					}
					case 1 << 15: { // 32K
						if (read) {
							stats.pc_AIMReadEnergy.incr(SystemConstants.AIM_32C_32K_READ_ENERGY);
							stats.pc_AIMTotalEnergy.incr(SystemConstants.AIM_32C_32K_READ_ENERGY);
						} else {
							stats.pc_AIMWriteEnergy.incr(SystemConstants.AIM_32C_32K_WRITE_ENERGY);
							stats.pc_AIMTotalEnergy.incr(SystemConstants.AIM_32C_32K_WRITE_ENERGY);
						}
						break;
					}
					case 1 << 16: { // 64K
						if (read) {
							stats.pc_AIMReadEnergy.incr(SystemConstants.AIM_32C_32K_READ_ENERGY);
							stats.pc_AIMTotalEnergy.incr(SystemConstants.AIM_32C_32K_READ_ENERGY);
						} else {
							stats.pc_AIMWriteEnergy.incr(SystemConstants.AIM_32C_32K_WRITE_ENERGY);
							stats.pc_AIMTotalEnergy.incr(SystemConstants.AIM_32C_32K_WRITE_ENERGY);
						}
						break;
					}
					default: {
						throw new RuntimeException("No case to handle the current AIM size!");
					}
				}
				break;
			}
			default: {
				if (params.numProcessors() == 1 || params.numProcessors() == 4) {
					// Leave these out for JUnit test cases
				} else {
					throw new RuntimeException("No case to handle the current core count!");
				}
			}
		}
	}

	void updatePhaseTolerableConflicts(ExecutionPhase phase) {
		switch (phase) {
			case REGION_BODY: {
				stats.pc_RegExecPreciseConflicts.incr();
				break;
			}
			case POST_COMMIT: {
				stats.pc_PostCommitPreciseConflicts.incr();
				break;
			}
			case PRE_COMMIT: {
				stats.pc_PreCommitPreciseConflicts.incr();
				break;
			}
			case READ_VALIDATION: {
				stats.pc_ReadValidationPreciseConflicts.incr();
				break;
			}
			case REGION_L2_COMMIT: {
				stats.pc_RegL2CommitPreciseConflicts.incr();
				break;
			}
			case EVICT_L1_READ_VALIDATION:
			case EVICT_L2_READ_VALIDATION: {
				stats.pc_RegEvictionRVPreciseConflicts.incr();
				break;
			}
			default: {
				assert false;
			}
		}
	}

	void updateTypeTolerableConflicts(ConflictType type) {
		switch (type) {
			case RW: {
				stats.pc_RWPreciseConflicts.incr();
				break;
			}
			case WW: {
				stats.pc_WWPreciseConflicts.incr();
				break;
			}
			case WR: {
				stats.pc_WRPreciseConflicts.incr();
				break;
			}
			default: {
				assert false;
			}
		}
	}

	/*
	 * void updateExecutionPhaseOnChipNetworkTraffic(ExecutionPhase phase, int numMsgs, double
	 * numBytes) { switch (phase) { case REGION_BODY: {
	 * stats.pc_ViserRegExecOnChipNetworkMessages.incr(numMsgs);
	 * stats.pc_ViserRegExecOnChipNetworkMessageSizeBytes.incr((int) numBytes); int num4ByteFlits =
	 * (int) Math.ceil(numBytes / MemorySystemConstants.BYTES_IN_FLIT_4);
	 * stats.pc_ViserRegExecOnChipNetworkMessageSize4BytesFlits.incr( num4ByteFlits); int
	 * num8ByteFlits = (int) Math.ceil(numBytes / MemorySystemConstants.BYTES_IN_FLIT_8);
	 * stats.pc_ViserRegExecOnChipNetworkMessageSize8BytesFlits.incr( num8ByteFlits); int
	 * num16ByteFlits = (int) Math.ceil(numBytes / MemorySystemConstants.BYTES_IN_FLIT_16);
	 * stats.pc_ViserRegExecOnChipNetworkMessageSize16BytesFlits.incr( num16ByteFlits); int
	 * num32ByteFlits = (int) Math.ceil(numBytes / MemorySystemConstants.BYTES_IN_FLIT_32);
	 * stats.pc_ViserRegExecOnChipNetworkMessageSize32BytesFlits.incr( num32ByteFlits); break; }
	 * case POST_COMMIT: { stats.pc_ViserPostCommitOnChipNetworkMessages.incr(numMsgs);
	 * stats.pc_ViserPostCommitOnChipNetworkMessageSizeBytes.incr((int) numBytes); int num4ByteFlits
	 * = (int) Math.ceil(numBytes / MemorySystemConstants.BYTES_IN_FLIT_4);
	 * stats.pc_ViserPostCommitOnChipNetworkMessageSize4BytesFlits.incr( num4ByteFlits); int
	 * num8ByteFlits = (int) Math.ceil(numBytes / MemorySystemConstants.BYTES_IN_FLIT_8);
	 * stats.pc_ViserPostCommitOnChipNetworkMessageSize8BytesFlits.incr( num8ByteFlits); int
	 * num16ByteFlits = (int) Math.ceil(numBytes / MemorySystemConstants.BYTES_IN_FLIT_16);
	 * stats.pc_ViserPostCommitOnChipNetworkMessageSize16BytesFlits.incr( num16ByteFlits); int
	 * num32ByteFlits = (int) Math.ceil(numBytes / MemorySystemConstants.BYTES_IN_FLIT_32);
	 * stats.pc_ViserPostCommitOnChipNetworkMessageSize32BytesFlits.incr( num32ByteFlits); break; }
	 * case PRE_COMMIT: { stats.pc_ViserPreCommitOnChipNetworkMessages.incr(numMsgs);
	 * stats.pc_ViserPreCommitOnChipNetworkMessageSizeBytes.incr((int) numBytes); int num4ByteFlits
	 * = (int) Math.ceil(numBytes / MemorySystemConstants.BYTES_IN_FLIT_4);
	 * stats.pc_ViserPreCommitOnChipNetworkMessageSize4BytesFlits.incr( num4ByteFlits); int
	 * num8ByteFlits = (int) Math.ceil(numBytes / MemorySystemConstants.BYTES_IN_FLIT_8);
	 * stats.pc_ViserPreCommitOnChipNetworkMessageSize8BytesFlits.incr( num8ByteFlits); int
	 * num16ByteFlits = (int) Math.ceil(numBytes / MemorySystemConstants.BYTES_IN_FLIT_16);
	 * stats.pc_ViserPreCommitOnChipNetworkMessageSize16BytesFlits.incr( num16ByteFlits); int
	 * num32ByteFlits = (int) Math.ceil(numBytes / MemorySystemConstants.BYTES_IN_FLIT_32);
	 * stats.pc_ViserPreCommitOnChipNetworkMessageSize32BytesFlits.incr( num32ByteFlits); break; }
	 * case READ_VALIDATION: { stats.pc_ViserReadValidationOnChipNetworkMessages.incr(numMsgs);
	 * stats.pc_ViserReadValidationOnChipNetworkMessageSizeBytes.incr((int) numBytes); int
	 * num4ByteFlits = (int) Math.ceil(numBytes / MemorySystemConstants.BYTES_IN_FLIT_4);
	 * stats.pc_ViserReadValidationOnChipNetworkMessageSize4BytesFlits.incr( num4ByteFlits); int
	 * num8ByteFlits = (int) Math.ceil(numBytes / MemorySystemConstants.BYTES_IN_FLIT_8);
	 * stats.pc_ViserReadValidationOnChipNetworkMessageSize8BytesFlits.incr( num8ByteFlits); int
	 * num16ByteFlits = (int) Math.ceil(numBytes / MemorySystemConstants.BYTES_IN_FLIT_16);
	 * stats.pc_ViserReadValidationOnChipNetworkMessageSize16BytesFlits.incr( num16ByteFlits); int
	 * num32ByteFlits = (int) Math.ceil(numBytes / MemorySystemConstants.BYTES_IN_FLIT_32);
	 * stats.pc_ViserReadValidationOnChipNetworkMessageSize32BytesFlits.incr( num32ByteFlits);
	 * break; } default: { assert false; } } }
	 */

	@Override
	public Line eviction(final Line incoming, final LinkedList<Line> set, final CacheLevel level,
			ExecutionPhase phase, short bits) {
		Line toEvict = null;
		if (params.usePLRU()) {
			for (int i = 0; i < set.size(); i++) {
				Line line = set.get(i);
				if (!line.valid()) {
					toEvict = line;
					break;
				}
			}
			if (toEvict == null) { // need to evict a valid line
				for (int i = 0; i < set.size(); i++) {
					if ((bits & (1 << i)) == 0) {
						toEvict = set.get(i);
						break;
					}
				}
			}
		} else {
			toEvict = set.getLast(); // straight LRU

			if ((params.evictCleanLineFirst() && !hasDirtyEviction) && level == CacheLevel.L2
					&& toEvict.valid()) {
				List<Line> tmp = new ArrayList<Line>(set.size());
				boolean notPreferred;
				long enc;
				do {
					Line l1Line = L1cache.getLine(toEvict);

					if (l1Line != null && l1Line.valid())
						enc = l1Line.getWriteEncoding(id) | toEvict.getWriteEncoding(id);
					else
						enc = toEvict.getWriteEncoding(id);
					notPreferred = enc != 0L;

					if (notPreferred && set.size() > 1) { // WAR or dirty line
						set.removeLast();
						tmp.add(toEvict);
						toEvict = set.getLast();
					} else
						break;
				} while (true);

				for (int i = tmp.size() - 1; i >= 0; i--)
					set.addLast(tmp.get(i));
				if (notPreferred) {
					// System.out.println("WAR Eviction from " + id);
					toEvict = set.getLast();
				}
			}
		}

		assert toEvict.id() == id;
		if (toEvict.valid()) {
			switch (level) {
				case L1: {
					stats.pc_l1d.pc_LineEvictions.incr();
					if (toEvict.dirty()) {
						stats.pc_l1d.pc_DirtyLineEvictions.incr();
					}
					break;
				}
				case L2: {
					stats.pc_l2d.pc_LineEvictions.incr();
					if (toEvict.dirty()) {
						stats.pc_l2d.pc_DirtyLineEvictions.incr();
					}
					// Only take into account lines accessed in this region
					if (toEvict.isAccessedInThisRegion(id)) {
						if (perRegionCacheOverflow == TCCPrivateCacheOverflow.NO_OVERFLOW) {
							if (!tccVictimCache.contains(toEvict.lineAddress().get())) {
								tccVictimCache.add(toEvict.lineAddress().get());
							}
							if (tccVictimCache.size() > SystemConstants.TCC_VC_SIZE_64) {
								perRegionCacheOverflow = TCCPrivateCacheOverflow.OVERFLOWN;

								if (perRegionOverflow8K == TCCRegionsWithOverflow.NO_OVERFLOW) {
									perRegionOverflow8K = TCCRegionsWithOverflow.CACHE_OVERFLOWN;
								} else if (perRegionOverflow16K == TCCRegionsWithOverflow.NO_OVERFLOW) {
									perRegionOverflow16K = TCCRegionsWithOverflow.CACHE_OVERFLOWN;
								} else if (perRegionOverflow32K == TCCRegionsWithOverflow.NO_OVERFLOW) {
									perRegionOverflow32K = TCCRegionsWithOverflow.CACHE_OVERFLOWN;
								} else if (perRegionOverflow64K == TCCRegionsWithOverflow.NO_OVERFLOW) {
									perRegionOverflow64K = TCCRegionsWithOverflow.CACHE_OVERFLOWN;
								}
							}
						}
					}
					break;
				}
				case L3: {
					stats.pc_l3d.pc_LineEvictions.incr();
					if (toEvict.dirty()) {
						stats.pc_l3d.pc_DirtyLineEvictions.incr();
					}
					break;
				}
				case MEMORY:
				default: {
					assert false : "Wrong level";
				}
			}
		}
		return toEvict;
	}

	public static class DataMemoryAccessResult {
		/** The latency of this memory operation, in cycles. */
		int latency = 0;
		/**
		 * true if remote communication happened, due to remote hit or LLC miss, false on a purely
		 * local hit
		 */
		boolean remoteCommunicatedHappened = false;

		/**
		 * Aggregate the result of another memory op into the current result.
		 */
		void aggregate(DataMemoryAccessResult dmar) {
			this.remoteCommunicatedHappened |= dmar.remoteCommunicatedHappened;
			this.latency = Math.max(this.latency, dmar.latency);
		}
	}

	/** Perform a data read specified by the given access. */
	public DataMemoryAccessResult read(final DataAccess access) {
		if (access.isAtomic()) {
			stats.pc_TotalAtomicReads.incr();
			stats.pc_TotalAtomicAccesses.incr();
		} else if (access.isLockAccess()) {
			stats.pc_TotalLockReads.incr();
			stats.pc_TotalLockAccesses.incr();
		} else {
			stats.pc_TotalDataReads.incr();
			stats.pc_TotalMemoryAccesses.incr();
		}

		if (access.isRegularMemAccess()) {
			if (perRegionOverflow8K != TCCRegionsWithOverflow.NO_OVERFLOW) {
				stats.pc_TCCNumSerializedMemoryAccesses8K.incr();
			}
			if (perRegionOverflow16K != TCCRegionsWithOverflow.NO_OVERFLOW) {
				stats.pc_TCCNumSerializedMemoryAccesses16K.incr();
			}
			if (perRegionOverflow32K != TCCRegionsWithOverflow.NO_OVERFLOW) {
				stats.pc_TCCNumSerializedMemoryAccesses32K.incr();
			}
			if (perRegionOverflow64K != TCCRegionsWithOverflow.NO_OVERFLOW) {
				stats.pc_TCCNumSerializedMemoryAccesses64K.incr();
			}
		}

		DataMemoryAccessResult dmaResult = new DataMemoryAccessResult();
		dmaResult.remoteCommunicatedHappened = false;

		MemoryResponse<Line> resp = null;
		resp = L1cache.requestWithSpecialInvalidState(this, access, true);
		if (params.useSpecialInvalidState()) {
			// Both cannot be true at the same time
			assert (resp.invalidStateHit ? !resp.invalidStateFailure : true)
					&& (resp.invalidStateFailure ? !resp.invalidStateHit : true);
		}
		if (resp.invalidStateHit || resp.invalidStateFailure) {
			stats.pc_TotalMemoryAccessesSpecialInvalidState.incr();
		}

		// Remove current address from TCC vicitim cache since it has been reused
		tccVictimCache.remove(access.lineAddress().get());

		Line line = resp.lineHit;
		assert line.id() == id : "The owner of a private line should always be the current core";
		assert line.valid() && line.getLevel() == CacheLevel.L1;
		assert line.getEpoch(id).equals(getCurrentEpoch());

		// update metadata after compute costs

		ExecutionPhase phase = ExecutionPhase.REGION_BODY;

		switch (resp.whereHit) {
			case L1: {
				if (access.isAtomic()) {
					stats.pc_l1d.pc_AtomicReadHits.incr();
				} else if (access.isLockAccess()) {
					stats.pc_l1d.pc_LockReadHits.incr();
				} else {
					stats.pc_l1d.pc_ReadHits.incr();
				}

				if (resp.invalidStateHit) {
					// The core had to talk with the LLC, L1 latency is included
					int cost;
					if (resp.invalidStateSharedHitLevel == CacheLevel.L3) {
						cost = SystemConstants.L3_HIT_LATENCY;
					} else {
						cost = SystemConstants.MEMORY_LATENCY;
					}
					memoryCyclesElapsed(cost, dmaResult);

					int sizeBytesOutgoing = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES
							+ SystemConstants.VISER_VERSION_BYTES;
					updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, phase);
					updateTCCBroadcastMessage(sizeBytesOutgoing);

					int sizeBytesReturn = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES;
					updateTrafficForOneNetworkMessage(1, sizeBytesReturn, phase);
					updateTCCBroadcastMessage(sizeBytesReturn);

					if (resp.invalidStateSharedHitLevel == CacheLevel.MEMORY) {
						// Outgoing message
						updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, phase);
						// updateTrafficForLLCToMemoryMessage(sizeBytesOutgoing, true);
						// updateMemoryAccesses(sizeBytesOutgoing, true);

						// // Return message. We are not actually fetching the
						// whole line into the LLC,
						// // so that is why we are not accounting for metadata
						// for other cores. Also,
						// // this is a invalid_state hit, so that means the
						// version matches.
						// int sizeMemBytesReturn =
						// MemorySystemConstants.DATA_MESSAGE_CONTROL_BYTES
						// +
						// MemorySystemConstants.DATA_MESSAGE_SIZE_BYTES +
						// MemorySystemConstants.VISER_VERSION_BYTES;
						// if (line.hasReadOffsets(id)) {
						// sizeMemBytesReturn +=
						// MemorySystemConstants.VISER_READ_METADATA_BYTES;
						// }
						// if (line.hasWrittenOffsets(id)) {
						// sizeMemBytesReturn +=
						// MemorySystemConstants.VISER_WRITE_METADATA_BYTES;
						// }

						// We do not need inclusivity, the LLC need not have the
						// line cached.
						int sizeMemBytesReturn = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES;
						updateTrafficForOneNetworkMessage(1, sizeMemBytesReturn, phase);
						// updateTrafficForLLCToMemoryMessage(sizeMemBytesReturn, true);
						// updateMemoryAccesses(sizeMemBytesReturn, true);
					}
				} else {
					memoryCyclesElapsed(SystemConstants.L1_HIT_LATENCY, dmaResult);
				}
				break;
			}

			case L2: {
				assert params.useL2();
				if (access.isAtomic()) {
					stats.pc_l1d.pc_AtomicReadMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_AtomicReadHits.incr();
					}
				} else if (access.isLockAccess()) {
					stats.pc_l1d.pc_LockReadMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_LockReadHits.incr();
					}
				} else {
					stats.pc_l1d.pc_ReadMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_ReadHits.incr();
					}
				}

				if (resp.invalidStateHit) {
					// The core had to talk with the LLC, L2 latency is included
					int cost;
					if (resp.invalidStateSharedHitLevel == CacheLevel.L3) {
						cost = SystemConstants.L3_HIT_LATENCY;
					} else {
						cost = SystemConstants.MEMORY_LATENCY;
					}
					memoryCyclesElapsed(cost, dmaResult);

					int sizeBytesOutgoing = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES
							+ SystemConstants.VISER_VERSION_BYTES;
					updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, phase);
					updateTCCBroadcastMessage(sizeBytesOutgoing);

					int sizeBytesReturn = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES;
					updateTrafficForOneNetworkMessage(1, sizeBytesReturn, phase);
					updateTCCBroadcastMessage(sizeBytesReturn);

					if (resp.invalidStateSharedHitLevel == CacheLevel.MEMORY) {
						// Outgoing message
						updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, phase);
						// updateTrafficForLLCToMemoryMessage(sizeBytesOutgoing, true);
						// updateMemoryAccesses(sizeBytesOutgoing, true);

						// // Return message. We are not actually fetching the
						// whole line into the
						// LLC,
						// // so that is why we are not accounting for metadata
						// for other cores.
						// Also,
						// // this is a invalid_state hit, so that means the
						// version matches.
						// int sizeMemBytesReturn =
						// MemorySystemConstants.DATA_MESSAGE_CONTROL_BYTES
						// +
						// MemorySystemConstants.DATA_MESSAGE_SIZE_BYTES +
						// MemorySystemConstants.VISER_VERSION_BYTES;
						// if (line.hasReadOffsets(id)) {
						// sizeMemBytesReturn +=
						// MemorySystemConstants.VISER_READ_METADATA_BYTES;
						// }
						// if (line.hasWrittenOffsets(id)) {
						// sizeMemBytesReturn +=
						// MemorySystemConstants.VISER_WRITE_METADATA_BYTES;
						// }

						// We do not need inclusivity, the LLC need not have the
						// line cached.
						int sizeMemBytesReturn = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES;
						updateTrafficForOneNetworkMessage(1, sizeMemBytesReturn, phase);
						// updateTrafficForLLCToMemoryMessage(sizeMemBytesReturn, true);
						// updateMemoryAccesses(sizeMemBytesReturn, true);
					}
				} else {
					memoryCyclesElapsed(SystemConstants.L2_HIT_LATENCY, dmaResult);
				}
				break;
			}

			case L3: {
				if (access.isAtomic()) {
					stats.pc_l1d.pc_AtomicReadMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_AtomicReadMisses.incr();
					}
					stats.pc_l3d.pc_AtomicReadHits.incr();
				} else if (access.isLockAccess()) {
					stats.pc_l1d.pc_LockReadMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_LockReadMisses.incr();
					}
					stats.pc_l3d.pc_LockReadHits.incr();
				} else {
					stats.pc_l1d.pc_ReadMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_ReadMisses.incr();
					}
					stats.pc_l3d.pc_ReadHits.incr();
				}

				// request to LLC, and a return data message
				int sizeBytesOutgoing = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES;

				if (params.useAIMCache() && access.isRegularMemAccess()) {
					if (resp.aimHit == CacheLevel.L3) {
						memoryCyclesElapsed(SystemConstants.L3_HIT_LATENCY, dmaResult);
					} else if (resp.aimHit == CacheLevel.MEMORY) {
						memoryCyclesElapsed(SystemConstants.MEMORY_LATENCY, dmaResult);

						// Consider a control message sent to memory
						updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, phase);
						// updateTrafficForLLCToMemoryMessage(sizeBytesOutgoing, true);
						// updateMemoryAccesses(sizeBytesOutgoing, true);

						// Account for the return message
						Line memLine = machine.memory.get(line.lineAddress().get());
						// If the memory line is null, it implies no metadata.
						if (memLine != null) {
							// accountOffChipTraffic(memLine);
						}
						// int sizeBytes = SystemConstants.DATA_MESSAGE_CONTROL_BYTES
						// + getAIMLineSize();
						// updateMemoryAccesses(sizeBytes, true);
					} else {
						throw new RuntimeException("Invalid hit level for AIM");
					}
				} else {
					memoryCyclesElapsed(SystemConstants.L3_HIT_LATENCY, dmaResult);
				}

				// The line was in special invalid state, but failed a version
				// check.
				if (resp.invalidStateFailure) {
					sizeBytesOutgoing += SystemConstants.VISER_VERSION_BYTES;
				}
				updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, phase);
				updateTCCBroadcastMessage(sizeBytesOutgoing);

				int sizeBytesReturn = SystemConstants.DATA_MESSAGE_CONTROL_BYTES
						+ SystemConstants.DATA_MESSAGE_SIZE_BYTES
						+ SystemConstants.VISER_VERSION_BYTES;
				if (!params.ignoreFetchingReadBits()) {
					if (line.hasReadOffsets(id)) {
						sizeBytesReturn += SystemConstants.VISER_READ_METADATA_BYTES;
					}
				} else {
					clearReadBitsForPrivateLines(line);
				}
				if (!params.ignoreFetchingWriteBits()) {
					if (line.hasWrittenOffsets(id)) {
						sizeBytesReturn += SystemConstants.VISER_WRITE_METADATA_BYTES;
					}
				} else {
					clearWriteBitsForPrivateLines(line);
				}

				updateTrafficForOneNetworkMessage(1, sizeBytesReturn, phase);
				updateTCCBroadcastMessage(sizeBytesReturn);
				break;
			}

			case MEMORY: {
				if (access.isAtomic()) {
					stats.pc_l1d.pc_AtomicReadMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_AtomicReadMisses.incr();
					}
					stats.pc_l3d.pc_AtomicReadMisses.incr();
				} else if (access.isLockAccess()) {
					stats.pc_l1d.pc_LockReadMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_LockReadMisses.incr();
					}
					stats.pc_l3d.pc_LockReadMisses.incr();
				} else {
					stats.pc_l1d.pc_ReadMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_ReadMisses.incr();
					}
					stats.pc_l3d.pc_ReadMisses.incr();
				}

				memoryCyclesElapsed(SystemConstants.MEMORY_LATENCY, dmaResult);

				// Since the line misses in LLC, it should not be present in the
				// AIM. The AIM stats
				// are updated when the line is fetched from the LLC.

				// request to LLC, and a return data message
				int sizeBytesOutgoing = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES;
				// The line was in special invalid state, but failed a version
				// check.
				if (resp.invalidStateFailure) {
					sizeBytesOutgoing += SystemConstants.VISER_VERSION_BYTES;
				}
				updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, phase);
				updateTCCBroadcastMessage(sizeBytesOutgoing);

				int sizeBytesReturn = SystemConstants.DATA_MESSAGE_CONTROL_BYTES
						+ SystemConstants.DATA_MESSAGE_SIZE_BYTES
						+ SystemConstants.VISER_VERSION_BYTES;
				if (!params.ignoreFetchingReadBits()) {
					if (line.hasReadOffsets(id)) {
						sizeBytesReturn += SystemConstants.VISER_READ_METADATA_BYTES;
					}
				} else {
					clearReadBitsForPrivateLines(line);
				}
				if (!params.ignoreFetchingWriteBits()) {
					if (line.hasWrittenOffsets(id)) {
						sizeBytesReturn += SystemConstants.VISER_WRITE_METADATA_BYTES;
					}
				} else {
					clearWriteBitsForPrivateLines(line);
				}

				updateTrafficForOneNetworkMessage(1, sizeBytesReturn, phase);
				updateTCCBroadcastMessage(sizeBytesReturn);

				// Consider a control message sent to memory. Data message is handled during
				// memory hit.
				updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, ExecutionPhase.REGION_BODY);
				// updateTrafficForLLCToMemoryMessage(sizeBytesOutgoing, true);
				// updateMemoryAccesses(sizeBytesOutgoing, true);
				break;
			}
		}

		if (access.isRegularMemAccess()) { // regular read
			// Update read encoding only if it happens before a write
			long enc = access.getEncoding();
			if (!line.isOffsetWritten(id, enc)) {
				line.orReadEncoding(id, enc);
				line.updateReadSiteInfo(id, enc, access.siteInfo(), access.lastSiteInfo());
			}
		} else { // Lock + atomic accesses
			// We don't set metadata for these special accesses

			if ((resp.whereHit == CacheLevel.L3 || resp.whereHit == CacheLevel.MEMORY)
					&& line.getLockOwnerID() != id.get() && line.getLockOwnerID() >= 0) {
				// Account for a round trip latency and network cost (LLC to
				// owner core + response
				// from owner core to LLC)
				memoryCyclesElapsed(SystemConstants.L3_HIT_LATENCY, dmaResult);

				// request to LLC, and a return data message
				int sizeBytesOutgoing = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES;
				updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, phase);
				updateTCCBroadcastMessage(sizeBytesOutgoing);

				int sizeBytesReturn = SystemConstants.DATA_MESSAGE_CONTROL_BYTES
						+ SystemConstants.DATA_MESSAGE_SIZE_BYTES;
				updateTrafficForOneNetworkMessage(1, sizeBytesReturn, phase);
				updateTCCBroadcastMessage(sizeBytesReturn);
			}
		}

		// L1 and L2 states and versions should always match
		if (ViserSim.assertsEnabled) {
			Line l1Line = L1cache.getLine(line);
			Line l2Line = L2cache.getLine(line);
			assert l1Line.getState() == l2Line.getState() : "Event:" + ViserSim.totalEvents;
			assert l1Line.getVersion() == l2Line
					.getVersion() : "L1 and L2 cache line version should match, Event: "
							+ ViserSim.totalEvents;
			assert l1Line.getEpoch(id).equals(l2Line.getEpoch(id)) : "Event:"
					+ ViserSim.totalEvents;
		}

		if (ViserSim.xassertsEnabled()) {
			// This does not hold in Viser, since the L3 cache is not inclusive.
			// Verify.verifyInvalidLinesInLLC();
			Verify.verifyCacheIndexing();
			Verify.verifyPrivateCacheInclusivityAndVersions(this);
			Verify.verifyPerCoreMetadata(this);
			Verify.verifyExecutionCostBreakdown(this);
			if (params.useAIMCache()) {
				Verify.verifyAIMCacheInclusivity(this);
				Verify.verifyAIMCacheDuplicates(this);
			}
		}

		return dmaResult;
	} // end read()

	int computeVariableMessageSizeBytes(Line memLine) {
		int sizeBytes = SystemConstants.DATA_MESSAGE_SIZE_BYTES
				/* line size */ + machine.VISER_VARIABLE_MSG_HEADER
				+ SystemConstants.VISER_VERSION_BYTES; // version bytes
		for (int i = 0; i < params.numProcessors(); i++) {
			CpuId cpuId = new CpuId(i);
			PerCoreLineMetadata md = memLine.getPerCoreMetadata(cpuId);
			Processor<Line> p = machine.getProc(cpuId);
			assert md.epoch.getRegionId() <= p.getCurrentEpoch().getRegionId();
			if (md.epoch.equals(p.getCurrentEpoch())) {
				// read and write information for this processor, if it is
				// non-zero
				if (memLine.hasReadOffsets(cpuId)) {
					sizeBytes += SystemConstants.VISER_READ_METADATA_BYTES;
				}
				if (memLine.hasWrittenOffsets(cpuId)) {
					sizeBytes += SystemConstants.VISER_WRITE_METADATA_BYTES;
				}
			}
		}
		return sizeBytes;
	}

	int getAIMLineSize() {
		int numCores = params.numProcessors();
		int size = SystemConstants.VISER_VERSION_BYTES
				+ numCores * SystemConstants.VISER_READ_METADATA_BYTES;
		size += (1 + Math.log(numCores) / Math.log(2)) * numCores;
		return size;
	}

	// /** Account for a data message back from memory. */
	// void accountOffChipTraffic(Line memLine) {
	// double sizeBytes = computeVariableMessageSizeBytes(memLine);
	// updateTrafficForLLCToMemoryMessage(sizeBytes, true);
	//
	// }

	class RemoteReadResponse {
		boolean isShared = false;
		boolean providedData = false;
	}

	// full bit map, we want to be precise at the byte-level
	long getEncodingForAccess(DataAccess access) {
		long tmp = 0;
		ByteAddress start = new DataByteAddress(access.addr().get());
		for (int i = 0; i < access.size(); i++) {
			tmp |= getEncodingForOffset(start.lineOffset());
			start.incr();
		}
		return tmp;
	}

	private long getEncodingForOffset(int off) {
		return (1L << off);
	}

	// No need to fetch the line if the access misses a private cache
	public DataMemoryAccessResult lockReleaseWrite(final DataAccess access) {
		DataMemoryAccessResult dmaResult = new DataMemoryAccessResult();
		MemoryResponse<Line> resp = L1cache.requestWithSpecialInvalidState(this, access, false);
		if (params.useSpecialInvalidState()) {
			// Both cannot be true at the same time
			assert (resp.invalidStateHit ? !resp.invalidStateFailure : true)
					&& (resp.invalidStateFailure ? !resp.invalidStateHit : true);
		}
		if (resp.invalidStateHit || resp.invalidStateFailure) {
			stats.pc_TotalMemoryAccessesSpecialInvalidState.incr();
		}

		Line line = resp.lineHit;
		if (resp.whereHit.compareTo(llc()) < 0) {
			assert line
					.id() == id : "The owner of a private line should always be the current core";
			assert line.valid() && line.getLevel() == CacheLevel.L1;
			assert line.getEpoch(id).equals(getCurrentEpoch());
		}

		switch (resp.whereHit) {
			case L1: {
				if (access.isAtomic()) {
					stats.pc_l1d.pc_AtomicWriteHits.incr();
				} else {
					stats.pc_l1d.pc_LockWriteHits.incr();
				}
				memoryCyclesElapsed(SystemConstants.L1_HIT_LATENCY, dmaResult);
				break;
			}

			case L2: {
				if (access.isAtomic()) {
					stats.pc_l1d.pc_AtomicWriteMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_AtomicWriteHits.incr();
					}
				} else {
					stats.pc_l1d.pc_LockWriteMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_LockWriteHits.incr();
					}
				}
				memoryCyclesElapsed(SystemConstants.L2_HIT_LATENCY, dmaResult);
				break;
			}
			case L3: {
				if (access.isAtomic()) {
					stats.pc_l1d.pc_AtomicWriteMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_AtomicWriteMisses.incr();
					}
					stats.pc_l3d.pc_AtomicWriteHits.incr();
				} else {
					stats.pc_l1d.pc_LockWriteMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_LockWriteMisses.incr();
					}
					stats.pc_l3d.pc_LockWriteHits.incr();
				}
				// request to LLC, and no return message
				memoryCyclesElapsed(SystemConstants.L3_ACCESS, dmaResult);
				int sizeBytesOutgoing = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES;
				updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, ExecutionPhase.REGION_BODY);
				updateTCCBroadcastMessage(sizeBytesOutgoing);
				break;
			}
			case MEMORY: {
				if (access.isAtomic()) {
					stats.pc_l1d.pc_AtomicWriteMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_AtomicWriteMisses.incr();
					}
					stats.pc_l3d.pc_AtomicWriteMisses.incr();
				}
				{
					stats.pc_l1d.pc_LockWriteMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_LockWriteMisses.incr();
					}
					stats.pc_l3d.pc_LockWriteMisses.incr();
				}
				memoryCyclesElapsed(SystemConstants.MEMORY_ACCESS, dmaResult);
				// request to LLC, and no return message
				int sizeBytesOutgoing = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES;
				updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, ExecutionPhase.REGION_BODY);
				updateTCCBroadcastMessage(sizeBytesOutgoing);

				// Consider a control message sent to memory
				updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, ExecutionPhase.REGION_BODY);
				// updateTrafficForLLCToMemoryMessage(sizeBytesOutgoing, true);
				// updateMemoryAccesses(sizeBytesOutgoing, true);
				break;
			}
		}
		MemoryResponse<Line> sharedResp = getLineFromLLCOrMemory(line, false);
		assert sharedResp.lineHit != null;
		Line llcLine = sharedResp.lineHit;
		// Still keep the same owner
		llcLine.setLockOwnerID(id.get());
		line.setLockOwnerID(id.get());

		if (access.type == MemoryAccessType.ATOMIC_WRITE) {
			assert resp.whereHit.compareTo(llc()) < 0; // We expect this to hit
														// all the time since
			// there's an atomic
			// read ahead.
			// Invalidate the line in the last owner
			if (line.getLockOwnerID() >= 0 && line.getLockOwnerID() != id.get()) {
				Processor<Line> lastOwner = machine.getProc(new CpuId(line.getLockOwnerID()));
				Line l2Line = lastOwner.L2cache.getLine(line);
				if (l2Line != null && l2Line.valid()) {
					l2Line.invalidate();
					Line l1Line = lastOwner.L1cache.getLine(line);
					if (l1Line != null && l1Line.valid())
						l1Line.invalidate();
				}
			}
		}

		return dmaResult;
	}

	/** Make a write request. */
	public DataMemoryAccessResult write(final DataAccess access) {
		if (access.isAtomic()) {
			stats.pc_TotalAtomicWrites.incr();
			stats.pc_TotalAtomicAccesses.incr();
		} else if (access.isLockAccess()) {
			stats.pc_TotalLockWrites.incr();
			stats.pc_TotalLockAccesses.incr();
		} else {
			stats.pc_TotalDataWrites.incr();
			stats.pc_TotalMemoryAccesses.incr();
		}

		if (access.type() == MemoryAccessType.LOCK_REL_WRITE
				|| access.type() == MemoryAccessType.ATOMIC_WRITE) {
			return lockReleaseWrite(access);
		}

		// Model TCC write buffer
		if (access.isRegularMemAccess()) {
			tccWriteSet.add(access.addr().get());

			// 8K WB
			if (tccWriteSet.size() > SystemConstants.TCC_WB_SIZE_8K
					&& perRegionOverflow8K == TCCRegionsWithOverflow.NO_OVERFLOW) {
				perRegionOverflow8K = TCCRegionsWithOverflow.WB_OVERFLOWN;
			}
			if (perRegionOverflow8K != TCCRegionsWithOverflow.NO_OVERFLOW) {
				stats.pc_TCCNumSerializedMemoryAccesses8K.incr();
			}

			// 16K WB
			if (tccWriteSet.size() > SystemConstants.TCC_WB_SIZE_16K
					&& perRegionOverflow16K == TCCRegionsWithOverflow.NO_OVERFLOW) {
				perRegionOverflow16K = TCCRegionsWithOverflow.WB_OVERFLOWN;
			}
			if (perRegionOverflow16K != TCCRegionsWithOverflow.NO_OVERFLOW) {
				stats.pc_TCCNumSerializedMemoryAccesses16K.incr();
			}

			// 32K WB
			if (tccWriteSet.size() > SystemConstants.TCC_WB_SIZE_32K
					&& perRegionOverflow32K == TCCRegionsWithOverflow.NO_OVERFLOW) {
				perRegionOverflow32K = TCCRegionsWithOverflow.WB_OVERFLOWN;
			}
			if (perRegionOverflow32K != TCCRegionsWithOverflow.NO_OVERFLOW) {
				stats.pc_TCCNumSerializedMemoryAccesses32K.incr();
			}

			// 64K WB
			if (tccWriteSet.size() > SystemConstants.TCC_WB_SIZE_64K
					&& perRegionOverflow64K == TCCRegionsWithOverflow.NO_OVERFLOW) {
				perRegionOverflow64K = TCCRegionsWithOverflow.WB_OVERFLOWN;
			}
			if (perRegionOverflow64K != TCCRegionsWithOverflow.NO_OVERFLOW) {
				stats.pc_TCCNumSerializedMemoryAccesses64K.incr();
			}
		}

		DataMemoryAccessResult dmaResult = new DataMemoryAccessResult();

		MemoryResponse<Line> resp = L1cache.requestWithSpecialInvalidState(this, access, false);
		if (params.useSpecialInvalidState()) {
			// Both cannot be true at the same time
			assert (resp.invalidStateHit ? !resp.invalidStateFailure : true)
					&& (resp.invalidStateFailure ? !resp.invalidStateHit : true);
		}
		if (resp.invalidStateHit || resp.invalidStateFailure) {
			stats.pc_TotalMemoryAccessesSpecialInvalidState.incr();
		}

		Line line = resp.lineHit;

		// Remove current address from TCC vicitim cache since it has been reused
		tccVictimCache.remove(access.lineAddress().get());

		assert line.id() == id : "The owner of a private line should always be the current core";
		assert line.valid() && line.getLevel() == CacheLevel.L1;
		assert line.getEpoch(id).equals(getCurrentEpoch());

		long enc = access.getEncoding();
		if (access.isRegularMemAccess()) { // regular write
			// Handle write-after-read upgrade case, where a write follows an
			// earlier read,
			// but only if the write hits in L1.
			if (line.isOffsetReadOnly(id, enc) && resp.whereHit == CacheLevel.L1) {
				// Only handle WAR at the first pair of read-write
				// Write back the old read value and the read encoding to the L2
				// cache as backup.
				// Do not copy all the values in the whole line, since that is
				// incorrect.
				// Consider the following situation:
				// R1
				// W1
				// R2
				// W2
				// The second write back will overwrite the backed up read
				// possibly before the read
				// was validated
				// Only handle WAR at the first pair of read-write, i.e.
				// read-only offsets
				long readOnlyBits = ((line.getReadEncoding(id) & ~line.getWriteEncoding(id)) & enc);
				L2cache.handleWriteAfterReadUpgrade(line, readOnlyBits);

				// Ideally, the L2 line will already have the data that is read,
				// since it will be
				// fetched from
				// memory. So, we do not need to add the cost. Data is actually
				// flowing in from the
				// memory,
				// not the front-end.
				stats.pc_ViserWARUpgrades.incr();
			}
		}
		// set write encoding after computing costs
		line.setValue(access.addr(), access.value());

		ExecutionPhase phase = ExecutionPhase.REGION_BODY;

		switch (resp.whereHit) {
			case L1: {
				if (access.isAtomic()) {
					stats.pc_l1d.pc_AtomicWriteHits.incr();
				} else if (access.isLockAccess()) {
					stats.pc_l1d.pc_LockWriteHits.incr();
				} else {
					stats.pc_l1d.pc_WriteHits.incr();
				}

				if (access.isRegularMemAccess() && resp.invalidStateHit) {
					// The core had to talk with the LLC, L1 latency is included
					int cost;
					if (resp.invalidStateSharedHitLevel == CacheLevel.L3) {
						cost = SystemConstants.L3_HIT_LATENCY;
					} else {
						cost = SystemConstants.MEMORY_LATENCY;
					}
					memoryCyclesElapsed(cost, dmaResult);

					int sizeBytesOutgoing = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES
							+ SystemConstants.VISER_VERSION_BYTES;
					updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, phase);
					updateTCCBroadcastMessage(sizeBytesOutgoing);

					int sizeBytesReturn = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES;
					updateTrafficForOneNetworkMessage(1, sizeBytesReturn, phase);
					updateTCCBroadcastMessage(sizeBytesReturn);

					if (resp.invalidStateSharedHitLevel == CacheLevel.MEMORY) {
						// Outgoing message
						updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, phase);
						// updateTrafficForLLCToMemoryMessage(sizeBytesOutgoing, true);
						// updateMemoryAccesses(sizeBytesOutgoing, true);

						// // Return message. We are not actually fetching the
						// whole line into the
						// LLC,
						// // so that is why we are not accounting for metadata
						// for other cores.
						// Also,
						// // this is a invalid_state hit, so that means the
						// version matches.
						// int sizeMemBytesReturn =
						// MemorySystemConstants.DATA_MESSAGE_CONTROL_BYTES
						// +
						// MemorySystemConstants.DATA_MESSAGE_SIZE_BYTES +
						// MemorySystemConstants.VISER_VERSION_BYTES;
						// if (line.hasReadOffsets(id)) {
						// sizeMemBytesReturn +=
						// MemorySystemConstants.VISER_READ_METADATA_BYTES;
						// }
						// if (line.hasWrittenOffsets(id)) {
						// sizeMemBytesReturn +=
						// MemorySystemConstants.VISER_WRITE_METADATA_BYTES;
						// }

						// We do not need inclusivity, the LLC need not have the line cached.
						int sizeMemBytesReturn = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES;
						updateTrafficForOneNetworkMessage(1, sizeMemBytesReturn, phase);
						// updateTrafficForLLCToMemoryMessage(sizeMemBytesReturn, true);
						// updateMemoryAccesses(sizeMemBytesReturn, true);
					}
				} else {
					memoryCyclesElapsed(SystemConstants.L1_HIT_LATENCY, dmaResult);
				}
				break;
			}

			case L2: {
				if (access.isAtomic()) {
					stats.pc_l1d.pc_AtomicWriteMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_AtomicWriteHits.incr();
					}
				} else if (access.isLockAccess()) {
					stats.pc_l1d.pc_LockWriteMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_LockWriteHits.incr();
					}
				} else {
					stats.pc_l1d.pc_WriteMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_WriteHits.incr();
					}
				}

				if (access.isRegularMemAccess() && resp.invalidStateHit) {
					// The core had to talk with the LLC, L2 latency is included
					int cost;
					if (resp.invalidStateSharedHitLevel == CacheLevel.L3) {
						cost = SystemConstants.L3_HIT_LATENCY;
					} else {
						cost = SystemConstants.MEMORY_LATENCY;
					}
					memoryCyclesElapsed(cost, dmaResult);

					int sizeBytesOutgoing = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES
							+ SystemConstants.VISER_VERSION_BYTES;
					updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, phase);
					updateTCCBroadcastMessage(sizeBytesOutgoing);

					int sizeBytesReturn = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES;
					updateTrafficForOneNetworkMessage(1, sizeBytesReturn, phase);
					updateTCCBroadcastMessage(sizeBytesReturn);

					if (resp.invalidStateSharedHitLevel == CacheLevel.MEMORY) {
						// Outgoing message
						updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, phase);
						// updateTrafficForLLCToMemoryMessage(sizeBytesOutgoing, true);
						// updateMemoryAccesses(sizeBytesOutgoing, true);

						// // Return message. We are not actually fetching the
						// whole line into the
						// LLC,
						// // so that is why we are not accounting for metadata
						// for other cores.
						// Also,
						// // this is a invalid_state hit, so that means the
						// version matches.
						// int sizeMemBytesReturn =
						// MemorySystemConstants.DATA_MESSAGE_CONTROL_BYTES
						// +
						// MemorySystemConstants.DATA_MESSAGE_SIZE_BYTES +
						// MemorySystemConstants.VISER_VERSION_BYTES;
						// if (line.hasReadOffsets(id)) {
						// sizeMemBytesReturn +=
						// MemorySystemConstants.VISER_READ_METADATA_BYTES;
						// }
						// if (line.hasWrittenOffsets(id)) {
						// sizeMemBytesReturn +=
						// MemorySystemConstants.VISER_WRITE_METADATA_BYTES;
						// }

						// We do not need inclusivity, the LLC need not have the
						// line cached.
						int sizeMemBytesReturn = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES;
						updateTrafficForOneNetworkMessage(1, sizeMemBytesReturn, phase);
						// updateTrafficForLLCToMemoryMessage(sizeMemBytesReturn, true);
						// updateMemoryAccesses(sizeMemBytesReturn, true);
					}
				} else {
					memoryCyclesElapsed(SystemConstants.L2_HIT_LATENCY, dmaResult);
				}
				break;
			}

			case L3: {
				if (access.isAtomic()) {
					stats.pc_l1d.pc_AtomicWriteMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_AtomicWriteMisses.incr();
					}
					stats.pc_l3d.pc_AtomicWriteHits.incr();
				} else if (access.isLockAccess()) {
					stats.pc_l1d.pc_LockWriteMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_LockWriteMisses.incr();
					}
					stats.pc_l3d.pc_LockWriteHits.incr();
				} else {
					stats.pc_l1d.pc_WriteMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_WriteMisses.incr();
					}
					stats.pc_l3d.pc_WriteHits.incr();
				}

				// request to LLC, and a return data message
				int sizeBytesOutgoing = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES;

				if (params.useAIMCache() && access.isRegularMemAccess()) {
					if (resp.aimHit == CacheLevel.L3) {
						memoryCyclesElapsed(SystemConstants.L3_HIT_LATENCY, dmaResult);
					} else if (resp.aimHit == CacheLevel.MEMORY) {
						memoryCyclesElapsed(SystemConstants.MEMORY_LATENCY, dmaResult);

						// Consider a control message sent to memory
						updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, phase);
						// updateTrafficForLLCToMemoryMessage(sizeBytesOutgoing, true);
						// updateMemoryAccesses(sizeBytesOutgoing, true);

						// Account for the return message
						Line memLine = machine.memory.get(line.lineAddress().get());
						// If the memory line is null, it implies no metadata.
						if (memLine != null) {
							// accountOffChipTraffic(memLine);
						}
						// int sizeInBytes = SystemConstants.DATA_MESSAGE_CONTROL_BYTES
						// + getAIMLineSize();
						// updateMemoryAccesses(sizeInBytes, false);
					} else {
						throw new RuntimeException("Invalid hit level for AIM");
					}
				} else {
					memoryCyclesElapsed(SystemConstants.L3_HIT_LATENCY, dmaResult);
				}

				// The line was in special invalid state, but failed a version
				// check.
				if (resp.invalidStateFailure && access.isRegularMemAccess()) {
					sizeBytesOutgoing += SystemConstants.VISER_VERSION_BYTES;
				}
				updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, phase);
				updateTCCBroadcastMessage(sizeBytesOutgoing);

				int sizeBytesReturn = SystemConstants.DATA_MESSAGE_CONTROL_BYTES
						+ SystemConstants.DATA_MESSAGE_SIZE_BYTES
						+ SystemConstants.VISER_VERSION_BYTES;
				if (!params.ignoreFetchingReadBits()) {
					if (line.hasReadOffsets(id)) {
						sizeBytesReturn += SystemConstants.VISER_READ_METADATA_BYTES;
					}
				} else {
					clearReadBitsForPrivateLines(line);
				}
				if (!params.ignoreFetchingWriteBits()) {
					if (line.hasWrittenOffsets(id)) {
						sizeBytesReturn += SystemConstants.VISER_WRITE_METADATA_BYTES;
					}
				} else {
					clearWriteBitsForPrivateLines(line);
				}

				if (access.isRegularMemAccess()) {
					updateTrafficForOneNetworkMessage(1, sizeBytesReturn, phase);
					updateTCCBroadcastMessage(sizeBytesReturn);
				}
				break;
			}

			case MEMORY: {
				if (access.isAtomic()) {
					stats.pc_l1d.pc_AtomicWriteMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_AtomicWriteMisses.incr();
					}
					stats.pc_l3d.pc_AtomicWriteMisses.incr();
				} else if (access.isLockAccess()) {
					stats.pc_l1d.pc_LockWriteMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_LockWriteMisses.incr();
					}
					stats.pc_l3d.pc_LockWriteMisses.incr();
				} else {
					stats.pc_l1d.pc_WriteMisses.incr();
					if (params.useL2()) {
						stats.pc_l2d.pc_WriteMisses.incr();
					}
					stats.pc_l3d.pc_WriteMisses.incr();
				}

				memoryCyclesElapsed(SystemConstants.MEMORY_LATENCY, dmaResult);

				// Since the line misses in LLC, it should not be present in the
				// AIM. But the AIM
				// statistics are updated while fetching from the LLC.

				// request to LLC, and a return data message
				int sizeBytesOutgoing = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES;
				// The line was in special invalid state, but failed a version
				// check.
				if (resp.invalidStateFailure) {
					sizeBytesOutgoing += SystemConstants.VISER_VERSION_BYTES;
				}
				updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, phase);
				updateTCCBroadcastMessage(sizeBytesOutgoing);

				int sizeBytesReturn = SystemConstants.DATA_MESSAGE_CONTROL_BYTES
						+ SystemConstants.DATA_MESSAGE_SIZE_BYTES
						+ SystemConstants.VISER_VERSION_BYTES;
				if (!params.ignoreFetchingReadBits()) {
					if (line.hasReadOffsets(id)) {
						sizeBytesReturn += SystemConstants.VISER_READ_METADATA_BYTES;
					}
				} else {
					clearReadBitsForPrivateLines(line);
				}
				if (!params.ignoreFetchingWriteBits()) {
					if (line.hasWrittenOffsets(id)) {
						sizeBytesReturn += SystemConstants.VISER_WRITE_METADATA_BYTES;
					}
				} else {
					clearWriteBitsForPrivateLines(line);
				}
				updateTrafficForOneNetworkMessage(1, sizeBytesReturn, phase);
				updateTCCBroadcastMessage(sizeBytesReturn);

				// Consider a control message sent to memory. Return message is
				// considered in request()
				updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, phase);
				// updateTrafficForLLCToMemoryMessage(sizeBytesOutgoing, true);
				// updateMemoryAccesses(sizeBytesOutgoing, true);
				break;
			}
		}

		if (access.isRegularMemAccess()) {
			// set metadata
			// write through write bits (and MRU-bits) at first write of each
			// region when using
			// modified plru
			if (!line.hasWrittenOffsets(id) && params.evictCleanLineFirst() && params.usePLRU()) {
				Line l2Line = L2cache.getLine(line);
				l2Line.orWriteEncoding(id, enc);
				L2cache.setMRUBit(l2Line, false); // Ensure the invariance that
													// we set MRU bits
				// every time setting
				// write bits
			}
			line.orWriteEncoding(id, enc);
			line.updateWriteSiteInfo(id, enc, access.siteInfo(), access.lastSiteInfo());
		} else { // lock acquire write
			// We don't set metadata for special accesses

			assert access.type == MemoryAccessType.LOCK_ACQ_WRITE;
			assert resp.whereHit.compareTo(llc()) < 0;
			// We expect this to hit all the time since there's a lock acquire
			// read ahead.
			MemoryResponse<Line> sharedResp = getLineFromLLCOrMemory(line, false);
			assert sharedResp.lineHit != null;
			Line llcLine = sharedResp.lineHit;

			// Invalidate the line in the last owner
			if (line.getLockOwnerID() >= 0 && line.getLockOwnerID() != id.get()) {
				Processor<Line> lastOwner = machine.getProc(new CpuId(line.getLockOwnerID()));
				Line l2Line = lastOwner.L2cache.getLine(line);
				if (l2Line != null && l2Line.valid()) {
					l2Line.invalidate();
					Line l1Line = lastOwner.L1cache.getLine(line);
					if (l1Line != null && l1Line.valid())
						l1Line.invalidate();
				}
			}

			line.setLockOwnerID(id.get());
			llcLine.setLockOwnerID(id.get()); // Current core owns the lock
		}

		if (ViserSim.assertsEnabled && access.type() != MemoryAccessType.LOCK_REL_WRITE) {
			// Since we invalidate the private line on a release that misses in
			// the private cache to
			// simulate not
			// bringing in a line
			Line l1Line = L1cache.getLine(line);
			Line l2Line = L2cache.getLine(line);
			assert l1Line.getState() == l2Line.getState();
			assert l1Line.getVersion() == l2Line
					.getVersion() : "L1 and L2 cache line version should match, Total events: "
							+ ViserSim.totalEvents;
			assert l1Line.getEpoch(id).equals(l2Line.getEpoch(id));
		}

		if (ViserSim.xassertsEnabled()) {
			// This does not hold in Viser, since the L3 cache is not inclusive.
			// Verify.verifyInvalidLinesInLLC();
			Verify.verifyCacheIndexing();
			Verify.verifyPrivateCacheInclusivityAndVersions(this);
			Verify.verifyPerCoreMetadata(this);
			Verify.verifyExecutionCostBreakdown(this);
			if (params.useAIMCache()) {
				Verify.verifyAIMCacheInclusivity(this);
				Verify.verifyAIMCacheDuplicates(this);
			}
		}

		return dmaResult;
	} // end write()

	void clearReadBitsForPrivateLines(Line line) {
		assert line.getLevel() == CacheLevel.L1;
		line.clearReadEncoding(id);
		if (params.useL2()) {
			Line l2Line = L2cache.getLine(line);
			assert l2Line != null;
			l2Line.clearReadEncoding(id);
		}
	}

	void clearWriteBitsForPrivateLines(Line line) {
		assert line.getLevel() == CacheLevel.L1;
		line.clearWriteEncoding(id);
		if (params.useL2()) {
			Line l2Line = L2cache.getLine(line);
			assert l2Line != null;
			l2Line.clearWriteEncoding(id);
		}
	}

	public Epoch getCurrentEpoch() {
		return machine.getEpoch(id);
	}

	/**
	 * Check for precise conflicts between two cache lines, ignoring the current processor.
	 *
	 * @param b
	 * @param earlyReadValidation
	 */
	void checkPreciseWriteReadConflicts(Line sharedLine, Line privLine, ExecutionPhase phase) {
		if (!(!params.isHttpd()
				&& (!ViserSim.modelOnlyROI() || ViserSim.getPARSECPhase() == PARSEC_PHASE.IN_ROI)
				|| ViserSim.getPARSECPhase() == PARSEC_PHASE.IN_SERVER_ROI)) { // Not
																				// in
																				// ROIs
			return;
		}

		stats.pc_ConflictCheckAttempts.incr();
		long existingReads = privLine.getReadEncoding(id);
		for (int i = 0; i < params.numProcessors(); i++) {
			if (i == id.get()) {
				continue; // ignore the same processor
			}
			CpuId cpuId = new CpuId(i);
			Processor<Line> p = machine.getProc(cpuId);
			PerCoreLineMetadata md = sharedLine.getPerCoreMetadata(cpuId);
			assert md != null;
			assert md.epoch.getRegionId() <= p.getCurrentEpoch().getRegionId();
			if (md.epoch.equals(p.getCurrentEpoch())) { // The region is ongoing
				long sharedWrites = sharedLine.getWriteEncoding(cpuId);
				if ((sharedWrites & existingReads) != 0) {
					boolean preciseConflict = true;
					if (params.siteTracking()) {
						preciseConflict = reportConflict(phase, "write", "read", sharedLine, cpuId,
								privLine, sharedWrites, existingReads);
					}
					if (preciseConflict) {
						stats.pc_PreciseConflicts.incr();
						updatePhaseTolerableConflicts(phase);
						updateTypeTolerableConflicts(ConflictType.WR);
						// Pause the current(reader) core at a precise
						// write-read conflict
						handleConflict(cpuId);
						return;
					}
				}
			}
		}
	}

	private boolean reportConflict(ExecutionPhase phase, String preop, String curop, Line preline,
			CpuId cpuId, Line curline, long preenc, long curenc) {
		/*
		 * rtnCoveredSet.clear(); srcCoveredSet.clear();
		 */
		boolean preciseConflict = false;
		boolean print = params.printConflictingSites();
		long enc = preenc & curenc;
		int[] preSiIndex;
		int[] curSiIndex;
		int[] preLastSiIndex;
		int[] curLastSiIndex;
		if (preop.equals("write")) {
			preSiIndex = preline.getWriteSiteInfo(cpuId);
			preLastSiIndex = preline.getWriteLastSiteInfo(cpuId);
		} else {
			preSiIndex = preline.getReadSiteInfo(cpuId);
			preLastSiIndex = preline.getReadLastSiteInfo(cpuId);
		}
		if (curop.equals("write")) {
			curSiIndex = curline.getWriteSiteInfo(id);
			curLastSiIndex = curline.getWriteLastSiteInfo(id);
		} else {
			curSiIndex = curline.getReadSiteInfo(id);
			curLastSiIndex = curline.getReadLastSiteInfo(id);
		}
		if (print)
			System.out.println("[visersim] During " + phase + ", a " + preop + "-" + curop
					+ " conflict is detected at " + curline.addr.lineAddr + ".");
		/*
		 * boolean noSrcInfo = false; boolean noFuncName = false;
		 */
		for (int off = 0; off < SystemConstants.LINE_SIZE(); off++) {
			if (((1L << off) & enc) != 0) {
				SiteInfoEntry curSi = machine.siteInfo.get(curSiIndex[off]);
				SiteInfoEntry curLastSi = machine.siteInfo.get(curLastSiIndex[off]);
				SiteInfoEntry preSi = machine.siteInfo.get(preSiIndex[off]);
				SiteInfoEntry preLastSi = machine.siteInfo.get(preLastSiIndex[off]);
				int curfno = curSi.fileIndexNo;
				int curlno = curSi.lineNo;
				int currno = curSi.routineIndexNo;
				int prefno = preSi.fileIndexNo;
				int prelno = preSi.lineNo;
				int prerno = preSi.routineIndexNo;
				/*
				 * rtnCoveredSet.add(currno); rtnCoveredSet.add(prerno); srcCoveredSet.add(curfno);
				 * srcCoveredSet.add(prefno);
				 */
				/*
				 * if (curfno == 0 || curlno == 0 || prefno == 0 || prelno == 0) { noSrcInfo = true;
				 * // break; } if (currno == 0 || prerno == 0) noFuncName = true;
				 */
				if (curlno != 0 && prelno != 0) {
					preciseConflict = true;
					if (print) {
						System.out.println("\tcurrent " + curop + " by " + curline.id() + " at "
								+ curfno + ":" + curlno + ":" + currno + " (callerSite: "
								+ curLastSi.fileIndexNo + ":" + curLastSi.lineNo + ").");
						System.out.println("\tprevious " + preop + " by " + cpuId + " at " + prefno
								+ ":" + prelno + ":" + prerno + " (callerSite: "
								+ preLastSi.fileIndexNo + ":" + preLastSi.lineNo + ").");
					}
				}
				machine.updateConflictCounters(curfno, curlno, currno, prefno, prelno, prerno,
						curLastSi.fileIndexNo, curLastSi.lineNo, preLastSi.fileIndexNo,
						preLastSi.lineNo);
			}
		}
		// reset the counters to allow counting for other lines.
		machine.resetConflictCounter();
		if (print)
			System.out.println(
					"=================================== Conflicts =======================================");

		/*
		 * for (int fno : srcCoveredSet) { machine.srcCoverage[fno]++; } for (int rno :
		 * rtnCoveredSet) { machine.rtnCoverage[rno]++; } if (noSrcInfo)
		 * stats.pc_ConflictsWithoutSrcInfo.incr(); if (noFuncName)
		 * stats.pc_ConflictsWithoutFuncName.incr();
		 */
		return preciseConflict;
	}

	void handleConflict(CpuId cpuId) {
		if (!regionWithExceptions) {
			if (!regionConflicted) {
				regionConflicted = true;
				stats.pc_RegionsWithTolerableConflicts.incr();

				stats.pc_RegionsWithExceptions.incr();
				regionWithExceptions = true;
			}
		}
	}

	/**
	 * Check for precise conflicts between two cache lines, ignoring the current processor.
	 */
	// used at precommit, early-pre-commit
	void checkPreciseConflicts(Line sharedLine, Line privLine, ExecutionPhase phase) {
		if (!(!params.isHttpd()
				&& (!ViserSim.modelOnlyROI() || ViserSim.getPARSECPhase() == PARSEC_PHASE.IN_ROI)
				|| ViserSim.getPARSECPhase() == PARSEC_PHASE.IN_SERVER_ROI)) { // Not
																				// in
																				// ROIs
			return;
		}

		stats.pc_ConflictCheckAttempts.incr();
		long existingWrites = privLine.getWriteEncoding(id);
		// long existingReads = privLine.getReadEncoding(id);
		for (int i = 0; i < params.numProcessors(); i++) {
			if (i == id.get()) {
				continue; // ignore the same processor
			}
			CpuId cpuId = new CpuId(i);
			Processor<Line> p = machine.getProc(cpuId);
			PerCoreLineMetadata md = sharedLine.getPerCoreMetadata(cpuId);
			assert md != null;
			assert md.epoch.getRegionId() <= p.getCurrentEpoch().getRegionId();
			if (md.epoch.equals(p.getCurrentEpoch())) { // The region is ongoing
				long sharedWrites = sharedLine.getWriteEncoding(cpuId);
				long sharedReads = sharedLine.getReadEncoding(cpuId);
				if ((sharedReads & existingWrites) != 0) {
					boolean preciseConflict = true;
					if (params.siteTracking()) {
						preciseConflict = reportConflict(phase, "read", "write", sharedLine, cpuId,
								privLine, sharedReads, existingWrites);
					}
					if (preciseConflict) {
						stats.pc_PreciseConflicts.incr();
						updatePhaseTolerableConflicts(phase);
						updateTypeTolerableConflicts(ConflictType.RW);
						handleConflict(cpuId);
						return;
					}
				} else if ((sharedWrites & existingWrites) != 0) {
					boolean preciseConflict = true;
					if (params.siteTracking()) {
						preciseConflict = reportConflict(phase, "write", "write", sharedLine, cpuId,
								privLine, sharedWrites, existingWrites);
					}
					if (preciseConflict) {
						stats.pc_PreciseConflicts.incr();
						updatePhaseTolerableConflicts(phase);
						updateTypeTolerableConflicts(ConflictType.WW);
						handleConflict(cpuId);
						return;
					}
				}
			}
		}
	}

	/**
	 * Supposed to be executed only while fetching from memory. This will clear old access
	 * information for past epochs.
	 */
	Line clearAccessEncoding(Line sharedLine) {
		int count = 0;
		for (int i = 0; i < params.numProcessors(); i++) {
			CpuId cpuId = new CpuId(i);
			Processor<Line> p = machine.getProc(cpuId);
			PerCoreLineMetadata md = sharedLine.getPerCoreMetadata(cpuId);
			assert md != null;
			assert md.epoch.getRegionId() <= p.getCurrentEpoch().getRegionId();
			if (md.epoch.getRegionId() < p.getCurrentEpoch().getRegionId()) {
				sharedLine.clearReadEncoding(cpuId);
				sharedLine.clearWriteEncoding(cpuId);
				count++;
			}
		}
		if (count == params.numProcessors()) { // No core has valid metadata
			sharedLine.clearAIMMD();
		}
		return sharedLine;
	}

	// Cannot use hashCode to search Java collections without overriding
	// equals() and hashCode(), since we create/use different line objects
	public Long getDeferredWriteMetadata(Line l) {
		Iterator<Map.Entry<Long, Long>> entries = wrMdDeferredDirtyLines.entrySet().iterator();
		while (entries.hasNext()) {
			Map.Entry<Long, Long> entry = entries.next();
			if (l.lineAddress().get() == entry.getKey()) {
				return entry.getValue();
			}
		}
		return null;
	}

	public void removeDeferredWriteLine(Line l) {
		Iterator<Map.Entry<Long, Long>> entries = wrMdDeferredDirtyLines.entrySet().iterator();
		while (entries.hasNext()) {
			Map.Entry<Long, Long> entry = entries.next();
			if (l.lineAddress().get() == entry.getKey()) {
				entries.remove();
				return;
			}
		}
		assert false;
	}

	/**
	 * Write back write encoding and dirty values to shared memory (LLC, then main memory). Also
	 * form epochs for later lookups.
	 */
	private void sendDirtyValuesToLLC() {
		final HashSet<Long> dirtyL1Lines = new HashSet<Long>();

		for (Deque<Line> set : L1cache.sets) {
			for (Line l : set) {
				if (l.hasWrittenOffsets(id)) {
					assert l.valid() : "Written line has to be VALID";
					assert l.getEpoch(id).equals(getCurrentEpoch());

					dirtyL1Lines.add(l.lineAddress().get()); // We want to skip L2 lines
					L3cache.updateWriteInfoInLLC(this, l, ExecutionPhase.PRE_COMMIT_L1);
				}
			}
		}

		if (params.useL2()) {
			// Visit L2-only dirty lines, and skip L1 dirty lines.
			for (Deque<Line> set : L2cache.sets) {
				for (Line l : set) {
					if (l.hasWrittenOffsets(id)) {
						assert l.valid() : "Dirty line has to be VALID.";
						assert l.getEpoch(id).equals(getCurrentEpoch());
						if (!dirtyL1Lines.contains(l.lineAddress().get())) {
							L3cache.updateWriteInfoInLLC(this, l, ExecutionPhase.PRE_COMMIT_L2);
						}
					}
				}
			}
		}
	}

	/**
	 * Check read/write-write conflicts for written lines and compute costs
	 */
	private boolean preCommitWriteBackDirtyLines(final Processor<Line> proc) {
		final HashSet<Long> dirtyL1Lines = new HashSet<Long>();

		// We can assume parallelization while sending messages, and hence account for the slowest
		// message in a batch for estimating the cycle cost. But that is not the default for
		// tracking execution cost.
		double bandwidthBasedCost = 0;
		// We consider these to be streaming operations. So that is why, we add up all the bytes and
		// compute network traffic in terms of flits.
		int totalSizeInBytes = 0;

		boolean written = false; // Track whether there is at least one written line
		// phase = ExecutionPhase.PRE_COMMIT_L1;
		for (Deque<Line> set : L1cache.sets) {
			for (Line l : set) {
				if (l.hasWrittenOffsets(id)) {
					if (!written) {
						written = true;
					}

					assert l.valid() : "Written line has to be VALID";
					assert l.getEpoch(id).equals(getCurrentEpoch());

					dirtyL1Lines.add(l.lineAddress().get()); // We want to skip L2 lines

					// Compute size of a message to LLC. We do not need to send
					// the version, we can just increment it
					int sizeInBytes = SystemConstants.TAG_BYTES
							+ SystemConstants.VISER_WRITE_METADATA_BYTES;

					// send values after read validation
					if (!params.deferWriteBacks()) {
						// size of values sent
						sizeInBytes += Long.bitCount(l.getWriteEncoding(id));
					}
					totalSizeInBytes += sizeInBytes;

					boolean hit = L3cache.checkConflictsForWrittenLines(proc, l,
							ExecutionPhase.PRE_COMMIT_L1);

					// Check if it is an LLC miss. This is not a streaming operation.
					if (!hit) {
						updateTrafficForOneNetworkMessage(1, sizeInBytes,
								ExecutionPhase.PRE_COMMIT);
						// updateTrafficForLLCToMemoryMessage(sizeInBytes, false);
						// updateMemoryAccesses(getAIMLineSize(), false);
					}

					int cost = hit ? SystemConstants.L3_ACCESS : SystemConstants.MEMORY_ACCESS;
					stats.pc_ExecDrivenCycleCount.incr(cost);
					updatePhaseExecDrivenCycleCost(ExecutionPhase.PRE_COMMIT, cost);
					// Count execution cycles but taking into account bandwidth
					bandwidthBasedCost += (sizeInBytes * SystemConstants.LLC_MULTIPLIER);
					if (!hit) {
						bandwidthBasedCost += (sizeInBytes * SystemConstants.MEM_MULTIPLIER);
					}
				}
			}
		}

		int bwCost = (int) Math.ceil(bandwidthBasedCost);
		stats.pc_BandwidthDrivenCycleCount.incr(bwCost);
		updatePhaseBWDrivenCycleCost(ExecutionPhase.PRE_COMMIT, bwCost);

		stats.pc_TCCCycleCount8K.incr(bwCost);
		stats.pc_TCCCycleCount16K.incr(bwCost);
		stats.pc_TCCCycleCount32K.incr(bwCost);
		stats.pc_TCCCycleCount64K.incr(bwCost);

		// Model TCC stall cycles since region has overflowed
		if (perRegionOverflow8K != TCCRegionsWithOverflow.NO_OVERFLOW) {
			tccPerRegionStalledCycles8K += SystemConstants.L3_HIT_LATENCY;
		}
		if (perRegionOverflow16K != TCCRegionsWithOverflow.NO_OVERFLOW) {
			tccPerRegionStalledCycles16K += SystemConstants.L3_HIT_LATENCY;

		}
		if (perRegionOverflow32K != TCCRegionsWithOverflow.NO_OVERFLOW) {
			tccPerRegionStalledCycles32K += SystemConstants.L3_HIT_LATENCY;

		}
		if (perRegionOverflow64K != TCCRegionsWithOverflow.NO_OVERFLOW) {
			tccPerRegionStalledCycles64K += SystemConstants.L3_HIT_LATENCY;

		}

		bandwidthBasedCost = 0;

		// Not very meaningful for number of messages
		updateTrafficForOneNetworkMessage(1, totalSizeInBytes, ExecutionPhase.PRE_COMMIT);
		updateTCCBroadcastMessage(totalSizeInBytes);

		totalSizeInBytes = 0;

		if (params.useL2()) {
			// phase = ExecutionPhase.PRE_COMMIT_L2;
			// Visit L2-only dirty lines, and skip L1 dirty lines.
			for (Deque<Line> set : L2cache.sets) {
				for (Line l : set) {
					if (l.hasWrittenOffsets(id)) {
						assert l.valid() : "Dirty line has to be VALID.";
						assert l.getEpoch(id).equals(getCurrentEpoch());

						if (!dirtyL1Lines.contains(l.lineAddress().get())) {
							if (!written) {
								written = true;
							}

							// Compute size of a message to LLC. We do not need to send the version,
							// we can just increment it
							int sizeBytes = SystemConstants.TAG_BYTES
									+ SystemConstants.VISER_WRITE_METADATA_BYTES;
							if (!params.deferWriteBacks()) {
								sizeBytes += Long.bitCount(l.getWriteEncoding(id));
							}
							totalSizeInBytes += sizeBytes;

							boolean hit = L3cache.checkConflictsForWrittenLines(proc, l,
									ExecutionPhase.PRE_COMMIT_L2);

							// Check if it is an LLC miss
							if (!hit) {
								updateTrafficForOneNetworkMessage(1, sizeBytes,
										ExecutionPhase.PRE_COMMIT);
								// updateTrafficForLLCToMemoryMessage(sizeBytes, false);
								// updateMemoryAccesses(getAIMLineSize(), false);
							}

							int cost = hit ? SystemConstants.L3_ACCESS
									: SystemConstants.MEMORY_ACCESS;
							stats.pc_ExecDrivenCycleCount.incr(cost);
							updatePhaseExecDrivenCycleCost(ExecutionPhase.PRE_COMMIT, cost);
							// Count execution cycles but taking into account bandwidth
							bandwidthBasedCost += (sizeBytes * SystemConstants.LLC_MULTIPLIER);
							if (!hit) {
								bandwidthBasedCost += (sizeBytes * SystemConstants.MEM_MULTIPLIER);
							}
						}
					}
				}
			}

			bwCost = (int) Math.ceil(bandwidthBasedCost);
			stats.pc_BandwidthDrivenCycleCount.incr(bwCost);
			updatePhaseBWDrivenCycleCost(ExecutionPhase.PRE_COMMIT, bwCost);

			stats.pc_TCCCycleCount8K.incr(bwCost);
			stats.pc_TCCCycleCount16K.incr(bwCost);
			stats.pc_TCCCycleCount32K.incr(bwCost);
			stats.pc_TCCCycleCount64K.incr(bwCost);
			// Model TCC stall cycles since region has overflowed
			if (perRegionOverflow8K != TCCRegionsWithOverflow.NO_OVERFLOW) {
				tccPerRegionStalledCycles8K += SystemConstants.L3_HIT_LATENCY;
			}
			if (perRegionOverflow16K != TCCRegionsWithOverflow.NO_OVERFLOW) {
				tccPerRegionStalledCycles16K += SystemConstants.L3_HIT_LATENCY;
			}
			if (perRegionOverflow32K != TCCRegionsWithOverflow.NO_OVERFLOW) {
				tccPerRegionStalledCycles32K += SystemConstants.L3_HIT_LATENCY;
			}
			if (perRegionOverflow64K != TCCRegionsWithOverflow.NO_OVERFLOW) {
				tccPerRegionStalledCycles64K += SystemConstants.L3_HIT_LATENCY;
			}

			// Not very meaningful for counting network messages
			updateTrafficForOneNetworkMessage(1, totalSizeInBytes, ExecutionPhase.PRE_COMMIT);
			updateTCCBroadcastMessage(totalSizeInBytes);
		}

		return written;
	}

	static class ReadValidationResponse {
		boolean versionsMatch;
		int numValidatedLines;
		boolean overlap;
		// boolean wrConlictbyEvictFound = false;

		public ReadValidationResponse() {
			versionsMatch = true;
			numValidatedLines = 0;
			overlap = false;
		}
	};

	// Return true is a write bit is set in an ongoing region by some other core
	boolean checkIfWriteBitIsSet(Line sharedLine) {
		for (Processor<Line> p : allProcessors) {
			if (p.id.equals(this.id)) {
				continue;
			}
			long writeMd = sharedLine.getWriteEncoding(p.id);
			if (Long.bitCount(writeMd) > 0) {
				return true;
			}
		}
		return false;
	}

	private ReadValidationResponse rvValidationMergedHelper(boolean retryAttempt) {
		ReadValidationResponse rvResp;
		if (params.useL2()) { // Do validation on the L2 lines updated with L1
								// line's read values
			if (!retryAttempt) { // Merge the read bits only on the first
									// attempt
				rvMergeReadInformationFromL1ToL2();
			}
			rvResp = rvPrivateCacheMergedHelper(L2cache, retryAttempt);
		} else {
			rvResp = rvPrivateCacheMergedHelper(L1cache, retryAttempt);
		}
		if (rvResp.versionsMatch) { // Read validation is successful
			// Account for the cost of refetching the Bloom filter if the read
			// validation set and
			// the write signature
			// overlaps
			if (params.skipValidatingReadLines() && params.useBloomFilter() && rvResp.overlap) {
				int sizeBytes = SystemConstants.BLOOM_FILTER_LLC_MESSAGE;
				updateTrafficForOneNetworkMessage(1, sizeBytes, ExecutionPhase.READ_VALIDATION);
			}
		}
		return rvResp;
	}

	private ReadValidationResponse rvPrivateCacheMergedHelper(HierarchicalCache<Line> cache,
			boolean retryAttempt) {
		ReadValidationResponse vvResp = new ReadValidationResponse();

		// We are assuming a parallelism in sending requests to the LLC
		final int BATCH_SIZE = 4;

		int l2LineCounter = 0;
		int numLinesValidated = 0;
		int maxBatchExecLatency = 0; // number of cycles based on pre-defined
										// constants
		double memBatchSizeBytes = 0; // number of bytes that need to go to
										// memory in a batch
		CacheLevel whereHitInBatch = CacheLevel.L3; // number of cycles based on
													// bandwidth data

		int totalSizeBytes = 0;
		boolean rdValAndWriteSignatureOverlap = false;

		for (Deque<Line> set : cache.sets) {
			for (Line l : set) {
				if (!l.valid() || !l.hasReadOffsets(id)) {
					continue;
				}
				// Line is valid and has some reads

				// A read line needs to be validated only if the Bloom filter
				// tells the core that
				// the line has been
				// updated during the region.
				if (params.skipValidatingReadLines() && params.useBloomFilter()) {
					stats.pc_BloomFilterTotalEnergy.incr(SystemConstants.BLOOM_FILTER_READ_ENERGY);
					stats.pc_BloomFilterReadEnergy.incr(SystemConstants.BLOOM_FILTER_READ_ENERGY);

					if (!bf.contains(l.lineAddress().get())) {
						continue;
					}
				}

				// There is a read line that is updated by a remote core, so
				// read validation needs
				// to repeat at least one more time after fetching the write
				// signature, according to
				// the
				// do-while-retry algorithm. We do not implement that algorithm
				// faithfully since the
				// simulator is single-threaded.
				rdValAndWriteSignatureOverlap = true;

				int l2Version = l.getVersion();
				long readEnc = l.getReadEncoding(id);
				// Need the tag bits, since the LLC/memory might reply
				// asynchronously
				int sizeBytes = SystemConstants.DATA_MESSAGE_CONTROL_BYTES
						+ SystemConstants.TAG_BYTES + Long.bitCount(readEnc);

				// Get the corresponding line from memory or LLC
				MemoryResponse<Line> resp = L3cache.requestLineFromLLCOrMemory(this, l, true,
						ExecutionPhase.READ_VALIDATION);
				Line sharedLine = resp.lineHit;
				assert sharedLine != null && sharedLine.getLevel() == CacheLevel.L3;

				int sharedVersion = sharedLine.getVersion();

				if (resp.whereHit == CacheLevel.L3) {
					maxBatchExecLatency = Math.max(maxBatchExecLatency, SystemConstants.L3_ACCESS);
				} else {
					assert resp.whereHit == CacheLevel.MEMORY;
					maxBatchExecLatency = Math.max(maxBatchExecLatency,
							SystemConstants.MEMORY_ACCESS);
					whereHitInBatch = CacheLevel.MEMORY;

					// LLC will forward the message to memory
					int sizeMemBytes = SystemConstants.DATA_MESSAGE_CONTROL_BYTES
							+ SystemConstants.TAG_BYTES + SystemConstants.VISER_VERSION_BYTES;
					updateTrafficForOneNetworkMessage(1, sizeMemBytes,
							ExecutionPhase.READ_VALIDATION);
					// updateTrafficForLLCToMemoryMessage(sizeMemBytes, true);
					// updateMemoryAccesses(getAIMLineSize(), true);

					memBatchSizeBytes += sizeMemBytes;
				}

				// In case of a version match, the LLC responds with a NACK if a
				// write bit is set in
				// the AIM cache,
				// indicating a potential write-read conflict. Otherwise, RCC
				// could miss
				// serializability violations.
				// Validation is not retried in case a conflict is observed
				// since the versions
				// already match.
				if (l2Version == sharedVersion && !retryAttempt) {
					if (checkIfWriteBitIsSet(sharedLine)) {
						stats.pc_potentialWrRdValConflicts.incr();

						// One LLC-to-core control message
						int sizeIncomingMessage = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES;
						updateTrafficForOneNetworkMessage(1, sizeIncomingMessage,
								ExecutionPhase.READ_VALIDATION);
						// The CC then compares the version, the data values, and the (core's) read
						// bits and (AIM's) write bits.
						// One core-to-LLC message
						// We do not need to send version and data bytes, since
						// the LLC has precise bits in the cache
						int sizeOutgoingMessage = SystemConstants.DATA_MESSAGE_CONTROL_BYTES
								+ SystemConstants.VISER_READ_METADATA_BYTES;
						updateTrafficForOneNetworkMessage(1, sizeOutgoingMessage,
								ExecutionPhase.READ_VALIDATION);

						// Check for a precise write-read conflict
						checkPreciseWriteReadConflicts(sharedLine, l,
								ExecutionPhase.READ_VALIDATION);

						// We do not account for the performance, since we
						// expect this case to be
						// rare and to be on the
						// slow path
					}
				}

				boolean preciseConflictFound = false;
				if (l2Version != sharedVersion) {
					assert l2Version < sharedVersion : "Local version should be smaller it seems.";

					// Since there's no early writing back during pre-commit, version mismatch
					// definitely indicates the existence of remote writers.
					if (l.hasWrittenOffsets(id)) {
						// The current core is the last writer, but there are remote writers as
						// well. Still need to setConcurrentRemoteWrite for self-invalidation during
						// post-commit.
						l.setConcurrentRemoteWrite();
					}

					l.setVersion(sharedVersion);

					vvResp.versionsMatch = false;

					// If it misses in the LLC, then the reply has to come from memory
					if (resp.whereHit == CacheLevel.MEMORY) {
						updateTrafficForOneNetworkMessage(1, sizeBytes,
								ExecutionPhase.READ_VALIDATION);
						// updateTrafficForLLCToMemoryMessage(sizeBytes, true);
						// updateMemoryAccesses(getAIMLineSize(), true);
					}

					// Mismatched versions, so the LLC replies with the values that are read.
					// These are not streaming operations.
					updateTrafficForOneNetworkMessage(1, sizeBytes, ExecutionPhase.READ_VALIDATION);

					if (!params.ignoreFetchingDeferredLinesDuringReadValidation()) {
						// Before value validation, make sure that the LLC has
						// the up-to-date values
						// This might be high if there are lots of true
						// conflicts or false positives
						if (params.deferWriteBacks() && sharedLine.isLineDeferred()
								&& sharedLine.getDeferredLineOwnerID() != id.get()) {
							fetchDeferredLineFromPrivateCache(sharedLine, true, false);
						}
					}

					preciseConflictFound = valueValidateReadLine(ExecutionPhase.READ_VALIDATION, l,
							sharedLine);
				}

				l2LineCounter++;
				numLinesValidated++;

				// Execution cycles should be over one batch of concurrent
				// messages since the
				// latency
				// depends on where the shared line hits (LLC or memory).
				if (l2LineCounter % BATCH_SIZE == 0) {
					stats.pc_ExecDrivenCycleCount.incr(maxBatchExecLatency);
					updatePhaseExecDrivenCycleCost(ExecutionPhase.READ_VALIDATION,
							maxBatchExecLatency);

					int batchSizeBytes = SystemConstants.VISER_RV_MESSAGE_SIZE_BYTES;
					totalSizeBytes += batchSizeBytes;

					// Count execution cycles but taking into account bandwidth
					long bandwidthBasedLatency = (long) Math
							.ceil(batchSizeBytes * SystemConstants.LLC_MULTIPLIER);
					if (whereHitInBatch == CacheLevel.MEMORY) {
						// assert memBatchSizeBytes < batchSizeBytes;
						bandwidthBasedLatency += (long) Math
								.ceil(memBatchSizeBytes * SystemConstants.MEM_MULTIPLIER);
					}
					stats.pc_BandwidthDrivenCycleCount.incr(bandwidthBasedLatency);
					updatePhaseBWDrivenCycleCost(ExecutionPhase.READ_VALIDATION,
							bandwidthBasedLatency);

					maxBatchExecLatency = 0;
					memBatchSizeBytes = 0;
					l2LineCounter = 0;
					whereHitInBatch = CacheLevel.L3;
				}
				if (preciseConflictFound) {
					// update counters
					stats.pc_FailedValidations.incr();
					if (!regionWithExceptions) {
						stats.pc_RegionsWithFRVs.incr();
						// After pre-commit
						stats.pc_RegionsWithFRVsAfterPrecommit.incr();
						if (!regionHasDirtyEvictionBeforeFRV && hasDirtyEviction) {
							stats.pc_RegionHasDirtyEvictionBeforeFRV.incr();
							regionHasDirtyEvictionBeforeFRV = true;
						}

						stats.pc_ExceptionsByFRVs.incr();
						stats.pc_RegionsWithExceptionsByFRVs.incr();

						stats.pc_RegionsWithExceptions.incr();
						regionWithExceptions = true;
					}
				}
			}
		}

		// Left-over accounting
		if (l2LineCounter > 0) {
			assert l2LineCounter < BATCH_SIZE;

			stats.pc_ExecDrivenCycleCount.incr(maxBatchExecLatency);
			updatePhaseExecDrivenCycleCost(ExecutionPhase.READ_VALIDATION, maxBatchExecLatency);

			// Count the cost of sending a batched message
			int batchSizeBytes = SystemConstants.VISER_RV_MESSAGE_SIZE_BYTES;
			totalSizeBytes += batchSizeBytes;

			// Count execution cycles but taking into account bandwidth
			long bandwidthBasedLatency = (long) Math
					.ceil(batchSizeBytes * SystemConstants.LLC_MULTIPLIER);
			if (whereHitInBatch == CacheLevel.MEMORY) {
				assert memBatchSizeBytes < batchSizeBytes;
				bandwidthBasedLatency += (long) Math
						.ceil(memBatchSizeBytes * SystemConstants.MEM_MULTIPLIER);
			}
			stats.pc_BandwidthDrivenCycleCount.incr(bandwidthBasedLatency);
			updatePhaseBWDrivenCycleCost(ExecutionPhase.READ_VALIDATION, bandwidthBasedLatency);
		}

		// Count the cost of sending all messages
		updateTrafficForOneNetworkMessage(1, totalSizeBytes, ExecutionPhase.READ_VALIDATION);
		vvResp.numValidatedLines = numLinesValidated;
		vvResp.overlap = rdValAndWriteSignatureOverlap;
		return vvResp;
	}

	/**
	 * Update each L2 line with information (read/write bits and values) from L1 cache
	 */
	private void rvMergeReadInformationFromL1ToL2() {
		assert params.useL2();

		for (Deque<Line> set : L2cache.sets) {
			for (Line l2Line : set) {
				if (!l2Line.valid()) {
					continue;
				}
				Line l1Line = L1cache.getLine(l2Line);
				if (l1Line == null) {
					continue;
				}
				if (l1Line.hasReadOffsets(id)) {
					// To comply with value updates, only update read-only bits
					// from l1line
					l2Line.orReadEncoding(id,
							l1Line.getReadEncoding(id) & ~l1Line.getWriteEncoding(id));
					l2Line.updateReadSiteInfo(id,
							l1Line.getReadEncoding(id) & ~l1Line.getWriteEncoding(id),
							l1Line.getReadSiteInfo(id), l1Line.getReadLastSiteInfo(id));
				}
				l2Line.copyReadOnlyValuesFromSource(l1Line);
				/*
				 * Also need to merge write metadata. Otherwise, (l2Version + 1 < sharedVersion ||
				 * !l2line.hasWrittenOffsets(id)) is True (line 2360 in
				 * rvPrivateCacheMergedHelper(HierarchicalCache<Line>, boolean)) doesn't necessarily
				 * indicate that "these were current remote writes", because even if the current
				 * core is the last and only writer, (!l2line.hasWrittenOffsets(id)) can till be
				 * true. As a result, false failed read validation will be reported between the core
				 * and itself.
				 */
				// L1Line's write bits are still needed although we don't
				// increase versions for
				// shared lines during
				// pre-commit, because we need to know if there are concurrent
				// writers.
				// not set dirty bit because we don't actually write back dirty
				// values from L1 here.
				l2Line.orWriteEncoding(id, l1Line.getWriteEncoding(id));
			}
		}
	}

	// This is supposed to be asynchronous, so we do not account for it.
	// We do not increment the conflict stat immediately since read validation
	// only counts one failed read validation.
	boolean valueValidateReadLine(ExecutionPhase phase, Line privLine, Line sharedLine) {
		assert sharedLine != null;
		stats.pc_ValidationAttempts.incr();
		boolean preciseConflict = false;
		if (privLine.valid() && privLine.hasReadOffsets(id)) { // Line has some
																// reads
			int[] privSiIndex = privLine.getReadSiteInfo(id);
			int[] privLastSiIndex = privLine.getReadLastSiteInfo(id);
			for (int offset = 0; offset < SystemConstants.LINE_SIZE(); offset++) {
				long enc = getEncodingForOffset(offset);
				long privValue = privLine.getValue(offset);
				long sharedValue = sharedLine.getValue(offset);
				if (privValue != sharedValue) {
					if (privLine.isOffsetRead(id, enc)) {
						// The current core has read from this byte offset,
						// match values
						if (!params.isHttpd()
								&& (!ViserSim.modelOnlyROI()
										|| ViserSim.getPARSECPhase() == PARSEC_PHASE.IN_ROI)
								|| ViserSim.getPARSECPhase() == PARSEC_PHASE.IN_SERVER_ROI) {
							if (params.siteTracking()) {
								SiteInfoEntry privSi = machine.siteInfo.get(privSiIndex[offset]);
								SiteInfoEntry privLastSi = machine.siteInfo
										.get(privLastSiIndex[offset]);
								int privLno = privSi.lineNo;
								int privFno = privSi.fileIndexNo;
								int privRno = privSi.routineIndexNo;
								short lw = sharedLine.getLastWriter(offset);
								if (lw != -1) {
									CpuId lastWriter = new CpuId(lw);
									int sharedSiIndex = sharedLine
											.getWriteSiteInfo(lastWriter)[offset];
									SiteInfoEntry sharedSi = machine.siteInfo.get(sharedSiIndex);
									int sharedLastSiIndex = sharedLine
											.getWriteLastSiteInfo(lastWriter)[offset];
									SiteInfoEntry sharedLastSi = machine.siteInfo
											.get(sharedLastSiIndex);
									int sharedLno = sharedSi.lineNo;
									int sharedFno = sharedSi.fileIndexNo;
									int sharedRno = sharedSi.routineIndexNo;
									if (lw == id.get()) {
										System.out.println("During " + phase
												+ ", read validation failed at "
												+ privLine.addr.get() + "(+" + offset + "):");
										System.out.println("\t" + id + " reads value " + privValue
												+ " at " + privFno + ":" + privLno + ":" + privRno
												+ "(callerSite: " + privLastSi.fileIndexNo + ":"
												+ privLastSi.lineNo + ").");
										System.out.println("\t" + lastWriter + " write value "
												+ sharedValue + " at " + sharedFno + ":" + sharedLno
												+ ":" + sharedRno + "(callerSite: "
												+ sharedLastSi.fileIndexNo + ":"
												+ sharedLastSi.lineNo + ").");
									} else {
										if (privLno != 0 && sharedLno != 0) {
											preciseConflict = true;
											if (params.printConflictingSites()) {
												System.out.println("During " + phase
														+ ", read validation failed at "
														+ privLine.addr.get() + "(+" + offset
														+ "):");
												System.out.println("\t" + id + " reads value "
														+ privValue + " at " + privFno + ":"
														+ privLno + ":" + privRno + "(callerSite: "
														+ privLastSi.fileIndexNo + ":"
														+ privLastSi.lineNo + ").");
												System.out.println("\t" + lastWriter
														+ " write value " + sharedValue + " at "
														+ sharedFno + ":" + sharedLno + ":"
														+ sharedRno + "(callerSite: "
														+ sharedLastSi.fileIndexNo + ":"
														+ sharedLastSi.lineNo + ").");
											}
										}
										machine.updateConflictCounters(privFno, privLno, privRno,
												sharedFno, sharedLno, sharedRno,
												privLastSi.fileIndexNo, privLastSi.lineNo,
												sharedLastSi.fileIndexNo, sharedLastSi.lineNo);
									}
								} else {
									System.out.println(
											"During " + phase + ", read validation failed at "
													+ privLine.addr.get() + "(+" + offset + "):");

									System.out.println("\t" + id + " reads value " + privValue
											+ " at " + privFno + ":" + privLno + ":" + privRno
											+ ".");
									System.out
											.println("\t" + "p-1 write value " + sharedValue + ".");
								}
							} else {
								preciseConflict = true;
							}
						}
					}
					// Update the L2 line, but not any WAR or written bytes
					// because the core has
					// updated values for these bytes in L1 (or L2 if the line's
					// missing in L1)
					if (!privLine.isOffsetWritten(id, enc)) {
						privLine.setValue(offset, sharedValue);
						// L1's write bits have been merged into the L2 line
						Line l1line = L1cache.getLine(privLine);
						if (l1line != null)
							l1line.setValue(offset, sharedValue);
					}
				}
			}
		}

		if (params.siteTracking()) {
			machine.resetConflictCounter();
			if (preciseConflict && params.printConflictingSites())
				System.out.println(
						"============================= Faild read validation =================================");
		}
		return preciseConflict;
	}

	/**
	 * Check whether any core has valid metadata in the AIM line. This helps avoid unnecessary AIM
	 * lookups on every LLC access. Conceptually, this method is implemented as a bit in the LLC.
	 */
	// boolean needToCheckAIMCache(Line llcLine) {
	// if (llcLine.hasAIMMD())
	// return true;
	//
	// boolean checkAIM = false;
	// for (int i = 0; i < params.numProcessors(); i++) {
	// CpuId cpuId = new CpuId(i);
	// Processor<Line> p = machine.getProc(cpuId);
	// PerCoreLineMetadata md = llcLine.getPerCoreMetadata(cpuId);
	// assert md != null;
	// assert md.epoch.getRegionId() <= p.getCurrentEpoch().getRegionId();
	// if (md.epoch.getRegionId() == p.getCurrentEpoch().getRegionId()) {
	// if (llcLine.hasReadOffsets(cpuId) || llcLine.hasWrittenOffsets(cpuId)) {
	// checkAIM = true;
	// break;
	// }
	// }
	// }
	// return checkAIM;
	// }

	/**
	 * This is just for lookup. This does not bring in or evict lines, and neither does it add
	 * costs.
	 */
	// This method should not be there. There is nothing like a lookup in a cache.
	MemoryResponse<Line> getLineFromLLCOrMemory(Line l, boolean read) {
		assert l.valid();
		MemoryResponse<Line> resp = new MemoryResponse<Line>();

		// Get the corresponding line from memory or LLC
		Line llcLine = L3cache.getLine(l);
		if (llcLine == null) { // Line not in LLC, get from memory
			llcLine = machine.memory.get(l.lineAddress().get());
			assert !llcLine.isLineDeferred();
			resp.whereHit = CacheLevel.MEMORY;
		} else {
			resp.whereHit = CacheLevel.L3;
		}

		if (params.useAIMCache() && /* needToCheckAIMCache(llcLine) */
				llcLine.hasAIMMD()) {
			aimcache.getLine(this, l, read);
		}

		assert llcLine != null && llcLine.valid();
		assert llcLine.id().get() == 0;
		resp.lineHit = llcLine;
		return resp;
	}

	/**
	 * Initiated on behalf of the private cache that is evicting a private line
	 */
	/*
	 * void writeBackDeferredLineToSharedCache(Line evictedPrivateLine, Line sharedLine) { assert
	 * evictedPrivateLine != null && sharedLine != null; assert
	 * evictedPrivateLine.lineAddress().get() == sharedLine.lineAddress().get(); assert
	 * evictedPrivateLine.isPrivateCacheLine() && !sharedLine.isPrivateCacheLine(); assert
	 * evictedPrivateLine.id().get() == sharedLine.getDeferredLineOwnerID();
	 * sharedLine.copyAllValues(evictedPrivateLine);
	 * sharedLine.setLastWritersFromPrivateLine(evictedPrivateLine);
	 * sharedLine.clearDeferredLineOwnerID(); // Account for the data message (whole line) int
	 * sizeBytesOutgoing = MemorySystemConstants.DATA_MESSAGE_CONTROL_BYTES +
	 * MemorySystemConstants.DATA_MESSAGE_SIZE_BYTES; if (evictedPrivateLine.hasReadOffsets(id)) {
	 * sizeBytesOutgoing += MemorySystemConstants.VISER_READ_METADATA_BYTES; } if
	 * (evictedPrivateLine.hasWrittenOffsets(id)) { sizeBytesOutgoing +=
	 * MemorySystemConstants.VISER_WRITE_METADATA_BYTES; } updateTrafficForOneNetworkMessage(1,
	 * sizeBytesOutgoing, ExecutionPhase.REGION_BODY);
	 * updateOnChipTrafficForOneNetworkMessageIncorrect(1, sizeBytesOutgoing);
	 * updateOnChipTrafficForOneNetworkMessageNoCompactVersions(1, sizeBytesOutgoing);
	 * updateTCCBroadcastMessage(sizeBytesOutgoing); }
	 */

	/** Initiated on behalf of the shared cache */
	void fetchDeferredLineFromPrivateCache(Line llcLine, boolean rv, boolean notCountCosts) {
		Processor<Line> ownerCore = machine.getProc(new CpuId(llcLine.getDeferredLineOwnerID()));
		CpuId cid = ownerCore.id;
		Line line;

		// search L1/L2
		MemoryResponse<Line> privateResp = ownerCore.L1cache.searchPrivateCache(llcLine);
		assert privateResp.lineHit != null;
		line = privateResp.lineHit;

		// Update read bits
		llcLine.orReadEncoding(cid, line.getReadEncoding(cid));
		llcLine.updateReadSiteInfo(cid, line.getReadEncoding(cid), line.getReadSiteInfo(cid),
				line.getReadLastSiteInfo(cid));
		// Update write bits
		llcLine.orWriteEncoding(cid, line.getWriteEncoding(cid));
		llcLine.updateWriteSiteInfo(cid, line.getWriteEncoding(cid), line.getWriteSiteInfo(cid),
				line.getWriteLastSiteInfo(cid));
		if (line.hasWrittenOffsets(cid)) {
			llcLine.incrementVersion();
			llcLine.setDirty(true);
			if (params.useBloomFilter()) {
				updatePerCoreBloomFilters(line);
			}
			line.setVersion(llcLine.getVersion());
		}
		llcLine.setEpoch(cid, ownerCore.getCurrentEpoch());

		// deal with values
		/*
		 * We can safely write back the whole line as long as we also send the line's write bits to
		 * the LLC so that the LLC can check write--read conflicts
		 * (RegularTests.testOptimizations8).
		 */
		llcLine.copyAllValues(line);
		llcLine.setLastWritersFromPrivateLine(line);

		// If both read and write offsets are set in the shared line, then no
		// need to maintain read
		// encoding. Reset read encoding in the LLC line directly.
		long readEnc = llcLine.getReadEncoding(cid);
		if (llcLine.isWrittenAfterRead(cid)) {
			readEnc &= (~llcLine.getWriteEncoding(cid));
		}
		llcLine.clearReadEncoding(cid);
		llcLine.orReadEncoding(cid, readEnc);
		// no need to update read site info

		// If's not safe to update the AIM cache since we're not sure if llcLine
		// is in the LLC or not (might be in the memory). So we need to check
		// first before adding a line into the AIM cache.
		if (params.useAIMCache()) {
			if (line.hasReadOffsets(cid) || line.hasWrittenOffsets(cid)) {
				if (L3cache.getLine(line) != null) { // The line hits in the LLC
					line.setAIMMD(true);
					// The line might be in the AIM cache
					aimcache.addLineIfNotPresent(this, line, false, true,
							ExecutionPhase.REGION_BODY);
				}
			}
		}

		// Clear write/read bits of the private line to avoid false races
		line.clearReadEncoding(cid);
		line.clearWriteEncoding(cid);

		if (line.getLevel() == CacheLevel.L1) {
			Line l2Line = ownerCore.L2cache.getLine(line);
			l2Line.setVersion(line.getVersion());
			l2Line.clearReadEncoding(cid);
			l2Line.clearWriteEncoding(cid);
		}

		llcLine.clearDeferredLineOwnerID();
		// The line is no longer deferred, hence remove the entry from the set
		// of deferred lines
		Long writeMd = null;
		if (params.areDeferredWriteBacksPrecise()) {
			writeMd = ownerCore.getDeferredWriteMetadata(line);
			assert writeMd != null : line.toString();
			assert Long.bitCount(writeMd) > 0 : "Otherwise it should not have been deferred";
			ownerCore.removeDeferredWriteLine(line);
		}

		if (!notCountCosts) {
			// One fetch message and one return data message (whole line)
			// Fetch message from the LLC to the owner core
			int sizeBytesOutgoing = SystemConstants.CONTROL_MESSAGE_SIZE_BYTES;
			updateTrafficForOneNetworkMessage(1, sizeBytesOutgoing, ExecutionPhase.REGION_BODY);
			if (rv) {
				updateRVDeferredLineTrafficForOneNetworkMessage(1, sizeBytesOutgoing);
			}
			updateTCCBroadcastMessage(sizeBytesOutgoing);

			int sizeBytesReturn;
			if (params.areDeferredWriteBacksPrecise()) {
				sizeBytesReturn = SystemConstants.DATA_MESSAGE_CONTROL_BYTES
						+ SystemConstants.VISER_WRITE_METADATA_BYTES + Long.bitCount(writeMd);
			} else {
				sizeBytesReturn = SystemConstants.DATA_MESSAGE_CONTROL_BYTES
						+ SystemConstants.DATA_MESSAGE_SIZE_BYTES;
			}

			// If offsets are written after read, then we avoid writing these
			// read bits back since
			// they are not useful for conflict detection.
			if (line.hasReadOnlyOffsets(cid)) {
				sizeBytesReturn += SystemConstants.VISER_READ_METADATA_BYTES;
			}
			if (line.hasWrittenOffsets(cid)) {
				sizeBytesReturn += SystemConstants.VISER_WRITE_METADATA_BYTES;
			}

			updateTrafficForOneNetworkMessage(1, sizeBytesReturn, ExecutionPhase.REGION_BODY);
			if (rv) {
				updateRVDeferredLineTrafficForOneNetworkMessage(1, sizeBytesReturn);
			}
			updateTCCBroadcastMessage(sizeBytesReturn);

			// Cost is LLC latency
			stats.pc_ExecDrivenCycleCount.incr(SystemConstants.L3_HIT_LATENCY);
			updatePhaseExecDrivenCycleCost(ExecutionPhase.REGION_BODY,
					SystemConstants.L3_HIT_LATENCY);
			stats.pc_BandwidthDrivenCycleCount.incr(SystemConstants.L3_HIT_LATENCY);
			updatePhaseBWDrivenCycleCost(ExecutionPhase.REGION_BODY,
					SystemConstants.L3_HIT_LATENCY);
			stats.pc_TCCCycleCount8K.incr(SystemConstants.L3_HIT_LATENCY);
			stats.pc_TCCCycleCount16K.incr(SystemConstants.L3_HIT_LATENCY);
			stats.pc_TCCCycleCount32K.incr(SystemConstants.L3_HIT_LATENCY);
			stats.pc_TCCCycleCount64K.incr(SystemConstants.L3_HIT_LATENCY);

			// Model TCC stall cycles since region has overflowed
			if (perRegionOverflow8K != TCCRegionsWithOverflow.NO_OVERFLOW) {
				tccPerRegionStalledCycles8K += SystemConstants.L3_HIT_LATENCY;
			}
			if (perRegionOverflow16K != TCCRegionsWithOverflow.NO_OVERFLOW) {
				tccPerRegionStalledCycles16K += SystemConstants.L3_HIT_LATENCY;
			}
			if (perRegionOverflow32K != TCCRegionsWithOverflow.NO_OVERFLOW) {
				tccPerRegionStalledCycles32K += SystemConstants.L3_HIT_LATENCY;
			}
			if (perRegionOverflow64K != TCCRegionsWithOverflow.NO_OVERFLOW) {
				tccPerRegionStalledCycles64K += SystemConstants.L3_HIT_LATENCY;
			}
		}
	}

	boolean matchVersions(Line privLine, Line sharedLine) {
		if (privLine.getVersion() == sharedLine.getVersion()) {
			return true;
		}
		assert privLine.getVersion() < sharedLine.getVersion();
		return false;
	}

	// Iterate over each private line that has a read-only byte offset (not also
	// written)
	// On first iteration, check for versions.
	// If failed, check for values, and update versions.
	// Then recheck for versions.
	// Keep retrying, till either a failure or a success.
	// Either we detect a conflict and terminate, or we keep retrying in the
	// hope of reading a consistent snapshot
	private void performReadValidation() {
		boolean retryAttempt = false;
		while (true) {
			ReadValidationResponse ret = rvValidationMergedHelper(retryAttempt);
			if (ret.versionsMatch) { // All private cache line versions matched.
				// Update stats
				updateNumValidatedLinesHistogram(ret.numValidatedLines);
				break;
			}
			retryAttempt = true;
		}
	}

	private void updateNumValidatedLinesHistogram(int count) {
		int key;
		if (count == 0) {
			key = 0;
		} else if (count > 0 && count <= 10) {
			key = 1;
		} else if (count > 10 && count <= 20) {
			key = 2;
		} else if (count > 20 && count <= 30) {
			key = 3;
		} else if (count > 30 && count <= 40) {
			key = 4;
		} else {
			key = 5;
		}
		Integer val = stats.hgramLinesValidated.get(key);
		if (val == null) {
			val = new Integer(1);
		} else {
			val++;
		}
		stats.hgramLinesValidated.put(key, val);
	}

	/*
	 * public boolean processRegionBegin(ThreadId tid, EventType type) { phase =
	 * ExecutionPhase.REGION_BODY; return true; }
	 */

	/**
	 * Currently we assume one thread to core mapping, otherwise it is more complicated.
	 */
	public void processRegionEnd(ThreadId tid, EventType type) {
		// Update LLC with precise write information and values from the private caches, L1 and L2
		// phase = ExecutionPhase.PRE_COMMIT;
		boolean written = preCommitWriteBackDirtyLines(this);

		// Validate reads in the private caches, by first validating versions and then validating
		// values. Repeat until a consistent snapshot is validated.
		// phase = ExecutionPhase.READ_VALIDATION;
		performReadValidation();

		// Only increase the counter for a successful region
		if (written) {
			stats.pc_RegionsWithWrites.incr();
		}

		// Tell the LLC to clear all write and read info for this core. This can be better handled
		// with epochs.
		// postCommitClearPerCoreMetadataInLLC();

		// Add network traffic for the Bloom filter sent by the LLC. This is
		// needed during read validation.
		if (params.useBloomFilter()) {
			int sizeBytes = SystemConstants.BLOOM_FILTER_LLC_MESSAGE;
			updateTrafficForOneNetworkMessage(1, sizeBytes, ExecutionPhase.READ_VALIDATION);

			// Update histogram
			updateBloomFilterHistogram();
		}

		// Send dirty values and clear W/R bits for private caches, L1 and L2
		// phase = ExecutionPhase.POST_COMMIT;
		postCommitSelfInvalidateHelper(type);

		// Tell the LLC to clear all write and read info for this core. This can
		// be better handled with epochs.
		machine.incrementEpoch(id);

		if (ViserSim.xassertsEnabled() && params.alwaysInvalidateReadOnlyLines()
				&& !params.invalidateWrittenLinesOnlyAfterVersionCheck()) {
			Verify.verifyPrivateCacheLinesAreInvalid(this);
		}

		// Clear the bloom filter
		if (params.useBloomFilter()) {
			// Cannot clear the Bloom filter at acquires if we are using RFRs and we plan to skip
			// validation
			set.clear();
			bf.clear();

			stats.pc_BloomFilterTotalEnergy.incr(SystemConstants.BLOOM_FILTER_WRITE_ENERGY);
			stats.pc_BloomFilterWriteEnergy.incr(SystemConstants.BLOOM_FILTER_WRITE_ENERGY);
		}

		// Clear stale lines from the AIM
		if (params.useAIMCache() && params.clearAIMCacheAtRegionBoundaries()) {
			aimcache.clearAIMCache2(this);
		}

		// Model TCC

		// Model the write buffer and broadcast messages in TCC
		long numBytes = (SystemConstants.CONTROL_MESSAGE_SIZE_BYTES
				+ ((long) tccWriteSet.size() * SystemConstants.TAG_BYTES))
				* (params.numProcessors() - 1);
		updateTCCBroadcastMessage(numBytes);

		if (tccWriteSet.size() > SystemConstants.TCC_WB_SIZE_8K) {
			stats.pc_TCCRegionsWBOverflows8K.incr();
		}
		if (tccWriteSet.size() > SystemConstants.TCC_WB_SIZE_16K) {
			stats.pc_TCCRegionsWBOverflows16K.incr();
		}
		if (tccWriteSet.size() > SystemConstants.TCC_WB_SIZE_32K) {
			stats.pc_TCCRegionsWBOverflows32K.incr();
		}
		if (tccWriteSet.size() > SystemConstants.TCC_WB_SIZE_64K) {
			stats.pc_TCCRegionsWBOverflows64K.incr();
		}

		if (perRegionCacheOverflow == TCCPrivateCacheOverflow.OVERFLOWN) {
			stats.pc_TCCRegionsCacheOverflows.incr();
		}

		// 8K
		if (perRegionOverflow8K == TCCRegionsWithOverflow.WB_OVERFLOWN
				|| perRegionOverflow8K == TCCRegionsWithOverflow.CACHE_OVERFLOWN) {
			stats.pc_TCCRegionsOverflows8K.incr();
			if (perRegionOverflow8K == TCCRegionsWithOverflow.WB_OVERFLOWN) {
				stats.pc_TCCRegionsFirstWBOverflows8K.incr();
			} else {
				stats.pc_TCCRegionsFirstCacheOverflows8K.incr();
			}
		}

		// 16K
		if (perRegionOverflow16K == TCCRegionsWithOverflow.WB_OVERFLOWN
				|| perRegionOverflow16K == TCCRegionsWithOverflow.CACHE_OVERFLOWN) {
			stats.pc_TCCRegionsOverflows16K.incr();
			if (perRegionOverflow16K == TCCRegionsWithOverflow.WB_OVERFLOWN) {
				stats.pc_TCCRegionsFirstWBOverflows16K.incr();
			} else {
				stats.pc_TCCRegionsFirstCacheOverflows16K.incr();
			}
		}

		// 32K
		if (perRegionOverflow32K == TCCRegionsWithOverflow.WB_OVERFLOWN
				|| perRegionOverflow32K == TCCRegionsWithOverflow.CACHE_OVERFLOWN) {
			stats.pc_TCCRegionsOverflows32K.incr();
			if (perRegionOverflow32K == TCCRegionsWithOverflow.WB_OVERFLOWN) {
				stats.pc_TCCRegionsFirstWBOverflows32K.incr();
			} else {
				stats.pc_TCCRegionsFirstCacheOverflows32K.incr();
			}
		}

		// 64K
		if (perRegionOverflow64K == TCCRegionsWithOverflow.WB_OVERFLOWN
				|| perRegionOverflow64K == TCCRegionsWithOverflow.CACHE_OVERFLOWN) {
			stats.pc_TCCRegionsOverflows64K.incr();
			if (perRegionOverflow64K == TCCRegionsWithOverflow.WB_OVERFLOWN) {
				stats.pc_TCCRegionsFirstWBOverflows64K.incr();
			} else {
				stats.pc_TCCRegionsFirstCacheOverflows64K.incr();
			}
		}

		// Model TCC stall cycles since region has overflowed

		// 8K
		if (perRegionOverflow8K != TCCRegionsWithOverflow.NO_OVERFLOW) {
			for (int i = 0; i < params.numProcessors(); i++) {
				CpuId cpuId = new CpuId(i);
				if (!cpuId.equals(id)) {
					Processor<Line> p = machine.getProc(cpuId);
					p.stats.pc_TCCCycleCount8K.incr(tccPerRegionStalledCycles8K);
				}
			}
		}
		// 16K
		if (perRegionOverflow16K != TCCRegionsWithOverflow.NO_OVERFLOW) {
			for (int i = 0; i < params.numProcessors(); i++) {
				CpuId cpuId = new CpuId(i);
				if (!cpuId.equals(id)) {
					Processor<Line> p = machine.getProc(cpuId);
					p.stats.pc_TCCCycleCount16K.incr(tccPerRegionStalledCycles16K);
				}
			}
		}
		// 32K
		if (perRegionOverflow32K != TCCRegionsWithOverflow.NO_OVERFLOW) {
			for (int i = 0; i < params.numProcessors(); i++) {
				CpuId cpuId = new CpuId(i);
				if (!cpuId.equals(id)) {
					Processor<Line> p = machine.getProc(cpuId);
					p.stats.pc_TCCCycleCount32K.incr(tccPerRegionStalledCycles32K);
				}
			}
		}
		// 64K
		if (perRegionOverflow64K != TCCRegionsWithOverflow.NO_OVERFLOW) {
			for (int i = 0; i < params.numProcessors(); i++) {
				CpuId cpuId = new CpuId(i);
				if (!cpuId.equals(id)) {
					Processor<Line> p = machine.getProc(cpuId);
					p.stats.pc_TCCCycleCount64K.incr(tccPerRegionStalledCycles64K);
				}
			}
		}

		tccWriteSet.clear();
		tccVictimCache.clear();
		perRegionCacheOverflow = TCCPrivateCacheOverflow.NO_OVERFLOW;
		perRegionOverflow8K = TCCRegionsWithOverflow.NO_OVERFLOW;
		perRegionOverflow16K = TCCRegionsWithOverflow.NO_OVERFLOW;
		perRegionOverflow32K = TCCRegionsWithOverflow.NO_OVERFLOW;
		perRegionOverflow64K = TCCRegionsWithOverflow.NO_OVERFLOW;
		tccPerRegionStalledCycles8K = 0;
		tccPerRegionStalledCycles16K = 0;
		tccPerRegionStalledCycles32K = 0;
		tccPerRegionStalledCycles64K = 0;

		// NOTE: The following checks are expensive

		// Assert that all metadata related to this core is zero
		if (ViserSim.assertsEnabled || ViserSim.xassertsEnabled()) {
			Verify.verifyPrivateMetadataCleared(this);
			Verify.verifySharedMetadataCleared(this);
			Verify.verifyTCCRegionOverflowBreakdown(this);
		}

		if (ViserSim.assertsEnabled && params.deferWriteBacks()) {
			Verify.verifyDeferredLines(this);
			if (params.areDeferredWriteBacksPrecise()) {
				Verify.verifyPrivateDeferredLines(this);
			}
		}

		// Current region finishes, reset counter flags
		resetFlagsForRegionCounters();
	}

	private void resetFlagsForRegionCounters() {
		regionConflicted = false;
		regionWithExceptions = false;
		hasDirtyEviction = false;
		regionHasDirtyEvictionBeforeFRV = false;
	}

	private void updateBloomFilterHistogram() {
		int count = set.size();
		int key;
		if (count == 0) {
			key = 0;
		} else if (count > 0 && count <= 10) {
			key = 1;
		} else if (count > 10 && count <= 20) {
			key = 2;
		} else if (count > 20 && count <= 30) {
			key = 3;
		} else if (count > 30 && count <= 40) {
			key = 4;
		} else {
			key = 5;
		}
		Integer val = stats.hgramLLCUpdatesInARegion.get(key);
		if (val == null) {
			val = new Integer(1);
		} else {
			val++;
		}
		stats.hgramLLCUpdatesInARegion.put(key, val);
	}

	public void updateVersionSizeHistogram(int version) {
		int key = 0;
		if (version < SystemConstants.MAX_8_BIT_VERSION) {
			key = 0;
		} else if (version >= SystemConstants.MAX_8_BIT_VERSION
				&& version < SystemConstants.MAX_16_BIT_VERSION) {
			key = 1;
		} else if (version >= SystemConstants.MAX_16_BIT_VERSION
				&& version < SystemConstants.MAX_24_BIT_VERSION) {
			key = 2;
		} else if (version >= SystemConstants.MAX_24_BIT_VERSION
				&& version < SystemConstants.MAX_32_BIT_VERSION) {
			key = 3;
		}
		Integer val = stats.hgramVersionSizes.get(key);
		if (val == null) {
			val = new Integer(1);
		} else {
			val++;
		}
		stats.hgramVersionSizes.put(key, val);
	}

	// We do not add performance cost since this is not on the critical path,
	// DRFx 2011 adds two
	// cycles
	void updatePerCoreBloomFilters(Line line) {
		long lineAddr = line.lineAddress().get();
		for (int i = 0; i < params.numProcessors(); i++) {
			CpuId cpuId = new CpuId(i);
			if (cpuId.equals(id)) { // Avoid polluting the filter of the
									// initiator core
				continue;
			}
			Processor<Line> p = machine.getProc(cpuId);
			p.bf.add(lineAddr);
			p.set.add(lineAddr);

			p.stats.pc_BloomFilterTotalEnergy.incr(SystemConstants.BLOOM_FILTER_WRITE_ENERGY);
			p.stats.pc_BloomFilterWriteEnergy.incr(SystemConstants.BLOOM_FILTER_WRITE_ENERGY);
		}
	}

	// The core just issues on command to the cache controller to flash clear
	// lines, so this operation is for free.

	// There could be L1 lines that have been read, but the fact is not
	// transmitted to L2 lines
	// because of
	// no L1 eviction. This implies that the L1 line is read only, but the L2
	// line is not (read and
	// write encoding
	// are both zero for the L2 line). For such cases, we need to skip
	// invalidating the L2 line as
	// well. In general,
	// we want to avoid invalidating those L2 lines for which the corresponding
	// L1 lines were not
	// invalidated.
	private void postCommitSelfInvalidateHelper(EventType type) {
		sendDirtyValuesToLLC();
		// Track L1 lines that were skipped, so that we can skip invalidating
		// those lines in the L2 cache.
		HashSet<Line> skippedL1Lines = new HashSet<Line>();
		postCommitSelfInvalidateSFRs(type, CacheLevel.L1, skippedL1Lines);
		if (params.useL2()) {
			postCommitSelfInvalidateSFRs(type, CacheLevel.L2, skippedL1Lines);
		}
	}

	private void postCommitSelfInvalidateSFRs(EventType type, CacheLevel level,
			HashSet<Line> skippedL1Lines) {
		Epoch currentEp = getCurrentEpoch();
		Epoch nextEp;
		nextEp = new Epoch(currentEp.getRegionId() + 1);

		// We can assume parallelization while sending messages, and hence
		// account for the slowest
		// message in a batch
		// for estimating the cycle cost. But that is not the default for
		// tracking execution cost.
		double bandwidthBasedCost = 0;
		// We consider writing back WAR-upgraded dirty lines to be streaming
		// operations. So that is
		// why, we add up all
		// the bytes and compute network traffic in terms of flits.
		int totalSizeInBytes = 0;

		HierarchicalCache<Line> cache = (level == CacheLevel.L1) ? L1cache : L2cache;
		for (Deque<Line> set : cache.sets) {
			for (Line l : set) {
				if (!l.valid()) {
					continue;
				}
				assert l.id() == id : "Private lines should be owned by the same core";

				if (level == CacheLevel.L2) {
					boolean found = false;
					Line l1Line = null;
					Iterator<Line> it = skippedL1Lines.iterator();
					// Speed up searching by removing found lines
					while (it.hasNext()) {
						Line skip = it.next();
						if (skip.lineAddress().get() == l.lineAddress().get()) {
							// So the L1 line corresponding to this L2 line was
							// not invalidated
							found = true;
							l1Line = skip;
							it.remove();
							break;
						}
					}

					if (found) {
						// Clear metadata from private L2 line
						l.clearReadEncoding(id);
						l.clearWriteEncoding(id);
						l.setVersion(l1Line.getVersion()); // Needed if the L1
															// line was dirty
						l.setEpoch(id, nextEp);
						l.clearConcurrentRemoteWrite();

						continue;
					}
				}

				if (l.isLineReadOnly(id)) {
					assert l.getEpoch(id).equals(currentEp);

					// Optimization: After a successful read validation, we know
					// that read-only
					// lines have valid
					// values before the start of the next region, so we can
					// avoid invalidating the
					// line. This should
					// allow more hits in the private caches.
					if (params.alwaysInvalidateReadOnlyLines()) {
						l.invalidate();
					} else {
						// Need to clear read and write metadata if we are not
						// going to invalidate
						// the line
						l.clearReadEncoding(id);
						l.clearWriteEncoding(id);
						l.setEpoch(id, nextEp);
						l.clearConcurrentRemoteWrite();
						if (params.useL2() && level == CacheLevel.L1) {
							skippedL1Lines.add(l);
						}
					}

				} else if (l.hasWrittenOffsets(id)) { // Written line
					assert l.getEpoch(id).equals(currentEp);

					MemoryResponse<Line> resp = getLineFromLLCOrMemory(l, true);
					Line sharedLine = resp.lineHit;
					assert sharedLine != null;
					int sharedVer = sharedLine.getVersion();
					boolean llcHit = (resp.whereHit == CacheLevel.L3) ? true : false;

					// Need to *model* the write back the dirty bytes for
					// WAR-upgraded lines
					if (l.isWrittenAfterRead(id)) {
						// Compute size of a message to LLC. We do not need to
						// send the version, we
						// can just increment
						// it
						long writeEnc = l.getWriteEncoding(id);
						int sizeInBytes = SystemConstants.TAG_BYTES;
						if (!params.deferWriteBacks()) {
							sizeInBytes += Long.bitCount(writeEnc);
						}
						totalSizeInBytes += sizeInBytes;

						int cost = llcHit ? SystemConstants.L3_ACCESS
								: SystemConstants.MEMORY_ACCESS;
						stats.pc_ExecDrivenCycleCount.incr(cost);
						updatePhaseExecDrivenCycleCost(ExecutionPhase.POST_COMMIT, cost);
						// Count execution cycles but taking into account
						// bandwidth
						bandwidthBasedCost += (sizeInBytes * SystemConstants.LLC_MULTIPLIER);
						if (!llcHit) {
							bandwidthBasedCost += (sizeInBytes * SystemConstants.MEM_MULTIPLIER);
						}
					}

					if (params.invalidateWrittenLinesOnlyAfterVersionCheck()) {
						long myVer = l.getVersion();
						assert myVer < sharedVer;
						// The line may have been read and written. In that
						// case, read validation
						// updates the version number in the private cache, but
						// then writing back
						// increases the version number in the LLC. So sharedVer
						// should always be
						// larger than myVer.
						// TODO: opt opportunities: all the offsets of the line
						// have been touched
						if (myVer == sharedVer - 1
								// myVer values may have been updated during
								// read validation
								&& !l.isThereAConcurrentRemoteWrite()) {
							// Need not invalidate, since there has been no
							// concurrent write
							l.clearReadEncoding(id);
							l.clearWriteEncoding(id);
							l.setVersion(sharedVer); // Update the version
							l.setEpoch(id, nextEp);
							if (params.useL2() && level == CacheLevel.L1) {
								skippedL1Lines.add(l);
							}
						} else {
							if (params.updateWrittenLinesDuringVersionCheck()) {
								// Update the values with LLC contents
								l.copyAllValues(sharedLine);
								if (level == CacheLevel.L1) {
									Line l2Line = L2cache.getLine(l);
									assert l2Line != null;
									l2Line.copyAllValues(sharedLine);
									if (params.useL2()) {
										skippedL1Lines.add(l);
									}
								}
								l.clearReadEncoding(id);
								l.clearWriteEncoding(id);
								l.setVersion(sharedVer);
								l.setEpoch(id, nextEp);

								int cost = (resp.whereHit == CacheLevel.L3)
										? SystemConstants.L3_ACCESS
										: SystemConstants.MEMORY_ACCESS;
								stats.pc_ExecDrivenCycleCount.incr(cost);
								updatePhaseExecDrivenCycleCost(ExecutionPhase.POST_COMMIT, cost);
								stats.pc_BandwidthDrivenCycleCount.incr(cost);
								updatePhaseBWDrivenCycleCost(ExecutionPhase.POST_COMMIT, cost);
								stats.pc_TCCCycleCount8K.incr(cost);
								stats.pc_TCCCycleCount16K.incr(cost);
								stats.pc_TCCCycleCount32K.incr(cost);
								stats.pc_TCCCycleCount64K.incr(cost);
							} else {
								// A written line is now being invalidated, this
								// requires that we
								// should
								// write back the data and remove the line from
								// the per-core
								// deferred set if the
								// line was deferred.
								// The line should not be deferred and has
								// already been written
								// back.
								l.invalidate();
							}
						}

						l.clearConcurrentRemoteWrite();
					} else {
						l.invalidate();
					}

				} else { // Untouched lines

					// The read/write access information might not be up-to-date
					// in the L2 cache
					if (level == CacheLevel.L1) {
						if (params.alwaysInvalidateReadOnlyLines()
								&& !params.invalidateWrittenLinesOnlyAfterVersionCheck()
								&& !params.invalidateUntouchedLinesOptimization()) {
							assert l.getEpoch(id).getRegionId() < currentEp.getRegionId();
						}

						if (ViserSim.assertsEnabled) {
							// L2 line should also be untouched
							Line l2Line = L2cache.getLine(l);
							assert !l2Line.isLineReadOnly(id) && !l2Line.hasWrittenOffsets(id);
							assert !l2Line.isAccessedInThisRegion(id);
						}
					}

					if (params.invalidateUntouchedLinesOptimization()) {
						// Get the current version of the LLC line. If the versions match, it
						// implies that there was no concurrent writer, so we can avoid
						// invalidation.
						MemoryResponse<Line> resp = L3cache.requestLineFromLLCOrMemory(this, l,
								true, ExecutionPhase.POST_COMMIT);
						assert resp.lineHit != null;
						long sharedVer = resp.lineHit.getVersion();
						long myVer = l.getVersion();
						if (myVer == sharedVer) {
							// Need not invalidate, since there has been no concurrent write
							l.clearReadEncoding(id);
							l.clearWriteEncoding(id);
							l.setEpoch(id, nextEp);
							l.clearConcurrentRemoteWrite();

							// If an L1 line is untouched, then we can assert that the L2 line is
							// also untouched. In that case, we can avoid adding this line.
							if (level == CacheLevel.L1) {
								// skippedL1Lines.add(l);
								if (ViserSim.assertsEnabled) {
									Line l2Line = L2cache.getLine(l);
									assert !l2Line.isAccessedInThisRegion(id);
								}
							}
						} else {
							l.invalidate();
						}

					} else if (params.useBloomFilter()) {
						stats.pc_BloomFilterTotalEnergy
								.incr(SystemConstants.BLOOM_FILTER_READ_ENERGY);
						stats.pc_BloomFilterReadEnergy
								.incr(SystemConstants.BLOOM_FILTER_READ_ENERGY);

						// LLC might have written it
						if (bf.contains(l.lineAddress().get())) {
							// Some of these lines could have been marked deferred in the LLC, which
							// could lead to assertion failures while checking deferred LLC lines.
							// This happens in RCC-SI, possibly because we do not use a special
							// INVALID state there.
							if (params.useSpecialInvalidState()) {
								l.clearReadEncoding(id);
								l.clearWriteEncoding(id);
								l.setEpoch(id, nextEp);
								l.clearConcurrentRemoteWrite();
								l.changeStateTo(ViserState.VISER_INVALID_TENTATIVE);
							} else {
								l.invalidate();
							}
						} else { // Definitely not updated by the LLC
							l.clearReadEncoding(id);
							l.clearWriteEncoding(id);
							l.setEpoch(id, nextEp);
							l.clearConcurrentRemoteWrite();
						}

					} else if (params.useSpecialInvalidState()) {

						assert !params.useBloomFilter() : "Shouldn't come here if both are enabled";
						l.clearReadEncoding(id);
						l.clearWriteEncoding(id);
						l.setEpoch(id, nextEp);
						l.clearConcurrentRemoteWrite();
						l.changeStateTo(ViserState.VISER_INVALID_TENTATIVE);

					} else {
						// It is wrong to not invalidate untouched lines, because of imprecision.
						// The read might be data-race-free, but we would report a failed read
						// validation.
						l.invalidate();
					}
				}
			}
		}

		double bwCost = Math.ceil(bandwidthBasedCost);
		stats.pc_BandwidthDrivenCycleCount.incr(bwCost);
		updatePhaseBWDrivenCycleCost(ExecutionPhase.POST_COMMIT, bwCost);

		if (totalSizeInBytes > 0) {
			updateTrafficForOneNetworkMessage(1, totalSizeInBytes, ExecutionPhase.POST_COMMIT);
			updateTCCBroadcastMessage(totalSizeInBytes);
		}
	}

	class Verifier {

		/** AIM Cache lines should be a strict subset of the LLC lines */
		public void verifyAIMCacheInclusivity(final Processor<Line> proc) {
			assert ViserSim.XASSERTS && ViserSim.xassertsEnabled();

			AIMCache.LineVisitor<Line> lv = new AIMCache.LineVisitor<Line>() {
				@Override
				public void visit(Line line) {
					if (line.lineAddress() != null) {
						assert line.getLevel() == CacheLevel.L3;
						Line llcLine = L3cache.getLine(line);
						if (llcLine == null) {
							System.out.println(ViserSim.totalEvents);
							System.out.println(line);
						}
						assert llcLine != null : "AIM is a subset of the LLC";
					}
				}
			};
			aimcache.visitAllLines(lv);
		}

		public void verifyAIMCacheDuplicates(final Processor<Line> proc) {
			assert ViserSim.XASSERTS && ViserSim.xassertsEnabled();

			for (Deque<Line> set : aimcache.sets) {
				for (Line l : set) {
					if (l.lineAddress() != null) {
						int counter = 0;
						for (Line tmp : set) {
							if (tmp.lineAddress() != null
									&& l.lineAddress().equals(tmp.lineAddress())) {
								counter++;
							}
						}
						assert counter == 1;
					}
				}
			}
		}

		public void verifyPrivateMetadataCleared(final Processor<Line> proc) {
			HierarchicalCache.LineVisitor<Line> l1Lv = new HierarchicalCache.LineVisitor<Line>() {
				@Override
				public void visit(Line line) {
					if (line.valid()) {
						assert line
								.id() == proc.id : "Private line should be owned by the same core";
						assert line.getLevel() == CacheLevel.L1;
						assert line.getReadEncoding(id) == 0;
						assert line.getWriteEncoding(id) == 0;
						assert !line.isThereAConcurrentRemoteWrite();
					}
				}
			};
			L1cache.visitAllLines(l1Lv);

			HierarchicalCache.LineVisitor<Line> l2Lv = new HierarchicalCache.LineVisitor<Line>() {
				@Override
				public void visit(Line line) {
					if (line.valid()) {
						assert line
								.id() == proc.id : "Private line should be owned by the same core";
						assert line.getLevel() == CacheLevel.L2;
						assert line.getReadEncoding(id) == 0;
						assert line.getWriteEncoding(id) == 0;
						assert !line.isThereAConcurrentRemoteWrite();
					}
				}
			};
			L2cache.visitAllLines(l2Lv);
		}

		// Iterating over memory data structure is going to be slooow
		public void verifySharedMetadataCleared(final Processor<Line> proc) {
			HierarchicalCache.LineVisitor<Line> l3Lv = new HierarchicalCache.LineVisitor<Line>() {
				@Override
				public void visit(Line line) {
					if (line.valid()) {
						assert line.getLevel() == CacheLevel.L3;
						assert line.getReadEncoding(id) == 0;
						assert line.getWriteEncoding(id) == 0;
					}
				}
			};
			L3cache.visitAllLines(l3Lv);
		}

		/**
		 * Verify that the owner core will have non-null metadata for private cache lines
		 */
		public void verifyPerCoreMetadata(final Processor<Line> proc) {
			assert ViserSim.XASSERTS && ViserSim.xassertsEnabled();

			HierarchicalCache.LineVisitor<Line> l1Lv = new HierarchicalCache.LineVisitor<Line>() {
				@Override
				public void visit(Line line) {
					if (line.valid()) {
						assert line
								.id() == proc.id : "Private line should be owned by the same core";
						assert line.getLevel() == CacheLevel.L1;
						// The current core may have executed a region boundary, and so might have
						// cleared its metadata. But the following assertion should still work
						// provided we always invalidate lines.
						if (params.alwaysInvalidateReadOnlyLines()
								&& !params.invalidateWrittenLinesOnlyAfterVersionCheck()) {
							assert line.hasReadOffsets(proc.id) || line.hasWrittenOffsets(proc.id);
						}
					}
				}
			};
			L1cache.visitAllLines(l1Lv);

			HierarchicalCache.LineVisitor<Line> l2Lv = new HierarchicalCache.LineVisitor<Line>() {
				@Override
				public void visit(Line line) {
					if (line.valid()) {
						assert line
								.id() == proc.id : "Private line should be owned by the same core";
						assert line.getLevel() == CacheLevel.L2;
						// L2 lines may not have updated metadata
					}
				}
			};
			L2cache.visitAllLines(l2Lv);
		}

		/**
		 * Any cache line marked invalid in the LLC should not be valid in any other private cache.
		 *
		 * When a private line is evicted (say E->I), the line is marked invalid in the LLC. If the
		 * same line is again brought in to the private cache, a new LLC line is created at the MRU
		 * spot. In that case, there are two lines in the LLC that have the same address, with one
		 * valid and another invalid. Therefore, we cannot assert that the line address of the
		 * invalid line will not be present in any private cache. That is why, we only check on LLC
		 * line addresses (as Integer objects since it is incorrect to compare addresses) that
		 * correspond to invalid lines and are present only once.
		 */
		public void verifyInvalidLinesInLLC() {
			assert ViserSim.XASSERTS && ViserSim.xassertsEnabled();

			// Iterate over invalid LLC lines
			final HashSet<Line> invalidLLCLines = new HashSet<Line>();
			HierarchicalCache.LineVisitor<Line> invalidLLCV = new HierarchicalCache.LineVisitor<Line>() {
				@Override
				public void visit(Line line) {
					if (line.invalid() && line.lineAddress() != null) {
						invalidLLCLines.add(line);
					}
				}
			};
			L3cache.visitAllLines(invalidLLCV);

			// Iterate over all LLC lines
			final HashSet<Line> allLLCLines = new HashSet<Line>();
			HierarchicalCache.LineVisitor<Line> allLLCV = new HierarchicalCache.LineVisitor<Line>() {
				@Override
				public void visit(Line line) {
					if (line.lineAddress() != null) {
						allLLCLines.add(line);
					}
				}
			};
			L3cache.visitAllLines(allLLCV);

			// Now strip invalid LLC lines that are also present as valid
			Iterator<Line> it = invalidLLCLines.iterator();
			while (it.hasNext()) {
				Line invalidLLCLine = it.next();
				assert invalidLLCLine.invalid();
				for (Line allLLCLine : allLLCLines) {
					if (allLLCLine.lineAddress().get() == invalidLLCLine.lineAddress().get()
							&& allLLCLine.valid()) {
						it.remove();
					}
				}
			}

			// Now iterate over all cache lines in all processors
			final HashSet<Line> privateLines = new HashSet<Line>();
			HierarchicalCache.LineVisitor<Line> lv = new HierarchicalCache.LineVisitor<Line>() {
				@Override
				public void visit(Line line) {
					if (line.valid() && line.lineAddress() != null) {
						privateLines.add(line);
					}
				}
			};
			for (Processor<Line> p : allProcessors) {
				p.L1cache.visitAllLines(lv);
			}

			// Now compare the two sets
			for (Line inv : invalidLLCLines) {
				for (Line priv : privateLines) {
					if (priv.lineAddress().get() == inv.lineAddress().get() && priv.valid()) {
						throw new RuntimeException(
								"Invalid lines in LLC should not be present and valid in any private cache.");
					}
				}
			}

		}

		private void verifyCacheIndexing() {
			assert ViserSim.XASSERTS && ViserSim.xassertsEnabled();

			for (Processor<Line> p : allProcessors) {
				p.L1cache.verifyIndices();

				if (p.L2cache != null) {
					p.L2cache.verifyIndices();
				}
			}

			if (L3cache != null) {
				L3cache.verifyIndices();
			}
		}

		private void verifyTCCRegionOverflowBreakdown(final Processor<Line> proc) {
			double target = proc.stats.pc_RegionBoundaries.get();
			double actual = proc.stats.pc_TCCRegionsFirstCacheOverflows8K.get()
					+ proc.stats.pc_TCCRegionsWBOverflows8K.get();
			assert target >= actual : "Sum8 should be less " + ViserSim.totalEvents;
			actual = proc.stats.pc_TCCRegionsFirstCacheOverflows16K.get()
					+ proc.stats.pc_TCCRegionsWBOverflows16K.get();
			assert target >= actual : "Sum16 should be less " + ViserSim.totalEvents;
			actual = proc.stats.pc_TCCRegionsFirstCacheOverflows32K.get()
					+ proc.stats.pc_TCCRegionsWBOverflows32K.get();
			assert target >= actual : "Sum32 should be less " + ViserSim.totalEvents;
			actual = proc.stats.pc_TCCRegionsFirstCacheOverflows64K.get()
					+ proc.stats.pc_TCCRegionsWBOverflows64K.get();
			assert target >= actual : "Sum64 should be less " + ViserSim.totalEvents;
		}

		private void verifyExecutionCostBreakdown(final Processor<Line> proc) {
			assert ViserSim.XASSERTS && ViserSim.xassertsEnabled();

			double target = proc.stats.pc_ExecDrivenCycleCount.get();
			double actual = proc.stats.pc_ViserRegExecExecDrivenCycleCount.get()
					+ proc.stats.pc_ViserPreCommitExecDrivenCycleCount.get()
					+ proc.stats.pc_ViserReadValidationExecDrivenCycleCount.get()
					+ proc.stats.pc_ViserPostCommitExecDrivenCycleCount.get();
			assert target == actual : "Values differ: " + ViserSim.totalEvents;

			target = proc.stats.pc_BandwidthDrivenCycleCount.get();
			actual = proc.stats.pc_ViserRegExecBWDrivenCycleCount.get()
					+ proc.stats.pc_ViserPreCommitBWDrivenCycleCount.get()
					+ proc.stats.pc_ViserReadValidationBWDrivenCycleCount.get()
					+ proc.stats.pc_ViserPostCommitBWDrivenCycleCount.get();
			assert target == actual : "Values differ: " + ViserSim.totalEvents;

			target = proc.stats.pc_OnChipNetworkMessages.get();
			actual = proc.stats.pc_ViserRegExecOnChipNetworkMessages.get()
					+ proc.stats.pc_ViserPreCommitOnChipNetworkMessages.get()
					+ proc.stats.pc_ViserReadValidationOnChipNetworkMessages.get()
					+ proc.stats.pc_ViserPostCommitOnChipNetworkMessages.get();
			assert target == actual : "Values differ: " + ViserSim.totalEvents;

			target = proc.stats.pc_OnChipNetworkMessageSize16BytesFlits.get();
			actual = proc.stats.pc_ViserRegExecOnChipNetworkMessageSize16BytesFlits.get()
					+ proc.stats.pc_ViserPreCommitOnChipNetworkMessageSize16BytesFlits.get()
					+ proc.stats.pc_ViserReadValidationOnChipNetworkMessageSize16BytesFlits.get()
					+ proc.stats.pc_ViserPostCommitOnChipNetworkMessageSize16BytesFlits.get();
			assert target == actual : "Values differ: " + ViserSim.totalEvents;
		}

		private void verifyPrivateCacheLinesAreInvalid(final Processor<Line> proc) {
			assert ViserSim.XASSERTS && ViserSim.xassertsEnabled();

			HierarchicalCache.LineVisitor<Line> lv = new HierarchicalCache.LineVisitor<Line>() {
				@Override
				public void visit(Line line) {
					assert line.id() == proc.id : "Private line should be owned by the same core";
					if (line.valid()) {
						// THIS DOES NOT ALWAYS WORK, ESPECIALLY IF WE ARE NOT
						// INVALIDATING READ-ONLY LINES
						assert false : "Private line should be INVALID";
					}
				}
			};
			L1cache.visitAllLines(lv);
			L2cache.visitAllLines(lv);
		}

		/**
		 * L1 and L2 cache are inclusive in this design. Meaningful only for valid lines. The cache
		 * line versions for VALID lines should be the same in both L1 and L2 caches.
		 */
		public void verifyPrivateCacheInclusivityAndVersions(final Processor<Line> proc) {
			assert ViserSim.XASSERTS && ViserSim.xassertsEnabled();

			// Only valid is L2 is enabled
			if (params.useL2()) {
				final HashSet<Line> l1Set = new HashSet<Line>();
				HierarchicalCache.LineVisitor<Line> l1Lv = new HierarchicalCache.LineVisitor<Line>() {
					@Override
					public void visit(Line line) {
						if (line.valid()) {
							assert line
									.id() == proc.id : "Private line should be owned by the same core";
							l1Set.add(line);
						}
					}
				};
				L1cache.visitAllLines(l1Lv);

				final HashSet<Line> l2Set = new HashSet<Line>();
				HierarchicalCache.LineVisitor<Line> l2Lv = new HierarchicalCache.LineVisitor<Line>() {
					@Override
					public void visit(Line line) {
						if (line.valid()) {
							assert line
									.id() == proc.id : "Private line should be owned by the same core";
							l2Set.add(line);
						}
					}
				};
				L2cache.visitAllLines(l2Lv);

				for (Line l1Line : l1Set) {
					assert l1Line.valid();
					boolean found = false;
					for (Line l2Line : l2Set) {
						assert l2Line.valid();
						if (l1Line.lineAddress().get() == l2Line.lineAddress().get()) {
							found = true;
							// Inclusivity is satisfied for this line, check for
							// matching versions
							assert l1Line.getVersion() == l2Line
									.getVersion() : "L1 and L2 line versions should match";
							break;
						}
					}
					if (!found) {
						throw new RuntimeException("L1 and L2 violate inclusivity.");
					}
				}
			}
		}

		public void verifyDeferredLines(final Processor<Line> proc) {
			// Iterate over valid LLC lines
			final HashSet<Line> deferredLLCLines = new HashSet<Line>();
			HierarchicalCache.LineVisitor<Line> deferredLLCV = new HierarchicalCache.LineVisitor<Line>() {
				@Override
				public void visit(Line line) {
					if (line.valid() && line.isLineDeferred()) {
						deferredLLCLines.add(line);
					}
				}
			};
			L3cache.visitAllLines(deferredLLCV);

			// Now check for the correctness of individual deferred lines
			for (Line dl : deferredLLCLines) {
				Processor<Line> ownerCore = proc.machine
						.getProc(new CpuId(dl.getDeferredLineOwnerID()));
				MemoryResponse<Line> privateResp = ownerCore.L1cache.searchPrivateCache(dl);
				if (privateResp.lineHit == null) {
					System.out.println(ViserSim.totalEvents);
					System.out.println(dl);
				}
				assert privateResp.lineHit != null;
				assert privateResp.lineHit.lineAddress().get() == dl.lineAddress().get();

				if (proc.params.areDeferredWriteBacksPrecise()) {
					Long writeMd = ownerCore.getDeferredWriteMetadata(privateResp.lineHit);

					if (writeMd == null) {
						System.out.println(dl);

						System.out.println(privateResp.whereHit);
						System.out.println(privateResp.lineHit);
						System.out.println(privateResp.lineHit
								.getWriteEncoding(new CpuId(dl.getDeferredLineOwnerID())));
					}
					assert writeMd != null : privateResp.lineHit.toString();
				}
			}
		}

		public void verifyPrivateDeferredLines(final Processor<Line> proc) {
			Iterator<Map.Entry<Long, Long>> entries = proc.wrMdDeferredDirtyLines.entrySet()
					.iterator();
			while (entries.hasNext()) {
				Map.Entry<Long, Long> entry = entries.next();
				MemoryResponse<Line> resp = proc.L2cache
						.searchPrivateCache(new DataLineAddress(entry.getKey()));
				if (resp.lineHit == null) {
					System.out.println(ViserSim.totalEvents);
					System.out.println(proc);
					System.out.println("Line address:" + entry.getKey());
					System.out.println(proc.L2cache.getLine(new DataLineAddress(entry.getKey())));
				}
				assert resp.lineHit != null : "Line address:" + entry.getKey();
			}
		}

	} // end class Verifier

	Verifier Verify = new Verifier();

} // end class Processor
