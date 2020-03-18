from options.constants import Constants
from tasks.collecttask import CollectTask
from tasks.producttask import ProductTask
from tasks.synctask import SyncTask


class ResultTask(Constants):
    """Collect results and generate plots."""

    @staticmethod
    def __outputPrefix():
        return "[result] "

    @staticmethod
    def __printTaskInfoStart(options):
        if options.verbose >= 1:
            print("\n" + ResultTask.__outputPrefix() + "Executing result task...")

    @staticmethod
    def __printTaskInfoEnd(options):
        if options.verbose >= 1:
            print(ResultTask.__outputPrefix() + "Done executing result task...\n")

    @staticmethod
    def resultTask(options):
        """Results are generated in the same machine where the simulators were executed."""
        ResultTask.__printTaskInfoStart(options)
        # resultsSet contains all parsed results
        resultsSet = CollectTask.collectTask(options)
        assert resultsSet
        CollectTask.postProcessResults(options, resultsSet)
        ProductTask.productTask(options, resultsSet)

        # if sameMachine is False, then copy the output and the products directory to the source
        # machine specified in config.ini
        if not options.sameMachine:
            if "run" not in options.getTasksTuple():
                # Leave out copying if "run" is included since there can be large scratch files
                SyncTask.syncOutputDir(options)
            SyncTask.syncProductsDir(options)

        ResultTask.__printTaskInfoEnd(options)
