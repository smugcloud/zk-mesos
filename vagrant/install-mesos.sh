#!/bin/bash

# Install mesos package from Mesosphere
# See: http://mesosphere.com/downloads
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv E56151BF
DISTRO=$(lsb_release -is | tr '[:upper:]' '[:lower:]')
CODENAME=$(lsb_release -cs)

# Add the repository
echo "deb http://repos.mesosphere.io/${DISTRO} ${CODENAME} main" | \
  sudo tee /etc/apt/sources.list.d/mesosphere.list

sudo apt-get update && sudo apt-get -y upgrade

sudo apt-get install -y -f openjdk-7-jre-headless libsvn1
sudo apt-get install -y -f

sudo apt-get install -y mesos

sudo mkdir -p /var/local/mesos/logs/{master,agent}
sudo mkdir -p /var/local/mesos/{master,agent}

# The package install will configure a master/agent to start
# at boot on each server: we need to get rid of that.
if [[ -e "/etc/init/mesos-*" ]]; then
    sudo rm /etc/init/mesos-*
fi

echo "Stopping Mesos Master/Agent if running on server"
for service in mesos-master mesos-slave; do
    IS_RUNNING=$(sudo service ${service} status|grep stop)
    if [[ -z ${IS_RUNNING} ]]; then
        echo "${service} is running; Stopping:"
        sudo service ${service} stop
    fi
done
