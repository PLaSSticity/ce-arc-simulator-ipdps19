import ast
import configparser
import os

from options import util
from options.constants import Constants


class Config(Constants):

    tup_allowedSyncKeys = ("SOURCE", "DEST", "RESULT")
    str_allowedEmailKey = "EMAIL"
    str_allowedUserKey = "USER"

    def __init__(self):
        cwd = os.getcwd()
        try:
            os.chdir(Config.VISER_EXP)
            if not os.path.exists(Config.CONFIG):
                util.raiseError("CONFIG file missing in ", Config.VISER_EXP, " directory.")

            self.config = configparser.ConfigParser()
            self.config.read(Config.CONFIG)
        finally:
            os.chdir(cwd)

    def getUser(self):
        if "USER" not in self.config:
            util.raiseError("CONFIG file does not contain USER section.")
        for key in self.config["USER"]:
            if key != Config.str_allowedUserKey.lower():
                util.raiseError("Invalid key in USER section in CONFIG file.")
        return self.config["USER"][key]

    def getEmails(self):
        if "EMAIL" not in self.config:
            util.raiseError("CONFIG file does not contain EMAIL section.")

        for key in self.config["EMAIL"]:
            if key != Config.str_allowedEmailKey.lower():
                util.raiseError("Invalid key in EMAIL section in CONFIG file.")

        return self.config["EMAIL"][key]

    def checkSyncBlock(self):
        if "SYNC" not in self.config:
            util.raiseError("CONFIG file does not contain SYNC section.")

        for key in self.config["SYNC"]:
            found = False
            for akey in Config.tup_allowedSyncKeys:
                if key.lower() == akey.lower():
                    found = True
            if not found:
                util.raiseError("Invalid key in SYNC section in CONFIG file.")

    def getSourceMachine(self):
        self.checkSyncBlock()
        str_sourceMachine = self.config["SYNC"]["SOURCE"]
        assert len(ast.literal_eval(str_sourceMachine)) == 1
        return ast.literal_eval(str_sourceMachine)[0]

    def getResultsMachine(self):
        self.checkSyncBlock()
        str_resultsMachine = self.config["SYNC"]["RESULT"]
        assert len(ast.literal_eval(str_resultsMachine)) == 1
        return ast.literal_eval(str_resultsMachine)[0]
