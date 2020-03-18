from options.constants import Constants
from result.result import Result
from result.resultset import ResultSet
from tasks.collecttask import CollectTask
from tasks.mcpattask import McPATTask


class ProductTask(Constants):

    @staticmethod
    def __outputPrefix():
        return "[product] "

    @staticmethod
    def __printTaskInfoStart(options):
        if options.verbose >= 1:
            print("\n" + ProductTask.__outputPrefix() + "Executing product task...")

    @staticmethod
    def __printTaskInfoEnd(options):
        if options.verbose >= 1:
            print(ProductTask.__outputPrefix() + "Done executing product task...\n")

    @staticmethod
    def productTask(options, resultsSet):
        ProductTask.__printTaskInfoStart(options)
        # Copy resultsSet so as to have a backup
        workingRS = resultsSet.copy()
        # Inflate the result set so that each simulator config result includes all the stats keys
        pintoolRS = ResultSet.limitToPintoolResults(workingRS)
        simRS = ResultSet.limitToSimulatorResults(workingRS)
        simRS = ResultSet.extractGlobalStats(simRS)
        li_allKeys = ResultSet.getAllKeys(simRS)
        simRS = ResultSet.inflateResultSetWithKeys(simRS, li_allKeys)
        inflatedRS = []
        inflatedRS.extend(pintoolRS)
        inflatedRS.extend(simRS)

        res = Result(options)
        res.generateResult(inflatedRS)

        if options.generateEnergyStats:
            mp = McPATTask(options)
            mp.parseXml(workingRS)
            mp.runMcPAT()
            mpResultsSet = CollectTask.collectMcpatResults(options, inflatedRS)
            res.generateEnergyResult(mpResultsSet)

        ProductTask.__printTaskInfoEnd(options)
