#! /usr/bin/python
#---------------------------------------------------------------------------
# Cedric Adjih - INRIA Hipercom - 2010
#---------------------------------------------------------------------------

import socket, sys, optparse, time, os, select
import traceback, tty, termios

import Scheduler
#import SensToolManager

#from SensToolManager import BaseExperimentPort
BaseExperimentPort = 20000
BaseProxyPort = 17000
MaxDataLength = 10

#---------------------------------------------------------------------------

def S(x):
    sys.stdout.write("> "+x+"\n")
    os.system(x)

#--------------------------------------------------

def syntax():
    sys.stderr.write("Syntax: %s <number of nodes>\n" % sys.argv[0])
    sys.exit(1)

#--------------------------------------------------

def startProcess(argList, withXterm = False, xtermOptionList=[], 
                 withSocketPair = False):
    print "[starting process]", argList
    if not withXterm: realArgList = argList
    else: realArgList = ["xterm"]+xtermOptionList+["-e"]+argList

    if withSocketPair:
        sd1, sd2 = socket.socketpair()
        process = subprocess.Popen(realArgList, 
                                   stdin=sd2, stdout=sd2, stderr=sd2)
    else: 
        process = subprocess.Popen(realArgList)
        sd1, sd2 = None, None
    return process, sd1

#---------------------------------------------------------------------------

# [Aug2010] Parts copied from AllSerena/admin/SerenaRemoteSchedulerServer.py
class LocalConnection:
    def __init__(self, nodeConnection, clientSocket):
        self.scheduler = nodeConnection.scheduler
        self.nodeConnection = nodeConnection
        self.clientSocket = clientSocket

        self.clientSocketInput = Scheduler.BufferedInputFdHandler(
            self.clientSocket.fileno(), self.clientSocket.recv,
            self.eventSocketInput, self.eventSocketClose)
        self.clientSocketOutput = Scheduler.BufferedOutputFdHandler(
            self.clientSocket.fileno(), self.clientSocket.send)
        self.scheduler.addFdHandler(self.clientSocketInput)
        self.scheduler.addFdHandler(self.clientSocketOutput)
       
    def eventSocketInput(self):
        data = self.clientSocketInput.peek()
        rawMessage = self.clientSocketInput.read(len(data))
        assert rawMessage == data
        self.nodeConnection.write(data)

    def eventSocketClose(self):
        self.scheduler.removeFdHandler(self.clientSocketInput)
        self.scheduler.removeFdHandler(self.clientSocketOutput)
        
    def write(self, data):
        self.clientSocketOutput.write(data)

#---------------------------------------------------------------------------

class SenslabNodeConnection:
    def __init__(self, config, scheduler, nodeId, sd=None):
        self.config = config
        self.scheduler = scheduler
        self.nodeId = nodeId
        self.sd = sd
        
        if self.config.shouldLog:
            self.log = open(self.config.resultDir+"/log.%d" % self.nodeId, "w")
        else: self.log = None

        self.clientList = []

    def connect(self):
        print "  connecting to node %s" % self.nodeId
        if self.sd == None:
            serverName = self.config.serverName
            self.sd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            serverName = "node%s" % self.nodeId
            #self.sd.connect((serverName, BaseExperimentPort+self.nodeId))
            self.sd.connect((serverName, BaseExperimentPort))
        self.scheduler.addFdHandler(Scheduler.FunctionalFdHandler(
                self.sd, waitInputFunc = lambda: True,
                handleInputFunc = self.eventInput))
        #self.sd.send("t\n")
        #self.clientSocketInput = Scheduler.BufferedInputFdHandler(
        #    self.clientSocket.fileno(), self.clientSocket.recv,
        #    self.eventSocketInput, self.eventSocketClose)
        #self.clientSocketOutput = Scheduler.BufferedOutputFdHandler(
        #    self.clientSocket.fileno(), self.clientSocket.send)
        #self.scheduler.addFdHandler(self.clientSocketInput)
        #self.scheduler.addFdHandler(self.clientSocketOutput)
        self.createListenSocket()

    def createListenSocket(self):
        self.listenSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listenSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        self.listenSocket.bind(("", BaseProxyPort+self.nodeId))
        self.listenSocket.listen(10000)
        self.scheduler.addFdHandler(Scheduler.FunctionalFdHandler(
                self.listenSocket, waitInputFunc = lambda: True,
                handleInputFunc = self.eventClientConnection))

    def eventClientConnection(self):
        clientSocket, address = self.listenSocket.accept()
        print "[proxy/serial] Client connection from address:", address
        if address[0] != "127.0.0.1": 
            raise RuntimeError(("client from different machine", address))
        client = LocalConnection(self, clientSocket)
        self.clientList.append(client)

    def eventInput(self):
        data = self.sd.recv(MaxDataLength)
        if data == "":
            #finished # XXX:TODO
            return
        if self.log != None:
            self.log.write(repr((time.time(), "out", data))+"\n")
            if self.config.withFlush: self.log.flush()
        #sys.stdout.write("[%d|" % self.nodeId +data+"]")
        #sys.stdout.flush()
        for client in self.clientList:
            client.write(data)

    def write(self, data):
        if self.log != None:
            self.log.write(repr((time.time(), "in", data))+"\n")
        self.sd.send(data)

#---------------------------------------------------------------------------

def hasStdinData():
    return len(select.select([sys.stdin], [], [], 0)[0]) > 0


def getNodeIdList(argList):
    result = []
    for token in argList:
        for spec in token.split("+"):
            if spec.find("-") > 0:
                start,stop = spec.split("-")
                result += range(int(start), int(stop)+1)
            else: result.append(int(spec))
    return result

def S(x):
    print "### ", x
    os.system(x)

class NodeManager:
    def __init__(self):
        self.scheduler = Scheduler.RealTimeScheduler()
        self.termAttr = None
        self.wsnetManager = None


    def resetExperiment(self):
        S("node-cli --start")
        time.sleep(10)
        S("node-cli --reset")
        time.sleep(10)
        print "<started>"

    def run(self, config, argList):
        self.config = config
        if config.simulConfigFileName != None:
            # Using a wsnet/wsim simulator
            S("killall wsim-senslabv14 wsnet")
            wsnetManager = SensToolManager.WSNetManager(self.scheduler, config)
            wsnetManager.start()
            sdTable = wsnetManager.sdTable
            nodeIdList = sorted(sdTable.keys())
            config.serverName = "localhost"
            config.resultDir = wsnetManager.simul.getFullFileName("")
        else:
            # Connecting for real in senslab
            if len(argList) < 1:
                syntax()
            nodeIdList = getNodeIdList(argList)
            print "NodeIdList:", nodeIdList
            #nbNode = int(argList[0])
            #nodeIdList = range(nbNode)
            #config.nbNode = nbNode
            sdTable = {}
            config.serverName = "experiment"
            config.resultDir = "result"
            try: os.mkdir(config.resultDir)
            except: pass
            wsnetManager = None

        self.wsnetManager = wsnetManager
        self.nodeIdList = nodeIdList
        self.createAllConnection()
        self.resetExperiment()
        self.redirectInputToNode(0)

        if config.shouldStartXterm:
            print "-- Starting xterm"
            for nodeId in nodeIdList:
                xtermProcess,unused = SensToolManager.startProcess(
                    ["telnet", "localhost", "%s" % (BaseProxyPort+nodeId)],
                    True, ["-T", "Node %s" % nodeId])
                self.wsnetManager.processManager.add(xtermProcess)

        self.scheduler.run()

    def createAllConnection(self):
        print "-- Connecting to nodes"
        connectionTable = {}

        for nodeId in self.nodeIdList:
            connection = SenslabNodeConnection(self.config, self.scheduler, 
                                               nodeId)
            connection.connect()
            connectionTable[nodeId] = connection

        self.connectionTable = connectionTable

    #http://stackoverflow.com/questions/2408560/python-nonblocking-console-input
    def redirectInputToNode(self, nodeId):
        if self.termAttr == None:
            try:
                self.termAttr = termios.tcgetattr(sys.stdin)
            except: 
                print "[WARNING] cannot termios.tcgetattr(sys.stdin)"
                #return
        #tty.setcbreak(sys.stdin.fileno())
        
        try:
            tty.setraw(sys.stdin.fileno())
        except:
            print "[WARNING] cannot tty.setraw(...)"
            #return

        self.scheduler.addFdHandler(Scheduler.FunctionalFdHandler(
                sys.stdin, waitInputFunc = lambda: True,
                handleInputFunc = lambda: self.eventStdinInfo(nodeId)))

    def eventStdinInfo(self, nodeId):
        data = ""
        while hasStdinData():
            c = sys.stdin.read(1)
            if c == chr(3): raise RuntimeError("Ctrl-C pressed")
            data += c
        #print "event[%s]" % data
        print "STOPPED"
        sys.exit(0)

        sys.stdout.write(data)
        self.connectionTable[nodeId].sd.send(data)

    def cleanUp(self):
        if self.wsnetManager != None:
            self.wsnetManager.killAllProcess()
        if self.termAttr != None:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.termAttr)

#---------------------------------------------------------------------------

parser = optparse.OptionParser()
parser.add_option("--log", dest="shouldLog", default=False, action="store_true")
parser.add_option("--simul", dest="simulConfigFileName", default=None)
#parser.add_option("--restart", dest="restartNode", default=None)
parser.add_option("--xterm", dest="shouldStartXterm", 
                  action="store_true", default=False)
parser.add_option("--flush", dest="withFlush", 
                  action="store_true", default=False)
parser.add_option("--gdb-node", dest="dbgNodeId", default="None")
(optionTable, argList) = parser.parse_args()

config = optionTable
manager = NodeManager()
try:
    manager.run(config, argList)
except:
    manager.cleanUp()
    sys.stderr.write("\n\r")
    traceback.print_exc()
    sys.exit(1)

#---------------------------------------------------------------------------

# -> http://www.python.org/search/hypermail/python-1993/0020.html
#os.system("stty raw")

#---------------------------------------------------------------------------
