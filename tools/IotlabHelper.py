#---------------------------------------------------------------------------
# Further Helper for IoT-LAB REST API
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

import sys, argparse, pprint, os, time
import json
sys.path.append("../iot-lab/parts/cli-tools")

from iotlabcli import rest, helpers, experiment

#---------------------------------------------------------------------------

def getCredentialsOrFail(parser):
    """return (name, password) from file, or exit if not available"""
    (name, password) = helpers.read_password_file(parser)
    if name == None or password == None:
        parser.error("stored .iotlabrc not available, use auth-cli (or make run-auth-cli)")
        sys.exit(1)
    return name, password

def getServerUrl():
    if os.path.exists("iotlab.url") and "--dev" in sys.argv:
        url = readFile("iotlab.url").strip()
    else: url = rest.API_URL # XXX 
    return url

#---------------------------------------------------------------------------

def objToJson(info):
    return json.dumps(info, cls=rest.Encoder)

def toJson(info):
    return json.dumps(info)

def fromJson(jsonStr):
    return json.loads(jsonStr)

#---------------------------------------------------------------------------

class IotlabException(Exception):
    def __init__(self, message, info):
        self.message = message
        self.info = info
    def __str__(self):
        return "IotlabException, %s:\n%s" % (str(self.message), str(self.info)) 

#---------------------------------------------------------------------------

# https://www.iot-lab.info/tools/rest-api-docs/

ExpStateList = ["Running", "Waiting", "Error", "Terminated", "Launching",
                "toLaunch"] # XXX: check this list

AllList = ("AllList",) # All nodes

class IotlabExp:
    def __init__(self, helper, expId):
        self.helper = helper # we also use directly self.helper.request
        self.expId = expId

    def stop(self):
        resultJson = self.helper.request.stop_experiment(self.expId)
        if resultJson == None: return None
        else: return fromJson(resultJson)

    def getState(self):
        return fromJson(self.helper.request.get_experiment_state
                        (self.expId))["state"]

    def doNodeCmd(self, cmd, nodeList = AllList, firmwareData = None):
        assert cmd in ["start", "stop", "reset", "update"]
        assert firmwareData == None or cmd == "update"
        if nodeList is AllList:
            nodeList = []
        jsonNodeList = toJson(nodeList)
        method = { "start": self.helper.request.start_command,
                   "stop": self.helper.request.stop_command,
                   "update": self.helper.request.update_command,
                   "reset": self.helper.request.reset_command }[cmd]
        if cmd == "update":
            arg = {
                "nodes.json": jsonNodeList, # XXX StringIO???
                "firmware.elf": firmwareData
                }
        else: arg = jsonNodeList
        return fromJson(method(self.expId, arg))

    def getResources(self):
        return fromJson(self.helper.request.get_experiment_resources(
                self.expId))

    def waitUntilRunning(self, verbose=True):
        """Wait until the experiment is in the state 'Running'
        raise an exception if it cannot reach that state (Terminated...)"""
        while True:
            state = self.getState()
            if verbose: 
                print "state:", state
            time.sleep(2)
            if state == "Running":
                break
            elif state in ["Waiting", "Launching", "toLaunch"]:
                continue
            else: 
                raise IotlabException("Experiment cannot be 'Running'", state)
        
#--------------------------------------------------

MaxExp = 1


class IotlabHelper:
    def __init__(self):
        self.parser = argparse.ArgumentParser() # XXX: not so useful
        #parser.parse_args()
        parser = self
        name, password = getCredentialsOrFail(parser)
        serverUrl = getServerUrl()
        self.request = rest.Api(url = serverUrl,
                                username=name, password=password, 
                                parser=parser)

    def _makeExp(self, expId):
        "Factory for IotlabExp"
        return IotlabExp(self, expId)

    def getSiteList(self):
        return fromJson(self.request.get_sites())

    def getExpInfoList(self, stateList = ["Running"]):
        """Return a list of running [opt:waiting] experiments"""

        unknownStateSet = set(stateList).difference(set(ExpStateList))
        if len(unknownStateSet) > 0:
            raise ValueError("Unknown experiment state", unknownStateSet)
        if len(stateList) == 0:
            raise ValueError("No experiment state specified")

        queryset = "state=" + ",".join(sorted(stateList))
        result = self.request.get_experiments(queryset)
        return fromJson(result)["items"]

    def getExpList(self, stateList = ["Running"]):        
        expInfoList = self.getExpInfoList(stateList)
        return [self._makeExp(expInfo["id"]) for expInfo in expInfoList]

    def startExp(self, name, duration, site, nbNode, archi="m3:at86rf231"):
        self.ensureExpLimit() # sanity check - avoid bugs and 'fork bombs'
        exp = experiment.Experiment(name, duration, reservation=None)

        exp.type = "alias"
        exp.set_alias_nodes("1", nbNode, {
                "mobile": False,
                "archi": archi,
                "site": site
                })
        exp_files = {
            "new_exp.json": objToJson(exp)
            }

        resultJson = self.request.submit_experiment(exp_files)
        result = fromJson(resultJson)
        if "error" in result:
            raise IotlabException("Cannot start experiment", result["error"])
        expId = result["id"]
        return self._makeExp(expId)

    def ensureExpLimit(self):
        expList = self.getExpInfoList(["Running", "Waiting", "Launching",
                                       "toLaunch"])
        if len(expList) >= MaxExp:
            self.error("%s experiment(s) already running/waiting:\n"
                       % len(expList) 
                       + pprint.pformat(expList))
        
    def error(self, message):
        sys.stderr.write("ERROR: "+message+"\n")
        sys.exit(1)

#---------------------------------------------------------------------------

def readFile(fileName):
    with open(fileName) as f:
        return f.read()

if __name__ == "__main__":
    iotlab = IotlabHelper()
    #pprint.pprint(iotlab.getSiteList())

    expInfoList = iotlab.getExpInfoList(["Running", "Waiting", "Launching",
                                         "toLaunch"])
    pprint.pprint(expInfoList)

    expList = iotlab.getExpList()

    if len(expList) == 0:
        print ("No experience, starting one")
        exp = iotlab.startExp("Rest", 10, "rocquencourt", 10)

    else:
        print ("Re-using already running experiment")
        exp = expList[0]

    print "Experiment id=%s" % exp.expId, exp.getState()
    exp.waitUntilRunning(verbose=True)

    #codeFirmwareFileName = \
    #    "../riot/RIOT/examples/hello-world/bin/iot-lab_M3/hello-world.elf"

    codeFirmwareFileName = \
        "../riot/RIOT/examples/rpl_udp/bin/iot-lab_M3/rpl_udp.elf"

    snifferFirmwareFileName = \
        "../iot-lab/parts/openlab/build.m3/bin/foren6_sniffer.elf"

    #https://github.com/iot-lab/iot-lab/wiki/HOWTO-use-Foren6-to-diagnose-in-realtime-your-6LoWPAN-experiment

    codeFirmwareData = readFile(codeFirmwareFileName)
    snifferFirmwareData = readFile(snifferFirmwareFileName)
     
    expInfo = exp.getResources()
    addressList = [nodeInfo["network_address"] for nodeInfo in expInfo["items"]]
    pprint.pprint(addressList)


    def getNodeId(address):
        nodeName = address.split(".")[0]
        return int(nodeName.split("-")[-1])

    snifferAddressList = [address for address in addressList
                          if getNodeId(address)%2 == 0]
    codeAddressList = list(set(addressList).difference(set(snifferAddressList)))

    
    print exp.doNodeCmd("update", snifferAddressList, snifferFirmwareData)
    print exp.doNodeCmd("update", codeAddressList, codeFirmwareData)

    #print "stopping experience"
    #exp.stop()

#---------------------------------------------------------------------------
