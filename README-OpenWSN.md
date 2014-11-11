# Launching an experiment with [OpenWSN](https://openwsn.atlassian.net/)

After you have a running VM as indicated in
[Installing a VM with all software and tools](README-vm.md),  you can start the OpenWSN experiments


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

