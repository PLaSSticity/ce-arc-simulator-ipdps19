"""This module controls running all the tasks specified in the experiment."""


def runAllTasks(options):
    """Run all the tasks.  The order is pre-determined and important."""
    tasksTuple = options.getTasksTuple()
    if "clean" in tasksTuple:
        from tasks.cleantask import CleanTask
        CleanTask.cleanTask(options)

    if "sync" in tasksTuple:
        from tasks.synctask import SyncTask
        SyncTask.syncTask(options)

    if "build" in tasksTuple:
        from tasks.buildtask import BuildTask
        BuildTask.buildTask(options)

    if "run" in tasksTuple:
        from tasks.runtask import RunTask
        RunTask.runTask(options)

    if "result" in tasksTuple:
        from tasks.resulttask import ResultTask
        ResultTask.resultTask(options)

    if "copy" in tasksTuple:
        from tasks.copytask import CopyTask
        CopyTask.copyTask(options)

    if "email" in tasksTuple:
        from tasks.emailtask import EmailTask
        EmailTask.emailTask(options)
