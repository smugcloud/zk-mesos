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
    #: Default URI for a local ZK; uses /mesos as the path
    DEFAULT_ZK = "zk://localhost:2181/mesos"

    #: timeout for a server connection, in seconds
    DEFAULT_TIMEOUT_SEC = 10

    #: Default label for master info, used as prefix in the znodes, names (eg, `info_000001`)
    MASTER_INFO_LABEL = 'info'


class ZookeeperDiscovery(object):
    """ Simple Reference Implementation (RI) for Mesos Master ZK discovery.

        This class takes a zookeeper URI (complete with path) and obtains the full
        address(es) of the Mesos Masters registered with Zookeeper.
    """

    def __init__(self, zk_uri=Constants.DEFAULT_ZK, timeout_sec=Constants.DEFAULT_TIMEOUT_SEC,
                 label=Constants.MASTER_INFO_LABEL):
        self.uri = zk_uri
        self.zk_hosts, self.zk_path = self._parse_uri(self.uri)
        self._zk = kazoo.client.KazooClient(hosts=self.zk_hosts, timeout=timeout_sec)
        self.label = label
        try:
            self._zk.start(timeout=timeout_sec)
        except Exception as e:
            logging.error('Timeout trying to connect to a ZK ensemble [{}]'.format(e))
            raise RuntimeError('No Zookeeper ensemble available at {}'.format(self.zk_hosts))

    @staticmethod
    def _parse_uri(uri):
        parse_url = urlparse.urlparse(uri, scheme='zk:', allow_fragments=False)
        return parse_url.netloc, parse_url.path

    def retrieve_leader(self):
        """ Retrieves from ZK the MasterInfo data

        :return: the retrieved ```MasterInfo``` data for one Master node
        :rtype: MasterInfo

        :raises NoNodeError: if the ```self.zk_path`` does not exist
        :raises ZookeeperExcetpion: if there are errors while fetching the data
        :raises ParseError: if the data cannot be parsed into a valid ```MasterInfo``` protobuf
        """
        all_znodes = self._get_nodes()
        # The lowest numbered znode is the Leader
        all_znodes.sort()
        node_path = os.path.join(self.zk_path, all_znodes[0])
        # TODO: make the ``stat`` accessible to clients of this class, perhaps?
        data, stat = self._zk.get(node_path)
        master_info = MasterInfo()
        master_info.ParseFromString(data)
        return ZookeeperDiscovery._to_dict(master_info)

    def retrieve_all(self):
        """ Retrieves information about the entire set of Mesos Masters currently active


        :return: the retrieved ```MasterInfo``` data for all the Master nodes
        :rtype: list(MasterInfo)

        :raises NoNodeError: if the ```self.zk_path`` does not exist
        :raises ZookeeperExcetpion: if there are errors while fetching the data
        :raises ParseError: if the data cannot be parsed into a valid ```MasterInfo``` protobuf
        """
        nodes = self._get_nodes()
        if not nodes:
            raise ZookeeperNoMaster("No Mesos Masters found for {}".format(self.zk_path))
        master_info = []
        for node in nodes:
            node_path = os.path.join(self.zk_path, node)
            data, stat = self._zk.get(node_path)
            master_info_pb = MasterInfo()
            master_info_pb.ParseFromString(data)
            master_info.append(ZookeeperDiscovery._to_dict(master_info_pb))
        return master_info

    @staticmethod
    def _to_dict(pb_info):
        """ Converts a MasterInfo protobuf into its dictionary equivalent

        :param pb_info: MasterInfo
        :return: the equivalent dict
        :rtype: dict
        """
        res = {
            'pid': pb_info.pid,
            'ip': pb_info.address.ip,
            'hostname': pb_info.address.hostname,
            'id': pb_info.id,
            'port': pb_info.address.port,
            'version': pb_info.version
        }
        return res

    def _get_nodes(self):
        """ Gets all the znode names that are currently active

            Internal method, should **not** be used by clients; use either of ```retrieve_all()```
            or ```retrieve_leader()```.

        :return: the list of node names (**not** the full path)
        :rtype: list(str)

        :raises NoNodeError: if the ```self.zk_path`` does not exist
        :raises ZookeeperExcetpion: if there are errors while fetching the data
        :raises ParseError: if the data cannot be parsed into a valid ```MasterInfo``` protobuf
        """
        if not self._zk.exists(self.zk_path):
            raise kazoo.exceptions.NoNodeError('The path {self.zk_path} provided in the URI {self.uri} '
                                               'could not be found on the Zookeeper ensemble'.format(self=self))
        nodes = [node for node in self._zk.get_children(self.zk_path) if node.startswith(self.label) and
                 not node.endswith('.json')]
        if not nodes:
            raise ZookeeperNoMaster('No Mesos Master found for {self.uri}'.format(self=self))
        return nodes

    def get_master_url(self):
        """ Convenience method to retrieve the Master location as a URL (``http://hostname:port``) from the ZK data

            This method is safe to call (will not raise) but may return an empty (``None``) URL

        :return: one of the Mesos Master's URL, as retrieved from the ZK ensemble
        :rtype: str
        """
        try:
            master_info = self.retrieve_leader()
            return 'http://{host}:{port}'.format(host=master_info.get('hostname'),
                                                 port=master_info.get('port'))
        except kazoo.exceptions.ZookeeperError:
            return None

    def get_all_urls(self):
        """ Gets all Masters' URLs

        :return: the list of hostname:port URLs for all the masters; or an empty list if an error occurs
        :rtype: list(str)
        """
        urls = []
        try:
            masters_info = self.retrieve_all()
            for master_info in masters_info:
                urls.append('http://{host}:{port}'.format(host=master_info.hostname, port=master_info.port))
        except kazoo.exceptions.ZookeeperError:
            # TODO: add logging and log(ERROR) here
            pass
        return urls

    def get_ip(self):
        master_info = self.retrieve_leader()
        return master_info.get('ip')
