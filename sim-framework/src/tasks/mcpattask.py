import math
import os
import subprocess
import time
import xml.etree.ElementTree as ET
from shutil import copyfile

from options import merge, util
from options.constants import Constants
from result.result import Result
from result.resultset import ResultSet
from result.statskeys import PerCoreStatsKeys, SimKeys, ViserSimKeys


def _isParam(tag):
    return tag == "param"


def _isStat(tag):
    return tag == "stat"


def _isComponent(tag):
    return tag == "component"


class McPATTask(Constants):
    """Generate energy stats from simulator stats by McPAT."""

    McPAT_HOME = os.getenv("MCPAT_ROOT")
    MCPAT_BIN = (McPAT_HOME + "/mcpat -infile ") if (McPAT_HOME is not None) else None

    VISER_McPAT_ARGS = (" -print_level 0 > "
                        if Constants.ADD_AIM_McPAT is False else " -print_level 2 > ")
    SIM_McPAT_ARGS = " -print_level 0 > "

    inFile = 'mcpat_template.xml'

    McPAT_ROOT_DIR = "mcpat"
    McPAT_INPUT_FILES = "input"
    McPAT_OUTPUT_FILES = "output"
    McPAT_TEMPLATES_DIR = Constants.VISER_EXP + os.sep + "mcpat_templates"
    McPAT_INP_SUFFIX = ".xml"

    INVALID_PLACEHOLDER = "xxx"
    VALID_PLACEHOLDER = "0"

    INCLUDE_CORE_EXEC = False

    PREFIX_COMP_CORE = "system.core"
    PREFIX_SYSTEM_L3 = "system.L3"
    PREFIX_SYSTEM_L2 = "system.L2"
    PREFIX_SYSTEM_NOC = "system.NoC"
    PREFIX_SYSTEM_MC = "system.mc"
    PREFIX_SYSTEM_L20 = "system.L20"
    PREFIX_SYSTEM_L2DIR = "system.L2Directory"

    TOTAL_CYCLES = "total_cycles"
    BUSY_CYCLES = "busy_cycles"
    READ_ACCESSES = "read_accesses"
    READ_MISSES = "read_misses"
    WRITE_ACCESSES = "write_accesses"
    WRITE_MISSES = "write_misses"
    MEM_ACCESSES = "memory_accesses"
    MEM_READS = "memory_reads"
    MEM_WRITES = "memory_writes"
    TOTAL_ACCESSES = "total_accesses"
    TOTAL_INSTRUCTIONS = "total_instructions"
    INT_INSTRUCTIONS = "int_instructions"
    COMMITTED_INSTRUCTIONS = "committed_instructions"
    COMMITTED_INT_INSTRUCTIONS = "committed_int_instructions"
    LOAD_INSTRUCTIONS = "load_instructions"
    STORE_INSTRUCTIONS = "store_instructions"

    # 'system': {
    #     'total_cycles': 'max_BandwidthDrivenCycleCount'
    # },
    # 'system.core0': {
    #     'total_cycles': 'pc_BandwidthDrivenCycleCount',
    # },
    # 'system.core0.dcache': {
    #     'read_misses': 'g_Data_L1ReadMisses',
    #     'write_misses': 'g_Data_L1WriteMisses',
    #     'read_accesses': 'g_TotalDataReads',
    #     'write_accesses': 'g_TotalDataWrites'
    # },
    # 'system.L20': {
    #     'read_accesses': 'g_Data_L1ReadMisses',
    #     'read_misses': 'g_Data_L2ReadMisses',
    #     'write_accesses': 'g_Data_L1WriteMisses',
    #     'write_misses': 'g_Data_L2WriteMisses'
    # },
    # 'system.L30': {
    #     'read_accesses': 'g_Data_L2ReadMisses',
    #     'read_misses': 'g_Data_L3ReadMisses',
    #     'write_accesses': 'g_Data_L2WriteMisses',
    #     'write_misses': 'g_Data_L3WriteMisses',
    # },
    # 'system.mc': {
    #     'memory_accesses':
    #     'g_Data_L3ReadMisses' + 'g_Data_L3WriteMisses' + 'g_AIMCacheReadMisses' +
    # 'g_AIMCacheWriteMisses',
    #     'memory_reads':
    #     'g_Data_L3ReadMisses' + 'g_AIMCacheReadMisses',
    #     'memory_writes':
    #     'g_Data_L3WriteMisses' + 'g_AIMCacheWriteMisses'
    # },
    # 'system.NoC0': {
    #     'total_accesses': 6 * 'g_OnChipNetworkMessageSize16BytesFlits'
    # }

    statsKeyDic = {
        'system': {
            'total_cycles': 'max_BandwidthDrivenCycleCount',
            'busy_cycles': 'max_BandwidthDrivenCycleCount'
        },
        'system.core0': {
            'total_instructions': 'Instructions',
            'int_instructions': 'Instructions',
            'committed_instructions': 'Instructions',
            'committed_int_instructions': 'Instructions',
            'load_instructions': 'g_TotalDataReads',
            'store_instructions': 'g_TotalDataWrites',
            'total_cycles': 'max_BandwidthDrivenCycleCount',
            'busy_cycles': 'max_BandwidthDrivenCycleCount'
        },
        'system.core0.dcache': {
            'read_misses': 'g_Data_L1ReadMisses',
            'write_misses': 'g_Data_L1WriteMisses',
            'read_accesses': 'g_TotalDataReads',
            'write_accesses': 'g_TotalDataWrites'
        },
        'system.L20': {
            'read_misses': 'g_Data_L2ReadMisses',
            'write_misses': 'g_Data_L2WriteMisses',
            'read_accesses': 'g_Data_L1ReadMisses',
            'write_accesses': 'g_Data_L1WriteMisses'
        },
        'system.L30': {
            'read_misses': 'g_Data_L3ReadMisses',
            'write_misses': 'g_Data_L3WriteMisses',
            'read_accesses': 'g_Data_L2ReadMisses',
            'write_accesses': 'g_Data_L2WriteMisses'
        },
        'system.mc': {
            # the following is correctly computed with g_Data_L3ReadMisses + g_Data_L3WriteMisses
            'memory_accesses': 'g_Data_L3ReadMisses',
            'memory_reads': 'g_Data_L3ReadMisses',
            'memory_writes': 'g_Data_L3WriteMisses'
        },
        'system.NoC0': {
            # the following is correctly computed with g_OnChipNetworkMessageSize16BytesFlits * 6
            'total_accesses': 'g_OnChipNetworkMessageSize16BytesFlits'
        }
    }

    def __init__(self, options):
        self.options = options
        # Create mpcat input and output directories
        self.mcpat_product = options.getExpProductsDir() + os.sep + McPATTask.McPAT_ROOT_DIR
        if not os.path.exists(self.mcpat_product):
            os.makedirs(self.mcpat_product)
        self.mcpat_input = self.mcpat_product + os.sep + McPATTask.McPAT_INPUT_FILES
        if not os.path.exists(self.mcpat_input):
            os.makedirs(self.mcpat_input)
        self.mcpat_output = self.mcpat_product + os.sep + McPATTask.McPAT_OUTPUT_FILES
        if not os.path.exists(self.mcpat_output):
            os.makedirs(self.mcpat_output)

    def parseXmlNoCore(self, resultsSet):
        cwd = os.getcwd()
        try:
            os.chdir(self.mcpat_input)

            for b in self.options.getBenchTuple():
                for w in self.options.getWorkloadTuple():
                    for t in self.options.getSimulatorsTuple():
                        if not util.isSimulatorConfig(t):
                            continue
                        suffix = w
                        if "viser4" in t or "mesi4" in t or "ce4" in t:
                            num_cores = 4
                        elif "viser8" in t or "mesi8" in t or "ce8" in t:
                            num_cores = 8
                        elif "viser16" in t or "mesi16" in t or "ce16" in t:
                            num_cores = 16
                        elif "viser32" in t or "mesi32" in t or "ce32" in t:
                            num_cores = 32
                        else:
                            util.raiseError("possibly wrong configuration!")
                        suffix = suffix + os.sep + str(
                            num_cores) + os.sep + b + McPATTask.McPAT_INP_SUFFIX

                        needsMetadata = False
                        if util.isViserConfig(t) or util.isCEConfig(t):
                            needsMetadata = True

                        # Copy the required input file template
                        srcpath = (McPATTask.McPAT_TEMPLATES_DIR + os.sep + "arc" + os.sep +
                                   "arc-" + str(num_cores) + ".xml")
                        if util.isCEConfigWithAIM(t):
                            srcpath = McPATTask.McPAT_TEMPLATES_DIR + os.sep + "ce-aim-" + str(
                                num_cores) + ".xml"
                        elif util.isMESIConfig(t) or util.isCEConfig(t):
                            srcpath = McPATTask.McPAT_TEMPLATES_DIR + os.sep + "mesi-" + str(
                                num_cores) + ".xml"
                        # print("Source file: %s" % (srcpath))
                        destpath = (self.mcpat_input + os.sep + b + "-" + t + "-" + w +
                                    McPATTask.McPAT_INP_SUFFIX)
                        copyfile(srcpath, destpath)

                        di_limit = {}
                        di_limit["bench"] = b
                        di_limit["workload"] = w
                        di_limit["tool"] = t
                        li_di_bench = ResultSet.limitResultSetWithDict(resultsSet, di_limit)

                        # Open destination file for editing
                        xml_tree = ET.parse(destpath)
                        root = xml_tree.getroot()
                        self.transform_system_no_core(root[0], num_cores, li_di_bench,
                                                      needsMetadata, util.isViserConfig(t),
                                                      util.isCEConfigWithAIM(t))

                        if McPATTask.ADD_AIM_McPAT and (util.isViserConfig(t) or
                                                        util.isCEConfigWithAIM(t)):
                            self.addAIMComponent(root[0], li_di_bench, num_cores, t,
                                                 util.isViserConfig(t))

                        xml_tree.write(destpath)
        finally:
            os.chdir(cwd)

    def parseXml(self, resultSet):
        if McPATTask.INCLUDE_CORE_EXEC:
            self.parseXmlCore(resultSet)
        else:
            self.parseXmlNoCore(resultSet)

    def parseXmlCore(self, resultsSet):
        cwd = os.getcwd()
        try:
            os.chdir(self.mcpat_input)

            for b in self.options.getBenchTuple():
                for w in self.options.getWorkloadTuple():
                    for t in self.options.getSimulatorsTuple():
                        if not util.isSimulatorConfig(t):
                            continue
                        suffix = w
                        if "viser4" in t or "mesi4" in t or "ce4" in t:
                            num_cores = 4
                        elif "viser8" in t or "mesi8" in t or "ce8" in t:
                            num_cores = 8
                        elif "viser16" in t or "mesi16" in t or "ce16" in t:
                            num_cores = 16
                        elif "viser32" in t or "mesi32" in t or "ce32" in t:
                            num_cores = 32
                        else:
                            util.raiseError("possibly wrong configuration!")
                        suffix = suffix + os.sep + str(
                            num_cores) + os.sep + b + McPATTask.McPAT_INP_SUFFIX

                        needsMetadata = False
                        if util.isViserConfig(t) or util.isCEConfig(t):
                            needsMetadata = True

                        # Copy the required input file template
                        assert False  # XXX: Should we use same templates for MESI/CE?
                        srcpath = McPATTask.McPAT_TEMPLATES_DIR + os.sep + suffix
                        destpath = (self.mcpat_input + os.sep + b + "-" + t + "-" + w +
                                    McPATTask.McPAT_INP_SUFFIX)
                        copyfile(srcpath, destpath)

                        di_limit = {}
                        di_limit["bench"] = b
                        di_limit["workload"] = w
                        di_limit["tool"] = t
                        li_di_bench = ResultSet.limitResultSetWithDict(resultsSet, di_limit)

                        # Open destination file for editing
                        xml_tree = ET.parse(destpath)
                        root = xml_tree.getroot()
                        self.transform_system(root[0], num_cores, li_di_bench, needsMetadata,
                                              util.isViserConfig(t))

                        if McPATTask.ADD_AIM_McPAT and (util.isViserConfig(t) or
                                                        util.isCEConfigWithAIM(t)):
                            self.addAIMComponent(root[0], li_di_bench, num_cores, t,
                                                 util.isViserConfig(t))

                        xml_tree.write(destpath)
        finally:
            os.chdir(cwd)

    def transform_L3(self, l3, li_data, num_cores):
        globalData = Result.getGlobalData(li_data)
        for child in l3:
            # print("Child:%s %s" % (child.tag, child.attrib))
            if _isParam(child.tag):
                if child.attrib["name"] == "L3_config":
                    vals = child.attrib["value"].split(",")
                    # latency = int(vals[5])
                    if num_cores == 4:
                        new_latency = McPATTask.LLC_4_LATENCY
                    elif num_cores == 8:
                        new_latency = McPATTask.LLC_8_LATENCY
                    elif num_cores == 16:
                        new_latency = McPATTask.LLC_16_LATENCY
                    elif num_cores == 32:
                        new_latency = McPATTask.LLC_32_LATENCY
                    vals[5] = str(new_latency)
                    child.attrib["value"] = ",".join(vals)
            elif _isStat(child.tag):
                key_name = child.attrib["name"]
                if key_name == McPATTask.READ_ACCESSES:
                    assert child.attrib["value"] == McPATTask.INVALID_PLACEHOLDER
                    key = SimKeys.L2_READ_MISSES_KEY
                    di_ms = merge.merge(globalData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))
                elif key_name == McPATTask.READ_MISSES:
                    assert child.attrib["value"] == McPATTask.INVALID_PLACEHOLDER
                    key = SimKeys.L3_READ_MISSES_KEY
                    di_ms = merge.merge(globalData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))
                elif key_name == McPATTask.WRITE_ACCESSES:
                    assert child.attrib["value"] == McPATTask.INVALID_PLACEHOLDER
                    key = SimKeys.L2_WRITE_MISSES_KEY
                    di_ms = merge.merge(globalData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))
                elif key_name == McPATTask.WRITE_MISSES:
                    assert child.attrib["value"] == McPATTask.INVALID_PLACEHOLDER
                    key = SimKeys.L3_WRITE_MISSES_KEY
                    di_ms = merge.merge(globalData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))

    def addAIMComponent(self, system, li_data, num_cores, tool, isViser):
        """Add the AIM component in place, otherwise McPAT might complain."""
        globalData = Result.getGlobalData(li_data)

        child = None
        counter = 0
        for child in system:
            counter += 1
            if _isComponent(child.tag) and McPATTask.PREFIX_SYSTEM_L3 in child.attrib["id"]:
                break

        new_l3 = ET.Element("component")
        new_l3.attrib["id"] = "system.L31"
        new_l3.attrib["name"] = "L31"
        param1 = ET.SubElement(new_l3, "param")
        param1.attrib["name"] = "L3_config"

        # IMP: These are hard coded constants about the AIM. Make sure these are in sync.
        assc = 4
        banking = 8
        throughput = 16
        cache_policy = 1
        aimSize = 32 * 1024
        output_width = 64
        if "8Kaim" in tool:
            aimSize = 8 * 1024
        elif "16Kaim" in tool:
            aimSize = 16 * 1024
        elif "64Kaim" in tool:
            aimSize = 64 * 1024
        elif util.isViserIdealAIMConfig(tool):
            if num_cores == 4:
                aimSize = McPATTask.LLC_4_LINES
            elif num_cores == 8:
                aimSize = McPATTask.LLC_8_LINES
            elif num_cores == 16:
                aimSize = McPATTask.LLC_16_LINES
            elif num_cores == 32:
                aimSize = McPATTask.LLC_32_LINES

        if num_cores == 4:
            ls = 60  # Bytes
            if not isViser:
                ls = 56
            la = 4  # cycles
        elif num_cores == 8:
            ls = 100  # Bytes
            if not isViser:
                ls = 96
            la = 6  # cycles, estimated from Cacti 7
        elif num_cores == 16:
            ls = 172
            if not isViser:
                ls = 168
            la = 8
        elif num_cores == 32:
            ls = 308
            if not isViser:
                ls = 304
            la = 10
        else:
            util.raiseError("unhandled core count in AIM component for tool %s!" % (tool))
        cs = aimSize * ls
        params = [cs, ls, assc, banking, throughput, la, output_width, cache_policy]
        param1.attrib["value"] = ",".join(str(p) for p in params)

        param2 = ET.SubElement(new_l3, "param")
        param2.attrib["name"] = "clockrate"
        param2.attrib["value"] = "1600"

        param3 = ET.SubElement(new_l3, "param")
        param3.attrib["name"] = "vdd"
        param3.attrib["value"] = "0"

        param4 = ET.SubElement(new_l3, "param")
        param4.attrib["name"] = "ports"
        param4.attrib["value"] = "1,1,1"

        param5 = ET.SubElement(new_l3, "param")
        param5.attrib["name"] = "device_type"
        param5.attrib["value"] = "2"

        param6 = ET.SubElement(new_l3, "param")
        param6.attrib["name"] = "buffer_sizes"
        param6.attrib["value"] = "16, 16, 16, 16"

        read_hits_key = ViserSimKeys.AIM_READ_HITS_KEY
        read_misses_key = ViserSimKeys.AIM_READ_MISSES_KEY
        write_hits_key = ViserSimKeys.AIM_WRITE_HITS_KEY
        write_misses_key = ViserSimKeys.AIM_WRITE_MISSES_KEY
        if util.isViserIdealAIMConfig(tool):
            read_hits_key = SimKeys.L3_READ_HITS_KEY
            read_misses_key = SimKeys.L3_READ_MISSES_KEY
            write_hits_key = SimKeys.L3_WRITE_HITS_KEY
            write_misses_key = SimKeys.L3_WRITE_MISSES_KEY

        read_hits = merge.merge(globalData, read_hits_key)
        read_misses = merge.merge(globalData, read_misses_key)
        write_hits = merge.merge(globalData, write_hits_key)
        write_misses = merge.merge(globalData, write_misses_key)

        stat1 = ET.SubElement(new_l3, "stat")
        stat1.attrib["name"] = "read_accesses"
        stat1.attrib["value"] = str(
            math.ceil(read_hits[read_hits_key] + read_misses[read_misses_key]))

        stat2 = ET.SubElement(new_l3, "stat")
        stat2.attrib["name"] = "write_accesses"
        stat2.attrib["value"] = str(
            math.ceil(write_hits[write_hits_key] + write_misses[write_misses_key]))

        stat3 = ET.SubElement(new_l3, "stat")
        stat3.attrib["name"] = "read_misses"
        stat3.attrib["value"] = str(math.ceil(read_misses[read_misses_key]))

        stat4 = ET.SubElement(new_l3, "stat")
        stat4.attrib["name"] = "write_misses"
        stat4.attrib["value"] = str(math.ceil(write_misses[write_misses_key]))

        stat5 = ET.SubElement(new_l3, "stat")
        stat5.attrib["name"] = "conflicts"
        stat5.attrib["value"] = "0"

        stat6 = ET.SubElement(new_l3, "stat")
        stat6.attrib["name"] = "duty_cycle"
        stat6.attrib["value"] = "0.018793"

        # ET.dump(new_child)
        system.insert(counter, new_l3)

    def transform_system_no_core(self, system, num_cores, li_data, needsMD, viserConfig,
                                 ceAIMConfig):
        globalData = Result.getGlobalData(li_data)
        for child in system:
            # print("Child:%s %s" % (child.tag, child.attrib))
            if _isParam(child.tag):
                key_name = child.attrib["name"]
                if key_name == "number_of_L1Directories":
                    child.attrib["value"] = str(0)
                elif key_name == "number_of_L2Directories":
                    if viserConfig:
                        child.attrib["value"] = str(0)
                    else:
                        child.attrib["value"] = str(1)
                elif key_name == "number_of_L3s":
                    assert int(child.attrib["value"]) == 1
                    if viserConfig or ceAIMConfig:
                        child.attrib["value"] = str(2)
            if _isStat(child.tag):
                key_name = child.attrib["name"]
                if key_name == McPATTask.TOTAL_CYCLES or key_name == McPATTask.BUSY_CYCLES:
                    # print("Key name:%s, key value:%s" % (key_name, child.attrib["value"]))
                    assert child.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                    key = SimKeys.BANDWIDTH_CYCLE_COUNT_KEY
                    di_ms = merge.merge(globalData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))

            elif _isComponent(child.tag):
                key_id = child.attrib["id"]
                key_name = child.attrib["name"]
                # print("Key id:%s, key name:%s" % (key_id, key_name))
                if McPATTask.PREFIX_COMP_CORE in key_id:
                    self.transform_cores_no_core(child, li_data, needsMD, viserConfig)
                elif McPATTask.PREFIX_SYSTEM_L20 in key_id:
                    self.transform_L2s_no_core(child, li_data, needsMD, viserConfig)
                elif McPATTask.PREFIX_SYSTEM_L3 in key_id:
                    self.transform_L3_no_core(child, li_data, num_cores)
                elif McPATTask.PREFIX_SYSTEM_NOC in key_id:
                    self.transform_nocs_no_core(child, li_data)
                elif McPATTask.PREFIX_SYSTEM_MC in key_id:
                    self.transform_mcs_no_core(child, li_data)
                elif McPATTask.PREFIX_SYSTEM_L2DIR in key_id and not viserConfig:
                    self.transform_L2_dir_no_core(child, li_data, num_cores)

    def transform_nocs_no_core(self, noc, li_data):
        globalData = Result.getGlobalData(li_data)
        for child in noc:
            if _isStat(child.tag):
                key_name = child.attrib["name"]
                if key_name == McPATTask.TOTAL_ACCESSES:
                    assert child.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                    key = SimKeys.ONCHIP_NETWORKMSG_SIZE_16BYTES_FLITS_KEY
                    di_ms = merge.merge(globalData, key)
                    # LATER: Should we add the memory accesses since the memory controller is
                    # connected to the NoC?
                    # mem_accesses = merge.merge(globalData, SimKeys.MEM_64BYTES_ACCESSES_KEY)
                    child.attrib["value"] = str(math.ceil(di_ms[key] * 6))

    # We do not do the manipulations here since the memory keys may be used elsewhere as in NoC
    # access estimation.
    def transform_mcs_no_core(self, mc, li_data):
        globalData = Result.getGlobalData(li_data)
        for child in mc:
            if _isStat(child.tag):
                key_name = child.attrib["name"]
                # print("Child:%s %s" % (key_name, child.attrib["value"]))
                if key_name == McPATTask.MEM_ACCESSES:
                    assert child.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                    # read_key = SimKeys.L3_READ_MISSES_KEY
                    # reads = merge.merge(globalData, read_key)
                    # write_key = SimKeys.L3_WRITE_MISSES_KEY
                    # writes = merge.merge(globalData, write_key)
                    # aim_read_key = ViserSimKeys.AIM_READ_MISSES_KEY
                    # aim_reads = merge.merge(globalData, aim_read_key)
                    # aim_write_key = ViserSimKeys.AIM_WRITE_MISSES_KEY
                    # aim_writes = merge.merge(globalData, aim_write_key)
                    # child.attrib["value"] = str(
                    #     math.ceil(reads[read_key] + writes[write_key] + aim_reads[aim_read_key] +
                    #               aim_writes[aim_write_key]))
                    mem_accesses_key = SimKeys.MEM_64BYTES_ACCESSES_KEY
                    mem_accesses = merge.merge(globalData, mem_accesses_key)
                    child.attrib["value"] = str(math.ceil(mem_accesses[mem_accesses_key]))
                elif key_name == McPATTask.MEM_READS:
                    assert child.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                    # read_key = SimKeys.L3_READ_MISSES_KEY
                    # reads = merge.merge(globalData, read_key)
                    # aim_read_key = ViserSimKeys.AIM_READ_MISSES_KEY
                    # aim_reads = merge.merge(globalData, aim_read_key)
                    # child.attrib["value"] = str(
                    #     math.ceil(reads[read_key] + aim_reads[aim_read_key]))
                    mem_reads_key = SimKeys.MEM_64BYTES_READS_KEY
                    mem_reads = merge.merge(globalData, mem_reads_key)
                    child.attrib["value"] = str(math.ceil(mem_reads[mem_reads_key]))
                elif key_name == McPATTask.MEM_WRITES:
                    assert child.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                    # write_key = SimKeys.L3_WRITE_MISSES_KEY
                    # writes = merge.merge(globalData, write_key)
                    # aim_write_key = ViserSimKeys.AIM_WRITE_MISSES_KEY
                    # aim_writes = merge.merge(globalData, aim_write_key)
                    # child.attrib["value"] = str(
                    #     math.ceil(writes[write_key] + aim_writes[aim_write_key]))
                    mem_writes_key = SimKeys.MEM_64BYTES_WRITES_KEY
                    mem_writes = merge.merge(globalData, mem_writes_key)
                    child.attrib["value"] = str(math.ceil(mem_writes[mem_writes_key]))

    def transform_L3_no_core(self, l3, li_data, num_cores):
        globalData = Result.getGlobalData(li_data)
        for child in l3:
            # print("Child:%s %s" % (child.tag, child.attrib))
            if _isParam(child.tag):
                if child.attrib["name"] == "L3_config":
                    vals = child.attrib["value"].split(",")
                    # latency = int(vals[5])
                    if num_cores == 4:
                        new_latency = McPATTask.LLC_4_LATENCY
                    elif num_cores == 8:
                        new_latency = McPATTask.LLC_8_LATENCY
                    elif num_cores == 16:
                        new_latency = McPATTask.LLC_16_LATENCY
                    elif num_cores == 32:
                        new_latency = McPATTask.LLC_32_LATENCY
                    vals[5] = str(new_latency)
                    child.attrib["value"] = ",".join(vals)
            elif _isStat(child.tag):
                key_name = child.attrib["name"]
                if key_name == McPATTask.READ_ACCESSES:
                    assert child.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                    key = SimKeys.L2_READ_MISSES_KEY
                    di_ms = merge.merge(globalData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))
                elif key_name == McPATTask.READ_MISSES:
                    assert child.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                    key = SimKeys.L3_READ_MISSES_KEY
                    di_ms = merge.merge(globalData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))
                elif key_name == McPATTask.WRITE_ACCESSES:
                    assert child.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                    key = SimKeys.L2_WRITE_MISSES_KEY
                    di_ms = merge.merge(globalData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))
                elif key_name == McPATTask.WRITE_MISSES:
                    assert child.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                    key = SimKeys.L3_WRITE_MISSES_KEY
                    di_ms = merge.merge(globalData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))

    def transform_L2s_no_core(self, l2, li_data, needsMD, viserConfig):
        # Find L2 id
        core_no = l2.attrib["name"][2:]
        assert int(core_no) == 0
        globalData = Result.getGlobalData(li_data)

        for child in l2:
            # print("Child:%s %s" % (child.tag, child.attrib))
            if _isParam(child.tag):
                if needsMD and child.attrib["name"] == "L2_config":
                    vals = child.attrib["value"].split(",")
                    cache_size = float(vals[0])
                    line_size = float(vals[1])
                    num_lines = cache_size / line_size
                    new_line_size = (line_size + McPATTask.RD_MD_BYTES_PER_LINE +
                                     McPATTask.WR_MD_BYTES_PER_LINE)
                    if viserConfig:
                        new_line_size += McPATTask.ARC_VERSION_SIZE
                    new_cache_size = num_lines * new_line_size
                    vals[0] = str(new_cache_size)
                    vals[1] = str(new_line_size)
                    child.attrib["value"] = ",".join(vals)
            elif _isStat(child.tag):
                stat_key_name = child.attrib["name"]
                if stat_key_name == McPATTask.READ_ACCESSES:
                    assert child.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                    key = SimKeys.L1_READ_MISSES_KEY
                    di_ms = merge.merge(globalData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))
                elif stat_key_name == McPATTask.READ_MISSES:
                    assert child.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                    key = SimKeys.L2_READ_MISSES_KEY
                    di_ms = merge.merge(globalData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))
                elif stat_key_name == McPATTask.WRITE_ACCESSES:
                    assert child.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                    key = SimKeys.L1_WRITE_MISSES_KEY
                    di_ms = merge.merge(globalData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))
                elif stat_key_name == McPATTask.WRITE_MISSES:
                    assert child.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                    key = SimKeys.L2_WRITE_MISSES_KEY
                    di_ms = merge.merge(globalData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))

    def transform_L2_dir_no_core(self, l2dir, li_data, num_cores):
        dir_name = l2dir.attrib["name"]
        assert dir_name.find("L2Directory") == 0
        dir_no = dir_name[len("L2Directory"):]
        assert int(dir_no) == 0

        globalData = Result.getGlobalData(li_data)

        for child in l2dir:
            # print(child.attrib["name"])
            if _isParam(child.tag):
                if child.attrib["name"] == "Dir_config":
                    banking = 8
                    throughput = 2
                    # Compute the directory line size in bytes
                    dir_line_size = math.ceil(
                        (McPATTask.DIR_LINE_SIZE + num_cores + math.log(num_cores, 2)) / 8)
                    if num_cores == 4:
                        cap = McPATTask.LLC_4_LINES * dir_line_size
                        params = [
                            cap, dir_line_size, McPATTask.LLC_4_ASSOC, banking, throughput,
                            McPATTask.LLC_4_LATENCY
                        ]
                    elif num_cores == 8:
                        cap = McPATTask.LLC_8_LINES * dir_line_size
                        params = [
                            cap, dir_line_size, McPATTask.LLC_8_ASSOC, banking, throughput,
                            McPATTask.LLC_8_LATENCY
                        ]
                    elif num_cores == 16:
                        cap = McPATTask.LLC_16_LINES * dir_line_size
                        params = [
                            cap, dir_line_size, McPATTask.LLC_16_ASSOC, banking, throughput,
                            McPATTask.LLC_16_LATENCY
                        ]
                    elif num_cores == 32:
                        cap = McPATTask.LLC_32_LINES * dir_line_size
                        params = [
                            cap, dir_line_size, McPATTask.LLC_32_ASSOC, banking, throughput,
                            McPATTask.LLC_32_LATENCY
                        ]
                    child.attrib["value"] = ",".join(str(p) for p in params)
            if _isStat(child.tag):
                l3_read_misses_key = SimKeys.L3_READ_MISSES_KEY
                read_misses = merge.merge(globalData, l3_read_misses_key)
                l3_read_hits_key = SimKeys.L3_READ_HITS_KEY
                read_hits = merge.merge(globalData, l3_read_hits_key)
                l3_write_hits_key = SimKeys.L3_WRITE_HITS_KEY
                write_hits = merge.merge(globalData, l3_write_hits_key)
                l3_write_misses_key = SimKeys.L3_WRITE_MISSES_KEY
                write_misses = merge.merge(globalData, l3_write_misses_key)
                if child.attrib["name"] == McPATTask.READ_ACCESSES:
                    child.attrib["value"] = str(
                        math.ceil(read_hits[l3_read_hits_key] + read_misses[l3_read_misses_key]))
                elif child.attrib["name"] == McPATTask.READ_MISSES:
                    child.attrib["value"] = str(math.ceil(read_misses[l3_read_misses_key]))
                elif child.attrib["name"] == McPATTask.WRITE_ACCESSES:
                    child.attrib["value"] = str(
                        math.ceil(write_hits[l3_write_hits_key] +
                                  write_misses[l3_write_misses_key]))
                elif child.attrib["name"] == McPATTask.WRITE_MISSES:
                    child.attrib["value"] = str(math.ceil(write_misses[l3_write_misses_key]))

    def transform_cores_no_core(self, core, li_data, needsMD, viserConfig):
        # Need to do the following transformations for each core

        # Find core id
        core_no = core.attrib["name"][4:]
        assert int(core_no) == 0
        globalData = Result.getGlobalData(li_data)

        for child in core:
            if _isStat(child.tag):
                key_name = child.attrib["name"]
                if (key_name == McPATTask.TOTAL_CYCLES or key_name == McPATTask.BUSY_CYCLES):
                    assert child.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                    key = SimKeys.BANDWIDTH_CYCLE_COUNT_KEY
                    di_ms = merge.merge(globalData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))
                elif (key_name == McPATTask.TOTAL_INSTRUCTIONS or
                      key_name == McPATTask.INT_INSTRUCTIONS or
                      key_name == McPATTask.COMMITTED_INSTRUCTIONS or
                      key_name == McPATTask.COMMITTED_INT_INSTRUCTIONS):
                    assert child.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                    key = SimKeys.INSTRUCTIONS_KEY
                    di_ms = merge.merge(globalData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))
                elif key_name == McPATTask.LOAD_INSTRUCTIONS:
                    assert child.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                    key = SimKeys.TOTAL_READS_KEY
                    di_ms = merge.merge(globalData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))
                elif key_name == McPATTask.STORE_INSTRUCTIONS:
                    assert child.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                    key = SimKeys.TOTAL_WRITES_KEY
                    di_ms = merge.merge(globalData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))

            elif _isComponent(child.tag):
                key_id = child.attrib["id"]
                assert McPATTask.PREFIX_COMP_CORE in key_id
                key_name = child.attrib["name"]
                if key_name == "dcache":
                    for stat in child:
                        stat_key_name = stat.attrib["name"]
                        if needsMD and stat_key_name == "dcache_config":
                            vals = stat.attrib["value"].split(",")
                            cache_size = float(vals[0])
                            line_size = float(vals[1])
                            num_lines = cache_size / line_size
                            new_line_size = (line_size + McPATTask.RD_MD_BYTES_PER_LINE +
                                             McPATTask.WR_MD_BYTES_PER_LINE)
                            if viserConfig:
                                new_line_size += McPATTask.ARC_VERSION_SIZE
                            new_cache_size = num_lines * new_line_size
                            vals[0] = str(new_cache_size)
                            vals[1] = str(new_line_size)
                            stat.attrib["value"] = ",".join(vals)
                        if stat_key_name == McPATTask.READ_ACCESSES:
                            assert stat.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                            key = SimKeys.TOTAL_READS_KEY
                            di_ms = merge.merge(globalData, key)
                            stat.attrib["value"] = str(math.ceil(di_ms[key]))
                        elif stat_key_name == McPATTask.READ_MISSES:
                            assert stat.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                            key = SimKeys.L1_READ_MISSES_KEY
                            di_ms = merge.merge(globalData, key)
                            stat.attrib["value"] = str(math.ceil(di_ms[key]))
                        elif stat_key_name == McPATTask.WRITE_ACCESSES:
                            assert stat.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                            key = SimKeys.TOTAL_WRITES_KEY
                            di_ms = merge.merge(globalData, key)
                            stat.attrib["value"] = str(math.ceil(di_ms[key]))
                        elif stat_key_name == McPATTask.WRITE_MISSES:
                            assert stat.attrib["value"] == McPATTask.VALID_PLACEHOLDER
                            key = SimKeys.L1_WRITE_MISSES_KEY
                            di_ms = merge.merge(globalData, key)
                            stat.attrib["value"] = str(math.ceil(di_ms[key]))

    def transform_system(self, system, num_cores, li_data, needsMD, viserConfig):
        globalData = Result.getGlobalData(li_data)
        for child in system:
            # print("Child:%s %s" % (child.tag, child.attrib))
            if viserConfig and _isParam(child.tag):
                key_name = child.attrib['name']
                if key_name == "number_of_L3s":
                    assert int(child.attrib["value"]) == 1
                    child.attrib["value"] = str(2)
            if _isStat(child.tag):
                key_name = child.attrib["name"]
                if key_name == McPATTask.TOTAL_CYCLES:
                    # print("Key name:%s, key value:%s" % (key_name, key_value))
                    assert child.attrib["value"] == McPATTask.INVALID_PLACEHOLDER
                    key = SimKeys.BANDWIDTH_CYCLE_COUNT_KEY
                    di_ms = merge.merge(globalData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))

            elif _isComponent(child.tag):
                key_id = child.attrib["id"]
                key_name = child.attrib["name"]
                # print("Key id:%s, key name:%s" % (key_id, key_name))
                if McPATTask.PREFIX_COMP_CORE in key_id:
                    self.transform_cores(child, num_cores, li_data, needsMD, viserConfig)
                elif McPATTask.PREFIX_SYSTEM_L2 in key_id:
                    self.transform_L2s(child, num_cores, li_data, needsMD, viserConfig)
                elif McPATTask.PREFIX_SYSTEM_L3 in key_id:
                    self.transform_L3(child, li_data, num_cores)
                elif McPATTask.PREFIX_SYSTEM_NOC in key_id:
                    self.transform_nocs(child, li_data)
                elif McPATTask.PREFIX_SYSTEM_MC in key_id:
                    self.transform_mcs(child, li_data)

    def transform_nocs(self, noc, li_data):
        globalData = Result.getGlobalData(li_data)
        for child in noc:
            if _isStat(child.tag):
                key_name = child.attrib["name"]
                if key_name == McPATTask.TOTAL_ACCESSES:
                    assert child.attrib["value"] == McPATTask.INVALID_PLACEHOLDER
                    key = SimKeys.ONCHIP_NETWORKMSG_SIZE_16BYTES_FLITS_KEY
                    di_ms = merge.merge(globalData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key] * 6))

    def transform_mcs(self, mc, li_data):
        globalData = Result.getGlobalData(li_data)
        for child in mc:
            if _isStat(child.tag):
                key_name = child.attrib["name"]
                if key_name == McPATTask.MEM_ACCESSES:
                    assert child.attrib["value"] == McPATTask.INVALID_PLACEHOLDER
                    read_key = SimKeys.L3_READ_MISSES_KEY
                    reads = merge.merge(globalData, read_key)
                    write_key = SimKeys.L3_WRITE_MISSES_KEY
                    writes = merge.merge(globalData, write_key)
                    aim_read_key = ViserSimKeys.AIM_READ_MISSES_KEY
                    aim_reads = merge.merge(globalData, aim_read_key)
                    aim_write_key = ViserSimKeys.AIM_WRITE_MISSES_KEY
                    aim_writes = merge.merge(globalData, aim_write_key)
                    child.attrib["value"] = str(
                        math.ceil(reads[read_key] + writes[write_key] + aim_reads[aim_read_key] +
                                  aim_writes[aim_write_key]))
                elif key_name == McPATTask.MEM_READS:
                    assert child.attrib["value"] == McPATTask.INVALID_PLACEHOLDER
                    read_key = SimKeys.L3_READ_MISSES_KEY
                    reads = merge.merge(globalData, read_key)
                    aim_read_key = ViserSimKeys.AIM_READ_MISSES_KEY
                    aim_reads = merge.merge(globalData, aim_read_key)
                    child.attrib["value"] = str(math.ceil(reads[read_key] +
                                                          aim_reads[aim_read_key]))
                elif key_name == McPATTask.MEM_WRITES:
                    assert child.attrib["value"] == McPATTask.INVALID_PLACEHOLDER
                    write_key = SimKeys.L3_WRITE_MISSES_KEY
                    writes = merge.merge(globalData, write_key)
                    aim_write_key = ViserSimKeys.AIM_WRITE_MISSES_KEY
                    aim_writes = merge.merge(globalData, aim_write_key)
                    child.attrib["value"] = str(
                        math.ceil(writes[write_key] + aim_writes[aim_write_key]))

    def transform_L2s(self, l2, num_cores, li_data, needsMD, viserConfig):
        # Find L2 id
        core_no = l2.attrib["name"][2:]
        assert int(core_no) < num_cores
        pcData = Result.getPerCoreData(li_data, int(core_no))

        for child in l2:
            # print("Child:%s %s" % (child.tag, child.attrib))
            if _isParam(child.tag):
                if needsMD and child.attrib["name"] == "L2_config":
                    vals = child.attrib["value"].split(",")
                    cache_size = float(vals[0])
                    line_size = float(vals[1])
                    num_lines = cache_size / line_size
                    new_line_size = (line_size + McPATTask.RD_MD_BYTES_PER_LINE +
                                     McPATTask.WR_MD_BYTES_PER_LINE)
                    if viserConfig:
                        new_line_size += McPATTask.ARC_VERSION_SIZE
                    new_cache_size = num_lines * new_line_size
                    vals[0] = str(new_cache_size)
                    vals[1] = str(new_line_size)
                    child.attrib["value"] = ",".join(vals)
            elif _isStat(child.tag):
                stat_key_name = child.attrib["name"]
                if stat_key_name == McPATTask.READ_ACCESSES:
                    assert child.attrib["value"] == McPATTask.INVALID_PLACEHOLDER
                    key = PerCoreStatsKeys.L1_READ_MISSES_KEY
                    di_ms = merge.merge(pcData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))
                elif stat_key_name == McPATTask.READ_MISSES:
                    assert child.attrib["value"] == McPATTask.INVALID_PLACEHOLDER
                    key = PerCoreStatsKeys.L2_READ_MISSES_KEY
                    di_ms = merge.merge(pcData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))
                elif stat_key_name == McPATTask.WRITE_ACCESSES:
                    assert child.attrib["value"] == McPATTask.INVALID_PLACEHOLDER
                    key = PerCoreStatsKeys.L1_WRITE_MISSES_KEY
                    di_ms = merge.merge(pcData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))
                elif stat_key_name == McPATTask.WRITE_MISSES:
                    assert child.attrib["value"] == McPATTask.INVALID_PLACEHOLDER
                    key = PerCoreStatsKeys.L2_WRITE_MISSES_KEY
                    di_ms = merge.merge(pcData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))

    def transform_cores(self, core, num_cores, li_data, needsMD, viserConfig):
        # Need to do the following transformations for each core

        # Find core id
        core_no = core.attrib["name"][4:]
        assert int(core_no) < num_cores
        pcData = Result.getPerCoreData(li_data, int(core_no))

        for child in core:
            if _isStat(child.tag):
                if child.attrib["name"] == McPATTask.TOTAL_CYCLES:
                    assert child.attrib["value"] == McPATTask.INVALID_PLACEHOLDER
                    key = PerCoreStatsKeys.TOTAL_CYCLES
                    di_ms = merge.merge(pcData, key)
                    child.attrib["value"] = str(math.ceil(di_ms[key]))
            elif _isComponent(child.tag):
                key_id = child.attrib["id"]
                assert McPATTask.PREFIX_COMP_CORE in key_id
                key_name = child.attrib["name"]
                if key_name == "dcache":
                    for stat in child:
                        stat_key_name = stat.attrib["name"]
                        if needsMD and stat_key_name == "dcache_config":
                            vals = stat.attrib["value"].split(",")
                            cache_size = float(vals[0])
                            line_size = float(vals[1])
                            num_lines = cache_size / line_size
                            new_line_size = (line_size + McPATTask.RD_MD_BYTES_PER_LINE +
                                             McPATTask.WR_MD_BYTES_PER_LINE)
                            if viserConfig:
                                new_line_size += McPATTask.ARC_VERSION_SIZE
                            new_cache_size = num_lines * new_line_size
                            vals[0] = str(new_cache_size)
                            vals[1] = str(new_line_size)
                            stat.attrib["value"] = ",".join(vals)
                        if stat_key_name == McPATTask.READ_ACCESSES:
                            assert stat.attrib["value"] == McPATTask.INVALID_PLACEHOLDER
                            key = PerCoreStatsKeys.TOTAL_READS_KEY
                            di_ms = merge.merge(pcData, key)
                            stat.attrib["value"] = str(math.ceil(di_ms[key]))
                        elif stat_key_name == McPATTask.READ_MISSES:
                            assert stat.attrib["value"] == McPATTask.INVALID_PLACEHOLDER
                            key = PerCoreStatsKeys.L1_READ_MISSES_KEY
                            di_ms = merge.merge(pcData, key)
                            stat.attrib["value"] = str(math.ceil(di_ms[key]))
                        elif stat_key_name == McPATTask.WRITE_ACCESSES:
                            assert stat.attrib["value"] == McPATTask.INVALID_PLACEHOLDER
                            key = PerCoreStatsKeys.TOTAL_WRITES_KEY
                            di_ms = merge.merge(pcData, key)
                            stat.attrib["value"] = str(math.ceil(di_ms[key]))
                        elif stat_key_name == McPATTask.WRITE_MISSES:
                            assert stat.attrib["value"] == McPATTask.INVALID_PLACEHOLDER
                            key = PerCoreStatsKeys.L1_WRITE_MISSES_KEY
                            di_ms = merge.merge(pcData, key)
                            stat.attrib["value"] = str(math.ceil(di_ms[key]))

    @staticmethod
    def __outputPrefix():
        return "[mcpat] "

    def runMcPAT(self):
        if self.options.verbose >= 1 or self.options.printOnly:
            print(McPATTask.__outputPrefix() + "Executing McPAT...")

        cwd = os.getcwd()
        os.chdir(self.mcpat_input)
        DEBUG = False
        try:
            total = 0
            for _, _, filenames in os.walk(os.getcwd()):
                for filename in filenames:
                    total += 1
                    cmdLine = McPATTask.MCPAT_BIN + filename
                    params = filename.split("-")
                    try:
                        assert len(params) == 3 or len(params) == 4
                    except AssertionError:
                        util.raiseError("File name:%s params=%s" % (filename, params), stack=True)
                    if util.isViserConfig(params[1]) or (util.isCEConfig(params[1]) and
                                                         "aim" in params[2]):
                        assert len(params) == 4
                        cmdLine += McPATTask.VISER_McPAT_ARGS
                    else:
                        cmdLine += McPATTask.SIM_McPAT_ARGS
                    outpath = self.mcpat_output + os.sep + filename.replace(".xml", ".mcpat")
                    cmdLine += outpath
                    if self.options.verbose >= 2 or self.options.printOnly:
                        print(McPATTask.__outputPrefix() + cmdLine)
                    # McPAT executions are very time consuming
                    if not os.path.exists(outpath) and not self.options.printOnly:
                        if DEBUG:
                            print("Running McPAT on %s" % (filename))
                        pid = subprocess.Popen(cmdLine, shell=True)
                        while pid.poll() is None:
                            time.sleep(3)
                    elif os.path.exists(outpath):
                        if DEBUG:
                            print("Skipping running McPAT on %s" % (filename))
        finally:
            os.chdir(cwd)
            if self.options.verbose >= 2 or self.options.printOnly:
                print(McPATTask.__outputPrefix() + "Done executing McPAT...")
