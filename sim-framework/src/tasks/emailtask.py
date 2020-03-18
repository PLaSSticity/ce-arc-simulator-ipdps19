import ast
import smtplib
import socket
from email.header import Header

from options import util
from options.constants import Constants


class EmailTask(Constants):

    @staticmethod
    def __outputPrefix():
        return "[email] "

    @staticmethod
    def __printTaskInfoStart(options):
        if options.verbose >= 1:
            print(EmailTask.__outputPrefix() + "Executing email task...")

    @staticmethod
    def __printTaskInfoEnd(options):
        if options.verbose >= 1:
            print(EmailTask.__outputPrefix() + "Done executing email task...")

    @staticmethod
    def emailTask(options):
        EmailTask.__printTaskInfoStart(options)
        str_emails = options.config.getEmails()
        # Construct message
        body = options.getExpCommand()
        try:
            # s = smtplib.SMTP("rain.cse.ohio-state.edu", 25, "localhost")
            s = smtplib.SMTP("localhost")
            for email in ast.literal_eval(str_emails):
                msg['Subject'] = Header(socket.gethostname() + ": Viser experiment is done",
                                        'utf-8')
                msg['Subject'] = Header(socket.gethostname() + ": Viser experiment is done",
                                        'utf-8')
                msg['From'] = "plass@cse.ohio-state.edu"
                msg['To'] = email
                s.send_message(msg)
            s.quit()
            EmailTask.__printTaskInfoEnd(options)
        except ConnectionRefusedError as e:
            util.raiseError(" Sending email failed..." + repr(e))
