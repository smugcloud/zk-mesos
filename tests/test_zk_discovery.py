# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import socket
import unittest

from mesos_commons.discovery import ZookeeperDiscoveryJson


class TestZookeeperDiscovery(unittest.TestCase):
    """ Runs unit tests for Mesos >= 0.24.0.

        Note the test require a running ZooKeeer and (at least)
        one Mesos Master to be connected to it, launched via::

            $ ./bin/mesos-master.sh --zk=zk://localhost:2181/mesos/test \
                --work_dir=/tmp/mesos-24 --quorum=1 --port=5051

    """

    def setUp(self):
        self.uri = 'zk://localhost:2181/mesos/test'
        self.zkd = ZookeeperDiscoveryJson(self.uri)
        self.assertIsNotNone(self.zkd)

    def test_uriparse(self):
        uri = 'zk://10.10.1.1:2181,10.10.0.81:2181/mesos/test/path'
        h, p = ZookeeperDiscoveryJson._parse_uri(uri)
        self.assertEqual('10.10.1.1:2181,10.10.0.81:2181', h)
        self.assertEqual('/mesos/test/path', p)

    def test_find_master(self):
        minfo = self.zkd.retrieve_leader()
        self.assertIsNotNone(minfo)
        self.assertEqual(socket.gethostname(), minfo.get('hostname'))
        self.assertEqual(5051, minfo.get('port'))

    def test_get_http(self):
        url = self.zkd.get_master_url()
        self.assertIsNotNone(url)
        ip, port = self.zkd.get_leader_ip()
        self.assertEquals('http://{ip}:{port}'.format(ip=ip, port=port), url)

    def test_can_get_leader(self):
        self.assertIsNotNone(self.zkd.retrieve_leader())
        self.assertIsNotNone(self.zkd.get_leader_ip()[0])

    def test_can_parse_ip(self):
        self.assertEquals(socket.gethostname(), self.zkd.retrieve_leader()['hostname'])
