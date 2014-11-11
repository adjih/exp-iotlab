#---------------------------------------------------------------------------
# Automating experiments with RIOT
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

import argparse, time, sys, random, os, pprint
import IotlabHelper
from IotlabHelper import extractNodeId, AllPossibleNodes

#---------------------------------------------------------------------------

ExperimentName = "RIOT IoT-LAB Experiment"

#---------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description = ExperimentName
)
IotlabHelper.parserAddTypicalArgs(parser, "QuickStart_RIOT")
parser.add_argument("--with-sniffer", action="store_true", default=False)
args = parser.parse_args()

iotlabHelper, exp = IotlabHelper.ensureExperimentFromArgs(args)
exp.makeLastSymLink() # XXX: cannot run multiple simultaneous exp. with this

#---------------------------------------------------------------------------

#RiotFirmwareFileName = "../riot/RIOT/examples/default/bin/iot-lab_M3/default.elf"
RiotFirmwareFileName = "../riot/RIOT/examples/rpl_udp/bin/iot-lab_M3/rpl_udp.elf"

nodeList = exp.getNodeList()
currentNodeList = nodeList[:]
currentNodeList.sort()

if args.with_sniffer:
    print ". option --with-sniffer, putting sniffer on nodes with even IDs"
    tentativeSnifferNodeList = [address for address in currentNodeList
                                if extractNodeId(address)%2 == 0]
    # Sniffer nodes
    foren6SnifferList, unusedNodeList = exp.ensureFlashedStdNodes(
        "foren6-sniffer", len(tentativeSnifferNodeList), 
        tentativeSnifferNodeList, False)

    currentNodeList = list(set(currentNodeList).difference(
            set(foren6SnifferList)))
    currentNodeList.sort()

riotRouterList, currentNodeList = exp.ensureFlashedStdNodes(
    "riot", AllPossibleNodes, currentNodeList, False)

#---------------------------------------------------------------------------
# Save scenario
#--------------------------------------------------

expInfo = exp.getPersistentInfo()
expInfo["name"] = ExperimentName
expInfo["args"] = vars(args)
expInfo["failed"] = currentNodeList
exp.savePersistentInfo(expInfo)

#---------------------------------------------------------------------------
