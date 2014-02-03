# coding: utf-8

import sys, os, os.path
import re

import time

LF = '\n'
LFLF = '\n\n'
SPACE = ' '

def timestamp():
  from datetime import datetime
  return datetime.now().strftime('%Y%m%d%H%M%S')

def slugify(value):
  import unicodedata
  value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
  value = re.sub('[^\w\s-]', '', value).strip().lower()
  value = re.sub('[-\s]+', '-', value)
  return value

def formatkv(kv, title=None):
  out = list()
  if title:
  	out.append("%s" % title)
  for (k, v) in kv:
    out.append("    %s: %s" % (k, v))
  return "\n".join(out)
