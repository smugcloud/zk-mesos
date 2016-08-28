# A python notebook to experiment with the Apache Mesos HTTP API - Part 1 of 3

This is the first of a series of three articles that shows how to setup a Vagrant-based Apache Mesos test/development environment on your laptop; then how to run a Python notebook against the HTTP API; and finally, how to launch Docker containers on the running Agent VM.

It is pretty jam-packed and requires a certain amount of familiarity with some concepts around containers, VMs and Mesos, but I am taking the time to show all the intermediate steps (hence, the 3-parts) and it should be easy to follow even if you have never used before Vagrant, Mesos or jupyter notebooks, for that matter.

A certain degree of familiarity with Python, requests and handling HTTP responses is going to be certainly helpful, as we will not be going into too much details there.

All the code is available [on my `zk-mesos` git repository](https://github.com/massenz/zk-mesos):

    git clone git@github.com:massenz/zk-mesos.git

and you can also see the [README](https://github.com/massenz/zk-mesos) there.

_This series is an extended (and updated) version of the [talk] I gave at **MesosCon Europe 2015** updated for Apache Mesos 1.0.0, which has just been released (August 2016) - you can also find the [slides] there._

## Getting Started

In order to follow along, you will need to clone the repository (as shown above) and install [Virtualbox](http://virtualbox.org) and [Vagrant]: they are both super-easy to get going, please follow the instructions on their respective sites and you'll be up and running (literally) in no time.

I also recommend to quickly scan the [Vagrant documentation]: a knowledge of Vagrant beyond  `vagrant up` is not really required to get the most out of this series, but it may help if you get stuck (or would like to experiment and improve on our `Vagrantfile`).

If you are not familiar with [Apache Mesos](https://mesos.apache.org) I would recommend to have a look at the project's site: there are also a couple of good books out there, [Mesos in Action] being the one I would recommend (also having been one of the manuscript's reviewers).

We will __not__ be building it from source here, but will instead use [Mesosphere packages]: you don't need to download them, the `Vagrantfile` will automatically download and install on the VMs.

To run the Python notebook, we will take advantage of the [Jupyter](http://jupyter.org) packages, and use a `virtualenv` to run all our code: the latter is not strictly necessary, but will prevent you messing up your system Python.

The steps are pretty simple, and YMMV, but if you have never used [virtualenv](https://virtualenv.pypa.io/en/stable/installation/) before:

    $ sudo pip install virtualenv

and then create and run a virtualenv:

    $ cd zk-mesos
    $ virtualenv mesos-demo
    $ source mesos-demo/bin/activate
    $ pip install -r requirements.txt

Finally, verify that you can run and load the Jupyter notebook:

    $ jupyter notebook

this should automatically open your browser and point it to http://localhost:8888, from where you can select the `notebooks/Demo-API.ipynb` -- don't run it just yet, but if it shows up, it will confirm that your Python setup is just fine.

## Building and installing Apache Mesos

Here is where the beauty of Vagrant shows in all its glory: installing Apache Messos Master and Agent is not trivial, but in our case, it's simply a matter or:

    $ cd vagrant
    $ vagrant up

(make sure to be in the same directory as the `Vagrantfile` when issuing any of the Vagrant commands, or it will complain about it).

It is worth noting that we are building __two__ Vagrant boxes, so any command will operate on __both__ unless specified; to avoid this, you can specify the name of the VM after the command; for example, to SSH onto the Agent:

    $ vagrant ssh Agent

should log you in on that box, from where you can explore, experiment and diagnose any issues.

The `vagrant up` command will take some time to execute, but it should eventually lead your Virtualbox to have two VMs, named respectively `mesos-master` and `mesos-agent` - incidentally, you should never need to use VBox to manage them (all the tasks can be undertaken via Vagrant commands), but you can do that too, if necessary or desired.

Once the VMs are built, ensure you can access Mesos HTTP UI at: <http://192.168.33.10:5050>;
you should also see one agent running, accessible either via the Master UI, or directly at: <http://192.168.33.11:5051/slave(1)/state>.

__NOTE__
> the Agent runs at a different IP (obviously) than the Master, but also on a different __port__ (__5051__ instead of __5050__): look into `vagrant/run-agent.sh` to see a few of the command line flags that we use to run the Agent (and in `run-master.sh` for the Master).

### Zookeeper

It's worth noting that we are also running an instance of Zookeeper (for Leader election and Master/Agent coordination) on the `mesos-master` VM, inside a Docker container: partly because we can, but also to show how easy it is to do so using containers.

This one line (in `run-master.sh`), will give you a perfectly good ZK instance (albeit, a catastrophically unreliable one in a production environment, where you want to run at least 3-5 nodes, at least, an on physically separate machines/racks):

    docker run -d --name zookeeper -p 2181:2181 -p 2888:2888 -p 3888:3888 jplock/zookeeper:3.4.8

# Wrap up

That's pretty much about it: you are now the proud owner of a Master/Agent 2-node Apache Mesos deployment: welcome in the same league as Twitter and Airbnb production wizards.

In Part 2, we will run our Python notebook against the Master API and will accept the Agent's offers to launch a Docker container.


[Mesosphere packages]: http://open.mesosphere.com/downloads/mesos/
[Vagrant]: https://www.vagrantup.com
[Vagrant]: https://www.vagrantup.com/docs
[Virtualbox]: https://www.virtualbox.org/wiki/Documentation
[Zookeeper documentation]: https://zookeeper.apache.org/doc/trunk/
[talk]: https://youtu.be/G7xfEs0lX5U
[slides]: http://events.linuxfoundation.org/sites/events/files/slides/MesosCon%20EU%20-%20HTTP%20API%20Framework.pdf
[Mesos in Action]: http://amzn.to/2citsRx
