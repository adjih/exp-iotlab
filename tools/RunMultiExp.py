#! /usr/bin/python
#---------------------------------------------------------------------------
# Radio Experiment Control
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

from __future__ import print_function, division

from IotlabHelper import readFile, writeFile
import argparse, subprocess, logging
import sys, shutil, os, time, fcntl, select
from os.path import join as J

#---------------------------------------------------------------------------

tstCmd = """
import time, sys
for i in xrange(10000000):
    sys.stdout.write("output line #%s" %i)
    if i % 3 == 0: sys.stdout.write("\\n")
    sys.stdout.flush()
    time.sleep(1)
"""

def runAndLogCommand(cmd, statusMustBeOk = False):
    logging.info("* starting process: " + " ".join(cmd))
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                               stderr=subprocess.STDOUT)
    status = None

    fd = process.stdout.fileno()
    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    pollDelay = 10
    current = ""
    while True:
        status = process.poll()
        if status != None:
            break
        fdList,unused,unused = select.select([fd],[],[], pollDelay)
        if len(fdList) > 0:
            data = process.stdout.read()
            sys.stdout.write(data)
            current += data
            sys.stdout.flush()
            while len(current) > 0:
                pos = current.find("\n")
                if pos < 0:
                    break
                line = current[:pos]
                if len(line) > 0:
                    logging.debug("> "+line)
                current = current[pos+1:]
            
    if statusMustBeOk and status != 0:
        logging.warning("command exited with non-zero status %s" % status)
        raise RuntimeError("command exited with non-zero status", status)
    return status

#---------------------------------------------------------------------------

def runMultipleExp(args, dirName):
    configDict = {}
    execfile(args.configFileName, configDict, configDict)
    baseConfigName = os.path.basename(args.configFileName)
    shutil.copy(args.configFileName, J(dirName, baseConfigName))

    expList = configDict["expArgList"]
    logging.info("config args: %s" % repr(expList))
    
    if args.flash:
        logging.info("*** reflashing")
        runAndLogCommand(["python","FlashRadioExp.py"], True)

    if not args.no_ssh_redirect:
        logging.info("*** doing ssh-forward")
        cmd = "./expctl ssh-forward --type radio-test"
        runAndLogCommand(cmd.split(" "), True)

    for cmd in expList:
        logging.info("*** experiment: %s" % cmd)
        if not args.no_dirname:
            cmd += " --dir %s" % dirName
        print (cmd)
        nbAttempt = 0
        while True:
            time.sleep(args.delay)
            if nbAttempt > 0: 
                logging.info("* retrying (%s/%s)"%(nbAttempt+1, args.nb_retry))
            status = runAndLogCommand(cmd.split(" "), False)
            if status == 0:
                logging.info("* (success)")
                break # success
            else: logging.warning("* (failure command status=%s)\n" % (-status))

            nbAttempt += 1
            if nbAttempt == args.nb_retry:
                logging.error("*** aborting, experiment failed '%s' times"
                              % nbAttempt)
                sys.exit(1)



#---------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument("configFileName", type=str)
parser.add_argument("--flash", action="store_true", default=False)
parser.add_argument("--no-ssh-redirect", action="store_true", default=False)
parser.add_argument("--no-dirname", action="store_true", default=False)
parser.add_argument("--nb-retry", type=int, default=5)
parser.add_argument("--delay", type=float, default=5)
args = parser.parse_args()

#-- create exp dir

name = time.strftime("%Y-%m-%d-%Hh%Mm%S")
dirName = "exp-"+name
if os.path.exists(dirName):
    raise RuntimeError("not overridding existing dir", dirName)
os.mkdir(dirName)
info = {
    "command": sys.argv,
    "args": repr(args),
    "config": args.configFileName
}
writeFile(J(dirName,"general.pydat"), repr(info))

#-- configure logger

logging.basicConfig(
    filename=J(dirName, "complete.log"),
    format='%(asctime)s|%(levelname)s|%(message)s',
    level=logging.DEBUG)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger("").addHandler(console)

#-- start

logging.info("*** starting: %s" % repr(sys.argv))

runMultipleExp(args, dirName)

#---------------------------------------------------------------------------

