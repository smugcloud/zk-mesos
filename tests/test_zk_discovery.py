__author__ = 'marco'

import socket
import unittest

from mesos import ZookeeperDiscoveryProtocolBuffer, ZookeeperDiscoveryJson


class TestZookeeperDiscovery(unittest.TestCase):
    def setUp(self):
        self.uri = 'zk://localhost:2181/mesos/test'
        self.zkd = ZookeeperDiscoveryProtocolBuffer(self.uri)
        self.assertIsNotNone(self.zkd)

    def test_uriparse(self):
        uri = 'zk://10.10.1.1:2181,10.10.0.81:2181/mesos/test/path'
        h, p = ZookeeperDiscoveryProtocolBuffer._parse_uri(uri)
        self.assertEqual('10.10.1.1:2181,10.10.0.81:2181', h)
        self.assertEqual('/mesos/test/path', p)

    def test_find_master(self):
        minfo = self.zkd.retrieve_leader()
        self.assertIsNotNone(minfo)
        self.assertEqual(socket.gethostname(), minfo.get('hostname'))
        self.assertIn(minfo.get('port'), xrange(5050, 5060))

    def test_get_http(self):
        url = self.zkd.get_master_url()
        self.assertIsNotNone(url)
        self.assertTrue(url.startswith('http://'))
        self.assertIsNotNone(self.zkd.get_leader_ip()[0])

class TestJsonZooKeeperDiscovery(unittest.TestCase):

    def setUp(self):
        self.uri = 'zk://localhost:2181/mesos/test'
        self.zkd = ZookeeperDiscoveryJson(self.uri)
        self.assertIsNotNone(self.zkd)

    def test_can_get_leader(self):
        self.assertIsNotNone(self.zkd.retrieve_leader())

    def test_can_parse_ip(self):
        self.assertEquals(socket.gethostname(), self.zkd.retrieve_leader()['hostname'])
