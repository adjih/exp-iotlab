#---------------------------------------------------------------------------
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

from __future__ import print_function, division, unicode_literals

import argparse, pprint, math, warnings

try: from cStringIO import StringIO
except: from io import BytesIO as StringIO # in this case: assume python 3

import sys, json, os, time, subprocess, shutil
import tarfile, zipfile

import numpy as np
import numpy.ma as ma

import matplotlib
if __name__ == "__main__":
    matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

#--------------------------------------------------

def toRepr(value):
    return repr(value).encode("ascii")

#---------------------------------------------------------------------------
# copied from IotlabHelper (and wrote equivalent zillion times)

def readFile(fileName):
    with open(fileName) as f:
        return f.read()

def writeFile(fileName, data):
    with open(fileName, "wb") as f:
        f.write(data)

def syso(msg): # name comes from Eclipse+Java
    sys.stdout.write(msg)
    sys.stdout.flush()

#--------------------------------------------------

J = os.path.join

def pseudoListDir(dirName, fileNameList):
    while dirName.startswith("./"):
        dirName = dirName[2:]
    while len(dirName) >= 2 and dirName.endswith("/"):
        dirName = dirName[:-1]
    if dirName == ".":
        dirName = ""
    result = []
    for fileName in fileNameList:
        if os.path.dirname(fileName) == dirName:
            result.append(os.path.basename(fileName))
    return result
        

class TarFileManager:
    def __init__(self, archiveName):
        uncompressCmdTable = {".lzma": "lzma", ".gz": "gzip", 
                              ".bz2": "bzip2", ".xz": "xz"}
        uncompressCmd = None
        for suffix,cmd in uncompressCmdTable.items():
            if archiveName.endswith(suffix):
                uncompressCmd = cmd
        if uncompressCmd != None:
            cmd = [uncompressCmd, "--decompress", "--stdout", archiveName]
            syso ("(uncompressing %s in RAM [%s]" % (archiveName,uncompressCmd))
            data = subprocess.check_output(cmd) # must have proper program
            decompressedFile = StringIO(data)
        elif archiveName.endswith(".lrz"):
            cmd = ["lrzip", "-d", "-o", "-", archiveName]
            syso ("(uncompressing %s [lrzip])" % archiveName)
            data = subprocess.check_output(cmd) # must have lrzip program
            decompressedFile = StringIO(data)

        else: decompressedFile = None
        #decompressedFile = StringIO(readFile(archiveName))

        self.tarFile = tarfile.open(archiveName, "r", 
                                    fileobj = decompressedFile)

        self.initNameSet()

    def initNameSet(self):
        nameList = self.tarFile.getnames()
        self.virtualDirName = (os.path.commonprefix(nameList))
        if self.virtualDirName == "":
            raise ValueError("No common directory for files in archive")
        self.nameSet = set()
        for name in nameList:
            if name == self.virtualDirName:
                continue
            if not name.startswith(self.virtualDirName+"/"):
                raise RuntimeError("internal error with common prefix",
                                   (name, self.virtualDirName))
            
            self.nameSet.add(name[len(self.virtualDirName+"/"):])

    def readFile(self, fileName):
        f = self.tarFile.extractfile(J(self.virtualDirName, fileName))
        result = f.read()
        f.close()
        return result

    def listdir(self, subDirName):
        # XXX: does not work for os.listDir("archive/subdir")
        #  if there are files "archive/subdir/subsubdir/aaa"
        if subDirName == "":
            subDirName = "."
        return sorted(pseudoListDir(subDirName, self.nameSet))

    def exists(self, fileName):
        return (fileName in self.nameSet)

    def isdir(self, fileName):
        return self.tarFile.getmember(J(self.virtualDirName,fileName)).isdir()

# XXX: no longer supported
class ZipFileManager:
    def __init__(self, archiveName):
        self.zipFile = zipfile.ZipFile(self.dirName+".zip", "r")
        self.nameList = set(self.zipFile.namelist())

    def readFile(self, fileName):
        f = self.zipFile.open(fullPath)
        result = f.read()
        f.close()
        return result

    def listdir(self, subDirName):
        return pseudoListDir


def getArchiveFileManager(dirName):
    TarSuffixList = [".tar.lzma", ".tar.lrz", ".tar"]    
    for suffix in TarSuffixList:
        if dirName.endswith(suffix):
            return TarFileManager(dirName), dirName[:-len(suffix)]
    for suffix in [".zip"]:
        if dirName.endswith(suffix):
            return ZipFileManager(dirName), dirName[:-len(suffix)]
    return None, dirName

# This implements either a file manager for a directory
# or a kind of minimal 'unionfs' of a read-only archive 
# with an overlay directory (for read and writes)

class FileManager:
    def __init__(self, dirName, autoDetectArchive = True):
        if autoDetectArchive:
            (self.archiveFileManager, self.dirName 
             ) = getArchiveFileManager(dirName)
        else: self.archiveFileManager, self.dirName = None, dirName
        self.linkTable = {}

    def updateLinkTableFrom(self, fileName):
        moreLinkTable = eval(self.readFile(fileName))
        self.linkTable.update(moreLinkTable)
    
    def writeFile(self, fileName, data):
        self.ensureDir()
        writeFile(J(self.dirName, fileName), data)

    def ensureDir(self):
        if not os.path.exists(self.dirName):
            os.mkdir(self.dirName)

    def readFile(self, fileName):
        if fileName in self.linkTable:
            fileName = self.linkTable[fileName]
        fullPath = J(self.dirName, fileName)
        if not os.path.exists(fullPath) and self.archiveFileManager != None:
            return self.archiveFileManager.readFile(fileName)
        return readFile(fullPath)

    def getPath(self, fileName):
        if fileName in self.linkTable:
            fileName = self.linkTable[fileName]
        return J(self.dirName, fileName)

    def exists(self, fileName):
        if fileName in self.linkTable:
            fileName = self.linkTable[fileName]
        fullPath = J(self.dirName, fileName)
        return (os.path.exists(fullPath) 
                or (self.archiveFileManager != None 
                    and self.archiveFileManager.exists(fileName)))

    def listdir(self, subDirName):
        # XXX: should raise an exception on absent dir
        if os.path.exists(J(self.dirName, subDirName)):
            result = os.listdir(J(self.dirName, subDirName))
        else: result = []
        if self.archiveFileManager != None:
            result += self.archiveFileManager.listdir(subDirName)
        return result

    #def isdir(self, fileName):
    #    # XXX: should raise an error on absent fileName
    #    if os.path.exists(J(self.dirName, fileName)):
    #        result = os.path.isdir(J(self.dirName, fileName))
    #    if self.archiveFileManager != None:
    #        return self.archiveFileManager.isdir(fileName)
    #    else: XXX

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


def ___finishMergeDirWithLink(fileManager, dirName, mergedExpMeta):
    fileManager.writeFile("meta.pydat", toRepr(mergedExpMeta))
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


def finishMergeDirWithVirtualLink(fileManager, dirName, mergedExpMeta):
    archiveFileManager = fileManager.archiveFileManager
    fileManager.writeFile("meta.pydat", toRepr(mergedExpMeta))
    realPathOf = { J(dirName, "meta.pydat"): "(generated)" }
    copiedSet = set()

    def copyFile(archiveFileName, fileName):
        print ("(copy: %s -> %s)" % (archiveFileName, fileName))
        copiedSet.add(fileName)
        content = archiveFileManager.readFile(archiveFileName)
        fileManager.writeFile(fileName, content)

    for fileName in archiveFileManager.listdir("."):
        if not archiveFileManager.isdir(fileName):
            copyFile(fileName, fileName)

    for subDirName in mergedExpMeta[MergedKeyPrefix+"subDirName"]:
        for fileName in archiveFileManager.listdir(subDirName):
            if os.path.basename(fileName) == "meta.pydat":
                continue
            linkOldPath = J(subDirName, fileName)
            oldPath = J(subDirName, fileName)
            newPath = fileName
            if newPath not in realPathOf:
                realPathOf[newPath] = oldPath
                syso("+")
            else:
                old = fileManager.readFile(oldPath)
                new = fileManager.readFile(realPathOf[newPath])
                syso(".")
                if old != new:
                    raise ValueError("inconsistent file content in merge", 
                                     (oldPath, realPathOf[newPath]))
                if fileName not in copiedSet:
                    copyFile(oldPath, fileName)
                
                
    del realPathOf[J(dirName, "meta.pydat")]
    fileManager.writeFile("virtual-link.pydat", toRepr(realPathOf))


def ___finishMergeDirWithZip(dirName, mergedExpMeta):
    zipName = dirName + ".zip"
    if os.path.exists(zipName):
        raise RuntimeError("archived file already exists", zipName)

    f = zipfile.ZipFile(zipName, "w", zipfile.ZIP_DEFLATED)
    for fileName in os.listdir(dirName):
        fullPath = J(dirName, fileName)
        if os.path.isfile(fullPath) and not os.path.islink(fullPath):
            f.write(fullPath)
            syso("+")

    f.writestr(J(dirName, "meta.pydat"), toRepr(mergedExpMeta))
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
                  raise ValueError("inconsistent file content in merge",                                     (oldPath, realPathOf[newPath]))
    f.close()

def attemptMergeDir(args, dirName):
    fileManager = FileManager(dirName)

    expMetaInfoList = []
    for subDirName in sorted(fileManager.listdir("")):
        metaFilePath = J(subDirName,"meta.pydat")
        if not fileManager.exists(metaFilePath):
            continue
        successFilePath = J(subDirName,"success.pydat")
        if not fileManager.exists(successFilePath):
            continue
        success = eval(fileManager.readFile(successFilePath))
        if not success:
            continue

        expMetaInfo = eval(fileManager.readFile(metaFilePath))
        expMetaInfo[MergedKeyPrefix+"subDirName"] = [subDirName]
        expMetaInfoList.append(expMetaInfo)

    mergedExpMeta = tryMergeMultipleExpMetaInfo(expMetaInfoList)
    if mergedExpMeta == None:
        return False
    assert "mergeInfo" not in mergedExpMeta # not necessary, but don't lose info
    mergedExpMeta["mergeInfo"] = sys.argv

    #finishMergeDirWithLink(fileManager, dirName, mergedExpMeta)
    #finishMergeDirWithZip(dirName, mergedExpMeta)
    finishMergeDirWithVirtualLink(fileManager, dirName, mergedExpMeta)

    if args.archive:
        raise RuntimeError("this is obsolete, compress with lrzip/lzma first")
        print ("archiving in tar")
        subprocess.check_call(["tar", "cf", dirName+".tar", dirName])
        shutil.rmtree(dirName)
        print ("compressing (lzma)")
        subprocess.check_call(["lzma", dirName+".tar"])
    return True

#attemptMergeDir("exp-2014-freq")
#attemptMergeDir("exp-2014-08-16-02h13m08")

#---------------------------------------------------------------------------

#  NOT!!!    (power, channel, sender, burst, receiver)
#       0      1        2       3      4

#AxisNameList = ["power", "channel", "sender", "burst", "receiver"]

#def getAxis(nameList):
#    assert set(nameList).issubset(set(AxisNameList))
#    return tuple(sorted([name.index(nameList) for name in nameList]))

#def getAxisWithout(nameList, noReceiver=False):
#    assert set(nameList).issubset(set(AxisNameList))
#    return tuple([i for i,name in enumerate(AxisNameList)
#                  if (name not in nameList
#                      and (name != "receiver" or not noReceiver))])

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

ErrorNameList = ( list(ReprOfSeqNumError.values())
 + ["bad-seq-num", "invalid-handle-irq", "outside-burst", "generic", "magic2"] )

class ExperimentParser(FileManager):

    def __init__(self, dirName):
        self.dirName = dirName
        FileManager.__init__(self, self.dirName)
        self.updateLinkTableFrom("virtual-link.pydat")
        self.generalInfo = eval(self.readFile("meta.pydat"))

    def parseOneBurst(self, fileName, idx):
        info = eval(self.readFile(fileName))
        expInfo = self.generalInfo
        nbNode = len(expInfo["idList"])
        nbPacket = expInfo["nbPacket"]

        # table for results
        recvArray = np.zeros((nbNode, nbPacket), np.uint8)
        lqiArray = np.zeros((nbNode, nbPacket), np.uint8)
        rssiArray = np.zeros((nbNode, nbPacket), np.int8)
        errorCountArrayTable = dict([ (errorName, np.zeros((nbNode,),np.int16))
                                      for errorName in ErrorNameList ])

        
        # check, just in case (normally empty)

        if len(info["unparsed"]) > 0:
            raise ValueError("unparsed information", info["unparsed"])

        # parse sender info


        rawSenderInfo = info["cmdXmit"][1][idx]

        if len(rawSenderInfo) != 2:
            #pprint.pprint(rawSenderInfo)
            #raise ValueError("too much sender info in cmdXmit", rawSenderInfo)
            warnings.warn("XXX: filtered out CCA/ED errors")
            rawSenderInfo = [
                x for x in rawSenderInfo
                if x[1].find("RF delay expired") < 0 ]
            #info["cmdXmit"][1][idx] = rawSenderInfo # XXX:hack back

        if len(rawSenderInfo) != 2:
            pprint.pprint(rawSenderInfo)
            raise ValueError("too much sender info in cmdXmit", rawSenderInfo)

        senderInfo = eval(rawSenderInfo[0][1])
        if senderInfo["nbPacket"] != expInfo["nbPacket"]:
            raise ValueError("inconsistent nb sent packets",
                             (senderInfo["nbPacket"], expInfo["nbPacket"]))
        if senderInfo["nbError"] != 0: # check no error found during exp. 
            warnings.warn("XXX: filtered out transmission errors")
            print("\ntransmission errors found: %s" %senderInfo["nbError"])
            #raise ValueError("transmission errors found",senderInfo["nbError"])

        edList = []
        for seqNum,(t1,t2,ed,success) in enumerate(senderInfo["send"]):
            if success != 1:
                warnings.warn("XXX: ignoring transmission errors")
                print ("transmission failure: %s %s %s" % (t1, t2, ed))
                #raise ValueError("transmission failed",
                #                 (senderInfo["send"],seqNum))
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

        for otherIdx, eventList in info["cmdXmit"][1].items():
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
        for otherIdx, eventList in info["cmdShow"][1].items():
            count = removeInvalidHandleIrq(eventList, "(#%s)" % (otherIdx)
                                           + "ignoring in 'show' ouput: [%s]")
            errorCountArrayTable["invalid-handle-irq"][otherIdx] += count
            if len(eventList) >= 2:
                raise ValueError("multiple output to cmd show", eventList)
        
        # parse receiver output

        notSeenSet = set(range(nbNode))

        for otherIdx, showStr in info["cmdShow"][0].items():
            assert otherIdx in notSeenSet
            notSeenSet.remove(otherIdx)
            if otherIdx == idx:
                continue
            recvInfo = eval(showStr)
            if recvInfo["nbChange"] >= 1:
                raise ValueError ("\nmultiple changes of xmitId", recvInfo)
            errorCountArrayTable["outside-burst"][otherIdx] += \
                recvInfo["nbLockedError"]
            errorCountArrayTable["generic"][otherIdx] += recvInfo["nbError"]
            errorCountArrayTable["magic2"][otherIdx] += recvInfo["nbMagicError"]
                        
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


                if seqNum >= SeqNumOffsetError:
                    # New-style errors
                    assert seqNum in ReprOfSeqNumError
                    errorType = ReprOfSeqNumError[seqNum]
                    errorLogTable[errorType].append(lastSeqNum)
                    # NOTE: information about timing is not copied

                else: 
                    # Well received packet
                    if (not (0 <= seqNum < nbPacket) 
                        or recvArray[otherIdx][seqNum]!=0
                        or (lastSeqNum != None and seqNum <= lastSeqNum)):
                        print ("ignoring inconsistent seqNum",
                               (lastSeqNum, seqNum, nbPacket))
                        pprint.pprint(recvInfo)
                        errorLogTable["bad-seq-num"].append(seqNum)
                        #raise ValueError("invalid packetIdx", i)

                    else:
                        lastSeqNum = seqNum
                        recvArray[otherIdx][i] = 1
                        lqiArray[otherIdx][i] = lqi
                        rssiArray[otherIdx][i] = rssi

            for errorName in ErrorNameList:
                if errorName in ["invalid-handle-irq", "generic",
                                 "magic2", "outside-burst"]:
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

        return ({ "ed":np.array(edList, np.int16),
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

        fullTable = { "recv": np.zeros(dimRecv,np.uint8),
                      "lqi": np.zeros(dimRecv,np.uint8),
                      "rssi": np.zeros(dimRecv,np.int8),
                      "ed": np.zeros(dimSend,np.int16) }
        
        resultTable = {}
        for powerIdx,power in enumerate(powerList):
            for channelIdx,channel in enumerate(channelList):
                for idx in idxList:
                    fileName = ("exp-i%s-p%s-c%s.pydat" % (idx, power, channel))
                    if self.exists(fileName):
                        (oneTable, oneErrorCountTable 
                         ) = self.parseOneBurst(fileName, idx)
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

# structurally, this is a mess:

class ExperimentAnalysis(FileManager):

    def __init__(self, dirName):
        self.dirName = dirName
        FileManager.__init__(self, self.dirName, False)

        self.generalInfo = eval(self.readFile("meta.pydat"))
        self.nbNode = len(self.generalInfo["idList"])
        self.nbPacket = self.generalInfo["nbPacket"]
        self.channelList = self.generalInfo["channelList"]
        self.powerList = self.generalInfo["powerList"]
        self.stat = np.load(self.getPath("stat.npz"))
        self.error =  np.load(self.getPath("error.npz"))
        self.nodePosTable = self._readNodePos()
        self._cache = {}

    def getNodePosTable(self):
        return self.nodePosTable

    def getCached(self, name):
        if name in self._cache:
            return self._cache[name]
        if name in self.stat:
            self._cache[name] = self.stat[name].copy()
            return self._cache[name]
        if name in self.error:
            self._cache[name] = self.error[name].copy()
            return self._cache[name]
        raise ValueError("Unknown data name", name)

    def _readNodePos(self): 
        resourceList = eval(self.readFile("resources.pydat"))["items"]

        infoOfAddress = {}
        for info in resourceList:
            infoOfAddress[info["network_address"]] = info

        posTable = {}
        for i,nodeInfo in enumerate(self.generalInfo["nodeList"]):
            moreInfo =  infoOfAddress.get(nodeInfo[0])
            posTable[i] = tuple([float(moreInfo[u]) for u in ["x","y","z"]])

        return posTable

    def getIdxClosest(self, x,y,z=None):
        dAndI = [ ((x-xx)**2 + (y-yy)**2 + (0 if z==None else (z-zz))**2, i)
                  for i,(xx,yy,zz) in enumerate(self.nodePosTable.values())]
        dAndI.sort()
        return dAndI[0][1], math.sqrt(dAndI[0][0])

    #--------------------------------------------------
    # commands
    #--------------------------------------------------

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
        statRecv = self.getCached("recv")
        statEd = self.getCached("ed")
        totalSentPacket = statEd.size
        print ("Total packets sent: %s" % totalSentPacket)
        totalRecvPacket = statRecv.sum()
        print ("Total packets received: %s (avg=%s per sent packet)" 
               % (totalRecvPacket, totalRecvPacket/totalSentPacket))


        print ("--- Detailed base stats :")
        for ip,power in enumerate(self.powerList):
            for ic,channel in enumerate(self.channelList):

                # compute quick stats
                linkRecv = statRecv[ip][ic].sum(2, dtype=np.uint32) 
                flatLinkRecv = linkRecv.flatten()
                linkCountAll = (flatLinkRecv == self.nbPacket).sum()
                linkCountSome = ((flatLinkRecv < self.nbPacket) 
                                 & (flatLinkRecv > 0)).sum()
                lossyProp = linkCountSome / (linkCountSome+linkCountAll)

                s = ""
                s += "%s dBm " % power
                s += "ch%s " % channel
                partStatRecv = statRecv[ip,ic]
                print (s+"- rcv:", int(partStatRecv.sum()), end=" - ")
                print ("avg ed=%.04f" % statEd[ip,ic].mean(), end=" - ")
                print ("magic=% 5d"%self.error["magic"][ip,ic].sum(), end=" - ")
                #print ("radio-crc=%s" % self.error["radio-crc"][ip,ic].sum())
                print ("lossy-link=%.3f %%" % (lossyProp*100))

    def getMaskedData(self, name):
        assert name in ["rssi", "lqi"]
        recvArray = self.getCached("recv")
        dataRawArray = self.getCached(name)
        dataArray = np.ma.masked_array(dataRawArray,
                                       mask=np.logical_not(recvArray))
        return dataArray


    #--------------------------------------------------

    def getRssi(self):
        # linkRecv[(channel, sender, receiver)] -> number of received pkt
        recv = expStat["recv"]
        linkRecv = recv[0].sum(3, dtype=np.uint32) 
        linkRssiAvg = np.ma.masked_array(
            expStat["rssi"], mask=(recv == 0))[0].mean(3)
        linkLqiAvg = np.ma.masked_array(
            expStat["lqi"], mask=(recv == 0))[0].mean(3)
        
        
    #--------------------------------------------------

    def plotLqiPsr(self):
        name = "lqi"
        recv = self.getCached("recv")
        data = self.getMaskedData(name)

        #      (power, channel, sender, receiver, packetIdx)
        #       0      1        2       3         4     
        assert (recv.shape[-1] == self.nbPacket)
        assert (recv.shape == data.shape)

        burstRecv = recv.sum(axis=4)
        successRate = recv.mean(axis=4)
        dataMean = data.mean(axis=4)
        dataMax = data.max(axis=4)

        ok = (burstRecv > 0)
        successRate = successRate[ok].flatten()
        dataMean = dataMean[ok].flatten()
        dataMax = dataMax[ok].flatten()
        plt.plot(successRate[0:], dataMean[0:],".")
        plt.show()
        
        #dataMean = data.max(axis=4) # XXXX
        assert successRate.shape == dataMean.shape



        ## aaaaaargh - the data keeps being rotated!!!
        heatmap, xLim, yLim = np.histogram2d(
            successRate.flatten(),  dataMean.flatten(), bins=30)
        #print (xLim, yLim)
        #rectangle = [xLim[0],xLim[-1],yLim[0],yLim[-1]]
        #print (rectangle)
        #plt.clf()
        #plt.imshow(heatmap, extent=rectangle, aspect="auto",
        #           #cmap=matplotlib.cm.hot,
        #           norm = matplotlib.colors.LogNorm(clip=True)
        #           #origin="lower"
        #           )
        #plt.colorbar()
        #plt.show()
        

        import pylab
        from pylab import hist2d, show
        hist2d(successRate.flatten(), dataMean.flatten(), bins=50,
               norm=matplotlib.colors.LogNorm())
        pylab.colorbar()
        show()

        hist2d(successRate.flatten(), dataMax.flatten(), bins=50,
               norm=matplotlib.colors.LogNorm())
        pylab.colorbar()
        show()

        
        plt.clf()

        if True:
            from mayavi import mlab
            zz = np.log(heatmap)
            zz[np.isinf(zz)] = 0
            mlab.surf(zz)
            mlab.show()


        data_array = np.log(heatmap)

        #=== begin part copied from:
        # http://stackoverflow.com/questions/14061061/how-can-i-render-3d-histograms-in-python
        #
        # Create a figure for plotting the data as a 3D histogram.
        #
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        #

        x_data, y_data = np.meshgrid( np.arange(data_array.shape[1]),
                                      np.arange(data_array.shape[0]) )
        #
        # Flatten out the arrays so that they may be passed to "ax.bar3d".
        # Basically, ax.bar3d expects three one-dimensional arrays:
        # x_data, y_data, z_data. The following call boils down to picking
        # one entry from each array and plotting a bar to from
        # (x_data[i], y_data[i], 0) to (x_data[i], y_data[i], z_data[i]).
        #
        x_data = x_data.flatten()
        y_data = y_data.flatten()
        z_data = data_array.flatten()
        #ax.zaxis.set_scale('log')        
        ax.bar3d( x_data,
                  y_data,
                  np.zeros(len(z_data)),
                  1, 1, z_data )
        plt.show()
        #=== end part copied

        hist, xedges, yedges = np.log(heatmap), xLim, yLim
        #=== begin part copied from:
        # http://matplotlib.org/examples/mplot3d/hist3d_demo.html
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        # [...snip...]
        elements = (len(xedges) - 1) * (len(yedges) - 1)
        xpos, ypos = np.meshgrid(xedges[:-1]+0.25, yedges[:-1]+0.25)
        
        xpos = xpos.flatten()
        ypos = ypos.flatten()
        zpos = np.zeros(elements)
        dx = 0.5 * np.ones_like(zpos)
        dy = dx.copy()
        dz = hist.flatten()

        #ax.zaxis.set_scale('log')        
        ax.bar3d(xpos, ypos, zpos, dx, dy, dz, color='b', zsort='average')

        plt.show()
        #=== end part copied


        #for ip,power in enumerate(self.powerList):
        #    for ic,channel in enumerate(self.channelList):
        #        for sendIdx in range(self.nbNode):
        #            for recvIdx in range(self.nbNode):
        #                data = (dataArray[ip,ic,sendIdx,recvIdx].mean())
        #                psr =recvArray[ip,ic,sendIdx,recvIdx].mean()
        #                if data is not np.ma.masked:
        #                    print (data,psr)
                   

    #--------------------------------------------------
    #
    #--------------------------------------------------

    def getStatData(self, powerIdx, channelIdx, refIdx, name, 
                    shouldSumError=False):
        #stat:  (len(powerList), len(channelList), nbNode, nbNode, nbPacket)
        #error: (len(powerList), len(channelList), nbNode, nbNode)
        #send:  (len(powerList), len(channelList), nbNode, nbPacket)

        if name == "lqi" or name == "rssi":
            recvArray = self.getCached("recv")
            dataRawArray = self.getCached(name)
            dataArray = np.ma.masked_array(dataRawArray, 
                                          mask=np.logical_not(recvArray))
            data = (dataArray[powerIdx,channelIdx,refIdx].mean(axis=1))

        elif name == "recv":
            recvArray = self.getCached("recv")
            data = recvArray[powerIdx,channelIdx,refIdx]
            data = data.sum(axis=1) / self.nbPacket

        elif name == "ed":
            # average energy of sender node idx
            data = self.getCached("ed")
            data = data[powerIdx, channelIdx].mean(axis=1)

        elif name in ErrorNameList:
            data = self.getCached(name)
            #print (data[powerIdx, channelIdx,refIdx])
            if shouldSumError:
                data = data[powerIdx, channelIdx].sum(axis=0)
            else: data = data[powerIdx, channelIdx,refIdx]

        return data


    def getEdOnChannel(self, channel):
        #dimRecv = (len(powerList), len(channelList), nbNode, nbNode, nbPacket)
        #dimStatRecv = (len(powerList), len(channelList), nbNode, nbNode)
        #dimSend = (len(powerList), len(channelList), nbNode, nbPacket)

        powerIdx = 0
        #channelIdx = 22-11
        channelIdx = 11-11
        refIdx = 100

        mode = "ed"

        if mode == "lqi":

            recvArray = self.stat["recv"]
            lqiArray = np.ma.masked_array(self.stat["lqi"], 
                                          mask=np.logical_not(recvArray))
            data = (lqiArray[powerIdx,channelIdx,refIdx].mean(axis=1))
        elif mode == "recv":
            data = self.stat["recv"][powerIdx,channelIdx,refIdx]
            data = data.sum(axis=1) / self.nbPacket

        elif mode == "ed":
            #data = self.stat["ed"][powerIdx, channelIdx].mean(axis=1)
            data = self.stat["ed"][powerIdx, channelIdx].max(axis=1)

        elif mode in ErrorNameList:
            data = self.error[mode][powerIdx, channelIdx].sum(axis=0)

        minData = data.min()
        maxData = data.max()
        print (minData)
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        for i,(x,y,z) in self.nodePosTable.items():
            if data[i] is np.ma.masked or data[i] <= minData *1.0001:
                zs = [minData - (maxData-minData)*0.01, minData]
                #continue
            else: zs = [minData, data[i]]
            ax.plot([x,x], [y,y], zs)
        plt.show()

        e

        axis = getAxisWithout(["channel", "sender"], noReceiver=True)
        print (axis)
        statEd = self.stat["ed"]
        statEd = self.error["radio-crc"]
        statEd = self.error["magic"]
        statEd = self.stat["recv"][:,:,:,:,0]
        avgEd = (statEd.mean(axis=axis))
        #avgEd = (statEd.max(axis=axis))

        idx = 22-11
        idx = 11-11

        minAvgEd = avgEd.min()
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        for i,(x,y,z) in self.nodePosTable.items():
            ax.plot([x,x], [y,y], [minAvgEd, avgEd[idx][i]])
        plt.show()
            
        plt.plot(avgEd[22-11])
        plt.plot(avgEd[11-11])
        plt.show()
        

    def plotPos(self):
        posTable = self.nodePosTable
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
#---------------------------------------------------------------------------
# GUI
#---------------------------------------------------------------------------

# http://matplotlib.org/examples/user_interfaces/embedding_in_tk.html
# http://stackoverflow.com/questions/4073660/python-tkinter-embed-matplotlib-in-gui

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

try: from Tkinter import *
except: from tkinter import * # assume python 3
#--------------------------------------------------

ModeList = ["rssi", "recv", "lqi", "ed"] + ErrorNameList

class ExperimentFrame(Frame):
    def __init__(self, app, parentFrame, dirName, isFirst):
        Frame.__init__(self, parentFrame)
        self.pack({"side":"left"})

        self.app = app
        self.parentFrame = parentFrame
        self.dirName = dirName
        self.exp = ExperimentAnalysis(dirName) # serves as a "model"
        self.param = {
            "expIdx":0, 
            "powerIdx":0, 
            "channelIdx":0, 
            "nodeIdx":0, 
            "withNodeIdx":0,
            "modeIdx":0
            }
        self.otherParam = {}
        if not isFirst:
            for name in self.param:
                #if name != "withNodeIdx":
                self.param[name] = None

        self.createErrorSumFrame()
        self.paramFrameTable = {}
        for (name, idxName, valueList) in [
            #("exp", "expIdx", )
            ("power", "powerIdx", self.exp.powerList),
            ("channel", "channelIdx", self.exp.channelList),
            ("mode", "modeIdx", ModeList),
            ("node", "withNodeIdx", ["(here)"])
            ]:
            self.createParamFrame(name, idxName, valueList)
        self.createFigure()
        
    def createErrorSumFrame(self):
        self.varShouldSumError = IntVar()
        frame = Frame(self, relief="groove",border=3)
        frame.pack()
        self.buttonShouldSumError = Checkbutton(
            frame, text="sum error", variable=self.varShouldSumError, 
            onvalue=True, offvalue=False)
        self.buttonShouldSumError.select()
        self.buttonShouldSumError.pack()
        print 

    def createParamFrame(self, name, nameIdx, valueList):
        pos = [0,0][:]
        def getPos():
            result = tuple(pos[:])
            pos[0] += 1
            if pos[0] >= 9 or (name == "mode" and pos[0] >=4):
                pos[0] = 0
                pos[1] += 1
            return {"row":result[1], "column":result[0]}

        frame = Frame(self, relief="groove",border=3)
        label = Label(frame, text=name, relief="raised")
        label.grid(getPos())
        def makeParamCallback(name, nameIdx, value):
            def func():
                self.param[nameIdx] = value
                self.setParam(nameIdx, value)
            return func

        indexVar = IntVar()
        if self.param.get(nameIdx) == None:
            indexVar.set(-1)
        buttonOther = Radiobutton(
            frame, text="(other)", variable=indexVar, value = -1,
            command=makeParamCallback(name, nameIdx, None))
        buttonOther.grid(getPos())
        self.paramFrameTable[name] = {
            "frame": frame,
            "label": label,
            "indexVar": indexVar,
            "<other>": buttonOther
            }
        for i,value in enumerate(valueList):
            text = "%s" % value
            button = Radiobutton(
                frame, text=text, variable=indexVar, value = i,
                command = makeParamCallback(name, nameIdx, i))
            button.grid(getPos())
        frame.pack()


    def createFigure(self):
        self.frameNode = Frame(self)
        self.figureNode = Figure(figsize=(5,2.5), dpi=100)
        self.canvasNode = FigureCanvasTkAgg(
            self.figureNode, master=self.frameNode)
        self.canvasNode.draw()
        self.axeNode = self.figureNode.add_subplot(111)
        self.axeNode.set_aspect("equal")
        self.axeNode.grid()
        self._drawNode()
        self._drawSelectedNode()
        self.canvasNode.get_tk_widget().pack({"side":"bottom"})

        self.frameResult = Frame(self)
        self.figure = Figure(figsize=(5,4), dpi=100)
        # canvas before axe: http://www.mail-archive.com/matplotlib-users@lists.sourceforge.net/msg15322.html
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.frameResult)
        self.canvas.draw()
        self.axe = self.figure.add_subplot(111, projection="3d")
        self._redraw()
        self.canvas.get_tk_widget().pack({"side":"bottom"})

        self.frameResult.pack({"side":"bottom"})
        self.frameNode.pack({"side":"bottom"})

    def getParamIdx(self, name):
        result = self.param[name]
        if result == None:
            result = self.otherParam.get(name, None)
        if result == None:
            result = 0
        return result

    def _redraw(self):
        self.axe.cla()
        powerIdx = 0
        channelIdx = 0
        nodeIdx = 0
        mode = ModeList[self.getParamIdx("modeIdx")]
        if self.param["withNodeIdx"] == 0:
            nodeIdx = self.param["nodeIdx"]
        else: nodeIdx = self.otherParam.get("nodeIdx", 0)
        #print ("REDRAW", self.param, mode, nodeIdx)
        #print (            self.getParamIdx("powerIdx"), 
        #    self.getParamIdx("channelIdx"), 
        #    nodeIdx, 
        #    mode)
        shouldSum = self.varShouldSumError.get()
        #print ("shouldSum:", shouldSum)
        data = self.exp.getStatData(
            self.getParamIdx("powerIdx"), 
            self.getParamIdx("channelIdx"), 
            nodeIdx, 
            mode,
            shouldSum)

        minData = data.min()
        maxData = data.max()
        for i,(x,y,z) in self.exp.getNodePosTable().items():
            if data[i] is np.ma.masked or data[i] <= minData *1.0001:
                zs = [minData - (maxData-minData)*0.01, minData]
                #continue
            else: zs = [minData, data[i]]
            self.axe.plot([x,x], [y,y], zs)

        self.canvas.draw()

    def _drawSelectedNode(self):
        nodeIdx = 0
        mode = ModeList[self.getParamIdx("modeIdx")]
        if self.param["withNodeIdx"] == 0:
            nodeIdx = self.param["nodeIdx"]
        else: nodeIdx = self.otherParam.get("nodeIdx", 0)
        print ("selected: nodeIdx=%s" % nodeIdx)
        nodePosTable = self.exp.getNodePosTable()
        (x,y,z) = nodePosTable[nodeIdx]
        # http://matplotlib.1069221.n5.nabble.com/change-a-matplotlib-lines-Line2D-and-update-the-plot-td21806.html
        if self.selectedNodeLine2D == None:
            self.selectedNodeLine2D = self.axeNode.plot([x],[y], "o")
        else: self.selectedNodeLine2D[0].set_data([x],[y])
        self.canvasNode.draw()

    def _drawNode(self):
        xList = []
        yList = []
        for x,y,z in self.exp.getNodePosTable().values():
            xList.append(x)
            yList.append(y)
        self.axeNode.plot(xList,yList,".k")
        cid = self.figureNode.canvas.mpl_connect(
            "button_release_event", self.eventClick)
        self.selectedNodeLine2D = None

    def eventClick(self, event):
        if event.inaxes == None:
            return
        #print (event)
        nodeIdx, distance = (self.exp.getIdxClosest(event.xdata,event.ydata))
        self.setParam("nodeIdx", nodeIdx)
        return

    def setParam(self, paramName, value):
        self.param[paramName] = value
        if paramName == "nodeIdx":
            self._drawSelectedNode()
        self._redraw()
        self.app.eventSetParam(self, paramName, value)

    def eventOtherSetParam(self, paramName, value):
        #assert value != None
        print (self.param)
        self.otherParam[paramName] = value
        if (self.param[paramName] == None 
            or (paramName == "nodeIdx"
                and self.param["withNodeIdx"] == None)):
            self._redraw()


class ExperimentApplication(Frame):

    def __init__(self, args, master=None):
        self.args = args
        Frame.__init__(self, master)
        self.pack()

        self.expFrameList = []
        for i,dirName in enumerate(args.dirNameList):
            expFrame = ExperimentFrame(self, self, dirName, i==0)
            self.expFrameList.append(expFrame)

    def eventSetParam(self, expFrame, paramName, value):
        for otherExpFrame in self.expFrameList:
            if otherExpFrame is not expFrame:
                otherExpFrame.eventOtherSetParam(paramName, value)

#--------------------------------------------------

def runGui(args):
    root = Tk()
    root.title("Radio Experience")
    app = ExperimentApplication(args, root)
    app.mainloop()
    #root.destroy()
    sys.exit(0)

#---------------------------------------------------------------------------

# XXX:remove
#PowerList = [
#    "-17", "-12", "-9", "-7", "-5", "-4", "-3", "-2", "-1",
#    "0", "0.7", "1.3", "1.8", "2.3", "2.8", "3"]
#powerList = PowerList

def runAsCommand():
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

    testParser = subparsers.add_parser("test")
    testParser.add_argument("dirName", type=str)

    guiParser = subparsers.add_parser("gui")
    guiParser.add_argument("dirNameList", nargs='+', type=str)

    lqiPsrParser = subparsers.add_parser("plot-lqi-psr")
    lqiPsrParser.add_argument("dirName", type=str)

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
        success = attemptMergeDir(args, args.dirName)
        if not success:
            print ("Error: Could not merge sub-directories of '%s'" 
                   % args.dirName)
            sys.exit(1)
        else:
            print ("(merged successfully)")

    elif args.command == "summary":
        analysis = ExperimentAnalysis(args.dirName)
        analysis.summary()

    elif args.command == "test":
        analysis = ExperimentAnalysis(args.dirName)
        analysis.getEdOnChannel(22)

    elif args.command == "pos":
        #analysis = ExperimentAnalysis(args.dirName)
        #analysis.plotPos()
        model = ExperimentModel(args.dirNameList)
        gui = ExperimentControllerView(model)

    elif args.command == "plot-lqi-psr":
        analysis = ExperimentAnalysis(args.dirName)
        analysis.plotLqiPsr()

    elif args.command == "gui":
        runGui(args)

#--------------------------------------------------

if __name__ == "__main__":
    runAsCommand()

#---------------------------------------------------------------------------
