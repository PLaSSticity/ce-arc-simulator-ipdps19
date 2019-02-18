import ast

from options import util
from options.constants import Constants


class BackendSimulator(Constants):

    CPUID_KEY = "cpuid"
    GLOBAL_CPUID_VAL = -1

    @staticmethod
    def parseStats(fileName, di_store):
        try:
            f = open(fileName)  # 'r' is implicit if omitted
            for line in f:
                coreid, d = BackendSimulator.__processLine(line)
                if not d:
                    continue  # Comment line
                if coreid in di_store:
                    di_store[coreid].update(d)
                else:
                    di_store.update({coreid: d})
        except RuntimeError as e:
            # Does not catch all exceptions
            # http://stackoverflow.com/questions/18982610/difference-between-except-and-except-exception-as-e-in-python
            print("Exception thrown:", fileName)
            print(line)
            util.raiseError(repr(e), stack=True)
        return di_store

    @staticmethod
    def __processLine(line):
        d = {}
        line = line.strip()
        val = -1
        # We have added histograms to the output file for Viser
        if not line.startswith("#"):
            tmp = ast.literal_eval(line)
            if BackendSimulator.CPUID_KEY in tmp:
                val = tmp[BackendSimulator.CPUID_KEY]
            assert (val >= -1 and val < 32)
            d = tmp
        return [val, d]
