#!/bin/bash

DISTRO=$(lsb_release -is | tr '[:upper:]' '[:lower:]')
CODENAME=$(lsb_release -cs)

sudo apt-get update && \
    sudo apt-get install -y -f openjdk-8-jre-headless libcurl3 libsvn1 libevent-dev

sudo apt-get install -y -f && sudo apt-get dist-upgrade -y

# Install Apache Mesos 1.0.0 package from Mesosphere
# See: http://open.mesosphere.com/downloads/mesos/#apache-mesos-1.0.0
curl http://repos.mesosphere.com/ubuntu/pool/main/m/mesos/mesos_1.0.0-2.0.86.ubuntu1604_amd64.deb \
    > mesos_1.0.0-2.0.86.ubuntu1604_amd64.deb 2>/dev/null

if [[ -f mesos_1.0.0-2.0.86.ubuntu1604_amd64.deb ]]; then
    echo "Apache Mesos 1.0.0 package downloaded, installing..."
    dpkg -i mesos_1.0.0-2.0.86.ubuntu1604_amd64.deb
else
    echo "Failed to download deb file for Mesos, aborting."
    exit 1
fi

sudo mkdir -p /var/local/mesos/logs/{master,agent}
sudo mkdir -p /var/local/mesos/{master,agent}

# The package install will configure a master/agent to start
# at boot on each server: we need to get rid of that.
if [[ -e "/etc/init/mesos-*" ]]; then
    sudo rm /etc/init/mesos-*
fi

# It seems that Mesosphere packages no longer install Mesos as a service.
IS_KNOWN=$(sudo service mesos-master status | grep -v "unrecognized service")
if [[ -z ${IS_KNOWN} ]]; then
  echo "Mesos is not running as a service; done."
  exit 0
fi

echo "Stopping Mesos Master/Agent if running on server"
for service in mesos-master mesos-slave; do
    IS_RUNNING=$(sudo service ${service} status|grep stop)
    if [[ -z ${IS_RUNNING} ]]; then
        echo "${service} is running; Stopping:"
        sudo service ${service} stop
    fi
done
