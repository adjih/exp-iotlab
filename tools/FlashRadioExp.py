#---------------------------------------------------------------------------
# Cedric Adjih - Inria 2014
#---------------------------------------------------------------------------

import argparse
import IotlabHelper
from IotlabHelper import extractNodeId, AllPossibleNodes

#---------------------------------------------------------------------------

ExperimentName = "Radio Test"

parser = argparse.ArgumentParser(
    description = ExperimentName
)
IotlabHelper.parserAddTypicalArgs(parser, "rest_radio_test")
args = parser.parse_args()

iotlabHelper, exp = IotlabHelper.ensureExperimentFromArgs(args, autoStart=False)
exp.makeLastSymLink() # XXX: cannot run multiple simultaneous exp. with this

#---------------------------------------------------------------------------

RadioTestFwFileName = "../iot-lab/parts/openlab/build.m3/bin/radio_test.elf"

nodeList = exp.getNodeList()

radioTestNodeList, currentNodeList = exp.ensureFlashedNodes(
    "radio-test", RadioTestFwFileName, AllPossibleNodes, nodeList)

print radioTestNodeList
print currentNodeList

#---------------------------------------------------------------------------

expInfo = exp.getPersistentInfo()
expInfo["name"] = ExperimentName
expInfo["args"] = vars(args)
expInfo["failed"] = currentNodeList
exp.savePersistentInfo(expInfo)

#---------------------------------------------------------------------------

