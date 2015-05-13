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

import logging
import os
import urlparse

import kazoo.client
import kazoo.exceptions

from messages_pb2 import MasterInfo


__author__ = 'marco@mesosphere.io'


class ZookeeperNoMaster(kazoo.exceptions.ZookeeperError):
    pass


class Constants(object):
    #: Default URI for a local ZK; uses /mesos/conf as the path
    DEFAULT_ZK = "zk://localhost:2181/mesos/conf"

    #: timeout for a server connection, in seconds
    DEFAULT_TIMEOUT_SEC = 10

    #: Default label for master info, used as prefix in the znodes, names (eg, `info_000001`)
    MASTER_INFO_LABEL = 'info'


class ZookeeperDiscovery(object):
    """ Simple Reference Implementation (RI) for Mesos Master ZK discovery.

        This class takes a zookeeper URI (complete with path) and obtains the full
        address(es) of the Mesos Masters registered with Zookeeper.
    """

    def __init__(self, zk_uri=Constants.DEFAULT_ZK, timeout_sec=Constants.DEFAULT_TIMEOUT_SEC):
        self.uri = zk_uri
        self.zk_hosts, self.zk_path = self._parse_uri(self.uri)
        self._zk = kazoo.client.KazooClient(hosts=self.zk_hosts, timeout=timeout_sec)
        try:
            self._zk.start(timeout=timeout_sec)
        except Exception as e:
            logging.error('Timeout trying to connect to a ZK ensemble [{}]'.format(e))
            raise RuntimeError('No Zookeeper ensemble available at {}'.format(self.zk_hosts))

    @staticmethod
    def _parse_uri(uri):
        parse_url = urlparse.urlparse(uri, scheme='zk:', allow_fragments=False)
        return parse_url.netloc, parse_url.path

    def retrieve_master_info(self):
        """ Retrieves from ZK the MasterInfo data

        :return: the retrieved ```MasterInfo``` data
        :rtype: MasterInfo

        :raises NoNodeError: if the ```self.zk_path`` does not exist
        :raises ZookeeperExcetpion: if there are errors while fetching the data
        :raises ParseError: if the data cannot be parsed into a valid ```MasterInfo``` protobuf
        """
        if not self._zk.exists(self.zk_path):
            raise kazoo.exceptions.NoNodeError('The path {self.zk_path} provided in the URI {self.zk_uri} '
                                               'could not be found on the Zookeeper ensemble'.format(self=self))
        # TODO: currently the LABEL is assumed hard-coded (see MASTER_INFO_LABEL in constants.cpp)
        nodes = [node for node in self._zk.get_children(self.zk_path) if node.startswith(Constants.MASTER_INFO_LABEL)]
        if not nodes:
            raise ZookeeperNoMaster('No Mesos Master found for {self.uri}'.format(self=self))
        # TODO: right now all we need is to get the hostname:port of any one Master, as it will
        #       redirect (302) the caller to the correct Leader
        node_path = os.path.join(self.zk_path, nodes[0])
        data, stat = self._zk.get(node_path)
        # TODO: make the ``stat`` accessible to clients of this class, perhaps?
        master_info = MasterInfo()
        master_info.ParseFromString(data)
        return master_info

    def get_master_url(self):
        """ Convenience method to retrieve the Master location as a URL (``http://hostname:port``) from the ZK data

            This method is safe to call (will not raise) but may return an empty (``None``) URL

        :return: one of the Mesos Master's URL, as retrieved from the ZK ensemble
        :rtype: str
        """
        try:
            master_info = self.retrieve_master_info()
            return 'http://{host}:{port}'.format(host=master_info.hostname, port=master_info.port)
        except kazoo.exceptions.ZookeeperError:
            return None



