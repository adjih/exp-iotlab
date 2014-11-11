---------------------------------------------------------------------------

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

# Experiments

Currently, there is one script that evolved in integrating multiple
functionalities. It is: "tools/ExpContikiRpl.py"

```
usage: ExpContikiRpl.py [-h] [--name NAME] [--site SITE] [--nb-nodes NBNODES]
                 [--duration DURATION] [--dev DEV]
                 [--nb-foren6-sniffers NBFOREN6SNIFFERS]
                 [--nb-zep-sniffers NBZEPSNIFFERS]
                 [--exp-type {contiki,riot,openwsn}]
                 [--nb-protocol-nodes NB_PROTOCOL_NODES]

IoT-LAB experiment

optional arguments:
  -h, --help            show this help message and exit
  --name NAME
  --site SITE
  --nb-nodes NBNODES
  --duration DURATION
  --dev DEV
  --nb-foren6-sniffers NBFOREN6SNIFFERS
  --nb-zep-sniffers NBZEPSNIFFERS
  --exp-type {contiki,riot,openwsn}
  --nb-protocol-nodes NB_PROTOCOL_NODES
```

Only the "contiki" experiment is tested.

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


