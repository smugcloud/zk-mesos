#!/bin/bash

# Starts Apache Mesos Agent node - run with superuser privileges (sudo).

LOG_DIR=/var/local/mesos/logs/agent
WORK_DIR=/var/local/mesos/agent
SANDBOX=/var/local/sandbox

# clean-up logs and work directory from previous runs.
rm -rf "${WORK_DIR}/*"
rm -rf "${LOG_DIR}/*"

mkdir -p ${WORK_DIR}
mkdir -p ${LOG_DIR}
mkdir -p ${SANDBOX}

mesos-agent --work_dir=${WORK_DIR} \
    --ip=192.168.33.11 --port=5051 \
    --master=zk://192.168.33.10:2181/mesos/vagrant \
    --log_dir=${LOG_DIR} \
    --containerizers=docker,mesos \
    --isolation="cgroups/cpu,cgroups/mem" \
    --attributes="rack:r2d2;pod:demo,dev" \
    --resources="ports:[9000-10000];ephemeral_ports:[32768-57344]" \
    --sandbox_directory=${SANDBOX} >/dev/null 2>&1 &
