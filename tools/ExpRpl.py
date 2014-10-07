#---------------------------------------------------------------------------
# Applying experiment in the tutorial of R. Pissard-Gibollet Ubimob'2014
# - https://www.iot-lab.info/tutorials/contiki-ipv6-stack-and-tools/
# Also automating the steps by N. Turro, O. Fambon, G. Harter et al.:
# - https://github.com/iot-lab/iot-lab/wiki/HOWTO-use-Foren6-to-diagnose-in-realtime-your-6LoWPAN-experiment
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

import argparse, time, sys, random, os, pprint
import IotlabHelper
from IotlabHelper import extractNodeId, AllPossibleNodes

#---------------------------------------------------------------------------

#ExperimentName = "Contiki RPL with border router"
ExperimentName = "IoT-LAB experiment"

#---------------------------------------------------------------------------

NodeFwFileName = "../iot-lab/parts/contiki/examples/ipv6/http-server/http-server.iotlab-m3"
BorderRouterFwFileName = "../iot-lab/parts/contiki/examples/ipv6/rpl-border-router/border-router.iotlab-m3"

#NodeFwFileName = "PreCompiled/http-server.iotlab-m3"
#BorderRouterFwFileName = "PreCompiled/border-router.iotlab-m3"

#---------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description = ExperimentName
)
IotlabHelper.parserAddTypicalArgs(parser, "IoTLab_Exp_REST")
args = parser.parse_args()

iotlabHelper, exp = IotlabHelper.ensureExperimentFromArgs(args)
exp.makeLastSymLink() # XXX: cannot run multiple simultaneous exp. with this

#exp.resetPersistentInfo()

#--------------------------------------------------
# Flash nodes
#--------------------------------------------------

random.seed(0) # for random order of sniffers

nodeList = exp.getNodeList()
currentNodeList = nodeList[:]

if args.exp_type == "contiki":

    #BorderRouterPriorityList = [69,68,65,63,61]
    BorderRouterPriorityList = [178,175,174,171,169,167]
    currentNodeList = IotlabHelper.sortNodeByPriority(
        currentNodeList, BorderRouterPriorityList)

    borderRouterList, currentNodeList = exp.ensureFlashedNodes(
        "contiki-border-router", BorderRouterFwFileName, 1, currentNodeList)
    print borderRouterList
    assert len(borderRouterList) == 1
    borderRouterNode = borderRouterList[0]

    #nodeRouterList, currentNodeList = exp.ensureFlashedNodes(
    #    "http-rpl-node", NodeFwFileName, AllPossibleNodes, 
    #    currentNodeList)
    contikiRouterList, currentNodeList = exp.ensureFlashedStdNodes(
        "contiki-rpl-node", args.nb_protocol_nodes, currentNodeList, True)

elif args.exp_type == "openwsn":

    BorderRouterPriorityList = [349,348,346,344,342,339]
    currentNodeList = IotlabHelper.sortNodeByPriority(
        currentNodeList, BorderRouterPriorityList)

    OpenWSNRouterFwFileName = "../openwsn/openwsn-fw-sink/projects/common/03oos_openwsn_prog"

    borderRouterList, currentNodeList = exp.ensureFlashedNodes(
        "openwsn-sink", OpenWSNRouterFwFileName, 1, currentNodeList)
    print borderRouterList
    assert len(borderRouterList) == 1
    borderRouterNode = borderRouterList[0]

    openwsnRouterList, currentNodeList = exp.ensureFlashedStdNodes(
        "openwsn", args.nb_protocol_nodes, currentNodeList, True)

elif args.exp_type == "riot":
    riotRouterList, currentNodeList = exp.ensureFlashedStdNodes(
        "riot", args.nb_protocol_nodes, currentNodeList, True)

else: raise RuntimeError("Unknown type of experiment", args.expType)

# Sniffer nodes
foren6SnifferList, currentNodeList = exp.ensureFlashedStdNodes(
    "foren6-sniffer", args.nbForen6Sniffers, currentNodeList, True)

zepSnifferList, currentNodeList = exp.ensureFlashedStdNodes(
    "zep-sniffer", args.nbZepSniffers, currentNodeList, True)

# Flash remaining nodes with 'default' (no radio) nodes
nodeRouterList, currentNodeList = exp.ensureFlashedStdNodes(
    "default", AllPossibleNodes, currentNodeList, True)

#--------------------------------------------------
# Save scenario
#--------------------------------------------------

expInfo = exp.getPersistentInfo()
expInfo["name"] = ExperimentName
expInfo["args"] = vars(args)
expInfo["failed"] = currentNodeList
exp.savePersistentInfo(expInfo)

#---------------------------------------------------------------------------
