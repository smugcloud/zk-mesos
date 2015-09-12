=========================
Zookeeper Mesos Discovery
=========================

.. image:: https://go-shields.herokuapp.com/license-apache2-blue.png


Motivation
----------

Up until and including Apache Mesos 0.23, to discover a Mesos Master URL it is necessary to bind
with native libraries (in particular, ``libmesos``)
and deal with a lot of undesirable complication (eg, JNI for Java projects; linking with
`Google Protobuf`_ libraries and Mesos' exported classes).

With the HTTP API released in 0.24 (Aug 2015) it is desirable to have Frameworks that are 'pure
language' (eg, Python and/or Java) and do not require bindings to C/C++ libraries.

The approach presented here allows clients to discover the Leading Master without binding to
any of the C++ libraries, and instead retrieves the JSON information directly from
ZooKeeper.

ZooKeeperDiscovery class
------------------------

This uses the ``kazoo`` Zookeeper client to connect to the running ZK instance and retrieve the
information about the leading Master: the base class is abstract, we create a concrete one
using the ``zookeeper_discovery()`` factory method, which uses the Mesos version to choose which
implementation to use::

    zk_discovery = zookeeper_discovery(cfg.mesos_version, cfg.zk, timeout_sec=15)

It would be also possible to conduct some form of "auto-discovery" by either trying to convert the
data and seeing which one works; or looking at the label prefixes of the stored data (the JSON
ones all begin with ``json.info_``, versions prior to 0.24, use ``info_``).

Two main methods are useful in the ``ZookeeperDiscovery`` class::

        retrieve_leader()   - returns a dict with info about the leading Master.
        retrieve_all()      - returns a list of dicts, about all running Masters.

See the code in ``bin/mesos-leader`` for an example usage.

This class needs to know where in the ZK tree to retrieve the information, this is provided in
the constructor, with the ``zk_uri`` argument which should mirror the contents of the ``--zk``
command-line flag used to execute the Mesos Master::

     ./bin/mesos-master.sh --zk=zk://localhost:2181/mesos --quorum=1 --work_dir=/var/local/mesos


Example Python Discovery
------------------------

An example usage is in ``bin/mesos-leader``: to run the demo app, just launch the script::

    ./mesos-leader --zk zk://localhost:2181/mesos/test

this should emit the information about the leading Master; eg, something like::

    2015-08-06 00:18:36 [INFO ] Connecting to localhost:2181
    2015-08-06 00:18:36 [INFO ] Zookeeper connection established, state: CONNECTED
    {
        "ip":855746752,
        "hostname":"gondor",
        "pid":"master@192.168.1.51:5051",
        "id":"20150806-001800-855746752-5051-509",
        "version":"0.24.0",
        "address":{
            "ip":"192.168.1.51",
            "hostname":"gondor",
            "port":5051
        },
        "port":5051
    }

passing the ``-a`` flag, all Masters' information will be emitted; ``--help`` will print
all the other flags' possible values.

Note that (due to MESOS-1201_) for Mesos < 0.24, the IP address stored in the ``ip`` field
won't convert correctly to the correct IP address (bytes are stored in network order, as opposed
to host order); we have thus to rely on the ``pid`` to retrieve the host IP.

See the section below for more info about the approach for Mesos versions prior to ``0.24``.


Protocol Buffers - 0.23.0 and older
-----------------------------------

Prior to version 0.24, Mesos Masters were storing the ``MasterInfo`` protocol buffer via its
serialization protocol, to decode which, we need the actual definition of the protocol buffers.

These can be imported via the Mesos python bindings (see [TODO: insert link]).

The only PB used (``MasterInfo``) has been included here (`proto/messages.proto`_) for
convenience and making the tests run; however, this **only works with Apache Mesos 0.23.x** and
is not compatible with prior versions.

See `Google ProtoBuf`_ for more information around Python bindings and compilation steps.

Installation
------------

See ``requirements.txt`` for the full set of dependencies; we recommend the use of
Python virtual environments, and then simply::

    pip install -r requirements.txt


.. _Google Protobuf: https://developers.google.com/protocol-buffers/docs/pythontutorial
.. _MESOS-1201: https://issues.apache.org/jira/browse/MESOS-1201
.. _proto/messages.proto: https://github.com/massenz/zk-mesos/blob/develop/proto/messages.proto

