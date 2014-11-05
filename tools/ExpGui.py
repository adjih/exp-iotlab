#---------------------------------------------------------------------------
# 
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

#---------------------------------------------------------------------------
# [Jul2014] 
#    Parts copied from GETRF-color/code/ColoringStat.py
#  and also,
#    parts copied from Nc/src/drawFlowAnim.py, itself with parts from:
# [Aug2007] Parts copied from OOLSR/simul/simulDisplay.py
#---------------------------------------------------------------------------

from __future__ import division
import time, json, sys, argparse, pprint
import IotlabHelper
from IotlabHelper import extractNodeId, fromJson, toJson
import Foren6Helper

import pygame
import pygame.gfxdraw
from pygame.locals import *

import os
#os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (1*1920,0)
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0,0)

DisplayHack = True

#---------------------------------------------------------------------------

def findClosest(screenPosList, xy):
    distList = [ (((uv[0]-xy[0])**2 + (uv[1]-xy[1])**2), uv[2])
                 for uv in screenPosList]
    distList.sort()
    return distList[0][-1]

#---------------------------------------------------------------------------

class ExpModel:
    def __init__(self, iotlab, exp):
        self.iotlab = iotlab
        self.exp = exp
        self.view = None
        self.updateInfo()
        self.groupManager = IotlabHelper.GroupManager()

    def setView(self, view):
        self.view = view

    def reloadInfo(self):
        # XXX: why need this?
        #iotlab, exp = getHelperAndExp(args)
        self.iotlab = IotlabHelper.IotlabHelper(self.iotlab.expServer)
        self.exp = self.iotlab._makeExp(self.exp.expId)
        #exp = iotlab._makeExp(args.exp_id)
        self.updateInfo()


    def updateInfo(self):

        CacheNodeList = "cache-node-list.json"
        CacheResource = "cache-resource-server.json" # XXX: move 

        if self.exp.hasFile(CacheNodeList):
            self.expNodeList = fromJson(self.exp.readFile(CacheNodeList))
        else:
            self.expNodeList = self.exp.getNodeList()
            self.exp.writeFile(CacheNodeList, toJson(self.expNodeList))

        self.expServer = IotlabHelper.getExpUniqueServer(
            self.exp, self.expNodeList)
        self.expServer = self.expServer.split(".")[0]

        if self.exp.hasFile(CacheResource):
            self.serverInfo = fromJson(self.exp.readFile(CacheResource))
        else:
            self.serverInfo = self.iotlab.getResources(self.expServer)
            self.exp.writeFile(CacheResource, toJson(self.serverInfo))

        siteInfo = self.serverInfo

        archi = "m3:at86rf231"
        nodePosList = [(extractNodeId(info["network_address"]), 
                        (float(info["x"]), float(info["y"]), float(info["z"])))
                       for info in siteInfo
                       if info["archi"] == archi 
                       and "null" not in (info["network_address"],
                                          info["x"], info["y"], info["z"])
                       and info["state"] in ("Alive", "Busy")]

        if DisplayHack:
            nodePosList = [(extractNodeId(info["network_address"]), 
                            (-float(info["y"]), float(info["x"]), float(info["z"])))
                           for info in siteInfo
                           if info["archi"] == archi 
                           and "null" not in (info["network_address"],
                                              info["x"], info["y"], info["z"])
                           and info["state"] in ("Alive", "Busy")]


        expInfo = self.exp.getPersistentInfo()
        nodeInfoByType = expInfo["nodeInfoByType"]
        #print nodeInfoByType.get("contiki-rpl-node")

        self.posOfNode = dict(nodePosList)
        nodeOfType = {}
        rplNodes = set()
        for typeName, info in nodeInfoByType.iteritems():
            nodeOfType[typeName] = [ extractNodeId(node)
                                     for node in info["nodes"] ]
            if typeName in ["border-router", "contiki-rpl-node"]:
                rplNodes = rplNodes.union(set(nodeOfType[typeName]))

        #print posOfNode
        xPosList = [x for x,y,z in self.posOfNode.itervalues()]
        yPosList = [y for x,y,z in self.posOfNode.itervalues()]

        self.xPosMin, self.xPosMax = min(xPosList), max(xPosList)
        self.yPosMin, self.yPosMax = min(yPosList), max(yPosList)
        self.nodeOfType = nodeOfType
        #print xPosMin, xPosMax, yPosMin, yPosMax

        self.nodeInfo = {}
        layoutInfoList = []
        nodeInfoFileName = "grenoble-node.txt"
        if os.path.exists(nodeInfoFileName):  #XXX!! big hack
            f = open(nodeInfoFileName)
            for line in f.readlines():
                line = line.strip()
                if len(line) == 0:
                    continue
                tokens = [x for x in line.split(" ") if x != ""]
                addressParts = tokens[0].split(":")
                nodeId = extractNodeId(tokens[1])
                address = "aaaa::200:0:0:" + addressParts[4]
                host = tokens[2]
                self.nodeInfo[nodeId] = (address, host)
                if nodeId not in rplNodes:
                    continue
                # XXX!! another hack
                if nodeId not in self.posOfNode:
                    print "(cannot find node %s)" % nodeId
                    continue
                x,y,z = self.posOfNode[nodeId]
                if DisplayHack and x > 21.85:
                    continue
                sx,sy = 4.5, 3.0
                ox,oy = -60,-30
                layoutInfo = { "x": (x-self.xPosMin)*sx +ox, 
                               "y": (y-self.yPosMin)*sy +oy, 
                               "id": addressParts[4],
                               "name": "n%s" %nodeId }
                layoutInfoList.append(layoutInfo)
        
        # Another hack
        layoutStr = Foren6Helper.genLayoutFile(layoutInfoList, scale=5.0)
        IotlabHelper.writeFile("sample.ini", layoutStr)


    def getNodeList(self):
        return [extractNodeId(address) for address in self.expNodeList]

    def getNodeListOfType(self, typeName):
        expInfo = self.exp.getPersistentInfo()
        nodeInfoByType = expInfo["nodeInfoByType"]
        if typeName not in nodeInfoByType:
            return []
        else:
            result = nodeInfoByType[typeName]["nodes"]
            return [extractNodeId(node) for node in result]

    def getGroupList(self): return self.groupManager.getGroupList()

    def getNodeInfo(self, nodeId):
        return self.nodeInfo.get(nodeId, ("",""))

#---------------------------------------------------------------------------


class ExpViewController:
    
    def __init__(self, xSize, ySize, model, **optionTable):
        self.margin = 10
        self.clock = pygame.time.Clock()
        pygame.init()
        self.xSize = xSize
        self.ySize = ySize
        self.screen = pygame.display.set_mode((self.xSize, self.ySize),
            pygame.RESIZABLE)
        pygame.display.set_caption("FIT IoT-LAB")
        self.clear()
        
        fontSize = 24
        self.font = pygame.font.Font(None, fontSize)
        #text = font.render("Alarm", True, (100, 100, 100))
        self.optionTable = optionTable

        self.model = model
        self.selectedNodeList = []
        self.mode = "view"
        self.yInfoSize = 60
        self.currentType = None
        self.currentGroup = None
        self.currentNodeInfo = None
        self.lastNodeId = None

    def show(self):
        self.loop()

    def setPixel(self, u, color):
        self.screen.set_at(u, color)

    def drawLine(self, u, v, color):
        pygame.draw.line(self.screen, color, u, v)

    def drawCircle(self, x, y, r, color):
        #pygame.draw.circle(self.screen, selectedColor, 
        #                   (int(xx), int(yy)), int(nodeSize/1.5), 0)
        #pygame.draw.circle(self.screen, color, (int(x), int(y)), r, 0)
        pygame.gfxdraw.aacircle(self.screen, int(x), int(y), int(r), color)
        pygame.gfxdraw.filled_circle(self.screen, int(x), int(y), int(r), color)
 

    def clear(self):
        win = (0,0,self.xSize,self.ySize)
        ColorWhite = (255,255,255)
        pygame.draw.rect(self.screen, ColorWhite, win)

    def posToScreen(self, x,y):
        xRel = (x-self.xPosMin) / (self.xPosMax-self.xPosMin)
        yRel = (y-self.yPosMin) / (self.yPosMax-self.yPosMin)
        x = self.margin + xRel * (self.xSize - 2*self.margin)
        y = self.margin + yRel * (self.ySize - self.yInfoSize- 2*self.margin)
        return x,y

    def updateCurrentType(self, delta):
        typeList = IotlabHelper.TypeToFirmware.keys()
        if self.currentType == None or not self.currentType in typeList:
            self.currentType = typeList[0]
        typeIdx = typeList.index(self.currentType)
        newTypeIdx = (typeIdx+delta) % len(typeList)
        assert 0 <= newTypeIdx < len(typeList)
        self.currentType = typeList[newTypeIdx]

    def setCurrentType(self, name):
        typeList = IotlabHelper.TypeToFirmware.keys()
        if name not in typeList:
            print ("<cannot find type %s>" % name)
        newTypeIdx = typeList.index(name)
        assert 0 <= newTypeIdx < len(typeList)
        self.currentType = typeList[newTypeIdx]

    def updateCurrentGroup(self, delta):
        groupList = self.model.getGroupList()
        if len(groupList) == 0:
            self.currentGroup = None
            return
        if self.currentGroup == None or not self.currentGroup in groupList:
            self.currentGroup = groupList[0]
        groupIdx = groupList.index(self.currentGroup)
        newGroupIdx = (groupIdx+delta) % len(groupList)
        assert 0 <= newGroupIdx < len(groupList)
        self.currentGroup = groupList[newGroupIdx]

    def setCurrentGroup(self, name):
        groupList = self.model.getGroupList()
        if name not in groupList:
            print ("<cannot find group %s>" % name)
            self.currentGroup = None
            return
        self.currentGroup = name
        newGroupIdx = groupList.index(self.currentGroup)
        assert 0 <= newGroupIdx < len(groupList)
        self.currentGroup = groupList[newGroupIdx]
        self.selectGroup()
        
    def newGroup(self):
        groupList = self.model.getGroupList()
        idx = 0
        while "%s"%idx in groupList:
            idx += 1
        self.model.groupManager.writeGroup("%s"%idx, self.selectedNodeList)
        self.currentGroup = "%s" % idx
        print "<new group %s>" % self.currentGroup
        self.model.updateInfo()

    def deleteGroup(self):
        if self.currentGroup == None:
            print "<no group>"
            return
        groupList = self.model.groupManager.deleteGroup(self.currentGroup)
        self.currentGroup = None


    def flashSelectedNodes(self):
        if self.currentType == None: 
            return
        opt = " --type %s " % self.currentType
        if len(self.selectedNodeList) == 0:
            return
        cmd = ("./expctl flash "
               + opt
               + " "+ " ".join(
                ["m3-%s" % x for x in self.selectedNodeList])) # XXX: not only m3
        print "+", cmd
        os.system(cmd)
        self.model.reloadInfo()
        #return self.cmdSelectedNodes("flash", opt)

    def cmdSelectedNodes(self, cmd, opt=""):
        if len(self.selectedNodeList) == 0:
            return
        cmd = ("./expctl %s-node " % cmd
               + opt
               + " "+ " ".join(
                ["m3-%s.grenoble.iot-lab.info" % x for x in self.selectedNodeList])) # XXX: not only m3 XXX!!! not onyl grenoble
        print "+", cmd
        os.system(cmd)
        self.model.updateInfo()

    def cmdPingLastNode(self, interval = 1):
        if self.lastNodeId == None or self.currentNodeInfo == None:
            print "<no last node>"
            return
        title1 = "ping6 [%s]" % self.currentNodeInfo
        address = [x for x in self.currentNodeInfo.split(" ") if x != ""][1] # XXX!!!!
        title2 = "Node %s" % self.lastNodeId
        cmd = "sudo ping6 -O -i %s -s1 %s" % (interval, address)
        os.system("roxterm --fork -T '%s' -n '%s' -e bash -c '%s ; sleep 10'"
                  % (title1, title2, cmd))

    def selectGroup(self):
        if self.currentGroup == None:
            print "<no group>"
            return
        self.selectedNodeList = self.model.groupManager.readGroup(
            self.currentGroup)
        nodeSet = set(self.model.getNodeList())
        self.selectedNodeList = [nodeId 
                                 for nodeId in self.selectedNodeList
                                 if nodeId in nodeSet]


    def loop(self):
        self.isFinished = False
        while not self.isFinished:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.isFinished = True
                elif event.type == pygame.KEYDOWN:
                    #print event, event.pygame.K_0
                    if event.key == pygame.K_q:
                        self.isFinished = True
                    elif event.key == pygame.K_c:
                        self.clearSelected()
                    elif (#event.key == pygame.K_p or 
                          event.unicode == u'+'): 
                        self.updateCurrentType(+1)
                    elif ( (event.unicode == u'-' and event.scancode != 15)
                          or event.key == pygame.K_m):
                        self.updateCurrentType(-1)

                    elif event.key == pygame.K_n:
                        self.newGroup()

                    elif event.unicode == '0' or event.unicode == u'\xe0':
                        self.setCurrentType("default")
                    elif event.unicode == '1' or event.unicode == u'&':
                        if event.mod & pygame.KMOD_ALT != 0:
                            self.setCurrentType("foren6-sniffer")
                        else: self.setCurrentGroup("sniffers")
                    elif event.unicode == '2' or event.unicode == u'\xe9':
                        if event.mod & pygame.KMOD_ALT != 0:
                            self.setCurrentType("contiki-rpl-node")
                        else: self.setCurrentGroup("rpl-nodes")
                    elif event.unicode == '3' or event.unicode == u'"':
                        if event.mod & pygame.KMOD_ALT != 0:
                            self.setCurrentType("contiki-border-router")
                        else: self.setCurrentGroup("rpl-border")
                    elif event.unicode == '4' or event.unicode == u"'":
                        self.setCurrentGroup("bottom-line")
                    elif event.unicode == '5' or event.unicode == u'(':
                        self.setCurrentGroup("connect")
                    elif event.unicode == '6' or event.unicode == u'-':
                        self.setCurrentGroup("further-connect")


                    #    self.deleteGroup()
                    elif event.key == pygame.K_l: #XXX
                        print self.model.groupManager.getGroupList()
                    elif event.key == pygame.K_g:
                        self.selectGroup()
                    #elif event.key == pygame.K_G:
                    #    self.saveGroup()
                    elif event.key == pygame.K_u:
                        self.model.reloadInfo()

                    elif event.key == pygame.K_f:
                        self.flashSelectedNodes()
                    elif event.key == pygame.K_r:
                        self.cmdSelectedNodes("reset")
                    elif event.key == pygame.K_d:
                        self.cmdSelectedNodes("stop")
                    elif event.key == pygame.K_e:
                        self.cmdSelectedNodes("start")
                    elif event.key == pygame.K_p:
                        if event.mod & pygame.KMOD_ALT != 0:
                            self.cmdPingLastNode(10)
                        else: self.cmdPingLastNode()

                    elif event.unicode == u'[':
                        self.updateCurrentGroup(-1)
                    elif event.unicode == u']':
                        self.updateCurrentGroup(+1)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.eventMouse(pygame.mouse.get_pos(), event.button)

        #elif event.type == MOUSEBUTTONDOWN:
        #    if event.button == 1:
        #        previous = targetNode
        #        targetNode = findClosest(screenPosList, event.pos)
        #        if previous == targetNode: targetNode = -1                
        #        print "Node %d" % targetNode
        #    elif event.button == 4: currentSimTime += 1
        #    elif event.button == 5: currentSimTime -= 1                
        #    else: print "event", dir(event)

            self.drawExp()
            pygame.display.flip()
            self.clock.tick(10)

    def eventMouse(self, pos, button):
        nodeId = findClosest(self.viewNodeList, pos)
        if button == 1:
            self.eventMouseSelect(nodeId)
        else: self.eventMouseStatus(nodeId)

    def eventMouseStatus(self, nodeId):
        self.currentNodeInfo = ("%s   " % nodeId 
                                + " ".join(self.model.getNodeInfo(nodeId)))
        self.lastNodeInfo = nodeId
        self.lastNodeId = nodeId
        print self.currentNodeInfo
    
    def eventMouseSelect(self, nodeId):
        if nodeId in self.selectedNodeList:
            self.selectedNodeList.remove(nodeId)
            print "-", nodeId
        else: 
            self.selectedNodeList.append(nodeId)
            print "+", nodeId

    def clearSelected(self):
        self.selectedNodeList = []
        self.currentNodeInfo = None
        self.lastNodeId = None
        self.lastNodeInfo = None

    def _drawStatusLine(self):
        if self.currentType ==  None:
            status = ""
        else: status = self.currentType
        msg = self.font.render(status, True, (0,0,255))
        self.screen.blit(msg, (0,self.ySize-self.yInfoSize))

        if self.currentGroup ==  None:
            status = ""
        else: status = self.currentGroup
        msg = self.font.render(status, True, (0,0,255))
        self.screen.blit(msg, (self.xSize//2,self.ySize-self.yInfoSize))

        if self.currentNodeInfo != None:
            msg = self.font.render(self.currentNodeInfo, True, (0,0,255))
            self.screen.blit(msg, (0,self.ySize-self.yInfoSize//2))


    def drawExp(self):
        self.clear()
        self._drawStatusLine()
        posOfNode = self.model.posOfNode
        self.xPosMin, self.xPosMax = self.model.xPosMin, self.model.xPosMax
        self.yPosMin, self.yPosMax = self.model.yPosMin, self.model.yPosMax
        if DisplayHack: self.yPosMax = 21.85
        typeOfNode = dict(
            [(node, typeName) 
             for (typeName, nodeList) in self.model.nodeOfType.iteritems()
             for node in nodeList])

        colorOfType = {
            "zep-sniffer": (255,255,0),
            "foren6-sniffer": (255,0,0),
            "contiki-rpl-node": (0,0,255),
            "border-router": (0,255,255),
            "contiki-border-router": (0,255,0),
            "openwsn": (0,0,127),
            "openwsn-sink": (0,255,255),
            "hipera": (127,255,127)
            }

        self.viewNodeList = []

        for nodeId, (xPos, yPos, zPos) in posOfNode.iteritems():
            if DisplayHack and yPos > 21.85:
                continue
            xx,yy = self.posToScreen(xPos,yPos)
            color = (127,127,255)
            nodeType = typeOfNode.get(nodeId)
            color = colorOfType.get(nodeType, (0,0,0))
            if nodeType == None:
                color = (127,127,127)
            nodeSize = 10
            self.drawCircle(xx, yy, nodeSize, color)
            if nodeId in self.selectedNodeList:
                selectedColor = (255,255,0)
                self.drawCircle(xx, yy, nodeSize/1.5, selectedColor)

            if nodeType != None:
                self.viewNodeList.append((xx,yy,nodeId))

#---------------------------------------------------------------------------

def runGui(iotlab, exp):
    xSize = 800
    ySize = 600

    model = ExpModel(iotlab, exp)
    application = ExpViewController(xSize, ySize, model)
    application.loop()

#---------------------------------------------------------------------------

while False:
    time.sleep(0.1)
    screen.fill((255,255,255))

        
    while True:        
        event = pygame.event.poll()
        if event.type == pygame.NOEVENT:
            break
        
        elif event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                previous = targetNode
                targetNode = findClosest(screenPosList, event.pos)
                if previous == targetNode: targetNode = -1                
                print "Node %d" % targetNode
            elif event.button == 4: currentSimTime += 1
            elif event.button == 5: currentSimTime -= 1                
            else: print "event", dir(event)
            
        elif event.type  == QUIT:
            print "<quitting>"
            sys.exit()
            
        elif event.type == KEYDOWN:
            #print event.mod, K_LCTRL
            if event.mod & KMOD_CTRL != 0: amount = 5.0
            elif event.mod & KMOD_SHIFT != 0: amount = 0.2
            else: amount = 1.0
            
            if event.key == ord('q'): print "<quitting>" ; sys.exit()
            elif event.key == ord('r'): mode = "rate" ; break
            elif event.key == ord('d'): mode = "dim" ; break
            elif event.key == ord('i'): mode = "innov" ; break
            elif event.key == ord('g'): mode = "gap" ; break            
            elif event.key == ord('/'): timeStep = - timeStep ; break
            elif event.key == ord(' '): withPause = not withPause ; break
            elif event.unicode == u'+': dotScale += 1 ; break
            elif event.unicode == u'-': dotScale -= 1 ; break
            elif event.unicode == u'=': dotScale  = 0 ; break
            elif event.key == K_HOME: currentSimTime = 0 ; break
            elif event.key == K_END: currentSimTime = nbTime-1 ; break
            elif event.key == K_LEFT: currentSimTime -= amount ; break
            elif event.key == K_RIGHT: currentSimTime += amount ; break
            else: print event, dir(event)
        #else: print event, dir(event)

    pygame.display.flip()
    #pygame.draw.circle(screen, color, (int(xx), int(yy)), nodeSize, 0)
    #screenPosList.append((xx,yy,nodeId))

#---------------------------------------------------------------------------
