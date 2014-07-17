# Extra garbage


#---------------------------------------------------------------------------
# Not used
#---------------------------------------------------------------------------

if False:
    profileName = iotlab.ensureEmptyProfile()
    print profileName

    if len(expList) == 0:
        print ("No experience, starting one")
        #exp = iotlab.startExp("Rest", 10, "rocquencourt", 10)
        exp = iotlab.startExp("AutoRest", 10, "grenoble", 8)

    else:
        print ("Re-using already running experiment")
        exp = expList[0]

    print "Experiment id=%s" % exp.expId, exp.getState()
    exp.waitUntilRunning(verbose=True)

    #exp.doNodeCmd("reset", AllList)

    #exitNow

    #codeFirmwareFileName = \
    #    "../riot/RIOT/examples/hello-world/bin/iot-lab_M3/hello-world.elf"

    #codeFirmwareFileName = \
    #    "../riot/RIOT/examples/rpl_udp/bin/iot-lab_M3/rpl_udp.elf"

    snifferFirmwareFileName = \
        "../iot-lab/parts/openlab/build.m3/bin/foren6_sniffer.elf"

    #codeFirmwareFileName = \
    #    "../riot/RIOT/examples/default/bin/iot-lab_M3//default.elf"

    #https://github.com/iot-lab/iot-lab/wiki/HOWTO-use-Foren6-to-diagnose-in-realtime-your-6LoWPAN-experiment

    codeFirmwareFileName = "../openwsn/openwsn-fw/firmware/openos/projects/common/03oos_openwsn_prog"

    #codeFirmwareData = readFile(codeFirmwareFileName)
    #snifferFirmwareData = readFile(snifferFirmwareFileName)
     
    #expInfo = exp.getResources()
    #addressList = [nodeInfo["network_address"] for nodeInfo in expInfo["items"]]
    #pprint.pprint(addressList)

    snifferAddressList = [address for address in addressList
                          if getNodeId(address)%2 == 0]
    snifferAddressList = []
    codeAddressList = list(set(addressList).difference(set(snifferAddressList)))
    
    if len(snifferAddressList) > 0:
        print exp.doNodeCmd("update", snifferAddressList, snifferFirmwareData)
    print exp.doNodeCmd("update", codeAddressList, codeFirmwareData)

    #print "stopping experience"
    #exp.stop()



if False:
        #exp = experiment.Experiment(name, duration, reservation=None)
        #exp.type = "alias"
        #exp.set_alias_nodes("1", nbNode, {
        #        "mobile": False,
        #        "archi": archi,
        #        "site": site
        #        })
        #exp_files = {
        #    "new_exp.json": objToJson(exp)
        #    }

        #'firmwareassociations': [{'firmwarename': 'hello-world-stripped.elf',
        # 'nodes': ['1']}]

        #if profileName == None:
        #    profileName = self.ensureEmptyProfile()
        pass



def flashSomeNodes(exp, firmwareFileName, addressList, addressFilter):
    if addressList == None:
        expInfo = exp.getResources()
        addressList = [nodeInfo["network_address"] 
                       for nodeInfo in expInfo["items"]]
    

def runSshRedirectAll(userName, addressList):
    nodeOfServer = getNodePerServer(addressList)

    if len(nodeOfServer) != 1:
        raise NotImplemented("more than 1 server") # XXX: support several

    server = nodeOfServer.keys()[0]
    nodeList = nodeOfServer[server]

    StartTcpPort = 30000
    currentPort = StartTcpPort
    #userName = os.environ.get("USER")
    cmd = ["ssh","%s@%s" % (userName, server)]
    for nodeName in nodeList:
        cmd.extend(["-L %s:%s:20000" % (currentPort, nodeName)])
        currentPort += 1

    # XXX Should probably write in some file, the 'nodeOfServer' + ports

    print "Port range:", StartTcpPort, currentPort-1
    print "starting ssh:", " ".join(cmd)
    subprocess.check_call(cmd)

#---------------------------------------------------------------------------


# evenNodeList = [ address for address in nodeList 
#                  if extractNodeId(address)%2 == 0 ]
# oddNodeList = list(set(nodeList).difference(evenNodeList))


# if len(oddNodeList) < 2:
#     sys.stderr.write("Error: need at least 2 nodes for RPL (with odd id)")
#     sys.exit(1)
# if len(evenNodeList) == 0:
#     sys.stderr.write("Error: need at least 1 node for sniffer (with even id)")
#     sys.exit(1)


# borderRouter = oddNodeList[0]
# rplNodeList = oddNodeList[1:]
# snifferList = evenNodeList


# rplNodeFw = IotlabHelper.readFile(NodeFwFileName)

# snifferFw = IotlabHelper.readFile(SnifferFwFileName)

# def reprNodeList(addressList):
#     return ", ".join([address.split(".")[0] for address in addressList])

# specList = [
#     ("border router", [borderRouter], borderRouterFw),
#     ("rpl/http-server node", rplNodeList, rplNodeFw),
#     ("sniffer (for foren6)", snifferList, snifferFw)
#     ]

# print "-- flashing nodes"
# for (category, nodeList, firmwareData) in specList:
#     print "%s: %s"%(category, reprNodeList(nodeList))
#     result = exp.doNodeCmd("update", nodeList, firmwareData)
#     print (result)

#print exp.doNodeCmd("reset", IotlabHelper.AllList)


#---------------------------------------------------------------------------


        ##self.sd.send("t\n")
        ##self.clientSocketInput = Scheduler.BufferedInputFdHandler(
        ##    self.clientSocket.fileno(), self.clientSocket.recv,
        ##    self.eventSocketInput, self.eventSocketClose)
        ##self.clientSocketOutput = Scheduler.BufferedOutputFdHandler(
        ##    self.clientSocket.fileno(), self.clientSocket.send)
        ##self.scheduler.addFdHandler(self.clientSocketInput)
        ##self.scheduler.addFdHandler(self.clientSocketOutput)


        
        #self.createListenSocket()

    # def createListenSocket(self):
    #     self.listenSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     self.listenSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    #     self.listenSocket.bind(("", BaseProxyPort+self.nodeId))
    #     self.listenSocket.listen(10000)
    #     self.scheduler.addFdHandler(Scheduler.FunctionalFdHandler(
    #             self.listenSocket, waitInputFunc = lambda: True,
    #             handleInputFunc = self.eventClientConnection))

    # def eventClientConnection(self):
    #     clientSocket, address = self.listenSocket.accept()
    #     print "[proxy/serial] Client connection from address:", address
    #     if address[0] != "127.0.0.1": 
    #         raise RuntimeError(("client from different machine", address))
    #     client = LocalConnection(self, clientSocket)
    #     self.clientList.append(client)


#---------------------------------------------------------------------------

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

# -> http://www.python.org/search/hypermail/python-1993/0020.html
#os.system("stty raw")

        #if self.log != None:
        #    self.log.write(repr((time.time(), "out", data))+"\n")
        #    if self.config.withFlush: self.log.flush()
        ##sys.stdout.write("[%d|" % self.nodeId +data+"]")
        ##sys.stdout.flush()
        #for client in self.clientList:
        #    client.write(data)

        
        #if self.config.shouldLog:
        #    self.log = open(self.config.resultDir+"/log.%d" % self.nodeId, "w")
        #else: self.log = None

        # self.clientList = []

        #if self.log != None:
        #    self.log.write(repr((time.time(), "in", data))+"\n")


#---------------------------------------------------------------------------
#---------------------------------------------------------------------------




raw_input("Will set tunnels for sniffer: ")
TunnelSnifferStartPort = 3000
sshRedirectPortList = [ 
    "-L %s:%s:%s" % (TunnelSnifferStartPort+i, snifferNode, 
                     IotlabHelper.SerialTcpPort)
    for i, snifferNode in enumerate(snifferList) ]
sshRedirectPortStr = " ".join(sshRedirectPortList)
sshSnifferTunnelCommand = "ssh -T %s@%s %s 'echo FORWARDING Sniffer PORTS ; sleep 600000'" % (
    iotlabHelper.userName, expServer, sshRedirectPortStr)
#print sshSnifferTunnelCommand
processManager.startSubProcessInTerm("ssh tunnels for sniffers to IoT-LAB", 
                                     sshSnifferTunnelCommand)




#---------------------------------------------------------------------------
#---------------------------------------------------------------------------
# Now 
#---------------------------------------------------------------------------
#---------------------------------------------------------------------------

#--------------------------------------------------
# Stop all nodes

#exp.doNodeCmd("stop", IotlabHelper.AllList)

#--------------------------------------------------
# Start ssh forwarding, tunslip, and reset all nodes
#
# XXX: this is messy, use a GUI
raw_input("Will run tunslip6. Press any key to continue: ")


raw_input("Will run tunslip6. Press any key to continue: ")
tunslipCommand = ("sudo " +TunslipBinFileName+" aaaa::1/64 -L -a localhost"
                  + " -p %s"% TunnelPort)
processManager.startSubProcessInTerm("Contiki tunslip6", tunslipCommand)

raw_input("Will run socat. Press any key to continue: ")
for i, snifferNode in enumerate(snifferList):
    port = TunnelSnifferStartPort+i
    link = "/tmp/mytty%d" % i
    cmd = "socat TCP4:127.0.0.1:%s pty,link=%s,raw" % (port, link)
    processManager.startSubProcessInTerm(
        "SOCAT %s :%s" % (snifferNode, port), cmd)

raw_input("Will run foren6: ")
cmd = "cd ../foren6 && make run"
processManager.startSubProcessInTerm("foren6", cmd)

raw_input("Will reset all nodes. Press any key to continue: ")
exp.doNodeCmd("reset", IotlabHelper.AllList)

print "Running (press [Ctrl-C] to interrupt)"
time.sleep(10000)

#---------------------------------------------------------------------------

scenarioInfo = {
    "borderRouter": borderRouterNode,
    "snifferList": snifferList,
    "failedList": currentNodeList
}
info["scenario"] = scenarioInfo

#TunnelPort = 2000
#sshTunnelCommand = "ssh -T %s@%s -L %s:%s:%s 'echo FORWARDING PORTS ; sleep 600000'" % (
#    iotlabHelper.userName, expServer, TunnelPort, borderRouterNode, 
#    IotlabHelper.SerialTcpPort)
#processManager.startSubProcessInTerm("ssh Tunnel to IoT-LAB", sshTunnelCommand)

#---------------------------------------------------------------------------
