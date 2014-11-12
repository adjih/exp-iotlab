
#

# Recognized formats are:
# - m: ID X received msg TYPE from ID Y #color
# - p_s: ID X selected ID Y as parent
# - p_d: ID X deleted ID Y as parent
# - d: ID X received event EID
# - i: ID X ignores ID Y 
#   (no output for the future when messages from Y to X are send)
# - r: ID X selected rank N    
#   (rank in paranthesis behind node name in graph)

import socket, json

AnchorPort = 23511
sd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sd.connect(("localhost", AnchorPort))

clock = 0




def sendData(data):
    info = {'type': 'raw', 'data': data, 'time': clock}
    tmpData = json.dumps(info)
    rawData = "%s#"%len(tmpData) + tmpData
    #rawData = '84#{"type":"raw","data":"p_s: ID sn10 selected ID sn11 as parent","time":1415750499304}'
    sd.send(rawData)


data = "p_s: ID sn10 selected ID sn11 as parent"
sendData(data)

data = "p_s: ID sn12 selected ID sn11 as parent"
sendData(data)

data = "p_s: ID sn12 selected ID sn14 as parent"
sendData(data)


data = "r: ID sn10 selected rank 123"
sendData(data)

data = "m: ID sn11 received msg DIO from ID sn13 #color6"
sendData(data)

data = "m: ID gw received msg TYPE_234 from ID sn11 #color8"
sendData(data)
