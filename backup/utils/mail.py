# coding: utf-8

import subprocess

from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from email.header import Header
from email.utils import COMMASPACE, formatdate


from enum import IntEnum

class Priority(IntEnum):
    HIGHEST = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    LOWEST = 5


from collections import namedtuple

class Attachment(namedtuple('Attachment', ['name', 'mimetype', 'data'])):
    __slots__ = ()


def sendMail(send_to, send_from, subject, text, attachments, priority=Priority.NORMAL):
    if attachments:
        mail = MIMEMultipart()
        part = MIMEText(text.encode('utf-8'), 'plain', 'utf-8')
        mail.attach(part)
        for attachment in attachments:
            if attachment.mimetype == 'text/html':
                part = MIMEText(attachment.data.encode('utf-8'), 'html', 'utf-8')
            elif attachment.mimetype == 'application/pdf':
                part = MIMEApplication(attachment.data, 'pdf', Name=attachment.name)
            else:
                part = MIMEApplication(attachment.data, Name=attachment.name)
            part['Content-Disposition'] = 'attachment; filename="{}"'.format(attachment.name)
            mail.attach(part)
    else:
        mail = MIMEText(text.encode('utf-8'), 'plain', 'utf-8')

    mail['Subject'] = Header(subject, 'utf-8')
    mail['To'] = COMMASPACE.join(send_to)
    mail['From'] = send_from
    mail['Date'] = formatdate(localtime=True)
    if priority is not Priority.NORMAL:
        mail['X-Priority'] = str(int(priority))

    process = subprocess.Popen(
        ["/usr/sbin/sendmail", "-oi", "-t"],
        stdin=subprocess.PIPE,
    )
    process.communicate(mail.as_bytes())
