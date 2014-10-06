# exp-iotlab

---------------------------------------------------------------------------

A few misc. utilities for automating experiments with IoT-LAB ( https://www.iot-lab.info ).

This is more of a personnal repository, released in case they would be
useful for someone: real IoT-LAB tools are can be
found on main [FIT IoT-LaB site](https://www.iot-lab.info),
on FIT IoT-LAB [github site](https://github.com/iot-lab/iot-lab)
and [wiki](https://github.com/iot-lab/iot-lab).

This is *work in progress* (probably some of the following as to be adjusted):

---------------------------------------------------------------------------

# Installing a VM with all software and tools

This is a "quick" way to set experiments using the parts documented below,
is to install a system in a VM, and then run the scripts/makefiles that
automatically install/download for you.
 
(this was not fully tested, under construction, some parts might fail for now)

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
(for both Contiki and OpenWSN). The option USE_DEMO_REPO will use in some case(s), fork(s) of repositories with minor modifications, instead of main repositories.

5) Configure properly your ssh access to IoT-LAB sites.
Generate/use a ssh key documented in [ssh IoT-LAB tutorial](https://www.iot-lab.info/tutorials/configure-your-ssh-access/)

Then, ensure that you have something like this in your .ssh/config:
```
# Configuration
Host *.iot-lab.info
User <YOUR_IOTLAB_USER_NAME>
IdentityFile ~/.ssh/id_rsa 
#            ^^^^^^^^^^^^^ the key you have put in IoT-LAB registration
```

6) Use [auth-cli](https://github.com/iot-lab/iot-lab/wiki/CLI-Tools) to store your IoT-LAB password:

```
cd exp-iotlab
make ensure-auth-info IOTLAB_USER=<YOUR_IOTLAB_USER_NAME>
```
(this just runs ```./iotlab/parts/cli-tools/auth-cli -u <IoT-LAB username>```)


7) Start an experiment as described in the next sections

---------------------------------------------------------------------------

# Launching an experiment with [RIOT](http://www.riot-os.org/)

(under construction)

---------------------------------------------------------------------------

# Launching an experiment with [OpenWSN](https://openwsn.atlassian.net/)

Once the step of the previous section "Installing a VM with all software 
and tools" have been followed,  you can start an experiment.

There are two ways to select nodes for an experiments:

- either make a reservation through https://www.iot-lab.info/ and then
  you can select experiment duration, site, and nodes.
- or through command line arguments of the script ExpOpenWSN.py

Actually, ```ExpOpenWSN.py``` first tries to find an active
node reservation at the IoT-LAB server; and if it does not find one,
it would use command line arguments (with default values), 
to make itself a reservation. Then:

1) Reserve-if-they-are-not-yet-reserved and then flash nodes with OpenWSN:
```
cd tools
python ExpOpenWSN.py --site grenoble --nb-nodes 5 --duration 20
```

2) Tunnel the port of the sink (and actually all OpenWSN nodes) through ssh
  to IoT-LAB experiment server:
```
./expctl ssh-forward
```

3) Redirect the port of the sink through socat in /tmp/tty
```
./expctl pseudo-tty
```

4) Run the web interface (in directory exp-iotlab/)
```
(cd .. && make run-openwsn-web)
xdg-open http://localhost:8080/
```

5) "Select mote..." choose "3236", and then you have the OpenWSN interface 
  for the Sink.

---------------------------------------------------------------------------

# Launching an experiment with Contiki and RPL

(this was demonstrated at 
IETF 90 [LLN Plugfest](https://bitbucket.org/6tisch/meetings/wiki/140720a_ietf90_toronto_plugfest) and [Bits-N-Bites](http://www.ietf.org/meeting/90/ietf-90-bits-n-bites.html) at Toronto).

Once the step of the previous section "Installing a VM with all software and tools" have been followed,  you can start an experiment.

The experiment is essentially the one described by
IoT-LAB tutorial for [contiki IPv6 stack and tools](https://www.iot-lab.info/tutorials/contiki-ipv6-stack-and-tools/), refer to this page to really understand
what is happening :)

```
cd tools
./expctl init ExpRpl.py --site strasbourg --nb-nodes 8 --nb-foren6-sniffers 2 --duration 20
```
This will start an experiment of duration 20 minutes,
with 8 nodes at the site of "strasbourg",
flashed according to instructions of the command line:
- It will be a "contiki" experiment by default, hence one of the nodes will
  be implicitely a "border-router".
- 2 of the nodes will be sniffers (with foren6 format).
- the remaining nodes will be flashed with "default" firmware (without radio,
  actually: [example_event](https://github.com/hikob/openlab/tree/master/appli/examples/event) from IoT-LAB/openlab).

Note that if an experiment is currently running, the script will reuse it.

8) Run the gui launcher
```
python TkExp.py
```

Then proceed as follows:

- click on "forw.ports" to establish a ssh tunnel to the nodes (border router and sniffers),
  A terminal should appear running an 
  ```ssh ... -L ... -L ...``` command (as a byproduct you would have to 
  type your ssh key passphrase).
- click on "tunslip6". This will start tunslip6
  (as described in [tutorial](https://www.iot-lab.info/tutorials/contiki-ipv6-stack-and-tools/), step 7, but this is automated here).
- click on "reset BR". This will reset the border router and will confirm
  that everything is well connected. After  a small delay 
  you should see ```Starting 'Border router process' 'Web server'```
- you should be able to access the web server in your web-browser with an
  address such as: ```http://[aaaa::323:4501:984:343]```.
  See [tutorial](https://www.iot-lab.info/tutorials/contiki-ipv6-stack-and-tools/ for details. 
- click on "foren6-sniffers". This will start a program connecting to the
  sniffer nodes, reading their serial (foren6/snif format), and:
  * outputting the packets in the "snif" format on pty /tmp/myttyS0
  * outputting the packets in the ZEP format (UDP) on loopback
- click on "wireshark". After some warnings (due to sudo wireshark),
  wireshark would start. You should see the RPL DODAGs, and router advertizements from the border router.
- click on "foren6". This will start foren6.
  It needs to be configured along to the steps given in the IoT-LAB tutorial [HOWTO use Foren6](https://github.com/iot-lab/iot-lab/wiki/HOWTO-use-Foren6-to-diagnose-in-realtime-your-6LoWPAN-experiment).
  * click on manage sources, and add: Target=`/tmp/myttyS0` Type=`snif`
  (channel irrelevant)
  * click on start -> you should see a node
- you should be seeing one single circle. This is the border router.
- now comes the TODO part :). You can start the other (unfinished) "GUI" with 
  by clicking on "GUI", and a new window with points appears after 2 sec or so:
  * points are nodes. gray = not reserved, green = border router, 
    red = sniffer, black = default-firmware (the one doing nothing on the radio). Note that sites are in 3D, whereas the map is in 2D, so
    some nodes are "hidden" (currently).
  * select some black nodes by right clicking (their center becomes yellow)
    (remember that some nodes are hidden due to 3D -> 2D).
  * press several times on the secret key "+", to select the firmware
    "contiki-rpl-node".
  * once this is done, press on the key "f", to flash the selected nodes
    (the ones with yellow), with contiki firmware. Be sure to check output
    on the terminal. 
  * looking at wireshark, the newly flashed nodes should be sending RPL DIS
    messages (DODAG Information Sollicitation) until they join the network, 
    and then RPL DIO messages (DODAG Information Object).
  * looking at foren6, notice that new nodes have appeared 
    _Currently the graph might not be displayed instantly, 
       this requires investigation_
  * refreshing the web page of the router you can see the actual addresses
    of the nodes
  * you can ping the nodes, with ```ping6 -s1 <IPv6 address of the node>```.
    ICMP Echo messages goe through the border router, and then on the air
    as 6LoWPAN packets (using the routes discovered by RPL). You should see
    packets-on-the-air with wireshark.
  * you can also directly access the nodes through the web interface.

At the end, you should get something like the following screenshot:

![Screenshot](doc/rpl-exp.png)


---------------------------------------------------------------------------

(Alternatively to a VM, you can use a schroot system instead of a VM, but it is a little more complicated). More unfinished info on [README-more.md](README-more.md).

