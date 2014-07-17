#---------------------------------------------------------------------------
# Further Helper for IoT-LAB REST API
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

import sys, argparse, pprint, os, time, random
import json, subprocess
sys.path.append("../iot-lab/parts/cli-tools")

from iotlabcli import rest, helpers, experiment

#---------------------------------------------------------------------------

SerialTcpPort = 20000

#---------------------------------------------------------------------------

def readFile(fileName):
    with open(fileName) as f:
        return f.read()

def writeFile(fileName, data):
    with open(fileName, "w") as f:
        f.write(data)

#--------------------------------------------------

def objToJson(info):
    return json.dumps(info, cls=rest.Encoder)

def toJson(info):
    return json.dumps(info)

def fromJson(jsonStr):
    return json.loads(jsonStr)

#---------------------------------------------------------------------------

def getCredentialsOrFail(parser):
    """return (name, password) from file, or exit if not available"""
    (name, password) = helpers.read_password_file(parser)
    if name == None or password == None:
        parser.error("stored .iotlabrc not available, use auth-cli (or make run-auth-cli)")
        sys.exit(1)
    return name, password

def getServerRestUrl():
    return rest.API_URL # XXX

#---------------------------------------------------------------------------

def extractNodeId(address):
    """m3-4.grenoble.iot-lab.info -> integer 4"""
    nodeName = address.split(".")[0]
    return int(nodeName.split("-")[-1])

def reprNodeList(nodeList):
    return ",".join([address.split(".")[0] for address in nodeList])

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

def getExpUniqueServer(exp, nodeList=None):
    if nodeList == None:
        nodeList = exp.getNodeList()
    nodeOfServer = getNodePerServer(nodeList)
    if len(nodeOfServer.keys()) != 1: 
        raise RuntimeError("ERROR: multi-site experiment not handled")
    expServer = nodeOfServer.keys()[0] 
    return expServer


def sortNodeByPriority(nodeList, nodeByPriorityList):
    def getPriority(address):
        nodeId = extractNodeId(address)
        if nodeId in nodeByPriorityList:
            return nodeByPriorityList.index(nodeId)
        else: return len(nodeByPriorityList)

    nodeList = nodeList[:]
    nodeList.sort(key=getPriority)
    return nodeList

#---------------------------------------------------------------------------
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
MaxFlashAttempts = 30

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
                print "  state:", state
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

    def safeFlashNodes(self, firmwareFileName, nodeCount, initialNodeList, 
                       verbose=True):
        """Flash nodes until the exact number `nodeCount' is successfully 
        flashed. Nodes are flashing in the order of `initialNodeList'.
        If `nodeCount' is None, all nodes are flashed, and only once."""
        if nodeCount == 0:
            return [], initialNodeList[:]
        
        countDown = MaxFlashAttempts
        nodeList = initialNodeList[:]
        flashedNodeList = []
        if verbose:
            print "- flashing %s node(s) with '%s'"%(nodeCount,firmwareFileName)
        assert nodeCount > 0
        firmwareData = readFile(firmwareFileName)
        if nodeCount == AllPossibleNodes:
            nodeCount = len(nodeList)
            tryOnce = True
        else: tryOnce = False
        while nodeCount > 0: #len(flashedNodeList):
            countDown -= 1
            if countDown == 0: # don't flash forever
                raise RuntimeError("Too many flash attempts")
            if nodeCount > len(nodeList):
                raise RuntimeError("Not enough available nodes in experiment", 
                                   (nodeList, nodeCount))
            tentativeNodeList = nodeList[:nodeCount]
            nodeList = nodeList[nodeCount:]
            if verbose:
                sys.stdout.write("  . flashing %s:" % reprNodeList(
                        tentativeNodeList))
                sys.stdout.flush()
            result = self.doNodeCmd("update", tentativeNodeList, firmwareData)
            successfulNodeList = result.get('0', [])
            failedNodeList = result.get('1', [])
            if verbose:
                print " success=%s failure=%s" % (
                    reprNodeList(successfulNodeList),
                    reprNodeList(failedNodeList))
            flashedNodeList.extend(successfulNodeList)
            nodeCount -= len(successfulNodeList)
            if tryOnce:
                break

        return flashedNodeList, nodeList

#--------------------------------------------------
# XXX: make it configurable

TypeToFirmware = {
    "foren6-sniffer":
        "../iot-lab/parts/openlab/build.m3/bin/foren6_sniffer.elf",
    "zep-sniffer":
        "../iot-lab/parts/openlab/build.m3/bin/zep_sniffer.elf",
    "zep-sniffer-a8-m3":
        "../iot-lab/parts/openlab/build.a8-m3/bin/zep_sniffer.elf"
}

#SnifferFwFileName = "PreCompiled/foren6_sniffer.elf"
# TunslipBinFileName = "sudo ../local/bin/tunslip6 aaaa::1/64 -L -a localhost -p 2000"

#--------------------------------------------------

ExpTemplateDir = "Experiment-%s"
ExpPersistentPath = "persistent.json"
AllPossibleNodes = ('AllNodes',)
LastExpSymLink = "Experiment-Last"

class IotlabPersistentExp(IotlabExp):
    """An experiment that stores some persistent data in a subdirectory.
    Assuming each experiment-id is unique, every experiment would have
    its own directory."""

    def __init__(self, helper, expId):
        IotlabExp.__init__(self, helper, expId)
        self.persistentInfoCache = None

    #--------------------------------------------------

    def makeLastSymLink(self, verbose=True):
        self.ensureDir()
        if os.path.exists(LastExpSymLink):
            os.remove(LastExpSymLink)
        if verbose:
            expDir = self.getPath("")
            print ". making symlink %s -> %s" % (LastExpSymLink, expDir)
        os.symlink(expDir, LastExpSymLink)

    def getPersistentInfo(self):
        if self.persistentInfoCache == None:
            self._fillPersistentInfoCache()
        return self.persistentInfoCache

    def savePersistentInfo(self, info):
        self.writeFile(ExpPersistentPath, toJson(info))
        self._fillPersistentInfoCache()

    def resetPersistentInfo(self):
        self.savePersistentInfo({})

    def _loadPersistentInfo(self):
        if not self.hasFile(ExpPersistentPath):
            return {}
        else: return fromJson(self.readFile(ExpPersistentPath))

    def _fillPersistentInfoCache(self):
        self.persistentInfoCache = self._loadPersistentInfo()

    def ensurePersistentNameOrReset(self, name):
        """Ensure that the 'ExperimentName' in the Persistent info 
        is equal to `name', or reset the persistent info.
        This can be used to 'reuse' a IoT-LAB reservation with 
        another kind of Python experiment script.
        Returns True iff the persistent info was reinitialized"""
        info = self.getPersistentInfo()
        oldName = info.get("ExperimentName")
        if oldName != name:
            if oldName != None:
                print "- Resetting persistent info (%s -> %s)" % (
                    repr(name), repr(oldName))
            info = { }
            info["ExperimentName"] = name
            self.savePersistentInfo(info)
            return True
        return False

    #--------------------------------------------------

    def ensureDir(self):
        expDir = self.getPath("")
        if not os.path.exists(expDir):
            os.mkdir(expDir)

    def getPath(self, subPath):
        prefix = ExpTemplateDir % self.expId
        if subPath == "":
            return prefix
        else: return os.path.join(prefix, subPath)

    def hasFile(self, subPath):
        return os.path.exists(self.getPath(subPath))

    def readFile(self, subPath):
        return readFile(self.getPath(subPath))
        
    def writeFile(self, subPath, data):
        self.ensureDir()
        return writeFile(self.getPath(subPath), data)
    
    #--------------------------------------------------

    def recordFlashedNodes(self, nodeTypeName, nodeList, firmwareFileName):
        expInfo = self.getPersistentInfo()
        if "nodeInfoByType" not in expInfo:
            expInfo["nodeInfoByType"] = {}
        expInfo["nodeInfoByType"][nodeTypeName] = {
            "nodes": nodeList,
            "firmware": firmwareFileName
            }
        self.savePersistentInfo(expInfo) # XXX: maybe not now

    def ensureFlashedNodes(self, nodeTypeName, firmwareFileName, 
                           nodeCount, initialNodeList):
        expInfo = self.getPersistentInfo()
        if nodeTypeName not in expInfo:
            flashedNodeList, currentNodeList = self.safeFlashNodes(
                firmwareFileName, nodeCount, initialNodeList)
            assert (nodeCount == AllPossibleNodes 
                    or len(flashedNodeList) == nodeCount)
            self.recordFlashedNodes(nodeTypeName, flashedNodeList, 
                                    firmwareFileName)
        else:
            flashedNodeList = expInfo["nodesInfoByType"][nodeTypeName]
            currentNodeList = initialNodeList[:]
            if (len(flashedNodeList) != nodeCount 
                and nodeCount != AllPossibleNodes):
                raise RuntimeError("Inconsistent number of flashed nodes",
                                   (flashedNodeList, nodeCount))
            print ". using already flashed '%s'" % reprNodeList(flashedNodeList)
        for address in flashedNodeList:
            if address in currentNodeList:
                currentNodeList.remove(address)
        return flashedNodeList, currentNodeList

    def ensureFlashedStdNodes(self, nodeTypeName, nodeCount, nodeList,
                              withRandomOrder = False):
        if withRandomOrder:
            nodeList = nodeList[:]
            random.shuffle(nodeList)
        fw = TypeToFirmware[nodeTypeName]
        return self.ensureFlashedNodes(nodeTypeName, fw, nodeCount, nodeList)

#--------------------------------------------------
# Standard firmware (sniffer)

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
        name, password = getCredentialsOrFail(self)
        if expServer == None:
            serverUrl = getServerRestUrl()
        else: serverUrl = "https://{0}/rest/" .format(expServer)
        self.request = rest.Api(url = serverUrl,
                                username=name, password=password, 
                                parser=self)
        self.userName = name

    #--------------------------------------------------
    # Site / resources information
    #--------------------------------------------------

    def getSiteList(self):
        return fromJson(self.request.get_sites())

    def getResources(self, site= None):
        return fromJson(self.request.get_resources(site))["items"]

    def getResourcesId(self, site= None):
        return fromJson(self.request.get_resources_id(site))["items"]

    def getAliveList(self, site, archi):
        return [info for info in self.getResources(site)
                if info["archi"] == archi and info["state"] == "Alive"]

    #--------------------------------------------------
    # Experiments
    #--------------------------------------------------

    def _makeExp(self, expId):
        "Factory for IotlabExp"
        return IotlabPersistentExp(self, expId)

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


#---------------------------------------------------------------------------
# More utilities functions
#---------------------------------------------------------------------------

DefaultSite = "grenoble"
DefaultNbNode = 4
DefaultDuration = 10 # minutes

def parserAddTypicalArgs(parser, defaultName):
    parser.add_argument("--name", default=defaultName)
    parser.add_argument("--site", default=DefaultSite)
    parser.add_argument("--nb-nodes", dest="nbNodes", 
                        type=int, default=DefaultNbNode)
    parser.add_argument("--duration", type=int, default=DefaultDuration)
    parser.add_argument("--dev", type=str, default=None)
    parser.add_argument("--nb-foren6-sniffers", dest="nbForen6Sniffers", 
                        type=int, default=0)
    parser.add_argument("--nb-zep-sniffers", dest="nbZepSniffers", 
                        type=int, default=0)

def ensureExperimentFromArgs(args):
    iotlab = IotlabHelper(args.dev)
    expList = iotlab.getExpList()
    if len(expList) == 0:
        print ("- No experience, starting one")
        exp = iotlab.startExp(args.name, args.duration, args.site, args.nbNodes)
    else:
        print ("- Re-using already running experiment")
        exp = expList[0]

    print ("  experiment id=%s" % (exp.expId))
    exp.waitUntilRunning(verbose=True)
    return iotlab, exp

#---------------------------------------------------------------------------
# Copied from contiki-senslab-unified/tools/cooja/jython/PySimul.py
# (I wrote in 2012-2013) and modified
# XXX: maybe should use python circus ? pexpect ? screenutils ?
#--------------------------------------------------

class ProcessManager:
    ROXTerm = "/usr/bin/roxterm"

    def __init__(self, isFirstTerm=True):
        self.processList = []
        self.isFirstTerm = isFirstTerm
        self.windowTitle = None

    def setWindowTitle(self, windowTitle):
        self.windowTitle = windowTitle

    def startSubProcessInTerm(self, tabTitle, command, bgColor="White"):
        command += " ; printf '<done>' ; sleep 10" # so that error can be seen
        if os.path.exists(self.ROXTerm):
            argList = [self.ROXTerm] 
            if self.isFirstTerm:
                # http://sourceforge.net/p/roxterm/discussion/422639/thread/e550bfb1/?limit=50
                argList.append("--fork")
                self.isFirstTerm = False
            else: argList.append("--tab")

            if self.windowTitle == None:
                self.windowTitle = "Experiment"
            argList += ["-T", self.windowTitle] 
            argList += [ "-n", tabTitle, "-e", "bash", "-c", command]

        else:
            argList = ["xterm", 
                       "-bg", bgColor, "-fg", "NavyBlue",
                       "-T", tabTitle,
                       "-e", "bash -c '%s'" % command]
        newProcess = subprocess.Popen(args=argList, shell=False)
        self.processList.append(newProcess)

    def addSubProcess(self, process):
        # XXX: this does not kill subprocess terms
        self.processList.append(process)

    def killEachSubProcess(self):
        for process in self.processList:
            process.terminate()
            del process

        self.processList = []

def testProcessManager():
    processManager = ProcessManager()
    processManager.setWindowTitle("ProcessManager test")
    processManager.startSubProcessInTerm("Do-sleep-5", "sleep 5")
    processManager.startSubProcessInTerm("Do-sleep-10", "sleep 10")
    processManager.startSubProcessInTerm("Do-sleep-20", "sleep 20")
    import time
    time.sleep(15)
    processManager.killEachSubProcess()

#---------------------------------------------------------------------------

if __name__ == "__main__":
    iotlab = IotlabHelper()
    
    #pprint.pprint(iotlab.getResources("grenoble"))
    #pprint.pprint(iotlab.getResourcesId("grenoble"))
    print "Alive at grenoble:", len(iotlab.getAliveList(
            "grenoble", "m3:at86rf231"))

    print "--- List of sites"
    pprint.pprint(iotlab.getSiteList())

    print "--- List of experiments"
    expInfoList = iotlab.getExpInfoList(["Running", "Waiting", "Launching",
                                         "toLaunch"])
    pprint.pprint(expInfoList)

    print "--- List of profiles"
    profileList = iotlab.getProfileList()
    pprint.pprint(profileList)

#---------------------------------------------------------------------------
