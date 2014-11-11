# exp-iotlab
---------------------------------------------------------------------------

# Quick Starting IoT-LAB experiments

Utilities and scripts for automating experiments with IoT-LAB ( https://www.iot-lab.info ) using different systems and experiments.

The idea is to be as simple as possible, and take care of the required
dependencies by automatically downloading/installing them
(there is a giant Makefile doing that).

The steps:

1) Start install and configure a virtual machine (with the proper Ubuntu),
  following the instructions:

  * [Installing/Configuring a Virtual Machine](README-vm.md) for IoT-LAB experiments.

2) Automatically launch one of the following experiments:
  
  * [Launching an RPL experiment with RIOT](README-RIOT.md)

  * [Launching an experiment with OpenWSN](README-OpenWSN.md)

  * [Launching an RPL experiment with Contiki and RPL](README-Contiki.md) 
    * This is based on IoT-LAB tutorials: 
      * [Contiki IPv6 stack and tools](https://www.iot-lab.info/tutorials/contiki-ipv6-stack-and-tools/)
      * [HOWTO use Foren6 to diagnose in realtime your 6LoWPAN experiment](https://github.com/iot-lab/iot-lab/wiki/HOWTO-use-Foren6-to-diagnose-in-realtime-your-6LoWPAN-experiment)
    * This was demonstrated at 
IETF 90 [LLN Plugfest](https://bitbucket.org/6tisch/meetings/wiki/140720a_ietf90_toronto_plugfest) and [Bits-N-Bites](http://www.ietf.org/meeting/90/ietf-90-bits-n-bites.html) at Toronto.

---------------------------------------------------------------------------

Note: this is a personnal contribution: real IoT-LAB tools can be
found on main [FIT IoT-LaB site](https://www.iot-lab.info),
on FIT IoT-LAB [github site](https://github.com/iot-lab/iot-lab)
and [wiki](https://github.com/iot-lab/iot-lab). This is *work in progress*.

---------------------------------------------------------------------------
