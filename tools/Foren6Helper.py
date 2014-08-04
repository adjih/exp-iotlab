#---------------------------------------------------------------------------
# 
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

Header = """[General]
background=
scale=1

"""

def genLayoutFile(nodeInfoList, scale=1.0):
    r = Header
    for nodeInfo in nodeInfoList:
        r += "[%s]\n" % nodeInfo["id"]
        r += "x=%s\n" % (scale*nodeInfo["x"])
        r += "y=%s\n" % (scale*nodeInfo["y"])
        if (int(nodeInfo["id"])-178)%5 == 0:
            r += "locked=true\n"
        else:             r += "locked=false\n"
        r += "name="
        if "name" in nodeInfo:
            r += nodeInfo["name"]
        r += "\n"
        r += "\n"
    return r


if __name__ == "__main__":
    sampleNodeInfo = [ {"id": "1379", "x": 100, "y":100, "name": "n1" },
                       {"id": "4081", "x": 0, "y":0, "name": "n2" },
                       {"id": "2668", "x": 100, "y":0, "name": "n3" } ]
    data = genLayoutFile(sampleNodeInfo, scale=0.1)
    f = open("sample.ini", "w")
    f.write(data)
    f.close()

#---------------------------------------------------------------------------

