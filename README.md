# exp-iotlab

---------------------------------------------------------------------------


A few misc. utilities for automating experiments with IoT-LAB ( https://www.iot-lab.info ).

This is more of a personnal repository, released in case they would be
useful for someone: real IoT-LAB tools are can be
found on main [FIT IoT-LaB site](https://www.iot-lab.info),
on FIT IoT-LAB [github site](https://github.com/iot-lab/iot-lab)
and [wiki](https://github.com/iot-lab/iot-lab).

---------------------------------------------------------------------------

This is *work in progress, nearly empty for now*

The main idea is to automatically run some experiments on FIT IoT-LAB
(see section [Experiments](#Experiments)):
* A thin Python module is provided, that can be used to write Python scripts, to start, stop, check start of an experiment. 
It uses the IoT-LAB utilities, modules and REST API.
* A few sample experiments *will* be provided.

For more automation, two parts are added (really a byproduct):
* A Makefile that could be a starting point to automatically retrieve
  some packages/components/modules/etc. (e.g. `git clone <RIOT>` or `sudo apt-get install wireshark`)
* Because the Makefile assumes some kind of Ubuntu distribution, 
  a script is provided to construct a proper schroot-ed environment.
  This also allows installation of packages without messing up your
  actual system.

---------------------------------------------------------------------------

# tl;dr

_This is not working for now (for me) because of SSH_AGENT_PID etc._


1) Configure your ssh config properly to access IoT-LAB servers.

2) Get an Ubuntu 12.04 or 14.04 (ever real or in a VM). Install a schroot-ed
Ubuntu 14.04:
```
git clone https://github.com/adjih/exp-iotlab.git
cd exp-iotlab/tools/system && ./create-schroot.sh
```

3) Start your schroot-ed Ubuntu 14.04:
```
cd exp-iotlab && make go-trusty
```

4) Start a Contiki RPL experiment in the newly appeared roxterm
```
cd tools && python ExpContikiRpl.py --site grenoble --nb-nodes 8 --nb-sniffers 2 --duration 10
```

See details below.

---------------------------------------------------------------------------

# Experiments

```
TODO
```

---------------------------------------------------------------------------

# Automatic Download/Install/Compilation

A `Makefile` is provided that attempts to automatically download the
requirements for different experiments. 
NOTE: the Makefile is far from being a well-thought Makefile that
would properly automatically recompile on any change.

This is done because testing
different IoT systems (RIOT, OpenWSN, Contiki) on IoT-LAB requires
a bit of manual work, and I was too lazy to repeat it several times :)

```
TODO
```

## 

```
TODO
```

## OpenWSN

```
TODO
```

## RIOT

```
TODO
```

---------------------------------------------------------------------------

# Schroot system


## Who can use this ?

This is tested on the following systems: Ubuntu 12.04 (32 bits) and Ubuntu 14.04 (64 bits). Other Ubuntu (or Debian) versions might work; other
systems (such as Arch Linux) could require more manual installation
(read  tools/system/create-schroot.sh).

## What is it ?

A schroot system is a way to run binaries from another system,
without installing a virtual machine. Essentially, you can
install (part of) another Ubuntu distribution in a directory, and
then run shells, commands, install packages, inside this distribution.

More information on [Ubuntu wiki](https://wiki.ubuntu.com/DebootstrapChroot)
for instance.

The system is installed by the scripts is: _Ubuntu 14.04 LTS (Trusty Tahr)_.


## How to install ?

Installation
```
cd tools/system
sudo ./create-schroot.sh
```

This will perform the following steps:
* it will install schroot if not installed, and update the configuration
  file for the following (name: `trusty`).
  
* it will install a Ubuntu-14.04 (Trusty Tahr) distribution in your home directory 
  ${HOME}/System-Ubuntu-14.04.

* it will install a few more packages for that Ubuntu.

## How to use ?

Once installed, you can just switch to that environment with:

```
schroot -c trusty
```

Your home directory will be available as usual (due to schroot configuration), 
but otherwise the system will be the one is $HOME/System-Ubuntu-14.04

---------------------------------------------------------------------------
