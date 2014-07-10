#---------------------------------------------------------------------------
# Applying experiment in the tutorial of R. Pissard-Gibollet Ubimob'2014
# - https://www.iot-lab.info/tutorials/contiki-ipv6-stack-and-tools/
# Also automating the steps by N. Turro, O. Fambon, G. Harter et al.:
# - https://github.com/iot-lab/iot-lab/wiki/HOWTO-use-Foren6-to-diagnose-in-realtime-your-6LoWPAN-experiment
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

import argparse, time, sys
import IotlabHelper
from IotlabHelper import extractNodeId, AllPossibleNodes

#---------------------------------------------------------------------------

ExperimentName = "Contiki RPL with border router"

#---------------------------------------------------------------------------

NodeFwFileName = "../iot-lab/parts/contiki/examples/ipv6/http-server/http-server.iotlab-m3"
BorderRouterFwFileName = "../iot-lab/parts/contiki/examples/ipv6/rpl-border-router/border-router.iotlab-m3"
SnifferFwFileName = "../iot-lab/parts/openlab/build.m3/bin/foren6_sniffer.elf"

NodeFwFileName = "PreCompiled/http-server.iotlab-m3"
BorderRouterFwFileName = "PreCompiled/border-router.iotlab-m3"
SnifferFwFileName = "PreCompiled/foren6_sniffer.elf"

#
TunslipBinFileName = "sudo ../local/bin/tunslip6 aaaa::1/64 -L -a localhost -p 2000"

#---------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description = "Run a Contiki RPL experiment"
)
IotlabHelper.parserAddTypicalArgs(parser)
args = parser.parse_args()

#---------------------------------------------------------------------------

iotlabHelper, exp = IotlabHelper.ensureExperimentFromArgs(args)

nodeList = exp.getNodeList()
nodeOfServer = IotlabHelper.getNodePerServer(nodeList)
if len(nodeOfServer.keys()) != 1: 
    sys.stderr.write("ERROR: multi-site experiment not handled")
    sys.exit(1)
expServer = nodeOfServer.keys()[0]

#--------------------------------------------------

expInfo = exp.loadPersistentInfo()
oldName = expInfo.get("name")
if oldName != ExperimentName:
    if oldName != None:
        print "- Experiment was '%s', erasing persistent [meta-]info" % (
            expInfo.get("name"))
    expInfo = { "name": ExperimentName }

currentNodeList = nodeList

borderRouterList, currentNodeList = IotlabHelper.ensurePersistentFlashNodes(
    exp, expInfo, "BorderRouter", BorderRouterFwFileName, 1, currentNodeList)
assert len(borderRouterList) == 1
borderRouterNode = borderRouterList[0]

nodeRouterList, currentNodeList = IotlabHelper.ensurePersistentFlashNodes(
    exp, expInfo, "HttpRplNode", NodeFwFileName, AllPossibleNodes, 
    currentNodeList)

#--------------------------------------------------

processManager = IotlabHelper.ProcessManager()
processManager.setWindowTitle("Contiki RPL Experiment")

#
TunnelPort = 2000
tunslipCommand = ("sudo " +TunslipBinFileName+" aaaa::1/64 -L -a localhost"
                  + " -p %s"% TunnelPort)
sshTunnelCommand = "ssh -T %s@%s -L %s:%s:%s 'echo FORWARDING PORTS ; sleep 600000'" % (
    iotlabHelper.userName, expServer, TunnelPort, borderRouterNode, 
    IotlabHelper.SerialTcpPort)
processManager.startSubProcessInTerm("ssh Tunnel to IoT-LAB", sshTunnelCommand)
time.sleep(10)
processManager.startSubProcessInTerm("Contiki tunslip6", tunslipCommand)
time.sleep(1000)

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
