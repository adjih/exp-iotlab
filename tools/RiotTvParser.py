#! /usr/bin/python
#---------------------------------------------------------------------------
# Cedric Adjih, Inria, 2014
#---------------------------------------------------------------------------

import re, sys, time
import socket, json

#---------------------------------------------------------------------------

BasePatternTable = {
    "address": "[transceiver] got address: <INT>\n",
    "select-parent": "VIZ: RPL <INT> selected parent: <INT>\n",
    "delete-parent": "VIZ: RPL <INT> deleted parent: <INT>\n",
    "dio": "fw <INT> <INT> <INT>\n"
}


PatternTable = {}

for name, value in BasePatternTable.iteritems():
    #value = re.sub("(10[.]([0-9.]+))", "<IP>", value)
    #value = re.sub("([0-9]+)", "<INT>", value)
    value = value.replace("[", ".").replace("]", ".") # XXX

    #value = value.replace("<IP>", "([x0-9a-f]+)")
    value = value.replace("<INT>", "([-]?[x0-9a-f]+)")
    #value = value.replace("<PYDAT>", ".*([{].+)")
    #print value
    PatternTable[name] = re.compile(value)

def findMatchInTable(data, patternTable):
    for rName,r in patternTable.iteritems():
        m = r.search(data)
        if m != None: break
    if m == None:
        return None, None
    else: return rName, m

#---------------------------------------------------------------------------

AnchorPort = 23511

class RiotTvReporter:
    def __init__(self):
        sd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sd.connect(("localhost", AnchorPort))
        self.sd = sd

    def sendData(self, data):
        clock = 0
        info = {'type': 'raw', 'data': data, 'time': int(time.time())}
        tmpData = json.dumps(info)
        rawData = "%s#"%len(tmpData) + tmpData
        #rawData = '84#{"type":"raw","data":"p_s: ID sn10 selected ID sn11 as parent","time":1415750499304}'
        #print ("SEND:", rawData)
        self.sd.send(rawData)

    def sendEventSelectParent(self, nodeChild, nodeParent):
        data = "p_s: ID %s selected ID %s as parent" % (nodeChild, nodeParent)
        self.sendData(data)

    def sendEventDeleteParent(self, nodeChild, nodeParent):
        data = "p_d: ID %s deleted ID %s as parent" % (nodeChild, nodeParent)
        self.sendData(data)

    def sendEventRank(self, name, rank):
        data = "r: ID %s selected rank %s" % (name, rank)
        self.sendData(data)

    def sendEventDio(self, receiver, sender):
        color = "2"
        data = "m: ID %s received msg DIO from ID %s #color%s" % (
            receiver, sender, color)
        self.sendData(data)

#---------------------------------------------------------------------------

class RiotNode:
    def __init__(self, parser, socketConnection):
        self.socketConnection = socketConnection
        self.parser = parser

    def notifyLine(self, line):
        name = self.socketConnection.getShortName()
        event, m = findMatchInTable(line, PatternTable)
        reprName = name.ljust(6)
        if event == "address":
            shortAddress = int(m.group(1))
            print "%s: ***ADDRESS %04x" % (reprName, shortAddress)
            self.parser.notifyNodeRiotAddress(name, shortAddress, self)

        elif event == "dio":
            myRiotAddress = int(m.group(1), 16)
            otherRiotAddress = int(m.group(3), 16)
            self.parser.notifyNodeRiotAddress(name, myRiotAddress, self)
            if otherRiotAddress in self.parser.addressTable:
                otherName = self.parser.addressTable[otherRiotAddress]
            else: otherName = None
            print "%s: ***DIO %04x(%s)->%04x(%s)" % (
                reprName, otherRiotAddress, otherName, myRiotAddress, name)
            if otherName != None:
                self.parser.reporter.sendEventDio(name, otherName)

        elif event == "select-parent" or event == "delete-parent":
            myRiotAddress = int(m.group(1), 16)
            otherRiotAddress = int(m.group(2), 16)
            self.parser.notifyNodeRiotAddress(name, myRiotAddress, self)
            if otherRiotAddress in self.parser.addressTable:
                otherName = self.parser.addressTable[otherRiotAddress]
            else: otherName = None
            if event == "select-parent":
                eventRepr = "PARENT"
                if otherName != None:
                    self.parser.reporter.sendEventSelectParent(name, otherName)
            else: 
                eventRepr = "NO-PARENT"
                if otherName != None:
                    self.parser.reporter.sendEventDeleteParent(name, otherName)
            print "%s: ***%s %04x(%s)->%04x(%s)" % (
                reprName, eventRepr, 
                otherRiotAddress, otherName, myRiotAddress, name)
        elif event != None:
            sys.stdout.write("%s: {%s} %s" % (reprName, event, line))
        else:
            sys.stdout.write("%s> %s" % (reprName, line))


class RiotTvParser:
    def __init__(self, args):
        self.args = args
        self.nodeTable = {}
        self.addressTable = {}
        self.reporter = RiotTvReporter()
        
    def notifyNodeRiotAddress(self, name, shortAddress, node):
        if (shortAddress in self.addressTable
            and name != self.addressTable[shortAddress]):
            print "******* address change", self.addressTable[shortAddress], \
                shortAddress, name
        self.addressTable[shortAddress] = name

    def notifyLine(self, socketConnection, line):
        connId = socketConnection.connId
        if connId not in self.nodeTable:
            node = RiotNode(self, socketConnection)
            self.nodeTable[connId] = node
        else: node = self.nodeTable[connId]
        node.notifyLine(line)

#---------------------------------------------------------------------------
