#! /usr/bin/python
#---------------------------------------------------------------------------
# parts from openlab (IoT-LAB) Makefiles
# - iot-lab/parts/contiki/platform/iotlab-m3/Makefile.iotlab-m3
# - iot-lab/parts/contiki/platform/openlab/Makefile.include
#
# Cedric Adjih - Inria 2014
#---------------------------------------------------------------------------

import sys, argparse, pprint, os, time, subprocess
import inspect, telnetlib

OpenOcdPath = "/usr/bin/openocd"

thisScriptPath = os.path.realpath(inspect.getfile(inspect.currentframe()))
thisDirName = os.path.dirname(thisScriptPath)

sys.path.append(thisDirName) # XXX: cleaner
import UsbHelper

#---------------------------------------------------------------------------

OpenOcdTarget = "stm32f1x"
OpenOcdIface = os.path.join(thisDirName, "iotlab-m3.cfg")

#---------------------------------------------------------------------------

TcpBasePort = 33000

#--------------------------------------------------

class OpenOcdCommand:
    def __init__(self, args):
        self._initFromArgs(args)

    def _initFromArgs(self, args):
        self.args = args
        self.mode = None
        if self.args.client:
            self._initClientFromArgs()
        else: self._initCmdLineFromArgs()

    def _initClientFromArgs(self):
        args = self.args
        self.currentCmdLine = []
        self._initPortsFromArgs()
        self.mode = "client"

        
    def _initCmdLineFromArgs(self):
        args = self.args
        self.mode = "command-line"
        cmd = [ 
            OpenOcdPath, 
            "-f", OpenOcdIface, 
            "-f", "target/%s.cfg" % OpenOcdTarget
        ]
        if args.device_index != None:
            cmd.extend(["-c", "ft2232_device_index %s" % args.device_index])
        self.currentCmdLine = cmd
        self._initPortsFromArgs()

    def _initPortsFromArgs(self):
        args = self.args
        if args.auto_port:
            deviceIndex = args.device_index if (args.device_index!=None) else 0
            basePort = deviceIndex * 10 + TcpBasePort
            args.gdbPort = basePort 
            args.tclPort = basePort+1
            args.telnetPort = basePort+2
            print "****** Using TCP ports: gdb=%s tcl=%s telnet=%s" % (
                args.gdbPort, args.tclPort, args.telnetPort)

        if args.client: 
            return # <-

        if args.gdbPort != None:
            self.add("gdb_port %s" % args.gdbPort)
        if args.tclPort != None:
            self.add("tcl_port %s" % args.tclPort)
        if args.telnetPort != None:
            self.add("telnet_port %s" % args.telnetPort)


    def add(self, openOcdCmd):
        if self.mode == "command-line":
            self.currentCmdLine.extend(["-c", openOcdCmd])
        else: self.currentCmdLine.append(openOcdCmd)

    def _doRunClient(self):
        #cmd = ["/bin/nc", "localhost", "%s"%self.args.telnetPort]
        #process = subprocess.Popen(cmd, stderr = subprocess.STDOUT)
        #text = "\n".join(self.currentCmdLine)
        #out,err = process.communicate(text)
        #sys.stdout.write(out)
        telnet = telnetlib.Telnet("localhost", self.args.telnetPort)

        for cmd in self.currentCmdLine + ["exit"]:
            out = telnet.read_very_eager()
            sys.stdout.write(out)
            telnet.write(cmd+"\n")
            sys.stdout.write(cmd+"\n")
        sys.stdout.write(telnet.read_all())
        
        self.currentCmdLine = []

    def doRun(self):
        if self.mode == "command-line":
            self._doRunCmdLine()
        else: self._doRunClient()
        if not self.args.no_shutdown and not self.args.client:
            cmd.add("shutdown")


    def _doRunCmdLine(self):
        cmd = self.currentCmdLine[:]
        self.currentCmdLine = None
        if self.args.roxterm:
            cmd = ["/usr/bin/roxterm", 
                   "-T", "OpenOCD", 
                   "-n", "Device %s" % self.args.device_index,
                   "-e"] + cmd 
        print "[openocd]", " ".join(cmd)
        subprocess.check_call(cmd)

#--------------------------------------------------

def cmdFlash(args):
    cmd = OpenOcdCommand(args)

    cmd.add("init")
    cmd.add("targets")
    cmd.add("reset halt")
    cmd.add("reset init")
    
    cmd.add("flash write_image erase "+args.firmwareFileName)
    cmd.add("verify_image "+args.firmwareFileName)

    cmd.add("reset run")
    
    cmd.doRun()


def cmdSend(args):
    cmd = OpenOcdCommand(args)
    for ocdCmd in args.ocdCmdList:
        cmd.add(ocdCmd)
    cmd.doRun()


def cmdServer(args):
    assert args.client == False
    args.no_shutdown = True

    cmd = OpenOcdCommand(args)

    cmd.add("init")
    cmd.add("targets")

    cmd.doRun()

def cmdPrintTty(args):
    assert args.device_index != None # you must pass it
    m3List = UsbHelper.getOrderedM3List()
    info = m3List[-1-args.device_index]
    print info["port"]

def cmdTty(args):
    assert args.device_index != None # you must pass it
    m3List = UsbHelper.getOrderedM3List()
    info = m3List[-1-args.device_index]
    ttyName = "/dev/%s" % info["port"]
    subprocess.check_call(["miniterm.py", ttyName, "500000"])

#---------------------------------------------------------------------------

def runCommand():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device-index", type=int, default=None)
    parser.add_argument("--no-shutdown", action="store_true", default=False)
    parser.add_argument("--auto-port", action="store_true", default=False)
    parser.add_argument("--client", action="store_true", default=False)
    parser.add_argument("--roxterm", action="store_true", default=False)
    subparsers = parser.add_subparsers(dest="command")

    flashParser = subparsers.add_parser("flash")
    flashParser.add_argument("firmwareFileName")

    serverParser = subparsers.add_parser("server")

    sendParser = subparsers.add_parser("send")
    sendParser.add_argument('ocdCmdList', nargs='+')

    printTtyParser = subparsers.add_parser("print-tty")

    ttyParser = subparsers.add_parser("tty")

    args = parser.parse_args()

    if args.command == "flash":
        cmdFlash(args)
    elif args.command == "send":
        cmdSend(args)
    elif args.command == "server":
        cmdServer(args)
    elif args.command == "print-tty":
        cmdPrintTty(args)
    elif args.command == "tty":
        cmdTty(args)
    else:
        raise NotImplemented("cmd", args.command)

#---------------------------------------------------------------------------

if __name__ == "__main__":
    runCommand()

#---------------------------------------------------------------------------

