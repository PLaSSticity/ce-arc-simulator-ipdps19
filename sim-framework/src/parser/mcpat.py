from options import util
from result.statskeys import EnergyStatsKeys


class Mcpat:

    # SB: This method seems very brittle. I do not like this.
    @staticmethod
    def parseDetailedStats(filename, d):
        """This only supports Viser configs that have an AIM."""
        f = open(filename)
        inProcessor = False
        inAIM = False
        num_l3s = 0
        for line in f:
            line = line.strip()

            if line == "Processor:":
                inProcessor = True
                continue
            elif ":" in line:
                inProcessor = False

            if "L3" in line:
                num_l3s += 1
                if num_l3s == 3:
                    inAIM = True

            if inAIM and "Runtime Dynamic" in line:
                d[EnergyStatsKeys.AIM_DYNAMIC_POWER] = Mcpat.__getValue(line)
            elif inAIM and "Subthreshold Leakage with power gating" in line:
                d[EnergyStatsKeys.AIM_STATIC_POWER] = Mcpat.__getValue(line)

            if inProcessor and "Area" in line:
                d[EnergyStatsKeys.AREA] = Mcpat.__getValue(line)
            elif inProcessor and "Subthreshold Leakage with power gating" in line:
                d[EnergyStatsKeys.STATIC_POWER] = Mcpat.__getValue(line)
            elif inProcessor and "Runtime Dynamic" in line:
                d[EnergyStatsKeys.DYNAMIC_POWER] = Mcpat.__getValue(line)

        try:
            if "idealaim" in filename and "32" in filename:
                assert num_l3s == 4
            else:
                assert num_l3s == 3
        except AssertionError:
            print("File name: ", filename)
            util.raiseError("Number of l3s %s do not match" % (num_l3s))

        return d

    @staticmethod
    def parseTerseStats(fileName, dic):
        f = open(fileName)
        for line in f:
            if "Total Cores" in line:
                break
            d = Mcpat.__processLine(line)
            dic.update(d)
        return dic

    @staticmethod
    def __processLine(line):
        d = {}
        if "Area" in line:
            d[EnergyStatsKeys.AREA] = Mcpat.__getValue(line)
        elif "Subthreshold Leakage with power gating" in line:
            d[EnergyStatsKeys.STATIC_POWER] = Mcpat.__getValue(line)
        elif "Runtime Dynamic" in line:
            d[EnergyStatsKeys.DYNAMIC_POWER] = Mcpat.__getValue(line)

        return d

    @staticmethod
    def __getValue(line):
        val = line.split(" ")[-2].strip()
        return float(val)
