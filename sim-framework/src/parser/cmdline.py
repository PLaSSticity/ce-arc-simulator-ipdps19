import argparse
import ast

from options import util
from options.benchmarks import Benchmark
from options.projects import Project


class CmdLine:
    """Helper class to parser command line arguments and perform limited sanity checks."""

    allowedTasks = [
        "clean",  # Kill existing related processes that are running
        "sync",  # Sync sources from the source machine
        "build",
        "run",
        "result",
        "email"
    ]

    allowedSizes = ["test", "simdev", "simsmall", "simmedium", "simlarge", "native"]

    # The suggested naming convention is <tool><num_cores>-<options>. Abiding to this will
    #  help with matching tool names.
    allowedTools = [
        "pintool",
        "mesi4",
        "mesi8",
        "mesi16",
        "mesi32",  # 32-way LLC
        "ce4",
        "ce4-32Kaim",
        # "ce4-16Kaim",
        "ce8",
        "ce8-32Kaim",
        "ce8-16Kaim",
        "ce16",
        "ce16-32Kaim",
        "ce16-16Kaim",
        "ce32",  # 32-way LLC
        "ce32-32MBLLC",
        "ce32-morecache",
        "ce32-32Kaim",
        "ce32-64Kaim",
        # "ce32-16Kaim",
        "mesi8-regularplru",
        "mesi16-regularplru",
        "mesi32-regularplru",
        "viser4-16Kaim",
        "viser4-32Kaim",
        "viser4-idealaim",
        "viser8-unopt",
        "viser8-readonlyopt",
        "viser8-lastwriteropt",
        "viser8-updatewrites",
        "viser8-untouchedlinesopt",
        "viser8-specialinvalid",
        "viser8-bloomfilter",
        "viser8-bloominvalid",
        "viser8-onebloom",
        "viser8-selfinvalidationopt",
        "viser8-deferwritebacks",
        "viser8-deferwritebacksprecise",
        "viser8-skipvalidatingreadlines",
        "viser8-ignorefetchingreadbits",
        "viser8-32Kaim",
        "viser8-fetchwritebits",
        "viser8-noatomicupdates",
        "viser8-ignorefetchwritebits",
        "viser8-nodefer",
        "viser8-precisedefer",
        "viser8-8Kaim",
        "viser8-16Kaim",
        "viser16-32Kaim",
        "viser16-16Kaim",
        "viser32-32Kaim",  # 32-way LLC
        # "viser32-16Kaim",
        "viser32-64Kaim",  # Just for testing
        "viser8-idealaim",
        "viser16-idealaim",
        "viser32-idealaim",
        "viser8-clearaimatregionboundaries",
        "viser8-ignoredeferredlinesduringreadvalidation",
        "viser8-userfrs",
        "viser8-evictnonwarlinefirst",
        "viser8-evictcleanlinefirst",
        "viser8-lru",
        "viser8-regularplru",
        "viser16-regularplru",
        "viser32-optregularplru",
        "viser32-regularplrucp1k",
        "viser32-regularplrucp100",
        "viser32-regularplrucp10",
        "viser32-regularplrucp1",
        "viser8-modifiedplru",
        "viser8-plruatomicasboundary",
        "viser8-plruatomicasregular",
        "rccsi8-unopt",
        "rccsi8-clearreadersfromllc",
        "rccsi8-usereadonlylineopt",
        "rccsi8-uselastwriteropt",
        "rccsi8-usebloomfilter",
        "rccsi8-deferwritebacks",
        "rccsi8-skipreadvalidation",
        "rccsi8",
        "rccsi16",
        "rccsi32",
        # SB: I am not sure about the correct renaming of the following tools.
        "pause8",
        "pause16",
        "pause32",
        "restart8",
        "restart8-waitatreads",
        "restart8-evictcleanlinesfirst",
        "restart8-unopt",
        "restart16-unopt",
        "restart32-unopt",
        "restart8-unoptpseudo",
        "restart16-unoptpseudo",
        "restart8-opt",
        "restart16-opt",
        "restart32-opt",
        "restart8-optpseudo",
        "restart16-optpseudo",
        "restart32-optpseudo",
        "restart8-unopt4assoc",
        "restart8-opt4assoc",
        "restart8-unopt2assoc",
        "restart8-opt2assoc",
        "restart8-unopt16assoc",
        "restart8-opt16assoc",
        "drf0unopt",
        "drf0bloomfilter",
        "drf0deferwritebacks",
        "drf0partialinvalid",
        "drf0opt",
        "barcunopt",
        "barcpartialinvalid",
        "barcpartialinvalidwp",
        "barcbloomfilter",
        "barcbloomfilter1008bits",
        "barcdeferwritebacks",
        "barcopt",
        "barcoptlru",
        "sarc",
        "sarcselfinvalidatrelease",
        "barcunoptspecialhandleatomics",
        "barcoptspecialhandleatomics",
        "sarcwp",
        "barcoptwp",
        "barcbloomfilter1008bitswp",
        "barcoptmdplru",
        "sarcbloomfilter",
        "drf0bloomfilter1008bits",
        "sniper"
    ]

    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description='Command line options for running experiments',
            conflict_handler='error',  # allow_abbrev=False
        )

        # Hack to get rid of main.py from the help message
        self.parser.prog = "arc"

        self.parser.add_argument("--tools", help="tools to run", required=True)
        self.parser.add_argument("--tasks", help="tasks to execute", default="build")
        self.parser.add_argument(
            "--workload",
            help="workload size",
            default="simsmall",
            choices=["test", "simdev", "simsmall", "simmedium", "simlarge", "native"])
        self.parser.add_argument("--trials", help="number of trials", type=int, default=1)
        self.parser.add_argument("--bench",
                                 help="list of benchmarks, or all,"
                                 " or none",
                                 default="none")
        self.parser.add_argument("--pinThreads",
                                 help="number of PARSEC benchmark threads",
                                 type=int,
                                 default=8)
        self.parser.add_argument("--pid",
                                 help="the pid of application process to be attatched",
                                 type=int,
                                 default=0)
        self.parser.add_argument("--cores",
                                 help="number of cores in the simulator",
                                 type=int,
                                 default=8)
        self.parser.add_argument("--outputDir",
                                 help="output directory relative to"
                                 " ~/exp-output",
                                 default="viser-temp")
        self.parser.add_argument("--verbose", help="verbosity level", default=1, type=int)
        self.parser.add_argument(
            "--printOnly",
            help="just print the constructed commands, will not execute",
            default=False,
            choices=[False, True],
            # type bool causes problems
            type=ast.literal_eval)
        self.parser.add_argument("--assert",
                                 help="enable running Java "
                                 "asserts in the backend simulator(s)",
                                 default=False,
                                 type=ast.literal_eval,
                                 choices=[False, True],
                                 required=True,
                                 dest="jassert")
        self.parser.add_argument("--xassert",
                                 help="enable running xasserts "
                                 "in the backend simulator(s)",
                                 default=False,
                                 type=ast.literal_eval,
                                 choices=[False, True],
                                 required=True)
        self.parser.add_argument("--period", help="run xasserts periodically", type=int, default=1)
        self.parser.add_argument("--roiOnly",
                                 help="Should simulation be "
                                 "limited only to the ROI?",
                                 default=True,
                                 choices=[False, True],
                                 type=ast.literal_eval)
        # Is the framework is running on the SOURCE machine?
        self.parser.add_argument("--sameMachine",
                                 help=argparse.SUPPRESS,
                                 type=ast.literal_eval,
                                 choices=[False, True],
                                 required=True)
        self.parser.add_argument("--project", help="project name", default="none")
        self.parser.add_argument("--lockstep",
                                 help="execute the Pintool and the backend in "
                                 "lockstep",
                                 default=False,
                                 choices=[False, True],
                                 type=ast.literal_eval)
        self.parser.add_argument("--siteTracking",
                                 help="track site info for each event ",
                                 default=False,
                                 choices=[False, True],
                                 type=ast.literal_eval)
        self.parser.add_argument("--attachPid",
                                 help="apply Pin by attaching it to an already"
                                 " running process",
                                 default=False,
                                 choices=[False, True],
                                 type=ast.literal_eval)
        self.parser.add_argument("--generateTrace",
                                 help="generate a trace file mostly for "
                                 "debugging purposes",
                                 default=False,
                                 choices=[False, True],
                                 type=ast.literal_eval)
        self.parser.add_argument("--pinTool",
                                 help="choose a pinTool to use (viser or viserST)",
                                 default="viser",
                                 choices=["viser", "viserST"])
        self.parser.add_argument("--confIndex",
                                 help=" the index (>=0) of the conflicting"
                                 " sites to validate with collision analysis ",
                                 type=int,
                                 default=-1)
        self.parser.add_argument("--parallelBenches",
                                 help=" the number (>=0) of the benchmarks"
                                 " allowed to run parallelly ",
                                 type=int,
                                 default=1)
        self.parser.add_argument("--generateEnergyStats",
                                 help="generate energy stats by McPAT",
                                 default=False,
                                 choices=[False, True],
                                 type=ast.literal_eval)

    def parse(self, options):
        # Check if environment variables are properly defined

        di_options = vars(self.parser.parse_args())
        options.setOptions(di_options)
        if options.verbose >= 2:
            options.printOptions()

        # Sanity checks
        if not Project.isSupportedProject(options.getProject()):
            util.raiseError("Invalid project: ", options.getProject())

        for t in options.getTasksTuple():
            # Allow an empty task, e.g., "clean,"
            if t not in CmdLine.allowedTasks and t:
                util.raiseError("Invalid task: ", t)

        for t in options.getToolsTuple():
            if t not in CmdLine.allowedTools:
                util.raiseError("Invalid tool: ", t)

        options.removeBenchDuplicates()

        for b in options.getBenchTuple():
            if (not Benchmark.isHTTPDBenchmark(b) and not Benchmark.isParsecBenchmark(b) and
                    not Benchmark.isSplash2xBenchmark(b)):
                util.raiseError("Invalid bench: ", b)

        if options.parallelBenches > len(options.getBenchTuple()) or options.parallelBenches < 1:
            util.raiseError("Invalid parallelBenches (should be within [1,benchNum]): ",
                            str(options.parallelBenches))

        for w in options.getWorkloadTuple():
            if w not in CmdLine.allowedSizes:
                util.raiseError("Invalid workload size: ", w)

        # if "run" is there in "tasks", then "tools" should have pintool and
        # at least one simulator
        if "run" in options.getTasksTuple():
            if "sniper" in options.getToolsTuple() and len(options.getToolsTuple()) > 1:
                util.raiseError("Sniper can be the only tool running!")
            if options.getSimulatorsTuple():
                if "pintool" not in options.getToolsTuple():
                    util.raiseError(
                        "The Pintool frontend is required to run the backend simulators.")

        # "Result" task requires bench and trials option
        if "result" in options.getTasksTuple():
            if not options.getBenchTuple():
                util.raiseError("No benchmark specified.")
            if options.trials == 0:
                util.raiseError("Number of trials unspecified.")
            if not options.getWorkloadTuple():
                util.raiseError("No workload size specified.")

        # Limited safety check for matching cores and configurations
        if "run" in options.getTasksTuple():
            if options.pinThreads == 16 or options.pinThreads == 32:
                for t in options.getToolsTuple():
                    if not util.isPintool(t) and not util.isSniperConfig(t):
                        if str(options.pinThreads) not in t:
                            util.raiseError("Check tool and threads combination: ", t,
                                            str(options.pinThreads))

        # # # SB: Need to polish this more
        # for t in options.getToolsTuple():
        #     if (("16" in t and options.pinThreads != 16) or
        #         ("32" in t and options.pinThreads != 32)):
        #         util.raiseError(("Check tool and threads combination: "), t,
        #                         str(options.pinThreads))

        # Lockstep execution only makes sense if there is at least one backend
        # along with the pintool
        if options.lockstep and not options.getSimulatorsTuple():
            util.raiseError("Lockstep execution only makes sense if there is at least one backend.")
