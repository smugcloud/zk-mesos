
# Apache Mesos HTTP API

This notebook will show how to connect to a running Master/Slave and launch commands via a simple `CommandInfo` protocol buffer.

The main goal of this notebook is to show how to interact with the new [Mesos HTTP API](https://github.com/apache/mesos/blob/master/docs/scheduler-http-api.md) in Python.

## Prerequisites

- you have RTFM (link above);
- you know how to build/run Apache Mesos locally (see the [Starting Guide](http://mesos.apache.org/gettingstarted/)) OR you can use the `Vagrant Up` method shown below;
- you are familiar with Python [Requests](http://www.python-requests.org/en/latest/) framework.

## Starting Mesos

### Vagrant Up

There is a [`Vagrantfile`](https://github.com/massenz/zk-mesos/blob/develop/vagrant/Vagrantfile) provided in this repository (along with a couple of `provisioning` shell scripts) that will do the needful:

```
    cd vagrant
    vagrant up
```

This will create two VMs (Master and Agent) running under [Virtualbox](http://virtualbox.org) and reachable at, respectively, `192.168.33.10` and `192.168.33.11`.

You could also edit the host machine's `/etc/hosts/` file to make those IPs be the targets for hostnames `mesos-master` and `mesos-agent`:

    mesos-master   192.168.33.10
    mesos-agent    192.168.33.11
    
Test that Mesos is running by opening a browser and pointing it to http://192.168.33.10:5050.

#### Troubleshooting Vagrant

If either the Master/Agent do not come up (or they do and fail) troubleshooting the actual cause of failure is going to be hard; this is what I typically do:

* re-provision the VMs (`vagrant halt` and `vagrant up --provision`);
* destroy the VMs (`vagrant destroy`) and run `vagrant up` again;
* log on either VM (`vagrant ssh master`) and look at the logs (in `/var/local/mesos/logs/master`), fix whatever needs fixing and try to re-run Mesos from within the VM:
```
cd
sudo ./run-master.sh
```


### Building Mesos

If DYI is more your thing (or prefer to run from `HEAD`) then follow the instructions on the [Getting Started page](http://mesos.apache.org/gettingstarted/) and take it from there.

Nothing unusal here, start ZooKeeper (`zkServer.sh start`) then start Master/Agent nodes on `localhost`:
```
./bin/mesos-master.sh --zk=zk://localhost:2181/mesos/test --work_dir=/tmp/mesos-24 --quorum=1 --port=5051           
```

and, in another shell:
```
./bin/mesos-slave.sh --master=zk://localhost:2181/mesos/test --work_dir=/tmp/slave --port=5055
```

Then navigate to the [Mesos Web UI](http://localhost:5051) and make sure all it's working just fine.
If the above doesn't work, it's unlikely that anything in the following ever will.

Remember to adjust the Master/Agent URLs accordingly:
```
# Adjust the ports according to how you launched Mesos:
# see --port in the commands in "Prerequisites"
MASTER_URL = 'http://localhost:5051'
SLAVE_URL = 'http://localhost:5055'
```

(if the above does not work, there may be issues with `hostname` resolution - you may need to update your `/etc/hosts` accordingly - completely outside the scope of this notebook, though).


## Python Virtualenv

I always strongly recommend that folks use virtual environments when messing around with Python and installing libraries - feel free to skip this, but if you end up borking your system... **you have been warned**.

Unfortunately, due to some issues around JSON and string encoding, this notebook only runs with Python 2.7, so make sure this is what the virtual env is going to use:

```
mkvirtualenv -p `which python2.7` demo
pip install -r requirements.txt
jupyter notebook
```

Then load this file (`notebooks/demo.pynb`) in the browser page that opens (if it doesn't, navigate to http://localhost:8888).

Happy hacking!


# Common Imports & Useful globals


```python
from __future__ import print_function

import json
import os
import pprint
import random
import requests
import sh
from threading import Thread
from time import ctime, sleep, time


# See KillTaskMessage in include/mesos/v1/scheduler/scheduler.proto
SUBSCRIBE_BODY = {
    "type": "SUBSCRIBE",
    "subscribe": {
        "framework_info": {
            "user" :  "vagrant",
            "name" :  "Example HTTP Framework"
        },
        "force" : True
    }
}

#### **NOTE**
#
# Even though framework_id is defined as "optional" in scheduler.proto, it MUST
# always be present:
#      optional FrameworkID framework_id = 1;
#
# in all Call messages, apart from the SUBSCRIBE - because we don't have an ID
# before subscribing (which is why it's defined as `optional`).


# See KillTaskMessage in include/mesos/v1/scheduler/scheduler.proto
TEARDOWN_BODY = {
    "type": "TEARDOWN",
    "framework_id": {
        "value" : None
    }
}

# See KillTaskMessage in include/mesos/v1/scheduler/scheduler.proto
KILLTASK_BODY = {
    "type": "KILL",
    "framework_id": {
        "value" : None
    },
    "kill": {
        "agent_id": {"value": None},
        "task_id": {"value": None}
    }
}


DOCKER_JSON = "../resources/container.json"
LAUNCH_JSON = "../resources/launch.json"
TASK_RESOURCES_JSON = "../resources/task_resources.json"


# Adjust the ports according to how you launched Mesos:
# see --port in the commands in "Prerequisites"
MASTER_URL = 'http://192.168.33.10:5050'
SLAVE_URL = 'http://192.168.33.11:5051'
API_V1 = '/api/v1/scheduler'
API_URL = '{}/{}'.format(MASTER_URL, API_V1)
CONTENT = 'application/json'

headers = {
    "Content-Type": CONTENT, 
    "Accept": CONTENT, 
    "Connection": "close"
}

pretty = pprint.PrettyPrinter(indent=2)

def get_json(filename):
    """ Loads the JSON from the given filename."""
    with open(filename) as jsonfile:
        lines = jsonfile.readlines()

    return json.loads("".join(lines))
```

These are the globals that are used to communicate with the background thread; they are currently **thread-unsafe** and may (or may not - chances of a race are pretty slim here) need to be protected with a `RLock`


```python
# TODO: THIS IS THREAD-UNSAFE
terminate = False
offers = []
framework_id = None
last_heartbeat = None
```

## POST helper method

Sends POST request to the given URL using the `requests` library: all optional arguments passed in `**kwargs` are passed straight through to the `post()` call.

If it's not a "streaming" request (see below) and we get a `2xx` response, we return the `Response` object.

### Streaming channel

When we specify a `stream` argument in `**kwargs`, then we open a "streaming channel" to Master: this is used to subscribe a Framework.

This uses [Request's streaming API](http://www.python-requests.org/en/latest/user/advanced/#chunk-encoded-requests) for the "chunk-encoded response".

This method opens a persistent connection to the Master which will continue to receive events "callbacks" for
the lifetime of the Framework; the stream is serialized in `RecordIO` format, which essential means it
looks something like:
```
110\n
{ "type": "OFFERS", ... }224\n
{ "type": "HEARTBEAT"... }435\n
...
```
this will continue until we either tear down the connection, or send a `TEARDOWN` call (see `terminate_framework()` below).


```python
def post(url, body, **kwargs):
    """ POST `body` to the given `url`.
    
        @return: the Response from the server.
        @rtype: requests.Response
    """
    import time
    print('Connecting to Master: ' + url)
    r = requests.post(url, headers=headers, data=json.dumps(body), **kwargs)
    
    if r.status_code not in [200, 202]:
        raise ValueError("Error sending request: {} - {}".format(r.status_code, r.text))
    if 'stream' in kwargs:
        # The streaming format needs some munging:
        first_line = True
        for line in r.iter_lines():
            if first_line:
                count_bytes = int(line)
                first_line = False
                continue
            body = json.loads(line[:count_bytes])
            count_bytes = int(line[count_bytes:])
            if body.get("type") == "HEARTBEAT":
                global last_heartbeat
                last_hearbeat = time.ctime()
            if body.get("type") == "ERROR":
                print("[ERROR] {}".format(body))
            # When we get OFFERS we want to see them (and eventually, use them)
            if body.get("type") == "OFFERS":
                global offers
                offers = body.get("offers")
            # We need to capture the framework_id to use in subsequent requests.
            if body.get("type") == "SUBSCRIBED":
                global framework_id
                framework_id = body.get("subscribed").get("framework_id").get("value")
                if framework_id:
                    print("Framework {} registered with Master at ({})".format(framework_id, url))
            if terminate:
                return
    return r
```


```python
def get_framework(index=None, id=None):
    """Gets information about the given Framework.
    
       From the `/state.json` endpoint (soon to be deprecated, in favor of `/state`)
       we retrieve the Framework information.
       
       Can only specify one of either `index` or `id`.
       
       @param index: the index in the array of active frameworks
       @param id: the framework ID
       @return: the full `FrameworkInfo` structure
       @rtype: dict
    """
    if index and id:
        raise ValueError("Cannot specify both ID and Index")
    r = requests.get("{}/state.json".format(MASTER_URL))
    master_state = r.json()
    frameworks = master_state.get("frameworks")
    if frameworks and isinstance(frameworks, list):
        if index is not None and len(frameworks) > index:
            return frameworks[index]
        elif id:
            for framework in frameworks:
                if framework.get("id") == id:
                    return framework
```

## Warm up

The following code just checks that there is connectivity and the settings are all correct: do not move forward until this run successfully.


```python
r = requests.get("{}/state.json".format(MASTER_URL))
master_state = r.json()

r = requests.get("{}/state.json".format(SLAVE_URL))
slave_state = r.json()

# If this is not true, you're in for a world of hurt:
assert master_state["version"] == slave_state["version"]
print("Mesos version running at {}".format(master_state["version"]))

# And right now there ought to be no frameworks:
assert get_framework(index=0) is None
```

    Mesos version running at 1.0.0


# Registering a Framework

Using the HTTP API requires to run at least two separate threads: one for the "incoming" Master messages **to** the Framework (the HTTP connection we opened with the initial `SUBSCRIBE` `POST`) and another **from** the Framework to the Master to actual convey our requests (eg, accepting `OFFER`s).

We will be using the `threading` module, as this is I/O-bound and there is no CPU contention; we will run a background thread (`persistent_channel`) to receive messages from Mesos, and will use the main thread to send `requests` to Master.

The code in this Notebook **is not thread-safe**; in particular, we don't use any form of locking, as there is no real concern about races over shared data: in real production code, one should obviously protect shared data with suitable `locks` (see the [Python Multithreading documentation](https://docs.python.org/3/library/threading.html) for more details).


```python
try:
    kwargs = {'stream':True, 'timeout':30}
    persistent_channel = Thread(target=post, args=(API_URL, SUBSCRIBE_BODY), kwargs=kwargs)
    persistent_channel.daemon = True
    persistent_channel.start()
    print("The background channel was started to {}".format(API_URL))
except Exception as ex:
    print("An error occurred: {}".format(ex))
```

    Connecting to Master: http://192.168.33.10:5050//api/v1/scheduler
    The background channel was started to http://192.168.33.10:5050//api/v1/scheduler
    Framework ee23e7d6-4aad-4058-9dbd-28057fc9cdeb-0003 registered with Master at (http://192.168.33.10:5050//api/v1/scheduler)


# Terminating a Framework

The request above will keep running forever (but see [Terminating the Request](#terminating) below) until we tear down the framework we just started:


```python
def terminate_framework(fid=None):
    if not fid:
        framework = get_framework(0)
        if framework:
            fid = framework['id']
        else:
            print("No frameworks to terminate")
    body = TEARDOWN_BODY
    body['framework_id']['value'] = fid
    post(API_URL, body)
```

## <a name="terminating"></a>Terminating the Request

The following is a "best effort" to close the running background thread that keeps the connection with Master alive: this actually only works if the Master keeps sending HEARTBEAT messages (so, on the next loop iteration `terminate` gets checked).

In theory, the `timeout` passed at start should prevent the thread to become unresponsive if no more messages are processed, but this does not necessarily seem to always be the case.

If all else fails, restarting the IPython kernel seems to be the only (unsatisfactory) solution.


```python
def close_channel():
    if persistent_channel.is_alive():
        terminate = True
        
    framework_id = None
    offers = None
        
    # Wait a bit...
    sleep(5)
    print("Channel was closed: {}".format(persistent_channel.is_alive()))
```


```python
# To close the incoming channel use the following code;
# this will also terminate the framework (if still running).

# NOTE: Commented out to avoid accidental execution
terminate_framework(fid=framework_id)
close_channel()

pass
```

    Connecting to Master: http://192.168.33.10:5050//api/v1/scheduler
    Channel was closed: True


# Accepting Offers for Resources

We need a tiny amount of resources (0.1 CPU, 32 MB of RAM) to run a simple command on the Slave.

## Wait for Offers

We need to wait first for the framework to register, then to get resource offers:


```python
# This code is safe to execute any number of times; it will only try to connect once.
# In other words, it's idempotent:

count = 0
while not framework_id and count < 10:
    sleep(3)
    print('.', end="")
    count += 1
    
if not framework_id:
    print("Failed to register, terminating Framework")
    close_channel()
else:
    print("Registered a Framework with ID: {}".format(framework_id))

    print("Waiting for offers...")

    count = 0
    while not offers and count < 10:
        print('.', end="")
        sleep(3)
        count += 1
        
    if not offers:
        print("Failed to obtain resources, terminating Framework")
        terminate_framework(framework_id)
        close_channel()
    else:
        print("Got offers:")
        pretty.pprint(offers)
```

    Registered a Framework with ID: ee23e7d6-4aad-4058-9dbd-28057fc9cdeb-0003
    Waiting for offers...
    Got offers:
    { u'offers': [ { u'agent_id': { u'value': u'e044dffe-223e-4677-bf7a-db0aea9529c6-S0'},
                     u'attributes': [ { u'name': u'rack',
                                        u'text': { u'value': u'r2d2'},
                                        u'type': u'TEXT'},
                                      { u'name': u'pod',
                                        u'text': { u'value': u'demo,dev'},
                                        u'type': u'TEXT'}],
                     u'framework_id': { u'value': u'ee23e7d6-4aad-4058-9dbd-28057fc9cdeb-0002'},
                     u'hostname': u'192.168.33.11',
                     u'id': { u'value': u'ee23e7d6-4aad-4058-9dbd-28057fc9cdeb-O2'},
                     u'resources': [ { u'name': u'ports',
                                       u'ranges': { u'range': [ { u'begin': 9000,
                                                                  u'end': 10000}]},
                                       u'role': u'*',
                                       u'type': u'RANGES'},
                                     { u'name': u'cpus',
                                       u'role': u'*',
                                       u'scalar': { u'value': 2.0},
                                       u'type': u'SCALAR'},
                                     { u'name': u'mem',
                                       u'role': u'*',
                                       u'scalar': { u'value': 496.0},
                                       u'type': u'SCALAR'},
                                     { u'name': u'disk',
                                       u'role': u'*',
                                       u'scalar': { u'value': 4930.0},
                                       u'type': u'SCALAR'}],
                     u'url': { u'address': { u'hostname': u'192.168.33.11',
                                             u'ip': u'192.168.33.11',
                                             u'port': 5051},
                               u'path': u'/slave(1)',
                               u'scheme': u'http'}}]}


## Launch a Task using the given offers

We will use a `CommandInfo` protobuf, embedded inside the `Launch` message - you can find them in 
[`mesos.proto`](https://github.com/apache/mesos/blob/master/include/mesos/v1/mesos.proto#L260) while the full request body will be an [Accept](https://github.com/apache/mesos/blob/master/include/mesos/v1/scheduler/scheduler.proto#L228) message.

The following is a simplified version of the `Accept` JSON:


```python
launch_json = get_json(LAUNCH_JSON)

task_id = str(random.randint(100, 1000))

launch_json["accept"]["offer_ids"].append(offers.get("offers")[0]["id"])
launch_json["framework_id"]["value"] = framework_id

task_infos = launch_json["accept"]["operations"][0]["launch"]["task_infos"][0]

task_infos["task_id"]["value"] = task_id
task_infos["command"]["value"] = "cd /var/local/www && /usr/bin/python -m SimpleHTTPServer 9000"
task_infos["agent_id"]["value"] = offers.get('offers')[0]["agent_id"]["value"]
task_infos["resources"] = get_json(TASK_RESOURCES_JSON)


try:
    r = post(API_URL, launch_json)
    print("Result: {}".format(r.status_code))
    if r.text:
        print(r.text)
    if 200 <= r.status_code < 300:
        print("Successfully launched task {} on Agent [{}]".format(task_id, offers.get('offers')[0]["agent_id"]["value"]))
except ValueError, err:
    print("Request failed: {}".format(err))
```

    Connecting to Master: http://192.168.33.10:5050//api/v1/scheduler
    Request failed: Error sending request: 400 - All non-subscribe calls should include the 'Mesos-Stream-Id' header


## Launching a Container

To launch a container, we need a slightly more convoluted form of the `LAUNCH` request: this is in the [container.json](https://github.com/massenz/zk-mesos/blob/develop/resources/container.json) file: we can read that in and then update those fields that are specific to the framework/offer.

```
{
  "framework_id": {
    "value": ## put the framework_id here ##
  },
  "type": "ACCEPT",
  "accept": {
    "offer_ids": [
        ## We'll need to append the offer_id here ##
    ],
    "operations": [
      {
        "type": "LAUNCH",
        "launch": {
          "task_infos": [
            {
              "name": "PingContainer",
              "agent_id": {
                "value": ## This is the ID of the agent, from the offer ##
              },
              "task_id": {
                "value": ## This is an arbitrary ID for the task, must be unique ##
              },
              "command": {
                "shell": true,
                "value": "ping -t 100 google.com"  <<-- we can ask the container to run a command
              },
              "container": {
                "docker": {
                  "image": "busybox", <<-- this is the name of the container
                  "network": "HOST",
                  "privileged": false
                },
                "type": "DOCKER"  <<-- here we ask Mesos to use Docker
                                    -- remember to start the slave with --containerizer=docker
              },
              ...
          }
        ]
      }
      ...
 }
 ```

In order for this to work, the Agent needs to be launched with the `--containerizer=docker,mesos` option (see
[here](http://mesos.apache.org/documentation/latest/docker-containerizer/)).
 
### Mesos Sandbox
 
Because the `CommandInfo` also specifies a `tarball` to be downloaded and extracted, this will be placed into the "Mesos Sandbox Directory": this is typically defined by the `MESOS_SANDBOX_DIRECTORY` OS env variable; however, in our case, as this needs to be known in advance (so we can `cd` to it and serve static files from) we will configure that via the `--mesos_sandbox` flag, when starting the Agent node.
 
In a less contrived situation (read: when you do this for real) one would obviously use either the dynamically set value, or symlink to it from whereve that needs to be.


```python
container_launch_info = get_json(DOCKER_JSON)

# Need to update the fields that reflect the offer ID / agent ID and a random, unique task ID:
task_id = str(random.randint(1, 100))
agent_id = offers.get('offers')[0]['agent_id']['value']
offer_id = offers.get('offers')[0]['id']

container_launch_info["framework_id"]["value"] = framework_id
container_launch_info["accept"]["offer_ids"].append(offer_id)

task_infos = container_launch_info["accept"]["operations"][0]["launch"]["task_infos"][0]
task_infos["agent_id"]["value"] = agent_id
task_infos["task_id"]["value"] = task_id
task_infos["resources"].append(get_json(TASK_RESOURCES_JSON))


#### URIS
# $MESOS_SANDBOX
# launch agent with --sandbox_directory
###

print("Sending ACCEPT message, launching a DOCKER container:")
pretty.pprint(container_launch_info)

try:
    r = post(API_URL, container_launch_info)
    print("Result: {}".format(r.status_code))
    if r.text:
        print(r.text)
except ValueError, err:
    print("Request failed: {}".format(err))
```

    Sending ACCEPT message, launching a DOCKER container:
    { u'accept': { u'filters': { u'refuse_seconds': 5},
                   u'offer_ids': [ { u'value': u'20151009-135032-169978048-5050-11032-O2'}],
                   u'operations': [ { u'launch': { u'task_infos': [ { u'agent_id': { u'value': u'20151009-135032-169978048-5050-11032-S0'},
                                                                      u'command': { u'shell': True,
                                                                                    u'uris': [ { u'extract': True,
                                                                                                 u'value': u'http://192.168.33.1:9000/content.tar.gz'}],
                                                                                    u'value': u'cd /var/local/sandbox && python -m SimpleHTTPServer 9090'},
                                                                      u'container': { u'docker': { u'image': u'python:2.7',
                                                                                                   u'network': u'HOST',
                                                                                                   u'privileged': False},
                                                                                      u'type': u'DOCKER'},
                                                                      u'name': u'PingContainer',
                                                                      u'resources': [ [ { u'name': u'cpus',
                                                                                          u'role': u'*',
                                                                                          u'scalar': { u'value': 0.2},
                                                                                          u'type': u'SCALAR'},
                                                                                        { u'name': u'mem',
                                                                                          u'role': u'*',
                                                                                          u'scalar': { u'value': 100},
                                                                                          u'type': u'SCALAR'}]],
                                                                      u'task_id': { u'value': '68'}}]},
                                      u'type': u'LAUNCH'}]},
      u'framework_id': { u'value': u'20151009-135032-169978048-5050-11032-0000'},
      u'type': u'ACCEPT'}
    Connecting to Master: http://192.168.33.10:5050//api/v1/scheduler
    Result: 202


## Killing a Task

From time to time, it may be necessary to terminate a task (maybe, to free resources, or because it is misbehaving):


```python
def kill_task(task_id):
    body = KILLTASK_BODY
    body["framework_id"]["value"] = get_framework(0).get("id")
    body["kill"]["agent_id"]["value"] = offers.get('offers')[0]["agent_id"]["value"]
    body["kill"]["task_id"]["value"] = task_id
    post(API_URL, body)
```


```python
# To kill a task, uncomment the line below, and replace the task ID with the corresponding **string**
# (even if the TaskID looks like an int value)
kill_task("938")
```

    Connecting to Master: http://192.168.33.10:5050//api/v1/scheduler


## Heartbeat

We receive a `HEARBEAT` event every few seconds from the Master, this confirms that it is still alive and well - failure to receive those would mean that we may need to find a new Leading Master and re-register.


```python
print(last_heartbeat)
```

    None

