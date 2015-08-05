#!/usr/bin/env python

from __future__ import print_function

import argparse
import json
import logging

from mesos import ZookeeperDiscoveryProtocolBuffer

__author__ = 'marco'


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--zk', required=True,
                        help="Zookeeper ensemble URI(s), eg, zk://10.10.1.2:2181,10.10.1.3:2181.")
    parser.add_argument('-a', default=False, dest='all', action='store_true',
                        help="Retrieve all Mesos Masters, not just the Leader")
    return parser.parse_args()


def main():
    config = parse_args()
    logging.info("Connecting to Zookeeper at {}".format(config.zk))
    zk_discovery = ZookeeperDiscoveryProtocolBuffer(config.zk, timeout_sec=15)
    logging.info("Connected")
    if config.all:
        res = zk_discovery.retrieve_all()
        logging.info("Found {} Masters; current Leader: {}".format(len(res), res[0].get('hostname')))
    else:
        res = zk_discovery.retrieve_leader()
        logging.info("Found leader: {}".format(res.get('hostname')))
    print(json.dumps(res, indent=4, separators=[',', ':']))


if __name__ == "__main__":
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)
    main()
