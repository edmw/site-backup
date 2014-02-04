# coding: utf-8

import pytest, mock

from sitebackup import main

def testHelp():
    with pytest.raises(SystemExit) as exceptioninfo:
        result = main(["-h",])
    assert exceptioninfo.value.code == 0
