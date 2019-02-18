import collections

from options.constants import Constants


class PintoolKeys(Constants):
    TOTAL_EVENTS_KEY = "totalEvents"
    TOTAL_EVENTS = "total events"

    ROI_START_KEY = "roiStart"
    ROI_START = "roi start"

    ROI_END_KEY = "roiEnd"
    ROI_END = "roi end"

    THREAD_BEGIN_KEY = "threadBegins"
    THREAD_BEGIN = "thread begin"

    THREAD_END_KEY = "threadEnd"
    THREAD_END = "thread end"

    MEMORY_EVENTS_KEY = "memoryEvents"
    MEMORY_EVENTS = "memory events"

    READ_EVENTS_KEY = "readEvents"
    READ_EVENTS = "reads"

    WRITE_EVENTS_KEY = "writeEvents"
    WRITE_EVENTS = "writes"

    BASIC_BLOCKS_KEY = "basicBlocks"
    BASIC_BLOCKS = "basic blocks"

    LOCK_ACQS_KEY = "lockAcqs"
    LOCK_ACQS = "lock acquires"

    LOCK_RELS_KEY = "lockRels"
    LOCK_RELS = "lock releases"

    LOCK_ACQ_READS_KEY = "lockAcqReads"
    LOCK_ACQ_READS = "lock acquire reads"

    LOCK_ACQ_WRITES_KEY = "lockAcqWrites"
    LOCK_ACQ_WRITES = "lock acquire writes"

    LOCK_REL_WRITES_KEY = "lockRelWrites"
    LOCK_REL_WRITES = "lock release writes"

    ATOMIC_READS_KEY = "atomicReads"
    ATOMIC_READS = "atomic reads"

    ATOMIC_WRITES_KEY = "atomicWrites"
    ATOMIC_WRITES = "atomic writes"

    THREAD_SPAWN_KEY = "threadSpawns"
    THREAD_SPAWN = "thread spawns"

    THREAD_JOIN_KEY = "threadJoins"
    THREAD_JOIN = "thread joins"


class SimKeys(Constants):
    """These are simulator stats keys"""

    L1_READ_HITS_KEY = "g_Data_L1ReadHits"
    L1_READ_MISSES_KEY = "g_Data_L1ReadMisses"
    L1_WRITE_HITS_KEY = "g_Data_L1WriteHits"
    L1_WRITE_MISSES_KEY = "g_Data_L1WriteMisses"
    L1_LINE_EVICTIONS_KEY = "g_Data_L1LineEvictions"
    L1_DIRTY_LINE_EVICTIONS_KEY = "g_Data_L1DirtyLineEvictions"
    L1_ATOMIC_READ_HITS_KEY = "g_Data_L1AtomicReadHits"
    L1_ATOMIC_READ_MISSES_KEY = "g_Data_L1AtomicReadMisses"
    L1_ATOMIC_WRITE_HITS_KEY = "g_Data_L1AtomicWriteHits"
    L1_ATOMIC_WRITE_MISSES_KEY = "g_Data_L1AtomicWriteMisses"
    L1_LOCK_READ_HITS_KEY = "g_Data_L1LockReadHits"
    L1_LOCK_READ_MISSES_KEY = "g_Data_L1LockReadMisses"
    L1_LOCK_WRITE_HITS_KEY = "g_Data_L1LockWriteHits"
    L1_LOCK_WRITE_MISSES_KEY = "g_Data_L1LockWriteMisses"

    L2_READ_HITS_KEY = "g_Data_L2ReadHits"
    L2_READ_MISSES_KEY = "g_Data_L2ReadMisses"
    L2_WRITE_HITS_KEY = "g_Data_L2WriteHits"
    L2_WRITE_MISSES_KEY = "g_Data_L2WriteMisses"
    L2_LINE_EVICTIONS_KEY = "g_Data_L2LineEvictions"
    L2_DIRTY_LINE_EVICTIONS_KEY = "g_Data_L2DirtyLineEvictions"
    L2_ATOMIC_READ_HITS_KEY = "g_Data_L2AtomicReadHits"
    L2_ATOMIC_READ_MISSES_KEY = "g_Data_L2AtomicReadMisses"
    L2_ATOMIC_WRITE_HITS_KEY = "g_Data_L2AtomicWriteHits"
    L2_ATOMIC_WRITE_MISSES_KEY = "g_Data_L2AtomicWriteMisses"
    L2_LOCK_READ_HITS_KEY = "g_Data_L2LockReadHits"
    L2_LOCK_READ_MISSES_KEY = "g_Data_L2LockReadMisses"
    L2_LOCK_WRITE_HITS_KEY = "g_Data_L2LockWriteHits"
    L2_LOCK_WRITE_MISSES_KEY = "g_Data_L2LockWriteMisses"

    L3_READ_HITS_KEY = "g_Data_L3ReadHits"
    L3_READ_MISSES_KEY = "g_Data_L3ReadMisses"
    L3_WRITE_HITS_KEY = "g_Data_L3WriteHits"
    L3_WRITE_MISSES_KEY = "g_Data_L3WriteMisses"
    L3_LINE_EVICTIONS_KEY = "g_Data_L3LineEvictions"
    L3_DIRTY_LINE_EVICTIONS_KEY = "g_Data_L3DirtyLineEvictions"
    L3_ATOMIC_READ_HITS_KEY = "g_Data_L3AtomicReadHits"
    L3_ATOMIC_READ_MISSES_KEY = "g_Data_L3AtomicReadMisses"
    L3_ATOMIC_WRITE_HITS_KEY = "g_Data_L3AtomicWriteHits"
    L3_ATOMIC_WRITE_MISSES_KEY = "g_Data_L3AtomicWriteMisses"
    L3_LOCK_READ_HITS_KEY = "g_Data_L3LockReadHits"
    L3_LOCK_READ_MISSES_KEY = "g_Data_L3LockReadMisses"
    L3_LOCK_WRITE_HITS_KEY = "g_Data_L3LockWriteHits"
    L3_LOCK_WRITE_MISSES_KEY = "g_Data_L3LockWriteMisses"

    TOTAL_READS_KEY = "g_TotalDataReads"
    TOTAL_WRITES_KEY = "g_TotalDataWrites"
    TOTAL_MEMORY_ACCESSES_KEY = "g_TotalMemoryAccesses"

    TOTAL_ATOMIC_READS_KEY = "g_TotalAtomicReads"
    TOTAL_ATOMIC_WRITES_KEY = "g_TotalAtomicWrites"
    TOTAL_ATOMIC_ACCESSES_KEY = "g_TotalAtomicAccesses"

    TOTAL_LOCK_READS_KEY = "g_TotalLockReads"
    TOTAL_LOCK_WRITES_KEY = "g_TotalLockWrites"
    TOTAL_LOCK_ACCESSES_KEY = "g_TotalLockAccesses"

    # EXECUTION_CYCLE_COUNT_KEY = "max_ExecutionDrivenCycleCount"
    # For MESI, exec-driven and bandwidth-driven should be the same
    BANDWIDTH_CYCLE_COUNT_KEY = "max_BandwidthDrivenCycleCount"

    REGION_BOUNDARIES_KEY = "g_RegionBoundaries"
    REGION_WITH_WRITES_KEY = "g_RegionsWithWrites"

    RUNNING_TIME_KEY = "SimulationRunningTimeMins"
    MEMORY_USAGE_KEY = "MemUsageGB"

    TOTAL_EVENTS_KEY = "TotalEvents"
    STACK_ACCESSES_KEY = "StackAccesses"
    REGION_SIZE_KEY = "AverageRegionSize"
    BASIC_BLOCKS_KEY = "BasicBlocks"
    INSTRUCTIONS_KEY = "Instructions"  # We bill one cycle for all instructions

    # CORELLC_NETWORK_MSGS_KEY = "g_CoreLLCNetworkMessages"
    # # CORELLC_NETWORKMSG_SIZE_BYTES_KEY = "g_CoreLLCNetworkMessageSizeBytes"
    # # CORELLC_NETWORKMSG_SIZE_4BYTES_FLITS_KEY = (
    # #     "g_CoreLLCNetworkMessageSize4BytesFlits")
    # # CORELLC_NETWORKMSG_SIZE_8BYTES_FLITS_KEY = (
    # #     "g_CoreLLCNetworkMessageSize8BytesFlits")
    # CORELLC_NETWORKMSG_SIZE_16BYTES_FLITS_KEY = "g_CoreLLCNetworkMessageSize16BytesFlits"
    # # CORELLC_NETWORKMSG_SIZE_32BYTES_FLITS_KEY = (
    # #     "g_CoreLLCNetworkMessageSize32BytesFlits")

    ONCHIP_NETWORK_MSGS_KEY = "g_OnChipNetworkMessages"
    # ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = "g_OnChipNetworkMessageSizeBytes"
    # ONCHIP_NETWORKMSG_SIZE_4BYTES_FLITS_KEY = (
    #     "g_OnChipNetworkMessageSize4BytesFlits")
    # ONCHIP_NETWORKMSG_SIZE_8BYTES_FLITS_KEY = (
    #     "g_OnChipNetworkMessageSize8BytesFlits")
    ONCHIP_NETWORKMSG_SIZE_16BYTES_FLITS_KEY = "g_OnChipNetworkMessageSize16BytesFlits"
    # ONCHIP_NETWORKMSG_SIZE_32BYTES_FLITS_KEY = (
    #     "g_OnChipNetworkMessageSize32BytesFlits")

    # LLC_MEM_MSGS_KEY = "g_LLCToMemoryMessages"
    # LLC_MEM_MSG_SIZE_BYTES_KEY = "g_LLCToMemoryMessageSizeBytes"
    # LLC_MEM_MSG_SIZE_4BYTES_FLITS_KEY = "g_LLCToMemoryMessageSize4BytesFlits"
    # LLC_MEM_MSG_SIZE_8BYTES_FLITS_KEY = "g_LLCToMemoryMessageSize8BytesFlits"
    # LLC_MEM_MSG_SIZE_16BYTES_FLITS_KEY = "g_LLCToMemoryMessageSize16BytesFlits"
    # LLC_MEM_MSG_SIZE_32BYTES_FLITS_KEY = (
    #     "g_LLCToMemoryMessageSize32BytesFlits")

    # LLC_MEM_MSG_READ_16BYTES_FLITS_KEY = "g_LLCToMemoryRead16BytesFlits"
    # LLC_MEM_MSG_WRITE_16BYTES_FLITS_KEY = "g_LLCToMemoryRead16BytesFlits"

    # This key is off-chip traffic, just in 64B packets.
    # LLC_MEM_MSG_64BYTES_FLITS_KEY = "g_LLCToMemoryMessageSize64BytesFlits"
    # LLC_MEM_MSG_READ_64BYTES_FLITS_KEY = "g_LLCToMemoryRead64BytesFlits"
    # LLC_MEM_MSG_WRITE_64BYTES_FLITS_KEY = "g_LLCToMemoryWrite64BytesFlits"

    MEM_64BYTES_ACCESSES_KEY = "g_Memory64BytesAccesses"
    MEM_64BYTES_READS_KEY = "g_Memory64BytesReads"
    MEM_64BYTES_WRITES_KEY = "g_Memory64BytesWrites"

    # RATIO_LLC_MEM_MSGS_EXEC_CYCLES_KEY = (
    #     "ratioViserLLCToMemoryMetadataWritebackExecutionCycles")
    # RATIO_LLC_MEM_MSGS_BANDWIDTH_CYCLES_KEY = (
    #     "ratioViserLLCToMemoryMetadataWritebackBandwidthCycles")

    # Max On-chip - This is the max bandwidth required among cores. Probably not what we want and
    # is kind of confusing.
    # MAX_REQD_BW_4BYTES_FLITS_KEY = "max_reqdBWInGBWith4BytesFlits"
    # MAX_REQD_BW_8BYTES_FLITS_KEY = "max_reqdBWInGBWith8BytesFlits"
    # MAX_REQD_BW_16BYTES_FLITS_KEY = "max_reqdBWInGBWith16BytesFlits"
    # MAX_REQD_BW_32BYTES_FLITS_KEY = "max_reqdBWInGBWith32BytesFlits"

    # Sum On-chip - This is the sum of bandwidth required across all cores.
    SUM_REQD_ONCHIPBW_16BYTES_FLITS_KEY = "sum_reqdOnChipBWInGBWith16BytesFlits"
    # Sum Off-chip
    SUM_REQD_OFFCHIPBW_64BYTES_FLITS_KEY = "sum_reqdOffChipBWInGBWith64BytesFlits"


class MESISimKeys(Constants):
    REMOTE_READ_HITS_KEY = "g_MESIReadRemoteHits"
    REMOTE_WRITE_HITS_KEY = "g_MESIWriteRemoteHits"
    UPGRADE_MISSES_KEY = "g_MESIUpgradeMisses"

    # We do not need the bandwidth-variants for this for MESI
    MEM_EXEC_CYCLE_COUNT_KEY = "dep_MESIMemSystemExecDrivenCycleCount"
    RATIO_MEM_EXEC_CYCLE_COUNT_KEY = ("ratioMESIMemSystemExecDrivenCycleCount")
    COHERENCE_EXEC_CYCLE_COUNT_KEY = ("dep_MESICoherenceExecDrivenCycleCount")
    RATIO_COHERENCE_EXEC_CYCLE_COUNT_KEY = ("ratioMESICoherenceExecDrivenCycleCount")

    MEM_ONCHIP_NETWORK_MSGS_KEY = ("g_MESIMemoryOnChipNetworkMessages")
    RATIO_MEM_ONCHIP_NETWORK_MSGS_KEY = ("ratioMESIMemoryOnChipNetworkMessages")
    # MEM_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
    #     "g_MESIMemoryOnChipNetworkMessageSizeBytes")
    # RATIO_MEM_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
    #     "ratioMESIMemoryOnChipNetworkMessageSizeBytes")
    # MEM_ONCHIP_NETWORKMSG_SIZE_4BYTES_FLITS_KEY = (
    #     "g_MESIMemoryOnChipNetworkMessageSize4BytesFlits")
    # RATIO_MEM_ONCHIP_NETWORKMSG_SIZE_4BYTES_FLITS_KEY = (
    #     "ratioMESIMemoryOnChipNetworkMessageSize4BytesFlits")
    # MEM_ONCHIP_NETWORKMSG_SIZE_8BYTES_FLITS_KEY = (
    #     "g_MESIMemoryOnChipNetworkMessageSize8BytesFlits")
    # RATIO_MEM_ONCHIP_NETWORKMSG_SIZE_8BYTES_FLITS_KEY = (
    #     "ratioMESIMemoryOnChipNetworkMessageSize4BytesFlits")
    MEM_ONCHIP_NETWORKMSG_SIZE_16BYTES_FLITS_KEY = (
        "g_MESIMemoryOnChipNetworkMessageSize16BytesFlits")
    RATIO_MEM_ONCHIP_NETWORKMSG_SIZE_16BYTES_FLITS_KEY = (
        "ratioMESIMemoryOnChipNetworkMessageSize16BytesFlits")
    # MEM_ONCHIP_NETWORKMSG_SIZE_32BYTES_FLITS_KEY = (
    #     "g_MESIMemoryOnChipNetworkMessageSize32BytesFlits")
    # RATIO_MEM_ONCHIP_NETWORKMSG_SIZE_32BYTES_FLITS_KEY = (
    #     "ratioMESIMemoryOnChipNetworkMessageSize32BytesFlits")

    COHERENCE_ONCHIP_NETWORK_MSGS_KEY = ("g_MESICoherenceOnChipNetworkMessages")
    RATIO_COHERENCE_ONCHIP_NETWORK_MSGS_KEY = ("ratioMESICoherenceOnChipNetworkMessages")
    # COHERENCE_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
    #     "g_MESICoherenceOnChipNetworkMessageSizeBytes")
    # RATIO_COHERENCE_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
    #     "ratioMESICoherenceOnChipNetworkMessageSizeBytes")
    # COHERENCE_ONCHIP_NETWORKMSG_SIZE_4BYTES_FLITS_KEY = (
    #     "g_MESICoherenceOnChipNetworkMessageSize4BytesFlits")
    # RATIO_COHERENCE_ONCHIP_NETWORKMSG_SIZE_4BYTES_FLITS_KEY = (
    #     "ratioMESICoherenceOnChipNetworkMessageSize4BytesFlits")
    # COHERENCE_ONCHIP_NETWORKMSG_SIZE_8BYTES_FLITS_KEY = (
    #     "g_MESICoherenceOnChipNetworkMessageSize8BytesFlits")
    # RATIO_COHERENCE_ONCHIP_NETWORKMSG_SIZE_8BYTES_FLITS_KEY = (
    #     "ratioMESICoherenceOnChipNetworkMessageSize8BytesFlits")
    COHERENCE_ONCHIP_NETWORKMSG_SIZE_16BYTES_FLITS_KEY = (
        "g_MESICoherenceOnChipNetworkMessageSize16BytesFlits")
    RATIO_COHERENCE_ONCHIP_NETWORKMSG_SIZE_16BYTES_FLITS_KEY = (
        "ratioMESICoherenceOnChipNetworkMessageSize16BytesFlits")
    # COHERENCE_ONCHIP_NETWORKMSG_SIZE_32BYTES_FLITS_KEY = (
    #     "g_MESICoherenceOnChipNetworkMessageSize32BytesFlits")
    # RATIO_COHERENCE_ONCHIP_NETWORKMSG_SIZE_32BYTES_FLITS_KEY = (
    #     "ratioMESICoherenceOnChipNetworkMessageSize32BytesFlits")


class PauseSimKeys(Constants):
    TOTAL_MEMORY_ACCESSES_SPECIAL_INVALID_KEY = ("g_TotalMemoryAccessesSpecialInvalidState")
    WRITE_AFTER_READ_UPGRADES_KEY = "g_ViserWARUpgrades"

    AIM_READ_HITS_KEY = "g_AIMCacheReadHits"
    AIM_READ_MISSES_KEY = "g_AIMCacheReadMisses"
    AIM_WRITE_HITS_KEY = "g_AIMCacheWriteHits"
    AIM_WRITE_MISSES_KEY = "g_AIMCacheWriteMisses"
    AIM_LINE_EVICTIONS_KEY = "g_AIMCacheLineEvictions"

    # bw driven cycles
    RESTART_BW_CYCLE_COUNT_KEY = ("dep_ViserRestartBWDrivenCycleCount")
    RATIO_RESTART_BW_CYCLE_COUNT_KEY = ("ratioViserRestartBWDrivenCycleCount")
    PAUSE_BW_CYCLE_COUNT_KEY = ("dep_ViserPauseBWDrivenCycleCount")
    RATIO_PAUSE_BW_CYCLE_COUNT_KEY = ("ratioViserPauseBWDrivenCycleCount")
    REG_EXEC_BW_CYCLE_COUNT_KEY = "dep_ViserRegExecBWDrivenCycleCount"
    RATIO_REG_EXEC_BW_CYCLE_COUNT_KEY = ("ratioViserRegExecBWDrivenCycleCount")
    PRE_COMMIT_BW_CYCLE_COUNT_KEY = ("dep_ViserPreCommitBWDrivenCycleCount")
    RATIO_PRE_COMMIT_BW_CYCLE_COUNT_KEY = ("ratioViserPreCommitBWDrivenCycleCount")
    READ_VALIDATION_BW_CYCLE_COUNT_KEY = ("dep_ViserReadValidationBWDrivenCycleCount")
    RATIO_READ_VALIDATION_BW_CYCLE_COUNT_KEY = ("ratioViserReadValidationBWDrivenCycleCount")
    POST_COMMIT_BW_CYCLE_COUNT_KEY = ("dep_ViserPostCommitBWDrivenCycleCount")
    RATIO_POST_COMMIT_BW_CYCLE_COUNT_KEY = ("ratioViserPostCommitBWDrivenCycleCount")

    NUM_SCAVENGES_KEY = "g_NumScavenges"

    SCAVENGE_TIME_KEY = "ScavengeRunningTimeMins"

    # on-chip traffic
    RESTART_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = ("g_ViserRestartOnChipNetworkMessageSizeBytes")
    RATIO_RESTART_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
        "ratioViserRestartOnChipNetworkMessageSizeBytes")
    RESTART_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "g_ViserRestartOnChipNetworkMessageSize4BytesFlits")
    RATIO_RESTART_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "ratioViserRestartOnChipNetworkMessageSize4BytesFlits")
    RESTART_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "g_ViserRestartOnChipNetworkMessageSize8BytesFlits")
    RATIO_RESTART_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "ratioViserRestartOnChipNetworkMessageSize8BytesFlits")
    RESTART_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "g_ViserRestartOnChipNetworkMessageSize16BytesFlits")
    RATIO_RESTART_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "ratioViserRestartOnChipNetworkMessageSize16BytesFlits")
    RESTART_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "g_ViserRestartOnChipNetworkMessageSize32BytesFlits")
    RATIO_RESTART_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "ratioViserRestartOnChipNetworkMessageSize32BytesFlits")

    # off-chip traffic
    RESTART_OFFCHIP_NETWORKMSG_SIZE_BYTES_KEY = ("g_ViserRestartOffChipNetworkMessageSizeBytes")
    RATIO_RESTART_OFFCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
        "ratioViserRestartOffChipNetworkMessageSizeBytes")
    RESTART_OFFCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "g_ViserRestartOffChipNetworkMessageSize4BytesFlits")
    RATIO_RESTART_OFFCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "ratioViserRestartOffChipNetworkMessageSize4BytesFlits")
    RESTART_OFFCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "g_ViserRestartOffChipNetworkMessageSize8BytesFlits")
    RATIO_RESTART_OFFCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "ratioViserRestartOffChipNetworkMessageSize8BytesFlits")
    RESTART_OFFCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "g_ViserRestartOffChipNetworkMessageSize16BytesFlits")
    RATIO_RESTART_OFFCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "ratioViserRestartOffChipNetworkMessageSize16BytesFlits")
    RESTART_OFFCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "g_ViserRestartOffChipNetworkMessageSize32BytesFlits")
    RATIO_RESTART_OFFCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "ratioViserRestartOffChipNetworkMessageSize32BytesFlits")

    NON_RESTART_OFFCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
        "g_ViserNonRestartOffChipNetworkMessageSizeBytes")
    RATIO_NON_RESTART_OFFCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
        "ratioViserNonRestartOffChipNetworkMessageSizeBytes")
    NON_RESTART_OFFCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "g_ViserNonRestartOffChipNetworkMessageSize4BytesFlits")
    RATIO_NON_RESTART_OFFCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "ratioViserNonRestartOffChipNetworkMessageSize4BytesFlits")
    NON_RESTART_OFFCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "g_ViserNonRestartOffChipNetworkMessageSize8BytesFlits")
    RATIO_NON_RESTART_OFFCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "ratioViserNonRestartOffChipNetworkMessageSize8BytesFlits")
    NON_RESTART_OFFCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "g_ViserNonRestartOffChipNetworkMessageSize16BytesFlits")
    RATIO_NON_RESTART_OFFCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "ratioViserNonRestartOffChipNetworkMessageSize16BytesFlits")
    NON_RESTART_OFFCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "g_ViserNonRestartOffChipNetworkMessageSize32BytesFlits")
    RATIO_NON_RESTART_OFFCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "ratioViserNonRestartOffChipNetworkMessageSize32BytesFlits")

    REG_EXEC_ONCHIP_NETWORK_MSGS_KEY = ("g_ViserRegExecOnChipNetworkMessages")
    RATIO_REG_EXEC_ONCHIP_NETWORK_MSGS_KEY = ("ratioViserRegExecOnChipNetworkMessages")
    REG_EXEC_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = ("g_ViserRegExecOnChipNetworkMessageSizeBytes")
    RATIO_REG_EXEC_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
        "ratioViserRegExecOnChipNetworkMessageSizeBytes")
    REG_EXEC_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "g_ViserRegExecOnChipNetworkMessageSize4BytesFlits")
    RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "ratioViserRegExecOnChipNetworkMessageSize4BytesFlits")
    REG_EXEC_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "g_ViserRegExecOnChipNetworkMessageSize8BytesFlits")
    RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "ratioViserRegExecOnChipNetworkMessageSize8BytesFlits")
    REG_EXEC_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "g_ViserRegExecOnChipNetworkMessageSize16BytesFlits")
    RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "ratioViserRegExecOnChipNetworkMessageSize16BytesFlits")
    REG_EXEC_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "g_ViserRegExecOnChipNetworkMessageSize32BytesFlits")
    RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "ratioViserRegExecOnChipNetworkMessageSize32BytesFlits")

    REG_EXEC_ONCHIP_NETWORK_MSGS_KEY = ("g_ViserRegExecOnChipNetworkMessages")
    RATIO_REG_EXEC_ONCHIP_NETWORK_MSGS_KEY = ("ratioViserRegExecOnChipNetworkMessages")
    REG_EXEC_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = ("g_ViserRegExecOnChipNetworkMessageSizeBytes")
    RATIO_REG_EXEC_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
        "ratioViserRegExecOnChipNetworkMessageSizeBytes")
    REG_EXEC_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "g_ViserRegExecOnChipNetworkMessageSize4BytesFlits")
    RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "ratioViserRegExecOnChipNetworkMessageSize4BytesFlits")
    REG_EXEC_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "g_ViserRegExecOnChipNetworkMessageSize8BytesFlits")
    RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "ratioViserRegExecOnChipNetworkMessageSize8BytesFlits")
    REG_EXEC_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "g_ViserRegExecOnChipNetworkMessageSize16BytesFlits")
    RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "ratioViserRegExecOnChipNetworkMessageSize16BytesFlits")
    REG_EXEC_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "g_ViserRegExecOnChipNetworkMessageSize32BytesFlits")
    RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "ratioViserRegExecOnChipNetworkMessageSize32BytesFlits")

    PRE_COMMIT_ONCHIP_NETWORK_MSGS_KEY = ("g_ViserPreCommitOnChipNetworkMessages")
    RATIO_PRE_COMMIT_ONCHIP_NETWORK_MSGS_KEY = ("ratioViserPreCommitOnChipNetworkMessages")
    PRE_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = ("g_ViserPreCommitOnChipNetworkMessageSizeBytes")
    RATIO_PRE_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
        "ratioViserPreCommitOnChipNetworkMessageSizeBytes")
    PRE_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "g_ViserPreCommitOnChipNetworkMessageSize4BytesFlits")
    RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "ratioViserPreCommitOnChipNetworkMessageSize4BytesFlits")
    PRE_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "g_ViserPreCommitOnChipNetworkMessageSize8BytesFlits")
    RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "ratioViserPreCommitOnChipNetworkMessageSize8BytesFlits")
    PRE_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "g_ViserPreCommitOnChipNetworkMessageSize16BytesFlits")
    RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "ratioViserPreCommitOnChipNetworkMessageSize16BytesFlits")
    PRE_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "g_ViserPreCommitOnChipNetworkMessageSize32BytesFlits")
    RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "ratioViserPreCommitOnChipNetworkMessageSize32BytesFlits")

    READ_VALIDATION_ONCHIP_NETWORK_MSGS_KEY = ("g_ViserReadValidationOnChipNetworkMessages")
    RATIO_READ_VALIDATION_ONCHIP_NETWORK_MSGS_KEY = (
        "ratioViserReadValidationOnChipNetworkMessages")
    READ_VALIDATION_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
        "g_ViserReadValidationOnChipNetworkMessageSizeBytes")
    RATIO_READ_VALIDATION_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
        "ratioViserReadValidationOnChipNetworkMessageSizeBytes")
    READ_VALIDATION_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "g_ViserReadValidationOnChipNetworkMessageSize4BytesFlits")
    RATIO_READ_VALIDATION_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "ratioViserReadValidationOnChipNetworkMessageSize4BytesFlits")
    READ_VALIDATION_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "g_ViserReadValidationOnChipNetworkMessageSize8BytesFlits")
    RATIO_READ_VALIDATION_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "ratioViserReadValidationOnChipNetworkMessageSize8BytesFlits")
    READ_VALIDATION_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "g_ViserReadValidationOnChipNetworkMessageSize16BytesFlits")
    RATIO_READ_VALIDATION_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "ratioViserReadValidationOnChipNetworkMessageSize16BytesFlits")
    READ_VALIDATION_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "g_ViserReadValidationOnChipNetworkMessageSize32BytesFlits")
    RATIO_READ_VALIDATION_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "ratioViserReadValidationOnChipNetworkMessageSize32BytesFlits")

    POST_COMMIT_ONCHIP_NETWORK_MSGS_KEY = ("g_ViserPostCommitOnChipNetworkMessages")
    RATIO_POST_COMMIT_ONCHIP_NETWORK_MSGS_KEY = ("ratioViserPostCommitOnChipNetworkMessages")
    POST_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
        "g_ViserPostCommitOnChipNetworkMessageSizeBytes")
    RATIO_POST_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
        "ratioViserPostCommitOnChipNetworkMessageSizeBytes")
    POST_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "g_ViserPostCommitOnChipNetworkMessageSize4BytesFlits")
    RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "ratioViserPostCommitOnChipNetworkMessageSize4BytesFlits")
    POST_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "g_ViserPostCommitOnChipNetworkMessageSize8BytesFlits")
    RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "ratioViserPostCommitOnChipNetworkMessageSize8BytesFlits")
    POST_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "g_ViserPostCommitOnChipNetworkMessageSize16BytesFlits")
    RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "ratioViserPostCommitOnChipNetworkMessageSize16BytesFlits")
    POST_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "g_ViserPostCommitOnChipNetworkMessageSize32BytesFlits")
    RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "ratioViserPostCommitOnChipNetworkMessageSize32BytesFlits")

    UPGRADE_NETWORK_MSGS_KEY = "g_ViserUpgradeMessages"
    RATIO_UPGRADE_NETWORK_MSGS_KEY = "ratioViserUpgradeMessages"
    UPGRADE_NETWORKMSG_BYTES_KEY = "g_ViserUpgradeMessageSizeBytes"
    RATIO_UPGRADE_NETWORKMSG_BYTES_KEY = ("ratioViserUpgradeMessageSizeBytes")
    UPGRADE_NETWORKMSG_SIZE_4BYTES_FLITS_KEY = ("g_ViserUpgradeMessageSize4BytesFlits")
    RATIO_UPGRADE_NETWORKMSG_SIZE_4BYTES_FLITS_KEY = ("ratioViserUpgradeMessageSize4BytesFlits")
    UPGRADE_NETWORKMSG_SIZE_8BYTES_FLITS_KEY = ("g_ViserUpgradeMessageSize8BytesFlits")
    RATIO_UPGRADE_NETWORKMSG_SIZE_8BYTES_FLITS_KEY = ("ratioViserUpgradeMessageSize8BytesFlits")
    UPGRADE_NETWORKMSG_SIZE_16BYTES_FLITS_KEY = ("g_ViserUpgradeMessageSize16BytesFlits")
    RATIO_UPGRADE_NETWORKMSG_SIZE_16BYTES_FLITS_KEY = ("ratioViserUpgradeMessageSize16BytesFlits")
    UPGRADE_NETWORKMSG_SIZE_32BYTES_FLITS_KEY = ("g_ViserUpgradeMessageSize32BytesFlits")
    RATIO_UPGRADE_NETWORKMSG_SIZE_32BYTES_FLITS_KEY = ("ratioViserUpgradeMessageSize32BytesFlits")

    # regions
    CONFLICTED_REGIONS_KEY = "g_RegionsWithTolerableConflicts"
    DEADLOCKED_REGIONS_KEY = "g_RegionsWithPotentialDeadlocks"
    DEADLOCKED_REGIONS_WITH_DIRTY_EVICTION_KEY = ("g_RegionHasDirtyEvictionBeforeDL")
    VALIDATION_FAILED_REGIONS_KEY = "g_RegionsWithFRVs"
    VALIDATION_FAILED_REGIONS_WITH_DIRTY_EVICTION_KEY = ("g_RegionHasDirtyEvictionBeforeFRV")

    # restarts
    WHOLE_APP_RESTARTS_KEY = "g_TotalWholeAppRestarts"
    REQUEST_REPROCESSING_KEY = "g_TotalTransRestarts"
    REGION_RESTARTS_KEY = "g_TotalRegionRestarts"

    # conflicts
    VALIDATION_ATTEMPTS_KEY = "g_ValidationAttempts"
    FAILED_VALIDATION_KEY = "g_FailedValidations"
    PRECISE_CONFLICTS_KEY = "g_PreciseConflicts"
    DEAD_LOCKS_KEY = "g_PotentialDeadlocks"

    L2_DIRTY_EVICTION_KEY = "g_DirtyL2Evictions"


class ViserSimKeys(Constants):
    TOTAL_MEMORY_ACCESSES_SPECIAL_INVALID_KEY = ("g_TotalMemoryAccessesSpecialInvalidState")
    WRITE_AFTER_READ_UPGRADES_KEY = "g_ViserWARUpgrades"

    AIM_READ_HITS_KEY = "g_AIMCacheReadHits"
    AIM_READ_MISSES_KEY = "g_AIMCacheReadMisses"
    AIM_WRITE_HITS_KEY = "g_AIMCacheWriteHits"
    AIM_WRITE_MISSES_KEY = "g_AIMCacheWriteMisses"
    AIM_LINE_EVICTIONS_KEY = "g_AIMCacheLineEvictions"
    # We do not track dirty line evictions for the AIM

    REG_EXEC_EXEC_CYCLE_COUNT_KEY = ("dep_ViserRegExecExecDrivenCycleCount")
    RATIO_REG_EXEC_EXEC_CYCLE_COUNT_KEY = ("ratioViserRegExecExecDrivenCycleCount")
    PRE_COMMIT_EXEC_CYCLE_COUNT_KEY = ("dep_ViserPreCommitExecDrivenCycleCount")
    RATIO_PRE_COMMIT_EXEC_CYCLE_COUNT_KEY = ("ratioViserPreCommitExecDrivenCycleCount")
    READ_VALIDATION_EXEC_CYCLE_COUNT_KEY = ("dep_ViserReadValidationExecDrivenCycleCount")
    RATIO_READ_VALIDATION_EXEC_CYCLE_COUNT_KEY = ("ratioViserReadValidationExecDrivenCycleCount")
    POST_COMMIT_EXEC_CYCLE_COUNT_KEY = ("dep_ViserPostCommitExecDrivenCycleCount")
    RATIO_POST_COMMIT_EXEC_CYCLE_COUNT_KEY = ("ratioViserPostCommitExecDrivenCycleCount")

    REG_EXEC_BW_CYCLE_COUNT_KEY = "dep_ViserRegExecBWDrivenCycleCount"
    RATIO_REG_EXEC_BW_CYCLE_COUNT_KEY = ("ratioViserRegExecBWDrivenCycleCount")
    PRE_COMMIT_BW_CYCLE_COUNT_KEY = ("dep_ViserPreCommitBWDrivenCycleCount")
    RATIO_PRE_COMMIT_BW_CYCLE_COUNT_KEY = ("ratioViserPreCommitBWDrivenCycleCount")
    READ_VALIDATION_BW_CYCLE_COUNT_KEY = ("dep_ViserReadValidationBWDrivenCycleCount")
    RATIO_READ_VALIDATION_BW_CYCLE_COUNT_KEY = ("ratioViserReadValidationBWDrivenCycleCount")
    POST_COMMIT_BW_CYCLE_COUNT_KEY = ("dep_ViserPostCommitBWDrivenCycleCount")
    RATIO_POST_COMMIT_BW_CYCLE_COUNT_KEY = ("ratioViserPostCommitBWDrivenCycleCount")

    VALIDATION_ATTEMPTS_KEY = "g_ValidationAttempts"
    PRECISE_CONFLICTS_KEY = "g_PreciseConflicts"

    NUM_SCAVENGES_KEY = "g_NumScavenges"

    SCAVENGE_TIME_KEY = "ScavengeRunningTimeMins"

    UPGRADE_NETWORK_MSGS_KEY = "g_ViserUpgradeMessages"
    RATIO_UPGRADE_NETWORK_MSGS_KEY = "ratioViserUpgradeMessages"
    # UPGRADE_NETWORKMSG_BYTES_KEY = "g_ViserUpgradeMessageSizeBytes"
    # RATIO_UPGRADE_NETWORKMSG_BYTES_KEY = ("ratioViserUpgradeMessageSizeBytes")
    # UPGRADE_NETWORKMSG_SIZE_4BYTES_FLITS_KEY = (
    #     "g_ViserUpgradeMessageSize4BytesFlits")
    # RATIO_UPGRADE_NETWORKMSG_SIZE_4BYTES_FLITS_KEY = (
    #     "ratioViserUpgradeMessageSize4BytesFlits")
    # UPGRADE_NETWORKMSG_SIZE_8BYTES_FLITS_KEY = (
    #     "g_ViserUpgradeMessageSize8BytesFlits")
    # RATIO_UPGRADE_NETWORKMSG_SIZE_8BYTES_FLITS_KEY = (
    #     "ratioViserUpgradeMessageSize8BytesFlits")
    UPGRADE_NETWORKMSG_SIZE_16BYTES_FLITS_KEY = ("g_ViserUpgradeMessageSize16BytesFlits")
    RATIO_UPGRADE_NETWORKMSG_SIZE_16BYTES_FLITS_KEY = ("ratioViserUpgradeMessageSize16BytesFlits")
    # UPGRADE_NETWORKMSG_SIZE_32BYTES_FLITS_KEY = (
    #     "g_ViserUpgradeMessageSize32BytesFlits")
    # RATIO_UPGRADE_NETWORKMSG_SIZE_32BYTES_FLITS_KEY = (
    #     "ratioViserUpgradeMessageSize32BytesFlits")

    RV_DEFERRED_LINE_MSGS_KEY = ("g_ViserRVDeferredLineMessages")
    RATIO_RV_DEFERRED_LINE_MSGS_KEY = ("ratioViserRVDeferredLineMessages")
    # RV_DEFERRED_LINE_MSGS_BYTES_KEY = ("g_ViserRVDeferredLineMessageSizeBytes")
    # RATIO_RV_DEFERRED_LINE_MSGS_BYTES_KEY = (
    #     "ratioViserRVDeferredLineMessageSizeBytes")
    # RV_DEFERRED_LINE_MSGS_4BYTES_FLITS_KEY = (
    #     "g_ViserRVDeferredLineMessageSize4ByteFlits")
    # RATIO_RV_DEFERRED_LINE_MSGS_4BYTES_FLITS_KEY = (
    #     "ratioViserRVDeferredLineMessageSize4ByteFlits")
    # RV_DEFERRED_LINE_MSGS_8BYTES_FLITS_KEY = (
    #     "g_ViserRVDeferredLineMessageSize8ByteFlits")
    # RATIO_RV_DEFERRED_LINE_MSGS_8BYTES_FLITS_KEY = (
    #     "ratioViserRVDeferredLineMessageSize8ByteFlits")
    RV_DEFERRED_LINE_MSGS_16BYTES_FLITS_KEY = ("g_ViserRVDeferredLineMessageSize16ByteFlits")
    RATIO_RV_DEFERRED_LINE_MSGS_16BYTES_FLITS_KEY = (
        "ratioViserRVDeferredLineMessageSize16ByteFlits")
    # RV_DEFERRED_LINE_MSGS_32BYTES_FLITS_KEY = (
    #     "g_ViserRVDeferredLineMessageSize32ByteFlits")
    # RATIO_RV_DEFERRED_LINE_MSGS_32BYTES_FLITS_KEY = (
    #     "ratioViserRVDeferredLineMessageSize32ByteFlits")

    REG_EXEC_ONCHIP_NETWORK_MSGS_KEY = ("g_ViserRegExecOnChipNetworkMessages")
    RATIO_REG_EXEC_ONCHIP_NETWORK_MSGS_KEY = ("ratioViserRegExecOnChipNetworkMessages")
    # REG_EXEC_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
    #     "g_ViserRegExecOnChipNetworkMessageSizeBytes")
    # RATIO_REG_EXEC_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
    #     "ratioViserRegExecOnChipNetworkMessageSizeBytes")
    # REG_EXEC_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
    #     "g_ViserRegExecOnChipNetworkMessageSize4BytesFlits")
    # RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
    #     "ratioViserRegExecOnChipNetworkMessageSize4BytesFlits")
    # REG_EXEC_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
    #     "g_ViserRegExecOnChipNetworkMessageSize8BytesFlits")
    # RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
    #     "ratioViserRegExecOnChipNetworkMessageSize8BytesFlits")
    REG_EXEC_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "g_ViserRegExecOnChipNetworkMessageSize16BytesFlits")
    RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "ratioViserRegExecOnChipNetworkMessageSize16BytesFlits")
    # REG_EXEC_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
    #     "g_ViserRegExecOnChipNetworkMessageSize32BytesFlits")
    # RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
    #     "ratioViserRegExecOnChipNetworkMessageSize32BytesFlits")

    PRE_COMMIT_ONCHIP_NETWORK_MSGS_KEY = ("g_ViserPreCommitOnChipNetworkMessages")
    RATIO_PRE_COMMIT_ONCHIP_NETWORK_MSGS_KEY = ("ratioViserPreCommitOnChipNetworkMessages")
    # PRE_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
    #     "g_ViserPreCommitOnChipNetworkMessageSizeBytes")
    # RATIO_PRE_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
    #     "ratioViserPreCommitOnChipNetworkMessageSizeBytes")
    # PRE_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
    #     "g_ViserPreCommitOnChipNetworkMessageSize4BytesFlits")
    # RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
    #     "ratioViserPreCommitOnChipNetworkMessageSize4BytesFlits")
    # PRE_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
    #     "g_ViserPreCommitOnChipNetworkMessageSize8BytesFlits")
    # RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
    #     "ratioViserPreCommitOnChipNetworkMessageSize8BytesFlits")
    PRE_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "g_ViserPreCommitOnChipNetworkMessageSize16BytesFlits")
    RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "ratioViserPreCommitOnChipNetworkMessageSize16BytesFlits")
    # PRE_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
    #     "g_ViserPreCommitOnChipNetworkMessageSize32BytesFlits")
    # RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
    #     "ratioViserPreCommitOnChipNetworkMessageSize32BytesFlits")

    READ_VALIDATION_ONCHIP_NETWORK_MSGS_KEY = ("g_ViserReadValidationOnChipNetworkMessages")
    RATIO_READ_VALIDATION_ONCHIP_NETWORK_MSGS_KEY = (
        "ratioViserReadValidationOnChipNetworkMessages")
    # READ_VALIDATION_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
    #     "g_ViserReadValidationOnChipNetworkMessageSizeBytes")
    # RATIO_READ_VALIDATION_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
    #     "ratioViserReadValidationOnChipNetworkMessageSizeBytes")
    # READ_VALIDATION_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
    #     "g_ViserReadValidationOnChipNetworkMessageSize4BytesFlits")
    # RATIO_READ_VALIDATION_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
    #     "ratioViserReadValidationOnChipNetworkMessageSize4BytesFlits")
    # READ_VALIDATION_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
    #     "g_ViserReadValidationOnChipNetworkMessageSize8BytesFlits")
    # RATIO_READ_VALIDATION_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
    #     "ratioViserReadValidationOnChipNetworkMessageSize8BytesFlits")
    READ_VALIDATION_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "g_ViserReadValidationOnChipNetworkMessageSize16BytesFlits")
    RATIO_READ_VALIDATION_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "ratioViserReadValidationOnChipNetworkMessageSize16BytesFlits")
    # READ_VALIDATION_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
    #     "g_ViserReadValidationOnChipNetworkMessageSize32BytesFlits")
    # RATIO_READ_VALIDATION_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
    #     "ratioViserReadValidationOnChipNetworkMessageSize32BytesFlits")

    POST_COMMIT_ONCHIP_NETWORK_MSGS_KEY = ("g_ViserPostCommitOnChipNetworkMessages")
    RATIO_POST_COMMIT_ONCHIP_NETWORK_MSGS_KEY = ("ratioViserPostCommitOnChipNetworkMessages")
    # POST_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
    #     "g_ViserPostCommitOnChipNetworkMessageSizeBytes")
    # RATIO_POST_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
    #     "ratioViserPostCommitOnChipNetworkMessageSizeBytes")
    # POST_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
    #     "g_ViserPostCommitOnChipNetworkMessageSize4BytesFlits")
    # RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
    #     "ratioViserPostCommitOnChipNetworkMessageSize4BytesFlits")
    # POST_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
    #     "g_ViserPostCommitOnChipNetworkMessageSize8BytesFlits")
    # RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
    #     "ratioViserPostCommitOnChipNetworkMessageSize8BytesFlits")
    POST_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "g_ViserPostCommitOnChipNetworkMessageSize16BytesFlits")
    RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "ratioViserPostCommitOnChipNetworkMessageSize16BytesFlits")
    # POST_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
    #     "g_ViserPostCommitOnChipNetworkMessageSize32BytesFlits")
    # RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
    #     "ratioViserPostCommitOnChipNetworkMessageSize32BytesFlits")

    TCC_REG_WB_OVERFLOWS_8K_KEY = ("g_TCCRegionsWBOverflows8K")
    RATIO_TCC_REG_WB_OVERFLOWS_8K_KEY = ("ratioTCCRegionsWBOverflows8K")
    TCC_REG_WB_OVERFLOWS_16K_KEY = ("g_TCCRegionsWBOverflows16K")
    RATIO_TCC_REG_WB_OVERFLOWS_16K_KEY = ("ratioTCCRegionsWBOverflows16K")
    TCC_REG_WB_OVERFLOWS_32K_KEY = ("g_TCCRegionsWBOverflows32K")
    RATIO_TCC_REG_WB_OVERFLOWS_32K_KEY = ("ratioTCCRegionsWBOverflows32K")
    TCC_REG_WB_OVERFLOWS_64K_KEY = ("g_TCCRegionsWBOverflows64K")
    RATIO_TCC_REG_WB_OVERFLOWS_64K_KEY = ("ratioTCCRegionsWBOverflows64K")

    TCC_REG_CACHE_OVERFLOWS_KEY = ("g_TCCRegionsCacheOverflows")
    RATIO_TCC_REG_CACHE_OVERFLOWS_KEY = ("ratioTCCRegionsCacheOverflows")

    TCC_REGIONS_OVERFLOWS_8K_KEY = ("g_TCCRegionsOverflows8K")
    RATIO_TCC_REGIONS_OVERFLOWS_8K_KEY = ("ratioTCCRegionsOverflows8K")
    TCC_REGIONS_OVERFLOWS_16K_KEY = ("g_TCCRegionsOverflows16K")
    RATIO_TCC_REGIONS_OVERFLOWS_16K_KEY = ("ratioTCCRegionsOverflows16K")
    TCC_REGIONS_OVERFLOWS_32K_KEY = ("g_TCCRegionsOverflows32K")
    RATIO_TCC_REGIONS_OVERFLOWS_32K_KEY = ("ratioTCCRegionsOverflows32K")
    TCC_REGIONS_OVERFLOWS_64K_KEY = ("g_TCCRegionsOverflows64K")
    RATIO_TCC_REGIONS_OVERFLOWS_64K_KEY = ("ratioTCCRegionsOverflows64K")

    TCC_REGIONS_FIRST_WB_OVERFLOWS_8K_KEY = ("g_TCCRegionsFirstWBOverflows8K")
    RATIO_TCC_REGIONS_FIRST_WB_OVERFLOWS_8K_KEY = ("ratioTCCRegionsFirstWBOverflows8K")
    TCC_REGIONS_FIRST_WB_OVERFLOWS_16K_KEY = ("g_TCCRegionsFirstWBOverflows16K")
    RATIO_TCC_REGIONS_FIRST_WB_OVERFLOWS_16K_KEY = ("ratioTCCRegionsFirstWBOverflows16K")
    TCC_REGIONS_FIRST_WB_OVERFLOWS_32K_KEY = ("g_TCCRegionsFirstWBOverflows32K")
    RATIO_TCC_REGIONS_FIRST_WB_OVERFLOWS_32K_KEY = ("ratioTCCRegionsFirstWBOverflows32K")
    TCC_REGIONS_FIRST_WB_OVERFLOWS_64K_KEY = ("g_TCCRegionsFirstWBOverflows64K")
    RATIO_TCC_REGIONS_FIRST_WB_OVERFLOWS_64K_KEY = ("ratioTCCRegionsFirstWBOverflows64K")

    TCC_REGIONS_FIRST_CACHE_OVERFLOWS_8K_KEY = ("g_TCCRegionsFirstCacheOverflows8K")
    RATIO_TCC_REGIONS_FIRST_CACHE_OVERFLOWS_8K_KEY = ("ratioTCCRegionsFirstCacheOverflows8K")
    TCC_REGIONS_FIRST_CACHE_OVERFLOWS_16K_KEY = ("g_TCCRegionsFirstCacheOverflows16K")
    RATIO_TCC_REGIONS_FIRST_CACHE_OVERFLOWS_16K_KEY = ("ratioTCCRegionsFirstCacheOverflows16K")
    TCC_REGIONS_FIRST_CACHE_OVERFLOWS_32K_KEY = ("g_TCCRegionsFirstCacheOverflows32K")
    RATIO_TCC_REGIONS_FIRST_CACHE_OVERFLOWS_32K_KEY = ("ratioTCCRegionsFirstCacheOverflows32K")
    TCC_REGIONS_FIRST_CACHE_OVERFLOWS_64K_KEY = ("g_TCCRegionsFirstCacheOverflows64K")
    RATIO_TCC_REGIONS_FIRST_CACHE_OVERFLOWS_64K_KEY = ("ratioTCCRegionsFirstCacheOverflows64K")

    TCC_SERIALIZED_MEM_ACCESSES_8K_KEY = ("g_TCCNumSerializedMemoryAccesses8K")
    RATIO_TCC_SERIALIZED_MEM_ACCESSES_8K_KEY = ("ratioTCCNumSerializedMemoryAccesses8K")
    TCC_SERIALIZED_MEM_ACCESSES_16K_KEY = ("g_TCCNumSerializedMemoryAccesses16K")
    RATIO_TCC_SERIALIZED_MEM_ACCESSES_16K_KEY = ("ratioTCCNumSerializedMemoryAccesses16K")
    TCC_SERIALIZED_MEM_ACCESSES_32K_KEY = ("g_TCCNumSerializedMemoryAccesses32K")
    RATIO_TCC_SERIALIZED_MEM_ACCESSES_32K_KEY = ("ratioTCCNumSerializedMemoryAccesses32K")
    TCC_SERIALIZED_MEM_ACCESSES_64K_KEY = ("g_TCCNumSerializedMemoryAccesses64K")
    RATIO_TCC_SERIALIZED_MEM_ACCESSES_64K_KEY = ("ratioTCCNumSerializedMemoryAccesses64K")

    TCC_CYCLES_8K_KEY = "max_TCCCycleCount8K"
    RATIO_TCC_CYCLES_8K_KEY = "ratioTCCCycleCount8K"
    TCC_CYCLES_16K_KEY = "max_TCCCycleCount16K"
    RATIO_TCC_CYCLES_16K_KEY = "ratioTCCCycleCount16K"
    TCC_CYCLES_32K_KEY = "max_TCCCycleCount32K"
    RATIO_TCC_CYCLES_32K_KEY = "ratioTCCCycleCount32K"
    TCC_CYCLES_64K_KEY = "max_TCCCycleCount64K"
    RATIO_TCC_CYCLES_64K_KEY = "ratioTCCCycleCount64K"

    TCC_BDCAST_MSG_BYTES_KEY = "g_TCCBroadCastMessagesBytes"
    RATIO_TCC_BDCAST_MSG_BYTES_KEY = "ratioTCCBroadCastMessagesBytes"
    # TCC_BDCAST_MSG_4BYTES_FLITS_KEY = ("g_TCCBroadCastMessages4BytesFlits")
    # RATIO_TCC_BDCAST_MSG_4BYTES_FLITS_KEY = (
    #     "ratioTCCBroadCastMessages4BytesFlits")
    # TCC_BDCAST_MSG_8BYTES_FLITS_KEY = ("g_TCCBroadCastMessages8BytesFlits")
    # RATIO_TCC_BDCAST_MSG_8BYTES_FLITS_KEY = (
    #     "ratioTCCBroadCastMessages8BytesFlits")
    TCC_BDCAST_MSG_16BYTES_FLITS_KEY = ("g_TCCBroadCastMessages16BytesFlits")
    RATIO_TCC_BDCAST_MSG_16BYTES_FLITS_KEY = ("ratioTCCBroadCastMessages16BytesFlits")
    # TCC_BDCAST_MSG_32BYTES_FLITS_KEY = ("g_TCCBroadCastMessages32BytesFlits")
    # RATIO_TCC_BDCAST_MSG_32BYTES_FLITS_KEY = (
    #     "ratioTCCBroadCastMessages32BytesFlits")

    BLOOM_FILTER_READ_ENERGY = "g_BloomFilterReadEnergy"
    BLOOM_FILTER_WRITE_ENERGY = "g_BloomFilterWriteEnergy"
    BLOOM_FILTER_TOTAL_ENERGY = "g_BloomFilterTotalEnergy"

    # # This is the dynamic estimate from the simulator. Modeling through McPAT which is the default
    # # seems to be more accurate.
    # AIM_DYNAMIC_READ_ENERGY = "g_AIMReadEnergy"
    # AIM_DYNAMIC_WRITE_ENERGY = "g_AIMWriteEnergy"
    # AIM_DYNAMIC_TOTAL_ENERGY = "g_AIMTotalEnergy"


class RCCSISimKeys(Constants):
    WRITE_AFTER_READ_UPGRADES_KEY = "g_RCCSIWARUpgrades"

    REG_EXEC_EXEC_CYCLE_COUNT_KEY = ("dep_RCCSIRegExecExecDrivenCycleCount")
    RATIO_REG_EXEC_EXEC_CYCLE_COUNT_KEY = ("ratioRCCSIRegExecExecDrivenCycleCount")
    PRE_COMMIT_EXEC_CYCLE_COUNT_KEY = ("dep_RCCSIPreCommitExecDrivenCycleCount")
    RATIO_PRE_COMMIT_EXEC_CYCLE_COUNT_KEY = ("ratioRCCSIPreCommitExecDrivenCycleCount")
    READ_VALIDATION_EXEC_CYCLE_COUNT_KEY = ("dep_RCCSIReadValidationExecDrivenCycleCount")
    RATIO_READ_VALIDATION_EXEC_CYCLE_COUNT_KEY = ("ratioRCCSIReadValidationExecDrivenCycleCount")
    STALL_EXEC_CYCLE_COUNT_KEY = ("dep_RCCSIStallExecDrivenCycleCount")
    RATIO_STALL_EXEC_CYCLE_COUNT_KEY = ("ratioRCCSIStallExecDrivenCycleCount")
    COMMIT_EXEC_CYCLE_COUNT_KEY = ("dep_RCCSICommitExecDrivenCycleCount")
    RATIO_COMMIT_EXEC_CYCLE_COUNT_KEY = ("ratioRCCSICommitExecDrivenCycleCount")
    POST_COMMIT_EXEC_CYCLE_COUNT_KEY = ("dep_RCCSIPostCommitExecDrivenCycleCount")
    RATIO_POST_COMMIT_EXEC_CYCLE_COUNT_KEY = ("ratioRCCSIPostCommitExecDrivenCycleCount")

    REG_EXEC_BW_CYCLE_COUNT_KEY = "dep_RCCSIRegExecBWDrivenCycleCount"
    RATIO_REG_EXEC_BW_CYCLE_COUNT_KEY = ("ratioRCCSIRegExecBWDrivenCycleCount")
    PRE_COMMIT_BW_CYCLE_COUNT_KEY = ("dep_RCCSIPreCommitBWDrivenCycleCount")
    RATIO_PRE_COMMIT_BW_CYCLE_COUNT_KEY = ("ratioRCCSIPreCommitBWDrivenCycleCount")
    READ_VALIDATION_BW_CYCLE_COUNT_KEY = ("dep_RCCSIReadValidationBWDrivenCycleCount")
    RATIO_READ_VALIDATION_BW_CYCLE_COUNT_KEY = ("ratioRCCSIReadValidationBWDrivenCycleCount")
    STALL_BW_CYCLE_COUNT_KEY = ("dep_RCCSIStallBWDrivenCycleCount")
    RATIO_STALL_BW_CYCLE_COUNT_KEY = ("ratioRCCSIStallBWDrivenCycleCount")
    COMMIT_BW_CYCLE_COUNT_KEY = ("dep_RCCSICommitBWDrivenCycleCount")
    RATIO_COMMIT_BW_CYCLE_COUNT_KEY = ("ratioRCCSICommitBWDrivenCycleCount")
    POST_COMMIT_BW_CYCLE_COUNT_KEY = ("dep_RCCSIPostCommitBWDrivenCycleCount")
    RATIO_POST_COMMIT_BW_CYCLE_COUNT_KEY = ("ratioRCCSIPostCommitBWDrivenCycleCount")

    PRECISE_CONFLICTS_KEY = "g_PreciseConflicts"
    PRECISE_WRWR_CONFLICTS_KEY = "g_PreciseWrWrConflicts"
    PRECISE_WRRD_CONFLICTS_KEY = "g_PreciseWrRdConflicts"
    PRECISE_RDVAL_CONFLICTS_KEY = "g_PreciseReadValidationConflicts"

    REG_EXEC_ONCHIP_NETWORK_MSGS_KEY = ("g_RCCSIRegExecOnChipNetworkMessages")
    RATIO_REG_EXEC_ONCHIP_NETWORK_MSGS_KEY = ("ratioRCCSIRegExecOnChipNetworkMessages")
    REG_EXEC_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = ("g_RCCSIRegExecOnChipNetworkMessageSizeBytes")
    RATIO_REG_EXEC_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
        "ratioRCCSIRegExecOnChipNetworkMessageSizeBytes")
    REG_EXEC_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "g_RCCSIRegExecOnChipNetworkMessageSize4BytesFlits")
    RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "ratioRCCSIRegExecOnChipNetworkMessageSize4BytesFlits")
    REG_EXEC_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "g_RCCSIRegExecOnChipNetworkMessageSize8BytesFlits")
    RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "ratioRCCSIRegExecOnChipNetworkMessageSize8BytesFlits")
    REG_EXEC_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "g_RCCSIRegExecOnChipNetworkMessageSize16BytesFlits")
    RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "ratioRCCSIRegExecOnChipNetworkMessageSize16BytesFlits")
    REG_EXEC_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "g_RCCSIRegExecOnChipNetworkMessageSize32BytesFlits")
    RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "ratioRCCSIRegExecOnChipNetworkMessageSize32BytesFlits")

    PRE_COMMIT_ONCHIP_NETWORK_MSGS_KEY = "g_RCCSIPreCommitOnChipNetworkMessages"
    RATIO_PRE_COMMIT_ONCHIP_NETWORK_MSGS_KEY = "ratioRCCSIPreCommitOnChipNetworkMessages"
    PRE_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = ("g_RCCSIPreCommitOnChipNetworkMessageSizeBytes")
    RATIO_PRE_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
        "ratioRCCSIPreCommitOnChipNetworkMessageSizeBytes")
    PRE_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "g_RCCSIPreCommitOnChipNetworkMessageSize4BytesFlits")
    RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "ratioRCCSIPreCommitOnChipNetworkMessageSize4BytesFlits")
    PRE_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "g_RCCSIPreCommitOnChipNetworkMessageSize8BytesFlits")
    RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "ratioRCCSIPreCommitOnChipNetworkMessageSize8BytesFlits")
    PRE_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "g_RCCSIPreCommitOnChipNetworkMessageSize16BytesFlits")
    RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "ratioRCCSIPreCommitOnChipNetworkMessageSize16BytesFlits")
    PRE_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "g_RCCSIPreCommitOnChipNetworkMessageSize32BytesFlits")
    RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "ratioRCCSIPreCommitOnChipNetworkMessageSize32BytesFlits")

    RDVAL_ONCHIP_NETWORK_MSGS_KEY = "g_RCCSIReadValidationOnChipNetworkMessages"
    RATIO_RDVAL_ONCHIP_NETWORK_MSGS_KEY = "ratioRCCSIReadValidationOnChipNetworkMessages"
    RDVAL_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = ("g_RCCSIReadValidationOnChipNetworkMessageSizeBytes")
    RATIO_RDVAL_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
        "ratioRCCSIReadValidationOnChipNetworkMessageSizeBytes")
    RDVAL_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "g_RCCSIReadValidationOnChipNetworkMessageSize4BytesFlits")
    RATIO_RDVAL_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "ratioRCCSIReadValidationOnChipNetworkMessageSize4BytesFlits")
    RDVAL_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "g_RCCSIReadValidationOnChipNetworkMessageSize8BytesFlits")
    RATIO_RDVAL_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "ratioRCCSIReadValidationOnChipNetworkMessageSize8BytesFlits")
    RDVAL_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "g_RCCSIReadValidationOnChipNetworkMessageSize16BytesFlits")
    RATIO_RDVAL_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "ratioRCCSIReadValidationOnChipNetworkMessageSize16BytesFlits")
    RDVAL_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "g_RCCSIReadValidationOnChipNetworkMessageSize32BytesFlits")
    RATIO_RDVAL_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "ratioRCCSIReadValidationOnChipNetworkMessageSize32BytesFlits")

    COMMIT_ONCHIP_NETWORK_MSGS_KEY = "g_RCCSICommitOnChipNetworkMessages"
    RATIO_COMMIT_ONCHIP_NETWORK_MSGS_KEY = "ratioRCCSICommitOnChipNetworkMessages"
    COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = "g_RCCSICommitOnChipNetworkMessageSizeBytes"
    RATIO_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
        "ratioRCCSICommitOnChipNetworkMessageSizeBytes")
    COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "g_RCCSICommitOnChipNetworkMessageSize4BytesFlits")
    RATIO_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "ratioRCCSICommitOnChipNetworkMessageSize4BytesFlits")
    COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "g_RCCSICommitOnChipNetworkMessageSize8BytesFlits")
    RATIO_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "ratioRCCSICommitOnChipNetworkMessageSize8BytesFlits")
    COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "g_RCCSICommitOnChipNetworkMessageSize16BytesFlits")
    RATIO_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "ratioRCCSICommitOnChipNetworkMessageSize16BytesFlits")
    COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "g_RCCSICommitOnChipNetworkMessageSize32BytesFlits")
    RATIO_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "ratioRCCSICommitOnChipNetworkMessageSize32BytesFlits")

    POST_COMMIT_ONCHIP_NETWORK_MSGS_KEY = "g_RCCSIPostCommitOnChipNetworkMessages"
    RATIO_POST_COMMIT_ONCHIP_NETWORK_MSGS_KEY = "ratioRCCSIPostCommitOnChipNetworkMessages"
    POST_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
        "g_RCCSIPostCommitOnChipNetworkMessageSizeBytes")
    RATIO_POST_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY = (
        "ratioRCCSIPostCommitOnChipNetworkMessageSizeBytes")
    POST_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "g_RCCSIPostCommitOnChipNetworkMessageSize4BytesFlits")
    RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY = (
        "ratioRCCSIPostCommitOnChipNetworkMessageSize4BytesFlits")
    POST_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "g_RCCSIPostCommitOnChipNetworkMessageSize8BytesFlits")
    RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY = (
        "ratioRCCSIPostCommitOnChipNetworkMessageSize8BytesFlits")
    POST_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "g_RCCSIPostCommitOnChipNetworkMessageSize16BytesFlits")
    RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY = (
        "ratioRCCSIPostCommitOnChipNetworkMessageSize16BytesFlits")
    POST_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "g_RCCSIPostCommitOnChipNetworkMessageSize32BytesFlits")
    RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY = (
        "ratioRCCSIPostCommitOnChipNetworkMessageSize32BytesFlits")


class EnergyStatsKeys(Constants):
    AREA = "Area"
    STATIC_POWER = "StaticPower"
    DYNAMIC_POWER = "DynamicPower"
    STATIC_ENERGY = "StaticEnergy"
    DYNAMIC_ENERGY = "DynamicEnergy"
    BLOOM_FILTER_ENERGY = "BloomFilterEnergy"
    AIM_DYNAMIC_POWER = "AIMDynamicPower"
    AIM_DYNAMIC_ENERGY = "AIMDynamicEnergy"
    AIM_STATIC_POWER = "AIMStaticPower"
    AIM_STATIC_ENERGY = "AIMStaticEnergy"
    TOTAL_ENERGY = "TotalEnergy"


class PerCoreStatsKeys(Constants):
    TOTAL_CYCLES = "pc_BandwidthDrivenCycleCount"

    TOTAL_READS_KEY = "pc_TotalDataReads"
    TOTAL_WRITES_KEY = "pc_TotalDataWrites"

    L1_READ_HITS_KEY = "pc_Data_L1ReadHits"
    L1_READ_MISSES_KEY = "pc_Data_L1ReadMisses"
    L1_WRITE_HITS_KEY = "pc_Data_L1WriteHits"
    L1_WRITE_MISSES_KEY = "pc_Data_L1WriteMisses"

    L2_READ_HITS_KEY = "pc_Data_L2ReadHits"
    L2_READ_MISSES_KEY = "pc_Data_L2ReadMisses"
    L2_WRITE_HITS_KEY = "pc_Data_L2WriteHits"
    L2_WRITE_MISSES_KEY = "pc_Data_L2WriteMisses"


class StackedKeys(Constants):

    # This is a mapping of the following form
    # {KEY: [[MESI_keys], [Viser_keys]]
    MESI_OFFSET = 0
    VISER_OFFSET = 1
    RCCSI_OFFSET = 2
    PAUSE_OFFSET = 3

    LEN_VALUES = 4  # MESI, Viser, RCC-SI and PAUSE/RESTART

    # The iteration order is deterministic
    di_stackedKeys = collections.OrderedDict()
    di_energyStackedKeys = collections.OrderedDict()

    # Exec cycle overheads
    MESI_EXEC_CYCLE_PROP_KEYS = []
    MESI_EXEC_CYCLE_PROP_KEYS.append(MESISimKeys.MEM_EXEC_CYCLE_COUNT_KEY)
    MESI_EXEC_CYCLE_PROP_KEYS.append(MESISimKeys.COHERENCE_EXEC_CYCLE_COUNT_KEY)
    '''
    VISER_EXEC_CYCLE_PROP_KEYS = []
    VISER_EXEC_CYCLE_PROP_KEYS.append(
        ViserSimKeys.REG_EXEC_EXEC_CYCLE_COUNT_KEY)
    VISER_EXEC_CYCLE_PROP_KEYS.append(
        ViserSimKeys.PRE_COMMIT_EXEC_CYCLE_COUNT_KEY)
    VISER_EXEC_CYCLE_PROP_KEYS.append(
        ViserSimKeys.READ_VALIDATION_EXEC_CYCLE_COUNT_KEY)
    VISER_EXEC_CYCLE_PROP_KEYS.append(
        ViserSimKeys.POST_COMMIT_EXEC_CYCLE_COUNT_KEY)

    RCCSI_EXEC_CYCLE_PROP_KEYS = []
    RCCSI_EXEC_CYCLE_PROP_KEYS.append(
        RCCSISimKeys.REG_EXEC_EXEC_CYCLE_COUNT_KEY)
    RCCSI_EXEC_CYCLE_PROP_KEYS.append(
        RCCSISimKeys.PRE_COMMIT_EXEC_CYCLE_COUNT_KEY)
    RCCSI_EXEC_CYCLE_PROP_KEYS.append(
        RCCSISimKeys.READ_VALIDATION_EXEC_CYCLE_COUNT_KEY)
    RCCSI_EXEC_CYCLE_PROP_KEYS.append(RCCSISimKeys.STALL_EXEC_CYCLE_COUNT_KEY)
    RCCSI_EXEC_CYCLE_PROP_KEYS.append(RCCSISimKeys.COMMIT_EXEC_CYCLE_COUNT_KEY)
    RCCSI_EXEC_CYCLE_PROP_KEYS.append(
        RCCSISimKeys.POST_COMMIT_EXEC_CYCLE_COUNT_KEY)

    # RZ: not supposed to be used
    PAUSE_EXEC_CYCLE_PROP_KEYS = []
    PAUSE_EXEC_CYCLE_PROP_KEYS.append(
        ViserSimKeys.REG_EXEC_EXEC_CYCLE_COUNT_KEY)
    PAUSE_EXEC_CYCLE_PROP_KEYS.append(
        ViserSimKeys.PRE_COMMIT_EXEC_CYCLE_COUNT_KEY)
    PAUSE_EXEC_CYCLE_PROP_KEYS.append(
        ViserSimKeys.READ_VALIDATION_EXEC_CYCLE_COUNT_KEY)
    PAUSE_EXEC_CYCLE_PROP_KEYS.append(
        ViserSimKeys.POST_COMMIT_EXEC_CYCLE_COUNT_KEY)

    di_stackedKeys[
        SimKeys.EXECUTION_CYCLE_COUNT_KEY] = [
        MESI_EXEC_CYCLE_PROP_KEYS,
        VISER_EXEC_CYCLE_PROP_KEYS,
        RCCSI_EXEC_CYCLE_PROP_KEYS,
        PAUSE_EXEC_CYCLE_PROP_KEYS]
    '''
    # Bandwidth cycle overheads
    VISER_BW_CYCLE_PROPS_KEY = []
    VISER_BW_CYCLE_PROPS_KEY.append(ViserSimKeys.REG_EXEC_BW_CYCLE_COUNT_KEY)
    VISER_BW_CYCLE_PROPS_KEY.append(ViserSimKeys.PRE_COMMIT_BW_CYCLE_COUNT_KEY)
    VISER_BW_CYCLE_PROPS_KEY.append(ViserSimKeys.READ_VALIDATION_BW_CYCLE_COUNT_KEY)
    VISER_BW_CYCLE_PROPS_KEY.append(ViserSimKeys.POST_COMMIT_BW_CYCLE_COUNT_KEY)

    RCCSI_BW_CYCLE_PROP_KEYS = []
    RCCSI_BW_CYCLE_PROP_KEYS.append(RCCSISimKeys.REG_EXEC_BW_CYCLE_COUNT_KEY)
    RCCSI_BW_CYCLE_PROP_KEYS.append(RCCSISimKeys.PRE_COMMIT_BW_CYCLE_COUNT_KEY)
    RCCSI_BW_CYCLE_PROP_KEYS.append(RCCSISimKeys.READ_VALIDATION_BW_CYCLE_COUNT_KEY)
    RCCSI_BW_CYCLE_PROP_KEYS.append(RCCSISimKeys.STALL_BW_CYCLE_COUNT_KEY)
    RCCSI_BW_CYCLE_PROP_KEYS.append(RCCSISimKeys.COMMIT_BW_CYCLE_COUNT_KEY)
    RCCSI_BW_CYCLE_PROP_KEYS.append(RCCSISimKeys.POST_COMMIT_BW_CYCLE_COUNT_KEY)

    PAUSE_BW_CYCLE_PROPS_KEY = []
    PAUSE_BW_CYCLE_PROPS_KEY.append(PauseSimKeys.REG_EXEC_BW_CYCLE_COUNT_KEY)
    PAUSE_BW_CYCLE_PROPS_KEY.append(PauseSimKeys.PRE_COMMIT_BW_CYCLE_COUNT_KEY)
    PAUSE_BW_CYCLE_PROPS_KEY.append(PauseSimKeys.READ_VALIDATION_BW_CYCLE_COUNT_KEY)
    PAUSE_BW_CYCLE_PROPS_KEY.append(PauseSimKeys.POST_COMMIT_BW_CYCLE_COUNT_KEY)
    PAUSE_BW_CYCLE_PROPS_KEY.append(PauseSimKeys.PAUSE_BW_CYCLE_COUNT_KEY)
    PAUSE_BW_CYCLE_PROPS_KEY.append(PauseSimKeys.RESTART_BW_CYCLE_COUNT_KEY)

    di_stackedKeys[SimKeys.BANDWIDTH_CYCLE_COUNT_KEY] = [
        MESI_EXEC_CYCLE_PROP_KEYS, VISER_BW_CYCLE_PROPS_KEY, RCCSI_BW_CYCLE_PROP_KEYS,
        PAUSE_BW_CYCLE_PROPS_KEY
    ]

    # Network traffic overheads
    '''
    # 4 bytes
    MESI_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY = []
    MESI_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY.append(
        MESISimKeys.MEM_ONCHIP_NETWORKMSG_SIZE_4BYTES_FLITS_KEY)
    MESI_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY.append(
        MESISimKeys.COHERENCE_ONCHIP_NETWORKMSG_SIZE_4BYTES_FLITS_KEY)

    VISER_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY = []
    VISER_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY.append(
        ViserSimKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
    VISER_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY.append(
        ViserSimKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
    VISER_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY.append(
        ViserSimKeys.READ_VALIDATION_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
    VISER_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY.append(
        ViserSimKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)

    RCCSI_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY = []
    RCCSI_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY.append(
        RCCSISimKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
    RCCSI_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY.append(
        RCCSISimKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
    RCCSI_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY.append(
        RCCSISimKeys.RDVAL_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
    RCCSI_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY.append(
        RCCSISimKeys.COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
    RCCSI_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY.append(
        RCCSISimKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)

    PAUSE_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY = []
    PAUSE_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY.append(
        PauseSimKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
    PAUSE_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY.append(
        PauseSimKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
    PAUSE_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY.append(
        PauseSimKeys.READ_VALIDATION_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
    PAUSE_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY.append(
        PauseSimKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
    PAUSE_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY.append(
        PauseSimKeys.RESTART_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)

    di_stackedKeys[SimKeys.ONCHIP_NETWORKMSG_SIZE_4BYTES_FLITS_KEY] = [
        MESI_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY, VISER_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY,
        RCCSI_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY, PAUSE_TRAFFIC_ONCHIP_4BYTES_FLITS_KEY
    ]

    # 8 bytes
    MESI_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY = []
    MESI_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY.append(
        MESISimKeys.MEM_ONCHIP_NETWORKMSG_SIZE_8BYTES_FLITS_KEY)
    MESI_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY.append(
        MESISimKeys.COHERENCE_ONCHIP_NETWORKMSG_SIZE_8BYTES_FLITS_KEY)

    VISER_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY = []
    VISER_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY.append(
        ViserSimKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
    VISER_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY.append(
        ViserSimKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
    VISER_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY.append(
        ViserSimKeys.READ_VALIDATION_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
    VISER_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY.append(
        ViserSimKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)

    RCCSI_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY = []
    RCCSI_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY.append(
        RCCSISimKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
    RCCSI_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY.append(
        RCCSISimKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
    RCCSI_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY.append(
        RCCSISimKeys.RDVAL_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
    RCCSI_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY.append(
        RCCSISimKeys.COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
    RCCSI_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY.append(
        RCCSISimKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)

    PAUSE_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY = []
    PAUSE_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY.append(
        PauseSimKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
    PAUSE_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY.append(
        PauseSimKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
    PAUSE_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY.append(
        PauseSimKeys.READ_VALIDATION_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
    PAUSE_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY.append(
        PauseSimKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
    PAUSE_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY.append(
        PauseSimKeys.RESTART_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)

    di_stackedKeys[SimKeys.ONCHIP_NETWORKMSG_SIZE_8BYTES_FLITS_KEY] = [
        MESI_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY, VISER_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY,
        RCCSI_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY, PAUSE_TRAFFIC_ONCHIP_8BYTES_FLITS_KEY
    ]
    '''

    # 16 bytes
    MESI_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY = []
    MESI_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY.append(
        MESISimKeys.MEM_ONCHIP_NETWORKMSG_SIZE_16BYTES_FLITS_KEY)
    MESI_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY.append(
        MESISimKeys.COHERENCE_ONCHIP_NETWORKMSG_SIZE_16BYTES_FLITS_KEY)

    VISER_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY = []
    VISER_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY.append(
        ViserSimKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
    VISER_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY.append(
        ViserSimKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
    VISER_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY.append(
        ViserSimKeys.READ_VALIDATION_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
    VISER_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY.append(
        ViserSimKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)

    RCCSI_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY = []
    RCCSI_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY.append(
        RCCSISimKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
    RCCSI_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY.append(
        RCCSISimKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
    RCCSI_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY.append(
        RCCSISimKeys.RDVAL_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
    RCCSI_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY.append(
        RCCSISimKeys.COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
    RCCSI_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY.append(
        RCCSISimKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)

    PAUSE_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY = []
    PAUSE_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY.append(
        PauseSimKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
    PAUSE_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY.append(
        PauseSimKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
    PAUSE_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY.append(
        PauseSimKeys.READ_VALIDATION_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
    PAUSE_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY.append(
        PauseSimKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
    PAUSE_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY.append(
        PauseSimKeys.RESTART_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)

    di_stackedKeys[SimKeys.ONCHIP_NETWORKMSG_SIZE_16BYTES_FLITS_KEY] = [
        MESI_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY, VISER_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY,
        RCCSI_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY, PAUSE_TRAFFIC_ONCHIP_16BYTES_FLITS_KEY
    ]
    '''
    # 32 bytes
    MESI_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY = []
    MESI_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY.append(
        MESISimKeys.MEM_ONCHIP_NETWORKMSG_SIZE_32BYTES_FLITS_KEY)
    MESI_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY.append(
        MESISimKeys.COHERENCE_ONCHIP_NETWORKMSG_SIZE_32BYTES_FLITS_KEY)

    VISER_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY = []
    VISER_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY.append(
        ViserSimKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
    VISER_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY.append(
        ViserSimKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
    VISER_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY.append(
        ViserSimKeys.READ_VALIDATION_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
    VISER_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY.append(
        ViserSimKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)

    RCCSI_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY = []
    RCCSI_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY.append(
        RCCSISimKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
    RCCSI_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY.append(
        RCCSISimKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
    RCCSI_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY.append(
        RCCSISimKeys.RDVAL_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
    RCCSI_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY.append(
        RCCSISimKeys.COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
    RCCSI_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY.append(
        RCCSISimKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)

    PAUSE_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY = []
    PAUSE_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY.append(
        PauseSimKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
    PAUSE_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY.append(
        PauseSimKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
    PAUSE_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY.append(
        PauseSimKeys.READ_VALIDATION_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
    PAUSE_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY.append(
        PauseSimKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
    PAUSE_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY.append(
        PauseSimKeys.RESTART_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)

    di_stackedKeys[SimKeys.ONCHIP_NETWORKMSG_SIZE_32BYTES_FLITS_KEY] = [
        MESI_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY, VISER_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY,
        RCCSI_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY, PAUSE_TRAFFIC_ONCHIP_32BYTES_FLITS_KEY
    ]

    # off-chip traffic
    # 16 bytes
    MESI_TRAFFIC_OFFCHIP_16BYTES_FLITS_KEY = []
    MESI_TRAFFIC_OFFCHIP_16BYTES_FLITS_KEY.append(SimKeys.LLC_MEM_MSG_SIZE_16BYTES_FLITS_KEY)

    VISER_TRAFFIC_OFFCHIP_16BYTES_FLITS_KEY = []
    RCCSI_TRAFFIC_OFFCHIP_16BYTES_FLITS_KEY = []

    PAUSE_TRAFFIC_OFFCHIP_16BYTES_FLITS_KEY = []
    PAUSE_TRAFFIC_OFFCHIP_16BYTES_FLITS_KEY.append(
        PauseSimKeys.NON_RESTART_OFFCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
    PAUSE_TRAFFIC_OFFCHIP_16BYTES_FLITS_KEY.append(
        PauseSimKeys.RESTART_OFFCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
    di_stackedKeys[SimKeys.LLC_MEM_MSG_SIZE_16BYTES_FLITS_KEY] = [
        MESI_TRAFFIC_OFFCHIP_16BYTES_FLITS_KEY, VISER_TRAFFIC_OFFCHIP_16BYTES_FLITS_KEY,
        RCCSI_TRAFFIC_OFFCHIP_16BYTES_FLITS_KEY, PAUSE_TRAFFIC_OFFCHIP_16BYTES_FLITS_KEY
    ]
    '''

    MESI_ENERGY_KEY = []
    MESI_ENERGY_KEY.append(EnergyStatsKeys.STATIC_ENERGY)
    MESI_ENERGY_KEY.append(EnergyStatsKeys.DYNAMIC_ENERGY)
    MESI_ENERGY_KEY.append(EnergyStatsKeys.BLOOM_FILTER_ENERGY)

    VISER_ENERGY_KEY = []
    VISER_ENERGY_KEY.append(EnergyStatsKeys.STATIC_ENERGY)
    VISER_ENERGY_KEY.append(EnergyStatsKeys.DYNAMIC_ENERGY)
    VISER_ENERGY_KEY.append(EnergyStatsKeys.BLOOM_FILTER_ENERGY)
    if not Constants.ADD_AIM_McPAT:
        VISER_ENERGY_KEY.append(EnergyStatsKeys.AIM_STATIC_ENERGY)
        VISER_ENERGY_KEY.append(EnergyStatsKeys.AIM_DYNAMIC_ENERGY)

    RCCSI_ENERGY_KEY = []

    PAUSE_ENERGY_KEY = []

    di_energyStackedKeys[EnergyStatsKeys.TOTAL_ENERGY] = [
        MESI_ENERGY_KEY, VISER_ENERGY_KEY, RCCSI_ENERGY_KEY, PAUSE_ENERGY_KEY
    ]
