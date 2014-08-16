#! /usr/bin/python
#---------------------------------------------------------------------------
# Radio Experiment Control
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

import argparse, os, re, sys, time, pprint
import IotlabHelper
from IotlabHelper import extractNodeId, AllPossibleNodes
import ConnectionTool

from os.path import join as J

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
                            for (node,localPort) in self.nodeAndPortList]
        return localAddressList

    #--------------------------------------------------

    def startExp(self):
        print "Starting experiment."
        self.control.start(self)

    def sendAll(self, command):
        self.sendTo(range(self.nbNode), command)

    def sendTo(self, idList, command):
        for i in idList:
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
        #print "+", nodeIO, line
        self.control.notifyLine(nodeIO.connection.connId, line)

#---------------------------------------------------------------------------

# the 
#PowerList = [
#    "-17", "-12", "-9", "-7", "-5", "-4", "-3", "-2", "-1",
#    "0", "0.7", "1.3", "1.8", "2.3", "2.8", "3"]

dbg = False

class RadioExperimentControl:
    def __init__(self, args):
       self.radioExp = None
       self.mainCoroutine = None
       self.receiverCoroutine = None
       self.unparsedList = []
       self.dbgState = {}
       self.args = args

    def start(self, radioExp):
        self.radioExp = radioExp
        self.mainCoroutine = self.runAsMainCoroutine()
        self._sendMainCoroutine(None) # start coroutine

    def notifyLine(self, i, line):
        if self.receiverCoroutine != None:
            self._sendReceiverCoroutine(("recv",i,line))
        else: 
            print i, repr(line)
            self.unparsedList.append((time.time(), i, line))

    def resetUnparsedList(self):
        result = self.unparsedList
        self.unparsedList = []
        return result

    #--------------------------------------------------

    def runAsMainCoroutine(self): # called only from 'start(...)
        
        # The main experiment-running loop
        #
        # this is using the 'coroutine' tricks with yield
        # you should read 'result = yield self.cmd_send(...)' as:
        # 'result = collect_mote_output_after_cmd(self.cmd_send(...))'

        name = time.strftime("%Y-%m-%d-%Hh%Mm%S")
        radioExpDirName = "radio-exp-" + name
        if self.args.dir != None:
            radioExpDirName = J(self.args.dir, radioExpDirName)
        os.mkdir(radioExpDirName)

        resourceInfo = self.radioExp.exp.cachedGetResources()
        IotlabHelper.writeFile(radioExpDirName+"/resources.pydat", 
                               repr(resourceInfo))
        All = "all"
        def Except(l): 
            return ("except", l)

        self.watchdogStart()

        print "+ start main coroutine"
        # Check every one is alive
        outTable,fullOutTable = yield self.sendSetChannel(All, 16)

        # Get tx power list from first node
        refId = 0
        table, unused = yield self.sendGetTxPowerList(refId)
        powerList = eval(table[refId])
        #powerList = [power for i,power in enumerate(powerList) if i%2 == 0]
        #powerList = ["-17", "-12", "-7", "-3", "0", "1.8", "3"]
        #powerList = ["0"]
        if args.power != None:
            powerList = [args.power]
        elif args.power_idx != None:
            powerList = [powerList[args.power_idx]]
        print "powerList:", powerList

        # Get uid of every node
        uidTable,unused = yield self.sendUid(All)

        # Run all experiments
        packetSize = self.args.packet_size
        nbPacket = self.args.nb_packet
        delayMs = self.args.delay

        if args.all_channel:
            channelList = range(11,27)
        else: channelList = [args.channel]

        idList = self.getIdList(All)
        #id = 0
        #channel = 16
        #powerStr = powerList[0]

        metaInfo = {
            "packetSize": packetSize,
            "nbPacket": nbPacket,
            "delayMs": delayMs,
            "channelList": channelList,
            "idList": idList,
            "nodeList": self.radioExp.nodeAndPortList,
            "launchTime": time.time(),
            "powerList": powerList,
            "version": {"major": 3},
            "uidTable": uidTable,
            "commandLine": sys.argv
            }
        
        IotlabHelper.writeFile(radioExpDirName+"/meta.pydat",
                               repr(metaInfo))
        self.resetUnparsedList()

        xmitId = 10000
        for power in powerList:
            for id in idList:
                for channel in channelList:
                    self.watchdogNotifyNewBurst()
                    startTime = time.time()
                    print id, power, channel, 
                    sys.stdout.flush()
                    # Run one experiment
                    infoChannel = yield self.sendSetChannel(All, channel)
                    infoClear = yield self.sendClear(All)
                    infoXmit = yield self.sendXmit(
                        id, xmitId, power, packetSize, nbPacket, delayMs)
                    time.sleep(0.1) # just in case
                    infoLock = yield self.sendLock(All)
                    infoShow = yield self.sendShow(All)
                    stopTime = time.time()
                    print stopTime - startTime
                    info = {
                        "startTime": startTime,
                        "stopTime": stopTime,
                        "senderIdx": id,
                        "power": power,
                        "channel": channel,

                        "cmdChannel": infoChannel,
                        "cmdClear": infoClear,
                        "cmdXmit": infoXmit,
                        "cmdLock": infoLock,
                        "cmdShow": infoShow,
                        "xmitId": xmitId,
                        "unparsed": self.resetUnparsedList()
                        }
                    fileName = (
                        radioExpDirName
                        +"/exp-i%s-p%s-c%s.pydat" % (id, power, channel))
                    IotlabHelper.writeFile(fileName, repr(info))
                    xmitId += 1

        IotlabHelper.writeFile(radioExpDirName+"/success.pydat", repr(True))
        yield "(the end)"

    #--------------------------------------------------
    # internals: manage coroutine stuff

    def _newReceiverCoroutine(self, coroutine):
        assert self.receiverCoroutine == None # we could keep a stack
        self.receiverCoroutine = coroutine
        self._sendReceiverCoroutine(None)

    def _sendReceiverCoroutine(self, data):
        data = self.receiverCoroutine.send(data)
        if data != None:
            self.receiverCoroutine = None # finished
            self._sendMainCoroutine(data)

    def _sendMainCoroutine(self, data):
        status = self.mainCoroutine.send(data)
        if status != None:
            print "FINISHED", status
            self.mainCoroutine = None
            sys.exit(0)

    #--------------------------------------------------
    # watchdog
    
    def watchdogStart(self):
        self.watchdogLastTime = time.time()
        self.watchdogCheck()
            
    def watchdogNotifyNewBurst(self):
        self.watchdogLastTime = time.time()

    def watchdogCheck(self):
        WatchdogInterval = 10 # sec
        currentTime = time.time()
        if (currentTime - self.watchdogLastTime) > self.args.timeout:
            sys.stderr.write("ERROR: watchdog time elapsed, dbgState:\n")
            pprint.pprint(self.dbgState, stream=sys.stderr)
            sys.stderr.write("unparsed:\n")
            pprint.pprint(self.unparsedList, stream=sys.stderr)
            sys.exit(1)
        sys.stdout.write("=")
        sys.stdout.flush()
        self.radioExp.scheduler.addEvent(
            WatchdogInterval, self.watchdogCheck)

    #--------------------------------------------------
            
    def sendXmit(self, idListSpec, xmitId, power, 
                 packetSize, nbPacket, delayMs):
        idList = self.getIdList(idListSpec)
        cmd = "send %s %s %s %s %s" % (xmitId, power, packetSize, 
                                       nbPacket, delayMs)
        return self.sendAndWait(idListSpec, "\n"+cmd+"\n", "send ACK")

    def sendSetChannel(self, idListSpec, channel):
        if dbg: print ". set channel %s [%s]:" % (channel, idListSpec),
        idList = self.getIdList(idListSpec)
        if dbg: sys.stdout.flush()
        self.radioExp.sendTo(idList, "\nchannel %s\n" % channel)
        self.waitFor(idListSpec, "channel ACK")

    def sendGetTxPowerList(self, idListSpec):
        return self.sendAndWait(idListSpec, "\nget_tx_power_list\n", "[")

    def sendUid(self, idListSpec):
        return self.sendAndWait(idListSpec, "\nuid\n", "uid=")

    def sendClear(self, idListSpec):
        return self.sendAndWait(idListSpec, "\nclear\n", "clear ACK")

    def sendLock(self, idListSpec):
        return self.sendAndWait(idListSpec, "\nlock\n", "lock ACK")

    def sendShow(self, idListSpec):
        return self.sendAndWait(idListSpec, "\nshow\n", "'nbPacket'")
        
    def sendAndWait(self, idListSpec, line, expected):
        idList = self.getIdList(idListSpec)
        self.radioExp.sendTo(idList, line)
        self.waitFor(idListSpec, expected)

    def waitFor(self, idListSpec, expectedText):
        #dbg = True
        idList = self.getIdList(idListSpec)
        def _waitFor():
            waitedSet = set(idList)
            result = {}
            fullResult = {}
            while len(waitedSet) > 0:
                self.dbgState = {"waited":waitedSet, "result": result, 
                                "fullResult": fullResult}
                info = yield
                assert info[0] == "recv"
                i = info[1]
                line = info[2]
                if i in waitedSet and line.find(expectedText) >= 0:
                    if dbg: sys.stdout.write("*%s" % len(waitedSet))
                    waitedSet.remove(i)
                    result[i] = line
                else:
                    if dbg: sys.stdout.write(".")
                if i not in fullResult:
                    fullResult[i] = []
                fullResult[i].append((time.time(),line))
                if dbg: sys.stdout.flush()
            self.dbgState = None
            if dbg: print
            yield result, fullResult
            
        self._newReceiverCoroutine(_waitFor())

    #--------------------------------------------------
    # convenience method

    def getIdList(self, idListSpec):
        if isinstance(idListSpec, int):
            return [idListSpec]
        elif isinstance(idListSpec,basestring):
            if idListSpec == "all":
                idList = range(self.radioExp.nbNode)
            else: raise ValueError("unknown spec", idListSpec)
        elif (isinstance(idListSpec, tuple) 
              and len(idListSpec) == 2
              and idListSpec[0] == "except"):
            allSet = set(self.getIdList("all"))
            excludedSet = set(self.getIdList(idListSpec[1]))
            assert excludedSet.issubset(allSet)
            idList = list(sorted(allSet.difference(excludedSet)))
        else: idList = idListSpec
        return idList

#---------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument("--exp-id", type=int, default=None)
parser.add_argument("--power-idx", type=int, default=None)
parser.add_argument("--power", type=str, default=None)
parser.add_argument("--delay", type=int, default=1)
parser.add_argument("--packet-size", type=int, default=50)
parser.add_argument("--nb-packet", type=int, default=100)
parser.add_argument("--all-channel", action="store_true", default=False)
parser.add_argument("--channel", type=int, default=11)
parser.add_argument("--timeout", type=int, default=60)
parser.add_argument("--dir", type=str, default=None)
args = parser.parse_args()

IotlabHelper.setExpIdDefaultAsLastExp(args)
iotlab, exp = IotlabHelper.getHelperAndExp(args)

# ./expctl ssh-forward --type radio-test

control = RadioExperimentControl(args)
radioExp = RadioExperiment(iotlab, exp, control)
connectionManager = ConnectionTool.ConnectionManager(
    args, radioExp.getLocalAddressList(), radioExp)
radioExp.setConnectionManager(connectionManager)
radioExp.run()

#---------------------------------------------------------------------------
