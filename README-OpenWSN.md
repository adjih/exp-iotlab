# Launching an experiment with [OpenWSN](https://openwsn.atlassian.net/)

After you have a running VM as indicated in
[Installing a VM with all software and tools](README-vm.md),  you can start the OpenWSN experiments

1) [Once] Before running the experiment for the first time, 
you need to automatically get  and compile necessary packages 
and code from repositories. In directory ```exp-iotlab``` use:
```
make openwsn-exp-deps USE_DEMO_REPO=yes
```
The option USE_DEMO_REPO will use in some case(s), fork(s) of repositories with minor modifications, instead of main repositories.

2) [Optional] Reserve some nodes independenly.

There are three ways to select nodes for an experiments:
- either make a reservation through https://www.iot-lab.info/ and then
  you can select experiment duration, site, and nodes
- use [web-view](https://github.com/iot-lab/iot-lab/tree/master/web-view),
  select some nodes and grab them:

  ```
  cd tools
  ./expctl web-view
  ```
  and click on ```[web-view]```; in the new window, select the nodes,
  and click on ```[grab]```
- or through command line arguments of the script ExpOpenWSN.py

Actually, ```ExpOpenWSN.py``` first tries to find an active
node reservation at the IoT-LAB server; and if it does not find one,
it would use command line arguments (with default values), 
to make itself a reservation.

3) If you have not reserved nodes (step 2):
```
cd tools
python ExpOpenWSN.py --site grenoble --nb-nodes 5 --duration 20
```

otherwise you can run simply:
```
cd tools
python ExpOpenWSN.py
```

4) Tunnel the port of the sink (and actually all OpenWSN nodes) through ssh
  to IoT-LAB experiment server:
```
./expctl ssh-forward
```

5) Redirect the port of the sink through socat in /tmp/tty
```
./expctl pseudo-tty
```

4) Run the web interface (in directory exp-iotlab/)
```
cd .. && make run-openwsn-web
```
and open the OpenVisualizer web interface in another window:
```
xdg-open http://localhost:8080/
```

5) "Select mote..." choose one of them, and then you have the OpenWSN interface 
  for the Sink.
