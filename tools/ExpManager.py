#! /usr/bin/python
#---------------------------------------------------------------------------
# [Jul2014] Copied from NC-iotlab/src/ExpManager.py and modified
#
# Cedric Adjih, Inria, 2010-2014
#---------------------------------------------------------------------------

import socket, sys, argparse, time, os, select
import traceback, tty, termios

from IotlabHelper import SerialTcpPort
import Scheduler

MaxDataLength = 100

#---------------------------------------------------------------------------

def S(x):
    sys.stdout.write("> "+x+"\n")
    os.system(x)

#---------------------------------------------------------------------------

class IotlabNodeConnection:
    def __init__(self, args, scheduler, connectId, node, port, sd=None):
        self.args = args
        self.scheduler = scheduler
        self.connectId = connectId
        self.node = node
        self.port = port
        self.sd = sd
        
        #if self.config.shouldLog:
        #    self.log = open(self.config.resultDir+"/log.%d" % self.nodeId, "w")
        #else: self.log = None

        # self.clientList = []

    def connect(self):
        print "  connection #%s to node %s:%s" % (
            self.connectId, self.node, self.port)
        if self.sd == None:
            self.sd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sd.connect((self.node, self.port))
        self.scheduler.addFdHandler(Scheduler.FunctionalFdHandler(
                self.sd, waitInputFunc = lambda: True,
                handleInputFunc = self.eventInput))


    def eventInput(self):
        data = self.sd.recv(MaxDataLength)
        if data == "":
            #finished # XXX:TODO
            return
        #if self.log != None:
        #    self.log.write(repr((time.time(), "out", data))+"\n")
        #    if self.config.withFlush: self.log.flush()
        ##sys.stdout.write("[%d|" % self.nodeId +data+"]")
        ##sys.stdout.flush()
        #for client in self.clientList:
        #    client.write(data)
        print data

    def write(self, data):
        #if self.log != None:
        #    self.log.write(repr((time.time(), "in", data))+"\n")
        self.sd.send(data)


#---------------------------------------------------------------------------

class ConnectionManager:
    def __init__(self):
        self.scheduler = Scheduler.RealTimeScheduler()
        self.termAttr = None
        self.state = "init"

    def setUp(self, args, nodeAndPortList):
        self.args = args
        sdTable = {}

        self.nodeAndPortList = nodeAndPortList
        self.createAllConnection()
        self.state = "connected"

    def createAllConnection(self):
        print "-- Connecting to nodes"
        connectionTable = {}

        for i,(node,port) in enumerate(self.nodeAndPortList):
            connection = IotlabNodeConnection(
                self.args, self.scheduler, i, node, port)
            connection.connect()
            connectionTable[i] = connection

        self.connectionTable = connectionTable

    def run(self):
        self.scheduler.run()

    def runAndCleanUp(self):
        try:
            self.run()
        except:
            self.cleanUp()
            sys.stderr.write("\n\r")
            traceback.print_exc()
            sys.exit(1)

    def cleanUp(self):
        if self.termAttr != None:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.termAttr)

#---------------------------------------------------------------------------

def hasStdinData():
    return len(select.select([sys.stdin], [], [], 0)[0]) > 0

def getNodeAndPortList(args):
    if args.nodes != None:
        return [(node, SerialTcpPort) for node in args.nodes]
    else:
        assert args.start_port != None
        return [("localhost", args.start_port+i) for i in range(args.nb_ports)]
    return args.nodeList

def areArgsConsistent(args):
    return ((args.nodes != None 
             and (args.start_port == None and args.nb_ports == None))
            or (args.nodes == None
                and (args.start_port != None and args.nb_ports != None)))

#---------------------------------------------------------------------------

def runAsCommand():
    parser = argparse.ArgumentParser()
    parser.add_argument("--nodes", nargs="*", default=None)
    parser.add_argument("--start-port", type=int, default=None)
    parser.add_argument("--nb-ports", type=int, default=None)
    parser.add_argument("experimentDir", type=str)
    args = parser.parse_args()

    assert areArgsConsistent(args)
    nodeAndPortList = getNodeAndPortList(args)
    print "NodePortList:", ",".join(["%s:%s" % np for np in nodeAndPortList])

    manager = ConnectionManager()
    manager.setUp(args, nodeAndPortList)
    manager.runAndCleanUp()

#---------------------------------------------------------------------------

if __name__ == "__main__":
    runAsCommand()

#---------------------------------------------------------------------------
