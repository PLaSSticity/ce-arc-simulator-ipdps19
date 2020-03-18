import os
import subprocess
import time

from options import util
from options.benchmarks import Benchmark
from options.conflicts import Conflicts
from options.constants import Constants
import tasks.sniper
from tasks.synctask import SyncTask


class RunTask(Constants):
    """Run the tools."""

    tasksTuple = ()
    toolsTuple = ()
    workloadTuple = ()

    pinIDsList = []
    mesiIDsList = []
    viserIDsList = []
    pauseIDsList = []
    rccsiIDsList = []

    httpdID = 0
    httpClientIDsList = []  # list for client ids

    TIMEOUT = 30
    PINTOOL_ROOT = ""

    @staticmethod
    def createExpOutputDir(options):
        outputDir = options.getExpOutputDir()
        if not os.path.exists(outputDir):
            os.makedirs(outputDir)

    @staticmethod
    def prepareOutputDirs(options):
        """This method creates the output directories beforehand based on input options."""
        cwd = os.getcwd()
        os.chdir(options.getExpOutputDir())
        try:
            for w in RunTask.workloadTuple:
                for num in range(1, options.trials + 1):
                    for b in RunTask.benchTuple:
                        path = RunTask.getPathPortion(b, w, num)
                        if not os.path.exists(path):
                            os.makedirs(path)
        finally:
            os.chdir(cwd)

    @staticmethod
    def __outputPrefix():
        return "[run] "

    @staticmethod
    def __printTaskInfoStart(options):
        if options.verbose >= 1:
            print(RunTask.__outputPrefix() + "Executing run task...")

    @staticmethod
    def __printTaskInfoEnd(options):
        if options.verbose >= 1:
            print(RunTask.__outputPrefix() + "Done executing run task...")

    @staticmethod
    def runTask(options):
        RunTask.__printTaskInfoStart(options)

        RunTask.toolsTuple = options.getToolsTuple()
        RunTask.workloadTuple = options.getWorkloadTuple()
        RunTask.benchTuple = options.getBenchTuple()

        if "sniper" in options.getToolsTuple():
            return tasks.sniper.Sniper.runSniper(options)
        else:
            # Setup root experimental output directory
            RunTask.createExpOutputDir(options)
            RunTask.prepareOutputDirs(options)
            RunTask.createRerunFile(options)

        try:
            cwd = os.getcwd()

            RunTask.PINTOOL_ROOT = (RunTask.ST_PINTOOL_ROOT) if (
                options.pinTool == "viserST") else (RunTask.VS_PINTOOL_ROOT)

            os.chdir(RunTask.PINTOOL_ROOT)

            for w in RunTask.workloadTuple:
                for num in range(1, options.trials + 1):
                    pausePresent = False
                    mesiPresent = False
                    viserPresent = False
                    rccsiPresent = False
                    for proj in options.getSimulatorsTuple():
                        if util.isMESIConfig(proj) or util.isCEConfig(proj):
                            mesiPresent = True
                        if util.isViserConfig(proj):
                            viserPresent = True
                        if util.isRCCSIConfig(proj):
                            rccsiPresent = True
                        if util.isPauseConfig(proj):
                            pausePresent = True

                    writeFifo = False
                    backendSimPresent = False
                    if (mesiPresent or viserPresent or rccsiPresent or pausePresent):
                        writeFifo = True
                        backendSimPresent = True
                    elif options.generateTrace:
                        writeFifo = True

                    if options.confIndex >= 0:
                        # Do collision analysis
                        assert (not writeFifo and not backendSimPresent)

                    benchNum = len(RunTask.benchTuple)
                    for bStart in range(0, benchNum, options.parallelBenches):
                        bEnd = (bStart + options.parallelBenches) if (
                            bStart + options.parallelBenches <= benchNum) else benchNum

                        # Clear lists of processIDs
                        RunTask.pinIDsList = []
                        RunTask.mesiIDsList = []
                        RunTask.viserIDsList = []
                        RunTask.pauseIDsList = []
                        RunTask.rccsiIDsList = []

                        benchmarks = RunTask.benchTuple[bStart:bEnd]
                        print(RunTask.__outputPrefix() + "Benchmarks to run parallelly: " +
                              ",".join(benchmarks))

                        for b in RunTask.benchTuple[bStart:bEnd]:
                            # Hack for vips, which is missing the ROI
                            # annotation in PARSEC 3.0 beta
                            if b == "vips" and options.roiOnly:
                                print(RunTask.__outputPrefix() + "*WARNING*: "
                                      "vips 3.0-beta is missing ROI "
                                      "annotation, resetting ROI flag.")

                            # Setup output directory for this current trial
                            for tool in RunTask.toolsTuple:
                                if util.isPintool(tool):
                                    if not options.generateTrace:
                                        RunTask.__setupFifos(options, backendSimPresent, b)
                                        time.sleep(1)

                                    if Benchmark.isHTTPDBenchmark(b):
                                        if options.attachPid:
                                            RunTask.__startServer(options, b)

                                    RunTask.__startPintool(options, b, w, num, writeFifo,
                                                           backendSimPresent)
                                    time.sleep(1)
                                    if backendSimPresent and not options.generateTrace:
                                        RunTask.__forkPipes(options, backendSimPresent, b)
                                        time.sleep(1)

                                if not options.generateTrace:
                                    if util.isMESIConfig(tool) or util.isCEConfig(tool):
                                        RunTask.__startMesiSimulator(options, b, w, num, tool)

                                    if util.isViserConfig(tool):
                                        RunTask.__startViserSimulator(options, b, w, num, tool)

                                    if util.isRCCSIConfig(tool):
                                        RunTask.__startRCCSISimulator(options, b, w, num, tool)

                                    if util.isPauseConfig(tool):
                                        RunTask.__startPauseSimulator(options, b, w, num, tool)

                            if not options.printOnly:
                                if b == "mysqld":
                                    if not options.attachPid:
                                        # wait for the server program to start completely
                                        if backendSimPresent:
                                            time.sleep(18000)
                                        else:
                                            time.sleep(2700)
                                elif b == "httpd":
                                    if not options.attachPid:
                                        # wait for the server program to start completely
                                        if backendSimPresent:
                                            time.sleep(300)
                                        else:
                                            time.sleep(60)
                                elif b == "memcached":
                                    if not options.attachPid:
                                        # wait for the server program to start completely
                                        if backendSimPresent:
                                            time.sleep(300)
                                        else:
                                            time.sleep(5)

                                if Benchmark.isHTTPDBenchmark(b):
                                    time.sleep(1)
                                    RunTask.__startClients(options, w, b)
                                    # Check if all clients have terminated
                                    while not RunTask.__checkClients():
                                        time.sleep(RunTask.TIMEOUT)
                                    RunTask.__stopServer(options, b)

                        if not options.printOnly:
                            # Check if all the processes have terminated
                            while not RunTask.__isTerminated(options):
                                time.sleep(RunTask.TIMEOUT)

                        benchmarks = RunTask.benchTuple[bStart:bEnd]
                        print(RunTask.__outputPrefix() + "Done running " + ",".join(benchmarks))

        finally:
            if not options.generateTrace:
                RunTask.__cleanFifos(options, backendSimPresent)

            # Switch back to the start directory
            os.chdir(cwd)

            # if sameMachine is False, then copy the output
            # directory to the source machine specified in config.ini
            if not options.sameMachine:
                SyncTask.syncOutputDir(options)

            RunTask.__printTaskInfoEnd(options)

    @staticmethod
    def __setupFifos(options, backendSimPresent, bench):
        cmdLine = "rm -f " + bench + "." + RunTask.FIFO_PREFIX + "*; "
        cmdLine += ("mkfifo " + bench + "." + RunTask.FIFO_FRONTEND + "; ")
        if backendSimPresent:
            for tool in options.getSimulatorsTuple():
                cmdLine += ("mkfifo " + bench + "." + RunTask.FIFO_PREFIX + tool + "; ")

        if options.verbose >= 2 or options.printOnly:
            print(RunTask.__outputPrefix() + cmdLine)
        if not options.printOnly:
            subprocess.call(cmdLine, shell=True)

        if options.lockstep:
            # SB: We could have done this from Python as well instead of calling a
            # C++ application
            cmdLine = "./namedpipe " + str(5 * options.pinThreads)
            if options.verbose >= 2 or options.printOnly:
                print(RunTask.__outputPrefix() + cmdLine)
            if not options.printOnly:
                subprocess.Popen(cmdLine, shell=True)

    @staticmethod
    def __cleanFifos(options, backendSimPresent):
        #   cmdLine = ("rm -f " + RunTask.FIFO_FRONTEND + "; ")

        #   if backendSimPresent:
        #        for tool in options.getSimulatorsTuple():
        #            cmdLine += ("rm -f " + RunTask.FIFO_PREFIX + tool + "; ")
        #
        #       for i in range(5 * options.pinThreads):
        #           cmdLine += ("rm -f " + RunTask.FIFO_PERTHREAD + str(i)
        #                     + "; ")

        cmdLine = "rm -rf *." + RunTask.FIFO_PREFIX + "*"
        if options.verbose >= 2 or options.printOnly:
            print(RunTask.__outputPrefix() + cmdLine)
        if not options.printOnly:
            subprocess.call(cmdLine, shell=True)

    @staticmethod
    def getPathPortion(bench, size, trial):
        return size + RunTask.FILE_SEP + str(trial) + RunTask.FILE_SEP + bench

    @staticmethod
    def getOutputPath(options, bench, size, trial):
        return options.getExpOutputDir() + RunTask.FILE_SEP + RunTask.getPathPortion(
            bench, size, trial)

    @staticmethod
    def __startPintool(options, bench, size, trial, writeFifo, backendSimPresent):
        if Benchmark.isHTTPDBenchmark(bench):
            if options.attachPid:
                cmdLine = RunTask.PINBIN
                cmdLine += " -pid " + str(RunTask.httpdID) + " "
                cmdLine += "-t " + RunTask.PINTOOL_ROOT + "/obj-intel64/visersim.so"
            else:
                cmdLine = RunTask.PINBIN
                cmdLine += "-t " + RunTask.PINTOOL_ROOT + "/obj-intel64/visersim.so"
        else:
            cmdLine = RunTask.PARSECMGMT
            if Benchmark.isParsecBenchmark(bench):
                cmdLine += bench
            elif Benchmark.isSplash2xBenchmark(bench):
                cmdLine += ("splash2x." + bench)
            else:
                util.raiseError("Invalid bench: ", bench)

            cmdLine += (" " + RunTask.PARSEC_ARGS1 + size + " -n " + str(options.pinThreads) + " " +
                        RunTask.PARSEC_ARGS3 + RunTask.PINTOOL_ROOT + RunTask.PARSEC_ARGS4)

        statsFile = (RunTask.getOutputPath(options, bench, size, trial) + RunTask.FILE_SEP +
                     "pintool-stats.output")
        cmdLine += " -sim-stats " + statsFile

        if options.siteTracking:
            cmdLine += " -siteTracking 1"
            cmdLine += " -source-names-index-file " + \
                RunTask.PINTOOL_ROOT + "/" + bench + ".filenames"
            cmdLine += " -routine-names-index-file " + \
                RunTask.PINTOOL_ROOT + "/" + bench + ".rtnnames"
            cmdLine += " -trace-text-file " + RunTask.PINTOOL_ROOT + "/eventTrace.txt"

        if not writeFifo:
            cmdLine += " -write-fifo 0"
        else:
            cmdLine += " -write-fifo 1"
        # We use a different key other than "threads" since benchmarks like
        # x264 uses that word as an argument
        cmdLine += " -pinThreads " + str(options.pinThreads)
        if options.lockstep:
            cmdLine += " -lockstep 1"
            cmdLine += " -backends " + str(options.nonMesiSimulators)
        else:
            cmdLine += " -lockstep 0"

        if backendSimPresent:
            cmdLine += (" -tosim-fifo " + RunTask.PINTOOL_ROOT + "/" + bench + "." +
                        RunTask.FIFO_FRONTEND)

        if options.confIndex >= 0:
            # do collision analysis
            cmdLine += " -enable-collisionAnalysis 1"
            tup_conflict = Conflicts.LI_SITES[options.confIndex]
            cmdLine += " -intstLine0 " + str(tup_conflict[0])
            cmdLine += " -usleep0 " + str(tup_conflict[1])
            cmdLine += " -intstLine1 " + str(tup_conflict[2])
            cmdLine += " -usleep1 " + str(tup_conflict[3])
        else:
            cmdLine += " -enable-collisionAnalysis 0"

        if not Benchmark.isHTTPDBenchmark(bench):
            cmdLine += ''' --"'''
        elif not options.attachPid:
            if bench == "httpd":
                cmdLine += " -- " + RunTask.HTTPD_DEBUG_START
            elif bench == "mysqld":
                cmdLine += (" -- " + RunTask.MYSQLD_START + RunTask.MYSQLD_CACHED_THREADS +
                            str(options.cores) + RunTask.MYSQLD_INNODB_THREADS + str(options.cores))
            elif bench == "memcached":
                cmdLine += (" -- " + RunTask.MEMCACHED_START + " -t " + str(options.cores))

        if options.verbose >= 2 or options.printOnly:
            print(RunTask.__outputPrefix() + cmdLine)
        if not options.printOnly:
            RunTask.pinIDsList.append(subprocess.Popen(cmdLine, shell=True))

    @staticmethod
    def __forkPipes(options, backendSimPresent, bench):
        cmdLine = "./pipefork " + bench + "." + RunTask.FIFO_FRONTEND

        if backendSimPresent:
            for tool in options.getSimulatorsTuple():
                cmdLine = cmdLine + " " + bench + "." + RunTask.FIFO_PREFIX + tool

        if options.verbose >= 2 or options.printOnly:
            print(RunTask.__outputPrefix() + cmdLine)

        if not options.printOnly:
            subprocess.Popen(cmdLine, shell=True)

    @staticmethod
    def __addJVMArgs(options):
        cmdLine = "java"
        if options.jassert:
            cmdLine += " -enableassertions"  # "-ea"
        return cmdLine

    @staticmethod
    def __addCommonSimulatorArgs(options, bench):
        cmdLine = ""
        enableXasserts = "false"
        if options.xassert:
            enableXasserts = "true"
        cmdLine += (" --cores " + str(options.cores) + " --pinThreads " + str(options.pinThreads) +
                    " --use-l2 true"
                    " --xassert " + enableXasserts + " --assert-period " + str(options.period))
        # Hack for vips, which is missing the ROI annotation in PARSEC 3.0 beta
        # Also hack for httpd, which doesn't have the ROI annotation
        if bench == "vips" or Benchmark.isHTTPDBenchmark(bench):
            cmdLine += " --model-only-roi false"
        else:
            cmdLine += " --model-only-roi " + \
                ("true" if options.roiOnly else "false")

        # Pass the fact that Pintool is configured
        cmdLine += " --pintool true"
        cmdLine += " "
        return cmdLine

    @staticmethod
    def __startMesiSimulator(options, bench, size, trial, tool):
        cmdLine = RunTask.__addJVMArgs(options)
        cmdLine += (RunTask.MESISIM_CLASSPATH + " --tosim-fifo " + bench + "." +
                    RunTask.FIFO_PREFIX + tool + " --sim-mode baseline")
        cmdLine += RunTask.__addCommonSimulatorArgs(options, bench)
        # Pass whether the backend needs to execute in lockstep with the
        # Pintool
        if options.lockstep and not options.isViserPresent() \
                and not options.isPausePresent() and not options.isRCCSIPresent():
            cmdLine += " --lockstep true"
        else:
            cmdLine += " --lockstep false"

        statsFile = (RunTask.getOutputPath(options, bench, size, trial) + RunTask.FILE_SEP + tool +
                     "-stats.py")
        cmdLine += " --stats-file " + statsFile

        if options.isPausePresent():
            cmdLine += " --with-pacifist-backends true"

        if tool == "mesi8":
            pass

        elif tool == "mesi4":
            assert options.cores == 4
            cmdLine += " --l3-assoc 8"
            cmdLine += " --l3-size 8388608"  # 8 MB = 64 * 1024 * 1024

        elif tool == "mesi16":
            assert options.cores == 16
            cmdLine += " --l3-size 33554432"  # 32 MB = 32 * 1024 * 1024

        elif tool == "mesi32":
            assert options.cores == 32
            cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
            cmdLine += " --l3-assoc 32"  # One way per core

#         elif tool == "mesi32-32wayllc":
#             assert options.pinThreads == 32
#             cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
#             cmdLine += " --l3-assoc 32"

        elif tool == "ce4":
            cmdLine += " --l3-assoc 8"
            cmdLine += " --l3-size 8388608"  # 8 MB = 64 * 1024 * 1024
            cmdLine += " --conflict-exceptions true"

        elif tool == "ce4-32Kaim":
            cmdLine += " --l3-assoc 8"
            cmdLine += " --l3-size 8388608"  # 8 MB = 64 * 1024 * 1024
            cmdLine += " --conflict-exceptions true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --num-aim-lines 32768"

        # elif tool == "ce4-16Kaim":
        #     cmdLine += " --l3-assoc 8"
        #     cmdLine += " --l3-size 8388608"  # 8 MB = 64 * 1024 * 1024
        #     cmdLine += " --conflict-exceptions true"
        #     cmdLine += " --use-aim-cache true"
        #     cmdLine += " --num-aim-lines 16384"

        elif tool == "ce8":
            cmdLine += " --conflict-exceptions true"

        elif tool == "ce8-32Kaim":
            cmdLine += " --conflict-exceptions true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --num-aim-lines 32768"

        elif tool == "ce8-16Kaim":
            cmdLine += " --conflict-exceptions true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --num-aim-lines 16384"

        elif tool == "ce16":
            assert options.cores == 16
            cmdLine += " --conflict-exceptions true"
            cmdLine += " --l3-size 33554432"  # 32 MB = 32 * 1024 * 1024

        elif tool == "ce16-32Kaim":
            assert options.cores == 16
            cmdLine += " --conflict-exceptions true"
            cmdLine += " --l3-size 33554432"  # 32 MB = 32 * 1024 * 1024
            cmdLine += " --use-aim-cache true"
            cmdLine += " --num-aim-lines 32768"

        elif tool == "ce16-16Kaim":
            assert options.cores == 16
            cmdLine += " --conflict-exceptions true"
            cmdLine += " --l3-size 33554432"  # 32 MB = 32 * 1024 * 1024
            cmdLine += " --use-aim-cache true"
            cmdLine += " --num-aim-lines 16384"

        elif tool == "ce32":
            assert options.cores == 32
            cmdLine += " --conflict-exceptions true"
            cmdLine += " --l3-size 67108864"  # 64 MB, results in 32*1024 lines
            cmdLine += " --l3-assoc 32"  # One way per core

        elif tool == "ce32-32MBLLC":
            # Smaller LLC for sanity.
            assert options.cores == 32
            cmdLine += " --conflict-exceptions true"
            cmdLine += " --l3-size 33554432"  # 32 MB, 32 assoc, so number of lines will decrease
            cmdLine += " --l3-assoc 32"  # One way per core, 16 way isn't very realistic

        elif tool == "ce32-morecache":
            # Increase the LLC size almost in proportion to the AIM size, to see how much would
            # CE improve in performance.
            assert options.cores == 32
            cmdLine += " --conflict-exceptions true"
            cmdLine += " --l3-size 88080384"  # 64 line size * 42 assoc * 2^15 lines
            cmdLine += " --l3-assoc 42"  # One way per core

        elif tool == "ce32-32Kaim":
            assert options.cores == 32
            cmdLine += " --conflict-exceptions true"
            cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
            cmdLine += " --l3-assoc 32"  # One way per core
            cmdLine += " --use-aim-cache true"
            cmdLine += " --num-aim-lines 32768"

        # SB: This not a meaningful AIM size for a 32 core machine.
        # elif tool == "ce32-16Kaim":
        #     assert options.cores == 32
        #     cmdLine += " --conflict-exceptions true"
        #     cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
        #     cmdLine += " --l3-assoc 32"  # One way per core
        #     cmdLine += " --use-aim-cache true"
        #     cmdLine += " --num-aim-lines 16384"

        elif tool == "ce32-64Kaim":
            assert options.cores == 32
            cmdLine += " --conflict-exceptions true"
            cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
            cmdLine += " --l3-assoc 32"  # One way per core
            cmdLine += " --use-aim-cache true"
            cmdLine += " --num-aim-lines 65536"


#         elif tool == "mesi-ce32-32wayllc":
#             assert options.pinThreads == 32
#             cmdLine += " --conflict-exceptions true"
#             cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
#             cmdLine += " --l3-assoc 32"

        elif tool == "mesi8-regularplru":
            # build on mesi.
            cmdLine += " --use-plru true"

        elif tool == "mesi32-regularplru":
            # build on mesi.
            cmdLine += " --use-plru true"
            cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
            cmdLine += " --l3-assoc 32"  # One way per core

        elif tool == "mesi16-regularplru":
            assert options.cores == 16
            cmdLine += " --use-plru true"
            cmdLine += " --l3-size 33554432"  # 32 MB = 32 * 1024 * 1024

        else:
            assert False

        if options.verbose >= 2 or options.printOnly:
            print(RunTask.__outputPrefix() + cmdLine)
        if not options.printOnly:
            RunTask.mesiID = subprocess.Popen(cmdLine, shell=True)

    @staticmethod
    def __startViserSimulator(options, bench, size, trial, tool):
        cmdLine = RunTask.__addJVMArgs(options)
        cmdLine += (RunTask.VISERSIM_CLASSPATH + " --tosim-fifo " + bench + "." +
                    RunTask.FIFO_PREFIX + tool + " --sim-mode viser")
        cmdLine += RunTask.__addCommonSimulatorArgs(options, bench)
        # Pass whether the backend needs to execute in lockstep with the
        # Pintool
        if options.lockstep:
            cmdLine += " --lockstep true"
        else:
            cmdLine += " --lockstep false"

        statsFile = (RunTask.getOutputPath(options, bench, size, trial) + RunTask.FILE_SEP + tool +
                     "-stats.py")
        cmdLine += " --stats-file " + statsFile
        if options.siteTracking:
            cmdLine += " --site-tracking true"

        if tool == "viser8-unopt":
            # This is the basic design, where we invalidate all private cache
            # lines at every region boundary.
            cmdLine += " --use-aim-cache true"

        elif tool == "viser8-readonlyopt":
            # Successful read validation implies all the read-only lines
            # contain consistent values, so we can avoid invalidating
            # read-only lines.
            # Built on top of viserbasic
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --use-aim-cache true"

        elif tool == "viser8-lastwriteropt":
            # Lines whose private and shared version numbers differ by one
            # during post-commit are those that were dirty in the current
            # region (so the current core must be the last writer), and so
            # must contain up-to-date values.
            # Built on top of viserreadonlyopt
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --use-aim-cache true"

        elif tool == "viser8-updatewrites":
            # For lines whose private
            # and shared version numbers differ by more than one, we
            # proactively fetch updated values from the shared memory and
            # update the private lines in the hope that it will lead to hits
            # in the future.
            # Built on top of viserlastwriteropt.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --update-written-lines-during-version-check true"
            cmdLine += " --use-aim-cache true"

        elif tool == "viser8-untouchedlinesopt":
            # We do not invalidate untouched lines whose shared version number did not change, this
            # implies that the line was not written during the ongoing region.
            # Built on top of viserlastwriteropt.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --invalidate-untouched-lines-opt true"
            cmdLine += " --use-aim-cache true"

        elif tool == "viser8-specialinvalid":
            # Use a special invalid state to mark untouched lines.
            # Built on top of viserlastwriteropt.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-aim-cache true"

        elif tool == "viser8-bloomfilter":
            # Built on top of viserlastwriteropt.
            # Use Bloom filter to optimize invalidating untouched lines.
            # We use two Bloom functions by default.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"

        elif tool == "viser8-bloominvalid":
            # Use both a Bloom filter and a special invalid state. The special invalid state is
            # used for lines which are invalidated because of Bloom filter query.
            # Built on top of viserspecialinvalid/viserbloomfilter
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"

        elif tool == "viser8-onebloom":
            # Use only one Bloom filter function.
            # Built on top of viserbloominvalid.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --use-two-bloom-funcs false"

        elif tool == "viser8-selfinvalidationopt":
            # Viser with self-invalidation optimizations and a realistic AIM cache.
            # Alias for viserbloominvalid.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"

        elif tool == "viser8-deferwritebacks":
            # Defer write backs at region boundaries.
            # Built on top of viserbloominvalid.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"

        elif tool == "viser8-deferwritebacksprecise":
            # Maintain precise information about dirty offsets that were deferred.
            # Built on top of viserdeferwritebacks.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --defer-write-backs-precise true"

        elif tool == "viser8-skipvalidatingreadlines":
            # Skip read validation of lines that are not in the write
            # signature. Need to take care of the atomicity of the write ignature.
            # Built on top of viserdeferwritebacks.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"

        elif tool == "viser8-ignorefetchingreadbits":
            # Avoid fetching read bits from shared memory into private caches.
            # Built on top of viserskipvalidatingreadlines.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"

        elif tool == "viser8-ignorefetchingwritebits":
            # Avoid fetching read bits from shared memory into private caches.
            # Built on top of viserignorefetchingreadbits.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"

        elif tool == "viser8-32Kaim":
            # Alias for viserignorefetchingreadbits.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"

        elif tool == "viser8-fetchwritebits":
            # build on viseropt.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits false"

        elif tool == "viser8-noatomicupdates":
            # build on viseropt
            # treat atomic updates as regular memory accesses,
            # i.e., not updating values directly into the LLC
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"

        elif tool == "viser8-precisedefer":
            # Viser with all optimizations and a realistic AIM cache and with
            # precise deferred write backs.
            # Built on top of viseropt.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --defer-write-backs-precise true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"

        elif tool == "viser8-8Kaim":
            # Viser with all optimizations and a realistic AIM cache.
            # Built on top of viseropt.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --num-aim-lines 8192"

        elif tool == "viser8-16Kaim":
            # Viser with all optimizations and a realistic AIM cache.
            # Built on top of viseropt.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --num-aim-lines 16384"

        elif tool == "viser16-32Kaim":
            assert options.cores == 16
            # Viser with all optimizations and a realistic AIM cache.
            # Built on top of viseropt.
            cmdLine += " --l3-size 33554432"  # 32 MB = 32 * 1024 * 1024
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"

        elif tool == "viser16-16Kaim":
            assert options.cores == 16
            # Viser with all optimizations and a realistic AIM cache.
            # Built on top of viseropt.
            cmdLine += " --l3-size 33554432"  # 32 MB = 32 * 1024 * 1024
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --num-aim-lines 16384"

        elif tool == "viser16-idealaim":
            assert options.cores == 16
            # Viser with all optimizations and a realistic AIM cache.
            # Built on top of viseropt16.
            cmdLine += " --l3-size 33554432"  # 32 MB = 32 * 1024 * 1024
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache false"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"

        elif tool == "viser32-32Kaim":
            assert options.cores == 32
            # Viser with all optimizations and a realistic AIM cache.
            # Built on top of viseropt.
            cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
            cmdLine += " --l3-assoc 32"  # One way per core
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"

        # elif tool == "viser32-16Kaim":
        #     assert options.cores == 32
        #     # Viser with all optimizations and a realistic AIM cache.
        #     # Built on top of viseropt.
        #     cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
        #     cmdLine += " --l3-assoc 32"  # One way per core
        #     cmdLine += " --always-invalidate-read-only-lines false"
        #     cmdLine += " --invalidate-written-lines-only-after-version-check" \
        #         " true"
        #     cmdLine += " --special-invalid-state true"
        #     cmdLine += " --use-bloom-filter true"
        #     cmdLine += " --use-aim-cache true"
        #     cmdLine += " --defer-write-backs true"
        #     cmdLine += " --skip-validating-read-lines true"
        #     cmdLine += " --ignore-fetching-read-bits true"
        #     cmdLine += " --ignore-fetching-write-bits true"
        #     cmdLine += " --num-aim-lines 16384"

        elif tool == "viser32-64Kaim":
            assert options.cores == 32
            # Viser with all optimizations and a realistic AIM cache.
            # Built on top of viseropt.
            cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
            cmdLine += " --l3-assoc 32"  # One way per core
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --num-aim-lines 65536"

        elif tool == "viser4-32Kaim":
            assert options.cores == 4
            # Viser with all optimizations and a realistic AIM cache.
            # Built on top of viseropt.
            cmdLine += " --l3-size 8388608"  # 8 MB = 8 * 1024 * 1024
            cmdLine += " --l3-assoc 8"  # One way per core
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --num-aim-lines 32768"

        elif tool == "viser4-16Kaim":
            assert options.cores == 4
            # Viser with all optimizations and a realistic AIM cache.
            # Built on top of viseropt.
            cmdLine += " --l3-size 8388608"  # 64 MB = 64 * 1024 * 1024
            cmdLine += " --l3-assoc 8"  # One way per core
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --num-aim-lines 16384"

        elif tool == "viser4-idealaim":
            assert options.cores == 4
            # Viser with all optimizations and a realistic AIM cache.
            # Built on top of viseropt.
            cmdLine += " --l3-size 8388608"  # 64 MB = 64 * 1024 * 1024
            cmdLine += " --l3-assoc 8"  # One way per core
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache false"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"

        elif tool == "viser32-idealaim":
            assert options.cores == 32
            # Viser with all optimizations and a realistic AIM cache.
            # Built on top of viseropt32.
            cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
            cmdLine += " --l3-assoc 32"  # One way per core
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache false"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"

        elif tool == "viser8-idealaim":
            # Use an ideal AIM cache.
            # Built on top of viseropt.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache false"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"

        elif tool == "viser8-clearaimatregionboundaries":
            # Clear AIM cache lines at region boundaries.
            # Built on top of viseropt.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --clear-aim-region-boundaries true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"

        elif tool == "viser8-ignoredeferredlinesduringreadvalidation":
            # Incorrectly ignore fetching updated values for LLC lines during
            # read validation. This configuration is to just get an estimate
            # of the cost.
            # Built on top of viseropt.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --ignore-deferred-lines-read-validation true"

        elif tool == "viser8-nodefer":
            # Disallow deferring of write backs
            # Built on top of viseropt.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs false"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"

        elif tool == "viser8-evictnonwarlinefirst":
            # build on viseropt.
            # evict non war lines first
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --evict-non-WAR-line-first true"

        elif tool == "viser8-evictcleanlinefirst":
            # build on viseropt.
            # evict clean lines first
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --evict-clean-line-first true"

        elif tool == "viser8-lru":
            # Alias for viseropt.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"

        elif tool == "viser8-modifiedplru":
            # build on viseropt.
            # use modified plru
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --use-plru true"
            cmdLine += " --evict-clean-line-first true"
            cmdLine += " --set-write-bits-in-l2 true"

        elif tool == "viser8-plruatomicasboundary":
            # build on viseroptregularplru.
            # treat atomic updates as region boundaries
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --use-plru true"
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"

        elif tool == "viser8-plruatomicasregular":
            # build on viseroptregularplru.
            # treat atomic updates as regular memory accesses
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --use-plru true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"

        elif tool == "drf0unopt":
            # This is the basic design of "BARC", where we invalidate all private cache
            # lines at every AFR boundary.
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"
            cmdLine += " --use-plru true"

        elif tool == "drf0partialinvalid":
            # build on drf0unopt.
            # avoid self-invalidations using a special invalid state
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"
            cmdLine += " --use-plru true"
            cmdLine += " --partial-invalid-state true"

        elif tool == "drf0bloomfilter":
            # build on drf0partialinvalid.
            # avoid self-invalidations using write signatures
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"
            cmdLine += " --use-plru true"
            cmdLine += " --partial-invalid-state true"
            cmdLine += " --use-bloom-filter true"

        elif tool == "drf0bloomfilter1008bits":
            # build on drf0bloomfilter.
            # use larger write signatures
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"
            cmdLine += " --use-plru true"
            cmdLine += " --partial-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --bloom-filter-bits 1008"

        elif tool == "drf0deferwritebacks":
            # build on drf0bloomfilter.
            # defer write backs of dirty lines
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"
            cmdLine += " --use-plru true"
            cmdLine += " --partial-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --defer-write-backs true"

        elif tool == "drf0opt":
            # Alias for drf0deferwritebacks.
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"
            cmdLine += " --use-plru true"
            cmdLine += " --partial-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --defer-write-backs true"

        elif tool == "barcunoptspecialhandleatomics":
            # Alias for drf0unopt
            cmdLine += " --use-plru true"

        elif tool == "barcunopt":
            # build on barcunoptspecialhandleatomics
            # treat atomics as region boundaries
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"
            cmdLine += " --use-plru true"

        elif tool == "barcdeferwritebacks":
            # build on barcunopt.
            # defer write backs of dirty lines
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"
            cmdLine += " --use-plru true"
            cmdLine += " --defer-write-backs true"

        elif tool == "barcpartialinvalid":
            # build on barcdeferwritebacks.
            # avoid self-invalidations using a special invalid state
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"
            cmdLine += " --use-plru true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --partial-invalid-state true"

        elif tool == "barcpartialinvalidwp":
            # build on barcpartialinvalid.
            # perform writer prediction
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"
            cmdLine += " --use-plru true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --partial-invalid-state true"
            cmdLine += " --writer-prediction true"

        elif tool == "barcbloomfilter":
            # build on barcpartialinvalid.
            # avoid self-invalidations using write signatures
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"
            cmdLine += " --use-plru true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --partial-invalid-state true"
            cmdLine += " --use-bloom-filter true"

        elif tool == "barcbloomfilter1008bits":
            # build on barcbloomfilter.
            # use larger write signatures
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"
            cmdLine += " --use-plru true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --partial-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --bloom-filter-bits 1008"

        elif tool == "barcoptspecialhandleatomics":
            # build on barcunoptspecialhandleatomics.
            # turn on all optimizations
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --partial-invalid-state true"
            cmdLine += " --use-plru true"

        elif tool == "barcopt":
            # Alias for barcbloomfilter.
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"
            cmdLine += " --use-plru true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --partial-invalid-state true"
            cmdLine += " --use-bloom-filter true"

        elif tool == "barcoptmdplru":
            # build on barcopt.
            # use modified plru to evict partially invalid lines first
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"
            cmdLine += " --use-plru true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --partial-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --evict-partially-invalid-line-first true"

        elif tool == "barcoptwp":
            # build on barcopt
            # perform writer prediction
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"
            cmdLine += " --use-plru true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --partial-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --writer-prediction true"

        elif tool == "barcoptlru":
            # build on barcopt.
            # use lru
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --partial-invalid-state true"

        elif tool == "sarc":
            # build on barcunopt.
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"
            cmdLine += " --sarc true"
            cmdLine += " --use-plru true"

        elif tool == "sarcwp":
            # build on sarc.
            # perform writer prediction
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"
            cmdLine += " --sarc true"
            cmdLine += " --use-plru true"
            cmdLine += " --writer-prediction true"

        elif tool == "sarcbloomfilter":
            # build on sarc.
            # avoid self-invalidations using write signatures
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"
            cmdLine += " --use-plru true"
            cmdLine += " --sarc true"
            cmdLine += " --use-bloom-filter true"

        elif tool == "sarcselfinvalidatrelease":
            # build on sarc.
            # self invalidate read-only lines at lock releases besides lock acquires
            cmdLine += " --treat-atomic-updates-as-region-boundaries true"
            cmdLine += " --treat-atomic-updates-as-regular-accesses true"
            cmdLine += " --sarc true"
            cmdLine += " --self-invalidate-at-release true"
            cmdLine += " --use-plru true"

        else:
            assert False

        if Benchmark.isHTTPDBenchmark(bench):
            cmdLine += " --is-httpd true"

        if options.verbose >= 2 or options.printOnly:
            print(RunTask.__outputPrefix() + cmdLine)
        if not options.printOnly:
            RunTask.viserIDsList.append(subprocess.Popen(cmdLine, shell=True))

    @staticmethod
    def __startPauseSimulator(options, bench, size, trial, tool):
        cmdLine = RunTask.__addJVMArgs(options)

        # RZ: treat viseroptregularplru as a pause/restart config because I want
        # to generate graphs for its (estimated) costs of restarting a whole
        # program at exceptions.
        if "viseroptregularplru" in tool:
            cmdLine += RunTask.VISERSIM_CLASSPATH
        elif "pause" in tool:
            cmdLine += RunTask.PAUSESIM_CLASSPATH
        else:
            cmdLine += RunTask.RESTARTSIM_CLASSPATH

        cmdLine += (" --tosim-fifo " + bench + "." + RunTask.FIFO_PREFIX + tool +
                    " --sim-mode viser")
        cmdLine += RunTask.__addCommonSimulatorArgs(options, bench)
        # Pass whether the backend needs to execute in lockstep with the
        # Pintool
        if options.lockstep:
            cmdLine += " --lockstep true"
        else:
            cmdLine += " --lockstep false"

        statsFile = (RunTask.getOutputPath(options, bench, size, trial) + RunTask.FILE_SEP + tool +
                     "-stats.py")
        cmdLine += " --stats-file " + statsFile
        if options.siteTracking:
            cmdLine += " --site-tracking true"

        if tool == "pause8":
            # Built on top of viseroptregularplru.
            # use regular PLRU on L2 evictions
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --use-plru true"
            cmdLine += " --pause-cores-at-conflicts true"

        elif tool == "pause16":
            # Built on top of viseroptregularplru.
            # use regular PLRU on L2 evictions
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --use-plru true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --l3-size 33554432"  # 32 MB = 32 * 1024 * 1024

        elif tool == "pause32":
            # Built on top of viseroptregularplru.
            # use regular PLRU on L2 evictions
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --use-plru true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
            cmdLine += " --l3-assoc 32"  # One way per core

        elif tool == "viser8-regularplru":
            # build on viseropt.
            # use regular plru
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --use-plru true"

        elif tool == "viser16-regularplru":
            # build on viseropt.
            # use regular plru
            assert options.cores == 16
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --use-plru true"
            cmdLine += " --l3-size 33554432"  # 32 MB = 32 * 1024 * 1024

        elif tool == "viser32-regularplru":
            assert options.cores == 32
            # build on viseropt.
            # use regular plru
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --use-plru true"
            cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
            cmdLine += " --l3-assoc 32"  # One way per core

        elif tool == "viser32-regularplrucp1k":
            assert options.cores == 32
            # build on viseroptregularplru32.
            # set a check point every 100 interations
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --use-plru true"
            cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
            cmdLine += " --l3-assoc 32"  # One way per core
            cmdLine += " --check-pointing-rate 1000"

        elif tool == "viser32-regularplrucp100":
            assert options.cores == 32
            # build on viseroptregularplru32.
            # set a check point every 100 interations
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --use-plru true"
            cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
            cmdLine += " --l3-assoc 32"  # One way per core
            cmdLine += " --check-pointing-rate 100"

        elif tool == "viser32-regularplrucp10":
            assert options.cores == 32
            # build on viseroptregularplru32.
            # set a check point every 10 interations
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --use-plru true"
            cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
            cmdLine += " --l3-assoc 32"  # One way per core
            cmdLine += " --check-pointing-rate 10"

        elif tool == "viser32-regularplrucp1":
            assert options.cores == 32
            # build on viseroptregularplru32.
            # set a check point every 1 interation
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --use-plru true"
            cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
            cmdLine += " --l3-assoc 32"  # One way per core
            cmdLine += " --check-pointing-rate 1"

        elif tool == "restart8":
            # Built on top of pause.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --restart-at-failed-validations-or-deadlocks true"

        elif tool == "restart8-evictcleanlinesfirst":
            # Built on top of pause.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --restart-at-failed-validations-or-deadlocks true"
            cmdLine += " --evict-clean-line-first true"

        elif tool == "restart8-unopt":
            # use regular PLRU on L2 evictions
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --restart-at-failed-validations-or-deadlocks true"
            cmdLine += " --use-plru true"

        elif tool == "restart16-unopt":
            # use regular PLRU on L2 evictions
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --restart-at-failed-validations-or-deadlocks true"
            cmdLine += " --use-plru true"
            cmdLine += " --l3-size 33554432"  # 32 MB = 32 * 1024 * 1024

        elif tool == "restart32-unopt":
            assert options.cores == 32
            # use regular PLRU on L2 evictions
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --restart-at-failed-validations-or-deadlocks true"
            cmdLine += " --use-plru true"
            cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
            cmdLine += " --l3-assoc 32"  # One way per core

        elif tool == "restart8-unoptpseudo":
            # based on restartunopt, but not save events for actual region restart.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --restart-at-failed-validations-or-deadlocks false"
            cmdLine += " --false-restart true"
            cmdLine += " --use-plru true"

        elif tool == "restart16-unoptpseudo":
            # use regular PLRU on L2 evictions
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --restart-at-failed-validations-or-deadlocks false"
            cmdLine += " --false-restart true"
            cmdLine += " --use-plru true"
            cmdLine += " --l3-size 33554432"  # 32 MB = 32 * 1024 * 1024

        elif tool == "restart8-opt":
            # use modified PLRU on L2 evictions
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --restart-at-failed-validations-or-deadlocks true"
            cmdLine += " --use-plru true"
            cmdLine += " --evict-clean-line-first true"
            cmdLine += " --set-write-bits-in-l2 true"

        elif tool == "restart16-opt":
            # use modified PLRU on L2 evictions
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --restart-at-failed-validations-or-deadlocks true"
            cmdLine += " --use-plru true"
            cmdLine += " --evict-clean-line-first true"
            cmdLine += " --set-write-bits-in-l2 true"
            cmdLine += " --l3-size 33554432"  # 32 MB = 32 * 1024 * 1024

        elif tool == "restart32-opt":
            # use modified PLRU on L2 evictions
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --restart-at-failed-validations-or-deadlocks true"
            cmdLine += " --use-plru true"
            cmdLine += " --evict-clean-line-first true"
            cmdLine += " --set-write-bits-in-l2 true"
            cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
            cmdLine += " --l3-assoc 32"  # One way per core

        elif tool == "restart-optpseudo":
            # based on restartopt, but not save events for actual region restart.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --restart-at-failed-validations-or-deadlocks false"
            cmdLine += " --false-restart true"
            cmdLine += " --use-plru true"
            cmdLine += " --evict-clean-line-first true"
            cmdLine += " --set-write-bits-in-l2 true"

        elif tool == "restart16-optpseudo":
            # based on restartopt, but not save events for actual region restart.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --restart-at-failed-validations-or-deadlocks false"
            cmdLine += " --false-restart true"
            cmdLine += " --use-plru true"
            cmdLine += " --evict-clean-line-first true"
            cmdLine += " --set-write-bits-in-l2 true"
            cmdLine += " --l3-size 33554432"  # 32 MB = 32 * 1024 * 1024

        elif tool == "restart32-optpseudo":
            # based on restartopt, but not save events for actual region restart.
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --restart-at-failed-validations-or-deadlocks false"
            cmdLine += " --false-restart true"
            cmdLine += " --use-plru true"
            cmdLine += " --evict-clean-line-first true"
            cmdLine += " --set-write-bits-in-l2 true"
            cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
            cmdLine += " --l3-assoc 32"  # One way per core

        elif tool == "restart8-unopt4assoc":
            # use regular PLRU on L2 evictions
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --restart-at-failed-validations-or-deadlocks true"
            cmdLine += " --use-plru true"
            cmdLine += " --l1-assoc 4"
            cmdLine += " --l2-assoc 4"

        elif tool == "restart8-opt4assoc":
            # use modified PLRU on L2 evictions
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --restart-at-failed-validations-or-deadlocks true"
            cmdLine += " --use-plru true"
            cmdLine += " --evict-clean-line-first true"
            cmdLine += " --set-write-bits-in-l2 true"
            cmdLine += " --l1-assoc 4"
            cmdLine += " --l2-assoc 4"

        elif tool == "restart8-unopt2assoc":
            # use regular PLRU on L2 evictions
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --restart-at-failed-validations-or-deadlocks true"
            cmdLine += " --use-plru true"
            cmdLine += " --l1-assoc 2"
            cmdLine += " --l2-assoc 2"

        elif tool == "restart8-opt2assoc":
            # use modified PLRU on L2 evictions
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --restart-at-failed-validations-or-deadlocks true"
            cmdLine += " --use-plru true"
            cmdLine += " --evict-clean-line-first true"
            cmdLine += " --set-write-bits-in-l2 true"
            cmdLine += " --l1-assoc 2"
            cmdLine += " --l2-assoc 2"

        elif tool == "restart8-unopt16assoc":
            # use regular PLRU on L2 evictions
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --restart-at-failed-validations-or-deadlocks true"
            cmdLine += " --use-plru true"
            cmdLine += " --l1-assoc 16"
            cmdLine += " --l2-assoc 16"

        elif tool == "restart8-opt16assoc":
            # use modified PLRU on L2 evictions
            cmdLine += " --always-invalidate-read-only-lines false"
            cmdLine += " --invalidate-written-lines-only-after-version-check" \
                " true"
            cmdLine += " --special-invalid-state true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --use-aim-cache true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-validating-read-lines true"
            cmdLine += " --ignore-fetching-read-bits true"
            cmdLine += " --ignore-fetching-write-bits true"
            cmdLine += " --pause-cores-at-conflicts true"
            cmdLine += " --restart-at-failed-validations-or-deadlocks true"
            cmdLine += " --use-plru true"
            cmdLine += " --evict-clean-line-first true"
            cmdLine += " --set-write-bits-in-l2 true"
            cmdLine += " --l1-assoc 16"
            cmdLine += " --l2-assoc 16"

        else:
            assert False

        if Benchmark.isHTTPDBenchmark(bench):
            cmdLine += " --is-httpd true"

        if options.verbose >= 2 or options.printOnly:
            print(RunTask.__outputPrefix() + cmdLine)
        if not options.printOnly:
            RunTask.pauseIDsList.append(subprocess.Popen(cmdLine, shell=True))

    @staticmethod
    def __startRCCSISimulator(options, bench, size, trial, tool):
        cmdLine = RunTask.__addJVMArgs(options)
        cmdLine += (RunTask.RCCSISIM_CLASSPATH + " --tosim-fifo " + bench + "." +
                    RunTask.FIFO_PREFIX + tool + " --sim-mode rccsi")
        cmdLine += RunTask.__addCommonSimulatorArgs(options, bench)
        # Pass whether the backend needs to execute in lockstep with the
        # Pintool
        if options.lockstep:
            cmdLine += " --lockstep true"
        else:
            cmdLine += " --lockstep false"

        statsFile = (RunTask.getOutputPath(options, bench, size, trial) + RunTask.FILE_SEP + tool +
                     "-stats.py")
        cmdLine += " --stats-file " + statsFile

        if tool == "rccsi8-unopt":
            # Base configuration for RCC-SI.
            # This is the basic design, where we invalidate all private cache
            # lines at every region boundary. The global reader information is
            # cleared from LLC lines using epochs.
            pass

        elif tool == "rccsi8-clearreadersfromllc":
            # Builds on rccsiunopt.
            # This is the basic design, where we invalidate all private cache
            # lines at every region boundary. The global reader information is
            # cleared from LLC lines by iterating over LLC lines.
            cmdLine += " --clear-readers-llc true"

        elif tool == "rccsi8-usereadonlylineopt":
            # Builds on rccsiunopt.
            cmdLine += " --read-only-line-opt true"

        elif tool == "rccsi8-uselastwriteropt":
            # Builds on rccsiusereadonlylineopt.
            cmdLine += " --read-only-line-opt true"
            cmdLine += " --last-writer-opt true"

        elif tool == "rccsi8-usebloomfilter":
            # Builds on rccsiusereadonlylineopt.
            cmdLine += " --read-only-line-opt true"
            cmdLine += " --last-writer-opt true"
            cmdLine += " --use-bloom-filter true"

        elif tool == "rccsi8-deferwritebacks":
            # Builds on rccsibloomfilter.
            cmdLine += " --read-only-line-opt true"
            cmdLine += " --last-writer-opt true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --defer-write-backs true"

        elif tool == "rccsi8-skipreadvalidation":
            # Builds on rccsideferwritebacks.
            cmdLine += " --read-only-line-opt true"
            cmdLine += " --last-writer-opt true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-read-validation true"

        elif tool == "rccsi8":
            # Alias for rccsiskipreadvalidation.
            cmdLine += " --read-only-line-opt true"
            cmdLine += " --last-writer-opt true"
            cmdLine += " --use-bloom-filter true"
            cmdLine += " --defer-write-backs true"
            cmdLine += " --skip-read-validation true"

        elif tool == "rccsi16":
            assert options.pinThreads == 16
            # RCC-SI with all optimizations.
            cmdLine += " --l3-size 33554432"  # 32 MB = 32 * 1024 * 1024
            cmdLine += " --defer-write-backs true"

        elif tool == "rccsi32":
            assert options.pinThreads == 32
            # RCC-SI with all optimizations.
            cmdLine += " --l3-size 67108864"  # 64 MB = 64 * 1024 * 1024
            cmdLine += " --l3-assoc 32"  # One way per core
            cmdLine += " --defer-write-backs true"

        else:
            assert False

        if options.verbose >= 2 or options.printOnly:
            print(RunTask.__outputPrefix() + cmdLine)
        if not options.printOnly:
            RunTask.rccsiIDsList.append(subprocess.Popen(cmdLine, shell=True))

    @staticmethod
    def __startServer(options, bench):
        if bench == "httpd":
            cmdLine = RunTask.HTTPD_START
            rootPath = RunTask.HTTPD_ROOT
        elif bench == "mysqld":
            cmdLine = RunTask.MYSQLD_START
            rootPath = RunTask.MYSQLD_ROOT

        if options.verbose >= 2 or options.printOnly:
            print(RunTask.__outputPrefix() + cmdLine)

        if not options.printOnly:
            subprocess.Popen(cmdLine, shell=True)
            time.sleep(1)
            proc1 = subprocess.Popen(['ps', 'ax'], stdout=subprocess.PIPE)
            proc2 = subprocess.Popen(['grep', bench],
                                     stdin=proc1.stdout,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
            # Allow proc1 to receive a SIGPIPE if proc2 exits.
            proc1.stdout.close()
            out, _ = proc2.communicate()
            for line in out.splitlines():
                if rootPath in line.decode("utf-8"):
                    print(line)
                    pid = int(line.split(None, 1)[0])
                    if pid > RunTask.httpdID:
                        RunTask.httpdID = pid
            print("serverId:", RunTask.httpdID)

    @staticmethod
    def __writeHttpdPidFile(options):
        if not options.printOnly:
            f = open(RunTask.HTTPD_PID_FILE, 'w')
            time.sleep(1)
            proc1 = subprocess.Popen(['ps', 'ax'], stdout=subprocess.PIPE)
            proc2 = subprocess.Popen(['grep', 'httpd'],
                                     stdin=proc1.stdout,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
            # Allow proc1 to receive a SIGPIPE if proc2 exits.
            proc1.stdout.close()
            out, _ = proc2.communicate()
            for line in out.splitlines():
                if RunTask.HTTPD_ROOT in line.decode("utf-8"):
                    print(line)
                    pid = int(line.split(None, 1)[0])
                    if pid > RunTask.httpdID:
                        RunTask.httpdID = pid
            print("httpdId:", RunTask.httpdID)
            f.write(str(RunTask.httpdID))

    @staticmethod
    def __stopServer(options, bench):
        if options.attachPid:
            if bench == "httpd":
                cmdLine = RunTask.HTTPD_STOP
            elif bench == "mysqld":
                cmdLine = RunTask.MYSQLD_STOP
        else:
            if bench == "httpd":
                cmdLine = RunTask.HTTPD_DEBUG_STOP
            elif bench == "mysqld":
                cmdLine = RunTask.MYSQLD_STOP
            elif bench == "memcached":
                cmdLine = RunTask.MEMCACHED_STOP

        if options.verbose >= 2 or options.printOnly:
            print(RunTask.__outputPrefix() + cmdLine)

        if not options.printOnly:
            pid = subprocess.Popen(cmdLine, shell=True)
            while pid.poll() is None:
                time.sleep(5)

    @staticmethod
    def __startClients(options, workload, bench):
        clients = options.cores
        if workload == 'test':
            if bench == "httpd":
                size = int((65536 / clients) + 1)  # 64k requests in total
            elif bench == "mysqld":
                size = int((128 / clients) + 1)  # 128 requests in total
            elif bench == "memcached":
                size = int(64 / clients)  # 64 requests in total

        elif workload == 'simsmall':
            if bench == "httpd":
                size = int((65536 * 2 / clients) + 1)  # 128k requests in total
            elif bench == "mysqld":
                size = int((256 / clients) + 1)  # 256 requests in total
            elif bench == "memcached":
                size = int(4096 / clients)  # 4k requests in total

        elif workload == 'simmedium':
            if bench == "httpd":
                size = int((65536 * 4 / clients) + 1)  # 256k requests in total
            elif bench == "mysqld":
                size = int((512 / clients) + 1)  # 512 requests in total
            elif bench == "memcached":
                size = int(65536 / clients)  # 4k requests in total

        if bench == "memcached":
            cmdLine = RunTask.MEMCACHED_CLIENT0 + " " + str(clients) + " " + str(size)
            if options.verbose >= 2 or options.printOnly:
                print(RunTask.__outputPrefix() + cmdLine)
            if not options.printOnly:
                RunTask.httpClientIDsList.append(subprocess.Popen(cmdLine, shell=True))
        else:

            for _ in range(0, clients // 2):
                if bench == "httpd":
                    cmdLine = RunTask.HTTP_CLIENT0 + " " + str(size)
                elif bench == "mysqld":
                    cmdLine = RunTask.MYSQL_CLIENT0 + " " + str(size)

                if options.verbose >= 2 or options.printOnly:
                    print(RunTask.__outputPrefix() + cmdLine)
                if not options.printOnly:
                    RunTask.httpClientIDsList.append(subprocess.Popen(cmdLine, shell=True))

                if bench == "httpd":
                    cmdLine = RunTask.HTTP_CLIENT1 + " " + str(size)
                elif bench == "mysqld":
                    cmdLine = RunTask.MYSQL_CLIENT1 + " " + str(size)

                if options.verbose >= 2 or options.printOnly:
                    print(RunTask.__outputPrefix() + cmdLine)
                if not options.printOnly:
                    RunTask.httpClientIDsList.append(subprocess.Popen(cmdLine, shell=True))

    @staticmethod
    def __checkClients():
        for pid in RunTask.httpClientIDsList:
            # print("check pid: ", pid.pid)
            if pid.poll() is None:
                return False
        return True

    @staticmethod
    def __isTerminated(options):
        assert options.processPintool(), ("Pintool is expected to be run" +
                                          "along with the simulators.")
        for pinID in RunTask.pinIDsList:
            if pinID.poll() is None:
                return False

            if options.processMESISim():
                for mesiID in RunTask.mesiIDsList:
                    if mesiID.poll() is None:
                        return False

            if options.processViserSim():
                for viserID in RunTask.viserIDsList:
                    if viserID.poll() is None:
                        return False

            if options.processPauseSim():
                for pauseID in RunTask.pauseIDsList:
                    if pauseID.poll() is None:
                        return False

            if options.processRCCSISim():
                for rccsiID in RunTask.rccsiIDsList:
                    if rccsiID.poll() is None:
                        return False

        return True

    @staticmethod
    def createRerunFile(options):
        cwd = os.getcwd()
        os.chdir(options.getExpOutputDir())
        try:
            options.createRerunFile()
        finally:
            os.chdir(cwd)
