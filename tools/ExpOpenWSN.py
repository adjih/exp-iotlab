#---------------------------------------------------------------------------
# Start an experiment with OpenWSN sink + OpenWSN router nodes
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

import argparse, time, sys, random, os, pprint
import IotlabHelper
from IotlabHelper import extractNodeId, AllPossibleNodes

#---------------------------------------------------------------------------

ExperimentName = "OpenWSN IoT-LAB experiment"

#---------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description = ExperimentName
)
IotlabHelper.parserAddTypicalArgs(parser, "OpenWSN_Exp_REST")
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


BorderRouterPriorityList = [349,348,346,344,342,339]
currentNodeList = IotlabHelper.sortNodeByPriority(
    currentNodeList, BorderRouterPriorityList)

OpenWSNRouterFwFileName = "../openwsn/openwsn-fw-sink/firmware/openos/projects/common/03oos_openwsn_prog"

borderRouterList, currentNodeList = exp.ensureFlashedNodes(
    "openwsn-sink", OpenWSNRouterFwFileName, 1, currentNodeList)
print borderRouterList
assert len(borderRouterList) == 1
borderRouterNode = borderRouterList[0]

# Flash remaining nodes with 'openwsn' (no radio) nodes
nodeRouterList, currentNodeList = exp.ensureFlashedStdNodes(
    "openwsn", AllPossibleNodes, currentNodeList, True)

#--------------------------------------------------
# Save scenario
#--------------------------------------------------

expInfo = exp.getPersistentInfo()
expInfo["name"] = ExperimentName
expInfo["args"] = vars(args)
expInfo["failed"] = currentNodeList
exp.savePersistentInfo(expInfo)

#---------------------------------------------------------------------------
