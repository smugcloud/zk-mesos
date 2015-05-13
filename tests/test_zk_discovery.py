__author__ = 'marco'

import unittest

from mesos import ZookeeperDiscovery

class TestZookeeperDiscovery(unittest.TestCase):
    def setUp(self):
        self.zk = ZookeeperDiscovery()

    def test_uriparse(self):
        uri = 'zk://10.10.1.1:2181,10.10.0.81:2181/mesos/test/path'
        h, p = ZookeeperDiscovery._parse_uri(uri)
        self.assertEqual('10.10.1.1:2181,10.10.0.81:2181', h)
        self.assertEqual('/mesos/test/path', p)

    def test_find_master(self):
        uri = 'zk://localhost:2181/test/marco'
        zkd = ZookeeperDiscovery(uri)
        self.assertIsNotNone(zkd)
        minfo = zkd.retrieve_master_info()
        self.assertIsNotNone(minfo)
        self.assertEqual('localhost', minfo.hostname)
        self.assertIn(minfo.port, xrange(5050, 5060))

    def test_get_http(self):
        uri = 'zk://localhost:2181/test/marco'
        zkd = ZookeeperDiscovery(uri)
        self.assertIsNotNone(zkd)
        url = zkd.get_master_url()
        self.assertIsNotNone(url)
        # TODO: is this the best we can do? we cannot know the actual port where this Master is running
        self.assertTrue(url.startswith('http://localhost:50'))
