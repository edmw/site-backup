# coding: utf-8

import unittest, mock

from sitebackup import main

class TestMain(unittest.TestCase):
  
  def testHelp(self):
    with self.assertRaises(SystemExit) as context:
      result = main(["-h",])
    self.assertEqual(context.exception.code, 0)

if __name__ == '__main__':
    unittest.main()
