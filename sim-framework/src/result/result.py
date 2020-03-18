import os

from options import merge, util
from options.constants import Constants
from result.bargraph import BarGraph
from result.htmlproduct import HTMLProduct
from result.resultset import ResultSet
from result.stackedbargraph import StackedBarGraph
from result.statskeys import EnergyStatsKeys as ESKeys
from result.statskeys import MESISimKeys as MSKeys
from result.statskeys import PauseSimKeys, PintoolKeys
from result.statskeys import RCCSISimKeys as RSKeys
from result.statskeys import SimKeys, StackedKeys
from result.statskeys import ViserSimKeys as VSKeys
from tasks.runtask import RunTask


class Result(Constants):

    def __init__(self, options):
        self.options = options

        self.normDir = ""
        self.absDir = ""

        self.pintoolStatsKeysList = []  # List to compute Pintool stats table
        self.__populatePintoolStatsTableList(self.pintoolStatsKeysList)

        self.simStatsKeysList = []  # List to compute simulator stats table
        self.__populateSimulatorStatsTableList(self.simStatsKeysList, options)

        self.absSimYKeysList = []  # List to plot absolute graphs
        self.__populateAbsoluteKeysList(self.absSimYKeysList, options)

        self.normSimYKeysList = []  # List to plot normalized graphs
        self.__populateNormalizedKeysList(self.normSimYKeysList, options)

        self.stackedFile = None

        # List to compute energy stats table
        self.ESKeysList = [
            ESKeys.AREA, ESKeys.STATIC_POWER, ESKeys.DYNAMIC_POWER,
            SimKeys.BANDWIDTH_CYCLE_COUNT_KEY, ESKeys.STATIC_ENERGY, ESKeys.DYNAMIC_ENERGY,
            ESKeys.BLOOM_FILTER_ENERGY, ESKeys.AIM_STATIC_ENERGY, ESKeys.AIM_DYNAMIC_ENERGY,
            ESKeys.TOTAL_ENERGY
        ]

    def __populatePintoolStatsTableList(self, pintoolStatsKeysList):
        pintoolStatsKeysList.append(PintoolKeys.TOTAL_EVENTS_KEY)
        pintoolStatsKeysList.append(PintoolKeys.ROI_START_KEY)
        pintoolStatsKeysList.append(PintoolKeys.ROI_END_KEY)
        pintoolStatsKeysList.append(PintoolKeys.THREAD_BEGIN_KEY)
        pintoolStatsKeysList.append(PintoolKeys.THREAD_END_KEY)
        pintoolStatsKeysList.append(PintoolKeys.MEMORY_EVENTS_KEY)
        pintoolStatsKeysList.append(PintoolKeys.READ_EVENTS_KEY)
        pintoolStatsKeysList.append(PintoolKeys.WRITE_EVENTS_KEY)
        pintoolStatsKeysList.append(PintoolKeys.ATOMIC_READS_KEY)
        pintoolStatsKeysList.append(PintoolKeys.ATOMIC_WRITES_KEY)
        pintoolStatsKeysList.append(PintoolKeys.LOCK_ACQS_KEY)
        pintoolStatsKeysList.append(PintoolKeys.LOCK_RELS_KEY)
        pintoolStatsKeysList.append(PintoolKeys.LOCK_ACQ_READS_KEY)
        pintoolStatsKeysList.append(PintoolKeys.LOCK_ACQ_WRITES_KEY)
        pintoolStatsKeysList.append(PintoolKeys.LOCK_REL_WRITES_KEY)
        pintoolStatsKeysList.append(PintoolKeys.THREAD_SPAWN_KEY)
        pintoolStatsKeysList.append(PintoolKeys.THREAD_JOIN_KEY)
        pintoolStatsKeysList.append(PintoolKeys.BASIC_BLOCKS_KEY)

    def __populateMESIStats(self, simStatsKeysList):
        simStatsKeysList.append(MSKeys.REMOTE_READ_HITS_KEY)
        simStatsKeysList.append(MSKeys.REMOTE_WRITE_HITS_KEY)
        simStatsKeysList.append(MSKeys.UPGRADE_MISSES_KEY)

        simStatsKeysList.append(MSKeys.MEM_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(MSKeys.RATIO_MEM_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(MSKeys.COHERENCE_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(MSKeys.RATIO_COHERENCE_EXEC_CYCLE_COUNT_KEY)

        simStatsKeysList.append(MSKeys.MEM_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(MSKeys.RATIO_MEM_ONCHIP_NETWORK_MSGS_KEY)
        # simStatsKeysList.append(
        #     MSKeys.MEM_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        # simStatsKeysList.append(
        #     MSKeys.RATIO_MEM_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        # simStatsKeysList.append(
        #     MSKeys.MEM_ONCHIP_NETWORKMSG_SIZE_4BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     MSKeys.RATIO_MEM_ONCHIP_NETWORKMSG_SIZE_4BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     MSKeys.MEM_ONCHIP_NETWORKMSG_SIZE_8BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     MSKeys.RATIO_MEM_ONCHIP_NETWORKMSG_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(MSKeys.MEM_ONCHIP_NETWORKMSG_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(MSKeys.RATIO_MEM_ONCHIP_NETWORKMSG_SIZE_16BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     MSKeys.MEM_ONCHIP_NETWORKMSG_SIZE_32BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     MSKeys.RATIO_MEM_ONCHIP_NETWORKMSG_SIZE_32BYTES_FLITS_KEY)

        simStatsKeysList.append(MSKeys.COHERENCE_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(MSKeys.RATIO_COHERENCE_ONCHIP_NETWORK_MSGS_KEY)
        # simStatsKeysList.append(
        #     MSKeys.COHERENCE_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        # simStatsKeysList.append(
        #     MSKeys.RATIO_COHERENCE_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        # simStatsKeysList.append(
        #     MSKeys.COHERENCE_ONCHIP_NETWORKMSG_SIZE_4BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     MSKeys.RATIO_COHERENCE_ONCHIP_NETWORKMSG_SIZE_4BYTES_FLITS_KEY
        # )
        # simStatsKeysList.append(
        #     MSKeys.COHERENCE_ONCHIP_NETWORKMSG_SIZE_8BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     MSKeys.RATIO_COHERENCE_ONCHIP_NETWORKMSG_SIZE_8BYTES_FLITS_KEY
        # )
        simStatsKeysList.append(MSKeys.COHERENCE_ONCHIP_NETWORKMSG_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(MSKeys.RATIO_COHERENCE_ONCHIP_NETWORKMSG_SIZE_16BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     MSKeys.COHERENCE_ONCHIP_NETWORKMSG_SIZE_32BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     MSKeys.
        #     RATIO_COHERENCE_ONCHIP_NETWORKMSG_SIZE_32BYTES_FLITS_KEY)

    def __populateViserStats(self, simStatsKeysList):
        simStatsKeysList.append(VSKeys.WRITE_AFTER_READ_UPGRADES_KEY)
        simStatsKeysList.append(VSKeys.TOTAL_MEMORY_ACCESSES_SPECIAL_INVALID_KEY)

        simStatsKeysList.append(VSKeys.AIM_READ_HITS_KEY)
        simStatsKeysList.append(VSKeys.AIM_READ_MISSES_KEY)
        simStatsKeysList.append(VSKeys.AIM_WRITE_HITS_KEY)
        simStatsKeysList.append(VSKeys.AIM_WRITE_MISSES_KEY)
        simStatsKeysList.append(VSKeys.AIM_LINE_EVICTIONS_KEY)

        simStatsKeysList.append(VSKeys.REG_EXEC_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(VSKeys.RATIO_REG_EXEC_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(VSKeys.PRE_COMMIT_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(VSKeys.RATIO_PRE_COMMIT_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(VSKeys.READ_VALIDATION_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(VSKeys.RATIO_READ_VALIDATION_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(VSKeys.POST_COMMIT_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(VSKeys.RATIO_POST_COMMIT_EXEC_CYCLE_COUNT_KEY)

        simStatsKeysList.append(VSKeys.REG_EXEC_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(VSKeys.RATIO_REG_EXEC_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(VSKeys.PRE_COMMIT_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(VSKeys.RATIO_PRE_COMMIT_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(VSKeys.READ_VALIDATION_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(VSKeys.RATIO_READ_VALIDATION_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(VSKeys.POST_COMMIT_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(VSKeys.RATIO_POST_COMMIT_BW_CYCLE_COUNT_KEY)

        simStatsKeysList.append(VSKeys.VALIDATION_ATTEMPTS_KEY)
        simStatsKeysList.append(VSKeys.PRECISE_CONFLICTS_KEY)
        simStatsKeysList.append(VSKeys.NUM_SCAVENGES_KEY)

        simStatsKeysList.append(VSKeys.UPGRADE_NETWORK_MSGS_KEY)
        simStatsKeysList.append(VSKeys.RATIO_UPGRADE_NETWORK_MSGS_KEY)
        # simStatsKeysList.append(VSKeys.UPGRADE_NETWORKMSG_BYTES_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_UPGRADE_NETWORKMSG_BYTES_KEY)
        # simStatsKeysList.append(
        #     VSKeys.UPGRADE_NETWORKMSG_SIZE_4BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_UPGRADE_NETWORKMSG_SIZE_4BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.UPGRADE_NETWORKMSG_SIZE_8BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_UPGRADE_NETWORKMSG_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(VSKeys.UPGRADE_NETWORKMSG_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(VSKeys.RATIO_UPGRADE_NETWORKMSG_SIZE_16BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.UPGRADE_NETWORKMSG_SIZE_32BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_UPGRADE_NETWORKMSG_SIZE_32BYTES_FLITS_KEY)

        # simStatsKeysList.append(VSKeys.ONCHIP_MSGS_INCORRECT_KEY)
        # simStatsKeysList.append(VSKeys.ONCHIP_MSGS_BYTES_INCORRECT_KEY)
        # simStatsKeysList.append(
        #     VSKeys.ONCHIP_MSGS_4BYTES_FLITS_INCORRECT_KEY)
        # simStatsKeysList.append(
        #     VSKeys.ONCHIP_MSGS_8BYTES_FLITS_INCORRECT_KEY)
        # simStatsKeysList.append(
        #     VSKeys.ONCHIP_MSGS_16BYTES_FLITS_INCORRECT_KEY)
        # simStatsKeysList.append(
        #     VSKeys.ONCHIP_MSGS_32BYTES_FLITS_INCORRECT_KEY)

        simStatsKeysList.append(VSKeys.REG_EXEC_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(VSKeys.RATIO_REG_EXEC_ONCHIP_NETWORK_MSGS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.REG_EXEC_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_REG_EXEC_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        # simStatsKeysList.append(
        #     VSKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(VSKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(VSKeys.RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)

        simStatsKeysList.append(VSKeys.PRE_COMMIT_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(VSKeys.RATIO_PRE_COMMIT_ONCHIP_NETWORK_MSGS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.PRE_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_PRE_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        # simStatsKeysList.append(
        #     VSKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(VSKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(VSKeys.RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY
        # )

        simStatsKeysList.append(VSKeys.READ_VALIDATION_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(VSKeys.RATIO_READ_VALIDATION_ONCHIP_NETWORK_MSGS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.READ_VALIDATION_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_READ_VALIDATION_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY
        # )
        # simStatsKeysList.append(
        #     VSKeys.READ_VALIDATION_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.
        #     RATIO_READ_VALIDATION_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.READ_VALIDATION_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.
        #     RATIO_READ_VALIDATION_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(VSKeys.READ_VALIDATION_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(VSKeys.RATIO_READ_VALIDATION_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.READ_VALIDATION_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.
        #     RATIO_READ_VALIDATION_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)

        simStatsKeysList.append(VSKeys.POST_COMMIT_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(VSKeys.RATIO_POST_COMMIT_ONCHIP_NETWORK_MSGS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.POST_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_POST_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        # simStatsKeysList.append(
        #     VSKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY
        # )
        # simStatsKeysList.append(
        #     VSKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY
        # )
        simStatsKeysList.append(VSKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(VSKeys.RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.
        #     RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)

        simStatsKeysList.append(VSKeys.TCC_REG_WB_OVERFLOWS_8K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_REG_WB_OVERFLOWS_8K_KEY)
        simStatsKeysList.append(VSKeys.TCC_REG_WB_OVERFLOWS_16K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_REG_WB_OVERFLOWS_16K_KEY)
        simStatsKeysList.append(VSKeys.TCC_REG_WB_OVERFLOWS_32K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_REG_WB_OVERFLOWS_32K_KEY)
        simStatsKeysList.append(VSKeys.TCC_REG_WB_OVERFLOWS_64K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_REG_WB_OVERFLOWS_64K_KEY)

        simStatsKeysList.append(VSKeys.TCC_REG_CACHE_OVERFLOWS_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_REG_CACHE_OVERFLOWS_KEY)

        simStatsKeysList.append(VSKeys.TCC_REGIONS_OVERFLOWS_8K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_REGIONS_OVERFLOWS_8K_KEY)
        simStatsKeysList.append(VSKeys.TCC_REGIONS_OVERFLOWS_16K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_REGIONS_OVERFLOWS_16K_KEY)
        simStatsKeysList.append(VSKeys.TCC_REGIONS_OVERFLOWS_32K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_REGIONS_OVERFLOWS_32K_KEY)
        simStatsKeysList.append(VSKeys.TCC_REGIONS_OVERFLOWS_64K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_REGIONS_OVERFLOWS_64K_KEY)

        simStatsKeysList.append(VSKeys.TCC_REGIONS_FIRST_WB_OVERFLOWS_8K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_REGIONS_FIRST_WB_OVERFLOWS_8K_KEY)
        simStatsKeysList.append(VSKeys.TCC_REGIONS_FIRST_WB_OVERFLOWS_16K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_REGIONS_FIRST_WB_OVERFLOWS_16K_KEY)
        simStatsKeysList.append(VSKeys.TCC_REGIONS_FIRST_WB_OVERFLOWS_32K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_REGIONS_FIRST_WB_OVERFLOWS_32K_KEY)
        simStatsKeysList.append(VSKeys.TCC_REGIONS_FIRST_WB_OVERFLOWS_64K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_REGIONS_FIRST_WB_OVERFLOWS_64K_KEY)

        simStatsKeysList.append(VSKeys.TCC_REGIONS_FIRST_CACHE_OVERFLOWS_8K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_REGIONS_FIRST_CACHE_OVERFLOWS_8K_KEY)
        simStatsKeysList.append(VSKeys.TCC_REGIONS_FIRST_CACHE_OVERFLOWS_16K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_REGIONS_FIRST_CACHE_OVERFLOWS_16K_KEY)
        simStatsKeysList.append(VSKeys.TCC_REGIONS_FIRST_CACHE_OVERFLOWS_32K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_REGIONS_FIRST_CACHE_OVERFLOWS_32K_KEY)
        simStatsKeysList.append(VSKeys.TCC_REGIONS_FIRST_CACHE_OVERFLOWS_64K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_REGIONS_FIRST_CACHE_OVERFLOWS_64K_KEY)

        simStatsKeysList.append(VSKeys.TCC_SERIALIZED_MEM_ACCESSES_8K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_SERIALIZED_MEM_ACCESSES_8K_KEY)
        simStatsKeysList.append(VSKeys.TCC_SERIALIZED_MEM_ACCESSES_16K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_SERIALIZED_MEM_ACCESSES_16K_KEY)
        simStatsKeysList.append(VSKeys.TCC_SERIALIZED_MEM_ACCESSES_32K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_SERIALIZED_MEM_ACCESSES_32K_KEY)
        simStatsKeysList.append(VSKeys.TCC_SERIALIZED_MEM_ACCESSES_64K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_SERIALIZED_MEM_ACCESSES_64K_KEY)

        simStatsKeysList.append(VSKeys.TCC_CYCLES_8K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_CYCLES_8K_KEY)
        simStatsKeysList.append(VSKeys.TCC_CYCLES_16K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_CYCLES_16K_KEY)
        simStatsKeysList.append(VSKeys.TCC_CYCLES_32K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_CYCLES_32K_KEY)
        simStatsKeysList.append(VSKeys.TCC_CYCLES_64K_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_CYCLES_64K_KEY)

        simStatsKeysList.append(VSKeys.TCC_BDCAST_MSG_BYTES_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_BDCAST_MSG_BYTES_KEY)
        # simStatsKeysList.append(VSKeys.TCC_BDCAST_MSG_4BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_TCC_BDCAST_MSG_4BYTES_FLITS_KEY)
        # simStatsKeysList.append(VSKeys.TCC_BDCAST_MSG_8BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_TCC_BDCAST_MSG_8BYTES_FLITS_KEY)
        simStatsKeysList.append(VSKeys.TCC_BDCAST_MSG_16BYTES_FLITS_KEY)
        simStatsKeysList.append(VSKeys.RATIO_TCC_BDCAST_MSG_16BYTES_FLITS_KEY)
        # simStatsKeysList.append(VSKeys.TCC_BDCAST_MSG_32BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_TCC_BDCAST_MSG_32BYTES_FLITS_KEY)

        simStatsKeysList.append(VSKeys.RV_DEFERRED_LINE_MSGS_KEY)
        simStatsKeysList.append(VSKeys.RATIO_RV_DEFERRED_LINE_MSGS_KEY)
        # simStatsKeysList.append(VSKeys.RV_DEFERRED_LINE_MSGS_BYTES_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_RV_DEFERRED_LINE_MSGS_BYTES_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RV_DEFERRED_LINE_MSGS_4BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_RV_DEFERRED_LINE_MSGS_4BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RV_DEFERRED_LINE_MSGS_8BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_RV_DEFERRED_LINE_MSGS_8BYTES_FLITS_KEY)
        simStatsKeysList.append(VSKeys.RV_DEFERRED_LINE_MSGS_16BYTES_FLITS_KEY)
        simStatsKeysList.append(VSKeys.RATIO_RV_DEFERRED_LINE_MSGS_16BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RV_DEFERRED_LINE_MSGS_32BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.RATIO_RV_DEFERRED_LINE_MSGS_32BYTES_FLITS_KEY)

        # simStatsKeysList.append(VSKeys.ONCHIP_NO_COMPACT_VERSIONS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.ONCHIP_SIZE_BYTES_NO_COMPACT_VERSIONS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.ONCHIP_SIZE_4BYTES_FLITS_NO_COMPACT_VERSIONS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.ONCHIP_SIZE_8BYTES_FLITS_NO_COMPACT_VERSIONS_KEY)
        # simStatsKeysList.append(VSKeys.ONCHIP_SIZE_16BYTES_FLITS_NO_COMPACT_VERSIONS_KEY)
        # simStatsKeysList.append(
        #     VSKeys.ONCHIP_SIZE_32BYTES_FLITS_NO_COMPACT_VERSIONS_KEY)

        simStatsKeysList.append(VSKeys.SCAVENGE_TIME_KEY)

        simStatsKeysList.append(VSKeys.BLOOM_FILTER_READ_ENERGY)
        simStatsKeysList.append(VSKeys.BLOOM_FILTER_WRITE_ENERGY)
        simStatsKeysList.append(VSKeys.BLOOM_FILTER_TOTAL_ENERGY)

        # simStatsKeysList.append(VSKeys.AIM_DYNAMIC_READ_ENERGY)
        # simStatsKeysList.append(VSKeys.AIM_DYNAMIC_WRITE_ENERGY)
        # simStatsKeysList.append(VSKeys.AIM_DYNAMIC_TOTAL_ENERGY)

    def __populateRCCSIStats(self, simStatsKeysList):
        simStatsKeysList.append(RSKeys.WRITE_AFTER_READ_UPGRADES_KEY)

        simStatsKeysList.append(RSKeys.REG_EXEC_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.RATIO_REG_EXEC_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.PRE_COMMIT_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.RATIO_PRE_COMMIT_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.READ_VALIDATION_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.RATIO_READ_VALIDATION_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.STALL_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.RATIO_STALL_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.COMMIT_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.RATIO_COMMIT_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.POST_COMMIT_EXEC_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.RATIO_POST_COMMIT_EXEC_CYCLE_COUNT_KEY)

        simStatsKeysList.append(RSKeys.REG_EXEC_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.RATIO_REG_EXEC_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.PRE_COMMIT_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.RATIO_PRE_COMMIT_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.READ_VALIDATION_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.RATIO_READ_VALIDATION_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.STALL_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.RATIO_STALL_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.COMMIT_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.RATIO_COMMIT_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.POST_COMMIT_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(RSKeys.RATIO_POST_COMMIT_BW_CYCLE_COUNT_KEY)

        simStatsKeysList.append(RSKeys.PRECISE_CONFLICTS_KEY)
        simStatsKeysList.append(RSKeys.PRECISE_WRWR_CONFLICTS_KEY)
        simStatsKeysList.append(RSKeys.PRECISE_WRRD_CONFLICTS_KEY)
        simStatsKeysList.append(RSKeys.PRECISE_RDVAL_CONFLICTS_KEY)

        simStatsKeysList.append(RSKeys.REG_EXEC_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_REG_EXEC_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(RSKeys.REG_EXEC_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(RSKeys.RATIO_REG_EXEC_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(RSKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)

        simStatsKeysList.append(RSKeys.PRE_COMMIT_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_PRE_COMMIT_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(RSKeys.PRE_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(RSKeys.RATIO_PRE_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(RSKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)

        simStatsKeysList.append(RSKeys.RDVAL_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_RDVAL_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(RSKeys.RDVAL_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(RSKeys.RATIO_RDVAL_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(RSKeys.RDVAL_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_RDVAL_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RDVAL_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_RDVAL_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RDVAL_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_RDVAL_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RDVAL_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_RDVAL_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)

        simStatsKeysList.append(RSKeys.COMMIT_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_COMMIT_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(RSKeys.COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(RSKeys.RATIO_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(RSKeys.COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)

        simStatsKeysList.append(RSKeys.POST_COMMIT_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_POST_COMMIT_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(RSKeys.POST_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(RSKeys.RATIO_POST_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(RSKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
        simStatsKeysList.append(RSKeys.RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)

    def __populatePauseStats(self, simStatsKeysList):
        simStatsKeysList.append(VSKeys.WRITE_AFTER_READ_UPGRADES_KEY)
        simStatsKeysList.append(VSKeys.TOTAL_MEMORY_ACCESSES_SPECIAL_INVALID_KEY)

        simStatsKeysList.append(VSKeys.AIM_READ_HITS_KEY)
        simStatsKeysList.append(VSKeys.AIM_READ_MISSES_KEY)
        simStatsKeysList.append(VSKeys.AIM_WRITE_HITS_KEY)
        simStatsKeysList.append(VSKeys.AIM_WRITE_MISSES_KEY)
        simStatsKeysList.append(VSKeys.AIM_LINE_EVICTIONS_KEY)

        # bw driven cycles
        simStatsKeysList.append(PauseSimKeys.RESTART_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_RESTART_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(PauseSimKeys.PAUSE_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_PAUSE_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(PauseSimKeys.REG_EXEC_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_REG_EXEC_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(PauseSimKeys.PRE_COMMIT_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_PRE_COMMIT_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(PauseSimKeys.READ_VALIDATION_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_READ_VALIDATION_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(PauseSimKeys.POST_COMMIT_BW_CYCLE_COUNT_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_POST_COMMIT_BW_CYCLE_COUNT_KEY)

        simStatsKeysList.append(VSKeys.NUM_SCAVENGES_KEY)

        # on-chip traffic
        simStatsKeysList.append(PauseSimKeys.RESTART_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_RESTART_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(PauseSimKeys.RESTART_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_RESTART_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RESTART_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_RESTART_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RESTART_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_RESTART_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RESTART_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_RESTART_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)

        # off-chip traffic
        simStatsKeysList.append(PauseSimKeys.RESTART_OFFCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_RESTART_OFFCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(PauseSimKeys.RESTART_OFFCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_RESTART_OFFCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RESTART_OFFCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_RESTART_OFFCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RESTART_OFFCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_RESTART_OFFCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.NON_RESTART_OFFCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(
            PauseSimKeys.RATIO_NON_RESTART_OFFCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RESTART_OFFCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_RESTART_OFFCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)

        simStatsKeysList.append(PauseSimKeys.REG_EXEC_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_REG_EXEC_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(PauseSimKeys.REG_EXEC_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_REG_EXEC_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(PauseSimKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.REG_EXEC_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_REG_EXEC_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)

        simStatsKeysList.append(PauseSimKeys.PRE_COMMIT_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_PRE_COMMIT_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(PauseSimKeys.PRE_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_PRE_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(PauseSimKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.PRE_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_PRE_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)

        simStatsKeysList.append(PauseSimKeys.READ_VALIDATION_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_READ_VALIDATION_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(PauseSimKeys.READ_VALIDATION_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_READ_VALIDATION_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(PauseSimKeys.READ_VALIDATION_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(
            PauseSimKeys.RATIO_READ_VALIDATION_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.READ_VALIDATION_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(
            PauseSimKeys.RATIO_READ_VALIDATION_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.READ_VALIDATION_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(
            PauseSimKeys.RATIO_READ_VALIDATION_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.READ_VALIDATION_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
        simStatsKeysList.append(
            PauseSimKeys.RATIO_READ_VALIDATION_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)

        simStatsKeysList.append(PauseSimKeys.POST_COMMIT_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_POST_COMMIT_ONCHIP_NETWORK_MSGS_KEY)
        simStatsKeysList.append(PauseSimKeys.POST_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_POST_COMMIT_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        simStatsKeysList.append(PauseSimKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(
            PauseSimKeys.RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.POST_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)
        simStatsKeysList.append(
            PauseSimKeys.RATIO_POST_COMMIT_ONCHIP_NETWORK_SIZE_32BYTES_FLITS_KEY)

        simStatsKeysList.append(PauseSimKeys.UPGRADE_NETWORK_MSGS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_UPGRADE_NETWORK_MSGS_KEY)
        simStatsKeysList.append(PauseSimKeys.UPGRADE_NETWORKMSG_BYTES_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_UPGRADE_NETWORKMSG_BYTES_KEY)
        simStatsKeysList.append(PauseSimKeys.UPGRADE_NETWORKMSG_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_UPGRADE_NETWORKMSG_SIZE_4BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.UPGRADE_NETWORKMSG_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_UPGRADE_NETWORKMSG_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.UPGRADE_NETWORKMSG_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_UPGRADE_NETWORKMSG_SIZE_16BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.UPGRADE_NETWORKMSG_SIZE_32BYTES_FLITS_KEY)
        simStatsKeysList.append(PauseSimKeys.RATIO_UPGRADE_NETWORKMSG_SIZE_32BYTES_FLITS_KEY)

        # regions
        simStatsKeysList.append(PauseSimKeys.CONFLICTED_REGIONS_KEY)
        simStatsKeysList.append(PauseSimKeys.DEADLOCKED_REGIONS_KEY)
        simStatsKeysList.append(PauseSimKeys.DEADLOCKED_REGIONS_WITH_DIRTY_EVICTION_KEY)
        simStatsKeysList.append(PauseSimKeys.VALIDATION_FAILED_REGIONS_KEY)
        simStatsKeysList.append(PauseSimKeys.VALIDATION_FAILED_REGIONS_WITH_DIRTY_EVICTION_KEY)

        # restarts
        simStatsKeysList.append(PauseSimKeys.WHOLE_APP_RESTARTS_KEY)
        simStatsKeysList.append(PauseSimKeys.REQUEST_REPROCESSING_KEY)
        simStatsKeysList.append(PauseSimKeys.REGION_RESTARTS_KEY)

        # conflicts
        simStatsKeysList.append(PauseSimKeys.PRECISE_CONFLICTS_KEY)
        simStatsKeysList.append(PauseSimKeys.DEAD_LOCKS_KEY)
        simStatsKeysList.append(PauseSimKeys.VALIDATION_ATTEMPTS_KEY)
        simStatsKeysList.append(PauseSimKeys.FAILED_VALIDATION_KEY)

    def __populateSimulatorStatsTableList(self, simStatsKeysList, options):
        # simStatsKeysList.append(SimKeys.EXECUTION_CYCLE_COUNT_KEY)
        simStatsKeysList.append(SimKeys.BANDWIDTH_CYCLE_COUNT_KEY)

        simStatsKeysList.append(SimKeys.L1_READ_HITS_KEY)
        simStatsKeysList.append(SimKeys.L1_READ_MISSES_KEY)
        simStatsKeysList.append(SimKeys.L1_WRITE_HITS_KEY)
        simStatsKeysList.append(SimKeys.L1_WRITE_MISSES_KEY)
        simStatsKeysList.append(SimKeys.L1_LINE_EVICTIONS_KEY)
        simStatsKeysList.append(SimKeys.L1_DIRTY_LINE_EVICTIONS_KEY)
        simStatsKeysList.append(SimKeys.L1_ATOMIC_READ_HITS_KEY)
        simStatsKeysList.append(SimKeys.L1_ATOMIC_READ_MISSES_KEY)
        simStatsKeysList.append(SimKeys.L1_ATOMIC_WRITE_HITS_KEY)
        simStatsKeysList.append(SimKeys.L1_ATOMIC_WRITE_MISSES_KEY)
        simStatsKeysList.append(SimKeys.L1_LOCK_READ_HITS_KEY)
        simStatsKeysList.append(SimKeys.L1_LOCK_READ_MISSES_KEY)
        simStatsKeysList.append(SimKeys.L1_LOCK_WRITE_HITS_KEY)
        simStatsKeysList.append(SimKeys.L1_LOCK_WRITE_MISSES_KEY)

        simStatsKeysList.append(SimKeys.L2_READ_HITS_KEY)
        simStatsKeysList.append(SimKeys.L2_READ_MISSES_KEY)
        simStatsKeysList.append(SimKeys.L2_WRITE_HITS_KEY)
        simStatsKeysList.append(SimKeys.L2_WRITE_MISSES_KEY)
        simStatsKeysList.append(SimKeys.L2_LINE_EVICTIONS_KEY)
        simStatsKeysList.append(SimKeys.L2_DIRTY_LINE_EVICTIONS_KEY)
        simStatsKeysList.append(SimKeys.L2_ATOMIC_READ_HITS_KEY)
        simStatsKeysList.append(SimKeys.L2_ATOMIC_READ_MISSES_KEY)
        simStatsKeysList.append(SimKeys.L2_ATOMIC_WRITE_HITS_KEY)
        simStatsKeysList.append(SimKeys.L2_ATOMIC_WRITE_MISSES_KEY)
        simStatsKeysList.append(SimKeys.L2_LOCK_READ_HITS_KEY)
        simStatsKeysList.append(SimKeys.L2_LOCK_READ_MISSES_KEY)
        simStatsKeysList.append(SimKeys.L2_LOCK_WRITE_HITS_KEY)
        simStatsKeysList.append(SimKeys.L2_LOCK_WRITE_MISSES_KEY)

        simStatsKeysList.append(SimKeys.L3_READ_HITS_KEY)
        simStatsKeysList.append(SimKeys.L3_READ_MISSES_KEY)
        simStatsKeysList.append(SimKeys.L3_WRITE_HITS_KEY)
        simStatsKeysList.append(SimKeys.L3_WRITE_MISSES_KEY)
        simStatsKeysList.append(SimKeys.L3_LINE_EVICTIONS_KEY)
        simStatsKeysList.append(SimKeys.L3_DIRTY_LINE_EVICTIONS_KEY)
        simStatsKeysList.append(SimKeys.L3_ATOMIC_READ_HITS_KEY)
        simStatsKeysList.append(SimKeys.L3_ATOMIC_READ_MISSES_KEY)
        simStatsKeysList.append(SimKeys.L3_ATOMIC_WRITE_HITS_KEY)
        simStatsKeysList.append(SimKeys.L3_ATOMIC_WRITE_MISSES_KEY)
        simStatsKeysList.append(SimKeys.L3_LOCK_READ_HITS_KEY)
        simStatsKeysList.append(SimKeys.L3_LOCK_READ_MISSES_KEY)
        simStatsKeysList.append(SimKeys.L3_LOCK_WRITE_HITS_KEY)
        simStatsKeysList.append(SimKeys.L3_LOCK_WRITE_MISSES_KEY)

        simStatsKeysList.append(SimKeys.TOTAL_READS_KEY)
        simStatsKeysList.append(SimKeys.TOTAL_WRITES_KEY)
        simStatsKeysList.append(SimKeys.TOTAL_MEMORY_ACCESSES_KEY)

        simStatsKeysList.append(SimKeys.TOTAL_ATOMIC_READS_KEY)
        simStatsKeysList.append(SimKeys.TOTAL_ATOMIC_WRITES_KEY)
        simStatsKeysList.append(SimKeys.TOTAL_ATOMIC_ACCESSES_KEY)

        simStatsKeysList.append(SimKeys.TOTAL_LOCK_READS_KEY)
        simStatsKeysList.append(SimKeys.TOTAL_LOCK_WRITES_KEY)
        simStatsKeysList.append(SimKeys.TOTAL_LOCK_ACCESSES_KEY)

        simStatsKeysList.append(SimKeys.BASIC_BLOCKS_KEY)
        simStatsKeysList.append(SimKeys.INSTRUCTIONS_KEY)
        simStatsKeysList.append(SimKeys.STACK_ACCESSES_KEY)
        simStatsKeysList.append(SimKeys.REGION_BOUNDARIES_KEY)
        simStatsKeysList.append(SimKeys.REGION_SIZE_KEY)

        # simStatsKeysList.append(SimKeys.CORELLC_NETWORK_MSGS_KEY)
        # simStatsKeysList.append(SimKeys.CORELLC_NETWORKMSG_SIZE_BYTES_KEY)
        # simStatsKeysList.append(
        #     SimKeys.CORELLC_NETWORKMSG_SIZE_4BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     SimKeys.CORELLC_NETWORKMSG_SIZE_8BYTES_FLITS_KEY)
        # simStatsKeysList.append(SimKeys.CORELLC_NETWORKMSG_SIZE_16BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     SimKeys.CORELLC_NETWORKMSG_SIZE_32BYTES_FLITS_KEY)

        simStatsKeysList.append(SimKeys.ONCHIP_NETWORK_MSGS_KEY)
        # simStatsKeysList.append(SimKeys.ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        # simStatsKeysList.append(
        #     SimKeys.ONCHIP_NETWORKMSG_SIZE_4BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     SimKeys.ONCHIP_NETWORKMSG_SIZE_8BYTES_FLITS_KEY)
        simStatsKeysList.append(SimKeys.ONCHIP_NETWORKMSG_SIZE_16BYTES_FLITS_KEY)
        # simStatsKeysList.append(
        #     SimKeys.ONCHIP_NETWORKMSG_SIZE_32BYTES_FLITS_KEY)

        # simStatsKeysList.append(SimKeys.LLC_MEM_MSGS_KEY)
        # simStatsKeysList.append(SimKeys.LLC_MEM_MSG_SIZE_BYTES_KEY)
        # simStatsKeysList.append(SimKeys.LLC_MEM_MSG_SIZE_4BYTES_FLITS_KEY)
        # simStatsKeysList.append(SimKeys.LLC_MEM_MSG_SIZE_8BYTES_FLITS_KEY)
        # simStatsKeysList.append(SimKeys.LLC_MEM_MSG_SIZE_16BYTES_FLITS_KEY)
        # simStatsKeysList.append(SimKeys.LLC_MEM_MSG_SIZE_32BYTES_FLITS_KEY)
        # simStatsKeysList.append(SimKeys.RATIO_LLC_MEM_MSGS_EXEC_CYCLES_KEY)
        # simStatsKeysList.append(SimKeys.RATIO_LLC_MEM_MSGS_BANDWIDTH_CYCLES_KEY)
        # simStatsKeysList.append(SimKeys.LLC_MEM_MSG_64BYTES_FLITS_KEY)

        simStatsKeysList.append(SimKeys.MEM_64BYTES_ACCESSES_KEY)
        simStatsKeysList.append(SimKeys.MEM_64BYTES_READS_KEY)
        simStatsKeysList.append(SimKeys.MEM_64BYTES_WRITES_KEY)

        simStatsKeysList.append(SimKeys.RUNNING_TIME_KEY)
        simStatsKeysList.append(SimKeys.MEMORY_USAGE_KEY)

        # simStatsKeysList.append(SimKeys.MAX_REQD_BW_4BYTES_FLITS_KEY)
        # simStatsKeysList.append(SimKeys.MAX_REQD_BW_8BYTES_FLITS_KEY)
        # simStatsKeysList.append(SimKeys.MAX_REQD_BW_16BYTES_FLITS_KEY)
        # simStatsKeysList.append(SimKeys.MAX_REQD_BW_32BYTES_FLITS_KEY)

        simStatsKeysList.append(SimKeys.SUM_REQD_ONCHIPBW_16BYTES_FLITS_KEY)
        simStatsKeysList.append(SimKeys.SUM_REQD_OFFCHIPBW_64BYTES_FLITS_KEY)

        if options.isMESIPresent():
            self.__populateMESIStats(simStatsKeysList)

        if options.isViserPresent():
            self.__populateViserStats(simStatsKeysList)

        if options.isRCCSIPresent():
            self.__populateRCCSIStats(simStatsKeysList)

        if options.isPausePresent():
            self.__populatePauseStats(simStatsKeysList)

    def __populateAbsoluteKeysList(self, absSimYKeysList, options):
        # absSimYKeysList.append(SimKeys.EXECUTION_CYCLE_COUNT_KEY)
        absSimYKeysList.append(SimKeys.BANDWIDTH_CYCLE_COUNT_KEY)
        if options.isPausePresent():
            absSimYKeysList.append(PauseSimKeys.RESTART_BW_CYCLE_COUNT_KEY)

        absSimYKeysList.append(SimKeys.L1_READ_HITS_KEY)
        absSimYKeysList.append(SimKeys.L1_READ_MISSES_KEY)
        absSimYKeysList.append(SimKeys.L1_WRITE_HITS_KEY)
        absSimYKeysList.append(SimKeys.L1_WRITE_MISSES_KEY)
        absSimYKeysList.append(SimKeys.L1_LINE_EVICTIONS_KEY)
        absSimYKeysList.append(SimKeys.L1_DIRTY_LINE_EVICTIONS_KEY)
        absSimYKeysList.append(SimKeys.L1_ATOMIC_READ_HITS_KEY)
        absSimYKeysList.append(SimKeys.L1_ATOMIC_READ_MISSES_KEY)
        absSimYKeysList.append(SimKeys.L1_ATOMIC_WRITE_HITS_KEY)
        absSimYKeysList.append(SimKeys.L1_ATOMIC_WRITE_MISSES_KEY)
        absSimYKeysList.append(SimKeys.L1_LOCK_READ_HITS_KEY)
        absSimYKeysList.append(SimKeys.L1_LOCK_READ_MISSES_KEY)
        absSimYKeysList.append(SimKeys.L1_LOCK_WRITE_HITS_KEY)
        absSimYKeysList.append(SimKeys.L1_LOCK_WRITE_MISSES_KEY)

        absSimYKeysList.append(SimKeys.L2_READ_HITS_KEY)
        absSimYKeysList.append(SimKeys.L2_READ_MISSES_KEY)
        absSimYKeysList.append(SimKeys.L2_WRITE_HITS_KEY)
        absSimYKeysList.append(SimKeys.L2_WRITE_MISSES_KEY)
        absSimYKeysList.append(SimKeys.L2_LINE_EVICTIONS_KEY)
        absSimYKeysList.append(SimKeys.L2_DIRTY_LINE_EVICTIONS_KEY)
        absSimYKeysList.append(SimKeys.L2_ATOMIC_READ_HITS_KEY)
        absSimYKeysList.append(SimKeys.L2_ATOMIC_READ_MISSES_KEY)
        absSimYKeysList.append(SimKeys.L2_ATOMIC_WRITE_HITS_KEY)
        absSimYKeysList.append(SimKeys.L2_ATOMIC_WRITE_MISSES_KEY)
        absSimYKeysList.append(SimKeys.L2_LOCK_READ_HITS_KEY)
        absSimYKeysList.append(SimKeys.L2_LOCK_READ_MISSES_KEY)
        absSimYKeysList.append(SimKeys.L2_LOCK_WRITE_HITS_KEY)
        absSimYKeysList.append(SimKeys.L2_LOCK_WRITE_MISSES_KEY)

        absSimYKeysList.append(SimKeys.L3_READ_HITS_KEY)
        absSimYKeysList.append(SimKeys.L3_READ_MISSES_KEY)
        absSimYKeysList.append(SimKeys.L3_WRITE_HITS_KEY)
        absSimYKeysList.append(SimKeys.L3_WRITE_MISSES_KEY)
        absSimYKeysList.append(SimKeys.L3_LINE_EVICTIONS_KEY)
        absSimYKeysList.append(SimKeys.L3_DIRTY_LINE_EVICTIONS_KEY)
        absSimYKeysList.append(SimKeys.L3_ATOMIC_READ_HITS_KEY)
        absSimYKeysList.append(SimKeys.L3_ATOMIC_READ_MISSES_KEY)
        absSimYKeysList.append(SimKeys.L3_ATOMIC_WRITE_HITS_KEY)
        absSimYKeysList.append(SimKeys.L3_ATOMIC_WRITE_MISSES_KEY)
        absSimYKeysList.append(SimKeys.L3_LOCK_READ_HITS_KEY)
        absSimYKeysList.append(SimKeys.L3_LOCK_READ_MISSES_KEY)
        absSimYKeysList.append(SimKeys.L3_LOCK_WRITE_HITS_KEY)
        absSimYKeysList.append(SimKeys.L3_LOCK_WRITE_MISSES_KEY)

        absSimYKeysList.append(SimKeys.TOTAL_READS_KEY)
        absSimYKeysList.append(SimKeys.TOTAL_WRITES_KEY)
        absSimYKeysList.append(SimKeys.TOTAL_MEMORY_ACCESSES_KEY)

        absSimYKeysList.append(SimKeys.TOTAL_ATOMIC_READS_KEY)
        absSimYKeysList.append(SimKeys.TOTAL_ATOMIC_WRITES_KEY)
        absSimYKeysList.append(SimKeys.TOTAL_ATOMIC_ACCESSES_KEY)

        absSimYKeysList.append(SimKeys.TOTAL_LOCK_READS_KEY)
        absSimYKeysList.append(SimKeys.TOTAL_LOCK_WRITES_KEY)
        absSimYKeysList.append(SimKeys.TOTAL_LOCK_ACCESSES_KEY)

        absSimYKeysList.append(SimKeys.BASIC_BLOCKS_KEY)
        absSimYKeysList.append(SimKeys.INSTRUCTIONS_KEY)

        absSimYKeysList.append(SimKeys.REGION_BOUNDARIES_KEY)
        absSimYKeysList.append(SimKeys.REGION_WITH_WRITES_KEY)
        absSimYKeysList.append(SimKeys.REGION_SIZE_KEY)

        # absSimYKeysList.append(SimKeys.CORELLC_NETWORK_MSGS_KEY)

        # absSimYKeysList.append(SimKeys.CORELLC_NETWORKMSG_SIZE_BYTES_KEY)
        if options.isPausePresent():
            absSimYKeysList.append(PauseSimKeys.RESTART_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)

        # absSimYKeysList.append(
        #     SimKeys.CORELLC_NETWORKMSG_SIZE_4BYTES_FLITS_KEY)
        # absSimYKeysList.append(
        #     SimKeys.CORELLC_NETWORKMSG_SIZE_8BYTES_FLITS_KEY)
        # absSimYKeysList.append(SimKeys.CORELLC_NETWORKMSG_SIZE_16BYTES_FLITS_KEY)
        # absSimYKeysList.append(
        #     SimKeys.CORELLC_NETWORKMSG_SIZE_32BYTES_FLITS_KEY)

        absSimYKeysList.append(SimKeys.ONCHIP_NETWORK_MSGS_KEY)
        # absSimYKeysList.append(SimKeys.ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        # absSimYKeysList.append(SimKeys.ONCHIP_NETWORKMSG_SIZE_4BYTES_FLITS_KEY)
        # absSimYKeysList.append(SimKeys.ONCHIP_NETWORKMSG_SIZE_8BYTES_FLITS_KEY)
        absSimYKeysList.append(SimKeys.ONCHIP_NETWORKMSG_SIZE_16BYTES_FLITS_KEY)
        # absSimYKeysList.append(
        #     SimKeys.ONCHIP_NETWORKMSG_SIZE_32BYTES_FLITS_KEY)

        # absSimYKeysList.append(SimKeys.LLC_MEM_MSGS_KEY)
        # absSimYKeysList.append(SimKeys.LLC_MEM_MSG_SIZE_BYTES_KEY)
        # absSimYKeysList.append(SimKeys.LLC_MEM_MSG_SIZE_4BYTES_FLITS_KEY)
        # absSimYKeysList.append(SimKeys.LLC_MEM_MSG_SIZE_8BYTES_FLITS_KEY)
        # absSimYKeysList.append(SimKeys.LLC_MEM_MSG_SIZE_16BYTES_FLITS_KEY)
        # absSimYKeysList.append(SimKeys.LLC_MEM_MSG_SIZE_32BYTES_FLITS_KEY)
        # absSimYKeysList.append(SimKeys.RATIO_LLC_MEM_MSGS_EXEC_CYCLES_KEY)
        # absSimYKeysList.append(SimKeys.RATIO_LLC_MEM_MSGS_BANDWIDTH_CYCLES_KEY)

        # absSimYKeysList.append(SimKeys.RUNNING_TIME_KEY)
        # absSimYKeysList.append(SimKeys.MEMORY_USAGE_KEY)

        # absSimYKeysList.append(SimKeys.MAX_REQD_BW_4BYTES_FLITS_KEY)
        # absSimYKeysList.append(SimKeys.MAX_REQD_BW_8BYTES_FLITS_KEY)
        # absSimYKeysList.append(SimKeys.MAX_REQD_BW_16BYTES_FLITS_KEY)
        # absSimYKeysList.append(SimKeys.MAX_REQD_BW_32BYTES_FLITS_KEY)

        absSimYKeysList.append(SimKeys.SUM_REQD_ONCHIPBW_16BYTES_FLITS_KEY)
        absSimYKeysList.append(SimKeys.SUM_REQD_OFFCHIPBW_64BYTES_FLITS_KEY)

        absSimYKeysList.append(SimKeys.MEM_64BYTES_ACCESSES_KEY)

        if options.isViserPresent():
            absSimYKeysList.append(VSKeys.WRITE_AFTER_READ_UPGRADES_KEY)
            absSimYKeysList.append(VSKeys.TOTAL_MEMORY_ACCESSES_SPECIAL_INVALID_KEY)

            absSimYKeysList.append(VSKeys.AIM_READ_HITS_KEY)
            absSimYKeysList.append(VSKeys.AIM_READ_MISSES_KEY)
            absSimYKeysList.append(VSKeys.AIM_WRITE_HITS_KEY)
            absSimYKeysList.append(VSKeys.AIM_WRITE_MISSES_KEY)
            absSimYKeysList.append(VSKeys.AIM_LINE_EVICTIONS_KEY)

            # absSimYKeysList.append(VSKeys.ONCHIP_MSGS_INCORRECT_KEY)
            # absSimYKeysList.append(
            #     VSKeys.ONCHIP_MSGS_BYTES_INCORRECT_KEY)
            # absSimYKeysList.append(
            #     VSKeys.ONCHIP_MSGS_4BYTES_FLITS_INCORRECT_KEY)
            # absSimYKeysList.append(
            #     VSKeys.ONCHIP_MSGS_8BYTES_FLITS_INCORRECT_KEY)
            # absSimYKeysList.append(
            #     VSKeys.ONCHIP_MSGS_16BYTES_FLITS_INCORRECT_KEY)
            # absSimYKeysList.append(
            #     VSKeys.ONCHIP_MSGS_32BYTES_FLITS_INCORRECT_KEY)

            # absSimYKeysList.append(VSKeys.ONCHIP_NO_COMPACT_VERSIONS_KEY)
            # absSimYKeysList.append(
            #     VSKeys.ONCHIP_SIZE_BYTES_NO_COMPACT_VERSIONS_KEY)
            # absSimYKeysList.append(
            #     VSKeys.ONCHIP_SIZE_4BYTES_FLITS_NO_COMPACT_VERSIONS_KEY)
            # absSimYKeysList.append(
            #     VSKeys.ONCHIP_SIZE_8BYTES_FLITS_NO_COMPACT_VERSIONS_KEY)
            # absSimYKeysList.append(VSKeys.ONCHIP_SIZE_16BYTES_FLITS_NO_COMPACT_VERSIONS_KEY)
            # absSimYKeysList.append(
            #     VSKeys.ONCHIP_SIZE_32BYTES_FLITS_NO_COMPACT_VERSIONS_KEY)

            absSimYKeysList.append(VSKeys.SCAVENGE_TIME_KEY)

            absSimYKeysList.append(VSKeys.BLOOM_FILTER_READ_ENERGY)
            absSimYKeysList.append(VSKeys.BLOOM_FILTER_WRITE_ENERGY)
            absSimYKeysList.append(VSKeys.BLOOM_FILTER_TOTAL_ENERGY)

            # absSimYKeysList.append(VSKeys.AIM_DYNAMIC_READ_ENERGY)
            # absSimYKeysList.append(VSKeys.AIM_DYNAMIC_WRITE_ENERGY)
            # absSimYKeysList.append(VSKeys.AIM_DYNAMIC_TOTAL_ENERGY)

        if options.isMESIPresent():
            absSimYKeysList.append(MSKeys.REMOTE_READ_HITS_KEY)
            absSimYKeysList.append(MSKeys.REMOTE_WRITE_HITS_KEY)
            absSimYKeysList.append(MSKeys.UPGRADE_MISSES_KEY)

        if options.isPausePresent():
            absSimYKeysList.append(PauseSimKeys.WRITE_AFTER_READ_UPGRADES_KEY)
            absSimYKeysList.append(PauseSimKeys.TOTAL_MEMORY_ACCESSES_SPECIAL_INVALID_KEY)

            absSimYKeysList.append(PauseSimKeys.AIM_READ_HITS_KEY)
            absSimYKeysList.append(PauseSimKeys.AIM_READ_MISSES_KEY)
            absSimYKeysList.append(PauseSimKeys.AIM_WRITE_HITS_KEY)
            absSimYKeysList.append(PauseSimKeys.AIM_WRITE_MISSES_KEY)
            absSimYKeysList.append(PauseSimKeys.AIM_LINE_EVICTIONS_KEY)
            absSimYKeysList.append(PauseSimKeys.L2_DIRTY_EVICTION_KEY)
            # regions
            absSimYKeysList.append(PauseSimKeys.CONFLICTED_REGIONS_KEY)
            absSimYKeysList.append(PauseSimKeys.DEADLOCKED_REGIONS_KEY)
            absSimYKeysList.append(PauseSimKeys.DEADLOCKED_REGIONS_WITH_DIRTY_EVICTION_KEY)
            absSimYKeysList.append(PauseSimKeys.VALIDATION_FAILED_REGIONS_KEY)
            absSimYKeysList.append(PauseSimKeys.VALIDATION_FAILED_REGIONS_WITH_DIRTY_EVICTION_KEY)

            # restarts
            absSimYKeysList.append(PauseSimKeys.WHOLE_APP_RESTARTS_KEY)
            absSimYKeysList.append(PauseSimKeys.REQUEST_REPROCESSING_KEY)
            absSimYKeysList.append(PauseSimKeys.REGION_RESTARTS_KEY)

    def __populateNormalizedKeysList(self, normSimYKeysList, options):
        # normSimYKeysList.append(SimKeys.EXECUTION_CYCLE_COUNT_KEY)
        normSimYKeysList.append(SimKeys.BANDWIDTH_CYCLE_COUNT_KEY)

        normSimYKeysList.append(SimKeys.L1_READ_HITS_KEY)
        normSimYKeysList.append(SimKeys.L1_READ_MISSES_KEY)
        normSimYKeysList.append(SimKeys.L1_WRITE_HITS_KEY)
        normSimYKeysList.append(SimKeys.L1_WRITE_MISSES_KEY)
        normSimYKeysList.append(SimKeys.L1_LINE_EVICTIONS_KEY)
        normSimYKeysList.append(SimKeys.L1_DIRTY_LINE_EVICTIONS_KEY)
        normSimYKeysList.append(SimKeys.L1_ATOMIC_READ_HITS_KEY)
        normSimYKeysList.append(SimKeys.L1_ATOMIC_READ_MISSES_KEY)
        normSimYKeysList.append(SimKeys.L1_ATOMIC_WRITE_HITS_KEY)
        normSimYKeysList.append(SimKeys.L1_ATOMIC_WRITE_MISSES_KEY)
        normSimYKeysList.append(SimKeys.L1_LOCK_READ_HITS_KEY)
        normSimYKeysList.append(SimKeys.L1_LOCK_READ_MISSES_KEY)
        normSimYKeysList.append(SimKeys.L1_LOCK_WRITE_HITS_KEY)
        normSimYKeysList.append(SimKeys.L1_LOCK_WRITE_MISSES_KEY)

        normSimYKeysList.append(SimKeys.L2_READ_HITS_KEY)
        normSimYKeysList.append(SimKeys.L2_READ_MISSES_KEY)
        normSimYKeysList.append(SimKeys.L2_WRITE_HITS_KEY)
        normSimYKeysList.append(SimKeys.L2_WRITE_MISSES_KEY)
        normSimYKeysList.append(SimKeys.L2_LINE_EVICTIONS_KEY)
        normSimYKeysList.append(SimKeys.L2_DIRTY_LINE_EVICTIONS_KEY)
        normSimYKeysList.append(SimKeys.L2_ATOMIC_READ_HITS_KEY)
        normSimYKeysList.append(SimKeys.L2_ATOMIC_READ_MISSES_KEY)
        normSimYKeysList.append(SimKeys.L2_ATOMIC_WRITE_HITS_KEY)
        normSimYKeysList.append(SimKeys.L2_ATOMIC_WRITE_MISSES_KEY)
        normSimYKeysList.append(SimKeys.L2_LOCK_READ_HITS_KEY)
        normSimYKeysList.append(SimKeys.L2_LOCK_READ_MISSES_KEY)
        normSimYKeysList.append(SimKeys.L2_LOCK_WRITE_HITS_KEY)
        normSimYKeysList.append(SimKeys.L2_LOCK_WRITE_MISSES_KEY)

        normSimYKeysList.append(SimKeys.L3_READ_HITS_KEY)
        normSimYKeysList.append(SimKeys.L3_READ_MISSES_KEY)
        normSimYKeysList.append(SimKeys.L3_WRITE_HITS_KEY)
        normSimYKeysList.append(SimKeys.L3_WRITE_MISSES_KEY)
        normSimYKeysList.append(SimKeys.L3_LINE_EVICTIONS_KEY)
        normSimYKeysList.append(SimKeys.L3_DIRTY_LINE_EVICTIONS_KEY)
        normSimYKeysList.append(SimKeys.L3_ATOMIC_READ_HITS_KEY)
        normSimYKeysList.append(SimKeys.L3_ATOMIC_READ_MISSES_KEY)
        normSimYKeysList.append(SimKeys.L3_ATOMIC_WRITE_HITS_KEY)
        normSimYKeysList.append(SimKeys.L3_ATOMIC_WRITE_MISSES_KEY)
        normSimYKeysList.append(SimKeys.L3_LOCK_READ_HITS_KEY)
        normSimYKeysList.append(SimKeys.L3_LOCK_READ_MISSES_KEY)
        normSimYKeysList.append(SimKeys.L3_LOCK_WRITE_HITS_KEY)
        normSimYKeysList.append(SimKeys.L3_LOCK_WRITE_MISSES_KEY)

        # normSimYKeysList.append(SimKeys.CORELLC_NETWORK_MSGS_KEY)
        # normSimYKeysList.append(SimKeys.CORELLC_NETWORKMSG_SIZE_BYTES_KEY)
        # normSimYKeysList.append(
        #     SimKeys.CORELLC_NETWORKMSG_SIZE_4BYTES_FLITS_KEY)
        # normSimYKeysList.append(
        #     SimKeys.CORELLC_NETWORKMSG_SIZE_8BYTES_FLITS_KEY)
        # normSimYKeysList.append(SimKeys.CORELLC_NETWORKMSG_SIZE_16BYTES_FLITS_KEY)
        # normSimYKeysList.append(
        #     SimKeys.CORELLC_NETWORKMSG_SIZE_32BYTES_FLITS_KEY)

        # normSimYKeysList.append(SimKeys.ONCHIP_NETWORK_MSGS_KEY)
        # normSimYKeysList.append(SimKeys.ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)
        # normSimYKeysList.append(
        #     SimKeys.ONCHIP_NETWORKMSG_SIZE_4BYTES_FLITS_KEY)
        # normSimYKeysList.append(
        #     SimKeys.ONCHIP_NETWORKMSG_SIZE_8BYTES_FLITS_KEY)
        # normSimYKeysList.append(SimKeys.ONCHIP_NETWORKMSG_SIZE_16BYTES_FLITS_KEY)
        # normSimYKeysList.append(
        #     SimKeys.ONCHIP_NETWORKMSG_SIZE_32BYTES_FLITS_KEY)

        # normSimYKeysList.append(SimKeys.LLC_MEM_MSGS_KEY)
        # normSimYKeysList.append(SimKeys.LLC_MEM_MSG_SIZE_BYTES_KEY)
        # normSimYKeysList.append(SimKeys.LLC_MEM_MSG_SIZE_4BYTES_FLITS_KEY)
        # normSimYKeysList.append(SimKeys.LLC_MEM_MSG_SIZE_8BYTES_FLITS_KEY)
        # normSimYKeysList.append(SimKeys.LLC_MEM_MSG_SIZE_16BYTES_FLITS_KEY)
        # normSimYKeysList.append(SimKeys.LLC_MEM_MSG_SIZE_32BYTES_FLITS_KEY)

        normSimYKeysList.append(SimKeys.MEM_64BYTES_ACCESSES_KEY)

        # normSimYKeysList.append(SimKeys.MEMORY_USAGE_KEY)

        if options.isViserPresent():
            pass
            #     normSimYKeysList.append(VSKeys.ONCHIP_MSGS_INCORRECT_KEY)
            #     normSimYKeysList.append(
            #         VSKeys.ONCHIP_MSGS_BYTES_INCORRECT_KEY)
            #     normSimYKeysList.append(
            #         VSKeys.ONCHIP_MSGS_4BYTES_FLITS_INCORRECT_KEY)
            #     normSimYKeysList.append(
            #         VSKeys.ONCHIP_MSGS_8BYTES_FLITS_INCORRECT_KEY)
            #     normSimYKeysList.append(
            #         VSKeys.ONCHIP_MSGS_16BYTES_FLITS_INCORRECT_KEY)
            #     normSimYKeysList.append(
            #         VSKeys.ONCHIP_MSGS_32BYTES_FLITS_INCORRECT_KEY)

        if options.isPausePresent():
            normSimYKeysList.append(PauseSimKeys.L2_DIRTY_EVICTION_KEY)
            # regions
            normSimYKeysList.append(PauseSimKeys.CONFLICTED_REGIONS_KEY)
            normSimYKeysList.append(PauseSimKeys.DEADLOCKED_REGIONS_KEY)
            normSimYKeysList.append(PauseSimKeys.DEADLOCKED_REGIONS_WITH_DIRTY_EVICTION_KEY)
            normSimYKeysList.append(PauseSimKeys.VALIDATION_FAILED_REGIONS_KEY)
            normSimYKeysList.append(PauseSimKeys.VALIDATION_FAILED_REGIONS_WITH_DIRTY_EVICTION_KEY)

            # restarts
            normSimYKeysList.append(PauseSimKeys.WHOLE_APP_RESTARTS_KEY)
            normSimYKeysList.append(PauseSimKeys.REQUEST_REPROCESSING_KEY)
            normSimYKeysList.append(PauseSimKeys.REGION_RESTARTS_KEY)

            # cycles/bytes
            normSimYKeysList.append(PauseSimKeys.RESTART_BW_CYCLE_COUNT_KEY)
            normSimYKeysList.append(PauseSimKeys.RESTART_ONCHIP_NETWORKMSG_SIZE_BYTES_KEY)

    def createExpProductsDir(self, str_productDir):
        if not os.path.exists(str_productDir):
            os.makedirs(str_productDir)

    def __createStackedProductsDir(self):
        """Make directory for stacked bar plots, and return a handle to the html container file.
        """
        stackedDir = self.options.getExpProductsDir() + Result.FILE_SEP + "stacked"
        if not os.path.exists(stackedDir):
            os.makedirs(stackedDir)
        stackedFile = open(stackedDir + Result.FILE_SEP + 'index.html', 'w+')
        stackedFile.write("""<!DOCTYPE HTML>\n<html>
                        <title>
                        Bar graphs with stacked representation
                        </title>
                        <body>""")
        return stackedFile

    def __createNormProductsDir(self, str_rootPath):
        """Make directory for absolute plots, and return a handle to the html container file.
        """
        self.normDir = str_rootPath + Result.FILE_SEP + "normalized"
        if not os.path.exists(self.normDir):
            os.makedirs(self.normDir)
        normFile = open(self.normDir + Result.FILE_SEP + 'index.html', 'w+')
        normFile.write("""<!DOCTYPE HTML>\n<html>
                        <title>
                        Bar graphs with normalized representation
                        </title>
                        <body>""")
        return normFile

    def __createAbsoluteProductsDir(self, str_rootPath):
        """Make directory for absolute plots, and return a handle to the html container file.
        """
        self.absDir = str_rootPath + Result.FILE_SEP + "absolute"
        if not os.path.exists(self.absDir):
            os.makedirs(self.absDir)
        absFile = open(self.absDir + Result.FILE_SEP + 'index.html', 'w+')
        absFile.write("""<!DOCTYPE HTML>\n<html>
                <title>
                Bar graphs with absolute representation
                </title>
                <body>""")
        return absFile

    def generateEnergyResult(self, resultsSet):
        self.__createSimStatsTable("energy_stats_table.html", resultsSet)
        str_productDir = self.options.getExpProductsDir()
        os.chdir(str_productDir)
        self.__generateStackedBars(resultsSet, self.stackedFile, StackedKeys.di_energyStackedKeys)

        self.stackedFile.write("\n</body>\n</html>")
        self.stackedFile.close()

    def generateResult(self, resultsSet):
        str_productDir = self.options.getExpProductsDir()
        self.createExpProductsDir(str_productDir)
        absFile = self.__createAbsoluteProductsDir(str_productDir)
        normFile = self.__createNormProductsDir(str_productDir)
        self.stackedFile = self.__createStackedProductsDir()

        os.chdir(str_productDir)
        self.options.createRerunFile()
        str_cmdLine = self.options.getExpCommand()

        # create an html container
        htm = HTMLProduct(self.options)
        htm.createHTMLFile(str_cmdLine)

        self.__createOutputTable()
        self.__createPintoolStatsTable(resultsSet)
        self.__createSimStatsTable("sim_stats_table.html", resultsSet)
        self.__generateGraphs(resultsSet, absFile, normFile)
        self.__generateStackedBars(resultsSet, self.stackedFile, StackedKeys.di_stackedKeys)

        absFile.write("\n</body>\n</html>")
        normFile.write("\n</body>\n</html>")

        absFile.close()
        normFile.close()

        if not self.options.generateEnergyStats:
            self.stackedFile.write("\n</body>\n</html>")
            self.stackedFile.close()

    def __generateStackedBars(self, resultsSet, stackedFile, di_stackedKeys):
        stackedDir = self.options.getExpProductsDir() + Result.FILE_SEP + "stacked"
        # We iterate in a deterministic order
        for key in di_stackedKeys:
            stackedGraph = StackedBarGraph(self.options, stackedDir, stackedFile, key, resultsSet,
                                           di_stackedKeys)
            stackedGraph.generateFile()
            stackedGraph.convertToEPS()
            stackedGraph.convertToPNG()
            str_htm = '\n<p><a href="' + key + '.png"> <img src=' + \
                key + '.png></a>\n<p><strong>' + \
                '</strong></p><br>'
            stackedFile.write(str_htm)

    def __generateGraphs(self, resultsSet, absFile, normFile):
        for key in self.absSimYKeysList:
            lrs = ResultSet.limitResultSetWithKey(resultsSet, key)
            absGraph = BarGraph(self.options, self.absDir, absFile, key, lrs, False)
            absGraph.generateFile()
            absGraph.convertToEPS()
            absGraph.convertToPNG()
            str_htm = '\n<p><a href="' + key + '.png"> <img src=' + \
                key + '.png></a>\n<p><strong>' + \
                '</strong></p><br>'
            absFile.write(str_htm)

        for key in self.normSimYKeysList:
            normGraph = BarGraph(self.options, self.normDir, normFile, key, lrs, True)
            normGraph.generateFile()
            normGraph.convertToEPS()
            normGraph.convertToPNG()
            str_htm = '\n<p><a href="' + key + '.png"> <img src=' + \
                key + '.png></a>\n<p><strong>' + \
                '</strong></p><br>'
            normFile.write(str_htm)

    def __createPintoolStatsTable(self, resultsSet):
        """Generate stats table by merging results over trials."""
        statsHtm = open("pintool_stats_table.html", "w")

        cwd = os.getcwd()
        os.chdir(self.options.getExpOutputDir())

        try:
            statsHtm.write("<!DOCTYPE HTML>\n<table border = 1>\n")

            # Generate first row
            statsHtm.write("<tr>\n<td></td>\n")
            for b in self.options.getBenchTuple():
                for w in self.options.getWorkloadTuple():
                    str_write = "<td>" + b + "<br>"
                    if len(self.options.getWorkloadTuple()) > 1:
                        str_write = str_write + "workload=" + w + "<br>"
                    statsHtm.write(str_write + "</td>\n")

            statsHtm.write("</tr>\n")

            # Generate data corresponding to each benchmark, on one row
            for key in self.pintoolStatsKeysList:
                statsHtm.write("<tr>\n<td>" + key)
                statsHtm.write("</td>\n")
                for b in self.options.getBenchTuple():
                    for w in self.options.getWorkloadTuple():
                        di_limit = {}
                        di_limit["bench"] = b
                        di_limit["workload"] = w
                        di_limit["tool"] = "pintool"
                        li_di_bench = ResultSet.limitResultSetWithDict(resultsSet, di_limit)
                        di_ms = merge.merge(li_di_bench, key)
                        statsHtm.write("<td>" + str(round(di_ms[key], Result.PRECISION_DIGITS)) +
                                       "</td>")
                statsHtm.write("</tr>")

        finally:
            statsHtm.write("</table>")
            statsHtm.close()
            os.chdir(cwd)

    def __createSimStatsTable(self, fileName, resultsSet):
        """Generate stats table by merging results over trials."""
        str_productDir = self.options.getExpProductsDir()
        os.chdir(str_productDir)
        statsHtm = open(fileName, "w")

        cwd = os.getcwd()
        os.chdir(self.options.getExpOutputDir())

        try:
            statsHtm.write("<!DOCTYPE HTML>\n<table border = 1>\n")

            # Generate the first row
            statsHtm.write("<tr>\n<td></td>\n")
            for b in self.options.getBenchTuple():
                for w in self.options.getWorkloadTuple():
                    for t in self.options.getSimulatorsTuple():
                        str_write = "<td>bench=" + b + "<br>"
                        if len(self.options.getWorkloadTuple()) > 1:
                            str_write = str_write + "workload=" + w + "<br>"
                        str_write = str_write + "tool=" + t
                        statsHtm.write(str_write + "</td>\n")

            statsHtm.write("</tr>\n")

            # Generate data corresponding to each benchmark, on one row
            if "energy" not in fileName:
                keysList = self.simStatsKeysList
            else:
                keysList = self.ESKeysList

            for key in keysList:
                statsHtm.write("<tr>\n<td>" + key)
                statsHtm.write("</td>\n")
                for b in self.options.getBenchTuple():
                    for w in self.options.getWorkloadTuple():
                        for t in self.options.getSimulatorsTuple():
                            di_limit = {}
                            di_limit["bench"] = b
                            di_limit["workload"] = w
                            di_limit["tool"] = t
                            li_di_bench = ResultSet.limitResultSetWithDict(resultsSet, di_limit)
                            if not li_di_bench:
                                util.raiseError(
                                    "Cannot find stats. Bench:" + b + " Workload:" + w + " Tool:" +
                                    t, " Key:" + key)
                            # Check if the key is not present in the
                            # dictionary, then create a dummy entry
                            for di_trial in li_di_bench:
                                if key not in di_trial:
                                    di_trial.update({key: 0})
                            di_ms = merge.merge(li_di_bench, key)
                            statsHtm.write(
                                "<td>" + str(round(di_ms[key], Result.PRECISION_DIGITS)) + "</td>")
                statsHtm.write("</tr>")
        finally:
            statsHtm.write("</table>")
            statsHtm.close()
            os.chdir(cwd)

    def __createOutputTable(self):
        """Generate success table."""
        outputDir = "../../exp-output/" + self.options.output
        outHtm = open("output_table.html", "w")
        outHtm.write("<!DOCTYPE HTML>\n<table border = 1>\n")

        workloadTuple = self.options.getWorkloadTuple()
        benchTuple = self.options.getBenchTuple()

        cwd = os.getcwd()
        os.chdir(self.options.getExpOutputDir())

        try:
            # Generate the first row
            outHtm.write("<tr>\n<td></td>\n")
            for num in range(1, self.options.trials + 1):
                for t in self.options.getToolsTuple():
                    outHtm.write("<td>trial=" + str(num) + "<br>tool=" + t + "</td>\n")
            outHtm.write("</tr>\n")

            # Generate data corresponding to each benchmark, on one row
            for b in tuple(benchTuple):
                for w in workloadTuple:
                    outHtm.write("<tr>\n<td>" + b)
                    if len(workloadTuple) > 1:
                        outHtm.write("<br>w")
                    outHtm.write("</td>\n")

                    for num in range(1, self.options.trials + 1):
                        path = outputDir + Result.FILE_SEP + RunTask.getPathPortion(b, w, num)
                        for t in self.options.getToolsTuple():
                            if t == "pintool":
                                _str_fileName = path + Result.FILE_SEP + t + "-stats.output"
                            else:
                                _str_fileName = path + Result.FILE_SEP + t + "-stats.py"

                            outHtm.write('<td><a href="')
                            outHtm.write(_str_fileName + '" target="_blank">')
                            outHtm.write("<font color=blue>OK</font></a></td>\n")
                outHtm.write("</tr>\n")
        finally:
            outHtm.write("</table>")
            outHtm.close()
            os.chdir(cwd)

    @staticmethod
    def getGlobalData(li_data):
        """This method assumes that the argument is a list."""
        li_tmp = []
        for trial_data in li_data:
            li_tmp.append(trial_data[-1])
        return li_tmp

    @staticmethod
    def getPerCoreData(li_data, core_num):
        """This method assumes that the argument is a list."""
        li_tmp = []
        for trial_data in li_data:
            li_tmp.append(trial_data[core_num])
        return li_tmp
