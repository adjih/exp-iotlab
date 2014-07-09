#---------------------------------------------------------------------------
# Automating the steps by O. Chambon et al:
# https://github.com/iot-lab/iot-lab/wiki/HOWTO-use-Foren6-to-diagnose-in-realtime-your-6LoWPAN-experiment
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

import argparse
import IotlabHelper

#---------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description = "Run an Contiki RPL experiment"
)

argList = parser.parse_args()

#---------------------------------------------------------------------------
