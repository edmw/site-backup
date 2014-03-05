# coding: utf-8

import sys, os, os.path
import subprocess
import collections

from email import message_from_string
from email.mime.text import MIMEText

Sender = collections.namedtuple('Sender', ['mail'])
Recipient = collections.namedtuple('Recipient', ['mail', 'certificate'])

class MailerError(Exception):
    def __init__(self, mailer, message):
        super(MailerError, self).__init__()
        self.mailer = mailer
        self.message = message
    def __str__(self):
        return "MailerError(%s)" % repr(self.message)

class Mailer(object):

    def __init__(self):
        self.sender = None
        self.recipients = []

    def __str__(self):
        return "Mailer(%s, %s)" % (str(self.sender), str(self.recipients))

    def recipients_as_string(self):
        return ", ".join([r.mail for r in self.recipients])

    def setSender(self, mail):
        self.sender = Sender(mail)

    def addRecipient(self, mail, certificate=None):
        self.recipients.append(Recipient(mail, certificate))

    def _send(self, mail, recipients):
        # set mail headers
        mail['To'] = ",".join([r.mail for r in recipients])

        # send mail using sendmail
        p = subprocess.Popen(
            ["/usr/sbin/sendmail", "-oi", "-t"],
            stdin=subprocess.PIPE,
        )
        p.communicate(mail.as_string())

        print mail.as_string()

    def _send_encrypted(self, mail, recipient):
        certificate = recipient.certificate

        if os.path.isfile(certificate):
            # encrypt mail using openssl
            p = subprocess.Popen(
                [
                    "/usr/bin/openssl",
                    "smime",
                    "-encrypt",
                    "-des3",
                    certificate
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            (stdoutdata, stderrdata) = p.communicate(mail.as_string())

            if not p.returncode == 0:
                message = "RC=%d" % p.returncode
                if stderrdata:
                    message = str(stderrdata).strip()
                raise MailerError(self, message) 

            mail = message_from_string(stdoutdata)

            self._send(mail, [recipient])

        else:
            raise MailerError(self,
                "certificate for %s not found" % str(recipient)
            )

    def sendMail(self, text, subject):
        mail = MIMEText(text)
        mail['From'] = self.sender.mail
        mail['Subject'] = subject

        # send separate mail to recipients with encryption
        for recipient in [r for r in self.recipients if r.certificate]:
            self._send_encrypted(mail, recipient)

        # send mail to recipients without encryption
        self._send(mail, [r for r in self.recipients if not r.certificate])
