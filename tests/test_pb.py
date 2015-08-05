__author__ = 'marco'

import unittest

from messages_pb2 import MasterInfo, Address


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
        minfo.port = 1234
        minfo.ip = 987654
        minfo.id = 'dontcare'
        minfo.version = "0.24.0"
        address = minfo.address
        address.ip = "10.10.1.22"
        address.port = 5050
        ss = minfo.SerializeToString()

        actual = MasterInfo()
        actual.ParseFromString(ss)
        self.assertEqual('0.24.0', actual.version)
        self.assertEqual('10.10.1.22', actual.address.ip)
        self.assertEqual(5050, actual.address.port)
