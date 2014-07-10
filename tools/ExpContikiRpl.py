#---------------------------------------------------------------------------
# Automating the steps by N. Turro, O. Fambon, G. Harter et al.:
# https://github.com/iot-lab/iot-lab/wiki/HOWTO-use-Foren6-to-diagnose-in-realtime-your-6LoWPAN-experiment
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------


import argparse
import IotlabHelper
from IotlabHelper import extractNodeId

#---------------------------------------------------------------------------

NodeFwFileName = "../iot-lab/parts/contiki/examples/ipv6/http-server/http-server.iotlab-m3"
BorderRouterFwFileName = "../iot-lab/parts/contiki/examples/ipv6/rpl-border-router/border-router.iotlab-m3"
SnifferFwFileName = "../iot-lab/parts/openlab/build.m3/bin/foren6_sniffer.elf"

NodeFwFileName = "PreCompiled/http-server.iotlab-m3"
BorderRouterFwFileName = "PreCompiled/border-router.iotlab-m3"
SnifferFwFileName = "PreCompiled/foren6_sniffer.elf"

#---------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description = "Run a Contiki RPL experiment"
)
IotlabHelper.parserAddTypicalArgs(parser)
args = parser.parse_args()

#---------------------------------------------------------------------------

rplNodeFw = IotlabHelper.readFile(NodeFwFileName)
borderRouterFw = IotlabHelper.readFile(NodeFwFileName)
snifferFw = IotlabHelper.readFile(SnifferFwFileName)

iotlabHelper, exp = IotlabHelper.ensureExperimentFromArgs(args)
nodeList = exp.getNodeList()

evenNodeList = [ address for address in nodeList 
                 if extractNodeId(address)%2 == 0 ]
oddNodeList = list(set(nodeList).difference(evenNodeList))

if len(oddNodeList) < 2:
    sys.stderr.write("Error: need at least 2 nodes for RPL (with odd id)")
    sys.exit(1)
if len(evenNodeList) == 0:
    sys.stderr.write("Error: need at least 1 node for sniffer (with even id)")
    sys.exit(1)


borderRouter = oddNodeList[0]
rplNodeList = oddNodeList[1:]
snifferList = evenNodeList

def reprNodeList(addressList):
    return ", ".join([address.split(".")[0] for address in addressList])

specList = [
    ("border router", [borderRouter], borderRouterFw),
    ("rpl/http-server node", rplNodeList, rplNodeFw),
    ("sniffer (for foren6)", snifferList, snifferFw)
    ]

print "-- flashing nodes"
for (category, nodeList, firmwareData) in specList:
    print "%s: %s"%(category, reprNodeList(nodeList))
    result = exp.doNodeCmd("update", nodeList, firmwareData)
    print (result)

#print exp.doNodeCmd("reset", IotlabHelper.AllList)

#---------------------------------------------------------------------------
