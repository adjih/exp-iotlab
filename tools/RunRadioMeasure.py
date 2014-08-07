#! /usr/bin/python
#---------------------------------------------------------------------------
# Radio Experiment Control
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

import argparse, os, re
import IotlabHelper
import threading, thread
from IotlabHelper import extractNodeId, AllPossibleNodes
import ConnectionTool

#---------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument("--exp-id", type=int, default=None)
args = parser.parse_args()

IotlabHelper.setExpIdDefaultAsLastExp(args)
iotlab, exp = IotlabHelper.getHelperAndExp(args)

#---------------------------------------------------------------------------

class NodeIO:
    def __init__(self, connection, address, observer = None):
        self.address = address
        self.connection = connection
        self.buffer = ""
        self.observer = observer

    def write(self, data):
        self.connection.write(data)

    def notifyInput(self, data):
        #print "> %s" % self.address.split(".")[0], repr(data)
        self.buffer += data
        while True:
            pos = self.buffer.find("\n")
            if pos < 0:
                break
            line = self.buffer[:pos]
            self.buffer = self.buffer[pos+1:]
            if self.observer != None:
                self.observer.notifyLine(self, line)
            else:
                print "> %s" % self.address.split(".")[0], repr(data)

#---------------------------------------------------------------------------

class RadioExperiment(threading.Thread):
    def __init__(self, iotlab, exp, control):
        threading.Thread.__init__(self)
        self.name = 'ioThread'
        self.daemon = True
        self.queue = Queue.Queue()

        self.iotlab = iotlab
        self.exp = exp
        forwardByType = IotlabHelper.fromJson(
            self.exp.readFile("ssh-forward-port.json"))
        self.nodeAndPortList = forwardByType.get("radio-test")

        self.nbNode = len(self.nodeAndPortList)
        self.nodeOfConnId = {}
        self.control = control

    def setConnectionManager(self, manager):
        self.connectionManager = manager
        self.scheduler = manager.scheduler

    def getLocalAddressList(self):
        localAddressList = [("localhost",localPort) 
                            for (node,localPort) in self.nodeAndPortList]
        return localAddressList

    #--------------------------------------------------

    def startExp(self):
        print "Starting experiment."
        self.control.putQueue(("start", self))
        while True:
            msg = self.queue.get()
            if msg[0] == "send-all":
                print "send-all", repr(msg[1])
                self.sendAll(msg[1])

    def sendAll(self, command):
        for i in range(self.nbNode):
            nodeIO = self.nodeOfConnId[i]
            nodeIO.write(command)

    def run(self):
        connectionManager.createAllConnections()
        self.scheduler.run()

    #--------------------------------------------------
    
    # Callbacks (from observee RadioTestObserver) 
    def notifyInput(self, socketConnection, data):
        nodeIO = self.nodeOfConnId[socketConnection.connId]
        nodeIO.notifyInput(data)
        #print "> notifyInput %s %s" % (socketConnection.connId, repr(data))

    def notifyCreate(self, socketConnection):
        connId = socketConnection.connId
        #print "> notifyCreate %s" % socketConnection.connId,
        nodeAddress = self.nodeAndPortList[connId][0]
        nodeIO = NodeIO(socketConnection, nodeAddress, self)
        self.nodeOfConnId[connId] = nodeIO

        if len(self.nodeOfConnId) == self.nbNode:
            self.scheduler.addEvent(0, self.startExp, ())

    def notifyExit(self):
        print "> notifyExit"

    #---------------------------------------------------------------------------
    
    # Callback from observees NodeIO
    def notifyLine(self, nodeIO, line):
        print nodeIO
        self.control.putQueue(line)
        #print "+", nodeIO, line

    #---------------------------------------------------------------------------
        
    def putQueue(self, data): # thread-safe
        self.queue.put(data)


#---------------------------------------------------------------------------

import threading, Queue, traceback, sys, os

# A perfect use case for threads
class RadioExperimentControl(threading.Thread):
    def __init__(self, radioExp = None):
        threading.Thread.__init__(self)
        self.name = 'controlThread'
        self.daemon = True
        self.queue = Queue.Queue()
        self.radioExp = radioExp

    def putQueue(self, data): # thread-safe
        self.queue.put(data)
        
    def run(self):
        try:
            self.doRun()
        except:
            traceback.print_exc(file=sys.stdout)
            os._exit(1)
            thread.interrupt_main()

    def doRun(self):
        print "+ running control thread"
        cmd, data = self.queue.get()
        if cmd != "start":
            raise ValueError("pop queue -> not 'start'", (cmd,data))
        self.radioExp = data

        while not self.checkInvalid():
            print "+ synchronizing"

    def checkInvalid(self):
        self.send("invalid\n", 1.0)

    def send(self, message, timeOut):
        timeOutTimer = self.setTimeOut(timeOut)
        self.radioExp.putQueue(("send-all", message))
        while True:
            cmd, data = self.queue.get()
            print cmd, data
        self.cancelTimeOut(timeOutTimer)

    def setTimeOut(self, timeOut):
        return threading.Timer(timeOut, 
                               lambda: self.queue.put(("time-out",None)))
  
    def cancelTimeOut(self, timeOutTimer):
        timeOutTimer.cancel()
        if not self.queue.empty():
            print "warning XXX"

#---------------------------------------------------------------------------

control = RadioExperimentControl()
control.start()

radioExp = RadioExperiment(iotlab, exp, control)
connectionManager = ConnectionTool.ConnectionManager(
    args, radioExp.getLocalAddressList(), radioExp)
radioExp.setConnectionManager(connectionManager)
radioExp.start()

#---------------------------------------------------------------------------

threadList = [control, radioExp]

import time

while True:
    time.sleep(100)

#---------------------------------------------------------------------------

