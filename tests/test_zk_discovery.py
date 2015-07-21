__author__ = 'marco'

import unittest

from mesos import ZookeeperDiscovery


class TestZookeeperDiscovery(unittest.TestCase):
    def setUp(self):
        self.uri = 'zk://localhost:2181/test/marco'
        self.zkd = ZookeeperDiscovery(self.uri)
        self.assertIsNotNone(self.zkd)

    def test_uriparse(self):
        uri = 'zk://10.10.1.1:2181,10.10.0.81:2181/mesos/test/path'
        h, p = ZookeeperDiscovery._parse_uri(uri)
        self.assertEqual('10.10.1.1:2181,10.10.0.81:2181', h)
        self.assertEqual('/mesos/test/path', p)

    def test_find_master(self):
        minfo = self.zkd.retrieve_leader()
        self.assertIsNotNone(minfo)
        self.assertEqual('localhost', minfo.get('hostname'))
        self.assertIn(minfo.get('port'), xrange(5050, 5060))

    def test_get_http(self):
        url = self.zkd.get_master_url()
        self.assertIsNotNone(url)
        # TODO: is this the best we can do? we cannot know the actual port where this Master is running
        self.assertTrue(url.startswith('http://localhost:50'))
        self.assertEqual('127.0.0.1', self.zkd.get_ip())
