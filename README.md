# Napalm Plugin for Beer Garden

This repo is meant to show the power of two Open-Source tools: 

* [Beer Garden](https://beer-garden.io) 
* [Napalm](https://napalm.readthedocs.io/en/latest/)

This is a sample for how to control network devices through Beer Garden, using Napalm's drivers. We
leverage Napalm for the device interface, and Beer Garden to get a nice GUI/ReST interface and 
tracability for actions taken on our devices. 

## Setup

Because we are going to be exercising some network operating systems, it is helpful if you have
some devices to play with. If not,  you should follow the [Setting up the Lab](https://napalm.readthedocs.io/en/latest/tutorials/lab.html)
portion of the Napalm tutorials. At the end, you will have a mock Arista EOS driver up and running.

Now you need to get beer-garden running. I've provided the docker-compose script from the beer-garden
repository, you can find it [here](https://github.com/beer-garden/beer-garden/blob/master/docker/docker-compose/docker-compose.yml)

This is as simple as:

```commandline
$ docker-compose up -d
```

Now you have beer-garden and some devices running, you just need to install the dependencies and 
run the plugin:

```commandline
pip install -r requirements.txt
python run.py eos \
-d ./conf/example_device_config.json \
-b ./conf/example_bg_config.json
```

This starts up a plugin for the Arista EOS device. Now visit http://localhost:2337
and you should see your new plugin up and running!

## Napalm Device Support

A high-level overview as of Feb 20, 2018:

* Arista EOS >= 4.15.0F
* JunOS >= 12.1
* IOS-XR >= 5.1.0
* NXOS >= 6.1
* IOS >= 12.4(20)T

Checkout [the supported devices list](https://napalm.readthedocs.io/en/latest/support/index.html) for a full list 
of supported devices and all their configuration options.  