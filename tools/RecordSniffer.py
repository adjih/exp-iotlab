#---------------------------------------------------------------------------
# A "recording" aggregator
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

import sys, time, struct, select, socket, fcntl, os

nbSniffers = int(sys.argv[1])
outputFileName = sys.argv[2]

refTime = time.time()

f = open(outputFileName, "w")

socketOf = {}
indexOfSocket = {}

def openSocket(i):
    global socketOf, indexOfSocket
    sd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sd.connect(("localhost", 3000+i))
    socketOf[i] = sd
    indexOfSocket[sd] = i
    fcntl.fcntl(sd, fcntl.F_SETFL, os.O_NONBLOCK)

for i in range(nbSniffers):
    openSocket(i)

while True:
    socketList = list(socketOf.values())
    rList, unused, unused = select.select(socketList, [], [])
    sys.stdout.write(".")
    sys.stdout.flush()
    for sd in rList:
        snifferId = indexOfSocket[sd]
        clock = time.time() - refTime
        data = sd.recv(8192)
        if len(data) == 0:
            sd.close()
            del indexOfSocket[sd]
            sys.stdout.write("*")
            sys.stdout.flush()
            openSocket(snifferId)
        header = struct.pack("!fBH", clock, snifferId, len(data))
        f.write(header+data)
        f.flush()

#---------------------------------------------------------------------------
