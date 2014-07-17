#! /usr/bin/python
#---------------------------------------------------------------------------
# [Jul2014] Copied from NC-iotlab/src/ExpManager.py and modified from that
#
# Cedric Adjih, Inria, 2010-2014
#---------------------------------------------------------------------------

import socket, sys, argparse, time, os, select
import traceback, tty, termios, struct
import warnings

import Scheduler

from IotlabHelper import SerialTcpPort
import SnifferHelper

MaxDataLength = 100

#---------------------------------------------------------------------------

def S(x):
    sys.stdout.write("> "+x+"\n")
    os.system(x)

#---------------------------------------------------------------------------

class SocketConnection:
    def __init__(self, manager, connId, node, port, sd=None):
        self.manager = manager
        self.scheduler = manager.scheduler
        self.args = manager.args
        self.connId = connId
        self.node = node
        self.port = port
        self.sd = sd

    def connect(self):
        print "  connection #%s to node %s:%s" % (
            self.connId, self.node, self.port)
        if self.sd == None:
            self.sd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sd.connect((self.node, self.port))
        self.scheduler.addFdHandler(Scheduler.FunctionalFdHandler(
                self.sd, waitInputFunc = lambda: True,
                handleInputFunc = self.eventInput))

    def eventInput(self):
        data = self.sd.recv(MaxDataLength)
        if data == "":
            #print "finished"
            #finished # XXX:TODO
            print "eof/error with connection #%d" % self.connId
            return
        observer = self.manager.observer
        if observer != None:
            observer.notifyInput(self, data)

    def write(self, data):
        self.sd.send(data)

#---------------------------------------------------------------------------

class ConnectionManager:
    def __init__(self, args, nodeAndPortList, observer=None):
        self.scheduler = Scheduler.RealTimeScheduler()
        self.termAttr = None
        self.state = "init"
        self.nodeAndPortList = nodeAndPortList
        self.args = args
        self.observer = observer

    def createAllConnections(self):
        print "-- Connecting to nodes"
        connectionTable = {}

        for i,(node,port) in enumerate(self.nodeAndPortList):
            connection = SocketConnection(self, i, node, port)
            connection.connect()
            connectionTable[i] = connection
            if self.observer != None:
                self.observer.notifyCreate(connection)

        self.connectionTable = connectionTable
        self.state = "connected"

    def run(self):
        self.scheduler.run()

    def runAndCleanUp(self):
        try:
            self.run()
        except:
            if self.observer != None:
                self.observer.notifyExit()
            self.cleanUp()
            sys.stderr.write("\n\r")
            traceback.print_exc()
            sys.exit(1)

    def cleanUp(self):
        if self.termAttr != None:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.termAttr)

#---------------------------------------------------------------------------
# XXX: NOT USED !

FmtHeader = "!fBH"

def iterRecordedFile(fileName):
    f = open(fileName)
    headerSize = struct.calcsize(FmtHeader)
    while True:
        data = f.read(headerSize)
        if len(data) == 0:
            break # end of file
        assert len(data) == headerSize
        clock, snifferId, dataSize = struct.unpack(FmtHeader, data)
        data = f.read(dataSize)
        yield (clock, snifferId, data)
    f.close()
     
class ReplayManager:
    def __init__(self, fileName, observer):
        self.fileName = fileName
        self.bufferOf = {}
        self.observer = observer

    def getSnifferIdList(self):
        # warning: this reads the whole file
        return list(set(
                ( snifferId for (clock, snifferId, data) 
                  in iterRecordedFile(self.fileName) )  ))
            
    def replay(self, realTime=False):
        isFirstTime = True
        for (clock, snifferId, data) in iterRecordedFile(self.fileName):
            #print clock, snifferId, repr(data)
            if realTime:
                if isFirstTime: 
                    startTime = time.time() - clock
                    isFirstTime = False
                currentTime = time.time()
                delay = (startTime + clock) - time.time()
                if delay > 0:
                    time.sleep(delay)
            lastData = self.bufferOf.get(snifferId, "")
            if self.observer != None:
                newData = self.observer(clock, snifferId, lastData + data)
            else: 
                print clock, snifferId, repr(lastData+data)
                newData = ""

            self.bufferOf[snifferId] = newData

def runReplay(fileName, sniffer, realTime=True):
    replay = ReplayManager("sniffer-rpl.log", None)
    #print replay.getSnifferIdList()
    replay.replay(realTime)

#runReplay("sniffer-rpl.log", None)

#---------------------------------------------------------------------------

def hasStdinData():
    return len(select.select([sys.stdin], [], [], 0)[0]) > 0

def getNodeAndPortList(args):
    if args.nodes != None:
        currentPort = args.start_port
        result = []
        for nodeStr in args.nodes:
            tokenList = nodeStr.split(":")
            if len(tokenList) > 2:
                raise ValueError("Bad node+port format", nodeStr)
            elif len(tokenList) == 2:
                node = tokenList[0]
                port = int(tokenList[1])
            elif len(tokenList) == 1:
                node = tokenList[0]
                port = currentPort
                currentPort += 1 # must have option --start-port
            else: raise RuntimeError("impossible case", tokenList)
            result.append((node, port))
        return result
    else:
        assert args.start_port != None
        return [("localhost", args.start_port+i) for i in range(args.nb_ports)]


def areArgsConsistent(args):
    return ((args.nodes != None 
             and (args.start_port == None and args.nb_ports == None))
            or (args.nodes == None
                and (args.start_port != None and args.nb_ports != None)))

#---------------------------------------------------------------------------

class AbstractConnectionObserver:
    def notifyCreate(self, socketConnection): abstract
    def notifyInput(self, socketConnection, data): abstract
    def notifyExit(self): abstract

# XXX: NOT USED
class TeeConnectionObserver:
    def __init__(self, *observerList):
        self.observerList = observerList
        
    def notifyCreate(self, socketConnection):
        for observer in self.observerList:
            observer.notifyCreate(socketConnection)

    def notifyInput(self, socketConnection, data):
        for observer in self.observerList:
            observer.notifyInput(socketConnection, data)

    def notifyExit(self):
        for observer in self.observerList:
            observer.notifyExit()

# XXX: NOT USED
class MuxConnectionObserver:
    def __init__(self, observerOfConnectId):
        self.observerOfConnectId = observerOfConnectId

    def notifyCreate(self, socketConnection):
        connId = socketConnection.connId
        observer = self.observerOfConnectId[connId]
        return observer.notifyCreate(socketConnection)

    def notifyInput(self, socketConnection, data):
        connId = socketConnection.connId
        observer = self.observerOfConnectId[connId]
        return observer.notifyInput(socketConnection, data)

    def notifyExit(self):
        warnings.warn("Not implemented yet. XXX")


class StdoutConnectionObserver:
    def notifyInput(self, socketConnection, data):
        print "> notifyInput %s %s" % (socketConnection.connId, repr(data))

    def notifyCreate(self, socketConnection):
        print "> notifyCreate %s" % socketConnection.connId

    def notifyExit(self):
        print "> notifyExit"


def popStruct(spec, data):
    specSize = struct.calcsize(spec)
    result = struct.unpack(spec, data[:specSize])
    return result, data[specSize:]


#--------------------------------------------------

class Foren6SnifferConnectionObserver:
    def __init__(self, observer):
        self.parserTable = {}
        self.observer = observer

    def notifyInput(self, socketConnection, data):
        #print "foren6",repr(data)
        connId =  socketConnection.connId
        assert connId in self.parserTable
        self.parserTable[connId].notifyData(data)

    def notifyCreate(self, socketConnection):
        connId = socketConnection.connId        
        self.parserTable[connId] = SnifferHelper.Foren6SnifferParser(
            connId, self.observer)

    def notifyExit(self):
        pass

#---------------------------------------------------------------------------

def runAsCommand():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    ncParser = subparsers.add_parser("connect")
    ncParser.add_argument("--start-port", type=int, default=None)
    ncParser.add_argument("--nb-ports", type=int, default=None)
    ncParser.add_argument("--nodes", nargs="*", default=None)

    ncParser.add_argument("--input", type=str,
                          choices=["dump", "foren6", "serial-zep"],
                          default="dump")

    ncParser.add_argument("--output", type=str,
                          choices=["wireshark", "socat", "tshark", "text"],
                          default="wireshark")


    ncParser.add_argument("--record-packet", type=str, default=None)
    ncParser.add_argument("--record", type=str, default=None)

    ncParser.add_argument("--unique", action="store_true", default=False)


    args = parser.parse_args()
    assert areArgsConsistent(args)
    nodeAndPortList = getNodeAndPortList(args)
    print "NodePortList:", ",".join(["%s:%s" % np for np in nodeAndPortList])

    if args.command == "connect":

        if args.input in ["foren6", "serial-zep"]:
            if args.output == "wireshark":
                outputObserver = SnifferHelper.ZepSenderObserver()
            elif args.output == "socat":
                outputObserver = SnifferHelper.SocatObserver()
            elif args.output == "tshark":
                outputObserver = SnifferHelper.TsharkSenderObserver()
            elif args.output == "text":
                outputObserver = SnifferHelper.TextDisplayObserver()
            else: raise ValueError("Unknown output type", args.output)

            if args.unique:
                outputObserver = SnifferHelper.UniqueFilterObserver(
                    outputObserver)

            if args.record_packet != None:
                outputObserver = SnifferHelper.RecordPacketObserver(
                    args.record_packet, outputObserver)
            
        if args.input == "foren6":
            observer = Foren6SnifferConnectionObserver(outputObserver)
        elif args.input == "serial-zep":
            observer = SerialZepConnectionObserver(outputObserver)
        elif args.input == "dump":
            observer = StdoutConnectionObserver()
        else: raise RuntimeError("impossible case", args.input)
            
        manager = ConnectionManager(args, nodeAndPortList, observer)
        manager.createAllConnections()
        manager.runAndCleanUp()

#---------------------------------------------------------------------------

if __name__ == "__main__":
    runAsCommand()

#---------------------------------------------------------------------------
