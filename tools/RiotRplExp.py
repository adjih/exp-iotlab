#---------------------------------------------------------------------------
# Trying to automate experiments with RIOT
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

import argparse
import IotlabHelper

#---------------------------------------------------------------------------

RiotFirmwareFileName = "../riot/RIOT/examples/default/bin/iot-lab_M3/default.elf"

#---------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description = "Run an Riot experiment"
)

IotlabHelper.parserAddTypicalArgs(parser)

args = parser.parse_args()

#---------------------------------------------------------------------------

iotlabHelper, exp = IotlabHelper.ensureExperimentFromArgs(args)

print ("- Reflashing nodes")
#firmwareData = IotlabHelper.readFile(RiotFirmwareFileName)
#result = exp.doNodeCmd("update", IotlabHelper.AllList, firmwareData)
#print (result)
print exp.doNodeCmd("reset", IotlabHelper.AllList)

#---------------------------------------------------------------------------
