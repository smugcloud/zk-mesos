#!/bin/bash

LOG_DIR=/var/local/mesos/logs/agent

mesos-slave --work_dir=/tmp/slave --ip=192.168.33.11 --port=5051 \
    --master=192.168.33.10:5050 --log_dir=$LOG_DIR >/dev/null 2>&1 &