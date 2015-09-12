======================
Mesos Client Libraries
======================

.. image:: https://go-shields.herokuapp.com/license-apache2-blue.png

:Author: Marco Massenzio (marco@mesosphere.io)
:Version: 0.2
:Last Updated: 2015-09-11


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

This library is explicitly aimed at Python Mesos Framework developers (and soon, expanded to
support Java too).

Leading Master Discovery
========================

See the documentation in `docs/leader_discovery.rst`_

An example usage is in `bin/mesos-leader`_ script.


HTTP API Client
===============

No implementation yet.

See `notebooks/HTTP API Tests.ipynb`_ for an example of how to interact with the HTTP API, in an
IPython Notebook.

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
