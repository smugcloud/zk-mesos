=========================
Zookeeper Mesos Discovery
=========================

.. image:: https://go-shields.herokuapp.com/license-apache2-blue.png


:Author: Marco Massenzio (marco@alertavert.com)
:Version: 0.1
:Last Updated: 2015-05-12

Motivation
----------

Currently, to discover a Mesos Master URL it is necessary to bind with native libraries (in particular, ``libmesos``)
and deal with a lot unnecessary complication (eg, JNI for Java projects).

With the upcoming HTTP API it is desirable to have Frameworks that are 'pure language' (eg, Python and/or Java) and
do not require bindings to C/C++ libraries.

The approach presented here meets this need halfway: it still requires the `Google Protobuf`_ step (although, given
that the only protobuf message used is ``MasterInfo`` which should be pretty stable, this is fairly lightweight
requirement) but it is otherwise "pure" Python (a very similar approach would work just as well for Java).

Approach
--------

To understand how this works, look in the Mesos source code, ``detector.cpp``, line 203::

    Try<MasterDetector*> MasterDetector::create(const string& mechanism)
    {
        // ...

        if (strings::startsWith(mechanism, "zk://")) {
            Try<zookeeper::URL> url = zookeeper::URL::parse(mechanism);
            if (url.isError()) {
              return Error(url.error());
            }
            if (url.get().path == "/") {
              return Error(
                  "Expecting a (chroot) path for ZooKeeper ('/' is not supported)");
            }
            return new ZooKeeperMasterDetector(url.get());
        }
    }


This will accept a user-define ``path`` inside wich Zookeeper will be asked to create sequential nodes; for example,
after the first master had been terminated and two additional ones started::


    [zk: localhost:2181(CONNECTED) 11] ls /test/marco
    [log_replicas, info_0000000002]
    [zk: localhost:2181(CONNECTED) 12] ls /test/marco
    [info_0000000003, log_replicas, info_0000000002]
    [zk: localhost:2181(CONNECTED) 13]

master(s) were launched with::

     ./bin/mesos-master.sh --zk=zk://localhost:2181/test/marco --quorum=1 --work_dir=/tmp/mesos-1


A (C++) worker node can be instructed to find the Master node via::

    ./bin/mesos-slave.sh --master=zk://localhost:2181/test/marco

In our code, we follow the same approach: given a ZK URL, we look inside the provided ``path`` and look for data
``znodes`` which start with the given ``label`` (currently, we use the default value, see
``Constants.MASTER_INFO_LABEL``).

Once found a valid data node, we retrieve the binary data and deserialize back to a valid ``MasterInfo`` protobuf
(see ``proto/messages.proto``).

Installation
------------

To compile the ``.proto`` file to a valid Python file, we need to enable `Google Protobuf`_ and a few other
dependencies::

    $ pip freeze
    google-apputils==0.4.2
    kazoo==2.1
    protobuf==2.6.1
    python-gflags==2.0

(see ``requirements.txt`` for the full set of dependencies); you can then build the ``messages_pb2.py`` with::

    SRC_DIR=proto protoc -I=$SRC_DIR --python_out=$SRC_DIR $SRC_DIR/messages.proto

Note that this step is not necessary (just use ``proto/messages_pb2.py``) unless you change the contents of
``messages.proto`` (which is not advisable, as it would make it incompatible with ``mesos/messages.proto::MasterInfo``).

.. _Google Protobuf: https://developers.google.com/protocol-buffers/docs/pythontutorial
