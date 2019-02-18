import sys
import traceback

from options.constants import Constants


def checkEnvVariables():
    # SB: These checks seem to be not working as intended
    if (Constants.PIN_ROOT is None or Constants.VS_PINTOOL_ROOT is None or
            Constants.PARSEC_ROOT is None or Constants.MESISIM_ROOT is None or
            Constants.VISERSIM_ROOT is None or Constants.VISER_EXP is None or
            Constants.RCCSISIM_ROOT is None):
        raiseError("One or more environment variables are not set.")


def raiseError(*args, stack=False):
    """Helper method to raise errors and exit.  stack is a ‘keyword-only’ argument, meaning that
    it can only be used as a keyword rather than a positional argument.
    """
    if stack:
        traceback.print_stack()
    stmt = "[error] "
    for s in args:
        stmt += s + " "
    sys.exit(stmt)


def isPintool(name):
    return "pintool" in name


def isMESIConfig(name):
    return "mesi" in name


def isViserConfig(name):
    # RZ: treat viseroptregularplru as a pause/restart config because I want
    # to generate graphs for its (estimated) costs of restarting a whole
    # program at exceptions.
    return ("viseroptregularplru" not in name) and ("viser" in name or "drf0" in name or
                                                    "arc" in name)


def isViserIdealAIMConfig(name):
    return isViserConfig(name) and "idealaim" in name


def isCEConfig(name):
    # Just "ce" may not work if it is a substring
    return "ce4" in name or "ce8" in name or "ce16" in name or "ce32" in name


def isCEConfigWithAIM(name):
    return isCEConfig(name) and ("-8Kaim" in name or "-16Kaim" in name or "-32Kaim" in name or
                                 "-64Kaim" in name)


def isCEConfigWithoutAIM(name):
    return isCEConfig(name) and not isCEConfigWithAIM(name)


def isPauseConfig(name):
    return "pause" in name or "restart" in name or "viseroptregularplru" in name


def isRCCSIConfig(name):
    return "rccsi" in name


def isSniperConfig(name):
    return "sniper" in name


def isSimulatorConfig(name):
    return (isMESIConfig(name) or isViserConfig(name) or isRCCSIConfig(name) or
            isPauseConfig(name) or isCEConfig(name))


def isOnlyCEConfigNoAIM(toolTuple):
    """This is to detect cases where only MESI or CE w/o AIM configs are being tested."""
    present = True
    for t in toolTuple:
        if isPintool(t):
            continue
        if isViserConfig(t) or isCEConfigWithAIM(t):
            present = False
    return present


# Sometimes we mix several configurations across different core counts, hence the options.cores
# value cannot be truested.
def getARCAIMLineSize(tool):  # Bytes
    size = 0
    if "viser4" in tool:
        size = 60
    elif "viser8" in tool:
        size = 100
    elif "viser16" in tool:
        size = 172
    elif "viser32" in tool:
        size = 308
    else:
        raiseError("unhandled core count")
    return size


# Sometimes we mix several configurations across different core counts, hence the options.cores
# value cannot be truested.
def getCEAIMLineSize(tool):  # Bytes
    size = 0
    if "ce4" in tool:
        size = 56
    elif "ce8" in tool:
        size = 96
    elif "ce16" in tool:
        size = 168
    elif "ce32" in tool:
        size = 304
    else:
        raiseError("unhandled core count")
    return size
