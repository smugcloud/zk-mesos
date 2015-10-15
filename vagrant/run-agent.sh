#!/bin/bash

LOG_DIR=/var/local/mesos/logs/agent
WORK_DIR=/var/local/mesos/agent
SANDBOX=/var/local/sandbox

# clean-up logs and work directory
rm -rf /tmp/slave
rm -rf "${LOG_DIR}/*"

mesos-slave --work_dir=${WORK_DIR} \
    --ip=192.168.33.11 --port=5051 \
    --master=zk://192.168.33.1:2181/mesos/vagrant \
    --log_dir=${LOG_DIR} \
    --containerizers=docker,mesos \
    --isolation="cgroups/cpu,cgroups/mem" \
    --attributes="rack:r2d2;pod:demo,dev" \
    --resources="ports:[9000-10000];ephemeral_ports:[32768-57344]" \
    --sandbox_directory=${SANDBOX} >/dev/null 2>&1 &
