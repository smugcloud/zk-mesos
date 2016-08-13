======================
Mesos Client Libraries
======================

.. image:: https://go-shields.herokuapp.com/license-apache2-blue.png

:Author: Marco Massenzio (marco@alertavert.com)
:Version: 1.0
:Last Updated: 2016-08-09


.. contents:: Table of Contents


Motivation
==========

Following the Apache Mesos `community meeting`_ of Sept-3-2015, it was decided that the Project
Maintainers would discontinue support for third-party, non-C++ libraries after the 1.0 release:
these will be deprecated and, after two quarters, removed from the Mesos official ASF repository.

This project aims to support Apache Mesos HTTP API (as released on the 0.24 release) and
subsequent modification.

Although the source code is released as open-source software, under the terms of the
`Apache 2 License`_ it is **important to note that this code is not endorsed by**
**the Apache Mesos official maintaners** and is not currently under the aegis of the Apache
Software Foundation.

Scope
=====

We currently aim to support:

- Leading Master Discovery via ZooKeeper;
- HTTP API wrapper client.

This library is explicitly aimed at Python Mesos Framework developers.

Dev Environment
===============

There is a Vagrant-based development environment (see the ``vagrant/Vagrantfile`` and associated
scripts).

This has been updated to support:

* Mesos 1.0.0 DEB `Mesosphere packages`_
* Vagrant_ 1.8
* Docker 1.11+ (to run Zookeeper and launch containers via Mesos).

The ``Vagrantfile`` will build and provision two VMs (running under Virtualbox_), one running the
 Master (and Zookeeper, in a Docker container) and the other the Agent::

    vagrant up

will do all the necessary heavy-lifting; the first time, it will take a bit as it needs to
download the Ubuntu 16.04 Vagrant box, provision all the files, build the ZK container and get
everything sorted (also worth noting that the Ubuntu VM takes quite some time to come up in
Virtualbox: you may see a few SSH timeouts in the Vagrant logs, this is normal and it will
succeed anyway: if it takes too long, or it fails mysteriously, uncomment the option to activate
the GUI during provisioning).

Once booted, the Master will be running on ``192.168.33.10`` and the Agent on ``192.168.33.11``,
the Web UI for Mesos is reachable from the host dev box via: ``http://192.168.33.10:5050``.

Unfortunately, with the current setup, any reboot of either VMs will cause the Master or Agent
**not** to come up again: you will have to manually restart them.

    TODO - make it so that Master/Agent and ZK restart after a VM reboot

For example, if the Master VM is rebooted, Mesos can be restarted with (by default Vagrant will
copy all the files in the folder containing the ``Vagrantfile`` to ``/vagrant`` on the VM::

    # On the host machine:
    cd vagrant
    vagrant ssh master
    
    # Once SSH'd into the VM:
    $ sudo /vagrant/run-master.sh
    $ exit

The logs are in the ``/var/local/mesos/{master,agent}/logs`` and can be inspected by SSH'ing into
the respective VM.

If necessary, Zookeeper can be accessed from the Master VM, via::

    docker exec -it zookeeper /bin/bash
    # cd /opt/zookeeper
    # ./bin/zkCli.sh

See the `Zookeeper documentation`_ for more info.


Leading Master Discovery
========================

See the documentation in `docs/leader_discovery.rst`_

An example usage is in `bin/mesos-leader`_ script.


HTTP API Client
===============

No implementation yet.

See `notebooks/HTTP API Tests.ipynb`_ for an example of how to interact with the HTTP API, in an
IPython Notebook.

This was presented at `MesosCon Europe`_ (and the slides_).

Contributing
============

Contributions from the community are welcomed and encouraged: please feel free to fork this
repository and submit pull requests, report issues and request new features.

I also plan to add contributors to the project; most likely, these will be folks who have
contributed some PRs or already have good standing and reputation in the Mesos community (and,
obviously, have demonstrated proficiency in Python).


.. _community meeting: https://docs.google.com/document/d/153CUCj5LOJCFAVpdDZC7COJDwKh9RDjxaTA0S7lzwDA/edit#heading=h.5vcsxedq9n7d
.. _bin/mesos-leader: https://github.com/massenz/zk-mesos/blob/develop/bin/mesos-leader
.. _docs/leader_discovery.rst: .. _proto/messages.proto: https://github.com/massenz/zk-mesos/blob/develop/docs/leader_discovery.rst
.. _Apache 2 License: http://www.apache.org/licenses/LICENSE-2.0
.. _notebooks/HTTP API Tests.ipynb: https://github.com/massenz/zk-mesos/blob/develop/notebooks/HTTP%20API%20Tests.ipynb
.. _Mesosphere packages: http://open.mesosphere.com/downloads/mesos/
.. _Vagrant: https://www.vagrantup.com
.. _Virtualbox: https://www.virtualbox.org/wiki/Documentation
.. _Zookeeper documentation: https://zookeeper.apache.org/doc/trunk/
.. _MesosCon Europe: https://youtu.be/G7xfEs0lX5U
.. _slides: http://events.linuxfoundation.org/sites/events/files/slides/MesosCon%20EU%20-%20HTTP%20API%20Framework.pdf
