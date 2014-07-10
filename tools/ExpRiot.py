#---------------------------------------------------------------------------
# Trying to automate experiments with RIOT
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

import argparse
import IotlabHelper

#---------------------------------------------------------------------------

# experiment-cli submit -d 5 -l 5,archi=m3:at86rf231+site=grenoble,hello-world-stripped.elf,default_m3_rest

RiotFirmwareFileName = "../riot/RIOT/examples/default/bin/iot-lab_M3/default-stripped.elf"

#---------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description = "Run an Riot experiment"
)

IotlabHelper.parserAddTypicalArgs(parser)

args = parser.parse_args()

#---------------------------------------------------------------------------

iotlabHelper, exp = IotlabHelper.ensureExperimentFromArgs(args)

print ("- Reflashing nodes")
firmwareData = IotlabHelper.readFile(RiotFirmwareFileName)
result = exp.doNodeCmd("update", IotlabHelper.AllList, firmwareData)
print (result)
#print exp.doNodeCmd("reset", IotlabHelper.AllList)

#---------------------------------------------------------------------------
