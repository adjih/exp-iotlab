#---------------------------------------------------------------------------
# Tools for identifying connected USB devices
#
# python UsbHelper.py -> list devices
# python UsbHelper.py show -> show all info of usb-serial
# python UsbHelper.py save -> save all info of usb-serial in subdir 'usb-info'
#
# Cedric Adjih - Inria - 2014
#---------------------------------------------------------------------------

import sys, os, subprocess, re, pprint
import pyudev       # sudo apt-get install python-pyudev

#---------------------------------------------------------------------------

# Identifying usb devices is not so straighforward.
#
# Some references:
# http://www.signal11.us/oss/udev/
# http://stackoverflow.com/questions/8426083/how-to-identify-devices-with-udev
# http://wiki.xfce.org/dev/thunar-volman-udev
# http://nbviewer.ipython.org/gist/amitsaha/5946601
# http://stackoverflow.com/questions/469243/how-can-i-listen-for-usb-device-inserted-events-in-linux-in-python?rq=1
#
# more to see: trying to shutdown usb ports, usually it is not possible:
# https://www.kernel.org/doc/Documentation/usb/power-management.txt
# https://github.com/codazoda/hub-ctrl.c

def showDeviceInfo(device):
    print "-"*50
    print "device:", dict(device)
    try: device.subsystem # (really)
    except: return
    print "general:",  device.sys_path, device.sys_name, device.sys_number
    print device.subsystem, device.driver, device.device_type
    print device.device_node, device.device_number, list(device.device_links)
    print "attributes:",
    try:
        print dict(device.attributes)
    except: print None
    print "tags:", dict(device.tags)
    print "init:", device.is_initialized, device.time_since_initialized


def showAllDeviceInfo(subsystem):
    context = pyudev.Context()
    for baseDevice in context.list_devices(subsystem=subsystem):
        print "=" * 75
        for device in [baseDevice]+list(baseDevice.traverse()):
            showDeviceInfo(device)

def saveAllDeviceInfo(subsystem):
    realStdout = sys.stdout
    InfoDir = "usb-info"
    if not os.path.exists(InfoDir):
        os.mkdir(InfoDir)
    context = pyudev.Context()
    for baseDevice in context.list_devices(subsystem=subsystem):
        name = baseDevice.sys_name
        fileName = os.path.join("usb-info", "info-"+ name)
        f = open(fileName, "w")
        print "-",fileName, baseDevice.driver
        sys.stdout = f
        print "=" * 75
        for device in [baseDevice]+list(baseDevice.traverse()):
            showDeviceInfo(device)
        f.close()
        sys.stdout = realStdout

#---------------------------------------------------------------------------

def getMoteDevices():
    resultList = []
    context = pyudev.Context()
    for baseDevice in context.list_devices(subsystem="usb-serial"):
        usbDevice = baseDevice.find_parent("usb", "usb_device")
        #showDeviceInfo(baseDevice)
        #showDeviceInfo(usbDevice)

        product = usbDevice.attributes["product"]
        if product == "Zolertia Z1":
            info = { 
                "type": "Zolertia Z1", 
                "port": baseDevice.sys_name,
                "id": usbDevice.attributes["serial"]
            }
            resultList.append(info)
        elif product == "FITECO M3" or product == "M3":
            iface = baseDevice.find_parent(
                subsystem="usb", device_type="usb_interface")
            if iface.attributes["bInterfaceNumber"] != "01":
                continue
            info = {
                "type": "IoT-LAB M3",
                "port": baseDevice.sys_name,
                "variant": product
            }
            resultList.append(info)
        else:
            pass
            print product ; showDeviceInfo(baseDevice)
    return resultList


def showMoteDevices():
    orderList = ["type", "port"]
    def getOrder(key):
        if key in orderList:
            return orderList.index(key)
        else: return len(orderList)

    infoList = getMoteDevices()
    infoList.sort(key=lambda x:x["type"])
    for info in infoList:
        keyList = info.keys()
        keyList.sort(key=getOrder)
        print " / ".join([ "%s: %s" % (k, info[k]) for k in keyList
                           if isinstance(info[k], basestring) ])

def kludgyGetDmesgLastEventTtyUsb():
    # as horrible as its name - you should use a pyudev.Monitor instead 
    # (but anyway, here is what people often do manually as a first step)
    lastEventOf = {}
    dmesgOutput = subprocess.check_output("dmesg")
    lines = dmesgOutput.splitlines()
    rTtyUsb = re.compile("[[]([0-9.]+)[]].+(ttyUSB[0-9]+)")
    for line in lines:
        if line.find("ttyUSB") <= 0:
            continue
        data = line.split(" ")
        m = rTtyUsb.match(line)
        if m != None:
            clockStr, ttyName = m.group(1), m.group(2)
            clock = float(clockStr)
            lastEventOf[ttyName] = clock
    return lastEventOf

def printLastM3():
    infoList = getMoteDevices()
    lastEventOf = kludgyGetDmesgLastEventTtyUsb()
    clockAndTtyList = [(lastEventOf.get(info["port"], 0), info["port"]) 
                       for info in infoList if info["type"] == "IoT-LAB M3"]
    clockAndTtyList.sort()
    if len(clockAndTtyList) == 0:
        sys.stderr.write("ERROR: not IoT-LAB M3 detected\n")
        print "NO.IOTLAB.M3"
        sys.exit(1)
    else:
        print "/dev/%s" % clockAndTtyList[-1][1]

#---------------------------------------------------------------------------

if __name__ == "__main__":
    if "save" in sys.argv:
        saveAllDeviceInfo("usb-serial")
    elif "show" in sys.argv:
        showAllDeviceInfo("usb-serial")
    elif "last" in sys.argv:
        pprint.pprint(kludgyGetDmesgLastEventTtyUsb())
    elif "kludgy-last-m3" in sys.argv:
        printLastM3()
    else:
        showMoteDevices()

#---------------------------------------------------------------------------
