#---------------------------------------------------------------------------
# Cedric Adjih
#---------------------------------------------------------------------------

from __future__ import print_function, division, unicode_literals

import argparse, pprint, math
from cStringIO import StringIO
import sys, json, os, time, subprocess, shutil
import tarfile, zipfile

import numpy as np
import numpy.ma as ma

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt


#---------------------------------------------------------------------------
# copied from IotlabHelper (and wrote equivalent zillion times)

def readFile(fileName):
    with open(fileName) as f:
        return f.read()

def writeFile(fileName, data):
    with open(fileName, "w") as f:
        f.write(data)

def syso(msg): # name comes from Eclipse+Java
    sys.stdout.write(msg)
    sys.stdout.flush()

#--------------------------------------------------

J = os.path.join

# This class needs to become 4 classes (Base,Zip,Tar,Union)

class TarFileManager:
    def __init__(self, archiveName):
        if archiveName.endswith(".lzma"):
            cmd = ["lzma", "--decompress", "--stdout", archiveName]
            syso ("(uncompressing %s [lzma])" % archiveName)
            data = subprocess.check_output(cmd) # must have 'lzma' program
            decompressedFile = StringIO(data)
        elif archiveName.endswith(".lrz"):
            cmd = ["lrzip", "-d", "-o", "-", archiveName]
            syso ("(uncompressing %s [lrzip])" % archiveName)
            data = subprocess.check_output(cmd) # must have 'lzma' program
            decompressedFile = StringIO(data)
        else:
            decompressedFile = StringIO(readFile(archiveName))

        self.tarFile = tarfile.open(self.dirName+".tar."+suffix, "r",
                                    fileobj = decompressedFile)
        self.tarNameList = set(self.tarFile.getnames())
        self.tarFile = []



class FileManager:
    def __init__(self, dirName):
        self.dirName = dirName
        self.zipFile = None

        if os.path.exists(self.dirName+".zip"):
            self.zipFile = zipfile.ZipFile(self.dirName+".zip", "r")
            self.zipNameList = set(self.zipFile.namelist())
        else: self.zipFile = None

        self.tarFile = None
        # suffix = "gz" 
        suffix = ".bz2"
        if os.path.exists(self.dirName+".tar.lzma"):
            cmd = ["lzma", "--decompress", "--stdout", self.dirName+".tar.lzma"]
            syso ("(uncompressing %s)" % (self.dirName+".tar.lzma"))
            data = subprocess.check_output(cmd) # must have 'lzma' program
            decompressedFile = StringIO(data)
            self.tarFile = tarfile.open(self.dirName+".tar."+suffix, "r",
                                        fileobj = decompressedFile)
            self.tarNameList = set(self.tarFile.getnames())
        elif os.path.exists(self.dirName+".tar."+suffix):
            # NOTE: tar+bzip2|gzip file, slow as molasses (probably decodes
            # everything before, for each extraction)
            self.tarFile = tarfile.open(self.dirName+".tar."+suffix, 
                                        "r:"+suffix)
            self.tarNameList = set(self.tarFile.getnames())
        else: self.tarFile = None

    def writeFile(self, fileName, data):
        self.ensureDir()
        writeFile(J(self.dirName, fileName), data)

    def ensureDir(self):
        if not os.path.exists(self.dirName):
            os.mkdir(self.dirName)

    def readFile(self, fileName):
        fullPath = J(self.dirName, fileName)
        if not os.path.exists(fullPath):
            if self.zipFile != None:
                f = self.zipFile.open(fullPath)
                result = f.read()
                f.close()
                return result
            elif self.tarFile != None:
                f = self.tarFile.extractfile(fullPath)
                result = f.read()
                f.close()
                return result
        return readFile(fullPath)

    def getPath(self, fileName):
        return J(self.dirName, fileName)

    def exists(self, fileName):
        fullPath = J(self.dirName, fileName)
        return (os.path.exists(fullPath) 
                or (self.zipFile != None and fullPath in self.zipNameList)
                or (self.tarFile != None and fullPath in self.tarNameList))

#---------------------------------------------------------------------------
# Merging subdirectories in one file
# (longer than expected)

MergedList = [
    "commandLine", "launchTime"
]

MergedKeyPrefix = "merged:"

def tryMergeOneExpMetaInfo(meta1, meta2, mergedList = MergedList):
    key1List = [k for k in sorted(meta1.keys()) 
                if k not in MergedList and not k.startswith(MergedKeyPrefix)]
    key2List = [k for k in sorted(meta1.keys()) 
                if k not in MergedList and not k.startswith(MergedKeyPrefix)]
    if key1List != key2List:
        raise ValueError("inconsistent experiment meta-data", 
                         (meta1.keys(), meta2.keys()))
    if key1List != key2List:
        return None

    diffKeyList = [ key for key in key1List if meta1[key] != meta2[key]]
    if len(diffKeyList) >= 2:
        return None
    if len(diffKeyList) == 0:
        raise ValueError("redundant experiments (same keys/values)", meta1)

    result = dict([(k,meta1[k]) for k in key1List]) # note: not a deep copy
    diffKey = diffKeyList.pop() 
    def ensureList(x):
        if not isinstance(x, list): return [x]
        else: return x
    value1 = ensureList(meta1[diffKey])
    value2 = ensureList(meta2[diffKey])
    result[diffKey] = value1 + value2
    
    mergedTable = {}
    for k in set(meta1.keys()).union(meta2.keys()):
        if k not in MergedList:
            continue
        l1 = [meta1[k]] if (k in meta1) else []
        l2 = [meta2[k]] if (k in meta2) else []
        mergedTable[MergedKeyPrefix+k] = l1 + l2

    for k in set(meta1.keys()).union(meta2.keys()).union(mergedTable.keys()):
        if not k.startswith(MergedKeyPrefix):
            continue
        result[k] = meta1.get(k,[]) + mergedTable.get(k,[]) + meta2.get(k,[])

    return result


def tryMergeMultipleExpMetaInfo(expMetaInfoList):
    # brute force merge
    # (requires expMetaInfoList is in some logical ordering, 
    #  if parameter space dimension >= 2)
    print ("Merging:",end=" ")
    changed = True
    while changed and len(expMetaInfoList) > 1:
        changed = False
        for i,meta1 in enumerate(expMetaInfoList):
            for j,meta2 in enumerate(expMetaInfoList):
                if j <= i:
                    continue
                newMeta = tryMergeOneExpMetaInfo(meta1, meta2)
                if newMeta != None:
                    expMetaInfoList[i] = newMeta
                    del expMetaInfoList[j]
                    changed = True
                    print ("#%s+#%s " %(i,j), end="")
                    sys.stdout.flush()
                    break
            if changed:
                break

    if len(expMetaInfoList) == 1:
        print (" succeeded.")
        return expMetaInfoList.pop()
    else:
        print (" failed.")
        return None


def finishMergeDirWithLink(fileManager, dirName, mergedExpMeta):
    fileManager.writeFile("meta.pydat", repr(mergedExpMeta))
    for subDirName in mergedExpMeta[MergedKeyPrefix+"subDirName"]:
        subDirPath = fileManager.getPath(subDirName)
        for fileName in os.listdir(subDirPath):
            if os.path.basename(fileName) == "meta.pydat":
                continue
            linkOldPath = J(subDirName, fileName)
            oldPath = J(subDirPath, fileName)
            newPath = J(dirName, fileName)
            if not os.path.lexists(newPath):
                os.symlink(linkOldPath, newPath)
            else:
                if not os.path.samefile(oldPath,newPath):
                    old = readFile(oldPath)
                    new = readFile(newPath)
                    if old != new:
                        raise ValueError("inconsistent file content in merge", 
                                         (oldPath, newPath))

def finishMergeDirWithZip(dirName, mergedExpMeta):
    zipName = dirName + ".zip"
    if os.path.exists(zipName):
        raise RuntimeError("archived file already exists", zipName)

    f = zipfile.ZipFile(zipName, "w", zipfile.ZIP_DEFLATED)
    for fileName in os.listdir(dirName):
        fullPath = J(dirName, fileName)
        if os.path.isfile(fullPath) and not os.path.islink(fullPath):
            f.write(fullPath)
            syso("+")

    f.writestr(J(dirName, "meta.pydat"), repr(mergedExpMeta))
    realPathOf = { J(dirName, "meta.pydat"): "(generated)"}
    for subDirName in mergedExpMeta[MergedKeyPrefix+"subDirName"]:
        subDirPath = J(dirName, subDirName)
        for fileName in os.listdir(subDirPath):
            if os.path.basename(fileName) == "meta.pydat":
                continue
            linkOldPath = J(subDirName, fileName)
            oldPath = J(subDirPath, fileName)
            newPath = J(dirName, fileName)
            if newPath not in realPathOf:
                f.write(oldPath, arcname = newPath)
                realPathOf[newPath] = oldPath
                #print ("new", oldPath, newPath)
                syso("+")
            else:
                #print ("old", oldPath, newPath)
                old = readFile(oldPath)
                new = readFile(realPathOf[newPath])
                syso(".")
                if old != new:
                    raise ValueError("inconsistent file content in merge", 
                                     (oldPath, realPathOf[newPath]))
    f.close()

def attemptMergeDir(dirName):
    fileManager = FileManager(dirName)

    expMetaInfoList = []
    for subDirName in sorted(os.listdir(dirName)):
        otherManager = FileManager(J(dirName, subDirName))
        if not otherManager.exists("meta.pydat"):
            continue
        if not otherManager.exists("success.pydat"):
            continue
        success = eval(otherManager.readFile("success.pydat"))
        if not success:
            continue

        expMetaInfo = eval(otherManager.readFile("meta.pydat"))
        expMetaInfo[MergedKeyPrefix+"subDirName"] = [subDirName]
        expMetaInfoList.append(expMetaInfo)

    mergedExpMeta = tryMergeMultipleExpMetaInfo(expMetaInfoList)
    if mergedExpMeta == None:
        return False
    assert "mergeInfo" not in mergedExpMeta # not necessary, but don't lose info
    mergedExpMeta["mergeInfo"] = sys.argv

    #finishMergeDirWithLink(fileManager, dirName, mergedExpMeta)
    finishMergeDirWithZip(dirName, mergedExpMeta)

    if args.archive:
        print ("archiving in tar")
        subprocess.check_call(["tar", "cf", dirName+".tar", dirName])
        shutil.rmtree(dirName)
        print ("compressing (lzma)")
        subprocess.check_call(["lzma", dirName+".tar"])
    return True

#attemptMergeDir("exp-2014-freq")
#attemptMergeDir("exp-2014-08-16-02h13m08")

#---------------------------------------------------------------------------

SeqNumOffsetError = 0xff00
SeqNumCrcError = SeqNumOffsetError+ord('C')
SeqNumLengthError = SeqNumOffsetError+ord('L')
SeqNumMagicError = SeqNumOffsetError+ord('M')
SeqNumCrc32Error = SeqNumOffsetError+ord('3')
ReprOfSeqNumError = {
    SeqNumCrcError: "radio-crc",
    SeqNumLengthError: "radio-length",
    SeqNumMagicError: "magic",
    SeqNumCrc32Error: "user-crc32"
    }

ErrorNameList = (ReprOfSeqNumError.values() 
                 + ["bad-seq-num", "invalid-handle-irq"])

class ExperimentParser(FileManager):

    def __init__(self, dirName):
        self.dirName = dirName
        FileManager.__init__(self, self.dirName)
        self.generalInfo = eval(self.readFile("meta.pydat"))

    def parseOneBurst(self, fileName, idx):
        info = eval(self.readFile(fileName))
        expInfo = self.generalInfo
        nbNode = len(expInfo["idList"])
        nbPacket = expInfo["nbPacket"]

        # table for results
        recvArray = np.zeros((nbNode, nbPacket), np.uint8)
        lqiArray = np.zeros((nbNode, nbPacket), np.uint8)
        rssiArray = np.zeros((nbNode, nbPacket), np.uint8)
        errorCountArrayTable = dict([ (errorName, np.zeros((nbNode,),np.int16))
                                      for errorName in ErrorNameList ])

        
        # check, just in case (normally empty)

        if len(info["unparsed"]) > 0:
            raise ValueError("unparsed information", info["unparsed"])

        # parse sender info

        rawSenderInfo = info["cmdXmit"][1][idx]
        if len(rawSenderInfo) != 2:
            raise ValueError("too much sender info in cmdXmit", rawSenderInfo)
        senderInfo = eval(rawSenderInfo[0][1])
        if senderInfo["nbPacket"] != expInfo["nbPacket"]:
            raise ValueError("inconsistent nb sent packets",
                             (senderInfo["nbPacket"], expInfo["nbPacket"]))
        if senderInfo["nbError"] != 0: # check no error found during exp. 
            raise ValueError("transmission errors found", senderInfo["nbError"])

        edList = []
        for seqNum,(t1,t2,ed,success) in enumerate(senderInfo["send"]):
            if success != 1:
                raise ValueError("transmission failed", 
                                 (senderInfo["send"],seqNum))
            edList.append(ed)

        def removeInvalidHandleIrq(clockAndMsgList, errorMsgTemplate):
            count = 0
            i = 0
            while i < len(clockAndMsgList):
                t, msg = clockAndMsgList[i]
                if msg.find("invalid handle_irq") >= 0:
                    print ("[%s]"%fileName, errorMsgTemplate % msg, end="")
                    del clockAndMsgList[i]
                    count += 1
                else: i += 1
            return count

        for otherIdx, eventList in info["cmdXmit"][1].iteritems():
            if otherIdx == idx:
                continue
            count = removeInvalidHandleIrq(eventList, "(#%s)" % (otherIdx)
                                           + "ignoring in 'send' output: %s")
            errorCountArrayTable["invalid-handle-irq"][otherIdx] += count
            if len(eventList) > 0:
                raise ValueError("unexpected output from receiver", 
                                 (otherIdx, eventList))

        xmitId = senderInfo["id"]
        senderPacketList = info["cmdXmit"][1]
        sys.stdout.write(".")
        sys.stdout.flush()

        # check receiver output
        for otherIdx, eventList in info["cmdShow"][1].iteritems():
            count = removeInvalidHandleIrq(eventList, "(#%s)" % (otherIdx)
                                           + "ignoring in 'show' ouput: [%s]")
            errorCountArrayTable["invalid-handle-irq"][otherIdx] += count
            if len(eventList) >= 2:
                raise ValueError("multiple output to cmd show", eventList)
        
        # parse receiver output

        notSeenSet = set(range(nbNode))

        for otherIdx, showStr in info["cmdShow"][0].iteritems():
            assert otherIdx in notSeenSet
            notSeenSet.remove(otherIdx)
            if otherIdx == idx:
                continue
            recvInfo = eval(showStr)
            if recvInfo["nbChange"] >= 1:
                print ("\nmultiple changes of xmitId", recvInfo)
                        
            errorLogTable = dict([ (errorName, []) 
                                   for errorName in ErrorNameList])

            lastSeqNum = -1
            for j,packetInfo in enumerate(recvInfo["recv"]):
                (i,rssi,lqi,ts,te) = packetInfo
                seqNum = i

                # Old-style errors (for old logs)
                #if packetInfo[0] == 0xffff:
                #     errorLogTable["radio-crc"].append(lastSeqNum)
                #elif packetInfo[0] == 0xfffe:
                #    errorLogTable["magic"].append(lastSeqNum)

                # New-style errors
                if seqNum >= SeqNumOffsetError:
                    assert seqNum in ReprOfSeqNumError
                    errorType = ReprOfSeqNumError[seqNum]
                    errorLogTable[errorType].append(lastSeqNum)
                    # NOTE: information about timing is not copied

                # Well received packet
                else: 

                    if (not (0 <= seqNum < nbPacket) 
                        or recvArray[otherIdx][seqNum]!=0
                        or (lastSeqNum != None and seqNum <= lastSeqNum)):
                        print ("ignoring inconsistent seqNum",
                               (lastSeqNum, seqNum, nbPacket))
                        pprint.pprint(recvInfo)
                        #raise ValueError("invalid packetIdx", i)

                    else:
                        lastSeqNum = seqNum
                        recvArray[otherIdx][i] = 1
                        lqiArray[otherIdx][i] = lqi
                        rssiArray[otherIdx][i] = rssi

            for errorName in ErrorNameList:
                if errorName == "invalid-handle-irq":
                    continue
                errorCountArrayTable[errorName][otherIdx] = len(
                    errorLogTable[errorName])

            #if errorCountArrayTable["user-crc32"][otherIdx] > 0:
            #    print (errorLogTable)
            #if errorCountArrayTable["magic"][otherIdx] > 0:
            #    #print (otherIdx, errorLogTable, fileName)
            #    print (idx, otherIdx, fileName)
            #if errorCountArrayTable["radio-crc"][otherIdx] > 0:
            #    print (errorLogTable)
            #if errorCountArrayTable["radio-length"][otherIdx] > 0:
            #    print (errorLogTable)
            #if recvInfo["nbLockedError"] > 0:
            #    pprint.pprint(recvInfo)
            #    print (fileName)

            countRecv = recvArray[otherIdx].sum()
            if recvInfo["id"] != xmitId and countRecv != 0:
                #print (recvInfo["id"], xmitId, countRecv)
                raise ValueError(
                    "bad xmit id", (recvInfo["id"], xmitId, recvInfo,countRecv))


        if len(notSeenSet) != 0:
            raise ValueError("missing report", notSeenSet)

        return ({ "ed":np.array(edList), 
                  "recv":recvArray,
                  "lqi":lqiArray,
                  "rssi":rssiArray }, 
                errorCountArrayTable)

    def parseEveryBurst(self):
        powerList = self.generalInfo["powerList"]
        idxList = self.generalInfo["idList"] # should be [0,1,2,3... n-1]
        channelList = self.generalInfo["channelList"]
        nbNode = len(self.generalInfo["idList"])
        nbPacket = self.generalInfo["nbPacket"]

        dimRecv = (len(powerList), len(channelList), nbNode, nbNode, nbPacket)
        dimStatRecv = (len(powerList), len(channelList), nbNode, nbNode)
        dimSend = (len(powerList), len(channelList), nbNode, nbPacket)

        errorCountTable = dict([ 
                (errorName, np.zeros((dimStatRecv), np.uint16))
                for errorName in ErrorNameList ])

        fullTable = { "recv": np.zeros(dimRecv),
                      "lqi": np.zeros(dimRecv),
                      "rssi": np.zeros(dimRecv),
                      "ed": np.zeros(dimSend) }
        
        resultTable = {}
        for powerIdx,power in enumerate(powerList):
            for channelIdx,channel in enumerate(channelList):
                for idx in idxList:
                    fileName = ("exp-i%s-p%s-c%s.pydat" % (idx, power, channel))
                    if exp.exists(fileName):
                        (oneTable, oneErrorCountTable 
                         ) = exp.parseOneBurst(fileName, idx)
                        #assert set(oneTable.keys()) == set(fullTable.keys())
                        for name in fullTable.keys():
                            fullTable[name][powerIdx,channelIdx,idx] \
                                = oneTable[name]
                        for name in errorCountTable.keys():
                            errorCountTable[name][powerIdx,channelIdx,idx] \
                                = oneErrorCountTable[name]
                    else: raise ValueError("missing file", fileName)

        return fullTable, errorCountTable

    def parseToMatrix(self):
        self.ensureDir()
        statTable, errorTable = self.parseEveryBurst()
        np.savez_compressed(self.getPath("stat"), **statTable)
        np.savez_compressed(self.getPath("error"), **errorTable)

#---------------------------------------------------------------------------

class ExperimentAnalysis(FileManager):

    def __init__(self, dirName):
        self.dirName = dirName
        FileManager.__init__(self, self.dirName)

        self.generalInfo = eval(self.readFile("meta.pydat"))
        self.nbNode = len(self.generalInfo["idList"])
        self.nbPacket = self.generalInfo["nbPacket"]
        self.channelList = self.generalInfo["channelList"]
        self.powerList = self.generalInfo["powerList"]
        self.stat = np.load(self.getPath("stat.npz"))
        self.error =  np.load(self.getPath("error.npz"))

    def readNodePos(self):
        resourceList = eval(self.readFile("resources.pydat"))["items"]

        infoOfAddress = {}
        for info in resourceList:
            infoOfAddress[info["network_address"]] = info

        posTable = {}
        for i,nodeInfo in enumerate(self.generalInfo["nodeList"]):
            moreInfo =  infoOfAddress.get(nodeInfo[0])
            posTable[i] = tuple([float(moreInfo[u]) for u in ["x","y","z"]])

        return posTable

    def summary(self):
        print ("--- Parameters")
        print ("Number of nodes: %s" % self.nbNode)
        print ("Number of packets: %s" % self.nbPacket)
        print ("Channel list: %s" % 
               " ".join(["%s"%c for c in self.channelList]))
        print ("Power list: %s" % 
               " ".join(["%s"%p for p in self.powerList]))
        
        print ("--- Error stats:")
        for name in ErrorNameList:
            print ("total %s: %s" % (name, self.error[name].sum()))

        print ("--- Base stats:")
        statRecv = self.stat["recv"].copy() # XXX:force load
        statEd = self.stat["ed"].copy() # XXX:force load
        totalSentPacket = self.stat["ed"].size
        print ("Total packets sent: %s" % totalSentPacket)
        totalRecvPacket = statRecv.sum()
        print ("Total packets received: %s (avg=%s per sent packet)" 
               % (totalRecvPacket, totalRecvPacket/totalSentPacket))

        print ("--- Detailed base stats :")
        for ip,power in enumerate(self.powerList):
            for ic,channel in enumerate(self.channelList):
                s = ""
                #if len(self.powerList) >= 2:
                s += "%s dBm " % power
                #if len(self.channelList) >= 2:
                s += "ch%s " % channel
                partStatRecv = statRecv[ip,ic]
                print (s+"- rcv:", int(partStatRecv.sum()), end=" - ")
                print ("avg ed=%.04f" % statEd[ip,ic].mean(), end=" - ")
                print ("magic=% 5d"%self.error["magic"][ip,ic].sum(), end=" - ")
                print ("radio-crc=%s" % self.error["radio-crc"][ip,ic].sum())

    def plotPos(self):
        posTable = self.readNodePos()
        xList = []
        yList = []
        for x,y,z in posTable.values():
            xList.append(x)
            yList.append(y)
        plt.plot(xList,yList,"*")
        plt.draw()

    def plot(self):
        powerList = self.generalInfo["powerList"]
        idxList = self.generalInfo["idList"] # should be [0,1,2,3... n-1]
        channelList = self.generalInfo["channelList"]
        recvArray =  self.readRecvMatrix()
        nbPacket = self.generalInfo["nbPacket"]

        print (time.time())
        xList = []
        yList = []
        for powerIdx,power in enumerate(powerList):
            for channelIdx,channel in enumerate(channelList):
                xList.append(channel)
                count = recvArray[powerIdx][channelIdx].size
                yList.append(recvArray[powerIdx][channelIdx].sum() 
                             / float(count))
        plt.plot(xList,yList)
        plt.ylim(0)
#        plt.show()
        plt.clf()

        print (time.time())

        # Histogram of loss rate of the links
        successRateList = []
        for powerIdx,power in enumerate(powerList):
            for channelIdx,channel in enumerate(channelList):
                for idx in idxList:
                    for otherIdx in idxList:
                        count= recvArray[powerIdx,channelIdx,idx,otherIdx].sum()
                        if count > 0:
                            successRateList.append(count / nbPacket)
        successRateList.sort()
        plt.plot(successRateList)
        plt.show()
        plt.clf()
        print (time.time())

#---------------------------------------------------------------------------

class ExperimentModel(ExperimentAnalysis): # implementation re-use
    def __init__(self, dirName):
        ExperimentAnalysis.__init__(self, dirName)
        self.posTable = self.readNodePos()

    def getClosest(self, x,y,z=None):
        dAndI = [ ((x-xx)**2 + (y-yy)**2 + (0 if z==None else (z-zz))**2, i)
                  for i,(xx,yy,zz) in enumerate(self.posTable.itervalues()) ]
        dAndI.sort()
        return dAndI[0][1], math.sqrt(dAndI[0][0])
        

class ExperimentControllerView:
    def __init__(self, model):
        self.model = model
        self.fig = plt.figure()

        self.ax = self.fig.add_subplot(111)
        xList = []
        yList = []
        for x,y,z in self.model.posTable.values():
            xList.append(x)
            yList.append(y)
        self.ax.plot(xList,yList,".k")

        cid = self.fig.canvas.mpl_connect("button_press_event", self.eventClick)
        plt.show()

    def eventClick(self, event):
        print ("click click", event)
        #self.fig.clf()
        #self.ax.clf()
        #print (event.x, event.y, event.canvas)
        print (event.xdata, event.canvas)
        nodeIdx, distance = (self.model.getClosest(event.xdata,event.ydata))
        
        #self.ax2 = self.fig.add_subplot(222)
        (x,y,z) = self.model.posTable[nodeIdx]
        print(self.ax.plot([x],[y], "o"))

        plt.draw()

#---------------------------------------------------------------------------

# XXX:remove
#PowerList = [
#    "-17", "-12", "-9", "-7", "-5", "-4", "-3", "-2", "-1",
#    "0", "0.7", "1.3", "1.8", "2.3", "2.8", "3"]
#powerList = PowerList

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest="command")

rawParserParser = subparsers.add_parser("parse")
rawParserParser.add_argument("dirName", type=str)

summaryParser = subparsers.add_parser("summary")
summaryParser.add_argument("dirName", type=str)

mergeParser = subparsers.add_parser("merge")
mergeParser.add_argument("dirName", type=str)
mergeParser.add_argument("--archive", action="store_true", default=False)

posParser = subparsers.add_parser("pos")
posParser.add_argument("dirName", type=str)

args = parser.parse_args()

def numpyReadArray(fileName):
    npzFile = np.load(fileName)
    keyList = npzFile.keys()
    if len(keyList) >= 2:
        raise ValueError("More than 2 keys", keyList)
    return npzFile[keyList[0]]


if args.command == "parse":
    exp = ExperimentParser(args.dirName)
    exp.parseToMatrix()

elif args.command == "merge":
    success = attemptMergeDir(args.dirName)
    if not success:
        print ("Error: Could not merge sub-directories of '%s'" % args.dirName)
        sys.exit(1)
    else:
        print ("(merged successfully)")

elif args.command == "summary":
    analysis = ExperimentAnalysis(args.dirName)
    analysis.summary()

elif args.command == "pos":
    #analysis = ExperimentAnalysis(args.dirName)
    #analysis.plotPos()
    model = ExperimentModel(args.dirName)
    gui = ExperimentControllerView(model)
    

#---------------------------------------------------------------------------
