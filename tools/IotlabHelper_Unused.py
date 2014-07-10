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
