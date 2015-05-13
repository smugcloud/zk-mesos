__author__ = 'marco'

import unittest

from messages_pb2 import MasterInfo

class TestMessagesPb(unittest.TestCase):

    def testMasterInfo(self):
        minfo = MasterInfo()
        minfo.id = "foo"
        minfo.hostname = 'bar'
        minfo.ip = 23456789
        minfo.port = 5050
        ss = minfo.SerializeToString()

        actual = MasterInfo()
        actual.ParseFromString(ss)
        self.assertEqual('bar', actual.hostname)
