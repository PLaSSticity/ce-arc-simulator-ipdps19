import math
import os.path
import sys
from enum import Enum
from parser.backendsimulator import BackendSimulator
from parser.mcpat import Mcpat
from parser.pintool import Pintool

from options import merge, util
from options.constants import Constants
from result.resultset import ResultSet
from result.statskeys import EnergyStatsKeys as EK
from result.statskeys import MESISimKeys as MK
from result.statskeys import SimKeys as SK
from result.statskeys import ViserSimKeys as VK
from tasks.mcpattask import McPATTask
from tasks.runtask import RunTask


class SimulatorType(Enum):
    MESI = 1
    VISER = 2
    RCCSI = 3
    PAUSE = 4


class CollectTask(Constants):

    @staticmethod
    def __outputPrefix():
        return "[collect] "

    @staticmethod
    def __printTaskInfoStart(options):
        if options.verbose >= 1:
            print("\n" + CollectTask.__outputPrefix() + "Executing collect task...")

    @staticmethod
    def __printTaskInfoEnd(options):
        if options.verbose >= 1:
            print(CollectTask.__outputPrefix() + "Done executing collect task...\n")

    @staticmethod
    def collectTask(options):
        CollectTask.__printTaskInfoStart(options)

        cwd = os.getcwd()
        os.chdir(options.getExpOutputDir())
        resSet = []  # list of dictionaries

        try:
            workloadTuple = options.getWorkloadTuple()
            benchTuple = options.getBenchTuple()

            for w in workloadTuple:
                for num in range(1, options.trials + 1):
                    for b in tuple(benchTuple):
                        path = RunTask.getPathPortion(b, w, num)
                        if not os.path.exists(path):
                            util.raiseError("Output file path not present: ",
                                            options.getExpOutputDir() + CollectTask.FILE_SEP + path)

                        dic = {}
                        # Create key/value pairs and add to the dict
                        dic["bench"] = b
                        dic["trial"] = str(num)
                        dic["workload"] = w
                        for tool in options.getToolsTuple():
                            resSet = CollectTask.__collectResult(path, tool, dic, resSet)

        finally:
            os.chdir(cwd)
            CollectTask.__printTaskInfoEnd(options)
        return resSet

    @staticmethod
    def __collectResult(path, tool, dic, resultsSet):
        if util.isPintool(tool):
            pinDic = dic.copy()
            pinDic["tool"] = tool
            pinDic = CollectTask.__processPintoolOutput(path, tool, pinDic)
            resultsSet.append(pinDic)

        elif util.isSimulatorConfig(tool):
            simDic = dic.copy()
            simDic["tool"] = tool
            if util.isMESIConfig(tool) or util.isCEConfig(tool):
                configType = SimulatorType.MESI
            elif util.isViserConfig(tool):
                configType = SimulatorType.VISER
            elif util.isRCCSIConfig(tool):
                configType = SimulatorType.RCCSI
            elif util.isPauseConfig(tool):
                configType = SimulatorType.PAUSE
            simDic = CollectTask.__processSimOutput(path, tool, simDic, configType)
            resultsSet.append(simDic)

        return resultsSet

    @staticmethod
    def __processPintoolOutput(path, tool, di_stats):
        """Parse the given output file and populate and return di_stats."""
        _str_fileName = path + CollectTask.FILE_SEP + tool + "-stats.output"
        if not os.path.isfile(_str_fileName):
            util.raiseError("Pintool stats file not present: ", _str_fileName, stack=False)
        di_stats = Pintool.parseStats(_str_fileName, di_stats)
        return di_stats

    @staticmethod
    def __processSimOutput(path, tool, di_stats, simType):
        _str_fileName = path + CollectTask.FILE_SEP + tool + "-stats.py"
        if not os.path.isfile(_str_fileName):
            configType = ""
            if simType == SimulatorType.MESI:
                configType = "MESI"
            elif simType == SimulatorType.VISER:
                configType = "Viser"
            elif simType == SimulatorType.RCCSI:
                configType = "RCC-SI"
            elif simType == SimulatorType.PAUSE:
                configType = "Pause"
            util.raiseError(configType + " simulator stats file not present:", _str_fileName)
        di_stats = BackendSimulator.parseStats(_str_fileName, di_stats)

        # Compute on-chip and off-chip network bandwidth.
        globalStats = di_stats[BackendSimulator.GLOBAL_CPUID_VAL]
        numSeconds = globalStats[SK.BANDWIDTH_CYCLE_COUNT_KEY] / CollectTask.CLK_FREQUENCY
        numOnChipBytes = (
            globalStats[SK.ONCHIP_NETWORKMSG_SIZE_16BYTES_FLITS_KEY] * CollectTask.NUM_BYTES_FLIT)
        onChipBW = numOnChipBytes / (numSeconds * math.pow(2, 30))
        globalStats[SK.SUM_REQD_ONCHIPBW_16BYTES_FLITS_KEY] = onChipBW

        # Off-chip traffic is computed during postProcessResults. So bandwidth can only be
        # computed after that.

        # numOffChipBytes = (
        #     globalStats[SK.LLC_MEM_MSG_SIZE_16BYTES_FLITS_KEY] * CollectTask.NUM_BYTES_FLIT)
        # offChipBW = numOffChipBytes / (numSeconds * math.pow(2, 30))
        # globalStats[SK.SUM_REQD_OFFCHIPBW_64BYTES_FLITS_KEY] = offChipBW

        return di_stats

    @staticmethod
    def postProcessResults(options, resultSet):
        # The result set is a list of all experiments. It should be a product of
        # (#benchmarks x #trials x #configs).

        DEBUG = False

        # Replace the memory access computation for ARC configurations
        for exp in resultSet:
            if util.isPintool(exp["tool"]):
                continue

            global_data = exp[BackendSimulator.GLOBAL_CPUID_VAL]

            if util.isViserConfig(exp["tool"]):
                llc_misses = (
                    global_data[SK.L3_READ_MISSES_KEY] + global_data[SK.L3_WRITE_MISSES_KEY])
                aim_misses = (
                    global_data[VK.AIM_READ_MISSES_KEY] + global_data[VK.AIM_WRITE_MISSES_KEY])
                llc_evictions = global_data[SK.L3_LINE_EVICTIONS_KEY]
                llc_dirty_evictions = global_data[SK.L3_DIRTY_LINE_EVICTIONS_KEY]
                aim_evictions = global_data[VK.AIM_LINE_EVICTIONS_KEY]
                # Communication between the memory subsystem and controller is in 64-Bytes lines
                aim_64bytes_lines = math.ceil(
                    util.getARCAIMLineSize(exp["tool"]) / Constants.DATA_LINE_SIZE)
                mem_reads = llc_misses + aim_misses * aim_64bytes_lines
                mem_writes = llc_dirty_evictions + aim_evictions * aim_64bytes_lines
                if util.isViserIdealAIMConfig(exp["tool"]):
                    ideal_aim_64bytes_lines = math.ceil(
                        (util.getARCAIMLineSize(exp["tool"]) + Constants.DATA_LINE_SIZE) /
                        Constants.DATA_LINE_SIZE)
                    mem_reads = llc_misses * ideal_aim_64bytes_lines
                    # The data and AIM lines are together, so writes cannot distinguish between the
                    # two parts
                    # mem_writes = llc_dirty_evictions + llc_evictions * aim_64bytes_lines
                    mem_writes = llc_evictions * ideal_aim_64bytes_lines
                global_data[SK.MEM_64BYTES_READS_KEY] = mem_reads
                global_data[SK.MEM_64BYTES_WRITES_KEY] = mem_writes
                global_data[SK.MEM_64BYTES_ACCESSES_KEY] = mem_reads + mem_writes
                if DEBUG:
                    print("Config:", exp["tool"])
                    print("Benchmark:", exp["bench"])
                    print("AIM evictions:", aim_evictions)
                    print("AIM misses:", aim_misses)
                    print("LLC misses:", llc_misses)
                    print("LLC evictions:", llc_evictions)
                    print("LLC dirty evictions:", llc_dirty_evictions)
                    print("Mem accesses:", mem_reads + mem_writes)
                    print("Size of AIM line in 64 Bytes:", aim_64bytes_lines)
            elif util.isCEConfigWithAIM(exp["tool"]):
                llc_misses = (
                    global_data[SK.L3_READ_MISSES_KEY] + global_data[SK.L3_WRITE_MISSES_KEY])
                llc_evictions = global_data[SK.L3_LINE_EVICTIONS_KEY]
                llc_dirty_evictions = global_data[SK.L3_DIRTY_LINE_EVICTIONS_KEY]
                aim_misses = (
                    global_data[VK.AIM_READ_MISSES_KEY] + global_data[VK.AIM_WRITE_MISSES_KEY])
                aim_evictions = global_data[VK.AIM_LINE_EVICTIONS_KEY]
                aim_64bytes_lines = math.ceil(
                    util.getCEAIMLineSize(exp["tool"]) / Constants.DATA_LINE_SIZE)
                mem_reads = llc_misses + aim_misses * aim_64bytes_lines
                mem_writes = llc_dirty_evictions + aim_evictions * aim_64bytes_lines
                global_data[SK.MEM_64BYTES_READS_KEY] = mem_reads
                global_data[SK.MEM_64BYTES_WRITES_KEY] = mem_writes
                global_data[SK.MEM_64BYTES_ACCESSES_KEY] = mem_reads + mem_writes
                if DEBUG:
                    print("Config:", exp["tool"])
                    print("Benchmark:", exp["bench"])
                    print("AIM evictions:", aim_evictions)
                    print("AIM misses:", aim_misses)
                    print("LLC misses:", llc_misses)
                    print("LLC evictions:", llc_evictions)
                    print("LLC dirty evictions:", llc_dirty_evictions)
                    print("Mem accesses:", mem_reads + mem_writes)
                    print("Size of AIM line in 64 Bytes:", aim_64bytes_lines)
            elif util.isCEConfigWithoutAIM(exp["tool"]):
                llc_misses = (
                    global_data[SK.L3_READ_MISSES_KEY] + global_data[SK.L3_WRITE_MISSES_KEY])
                llc_evictions = global_data[SK.L3_LINE_EVICTIONS_KEY]
                llc_dirty_evictions = global_data[SK.L3_DIRTY_LINE_EVICTIONS_KEY]
                l2_evictions = global_data[SK.L2_LINE_EVICTIONS_KEY]
                l2_misses = global_data[SK.L2_READ_MISSES_KEY] + global_data[SK.L2_WRITE_MISSES_KEY]
                # CE only transmits read and write metadata per core but that only
                # impacts on-chip traffic. The off-chip traffic computation assumes the memory
                # controller granularity is 64 Bytes.
                ce_line_size = math.ceil(
                    (Constants.RD_MD_BYTES_PER_LINE + Constants.WR_MD_BYTES_PER_LINE) /
                    Constants.NUM_BYTES_MEM_FLIT)
                aim_64bytes_lines = math.ceil(
                    util.getCEAIMLineSize(exp["tool"]) / Constants.DATA_LINE_SIZE)
                mem_reads = llc_misses + l2_misses * aim_64bytes_lines
                mem_writes = llc_dirty_evictions + l2_evictions * aim_64bytes_lines
                global_data[SK.MEM_64BYTES_READS_KEY] = mem_reads
                global_data[SK.MEM_64BYTES_WRITES_KEY] = mem_writes
                global_data[SK.MEM_64BYTES_ACCESSES_KEY] = mem_reads + mem_writes
                if DEBUG:
                    print("Config:", exp["tool"])
                    print("Benchmark:", exp["bench"])
                    print("LLC misses:", llc_misses)
                    print("LLC evictions:", llc_evictions)
                    print("LLC dirty evictions:", llc_dirty_evictions)
                    print("L2 misses:", l2_misses)
                    print("L2 evictions:", l2_evictions)
                    print("Mem accesses:", mem_reads + mem_writes)
                    print("Size of CE line in 64 Bytes:", ce_line_size)
                    print("Size of AIM line in 64 Bytes:", aim_64bytes_lines)
            elif util.isMESIConfig(exp["tool"]):
                llc_misses = (
                    global_data[SK.L3_READ_MISSES_KEY] + global_data[SK.L3_WRITE_MISSES_KEY])
                llc_dirty_evictions = global_data[SK.L3_DIRTY_LINE_EVICTIONS_KEY]
                mem_reads = llc_misses
                mem_writes = llc_dirty_evictions
                global_data[SK.MEM_64BYTES_READS_KEY] = mem_reads
                global_data[SK.MEM_64BYTES_WRITES_KEY] = mem_writes
                global_data[SK.MEM_64BYTES_ACCESSES_KEY] = mem_reads + mem_writes
            else:
                util.raiseError("unknown config %s" % (exp["tool"]))

        # Now we have an estimate of the off-chip memory access
        for exp in resultSet:
            if util.isPintool(exp["tool"]):
                continue
            global_data = exp[BackendSimulator.GLOBAL_CPUID_VAL]
            numOffChipBytes = (
                global_data[SK.MEM_64BYTES_ACCESSES_KEY] * CollectTask.NUM_BYTES_MEM_FLIT)
            numSeconds = (global_data[SK.BANDWIDTH_CYCLE_COUNT_KEY] / CollectTask.CLK_FREQUENCY)
            offChipBW = numOffChipBytes / (numSeconds * math.pow(2, 30))
            global_data[SK.SUM_REQD_OFFCHIPBW_64BYTES_FLITS_KEY] = offChipBW

        # Fill in the max required bandwidth computation

        # Check whether any of the configs exceed the available bandwidth. If yes, then we round
        # off the bandwidth value and scale the execution cycles.
        for exp in resultSet:
            if not util.isPintool(exp["tool"]):
                globalStats = exp[BackendSimulator.GLOBAL_CPUID_VAL]
                offChipBW = globalStats[SK.SUM_REQD_OFFCHIPBW_64BYTES_FLITS_KEY]
                onChipBW = globalStats[SK.SUM_REQD_ONCHIPBW_16BYTES_FLITS_KEY]

                if DEBUG or (onChipBW > Constants.ONCHIP_BW) or (offChipBW > Constants.OFFCHIP_BW):
                    print("Benchmark:%s Tool: %s OnChipBW: %s OffChipBW: %s" %
                          (exp["bench"], exp["tool"], onChipBW, offChipBW))

                if onChipBW > Constants.ONCHIP_BW:
                    frac = (onChipBW / Constants.ONCHIP_BW)
                    numCycles = globalStats[SK.BANDWIDTH_CYCLE_COUNT_KEY]
                    newNumCycles = int(round(frac * numCycles))
                    if util.isViserConfig(exp["tool"]):
                        reg = globalStats[VK.REG_EXEC_BW_CYCLE_COUNT_KEY]
                        pre = globalStats[VK.PRE_COMMIT_BW_CYCLE_COUNT_KEY]
                        post = globalStats[VK.POST_COMMIT_BW_CYCLE_COUNT_KEY]
                        rv = globalStats[VK.READ_VALIDATION_BW_CYCLE_COUNT_KEY]
                        assert reg + pre + post + rv == numCycles
                        globalStats[VK.REG_EXEC_BW_CYCLE_COUNT_KEY] = int(round(reg * frac))
                        reg = globalStats[VK.REG_EXEC_BW_CYCLE_COUNT_KEY]
                        globalStats[VK.PRE_COMMIT_BW_CYCLE_COUNT_KEY] = int(round(pre * frac))
                        pre = globalStats[VK.PRE_COMMIT_BW_CYCLE_COUNT_KEY]
                        globalStats[VK.READ_VALIDATION_BW_CYCLE_COUNT_KEY] = int(round(rv * frac))
                        rv = globalStats[VK.READ_VALIDATION_BW_CYCLE_COUNT_KEY]
                        globalStats[VK.POST_COMMIT_BW_CYCLE_COUNT_KEY] = (
                            newNumCycles - reg - pre - rv)
                    else:
                        coh = globalStats[MK.COHERENCE_EXEC_CYCLE_COUNT_KEY]
                        ex = globalStats[MK.MEM_EXEC_CYCLE_COUNT_KEY]
                        assert coh + ex == numCycles
                        globalStats[MK.COHERENCE_EXEC_CYCLE_COUNT_KEY] = int(round(coh * frac))
                        coh = globalStats[MK.COHERENCE_EXEC_CYCLE_COUNT_KEY]
                        globalStats[MK.MEM_EXEC_CYCLE_COUNT_KEY] = (newNumCycles - coh)
                    print("Scaling cycles for [%s, %s] by %s because on-chip bandwidth exceeds "
                          "available limit" % (exp["bench"], exp["tool"], frac))
                    print("Old cycles: %s new scaled cycles: %s" % (numCycles, newNumCycles))
                    globalStats[SK.BANDWIDTH_CYCLE_COUNT_KEY] = newNumCycles
                    # globalStats[SK.SUM_REQD_ONCHIPBW_16BYTES_FLITS_KEY] = Constants.ONCHIP_BW

                if offChipBW > Constants.OFFCHIP_BW:
                    frac = (offChipBW / Constants.OFFCHIP_BW)
                    numCycles = globalStats[SK.BANDWIDTH_CYCLE_COUNT_KEY]
                    newNumCycles = int(round(numCycles * frac))
                    if util.isViserConfig(exp["tool"]):
                        reg = globalStats[VK.REG_EXEC_BW_CYCLE_COUNT_KEY]
                        pre = globalStats[VK.PRE_COMMIT_BW_CYCLE_COUNT_KEY]
                        post = globalStats[VK.POST_COMMIT_BW_CYCLE_COUNT_KEY]
                        rv = globalStats[VK.READ_VALIDATION_BW_CYCLE_COUNT_KEY]
                        try:
                            assert reg + pre + post + rv == numCycles
                        except AssertionError:
                            print("Reg: %s Pre: %s RV: %s Post: %s Sum: %s Total: %s" %
                                  (reg, pre, rv, post, reg + pre + rv + post, numCycles))
                            sys.exit()

                        globalStats[VK.REG_EXEC_BW_CYCLE_COUNT_KEY] = int(round(reg * frac))
                        reg = globalStats[VK.REG_EXEC_BW_CYCLE_COUNT_KEY]
                        globalStats[VK.PRE_COMMIT_BW_CYCLE_COUNT_KEY] = int(round(pre * frac))
                        pre = globalStats[VK.PRE_COMMIT_BW_CYCLE_COUNT_KEY]
                        globalStats[VK.READ_VALIDATION_BW_CYCLE_COUNT_KEY] = int(round(rv * frac))
                        rv = globalStats[VK.READ_VALIDATION_BW_CYCLE_COUNT_KEY]
                        globalStats[VK.POST_COMMIT_BW_CYCLE_COUNT_KEY] = (
                            newNumCycles - reg - pre - rv)
                        post = globalStats[VK.POST_COMMIT_BW_CYCLE_COUNT_KEY]
                    else:
                        coh = globalStats[MK.COHERENCE_EXEC_CYCLE_COUNT_KEY]
                        ex = globalStats[MK.MEM_EXEC_CYCLE_COUNT_KEY]
                        try:
                            assert coh + ex == numCycles
                        except AssertionError:
                            print("Coh: %s Ex: %s NumCycles: %s" % (coh, ex, numCycles))
                            sys.exit()

                        globalStats[MK.COHERENCE_EXEC_CYCLE_COUNT_KEY] = int(round(coh * frac))
                        coh = globalStats[MK.COHERENCE_EXEC_CYCLE_COUNT_KEY]
                        globalStats[MK.MEM_EXEC_CYCLE_COUNT_KEY] = (newNumCycles - coh)
                    print("Scaling cycles for [%s, %s] by %s because off-chip bandwidth exceeds "
                          "available limit" % (exp["bench"], exp["tool"], frac))
                    print("Old cycles: %s new scaled cycles: %s" % (numCycles, newNumCycles))
                    globalStats[SK.BANDWIDTH_CYCLE_COUNT_KEY] = newNumCycles
                    # globalStats[SK.SUM_REQD_OFFCHIPBW_64BYTES_FLITS_KEY] = Constants.OFFCHIP_BW

    @staticmethod
    def collectMcpatResults(options, resSet):
        cwd = os.getcwd()
        odir = (options.getExpProductsDir() + os.sep + McPATTask.McPAT_ROOT_DIR + os.sep +
                McPATTask.McPAT_OUTPUT_FILES)
        os.chdir(odir)
        energyStats = []  # list of dictionaries

        try:
            for w in options.getWorkloadTuple():
                for b in tuple(options.getBenchTuple()):
                    dic = {}
                    dic["bench"] = b
                    dic["workload"] = w
                    for t in options.getToolsTuple():
                        if util.isPintool(t):
                            continue
                        statsFile = b + '-' + t + '-' + w + '.mcpat'

                        if not os.path.exists(statsFile):
                            util.raiseError("[error] Mcpat output file not present: ", statsFile)

                        mergedDic = dic.copy()
                        mergedDic["tool"] = t
                        li_di_bench = ResultSet.limitResultSetWithDict(resSet, mergedDic)
                        merged_cycles = merge.merge(
                            li_di_bench, SK.BANDWIDTH_CYCLE_COUNT_KEY)[SK.BANDWIDTH_CYCLE_COUNT_KEY]

                        merged_bf_energy = 0.0
                        if not util.isOnlyCEConfigNoAIM(options.getToolsTuple()):
                            merged_bf_energy = merge.merge(
                                li_di_bench,
                                VK.BLOOM_FILTER_TOTAL_ENERGY)[VK.BLOOM_FILTER_TOTAL_ENERGY]

                        dynamic_aim_energy = 0
                        static_aim_energy = 0
                        simDic = {}
                        if util.isViserConfig(t) or util.isCEConfigWithAIM(t):
                            simDic = Mcpat.parseDetailedStats(statsFile, simDic)
                            if not CollectTask.ADD_AIM_McPAT:  # Estimate from the simulator
                                # dynamic_aim_energy = (merge.merge(
                                #     li_di_bench,
                                #     VK.AIM_DYNAMIC_TOTAL_ENERGY)[VK.AIM_DYNAMIC_TOTAL_ENERGY])
                                simDic[EK.AIM_STATIC_POWER] = 0
                                simDic[EK.AIM_DYNAMIC_POWER] = 0
                            else:
                                dynamic_aim_energy = (simDic[EK.AIM_DYNAMIC_POWER] * merged_cycles /
                                                      CollectTask.CLK_FREQUENCY)
                                static_aim_energy = (simDic[EK.AIM_STATIC_POWER] * merged_cycles /
                                                     CollectTask.CLK_FREQUENCY)
                        else:
                            simDic = Mcpat.parseTerseStats(statsFile, simDic)

                        simDic[EK.STATIC_ENERGY] = (
                            simDic[EK.STATIC_POWER] * merged_cycles / CollectTask.CLK_FREQUENCY)
                        simDic[EK.DYNAMIC_ENERGY] = (
                            simDic[EK.DYNAMIC_POWER] * merged_cycles / CollectTask.CLK_FREQUENCY)
                        simDic[EK.BLOOM_FILTER_ENERGY] = merged_bf_energy
                        simDic[EK.AIM_STATIC_ENERGY] = static_aim_energy
                        simDic[EK.AIM_DYNAMIC_ENERGY] = dynamic_aim_energy
                        # McPAT output already includes the AIM component
                        simDic[EK.TOTAL_ENERGY] = (
                            simDic[EK.STATIC_ENERGY] + simDic[EK.DYNAMIC_ENERGY] + merged_bf_energy)

                        # Union the two dictionaries
                        energyStats.append({**mergedDic, **simDic})

        finally:
            os.chdir(cwd)
        return energyStats
