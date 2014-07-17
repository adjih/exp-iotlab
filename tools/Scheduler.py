#---------------------------------------------------------------------------
# Simple scheduler
#
# Cedric Adjih, Inria, 2003-2008
#---------------------------------------------------------------------------
# [Jul2014] copied from NC-iotlab/src/Scheduler.py
# [Aug2010] copied from AllSerena/admin
# [June2010] copied from IHO/PyONet/Scheduler.py
# [Sept 2008] comes from NC/src/Scheduler.py, which comes from:
# This Scheduler.py comes from pyOLSR, and then was updated in C-AR/Admin
#---------------------------------------------------------------------------

import time, select, os, sys, socket, errno
import bisect

#---------------------------------------------------------------------------

class SimulationScheduler:
    
    def __init__(self, initialTime = 0):
        self.queue = []
        self.eventCount = 0
        self.finished = [ False ]
        self.clock=initialTime
        
    def addEvent(self, relativeTime, callback, data = ()):
        assert relativeTime >= 0
        result = self.eventCount
        newClock = self.clock+relativeTime
        bisect.insort_right(
            self.queue, (newClock, self.eventCount, callback, data, result))
        self.eventCount += 1
        return result

    def _dispatchQueueTop(self):
        self.clock,unused,callback,callbackData,identifier = self.queue[0]
        self.queue = self.queue[1:]
        apply(callback,callbackData)
        
    def run(self):
        while len(self.queue)>0 and not self.finished[-1]:
            self._dispatchQueueTop()

    def stop(self):
        self.finished[-1] = True
        self.wasRecursive = True # for the RealTime..

    def getTime(self): return self.clock

#---------------------------------------------------------------------------

MaxWaitDelay = 3600.0 # XXX: 1 hour

class AbstractFdHandler:
    def fileno(self):           NotImplemented
    def waitingForInput(self):  NotImplemented
    def waitingForOutput(self): NotImplemented
    def waitingForExcept(self): NotImplemented    
    def handleInput(self):      NotImplemented
    def handleOutput(self):     NotImplemented
    def handleExcept(self):     NotImplemented

BlockSize = 1024
    
class BufferedInputFdHandler:
    def __init__(self, fd, fdReadMethod,
                 wakeUpFunction = None, closeFunction = None):
	self.fd = fd
	self.fdReadMethod = fdReadMethod
	self.buffer = ""
	self.running = True
	self.wakeUpFunction = wakeUpFunction
	self.closeFunction = closeFunction
    def fileno(self): return self.fd
    def waitingForInput(self):  
	return self.running
    def waitingForOutput(self): return False
    def waitingForExcept(self): return False
    def handleInput(self):
	try: data = self.fdReadMethod(BlockSize)
        except socket.error, (value,msg):
            if value == errno.ECONNRESET:
                self.closeFunction()
                return
            else: raise

	if len(data) == 0:
	    self.closeFunction()
	else:
	    self.buffer += data
	    while True:
		lastSize = len(self.buffer)
		self.wakeUpFunction()
		if len(self.buffer) == lastSize or len(self.buffer) == 0:
		    break
		lastSize = len(self.buffer)
    def peek(self, maxByte = None):
	if maxByte == None: 
	    return self.buffer
	else:
	    assert maxByte <= len(self.buffer)
	    return self.buffer[0:maxByte]
    def read(self, size = None):
	if size == None: size = len(self.buffer)
	result = self.buffer[0:size]
	self.buffer = self.buffer[size:]
	return result
    def handleOutput(self):     NotImplemented
    def handleExcept(self):     NotImplemented
    def setRunning(self, value = True):
	self.running = value
        
class BufferedOutputFdHandler:
    def __init__(self, fd, fdWriteMethod):
	self.fd = fd
	self.buffer = ""
	self.fdWriteMethod = fdWriteMethod
    def fileno(self): return self.fd
    def waitingForInput(self):  return False
    def waitingForOutput(self): return len(self.buffer) > 0
    def waitingForExcept(self): return False
    def handleInput(self): NotImplemented
    def write(self, data):
	self.buffer += data
    def handleOutput(self):
	assert len(self.buffer) > 0
	size = min(BlockSize, len(self.buffer))
	self.fdWriteMethod(self.buffer[:size])
	self.buffer = self.buffer[size:]
    def handleExcept(self):     NotImplemented
	
class FunctionalFdHandler:
    def __init__(self, fd, waitInputFunc=None, waitOutputFunc=None,
                 waitExceptFunc=None, handleInputFunc=None,
                 handleOutputFunc=None, handleExceptFunc=None):
        self.fd = fd
        self.waitInputFunc = waitInputFunc
        self.waitOutputFunc = waitOutputFunc
        self.waitExceptFunc = waitExceptFunc
        self.handleInputFunc = handleInputFunc
        self.handleOutputFunc = handleOutputFunc
        self.handleExceptFunc = handleExceptFunc
    def fileno(self): return self.fd.fileno()
    def waitingForInput(self):
        if self.waitInputFunc != None: return self.waitInputFunc()
        else: return False
    def waitingForOutput(self):
        if self.waitOutputFunc != None: return self.waitOutputFunc()
        else: return False
    def waitingForExcept(self):
        if self.waitExceptFunc != None: return self.waitExceptFunc()
        else: return False
    def handleInput(self):  return self.handleInputFunc()
    def handleOutput(self): return self.handleOutputFunc()
    def handleExcept(self): return self.handleExceptFunc()

class RealTimeScheduler(SimulationScheduler): # implementation reuse
    def __init__(self):
        self.dbg = False
        SimulationScheduler.__init__(self)
        self.clock = self.getTime()
        #self.fdPoll = select.poll()
        #self.fdHandler = {}
        self.fdHandlerList = []
        self.finished = []
        self.preWaitFunction = None

    def addFdHandler(self, fdHandler):
        #self.fdHandler[fd] = (function, argList)
        #XXX: what if double registration ?
        #self.fdPoll.register(fd, pollEventMask)
        #self.fdHandler
        self.fdHandlerList.append(fdHandler)

    def removeFdHandler(self, fdHandler):
        self.fdHandlerList.remove(fdHandler)

    def scheduleYield(self):
        self.shouldYield = True

    def run(self, maxRunTime = None):
        self.wasRecursive = True
        self.finished.append(False)
        if maxRunTime != None:
            timeLimit = time.time() + maxRunTime
        else: timeLimit = None
        while not self.finished[-1] and ((timeLimit == None)
                                         or (time.time() < timeLimit)):
            if self.dbg: print "[sched] loop:", time.time(), self.finished, self.queue
            # Dispatch current events (deaf by design, if CPU starved)
            if timeLimit == None:
                maxDelay = MaxWaitDelay
            else:
                maxDelay = max(timeLimit - time.time(), 0)
            delay = maxDelay
            
            if self.preWaitFunction != None:
                self.preWaitFunction()
            
            self.shouldYield = False
            while len(self.queue)>0 and not self.shouldYield:
                nextTime,unused0, unused1,unused2,unused3 = self.queue[0]
                delay = nextTime-time.time()
                if delay<=0:
                    self._dispatchQueueTop()
                    delay = maxDelay
                else: break
            
            if len(self.queue)>0:
                nextTime,unused0, unused1,unused2,unused3 = self.queue[0]
                delay = max(nextTime-time.time(), 0)

            # Wait for some event

            t = time.time()
            #print self.fdHandlerList
            def getFdHandlerList(function):
                return [ x for x in self.fdHandlerList if function(x)]
            inputFdList = getFdHandlerList(lambda x: x.waitingForInput())
            outputFdList = getFdHandlerList(lambda x: x.waitingForOutput())
            exceptFdList = getFdHandlerList(lambda x: x.waitingForExcept())

            #pollResultList = self.fdPoll.poll(delay * 1000)
            #print delay, time.time()-t
            #print pollResultList
            if self.dbg:
                print "[sched]Waiting for", delay, inputFdList, 
                sys.stdout.flush()
            (inputFdReady,outputFdReady,exceptFdReady
             ) = select.select(inputFdList, outputFdList, exceptFdList, delay)
            if self.dbg:
                print "[sched] done", time.time(), inputFdReady, \
                      outputFdReady, exceptFdReady
                sys.stdout.flush()
            
            self.clock = time.time()

            # Dispatch fd handlers
            #for fd,event in pollResultList:
            #    function,argList = self.fdHandler[fd]
            #    apply(function, argList)
            self.doCallBack(inputFdReady, outputFdReady, exceptFdReady)
            
        self.finished = self.finished[:-1]

    def doCallBack(self, inputFdReady, outputFdReady, exceptFdReady):
        self.wasRecursive = False
        for x in inputFdReady:
            x.handleInput()
            if self.wasRecursive: return
        for x in outputFdReady:
            x.handleOutput()
            if self.wasRecursive: return
        for x in exceptFdReady:
            x.handleExcept()
            if self.wasRecursive: return

    def getTime(self): return time.time()

#---------------------------------------------------------------------------

def testScheduler(schedulerClass, isRealTime = 0):
    MaxTime=100.001
    scheduler=schedulerClass()
    initialClock = scheduler.getTime()

    every={ "1":[], "2":[], "3":[], "fd":[] }
    everyList = []

    def callbackFunc(identifier, interval):
        everyList.append(identifier)
        every[identifier].append( scheduler.clock-initialClock )
        scheduler.addEvent(interval, callbackFunc, (identifier,interval))

    #def callbackFDFunc():
    #    every["fd"].append( (scheduler.clock - initialClock)*10 )
    #    everyList.append( os.read(readFd, 1) )

    class TestCallbackFd:
        def __init__(self, readFd): self.fd = readFd
        def fileno(self): return self.fd
        def waitingForInput(self): return True
        def waitingForOutput(self): return False
        def waitingForExcept(self): return False
        def handleInput(self):
            every["fd"].append( (scheduler.clock - initialClock)*10 )
            everyList.append( os.read(self.fd, 1) )

    if isRealTime:
        #XXX: tests should be more clever
        def childLoop():
            #print os.read(readSyncFd, 1)
            time.sleep(0.5)          
            for i in range(int(MaxTime)):
                os.write(writeFd, "A")
                time.sleep(1.0)
            sys.exit(0)

        readFd, writeFd = os.pipe()
        #readSyncFd, writeSyncFd = os.pipe()
        scheduler.addFdHandler( TestCallbackFd(readFd) )
        if os.fork()==0: childLoop()

    #print writeSyncFd
    c1=scheduler.addEvent(0, callbackFunc, ("3",3) )
    c2=scheduler.addEvent(0, callbackFunc, ("2",2) )
    c3=scheduler.addEvent(0, callbackFunc, ("1",1) )
    scheduler.addEvent(MaxTime-1, scheduler.stop, [])
    #if isRealTime: os.write(writeSyncFd, "@")
    scheduler.run()

    assert (c1,c2,c3) == (0,1,2)
    #if isRealTime: print every,"\n",everyList
    def intRound(x): return int(round(x))
    assert map(intRound, every["1"])==range(0,int(MaxTime),1)
    assert map(intRound, every["2"])==range(0,int(MaxTime),2)
    assert map(intRound, every["3"])==range(0,int(MaxTime+1),3)
    if isRealTime:
        everyFdList = map(intRound, every["fd"])
        #print everyFdList
        assert everyFdList == range(5,int(MaxTime*10), 
                                    10) #NOTE: stringent: 0.1%!
    print "Tests for %s are ok." % schedulerClass

#---------------------------------------------------------------------------

if __name__=="__main__":
    testScheduler(SimulationScheduler, 0)
    print "(please wait, real time scheduler test lasts for long [100 sec])"
    testScheduler(RealTimeScheduler, 1) #XXX: test also I/O

#---------------------------------------------------------------------------
