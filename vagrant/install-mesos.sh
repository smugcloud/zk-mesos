#!/bin/bash

sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y -f openjdk-7-jre-headless libsvn1
sudo apt-get install -y -f 

sudo dpkg -i /var/local/images/mesos_0.24*ubuntu1404_amd64.deb

sudo mkdir -p /var/local/mesos/logs/{master,agent}

# The package install will configure a master/agent to start
# at boot on each server and point to a non-existent ZooKeeper
# We need to get rid of that:
sudo mv /etc/init/mesos-* /var/local/mesos
