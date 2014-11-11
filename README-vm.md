# Installing a VM with all software and tools

This is a "quick" way to set experiments using the parts documented below:
 - install a system in a VM, 
 - then run the scripts/makefiles that automatically install/download for you.

More details here:

1) Get Ubuntu 14.04 32 bits in a VM (VirtualBox, vmware, ...)

2) In the newly installed Ubuntu 14.04 in a VM:
```sudo apt-get install git```

3) Automatically update the system with proper packages
```
git clone https://github.com/adjih/exp-iotlab.git
cd exp-iotlab/tools/system && sudo ./update-schroot-dist.sh really-update extra
```

4) Automatically get and compile necessary packages and code from repositories
```
make all-exp-deps USE_DEMO_REPO=yes
```
(if you plan to do experiments with only one of RIOT, OpenWSN or Contiki: you can use ```riot-exp-deps```, ```openwsn-exp-deps``` or ```contiki-exp-deps``` instead of ```all-exp-deps``` to compile a subset). The option USE_DEMO_REPO will use in some case(s), fork(s) of repositories with minor modifications, instead of main repositories.

5) Configure properly your ssh access to IoT-LAB sites.
Generate/use a ssh key documented in [ssh IoT-LAB tutorial](https://www.iot-lab.info/tutorials/configure-your-ssh-access/)


Then, ensure that you have something like this in your .ssh/config:
```
# Configuration
Host *.iot-lab.info
User <YOUR_IOTLAB_USER_NAME>
IdentityFile ~/.ssh/id_rsa 
#            ^^^^^^^^^^^^^ the key that you have given for IoT-LAB registration
```

6) Use [auth-cli](https://github.com/iot-lab/iot-lab/wiki/CLI-Tools) to store your IoT-LAB password:

```
cd exp-iotlab
make ensure-auth-info IOTLAB_USER=<YOUR_IOTLAB_USER_NAME>
```
(this just runs ```./iotlab/parts/cli-tools/auth-cli -u <IoT-LAB username>```)


7) You might wish to configure ```sudo``` without password. Type:
```
sudo visudo
```
and at the end of the file, add:
```
<username> ALL=(ALL) NOPASSWD: ALL
```
and save. ```<username>``` is your user name 

8) Start an experiment as described in the [other sections](README.md)

---------------------------------------------------------------------------

(Alternatively to a VM, you can use a schroot system instead of a VM, but it is a little more complicated). More unfinished info on [README-more.md](README-more.md).
