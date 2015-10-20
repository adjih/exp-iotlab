#---------------------------------------------------------------------------
# Radio Map Analysis
# (code gets moved from freq-analysis-final.ipynb to here)
#---------------------------------------------------------------------------
# Cedric Adjih - 2015
#---------------------------------------------------------------------------

#--------------------------------------------------
# From: http://www.phyletica.com/?p=308 
import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
#--------------------------------------------------

import warnings, os, sys, types, time
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats # sudo apt-get install python-scipy
import scipy.sparse.csgraph
from pylab import *
from mpl_toolkits.mplot3d import Axes3D

import argparse

import matplotlib.ticker as ticker

try: from astropy.stats.funcs import binom_conf_interval
except: from astropyStatFuncs import binom_conf_interval # local copy

#---------------------------------------------------------------------------

DefaultExpDir = "../exp-2015-02-04-23h02m50"
expDir = DefaultExpDir

FilterCountLow = 7
FilterCountHigh = 11

#---------------------------------------------------------------------------

def saveallfig(prefix, withCrop=False):
    savefig(prefix+".png", bbox_inches="tight", pad_inches=0)
    pdfName = prefix+".pdf"
    savefig(pdfName, bbox_inches="tight", pad_inches=0)
    print ("(figure: %s)" % pdfName)
    if withCrop:
        pdfCroppedName = prefix+"-cropped.pdf"
        os.system("pdfcrop "+pdfName+" "+pdfCroppedName)

#--------------------------------------------------

# Read meta-data, e.g. information about the "experiment"
def readPydat(name):
    with open(name, "rb") as f:
        return eval(f.read())

#--------------------------------------------------

expStat = np.load(expDir+"/stat.npz")
expError = np.load(expDir+"/error.npz")

meta = readPydat(expDir+"/meta.pydat")
ressources = readPydat(expDir+"/resources.pydat")

channelList = meta["channelList"]
powerList = meta["powerList"]


# Copy data (because np.load re-loads compressed file on demand (?))
# Indices of the matrices are as follows:
#   (power, channel, sender, receiver, packetIdx)
#       0      1        2       3         4     
recv = expStat["recv"].copy()

# Number of packets sent, number of nodes, number of channels
nbPacket = recv.sum(4).max()
assert nbPacket == meta["nbPacket"]
nbNode = len(meta["nodeList"])
nbChannel = len(channelList)

eqSendRecv = np.array(nbChannel*[np.identity(nbNode,dtype="bool")]) # matrix with boolean "sender == receiver"

assert len(powerList) == 1 # stats rely on the existence of only one power
connRecv = recv[0].sum(3, dtype=np.uint32) # linkRecv[(channel, sender, receiver)] -> number of received pkt
assert connRecv.shape == (nbChannel, nbNode, nbNode)

nbConn = nbNode * (nbNode-1)

#--- Distance computation, positions

def addressToNodeId(address):
    return int(address.split(".")[0].split("-")[-1])
    
addressToPos = {}
for info in ressources['items']:
    xyz = float(info["x"]), float(info["y"]), float(info["z"])
    addressToPos[info["network_address"]] = np.array(xyz)

nodeIdxToPos = {}
for nodeIdx,(address,port) in enumerate(meta["nodeList"]):
    nodeIdxToPos[nodeIdx] = addressToPos[address]
    
assert set(nodeIdxToPos.keys()) == set(range(nbNode))

def nodeDist(u,v):
    uv = (nodeIdxToPos[u] - nodeIdxToPos[v])
    return sqrt((uv**2).mean())

distArray = np.array([  [nodeDist(u,v) for v in range(nbNode)] 
                        for u in range(nbNode)])
allDist = np.array(nbChannel*[distArray])

xList,yList,zList = zip(*nodeIdxToPos.values())
xArray,yArray,zArray = np.array(xList), np.array(yList), np.array(zList)

#..................................................


#---------------------------------------------------------------------------
#---------------------------------------------------------------------------
#---------------------------------------------------------------------------

#---------------------------------------------------------------------------
# Utils
#---------------------------------------------------------------------------

#..................................................
# from: http://stackoverflow.com/questions/8130823/set-matplotlib-3d-plot-aspect-ratio

def axisEqual3D(ax):
    extents = np.array([getattr(ax, 'get_{}lim'.format(dim))() for dim in 'xyz'])
    sz = extents[:,1] - extents[:,0]
    centers = np.mean(extents, axis=1)
    maxsize = max(abs(sz))
    r = maxsize/2
    for ctr, dim in zip(centers, 'xyz'):
        getattr(ax, 'set_{}lim'.format(dim))(ctr - r, ctr + r)

#..................................................
# modification of axes3d.py is required according
# http://stackoverflow.com/questions/10326371/setting-aspect-ratio-of-3d-plot
# (HYRY answer)
#
# so we have this massive hack of modifying methods of one instance of Axes(3D):

def get_proj_hacked(self):
    if not hasattr(self, "pbaspect"):
        return Axes3D.get_proj(self)
    print "get_proj_hacked", self.pbaspect
    self.lim_scale = self.pbaspect
    result = Axes3D.get_proj(self)
    self.lim_scale = [1.0, 1.0, 1.0]
    return result

def hackAxesFor3DAspect(ax):
    ax.get_proj = lambda : get_proj_hacked(ax)
    ax.lim_scale = [1.0, 1.0, 1.0]
    true_get_xlim3d = ax.__class__.get_xlim3d
    true_get_ylim3d = ax.__class__.get_ylim3d
    true_get_zlim3d = ax.__class__.get_zlim3d
    ax.get_xlim3d = lambda: true_get_xlim3d(ax) / ax.lim_scale[0]
    ax.get_ylim3d = lambda: true_get_ylim3d(ax) / ax.lim_scale[1]
    ax.get_zlim3d = lambda: true_get_zlim3d(ax) / ax.lim_scale[2]

#---------------------------------------------------------------------------
# Figure: 3d floor plan
#---------------------------------------------------------------------------

def plot3dFloorPlan():
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    hackAxesFor3DAspect(ax)
    ax.plot(xArray, yArray, zArray, '.', markersize=1)
    #ax.set_aspect('equal', 'box')
    #ax.scatter(xArray, yArray, zArray, marker='o')
    #axisEqual3D(ax)
    ax.set_zlim(0)
    ax.set_xlim(0)
    ax.set_ylim(0)

    xWidth = xArray.max()-xArray.min()
    yWidth = yArray.max()-yArray.min()
    zWidth = zArray.max()-zArray.min()
    maxWidth = max(xWidth, yWidth, zWidth)

    ax.pbaspect = [
        xWidth /float (maxWidth),
        yWidth /float (maxWidth),
        zWidth /float (maxWidth)
    ] # requires modif of axes3d.py (see above)



    ax.view_init(49, -68) # azimuth

    ax.set_yticks(arange(0, max(yArray), 10))
    ax.set_zticks(arange(0, max(zArray), 10))

    #http://stackoverflow.com/questions/5525782/adjust-label-positioning-in-axes3d-of-matplotlib
    ax.set_xlabel("(m)")
    ax.xaxis._axinfo['label']['space_factor'] = 4

    ax.set_ylabel("(m)")
    ax.yaxis._axinfo['label']['space_factor'] = 2

    saveallfig("3d-floor-plan", withCrop=True)

#---------------------------------------------------------------------------
# Utils
#---------------------------------------------------------------------------

# copied from parseRadioExp.py and modified

def plotData(ax, data, nodeSubset, withRefNode=False):
    minData = data.min()
    maxData = data.max()

    for nodeId in nodeSubset:
        dataNode = data[nodeId]
        #dataNode = recv[0][channelList.index(edChannel)].sum(2)[refNode][nodeId]
        if dataNode is np.ma.masked or dataNode <= minData *1.0001:
            zs = [minData - (maxData-minData)*0.01, minData]
            #continue
        else: zs = [minData, dataNode]
        x,y = xArray[nodeId], yArray[nodeId]
        if nodeId == refNode and withRefNode: 
            color="r"
            zs = [minData, maxData]
        else: color = "k"
        ax.plot([x,x], [y,y], zs, color=color)

    ax.view_init(49, -68) # elev, azimuth
    
    ax.plot(xArray[nodeSubset], yArray[nodeSubset], minData, '.', markersize=1)
    return ax


def updateXYAspect(ax, nodeSubset):
    _xArray = xArray[nodeSubset]
    _yArray = yArray[nodeSubset]
    _zArray = zArray[nodeSubset]
    xWidth = _xArray.max()-_xArray.min()
    yWidth = _yArray.max()-_yArray.min()
    zWidth = _zArray.max()-_zArray.min()
    #maxWidth = max(xWidth, yWidth, zWidth)
    maxWidth = max(xWidth, yWidth)


    ax.pbaspect = [
        xWidth /float (maxWidth),
        yWidth /float (maxWidth),
        1.0 #zWidth /float (maxWidth)
    ] # requires modif of axes3d.py (see above)

    ax.set_yticks(arange(0, max(_yArray), 10))
    #ax.set_zticks(arange(0, max(zArray), 10))


# ...    http://stackoverflow.com/questions/20924085/python-conversion-between-coordinates
def cart2pol(x, y):
    rho = np.sqrt(x**2 + y**2)
    phi = np.arctan2(y, x)
    return(rho, phi)
# ...


#---------------------------------------------------------------------------
# Figure: location of APs -> ED with max RSSI (3D, node 100, ch 17)
# Figure: correlation between interference (~10 802.11 beacon/s). 
# + map with nodes which (1) receive perfectly (2) receive nothing 
# (3) receive a portion. 3D, node 100, ch 17
#---------------------------------------------------------------------------

refChannel = 17
refNode = 100

# --- Location of AP
def plotMaxEnergy(onlyPart=False, withRefNode=False):
    if onlyPart: nodeSubset = where(xArray < 25)[0] # some nodes
    else: nodeSubset = where(xArray > -100)[0] # all nodes

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    hackAxesFor3DAspect(ax)

    allEdData = expStat["ed"]
    edData = allEdData[0][channelList.index(refChannel)]
    data = edData.max(1)

    plotData(ax, data, nodeSubset, withRefNode)
    updateXYAspect(ax, nodeSubset)

    #http://stackoverflow.com/questions/5525782/adjust-label-positioning-in-axes3d-of-matplotlib
    ax.set_zlabel("(dBm)")
    ax.zaxis._axinfo['label']['space_factor'] = 1.8

    ax.set_xlabel("(m)")
    ax.xaxis._axinfo['label']['space_factor'] = 2.2

    ax.set_ylabel("(m)")
    ax.yaxis._axinfo['label']['space_factor'] = 1.8
    infix = "-part" if onlyPart else ""
    infix += "-sender100" if withRefNode else ""
    if onlyPart: ax.view_init(60, -40) # elev, azimuth
    ax.set_zlim(-91)
    saveallfig("max-energy-ch17"+infix, withCrop=True)

# --- Map of nodes

def plotRefRecvRate():
    nodeSubset = where(xArray > -100)[0] # all nodes
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    hackAxesFor3DAspect(ax)

    nodeSubset = where(xArray < 25)[0] # all nodes

    data = recv[0][channelList.index(refChannel)].sum(2)[refNode].copy()
    data = data/100.0
    data[refNode] = 1.2
    plotData(ax, data, nodeSubset)
    updateXYAspect(ax, nodeSubset)

    #http://stackoverflow.com/questions/5525782/adjust-label-positioning-in-axes3d-of-matplotlib
    ax.zaxis._axinfo['label']['space_factor'] = 1.7
    ax.set_zlim(0, 1.05)

    ax.view_init(60, -40) # elev, azimuth
    ax.set_zlabel("PDR (from node #100)")

    def plotFromXP(nodeIdx, color="k"):
        ax.plot([xp0, xArray[nodeIdx]], [yp0, yArray[nodeIdx]], [zArray[nodeIdx]]*2, color=color)

    plotFromXP(refNode, 'r')
    plotFromXP(neigh[subAngle.argmax()], 'b')
    plotFromXP(neigh[subAngle.argmin()], 'b')

    saveallfig("pdr-sender%s-ch%s" % (refNode, refChannel), withCrop=True)


xp0, yp0 = 15,15 # near the middle of the "box"
recvData = recv[0][channelList.index(refChannel)][refNode]
neigh = where((0 < recvData.sum(1)) & (recvData.sum(1) < nbPacket))[0]

subDist,subAngle = cart2pol(-(xArray[neigh]-xp0), yArray[neigh]-yp0)
minAngle, maxAngle = subAngle.min(), subAngle.max()

# --- Selected nodes

def plotRefNeigh(onlyPart=False):
    selection2 = where((minAngle <= angle) & (angle <= maxAngle) 
                       & (recvData.sum(1) < Rate)
                       & (recvData.sum(1) > 0))[0]
    selection3 = where((minAngle <= angle) & (angle <= maxAngle) 
                       & (recvData.sum(1) >= Rate))[0]
    nonSelection = where(logical_not((minAngle <= angle) 
                                     & (angle <= maxAngle)))[0]

    m1 = "o" if onlyPart else "."
    m2 = "s" if onlyPart else "."
    #c2 = '#9999ff' if onlyPart else "b"
    opt = { "markersize":12, "alpha":0.7 } if onlyPart else {}
    plt.plot(xArray[selection2], yArray[selection2], m1, color='r')
    plt.plot(xArray[selection3], yArray[selection3], m2,
             color='g', markersize=5)
    plt.plot(xArray[nonSelection], yArray[nonSelection], '.', color='#afafaf')
    plt.plot([xArray[refNode]], [yArray[refNode]], 'o', color='k', **opt)
    if onlyPart: xlim(-2,25)
    else: xlim(-2)

    axes().set_aspect('equal')
    xlabel("(m)")
    ylabel("(m)")
    grid()

    infix = "-part" if onlyPart else ""
    saveallfig("selected-sender100-ch17"+infix+"-pdr%s"%Rate)




# ref-loss-bitmap, ref-loss-only-bitmap

def plotRefLossBitmap(actualChannel, nodeIdx, selection, infix=""):
    channel = channelList.index(actualChannel)

    # Extract data: neigh = array of node indices of the nodes (neighbors) that have a lossy connection
    recvData = recv[0][channel][nodeIdx]

    #neigh = selection[where(selection != refNode)]
    neigh = selection
    
    # Figure
    clf()
    fig = matplotlib.pyplot.gcf()
    #fig.set_size_inches(10.0,20.0)

    data2d = 1.0 - (logical_not(recvData[neigh]).astype(float))
    refNodePos =  where(selection == refNode)[0]
    assert len(refNodePos) == 1
    data2d[refNodePos] = 0.33

    # The raw packet receival loss
    # http://wiki.scipy.org/Cookbook/Matplotlib/Show_colormaps
    imshow(data2d, interpolation='none', cmap=get_cmap("hot"), 
           extent=[0,100,0,len(neigh)], aspect="auto")
    #title("lost packets on one connection (1 dot = 1 lost packet)")
    ylabel("neighbor (sorted by polar coordinates)")
    xlabel("packet (sequence number)")
    grid()
    saveallfig("bitmap-%ssender%s-ch%s" % (infix, refNode, refChannel))
 

distXP,angle = cart2pol(-(xArray-xp0), yArray-yp0)
refSelection = where((minAngle <= angle) & (angle <= maxAngle))[0]
refSelection2 = where((minAngle <= angle) & (angle <= maxAngle) 
                      & (recvData.sum(1) < nbPacket))[0]

#---------------------------------------------------------------------------
# Basic link analysis
#---------------------------------------------------------------------------

assert len(powerList) == 1 # stats rely on the existence of only one power in the experiments
linkRecv = recv[0].sum(3, dtype=np.uint32) # linkRecv[(channel, sender, receiver)] -> number of received pkt
assert linkRecv.shape == (nbChannel, nbNode, nbNode)
eqSendRecv0 = np.identity(nbNode,dtype="bool")
eqSendRecv = np.array(nbChannel*[eqSendRecv0]) # matrix with boolean "sender == receiver"


def plotHist3d(xHistData,yHistData,xBins,yBins, wx=0.6, wy=0.6, ox=0, oy=0, 
               color="#ff0000", normAxis = None, **kw):
    # http://matplotlib.org/examples/mplot3d/bars3d_demo.html
    # from: http://matplotlib.org/examples/mplot3d/hist3d_demo.html
    hist, xedges, yedges = np.histogram2d(xHistData, yHistData,  
                                          (xBins, yBins))

    if normAxis == 0:
        hist = hist / hist.sum(axis=normAxis)[np.newaxis,:]
    elif normAxis == 1:
        hist = hist / hist.sum(axis=normAxis)[:,np.newaxis]
    else: assert normAxis == None

    dxe = (xedges[1]-xedges[0])
    dye = (yedges[1]-yedges[0])

    ax = figure(figsize=(16,16)).add_subplot(111, projection='3d') #XXX
    #ax = figure(figsize=(10,10)).add_subplot(111, projection='3d') #XXX
    #ax = figure(figsize=(8,8)).add_subplot(111, projection='3d') #XXX

    elements = (len(xedges) - 1) * (len(yedges) - 1)
    xpos, ypos = np.meshgrid(xedges[:-1]+ox, yedges[:-1]+oy)
    xpos = xpos.flatten()
    ypos = ypos.flatten()
    zpos = np.zeros(elements)
    dx = wx * (dxe) * np.ones_like(zpos)
    dy = wy * (dye) * np.ones_like(zpos)
    dz = hist.transpose().flatten()

    if isinstance(color, types.FunctionType):
        colZ = np.array([color(x,y,hist[x,y]) for y in range(len(yBins)-1) for x in range(len(xBins)-1)])
        color = cm.coolwarm( (colZ - colZ.min()) / (colZ.max() - colZ.min()) )
  
    ax.bar3d(xpos, ypos, zpos, dx, dy, dz, color=color, zsort='max', **kw)
    return ax


def plotLinkChannel(colorModeList = None):    
    freqArray, senderArray, receiverArray = np.where((linkRecv > 0))  # Note: indeed sender -> sender is not counted
    nonZeroRecvArray = linkRecv[freqArray, senderArray, receiverArray]
    freqArray = np.array(channelList)[freqArray]

    nbDisc = 20
    dd = 1 /float (nbDisc)
    eps = 0.0001
    channelBins = arange( min(channelList)-0.5, max(channelList)+1 +0.5, 1)
    probBins = arange(-0*eps, 1 +2*eps + 0.5*dd , dd *(1+eps) )

    if colorModeList == None:
        colorModeList = ["col0", "col1", "col2", "col3", "col4", "col5"]

    for colorMode in colorModeList:
        if colorMode == "col0":
            colorOfChannel = linspace(0, 1, len(channelBins)-1) 
            colorOfChannel = colorOfChannel ** 2 # semi-hack to adjust values
            colorMap = np.repeat( colorOfChannel.reshape(-1,1), 
                                  len(probBins)-1, 1 ).flatten()
            colorInfo = cm.rainbow(colorMap)
        elif colorMode == "col1":
            colorOfChannel = linspace(0, 0.9, len(channelBins)-1) 
            colorOfChannel = colorOfChannel ** 1.5 # semi-hack to adjust values
            colorMap = np.repeat( colorOfChannel.reshape(-1,1), 
                                  len(probBins)-1, 1 ).flatten()
            colorInfo = cm.coolwarm(colorMap)
        elif colorMode == "col2":
            colorOf = linspace(0, 0.6, len(probBins)-1)
            colorMap = np.array([(0*(x%2) + (y%8))/8.0 
                                 for y in range(len(probBins)-1) 
                                 for x in range(len(channelBins)-1)])
            colorInfo = cm.coolwarm(colorMap)
        elif colorMode == "col3":
            colorInfo="#9f8f9f"
        elif colorMode == "col4":
            colorInfo = lambda x,y,z: math.log(z)
        elif colorMode == "col5":
            colorInfo = lambda x,y,z: float(x%8)

        ax = plotHist3d(freqArray, nonZeroRecvArray /float (nbPacket), 
                        channelBins, probBins, 
                        wx=0.88, wy=0.9, ox=0.5, oy=0, 
                        color=colorInfo)
        
        font = { "size": 30 }

        #plt.tick_params(axis='both', which='major', labelsize=font["size"])
        #plot.tick_params(axis='both', which='minor', labelsize=8)

        ax.set_xlabel("frequency", fontdict=font)
        ax.xaxis._axinfo['label']['space_factor'] = 1.1

        ax.set_ylabel("PDR", fontdict=font)
        ax.yaxis._axinfo['label']['space_factor'] = 1.5

        ax.set_zlabel("number of links", fontdict=font, 
                      horizontalalignment="right", verticalalignment="top") # no avail
        ax.zaxis._axinfo['label']['space_factor'] = 1.5

        channelTickArray = np.arange(min(channelList), max(channelList)+1, 1)
        ax.set_xticks(channelTickArray)
        xlim(min(channelList),max(channelList)+1)

        plt.tick_params(axis='both', which='major', labelsize=18)
        plt.tick_params(axis='z', which='major', labelsize=12)
        #plt.tick_params(axis='x', which='major', labelsize=16, label=True)
        #plt.ticklabel_format(useOffset=10.0, axis="x")

        # https://dawes.wordpress.com/2014/06/27/publication-ready-3d-figures-from-matplotlib/
        #[t.set_va('center') for t in ax.get_yticklabels()]
        #[t.set_ha('left') for t in ax.get_yticklabels()]
        #[t.set_va('baseline') for t in ax.get_xticklabels()]

        #print t.get_position()
        #print t.set_position((100.0,100.0))
        #t.refresh()
        #[t.set_va('center') for t in ax.get_zticklabels()]
        #[t.set_ha('left') for t in ax.get_zticklabels()]
        #http://sourceforge.net/p/matplotlib/mailman/message/14187488/

        for t in ax.get_xticklabels():
            t.set_ha('left')
            t.set_va('bottom')
            t.set_rotation(50)

        for t in ax.get_yticklabels():
            t.set_ha('right')
            t.set_va('bottom')

        saveallfig("link-channel-3d-"+colorMode, withCrop=True)
        if withShow: plt.show()


#---------------------------------------------------------------------------
# Histogram of the number of channels
#---------------------------------------------------------------------------

Rate = 90  # percent
RateThreshold = nbPacket * (Rate/float (100))

RateThreshold50 = nbPacket * (50/float (100))
RateThreshold90 = nbPacket * (90/float (100))

noDiag = logical_not(eqSendRecv0)

connRecv = linkRecv

betterConn = (connRecv > RateThreshold)
channelCountOfLink = betterConn.sum(0)

betterConn90 = (connRecv > RateThreshold90)
channelCountOfLink90 = betterConn90.sum(0)

betterConn50 = (connRecv > RateThreshold50)
channelCountOfLink50 = betterConn50.sum(0)

def writeFile(fileName, content):
    with open(fileName, "w") as f:
        f.write(content)

def plotHistLinkNbChannel():
    #from pylab import rcParams
    #print rcParams["figure.figsize"]
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(8,3.5)
    flatChannelCountOfLink = channelCountOfLink50[
        where(channelCountOfLink50 > 0)]
    binBound = np.arange(len(channelList)+1) + 0.5

    channelTickArray = np.arange(1, len(channelList)+1, 1)
    xticks(channelTickArray)
    xlim(0,16.5)
    ylim(0,10000)

    h,_,_ = plt.hist(flatChannelCountOfLink, bins=binBound, 
                     color="g", rwidth=0.8)
    xlabel("number of frequencies with PDR>50%")
    ylabel("number of links")
    grid()
    saveallfig("hist-useable-channel-pdr50")

    r  = "\\newcommand{\StatTotalLinkPdrFifty}{%s}\n" % (h.sum())
    r += "\\newcommand{\StatTotalGoodLinkPdrFifty}{%s}\n" % (h[-1])
    
    writeFile("stat-useable-channel-pdr50-part.tex", r)


def plotHistLinkDistNbChannel(normAxis=None):
    assert normAxis in [None, 0]
    senderReceiverAvailLink = where(channelCountOfLink > 0)

    distInfo = distArray[senderReceiverAvailLink]
    channelCountInfo = channelCountOfLink[senderReceiverAvailLink]

    if normAxis == None:
        chStep = 4
    else: chStep = 1
    channelBins = np.arange(0, len(channelList)+1, chStep) + 0.5

    maxDist = distInfo.max()
    nbDistStep = 20
    distBins = np.arange(0, maxDist*1.02, maxDist*1.01 / nbDistStep)

    colorInfo = "#9f8f9f"

    ax = plotHist3d(channelCountInfo, distInfo, 
                    channelBins, distBins, 
                    wx=0.8, wy=0.8, ox=0.5, oy=0, 
                    color=colorInfo, normAxis=normAxis)  


    ax.set_xlabel("useable channels (count)")
    ax.set_ylabel("distance (meter)")

    if normAxis == None:
        ax.view_init(16, 167) # elev, azimuth
        ax.set_zlabel("count (histogram)")
        saveallfig("hist-link-dist-nb-channel")
    elif normAxis == 0:
        ax.view_init(16, 30) # elev, azimuth
        ax.set_zlabel("Probability ")
        ax.set_title("Prob. that a link with a given distance has `y` useable channels")
        saveallfig("prob-link-dist-nb-channel")

    #warnings.warn("graph not saved")




def plotChartFreqLink():
    flatChannelCountOfLink = channelCountOfLink[where(channelCountOfLink > 0)]

    nbLinkTotal = count_nonzero(logical_not(eqSendRecv[0]))
    nbLinkNonZero = count_nonzero((connRecv > 0).sum(0))
    nbLinkGoodSomeChannel = len(flatChannelCountOfLink)
    nbLinkGoodAllChannel = count_nonzero(flatChannelCountOfLink 
                                         == len(channelList))

    linkStat = [nbLinkNonZero - nbLinkGoodSomeChannel, nbLinkGoodAllChannel,
                nbLinkGoodSomeChannel-nbLinkGoodAllChannel, 
                ]
    linkStat = np.array(linkStat)
    colors = ["r", "g", "y"]
    pie(linkStat, 
        colors=colors,
        labels=["bad connections:\nPDR<%s%% on all\nfrequencies" % Rate, 
                "good connections:\nPDR>%s%% on all frequencies" % Rate,
"unbalanced connections: some frequencies\nwith PDR>%s%%, others with PDR<%s%%"
                % (Rate,Rate)       ])
    plt.axis('equal') 
    saveallfig("chart-freq-link-pdr%s" % Rate) 
    nbBad = (nbLinkNonZero - nbLinkGoodSomeChannel)
    nbGood = nbLinkGoodAllChannel
    nbUnbalanced = nbLinkGoodSomeChannel-nbLinkGoodAllChannel
    r = ""
    r += "\\newcommand{\\StatPairTotal}{%d}\n" % nbLinkTotal
    r += "\\newcommand{\\StatCountLinkNonZero}{%d}\n" % nbLinkNonZero
    r += "\\newcommand{\\StatCountLinkBad}{%d}\n" % nbBad
    r += "\\newcommand{\\StatCountLinkGood}{%d}\n" % nbGood
    r += "\\newcommand{\\StatCountLinkUnbalanced}{%d}\n" % nbUnbalanced
    r += "\\newcommand{\\StatPercentLinkBad}{%s}\n" % (
        100 *nbBad /float (nbLinkNonZero) )
    r += "\\newcommand{\\StatPercentLinkGood}{%s}\n" % (
        100 * nbGood /float (nbLinkNonZero) )
    r += "\\newcommand{\\StatPercentLinkUnbalanced}{%s}\n" % (
        100 * nbUnbalanced /float (nbLinkNonZero) )


    writeFile("freq-link-pdr%s.tex" % Rate, r)

#---------------------------------------------------------------------------
# Link-type depending on distance
#---------------------------------------------------------------------------

def plotLinkTypeDist(withZoom = False):
    eps = 0.0001
    HighRateThreshold = nbPacket*0.9  +eps # 90%

    noDiag = logical_not(eqSendRecv0)

    excellentConn = (connRecv >= HighRateThreshold)
    someConn = (connRecv > 0)
    nonExcellentConn = (connRecv < HighRateThreshold) #& someConn

    excellentCountOfLink = excellentConn.sum(0)
    someCountOfLink = someConn.sum(0)
    nonExcellentCountOfLink = nonExcellentConn.sum(0)

    badConnection = someConn.sum(0)

    flatDistSomeLink = distArray[where(someCountOfLink > 0)]
    flatDistExcellentLink = distArray[
        where(excellentCountOfLink == len(channelList))]
    flatDistFreqDepLink = distArray[
        where( (excellentCountOfLink > 0) & (nonExcellentCountOfLink > 0) )]

    #maxDist = flatDistSomeLink.max() / (2.5 if withZoom else 1.0)
    maxDist = flatDistSomeLink.max() / (2.5 if withZoom else 1.0)
    nbDistStep = 30
    distBins = np.arange(0, maxDist*1.02, maxDist*1.01 / nbDistStep)

    if withZoom:
        maxDist = 14
        distBins = np.arange(0, maxDist*1.02, 0.34)
        ylim(0, 1300)

    h1 = plt.hist(flatDistSomeLink, bins=distBins, 
                  label="PDR > 0% on at least one channel", 
                  rwidth=1.0, color="w")
    h2 = plt.hist(flatDistFreqDepLink, bins=distBins, 
                  label="PDR > 90% on at least one channel \nand PDR < 90% on at least another", rwidth=1.0, color="#afafaf")
    h3 = plt.hist(flatDistExcellentLink, bins=distBins, 
                  label="PDR > 90% on all channels", rwidth = 0.5, alpha=0.5, color="b")

    plt.legend()

    xlabel("distance (m)")
    ylabel("link count (histogram)")
    #title("Histogram of number of links of each type (vs distance)")
    grid()
    saveallfig("hist-link-type-dist" + ("-zoom" if withZoom else ""))


def plotNewLinkTypeDist(withZoom = False):
    eps = 0.0001

    HighRateThreshold = RateThreshold

    noDiag = logical_not(eqSendRecv0)

    goodConn = (connRecv >= HighRateThreshold)
    someConn = (connRecv > 0)
    nonGoodConn = (connRecv < HighRateThreshold) #& someConn

    goodCountOfLink = goodConn.sum(0)
    someCountOfLink = someConn.sum(0)
    nonGoodCountOfLink = nonGoodConn.sum(0)

    flatDistBad = distArray[
        where( (someCountOfLink > 0) & (goodCountOfLink == 0) ) ]
    flatDistGood = distArray[
        where(goodCountOfLink == len(channelList))]
    flatDistUnbalanced = distArray[
        where( (goodCountOfLink > 0) & (nonGoodCountOfLink > 0) )]

    #maxDist = flatDistSomeLink.max() / (2.5 if withZoom else 1.0)
    maxDist = flatDistUnbalanced.max() / (2.5 if withZoom else 1.0)
    nbDistStep = 30
    distBins = np.arange(0, maxDist*1.02, maxDist*1.01 / nbDistStep)

    if withZoom:
        maxDist = 14
        distBins = np.arange(0, maxDist*1.02, 0.34)
        ylim(0, 1200)

    labels=["bad connections:\nPDR<50% on all\nfrequencies",
            "good connections:\nPDR>50% on all frequencies",
            "unbalanced connections: some frequencies\nwith PDR>50%,"
            " others with PDR<50%"]

    labelBad = "bad connections"
    labelGood = "good connections"
    labelUnbalanced = "unbalanced connections"

    infoList = [
        (flatDistGood, labelGood, "g", 1),
        (flatDistUnbalanced, labelUnbalanced, "y", 0.5),
        (flatDistBad, labelBad, "r", 1),
    ]

    currentData = np.array([])
    currentZorder = len(infoList)
    for i,(data, label,color,alpha) in enumerate(infoList):
        #currentData = np.concatenate((currentData, data))
        currentData = data
        currentHist, bin_edges = np.histogram(currentData, bins=distBins)
        dx = bin_edges[1] - bin_edges[0]
        wx = 0.8
        lx = wx/3
        ox = i*dx*(wx-lx)/float(2)

        wx = 1.0 ; lx = wx ; ox = 0

        plt.bar((bin_edges[:-1]+bin_edges[1:])/2.0 + ox,
                currentHist, 
                color = color, 
                width = lx*dx,
                label = label, 
                alpha = alpha)
        #h1 = plt.hist(currentData, bins=distBins, label=label, 
        #              rwidth=0.1, 
        #              align = {0:"left", 1:"mid", 2:"right"}[i],
        #              color=color, zorder=currentZorder)
        currentZorder -= 1
    xlim(0,14)

    # h1 = plt.hist(flatDistBad, bins=distBins, 
    #               label=labelBad, 
    #               rwidth=1.0, color="r")
    # h2 = plt.hist(flatDistGood, bins=distBins, 
    #               label=labelGood, rwidth=1.0, color="g")
    # h3 = plt.hist(flatDistUnbalanced, bins=distBins, 
    #               label=labelUnbalanced, rwidth = 0.5, alpha=0.5, color="y")

    plt.legend()

    xlabel("distance (m)")
    ylabel("link repartition (count, bar chart)")
    #title("Histogram of number of links of each type (vs distance)")
    grid()
    saveallfig("hist-link-type-dist" + ("-zoom" if withZoom else "")
               +"-pdr%s" % Rate)


#---------------------------------------------------------------------------
# Frequency coherence computation
#---------------------------------------------------------------------------

def getCoherenceStat(threshold, withFilter = False):
    assert threshold in ["low", "middle", "high"]
    eps = 0.0001
    HighRateThreshold = nbPacket*0.9  -eps # 90%
    LowRateThreshold = nbPacket*0.1  +eps # 10%

    noDiag = logical_not(eqSendRecv0)

    excellentConn = (connRecv >= HighRateThreshold)
    someConn = (connRecv > 0)
    badOrNoneConn = (connRecv < LowRateThreshold) 
    badConn = badOrNoneConn & someConn

    excellentCountOfLink = excellentConn.sum(0)
    someCountOfLink = someConn.sum(0)
    badCountOfLink = badConn.sum(0)

    if not withFilter:
        linkSelect = where( (excellentCountOfLink > 0) & (badCountOfLink > 0) )
    else:
        linkSelect = where( (excellentCountOfLink > 0) & (badCountOfLink > 0) 
                            & (excellentCountOfLink >= FilterCountLow) 
                            & (excellentCountOfLink <= FilterCountHigh) )

        
    nbTotal  = count_nonzero(someCountOfLink > 0)
    nbVarying = count_nonzero( (excellentCountOfLink > 0) & (badCountOfLink > 0) )


    r = "\\newcommand{\\StatCountLinkTotalAgain}{%d}\n" % nbTotal
    r += "\\newcommand{\\StatCountLinkVarying}{%d}\n" % nbVarying
    r += "\\newcommand{\\StatPercentLinkVarying}{%s}\n" % (
        100 *nbVarying /float (nbTotal) )


    writeFile("stat-varying-pdr%s.tex" % Rate, r)

    distSeq = []
    changeSeq = []
    peakWidthSeq = []
    holeWidthSeq = []
    peakNbSeq = []
    holeNbSeq = []

    for u,v in zip(*linkSelect):
        excelSeq = excellentConn[...,u,v]
        badSeq = badOrNoneConn[...,u,v]
        state = None
        stateChange = 0

        for e,b in zip(excelSeq, badSeq):
            if state == None:
                if e: state = "good"
                elif b: state = "bad"
            else:
                if e and state != "good":
                    state = "good"
                    stateChange += 1
                elif b and state != "bad":
                    state = "bad"
                    stateChange += 1

        if threshold == "middle":
            missSeq = (connRecv[...,u,v] < nbPacket /float (2)) # <50%
        elif threshold == "low":
            missSeq = badSeq # <10 %
        elif threshold == "high":
            missSeq = logical_not(excelSeq) # <90%
        else: raise RuntimeError("bad threshold name", threshold)

        channelPattern = ("".join([("0" if x else "1") for x in missSeq]))
        channelHoleList = [x for x in channelPattern.split("1") if x != ""]
        nbChannelHole = len(channelHoleList)
        avgChannelHoleWidth = len("".join(channelHoleList)) /float (
            nbChannelHole) # can't be /0
        channelPeakList = [x for x in channelPattern.split("0") if x != ""]
        nbChannelPeak = len(channelPeakList)
        avgChannelPeakWidth = len("".join(channelPeakList)) /float (
            nbChannelPeak) # can't be /0
        #print channelPattern, channelHoleList, avgChannelHoleWidth, channelPeakList, avgChannelPeakWidth

        distSeq.append(distArray[u,v])
        changeSeq.append(stateChange)
        holeWidthSeq.append(avgChannelHoleWidth)
        holeNbSeq.append(nbChannelHole)
        peakWidthSeq.append(avgChannelPeakWidth)
        peakNbSeq.append(nbChannelPeak)

    distSeq = np.array(distSeq)
    changeSeq = np.array(changeSeq)
    holeWidthSeq, peakWidthSeq = np.array(holeWidthSeq), np.array(peakWidthSeq)
    holeNbSeq, peakNbSeq = np.array(holeNbSeq), np.array(peakNbSeq)

    return {"dist": distSeq, "change": changeSeq, 
            "holeWidth": holeWidthSeq, "peakWidth": peakWidthSeq,
            "holeNb":holeNbSeq, "peakNb": peakNbSeq}


def plotOneCoherence(threshold, valueName, withFilter=False):
    withZoom = True

    stat = getCoherenceStat(threshold, withFilter=withFilter)
    distSeq = stat["dist"]

    maxDist = distSeq.max() / (1.1 if withZoom else 1.0)
    minDist = distSeq.min() 
    nbDistStep = 15
    #nbDistStep = 10
    distBins = np.arange(minDist*0.9, maxDist*1.02, maxDist*1.01/nbDistStep)

    if valueName != "count":
        valueSeq = stat[valueName]
        histCount,binEdge = np.histogram(distSeq, bins=distBins)
        histSum,binEdgeAgain = np.histogram(distSeq, bins=distBins, 
                                            weights=valueSeq)
        hist = histSum / (histCount.astype(float)
                          + (histCount == 0).astype(float)) # avoid /0
    else:
        hist,binEdge = np.histogram(distSeq, bins=distBins)

    plot( (binEdge[:-1]+binEdge[1:])/2.0 , hist, 'o-')

    ylim(0, hist.max()*1.03)
    xlim(0, maxDist*1.085)
    xlabel("distance (m)")

    if withFilter:
        FilterTitle = ("\nfiltering on links with `n' frequencies where PDR"
                       ">90%%, %s<=n<=%s" % (FilterCountLow, FilterCountHigh))
    else: FilterTitle = ""
    thresholdStr = {"low":"10%","middle":"50%","high":"90%"}[threshold]
    valueTitle = valueName
    if valueName == "change":
        ylabel("avg. number of channel type changes") 
        title(
            "Number of channel type changes (>90% to <10% or revers)\n"
            "on sequence of all channels per link, avg by distance"
            + FilterTitle)
    elif valueName == "count":
        ylabel("histogram (count)")
        title("Number of links with one available frequency\n"
              +"(PDR threshold=%s)" % thresholdStr
              +FilterTitle)
    else: 
        valueTitle = valueName.replace("W", " w").replace("N", " n")
        #ylabel("average")
        ylabel('average "'+valueTitle + 
               '" (PDR threshold=%s)' % thresholdStr
              +FilterTitle)
    grid()

    prefix = "filtered-" if withFilter else ""
    valueStr = valueTitle.replace(" ","_")
    saveallfig(prefix+"coherence-dist-%s-pdr_%s" % (valueStr,threshold),
               withCrop=True)

    
def plotCoherence(withFilter = False):
    global withShow
    for threshold in ["low", "high", "middle"]:
        for valueName in ["holeWidth","peakWidth","holeNb","peakNb","change",
                          "count"]:
            plotOneCoherence(threshold, valueName, withFilter)
            if withShow: plt.show()
            plt.clf()

def plotSelectedCoherence():
    for param in [("high", "peakWidth", False)]:
        plotOneCoherence(*param)
        if withShow: plt.show()
        plt.clf()

#---------------------------------------------------------------------------
# Traveling pair
#---------------------------------------------------------------------------

def plotTravelingPair(D, mode, onlyPart):

    if onlyPart: xCrop = 20
    else: xCrop = xArray.min()

    lineIndex = np.where((yArray > 0.93) & (yArray < 0.95))[0]

    fig = figure(figsize=(7,7))
    ax = fig.add_subplot(1,1,1)

    PdrUp = 0.5
    PdrDown = PdrUp

    for channelIdx,channel in enumerate(channelList):
        pdrList = []
        xList = []
        lastState = None
        lastX = None
        lastChangeX = None
        changeList = []
        for nodeIdx in lineIndex:
            x0 = xArray[nodeIdx]
            y0 = yArray[nodeIdx]
            if x0 < xCrop: continue

            dx = (xArray[lineIndex] -(x0+D))
            dpx = np.ma.masked_array(dx, dx <=0)
            if dpx.count() == 0:
                continue
            pos = dpx.argmin()
            otherNodeIdx = lineIndex[pos]
            x1 = xArray[otherNodeIdx]
            assert x1 > x0
            #print x0, x1, x1-x0

            thisPdr = (linkRecv[channelIdx][nodeIdx][otherNodeIdx] 
                       /float (nbPacket))
            pdrList.append(thisPdr)
            xList.append(x0)

            if thisPdr >= PdrUp:
                state = "up"
            elif thisPdr < PdrDown:
                state = "down"
            else: state = lastState

            if state != lastState:
                if lastState != None:
                    dotColor = "r" if (state == "down") else "g"
                    dotColor = "b"
                    xh = (lastX+x0)/2.0
                    if mode == "dot":
                        ax.plot([xh], [0.5+channel], marker="o", 
                                color=dotColor, alpha=0.5)
                    changeList.append((lastChangeX, xh, state))
                else: xh = x0
                lastChangeX = xh
            lastX = x0
            lastState = state

        xMin, xMax = min(xList)-1,max(xList)
        state = {None:None, "up":"down", "down":"up"}[lastState]
        changeList.append((lastChangeX, xMax, state))

        for xx0, xx1, state in changeList:
            t0 = (xx0-xMin) /float (xMax-xMin)
            t1 = (xx1-xMin) /float (xMax-xMin)
            if mode == "up":
                if state == "up": color,alpha = "w", 0
                else: color,alpha = "g", 0.3
            elif mode == "down":
                if state == "up": color,alpha = "r", 0.2
                else: color,alpha = "w", 0
            else: continue

            ax.axhspan(channel, channel+0.9, t0, t1, color=color, alpha=alpha) 

        pdrArray = np.array(pdrList)
        color = "#000080" if (channelIdx%2 == 0) else "#004000" #"#228B22" # NavyBlue / ForestGreen 
        color = "#222222"
        ax.plot(xList, pdrArray*0.8 + channel, '-', color=color)


    ax.set_xlabel("location of the pair of nodes (m)")
    ax.set_ylabel("PDR (per frequency)")
    channelTickArray = np.arange(min(channelList), max(channelList)+1, 1)
    ax.set_yticks(channelTickArray)
    #for label in ax.yaxis.get_xticklabels():
    #       label.set_verticalalignment('right')
    #ax.tick_params(direction='out', pad=100)
    ax.grid()

    ax.yaxis.set_major_formatter(ticker.NullFormatter())
    ax.yaxis.set_minor_locator(ticker.FixedLocator(channelTickArray+0.5))
    ax.yaxis.set_minor_formatter(ticker.FixedFormatter(channelTickArray))

    xTickArray = np.arange(xCrop, xMax, 5).astype(int)
    ax.xaxis.set_major_formatter(ticker.NullFormatter())
    ax.xaxis.set_minor_locator(ticker.FixedLocator(xTickArray))
    ax.xaxis.set_minor_formatter(ticker.FixedFormatter(xTickArray-xCrop))


    ax.set_ylim(channelTickArray.min()-0.1, channelTickArray.max()+1)
    ax.set_xlim(xMin, xMax)

    infix = "-part" if onlyPart else ""
    saveallfig("traveling-pair-%s-dist%05.2f" % (mode,D) + infix)
    print ("traveling-pair-%s-dist%05.2f" % (mode,D) + infix)

def plotAllTravelingPair():
    for onlyPart in [True, False]:
        for mode in ["up", "down", "dot"]:
            for d in np.arange(3,15,0.2):
                plotTravelingPair(d, mode, onlyPart)
                if withShow: plt.show()
                plt.clf()

def plotSelectedTravelingPair():
    for i,param in enumerate([(11.2, "down", True)]):
        plotTravelingPair(*param)
        saveallfig("traveling-pair-selected%s" % i)
        if withShow: plt.show()

#---------------------------------------------------------------------------
# RSSI vs distance
#---------------------------------------------------------------------------

def plotRssiDist3d():
    allRssi = expStat["rssi"][0].copy()
    indices = where(recv[0] > 0)
    rssiA = allRssi[indices]
    distIdxSendRecv = np.array(nbChannel*[distArray])
    distIdxSendRecvSeq = np.repeat(distIdxSendRecv[:,:,:,np.newaxis], nbPacket, axis=3)
    distA = distIdxSendRecvSeq[indices]
    distBins = arange(0, 10, 0.31)
    rssiBins = arange(-91.5, -20.5, 3)
    ax = plotHist3d(rssiA, distA, rssiBins, distBins)
    ax.view_init(24, -28) # elev, azimuth
    saveallfig("rssi-dist-3d-view1", withCrop=True)
    ax.view_init(39, 25) # elev, azimuth
    saveallfig("rssi-dist-3d-view2", withCrop=True)

def plotRssiDist():
    allRssi = expStat["rssi"][0].copy()
    indices = where(recv[0] > 0)
    rssiA = allRssi[indices]
    distIdxSendRecv = np.array(nbChannel*[distArray])
    distIdxSendRecvSeq = np.repeat(distIdxSendRecv[:,:,:,np.newaxis],
                                   nbPacket, axis=3)
    distA = distIdxSendRecvSeq[indices]

    #--------------------------------------------------

    indicesB = where( (recv[0] > 0) & (allRssi >= -90))
    rssiB = allRssi[indicesB]
    distB = distIdxSendRecvSeq[indicesB]

    slopeRssi, interceptRssi, r_value, p_value, std_err = stats.linregress(
        log10(distB), rssiB/1.0)

    slopeDist, interceptDist, r_value, p_value, std_err = stats.linregress(
        rssiB/1.0, log10(distB))
    #--------------------------------------------------

    withLog = True
    distBins = arange(0, 10, 0.31)
    rssiBins = arange(-91.5, -20.5, 3)

    distBins = arange(0, 30, 0.33)
    rssiBins = arange(-91.5, -20.5, 3)
    if not withLog:
        hist2d(distA, rssiA, bins=(distBins, rssiBins), 
               norm=matplotlib.colors.LogNorm(vmin=2000))
    else:
        hist2d(log10(distA), rssiA, bins=24, #bins=(distBins, rssiBins), 
               norm=matplotlib.colors.LogNorm(vmin=2000))
    cbar = colorbar()
    cbar.set_label('count (heat map, log scale)')


    plt.plot(log10(distBins[1:]), slopeRssi*log10(distBins[1:])+interceptRssi,
             label="$\gamma=%s$" % (-slopeRssi/10.0))
    plt.plot(log10(distBins[1:]), 
             (log10(distBins[1:])-interceptDist) /float (slopeDist),
             label="$\gamma=%s$" % (-1.0/(10.0*slopeDist)))


    grid()
    #title("density map of rssi vs distance (all received packets)")
    ylabel("rssi (dBm)")
    xlabel("distance (m)")
    if not withLog: xlim(0, 8)
    saveallfig("rssi-dist")
    warnings.warn("avoiding 'MemoryError' on Ubuntu 14.04, 8 GB, skiping rest of function") 
    return# XXX: this was added for Ubuntu script (fine on MacOS + 16 GB).

    if withShow: plt.show()
    plt.clf()
    hexbin(distA, rssiA, gridsize=(70,10), mincnt = 1,
           norm=matplotlib.colors.LogNorm(vmin=2000))
    cbar = colorbar()
    cbar.set_label('count (heat map, log scale)')
    grid()
    #title("density map of rssi vs distance (all received packets)")
    ylabel("rssi (dBm)")
    xlabel("distance (m)")
    xlim(0, 8)
    ylim(-91)

    plt.plot(distBins[1:], slopeRssi*log10(distBins[1:])+interceptRssi,
             label="$\gamma=%s$" % (-slopeRssi/10.0))
    plt.plot(distBins[1:], 
             (log10(distBins[1:])-interceptDist) /float (slopeDist),
             label="$\gamma=%s$" % (-1.0/(10.0*slopeDist)))

    saveallfig("rssi-dist-hex")

#---------------------------------------------------------------------------
# Connectivity
#---------------------------------------------------------------------------

def plotFurthestNodes():
    NbPacketConnectivity = nbPacket /float (2)    

    # XXX: this is redundant with next function
    # Link 
    InfiniteDist = 1000000
    hasLink = ( (connRecv >= NbPacketConnectivity) 
                & (connRecv.transpose(0,2,1) >= NbPacketConnectivity) )
    graphDistFreq = (hasLink.astype(int32) 
                     + logical_not(hasLink).astype(int32) * InfiniteDist)
    graphDistAny = graphDistFreq.min(0)

    # Connectivity - first find furthest nodes
    graphDist = graphDistFreq[channelList.index(22)].copy() # <- 22 
    totalDist = scipy.sparse.csgraph.floyd_warshall(graphDist)
    furthestNodes = np.unravel_index(totalDist.argmax(), graphDist.shape)

    plot(xArray, yArray, ".")
    for i in furthestNodes:
        plot(xArray[i], yArray[i], "o")
    saveallfig("furthest-nodes")

def runOneConnectivityTrial(nbSubsetNode, graphDist, furthestNodes = None): 
    """run by selecting nodes at random and returns maximum distance
    between two nodes in the network"""
    nodeSet = set(range(nbNode))
    
    if furthestNodes != None:
        assert len(furthestNodes) == 2
        nodeSet = nodeSet.difference(set(furthestNodes))
    
        nodeArray = np.array(list(nodeSet))
        np.random.shuffle(nodeArray)
        nodeSubsetArray = np.array(  list(nodeArray[0:nbSubsetNode-2])
                                     +list(furthestNodes)  )
    else:
        nodeArray = np.array(list(range(nbNode)))
        np.random.shuffle(nodeArray)
        nodeSubsetArray = np.array(list(nodeArray[0:nbSubsetNode]))

    # computation
    subgraphDist = graphDist[nodeSubsetArray][...,nodeSubsetArray].copy()
    totalSubgraphDist = scipy.sparse.csgraph.floyd_warshall(subgraphDist)
    #totalSubgraphDist = scipy.sparse.csgraph.shortest_path(subgraphDist)
    
    return totalSubgraphDist.max()  


def estimateConnectivityProb(nbIteration, nbSubsetNodeList, connChannelList,
                       withFurthest=False):
    NbPacketConnectivity = nbPacket /float (2)    

    # Link 
    InfiniteDist = 1000000
    hasLink = ( (connRecv >= NbPacketConnectivity) 
                & (connRecv.transpose(0,2,1) >= NbPacketConnectivity) )
    graphDistFreq = (hasLink.astype(int32) 
                     + logical_not(hasLink).astype(int32) * InfiniteDist)
    graphDistAny = graphDistFreq.min(0)

    # Connectivity - first find furthest nodes
    if withFurthest:
        graphDist = graphDistFreq[channelList.index(22)].copy() # <- 22 
        totalDist = scipy.sparse.csgraph.floyd_warshall(graphDist)
        furthestNodes = np.unravel_index(totalDist.argmax(), graphDist.shape)
    else: furthestNodes = None

    # Perform experiments
    countTable = {}
    for graphType in connChannelList:
        t = time.time()
        countList = []
        for nbSubsetNode in nbSubsetNodeList:
            count = 0
            for i in range(nbIteration):
                np.random.seed(nbSubsetNode + i* nbNode)
                if graphType == "all":
                    graph = graphDistAny
                else: graph = graphDistFreq[channelList.index(graphType)]
                if runOneConnectivityTrial(
                        nbSubsetNode, graph, furthestNodes) < InfiniteDist:
                    count += 1
            countList.append(count)
            #print graphType, nbSubsetNode, count
            sys.stdout.write(".")
            sys.stdout.flush()
        countTable[graphType] = countList
        print ("(%s sec)" % (time.time()-t))
    info = {
        "nbIteration": nbIteration,
        "nbSubsetNodeList": nbSubsetNodeList,
        "countTable": countTable,
        "selectedChannelList": connChannelList
    }
    return info


ConnectivityNbIteration = 1000
#ConnectivityChannelList = ["all", 11, 15, 17, 22, 23, 26]
ConnectivityChannelList = ["all"] + channelList
ConnectivityNbSubsetNodeList = range(2,150,2)

# constants for faster computation (for debug):
#ConnectivityNbIteration = 100
#ConnectivityChannelList = ["all", 15, 22]
#ConnectivityNbSubsetNodeList = [2] + range(5,150,5)

ConnectivityFileName = expDir + "-connectivity-nit%s-nch%s-nn%s.pydat" % (
    ConnectivityNbIteration, len(ConnectivityChannelList), 
    len(ConnectivityNbSubsetNodeList))


def getConnectivityStat(withFurthest=False, forceCompute=False):
    fileName = (ConnectivityFileName.replace(".pydat", "-furthest.pydat")
                if withFurthest else ConnectivityFileName)
    if (not os.path.exists(fileName)) or forceCompute:
        info = estimateConnectivityProb(ConnectivityNbIteration, 
                                        ConnectivityNbSubsetNodeList,
                                        ConnectivityChannelList,
                                        withFurthest)
        f = open(fileName, "w")
        f.write(repr(info))
        f.close()
    else:
        print ("(reading stats from file '%s')" % fileName)
        with open(fileName) as f:
            info = eval(f.read())
    return info


def doPlotConnectivityProb(chListName, withFurthest=False, forceCompute=False):
    stat = getConnectivityStat(withFurthest, forceCompute)

    nbIteration = stat["nbIteration"]
    nbNodeList = stat["nbSubsetNodeList"]
    countTable = stat["countTable"]
    chList = stat["selectedChannelList"]



    #for infix,chPlotList in [
    infix, chPlotList = {
        "part": ("", ["all", 15, 23]),
        "full": ("-full", ["all", 15, 17, 22, 23, 26]),
        "full2": ("-full2",  ConnectivityChannelList)
    }[chListName]


    for i,ch in enumerate(chPlotList):
        if ch not in chList:
            print "(data missing for channel %s)" % ch
            continue
        probArray = np.array(countTable[ch]) /float (nbIteration)
        probConfidenceArray = binom_conf_interval(countTable[ch], nbIteration,
                                                  0.95, 'jeffreys').transpose()
        low, high = probConfidenceArray.transpose()
        confidenceLow = probArray - low
        confidenceHigh = high - probArray 
        probConfidenceArray = np.array([ confidenceLow, confidenceHigh ])
        label = "all freq." if ch == "all" else "channel %s" % ch
        opt = {"yerr":probConfidenceArray} if chListName=="part" else {}
        opt["fmt"] = "o-"

        c20 = "#"+6*"7"
        c11 = "#"+6*"0"
        if chListName == "full2":
            opt ={} 
            if ch in ["all", 22, 20, 11]: 
                opt.update({"fmt": "o-"})
                if ch == "all": opt["color"] = "b"
                elif ch == 22: opt["color"] = "r"
                elif ch == 20: opt["color"] = c20
                elif ch == 11: opt["color"] = c11
            else: opt.update({"color": "#"+6*"9"})

        plt.errorbar(nbNodeList, probArray, label=label, **opt)

    nAll = 50
    iAll = where(np.array(nbNodeList) <= nAll)[0].max()
    xAll = nbNodeList[iAll]
    yAll = np.array(countTable["all"][iAll]) /float (nbIteration)    
    plt.annotate(
        'all frequencies', xy=(xAll, yAll), xytext=(32, 0.8), size="x-large", 
        arrowprops=dict(facecolor='black', shrink=0.1, width=1, color="b"))

    n22 = 60
    i22 = where(np.array(nbNodeList) <= n22)[0].max()
    x22 = nbNodeList[i22]
    y22 = np.array(countTable[22][i22]) /float (nbIteration)
    plt.annotate(
        'channel 22', xy=(x22, y22), xytext=(70, 0.20), size="x-large",
        arrowprops=dict(facecolor='black', shrink=0.1, width=1, color="r"))

    n11 = 67
    i11 = where(np.array(nbNodeList) <= n11)[0].max()
    x11 = nbNodeList[i11]
    y11 = np.array(countTable[11][i11]) /float (nbIteration)    
    plt.annotate(
        'channel 11', xy=(x11, y11), xytext=(75, 0.30), size="x-large", 
        arrowprops=dict(facecolor='black', shrink=0.1, width=1, color=c11))

    n20 = 70
    i20 = where(np.array(nbNodeList) <= n20)[0].max()
    x20 = nbNodeList[i20]
    y20 = np.array(countTable[20][i20]) /float (nbIteration)    
    plt.annotate(
        'channel 20', xy=(x20, y20), xytext=(80, 0.40), size="x-large",
        arrowprops=dict(facecolor='black', shrink=0.1, width=1, color=c20))

    grid()
    xlabel("number of nodes")
    ylabel("probability of connectivity")
    xlim(20,100)
    #plt.legend(loc="upper left")
    infix = infix + ("-furthest" if withFurthest else "")
    saveallfig("prob-connectivity%s-it%s-nx%s" 
               % (infix, nbIteration, len(nbNodeList)),
               withCrop=True)

# connectivity-prob

def plotConnectivityProb(forceCompute):
    for withFurthest in [False]:
        for chListName in ["full2"]: #["full2", "full","part"]:
            doPlotConnectivityProb(
                chListName,
                withFurthest = withFurthest, 
                forceCompute = forceCompute)
            if withShow: plt.show()
            plt.clf()

#---------------------------------------------------------------------------
# Argument parsing (not used)
#---------------------------------------------------------------------------

#parser = argparse.ArgumentParser()
#subparsers = parser.add_subparsers(dest="command")
#parser.add_argument("--test", action="store_true", default=False)
#args = parser.parse_args()

#---------------------------------------------------------------------------
# Main program
#---------------------------------------------------------------------------

allFig = "all" in sys.argv
reallyAllFig = "really-all" in sys.argv
withShow = "show" in sys.argv
forceCompute = "recompute" in sys.argv

PlotNameAndFunctionList = [
    ("3d-floor-plan", plot3dFloorPlan),
    ("max-energy", plotMaxEnergy),
    ("max-energy-part", lambda: plotMaxEnergy(onlyPart=True, withRefNode=True)),
    #("max-energy-ref", lambda: plotMaxEnergy(onlyPart=True, withRefNode=True)),
    ("ref-pdr", plotRefRecvRate),
    ("ref-neigh", plotRefNeigh),
    ("ref-neigh-part", lambda: plotRefNeigh(onlyPart=True)),
    ("ref-loss-bitmap",
     lambda: plotRefLossBitmap(refChannel, refNode, refSelection, "")),
    ("pres-loss-bitmap",
     lambda: plotRefLossBitmap(26, 100, refSelection, "")),
    ("ref-loss-only-bitmap",
     lambda: plotRefLossBitmap(refChannel, refNode, refSelection2, "loss-")),
    ("link-nb-channel", plotHistLinkNbChannel), 
    ("link-type-dist", plotNewLinkTypeDist),
    ("link-type-dist-zoom", lambda: plotNewLinkTypeDist(withZoom=True)),
    #("coherence-all", plotCoherence),
    #("filtered-coherence-all", lambda: plotCoherence(withFilter=True)),
    ("coherence-selected", plotSelectedCoherence),
    ("link-channel", plotLinkChannel),
    #("prob-link-dist-nb-channel",  # XXX: to put back
    # lambda: plotHistLinkDistNbChannel(0)),
    #("link-dist-nb-channel", plotHistLinkDistNbChannel),
    #("traveling-pair", plotAllTravelingPair),
    ("traveling-pair-selected", plotSelectedTravelingPair),
    #("rssi-dist-3d", plotRssiDist3d),
    ("rssi-dist", plotRssiDist),
    ("chart-freq-link", plotChartFreqLink),
    ("furthest-nodes", plotFurthestNodes),
    ("connectivity-prob", lambda: plotConnectivityProb(forceCompute)),
]

slowFig = ["coherence-all", "filtered-coherence-all",
           "traveling-pair" ] # too long

for plotName,plotFunction in PlotNameAndFunctionList:
    if (plotName in sys.argv or reallyAllFig
        or (allFig and plotName not in slowFig)):
        print ("Plotting: %s" % plotName)
        plotFunction()
        if withShow: plt.show()
        plt.clf()

if len(sys.argv) <= 1:
    figList = [name for name,func in PlotNameAndFunctionList]
    
    print ("Syntax: %s [show] [all] [<figure>*]" % sys.argv[0])
    print (" show -> interactive plot")
    print (" all -> plot all figures")
    print (" <figure> = %s" % " | ".join(figList))

#---------------------------------------------------------------------------
