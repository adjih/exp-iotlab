#---------------------------------------------------------------------------
# Further Helper for IoT-LAB REST API
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

import sys, argparse, pprint, os, time
import json, subprocess
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

#def getServerUrl():
#    if os.path.exists("iotlab.url") and "--dev" in sys.argv:
#        url = readFile("iotlab.url").strip()
#    else: url = rest.API_URL # XXX 
#    return url

def getServerUrl():
    return rest.API_URL # XXX

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
        delay = 1
        while True:
            state = self.getState()
            if verbose: 
                print "state:", state
            time.sleep(delay)
            delay = min(delay * 1.5, 20)
            if state == "Running":
                break
            elif state in ["Waiting", "Launching", "toLaunch"]:
                continue
            else: 
                raise IotlabException("Experiment cannot be 'Running'", state)

    def getNodeList(self):
        # XXX: should cache getRessources
        expInfo = self.getResources()
        addressList = [nodeInfo["network_address"] 
                       for nodeInfo in expInfo["items"]]
        return addressList


def getNodePerServer(addressList):
    nodeOfServer = {}
    for address in addressList:
        addressToken = address.split(".")
        name = addressToken[0]
        server = ".".join(addressToken[1:])
        if server not in nodeOfServer:
            nodeOfServer[server] = []
        nodeOfServer[server].append(name)
    return nodeOfServer

def readFile(fileName):
    with open(fileName) as f:
        return f.read()

#--------------------------------------------------

NameEmptyProfileM3 = "default_m3_rest"

EmptyProfileM3 = {
    "consumption": None,
    "nodearch": "m3",
    "power": "dc", 
    "profilename": NameEmptyProfileM3,
    "radio": None
}

#--------------------------------------------------

MaxExp = 1

class IotlabHelper:
    def __init__(self, expServer=None):
        self.parser = argparse.ArgumentParser() # XXX: not so useful
        #parser.parse_args()
        parser = self
        name, password = getCredentialsOrFail(parser)
        if expServer == None:
            serverUrl = getServerUrl()
        else: serverUrl = "https://{0}/rest/" .format(expServer)
        self.request = rest.Api(url = serverUrl,
                                username=name, password=password, 
                                parser=parser)
        self.userName = name

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

    def startExp(self, name, duration, site, nbNode, archi="m3:at86rf231",
                 profileName=None):
        self.ensureExpLimit() # sanity check - avoid bugs and 'fork bombs'

        #exp = experiment.Experiment(name, duration, reservation=None)
        #exp.type = "alias"
        #exp.set_alias_nodes("1", nbNode, {
        #        "mobile": False,
        #        "archi": archi,
        #        "site": site
        #        })
        #exp_files = {
        #    "new_exp.json": objToJson(exp)
        #    }

        #'firmwareassociations': [{'firmwarename': 'hello-world-stripped.elf',
        # 'nodes': ['1']}]

        #if profileName == None:
        #    profileName = self.ensureEmptyProfile()

        info = {'duration': duration,
                'firmwareassociations': None,
                'name': name,
                'nodes': [{'alias': '1',
                            'nbnodes': nbNode,
                            'properties': {'archi': archi,
                                            'mobile': False,
                                            'site': site}}],
                'profileassociations': None,
                #[{'nodes': ['1'], 'profilename': profileName}],
                'reservation': None,
                'type': 'alias'}

        exp_files = { "new_exp.json": toJson(info) }

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

    #--------------------------------------------------

    def getProfileList(self):
        return fromJson(self.request.get_profiles())

    def addProfile(self, profileName, profileInfo):
        profileJson = toJson(profileInfo)
        self.request.add_profile(profileName, profileJson)

    def getProfile(self, name):
        return fromJson(self.requests.get_profile(name))
        
    def ensureEmptyProfile(self):
        profileList = self.getProfileList()
        for profile in profileList:
            if profile["profilename"] == NameEmptyProfileM3:
                return profile # success
        self.addProfile(NameEmptyProfileM3, EmptyProfileM3)
        return NameEmptyProfileM3

    #--------------------------------------------------

#---------------------------------------------------------------------------
# More utilities functions
#---------------------------------------------------------------------------

def flashSomeNodes(exp, firmwareFileName, addressList, addressFilter):
    if addressList == None:
        expInfo = exp.getResources()
        addressList = [nodeInfo["network_address"] 
                       for nodeInfo in expInfo["items"]]
    
def extractNodeId(address):
    """m3-4.grenoble.iot-lab.info -> integer 4"""
    nodeName = address.split(".")[0]
    return int(nodeName.split("-")[-1])

def runSshRedirectAll(userName, addressList):
    nodeOfServer = getNodePerServer(addressList)

    if len(nodeOfServer) != 1:
        raise NotImplemented("more than 1 server") # XXX: support several

    server = nodeOfServer.keys()[0]
    nodeList = nodeOfServer[server]

    StartTcpPort = 30000
    currentPort = StartTcpPort
    #userName = os.environ.get("USER")
    cmd = ["ssh","%s@%s" % (userName, server)]
    for nodeName in nodeList:
        cmd.extend(["-L %s:%s:20000" % (currentPort, nodeName)])
        currentPort += 1

    # XXX Should probably write in some file, the 'nodeOfServer' + ports

    print "Port range:", StartTcpPort, currentPort-1
    print "starting ssh:", " ".join(cmd)
    subprocess.check_call(cmd)

#---------------------------------------------------------------------------

#DefaultSite = "grenoble"
#DefaultNbNode = 8
DefaultSite = "strasbourg"
DefaultNbNode = 3
DefaultDuration = 10 # minutes

def parserAddTypicalArgs(parser):
    parser.add_argument("--name", default="rest")
    parser.add_argument("--site", default=DefaultSite)
    parser.add_argument("--nb", type=int, default=DefaultNbNode)
    parser.add_argument("--duration", type=int, default=DefaultDuration)
    parser.add_argument("--dev", type=str, default=None)

def ensureExperimentFromArgs(args):
    iotlab = IotlabHelper(args.dev)
    expList = iotlab.getExpList()
    if len(expList) == 0:
        print ("- No experience, starting one")
        exp = iotlab.startExp(args.name, args.duration, args.site, args.nb)
    else:
        print ("- Re-using already running experiment")
        exp = expList[0]

    print ("- Experiment id=%s" % exp.expId, exp.getState())
    exp.waitUntilRunning(verbose=True)
    return iotlab, exp

#---------------------------------------------------------------------------

if __name__ == "__main__":
    iotlab = IotlabHelper()
    
    print "--- List of sites"
    pprint.pprint(iotlab.getSiteList())

    print "--- List of experiments"
    expInfoList = iotlab.getExpInfoList(["Running", "Waiting", "Launching",
                                         "toLaunch"])
    pprint.pprint(expInfoList)

    print "--- List of profiles"
    profileList = iotlab.getProfileList()
    pprint.pprint(profileList)

    profileName = iotlab.ensureEmptyProfile()
    print profileName

    sys.exit(0)

    #expList = iotlab.getExpList()

#---------------------------------------------------------------------------
# Not used
#---------------------------------------------------------------------------

if False:
    if len(expList) == 0:
        print ("No experience, starting one")
        #exp = iotlab.startExp("Rest", 10, "rocquencourt", 10)
        exp = iotlab.startExp("AutoRest", 10, "grenoble", 8)

    else:
        print ("Re-using already running experiment")
        exp = expList[0]

    print "Experiment id=%s" % exp.expId, exp.getState()
    exp.waitUntilRunning(verbose=True)

    #exp.doNodeCmd("reset", AllList)

    #exitNow

    #codeFirmwareFileName = \
    #    "../riot/RIOT/examples/hello-world/bin/iot-lab_M3/hello-world.elf"

    #codeFirmwareFileName = \
    #    "../riot/RIOT/examples/rpl_udp/bin/iot-lab_M3/rpl_udp.elf"

    snifferFirmwareFileName = \
        "../iot-lab/parts/openlab/build.m3/bin/foren6_sniffer.elf"

    #codeFirmwareFileName = \
    #    "../riot/RIOT/examples/default/bin/iot-lab_M3//default.elf"

    #https://github.com/iot-lab/iot-lab/wiki/HOWTO-use-Foren6-to-diagnose-in-realtime-your-6LoWPAN-experiment

    codeFirmwareFileName = "../openwsn/openwsn-fw/firmware/openos/projects/common/03oos_openwsn_prog"

    #codeFirmwareData = readFile(codeFirmwareFileName)
    #snifferFirmwareData = readFile(snifferFirmwareFileName)
     
    #expInfo = exp.getResources()
    #addressList = [nodeInfo["network_address"] for nodeInfo in expInfo["items"]]
    #pprint.pprint(addressList)


    snifferAddressList = [address for address in addressList
                          if getNodeId(address)%2 == 0]
    snifferAddressList = []
    codeAddressList = list(set(addressList).difference(set(snifferAddressList)))
    
    if len(snifferAddressList) > 0:
        print exp.doNodeCmd("update", snifferAddressList, snifferFirmwareData)
    print exp.doNodeCmd("update", codeAddressList, codeFirmwareData)

    #print "stopping experience"
    #exp.stop()

#---------------------------------------------------------------------------
