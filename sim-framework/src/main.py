#!/usr/bin/env python

import sys

from parser.cmdline import CmdLine
from options.options import Options
from tasks import tasks


def main():
    _options = Options(sys.argv)
    _cmdparser = CmdLine()
    _cmdparser.parse(_options)

    tasks.runAllTasks(_options)


if __name__ == "__main__":
    main()
