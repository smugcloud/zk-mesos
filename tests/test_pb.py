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

    def testVersionIpAddress(self):
        minfo = MasterInfo()

        # Initialize required fields
        minfo.ip = 23345
        minfo.id = 'dontcare'
        minfo.version = "0.24.0"
        minfo.ip_address = '10.1.100.5'
        minfo.port = 5050
        ss = minfo.SerializeToString()

        actual = MasterInfo()
        actual.ParseFromString(ss)
        self.assertEqual('0.24.0', actual.version)
        self.assertEqual('10.1.100.5', actual.ip_address)
