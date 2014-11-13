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

class RadioExperiment:
    def __init__(self, iotlab, exp, control):
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
                            for (node,localPort) 
                            in self.nodeAndPortList]
        return localAddressList

    #--------------------------------------------------

    def startExp(self):
        print "Starting experiment."
        self.control.start(self)

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
        self.control.notifyLine(line)
        #print "+", nodeIO, line

#---------------------------------------------------------------------------

class RadioExperimentControl:
    def __init__(self):
       self.radioExp = None

    def notifyLine(self, nodeIO, line):
        print nodeIO, line

    def start(self, radioExp):
        self.radioExp = radioExp

#---------------------------------------------------------------------------

control = RadioExperimentControl()
radioExp = RadioExperiment(iotlab, exp, control)
connectionManager = ConnectionTool.ConnectionManager(
    args, radioExp.getLocalAddressList(), radioExp)
radioExp.setConnectionManager(connectionManager)
radioExp.run()

#---------------------------------------------------------------------------

