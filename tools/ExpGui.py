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

import pygame
import pygame.gfxdraw
from pygame.locals import *

import os
#os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (1*1920,0)
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0,0)

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

    def setView(self, view):
        self.view = view

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
                       and info["state"] in ("Alive", "Busy")]

        expInfo = self.exp.getPersistentInfo()
        nodeInfoByType = expInfo["nodeInfoByType"]

        self.posOfNode = dict(nodePosList)
        nodeOfType = {}
        for typeName, info in nodeInfoByType.iteritems():
            nodeOfType[typeName] = [ extractNodeId(node)
                                     for node in info["nodes"] ]

        #print posOfNode
        xPosList = [x for x,y,z in self.posOfNode.itervalues()]
        yPosList = [y for x,y,z in self.posOfNode.itervalues()]

        self.xPosMin, self.xPosMax = min(xPosList), max(xPosList)
        self.yPosMin, self.yPosMax = min(yPosList), max(yPosList)
        self.nodeOfType = nodeOfType
        #print xPosMin, xPosMax, yPosMin, yPosMax

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
        y = self.margin + yRel * (self.ySize - 2*self.margin)
        return x,y

    def toggleSelection(self):
        # unused
        if self.mode == "view": self.mode = "selection"
        else: self.mode = "view"

    def loop(self):
        self.isFinished = False
        while not self.isFinished:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.isFinished = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.isFinished = True
                    elif event.key == pygame.K_c:
                        self.clearSelected()
                    elif event.key == pygame.K_s:
                        self.toggleSelection()
                    elif event.key == pygame.K_r:
                        self.redraw()
                    elif event.key == pygame.K_p:
                        self.band += 1
                        self.redraw() 
                    elif event.key == pygame.K_m:
                        self.band -= 1
                        self.redraw()                                         
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
        if nodeId in self.selectedNodeList:
            self.selectedNodeList.remove(nodeId)
            print "-", nodeId
        else: 
            self.selectedNodeList.append(nodeId)
            print "+", nodeId

    def clearSelected(self):
        self.selectedNodeList = []

    def drawExp(self):
        posOfNode = self.model.posOfNode
        self.xPosMin, self.xPosMax = self.model.xPosMin, self.model.xPosMax
        self.yPosMin, self.yPosMax = self.model.yPosMin, self.model.yPosMax
        typeOfNode = dict(
            [(node, typeName) 
             for (typeName, nodeList) in self.model.nodeOfType.iteritems()
             for node in nodeList])

        colorOfType = {
            "zep-sniffer": (255,255,0),
            "foren6-sniffer": (255,0,0),
            "http-rpl-node": (0,0,255),
            "border-router": (0,255,0)
            }

        self.viewNodeList = []

        for nodeId, (xPos, yPos, zPos) in posOfNode.iteritems():
            xx,yy = self.posToScreen(xPos,yPos)
            color = (127,127,255)
            #print typeOfNode.get(nodeId)
            color = colorOfType.get(typeOfNode.get(nodeId), (0,0,0))
            nodeSize = 10
            self.drawCircle(xx, yy, nodeSize, color)
            if nodeId in self.selectedNodeList:
                selectedColor = (255,255,0)
                self.drawCircle(xx, yy, nodeSize/1.5, selectedColor)

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
