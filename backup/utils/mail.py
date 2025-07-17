# coding: utf-8

import subprocess
from collections import namedtuple
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from enum import IntEnum

from backup.utils import COMMASPACE, LF, SPACER


class Priority(IntEnum):
    HIGHEST = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    LOWEST = 5


class Attachment(namedtuple("Attachment", ["name", "mimetype", "data"])):
    __slots__ = ()


def sendMail(
    send_to: list[str],
    send_from: str,
    subject: str,
    text: str,
    attachments: list[Attachment] | None,
    priority: Priority = Priority.NORMAL,
) -> None:
    if attachments:
        mail = MIMEMultipart()
        part = MIMEText(text, "plain", "utf-8")
        mail.attach(part)
        for attachment in attachments:
            if attachment.mimetype == "text/html":
                part = MIMEText(attachment.data, "html", "utf-8")
            elif attachment.mimetype == "application/pdf":
                part = MIMEApplication(attachment.data, "pdf", Name=attachment.name)
            else:
                part = MIMEApplication(attachment.data, Name=attachment.name)
            part["Content-Disposition"] = f'attachment; filename="{attachment.name}"'
            mail.attach(part)
    else:
        mail = MIMEText(text, "plain", "utf-8")

    mail["Subject"] = str(Header(subject, "utf-8"))
    mail["To"] = COMMASPACE.join(send_to)
    mail["From"] = send_from
    mail["Date"] = formatdate(localtime=True)
    if priority is not Priority.NORMAL:
        mail["X-Priority"] = str(int(priority))

    process = subprocess.Popen(
        ["/usr/sbin/sendmail", "-oi", "-t"],
        stdin=subprocess.PIPE,
    )
    process.communicate(mail.as_bytes())


Sender = namedtuple("Sender", ["mail"])
Recipient = namedtuple("Recipient", ["mail"])


class MailerError(Exception):
    def __init__(self, mailer, message):
        super(MailerError, self).__init__()
        self.mailer = mailer
        self.message = message

    def __str__(self):
        return f"MailerError({self.message!r})"


class Mailer(object):

    def __init__(self):
        self.sender = None
        self.recipients = []

    def __str__(self):
        str_sender = self.sender.mail if self.sender else "None"
        str_recipients = COMMASPACE.join(
            recipient.mail for recipient in self.recipients
        )
        str_template = "Mailer to {1} from {0}"
        return str_template.format(str_sender, str_recipients)

    def __format_value__(self):
        str_sender = SPACER + str(self.sender) if self.sender else SPACER + "None"
        str_recipients = LF.join(
            SPACER + str(recipient) for recipient in self.recipients
        )
        str_template = "Mailer(" + LF + "{0}," + LF + "{1}" + LF + ")"
        return str_template.format(str_sender, str_recipients)

    def setSender(self, sender):
        self.sender = sender

    def addRecipient(self, recipient):
        self.recipients.append(recipient)

    def serviceable(self):
        return self.sender is not None and len(self.recipients) > 0

    def send(self, subject, text, attachments, priority=Priority.NORMAL):
        mail_from = self.sender.mail if self.sender else None
        if mail_from is None:
            raise MailerError(self, "No sender specified!")
        mail_to = [r.mail for r in self.recipients] or None
        if mail_to is None:
            raise MailerError(self, "No recipient specified!")
        sendMail(mail_to, mail_from, subject, text, attachments, priority)
