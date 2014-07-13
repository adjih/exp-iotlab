#---------------------------------------------------------------------------
# Applying experiment in the tutorial of R. Pissard-Gibollet Ubimob'2014
# - https://www.iot-lab.info/tutorials/contiki-ipv6-stack-and-tools/
# Also automating the steps by N. Turro, O. Fambon, G. Harter et al.:
# - https://github.com/iot-lab/iot-lab/wiki/HOWTO-use-Foren6-to-diagnose-in-realtime-your-6LoWPAN-experiment
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

import argparse, time, sys, random
import IotlabHelper
from IotlabHelper import extractNodeId, AllPossibleNodes

#---------------------------------------------------------------------------

ExperimentName = "Contiki RPL with border router"

#---------------------------------------------------------------------------

NodeFwFileName = "../iot-lab/parts/contiki/examples/ipv6/http-server/http-server.iotlab-m3"
BorderRouterFwFileName = "../iot-lab/parts/contiki/examples/ipv6/rpl-border-router/border-router.iotlab-m3"
SnifferFwFileName = "../iot-lab/parts/openlab/build.m3/bin/foren6_sniffer.elf"

#NodeFwFileName = "PreCompiled/http-server.iotlab-m3"
#BorderRouterFwFileName = "PreCompiled/border-router.iotlab-m3"
#SnifferFwFileName = "PreCompiled/foren6_sniffer.elf"

#
#TunslipBinFileName = "sudo ../local/bin/tunslip6 aaaa::1/64 -L -a localhost -p 2000"
TunslipBinFileName = "../local/bin/tunslip6"

#---------------------------------------------------------------------------

parser = argparse.ArgumentParser(
    description = ExperimentName
)
parser.add_argument("--wipe", dest="wipe", action="store_true", default=False)
parser.add_argument("--nb-sniffers", dest="nbSniffers", type=int, default=0)
IotlabHelper.parserAddTypicalArgs(parser, "ContikiRpl_BorderHttpSniffer")
args = parser.parse_args()

#---------------------------------------------------------------------------

iotlabHelper, exp = IotlabHelper.ensureExperimentFromArgs(args)

#--------------------------------------------------
# Identify the IoT-LAB server of the experiment
# this will be used for an ssh tunnel

nodeList = exp.getNodeList()
nodeOfServer = IotlabHelper.getNodePerServer(nodeList)
if len(nodeOfServer.keys()) != 1: 
    sys.stderr.write("ERROR: multi-site experiment not handled")
    sys.exit(1)
expServer = nodeOfServer.keys()[0] 

#--------------------------------------------------
# Ensure that persistent info corresponds to this experiment

BorderRouterPriorityList = [69,68,65,63,61]

def getPriority(address):
    nodeId = IotlabHelper.extractNodeId(address)
    if nodeId in BorderRouterPriorityList:
        return BorderRouterPriorityList.index(nodeId)
    else: return len(BorderRouterPriorityList)

nodeList.sort(key=getPriority)

if args.wipe:
    exp.resetPersistentInfo()
isReset = exp.ensurePersistentNameOrReset(ExperimentName)

expInfo = exp.getPersistentInfo()
if isReset:
    expInfo["nbSniffers"] = args.nbSniffers
    exp.savePersistentInfo(expInfo)
nbSniffers = expInfo["nbSniffers"]

#--------------------------------------------------
# Ensure that the nodes are reflashed with proper firmware

currentNodeList = nodeList

borderRouterList, currentNodeList = exp.ensureFlashedNodes(
    "BorderRouter", BorderRouterFwFileName, 1, currentNodeList)
assert len(borderRouterList) == 1
borderRouterNode = borderRouterList[0]

random.seed(0)
random.shuffle(currentNodeList) # we want to take random nodes as sniffers

if nbSniffers > 0:
    snifferList, currentNodeList = exp.ensureFlashedNodes(
        "Sniffer", SnifferFwFileName, nbSniffers, currentNodeList)
    assert len(snifferList) == nbSniffers
else:
    snifferList = []

nodeRouterList, currentNodeList = exp.ensureFlashedNodes(
    "HttpRplNode", NodeFwFileName, AllPossibleNodes, 
    currentNodeList)

#--------------------------------------------------
# Stop all nodes

#exp.doNodeCmd("stop", IotlabHelper.AllList)

#--------------------------------------------------
# Start ssh forwarding, tunslip, and reset all nodes
#
# XXX: this is messy, use an interface

processManager = IotlabHelper.ProcessManager()
processManager.setWindowTitle("Contiki RPL Experiment")

TunnelPort = 2000
sshTunnelCommand = "ssh -T %s@%s -L %s:%s:%s 'echo FORWARDING PORTS ; sleep 600000'" % (
    iotlabHelper.userName, expServer, TunnelPort, borderRouterNode, 
    IotlabHelper.SerialTcpPort)
processManager.startSubProcessInTerm("ssh Tunnel to IoT-LAB", sshTunnelCommand)

raw_input("Will run tunslip6. Press any key to continue: ")
tunslipCommand = ("sudo " +TunslipBinFileName+" aaaa::1/64 -L -a localhost"
                  + " -p %s"% TunnelPort)
processManager.startSubProcessInTerm("Contiki tunslip6", tunslipCommand)

TunnelSnifferStartPort = 3000
sshRedirectPortList = [ 
    "-L %s:%s:%s" % (TunnelSnifferStartPort+i, snifferNode, 
                     IotlabHelper.SerialTcpPort)
    for i, snifferNode in enumerate(snifferList) ]
sshRedirectPortStr = " ".join(sshRedirectPortList)
sshSnifferTunnelCommand = "ssh -T %s@%s %s 'echo FORWARDING Sniffer PORTS ; sleep 600000'" % (
    iotlabHelper.userName, expServer, sshRedirectPortStr)
#print sshSnifferTunnelCommand
processManager.startSubProcessInTerm("ssh tunnels for sniffers to IoT-LAB", 
                                     sshSnifferTunnelCommand)

raw_input("Will run socat. Press any key to continue: ")
for i, snifferNode in enumerate(snifferList):
    port = TunnelSnifferStartPort+i
    link = "/tmp/mytty%d" % i
    cmd = "socat TCP4:127.0.0.1:%s pty,link=%s,raw" % (port, link)
    processManager.startSubProcessInTerm(
        "SOCAT %s :%s" % (snifferNode, port), cmd)

raw_input("Will run foren6: ")
cmd = "cd ../foren6 && make run"
processManager.startSubProcessInTerm("foren6", cmd)

raw_input("Will reset all nodes. Press any key to continue: ")
exp.doNodeCmd("reset", IotlabHelper.AllList)

time.sleep(1000)

#---------------------------------------------------------------------------
