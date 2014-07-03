#---------------------------------------------------------------------------
# Cedric Adjih
#---------------------------------------------------------------------------

import sys, argparse, pprint
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

#---------------------------------------------------------------------------

def objToJson(info):
    return json.dumps(info, cls=rest.Encoder)

def toJson(info):
    return json.dumps(info)

def fromJson(jsonStr):
    return json.loads(jsonStr)

#---------------------------------------------------------------------------

class IotlabHelper:
    def __init__(self):
        self.parser = argparse.ArgumentParser() # XXX: not so useful
        #parser.parse_args()
        parser = self
        name, password = getCredentialsOrFail(parser)
        self.request = rest.Api(username=name, password=password, 
                                parser=parser)

    def getSiteList(self):
        return fromJson(self.request.get_sites())

    def getCurrentExpList(self, withWaiting=False):
        """Return a list of running [opt:waiting] experiments"""
        # https://www.iot-lab.info/tools/rest-api-docs/get-users-experiments-details/
        queryset = "state=Running"
        if withWaiting:
            queryset += ",Waiting"
        result = self.request.get_experiments(queryset)
        return fromJson(result)["items"]

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

        #pprint.pprint(fromJson(objToJson(exp)))
        #print "exp_files=", exp_files
        resultJson = self.request.submit_experiment(exp_files)
        return fromJson(resultJson)

    def stopExp(self, expId):
        resultJson = self.request.stop_experiment(expId)
        return fromJson(resultJson)

    def ensureExpLimit(self):
        MaxExp = 1
        expList = self.getCurrentExpList(withWaiting=True)
        if len(expList) >= MaxExp:
            self.error("%s experiment(s) already running/waiting:\n"
                       % len(expList) 
                       + pprint.pformat(expList))
        
    def error(self, message):
        sys.stderr.write("ERROR: "+message+"\n")
        sys.exit(1)

#---------------------------------------------------------------------------

if __name__ == "__main__":
    iotlab = IotlabHelper()
    #pprint.pprint(iotlab.getSiteList())

    expList = iotlab.getCurrentExpList(withWaiting=True)
    #pprint.pprint(expList)

    pprint.pprint(iotlab.stopExp("8150"))

    #if len(expList) == 0:
    #iotlab.ensureNoExp()
    iotlab.startExp("testREST", 10, "grenoble", 2)

#---------------------------------------------------------------------------
