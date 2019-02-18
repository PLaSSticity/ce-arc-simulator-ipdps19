import os
import subprocess
import time

# only importing the module to avoid circular dependency
# https://stackoverflow.com/questions/7336802/how-to-avoid-circular-imports-in-python
import tasks.runtask

from options import util
from options.benchmarks import Benchmark
from options.constants import Constants


class Sniper(Constants):
    """Run the Sniper tool. It assumes the Sniper tool is available."""

    SNIPER_EXEC = "run-sniper"
    CMD_LINE_OPTIONS = " --viz --power --pin-stats --no-cache-warming"

    PIN_HOME = os.getenv("PIN_HOME")
    GRAPHITE_ROOT = os.getenv("GRAPHITE_ROOT")
    SNIPER_ROOT = os.getenv("SNIPER_ROOT")
    PARSEC_SNIPER = os.getenv("PARSEC_SNIPER")

    sniperIDsList = []
    TIMEOUT = 30

    @staticmethod
    def __outputPrefix():
        return "[sniper] "

    @staticmethod
    def __printTaskInfoStart(options):
        if options.verbose >= 1:
            print(Sniper.__outputPrefix() + "Executing run task...")

    @staticmethod
    def __printTaskInfoEnd(options):
        if options.verbose >= 1:
            print(Sniper.__outputPrefix() + "Done executing run task...")

    @staticmethod
    def runSniper(options):
        Sniper.__printTaskInfoStart(options)
        try:
            workloadTuple = tasks.runtask.RunTask.workloadTuple
            benchTuple = tasks.runtask.RunTask.benchTuple

            for w in workloadTuple:
                for num in range(1, options.trials + 1):
                    benchNum = len(benchTuple)
                    for bStart in range(0, benchNum, options.parallelBenches):
                        bEnd = (bStart + options.parallelBenches) if (
                            bStart + options.parallelBenches <= benchNum) else benchNum

                        # Clear lists of processIDs
                        Sniper.sniperIDsList = []

                        benchmarks = benchTuple[bStart:bEnd]
                        print(Sniper.__outputPrefix() + "Benchmarks to run parallelly: " +
                              ",".join(benchmarks))

                        for b in benchTuple[bStart:bEnd]:
                            # Hack for vips, which is missing the ROI annotation in PARSEC 3.0 beta
                            if b == "vips" and options.roiOnly:
                                print(Sniper.__outputPrefix() +
                                      "*WARNING*: vips 3.0-beta is missing ROI "
                                      "annotation, resetting ROI flag.")

                            # Setup output directory for this current trial
                            Sniper._startSniper(options, b, w, num)

                        if not options.printOnly:
                            # Check if all the processes have terminated
                            while not Sniper.__isTerminated(options):
                                time.sleep(Sniper.TIMEOUT)

                        benchmarks = benchTuple[bStart:bEnd]
                        print(Sniper.__outputPrefix() + "Done running " + ",".join(benchmarks))
        finally:
            Sniper.__printTaskInfoEnd(options)

    @staticmethod
    def _startSniper(options, bench, workload, trial):
        cmdLine = Sniper.PARSEC_SNIPER + "/bin/parsecmgmt -a run -p "
        if Benchmark.isParsecBenchmark(bench):
            cmdLine += bench
        else:
            util.raiseError("Invalid bench: ", bench)

        cmd_options = Sniper.CMD_LINE_OPTIONS
        # Pass Sniper configuration file
        if options.cores == 8:
            cmd_options += " -c arc-8"
        elif options.cores == 16:
            cmd_options += " -c arc-16"
        elif options.cores == 32:
            cmd_options += " -c arc-32"
        else:
            util.raiseError("Unknown number of cores: %s" % (options.cores))

        # Append benchmark to output directory name, since otherwise Sniper will overwrite contents
        out_dir = options.getExpOutputDir() + "-" + bench

        cmdLine += (" -c gcc-hooks -i " + workload + " -n " + str(options.pinThreads) +
                    ''' -s "''' + Sniper.SNIPER_ROOT + Sniper.FILE_SEP + Sniper.SNIPER_EXEC +
                    " -n " + str(options.pinThreads) + " -d " + out_dir + cmd_options)

        if options.roiOnly and bench != "vips":
            cmdLine += " --roi"
        cmdLine += ''' -- "'''

        if options.verbose >= 2 or options.printOnly:
            print(Sniper.__outputPrefix() + cmdLine)
        if not options.printOnly:
            Sniper.sniperIDsList.append(subprocess.Popen(cmdLine, shell=True))

    @staticmethod
    def __isTerminated(options):
        for idx in Sniper.sniperIDsList:
            if idx.poll() is None:
                return False

        return True
