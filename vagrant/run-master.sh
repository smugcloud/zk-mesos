#!/bin/bash

LOG_DIR=/var/local/mesos/logs/master

sudo mkdir -p /tmp/logs
mesos-master --work_dir=/tmp/master --ip=192.168.33.10 --port=5050 \
    --hostname=192.168.33.10 --log_dir=$LOG_DIR >/dev/null 2>&1 &
