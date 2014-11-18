#! /usr/bin/python
#---------------------------------------------------------------------------
# [Jul2014] Copied from NC-iotlab/src/ExpManager.py and modified from that
#
# Cedric Adjih, Inria, 2010-2014
#---------------------------------------------------------------------------

import socket, sys, argparse, time, os, select, struct
import traceback, tty, termios, struct
import warnings

import Scheduler

from IotlabHelper import SerialTcpPort, fromJson, extractNodeId, extractNodeName
import SnifferHelper
import RiotTvParser

MaxDataLength = 100

#---------------------------------------------------------------------------

def S(x):
    sys.stdout.write("> "+x+"\n")
    os.system(x)

#---------------------------------------------------------------------------

def makeStruct(**kw):
    return type("Struct", (), kw)

#---------------------------------------------------------------------------
# Command
#---------------------------------------------------------------------------

def prependSize(code):
    return struct.pack("!B", len(code)) + code

#---------------------------------------------------------------------------
# [Nov2014] Copied from WSNColor/contiki/z1, itself:
# [Apr2012] copied from AllSerena/admin/SerenaRemoteSchedulerServer.py
#---------------------------------------------------------------------------

def addSizeHeader(data):
    return struct.pack("!I", len(data))+data

class GenericClient:

    def __init__(self, scheduler, clientSocket, address,
                 sendDataFunction, closeClientFunction, sizeFormat = None):
        self.address = address
        self.scheduler = scheduler
        self.clientSocket = clientSocket

        self.clientSocketInput = Scheduler.BufferedInputFdHandler(
            self.clientSocket.fileno(), self.clientSocket.recv,
            self.eventSocketInput, self.eventSocketClose)
        self.clientSocketOutput = Scheduler.BufferedOutputFdHandler(
            self.clientSocket.fileno(), self.clientSocket.send)
        self.scheduler.addFdHandler(self.clientSocketInput)
        self.scheduler.addFdHandler(self.clientSocketOutput)
        self.sendDataFunction = sendDataFunction
        self.closeClientFunction = closeClientFunction
        self.sizeFormat = (sizeFormat, 0)
        self.state = "connected"
        
    def eventSocketInput(self):
        if self.sizeFormat == None:
            self.sendDataFunction(self.clientSocketInput.read(), self.address)
            return
        headerSpec, sizePos = self.sizeFormat
        headerSize = struct.calcsize(headerSpec)
        data = self.clientSocketInput.peek()
        if len(data) >= headerSize:
            info = struct.unpack(headerSpec, data[0:headerSize])
            messageSize = info[sizePos]
            if len(data) >= headerSize + messageSize:
                unusedRawMessageSize = self.clientSocketInput.read(headerSize)
                rawMessage = self.clientSocketInput.read(messageSize)
                self.sendDataFunction(rawMessage, self.address)

    def eventSocketClose(self):
        self.scheduler.removeFdHandler(self.clientSocketInput)
        self.scheduler.removeFdHandler(self.clientSocketOutput)
        if self.state == "connected":
            self.closeClientFunction(self.address, self)
            self.state == "deleted"

    def write(self, data):
        self.clientSocketOutput.write(data)

    #def _getReprTime(self):
    #    clock1 = time.time()
    #    return self._reprTime(clock1)

    #def _reprTime(self, clock):
    #    date = datetime.datetime.fromtimestamp(clock)
    #    return date.strftime("%H:%M:%S.%f")


class GenericTcpServer:

    def __init__(self, config, scheduler, clientFactory = None):
        self.config = config
        self.scheduler = scheduler
        self.clientTable = {}
        self.createSocket()
        if clientFactory == None:
            clientFactory = self.defaultCreateClient
        self.clientFactory = clientFactory

    def createSocket(self):
        self.listenSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listenSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        self.listenSocket.bind(("", self.config.port))
        self.listenSocket.listen(10000)
        
        self.scheduler.addFdHandler(Scheduler.FunctionalFdHandler(
                self.listenSocket, waitInputFunc = lambda: True,
                handleInputFunc = self.eventClientConnection))

    def eventClientConnection(self):
        clientSocket, address = self.listenSocket.accept()
        self.log("[tcp-server] Client connection from address:"
                 + repr(address)+"\n")
        if address[0] != "127.0.0.1": 
            raise RuntimeError(("client from different machine", address))
        client = self.clientFactory(self, clientSocket, address)
        self.clientTable[address] = client
        
    def removeClient(self, address, client):
        assert self.clientTable[address] == client
        del self.clientTable[address]
        self.log("[tcp-server] Client disconnected %s" %(client.address,)
                 + "/ now %s client(s)\n" % len(self.clientTable))

    def log(self, data):
        sys.stdout.write(data)
        sys.stdout.flush()

    def defaultCreateClient(self, myself, clientSocket, address):
        return GenericClient(self.scheduler, clientSocket, address,
                             self.defaultSendData,
                             self.removeClient, None)

    def defaultSendData(self, data, address):
        self.log("[send-data %s]%s\n" %(repr(data), address))

    def writeToAllClient(self, data):
        for client in self.clientTable.itervalues():
            client.write(data)

#---------------------------------------------------------------------------

class SocketConnection:
    def __init__(self, manager, connId, node, port, name, sd=None):
        self.manager = manager
        self.scheduler = manager.scheduler
        self.args = manager.args
        self.connId = connId
        self.node = node
        self.port = port
        self.name = name
        self.sd = sd
        self.proxyServer = None

    def getShortName(self):
        return extractNodeName(self.name)

    def getNodeId(self):
        return extractNodeId(self.name)

    def connect(self):
        print "  connection #%s to node %s:%s (%s)" % (
            self.connId, self.node, self.port, self.name)
        if self.sd == None:
            self.sd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sd.connect((self.node, self.port))
            if self.args.proxy:
                assert self.proxyServer == None
                config = makeStruct(port = self.port 
                                    + self.args.proxy_port_offset)
                self.proxyServer = GenericTcpServer(
                    config, self.scheduler, self.createClient)

        self.scheduler.addFdHandler(Scheduler.FunctionalFdHandler(
                self.sd, waitInputFunc = lambda: True,
                handleInputFunc = self.eventInput))

    def createClient(self, proxyServer, clientSocket, address):
        return GenericClient(self.scheduler, clientSocket, address,
                             self.eventClientData,
                             self.proxyServer.removeClient, None)
      
    def eventInput(self):
        data = self.sd.recv(MaxDataLength)
        if data == "":
            print "eof/error with connection #%d" % self.connId
            return
        observer = self.manager.observer
        if observer != None:
            observer.notifyInput(self, data)
            if self.proxyServer != None:
                self.proxyServer.writeToAllClient(data)

    def eventClientData(self, data, address):
        self.write(data)

    def write(self, data):
        self.sd.send(data)

#---------------------------------------------------------------------------

def matchName(nodeRef, address):
    nodeId = extractNodeId(address)
    shortName = extractNodeName(address)
    return (nodeRef == address or nodeRef == nodeId 
            or nodeRef == str(nodeId) or nodeRef == shortName)

class ConnectionManager:
    def __init__(self, args, nodePortNameList, observer=None):
        self.scheduler = Scheduler.RealTimeScheduler()
        self.termAttr = None
        self.state = "init"
        self.nodePortNameList = nodePortNameList
        self.args = args
        self.observer = observer

        if self.args.mux:
            self.muxServerStart()
        else: self.muxServer = None

    def createAllConnections(self):
        print "-- Connecting to nodes"
        connectionTable = {}

        for i,(node,port,name) in enumerate(self.nodePortNameList):
            connection = SocketConnection(self, i, node, port, name)
            connection.connect()
            connectionTable[i] = connection
            if self.observer != None:
                self.observer.notifyCreate(connection)

        self.connectionTable = connectionTable
        self.state = "connected"

    #--------------------------------------------------

    def muxServerStart(self):
        config = makeStruct(port = self.args.mux_port)
        self.muxServer = GenericTcpServer(
            config, self.scheduler, self.muxCreateClient)

    def muxCreateClient(self, muxServer, clientSocket, address):
        return GenericClient(self.scheduler, clientSocket, address,
                             self.muxEventClientData,
                             self.muxServer.removeClient, "!I")

    def muxEventClientData(self, data, address):
        command = fromJson(data)
        self.muxEventClientCommand(command)

    def muxEventClientCommand(self, command):
        if "type" not in command:
            raise RuntimeError("cannot understand command", command)

        cmd = command["type"]
        if cmd == "send":
            connId = command.get("socket-id", None)
            name = command.get("name", None)
            for connection in self.connectionTable.values():
                ok = ((connId == None or connId == connection.connId)
                      and (name == None or matchName(name, connection.name)))
                if command.get("exclude", False):
                    ok = not ok
                if ok:
                    connection.write(command["data"])
    
    #--------------------------------------------------

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

def getNodePortNameList(args):
    if args.nodes != None:
        currentPort = args.start_port
        result = []
        for nodeStr in args.nodes:
            tokenList = nodeStr.split(":")
            if len(tokenList) > 3:
                raise ValueError("Bad node+port format", nodeStr)
            elif len(tokenList) == 3:
                node = tokenList[0]
                port = int(tokenList[1])
                name = tokenList[2]
            elif len(tokenList) == 2:
                node = tokenList[0]
                port = int(tokenList[1])
                name = None
            elif len(tokenList) == 1:
                node = tokenList[0]
                port = currentPort
                currentPort += 1 # must have option --start-port
                name = None
            else: raise RuntimeError("impossible case", tokenList)
            result.append((node, port, name))
        return result
    else:
        assert args.start_port != None
        return [("localhost", args.start_port+i, None) 
                for i in range(args.nb_ports)]


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

#--------------------------------------------------

class LineConnectionObserver:
    def __init__(self, observer):
        self.parserTable = {}
        self.observer = observer
        
    def notifyInput(self, socketConnection, data):
        connId =  socketConnection.connId
        assert connId in self.parserTable
        newData = self.parserTable[connId] + data
        while True:
            pos = newData.find("\n")
            if pos < 0:
                break
            self.observer.notifyLine(socketConnection, newData[:pos+1])
            newData = newData[pos+1:]
        self.parserTable[connId] = newData

    def notifyCreate(self, socketConnection):
        connId = socketConnection.connId
        self.parserTable[connId] = ""

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
                          choices=["dump", "foren6", "serial-zep", "line"],
                          default="dump")

    ncParser.add_argument("--output", type=str,
                          choices=["wireshark", "socat", "tshark", "text",
                                   "wireshark+socat", "wireshark+smartrf",
                                   "riot-tv-reporter"],
                          default="wireshark")

    ncParser.add_argument("--record-packet", type=str, default=None)
    ncParser.add_argument("--record", type=str, default=None)

    ncParser.add_argument("--unique", action="store_true", default=False)

    ncParser.add_argument("--proxy", action="store_true", default=False)
    ncParser.add_argument("--proxy-port-offset", type=int, default=10000)
    ncParser.add_argument("--proxy-mode", choices=["unique", "mux"], 
                          default="unique") # not used

    ncParser.add_argument("--mux", action="store_true", default=False)
    ncParser.add_argument("--mux-port", type=int, default=19999)

    args = parser.parse_args()
    assert areArgsConsistent(args)
    nodePortNameList = getNodePortNameList(args)
    #print "NodePortNameList:", ",".join([
    #        "%s:%s:%s" % np for np in nodePortNameList])

    if args.command == "connect":

        if args.input in ["foren6", "serial-zep"]:
            if args.output == "wireshark":
                outputObserver = SnifferHelper.ZepSenderObserver()
            elif args.output == "socat":
                outputObserver = SnifferHelper.SocatObserver()
            elif args.output == "wireshark+socat":
                observer1 = SnifferHelper.ZepSenderObserver()
                observer1 = SnifferHelper.UniquePacketObserver(observer1)
                observer2 = SnifferHelper.SocatObserver()
                outputObserver = SnifferHelper.TeePacketObserver(
                    observer1, observer2)
            elif args.output == "wireshark+smartrf":
                observer1 = SnifferHelper.SmartRFSnifferSenderObserver()
                observer1 = SnifferHelper.UniquePacketObserver(observer1)
                observer2 = SnifferHelper.ZepSenderObserver()
                observer2 = SnifferHelper.UniquePacketObserver(observer2)
                outputObserver = SnifferHelper.TeePacketObserver(
                    observer1, observer2)
            elif args.output == "tshark":
                outputObserver = SnifferHelper.TsharkSenderObserver()
            elif args.output == "text":
                outputObserver = SnifferHelper.TextDisplayObserver()
            else: raise ValueError("Unknown output type", args.output)

            if args.unique:
                outputObserver = SnifferHelper.UniquePacketObserver(
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
        elif args.input == "line":
            if args.output == "riot-tv-reporter":
                parser = RiotTvParser.RiotTvParser(args)
            else: raise ValueError("Unknown output type", args.output)
            observer = LineConnectionObserver(parser)
        else: raise RuntimeError("impossible case", args.input)
            
        manager = ConnectionManager(args, nodePortNameList, observer)
        manager.createAllConnections()
        manager.runAndCleanUp()

#---------------------------------------------------------------------------

if __name__ == "__main__":
    runAsCommand()

#---------------------------------------------------------------------------
