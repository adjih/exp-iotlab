#! /usr/bin/python
#---------------------------------------------------------------------------

import Tkinter, os
from Tkinter import *

import optparse


parser = optparse.OptionParser()
parser.add_option("--mote-id", dest="moteId", action="store", default=0,
     type="int")
(options, argList) = parser.parse_args()

CommandList = [
    ("info", "./expctl info"),
    ("forw.ports", "./expctl ssh-forward"),
    ("tunslip6", "./expctl tunslip6"),
    ("reset BR", "./expctl reset border-router"),
    ("foren6-sniffers", "./expctl foren6-sniffers"),
    ("foren6", "./expctl foren6"),
    ("gui", "./expctl gui")
]

ExtraCommandList = [
    ("compile-hello", "cd ~/Common/CA/hipercom/node_ui && PATH=/opt/msp430-gcc-4.4.5/bin:$PATH && make TARGET=z1 clean && make TARGET=z1  && echo 'done.'"),
    ("flash-hello", "cd ~/Common/HA  && ./hlab flash-all --exp-conf exp-hello.conf && echo 'done.'"),
    ("all-mote", "cd ~/Common/HA  && ./hlab all-mote-list --summary"),
    ("Xnest", " { Xnest :2 & } ; sleep 1 ; { xterm -display :2 & } ; { DISPLAY=:2 ; wmii & } "),
    ("run-hello", "cd ~/Common/HA  && python run-hello.py"),
    ("run-hello :2", "xterm -display :2 -e 'cd ~/Common/HA  && python run-hello.py' &"),
    ("start-rpl-9 :2", "ssh -i ~/.ssh/id_dsa.smartmesh hipercom@manet18.inria.fr 'cd ~/Common/CA/hipercom/node_ui && ./hctl --mote-id 9 start-rpl'"),
    ("TkSMesh", "ssh -f -X -i ~/.ssh/id_dsa.smartmesh hipercom@manet19.inria.fr 'cd ~/Common/CA/hipercom/node_ui && python TkSmartMesh.py --mote-id 3 &' &"),
    ("HelloAnalysis", "cd ~/Common/HA && python HelloAnalysis.py"),

    ("compile-smartmesh", "cd ~/Common/smartmesh/contiki-senslab/hipercom/node_ui && PATH=/opt/msp430-gcc-4.4.5/bin:$PATH && make TARGET=z1 clean && make TARGET=z1 ; echo 'done.'"),
    ("flash-smartmesh", "cd ~/Common/HA && ./hlab flash-all --exp-conf exp-smartmesh.conf && echo 'done.'"),

    ("compile-control", "cd ~/Common/smartmesh/contiki-senslab/hipercom/node_ui && PATH=/opt/msp430-gcc-4.4.5/bin:$PATH && make TARGET=z1 clean && make TARGET=z1 && cd ~/Common/CA/hipercom/node_ui && make TARGET=z1 clean && make TARGET=z1 ; echo 'done.'"),
    ("flash-control", "cd ~/Common/HA && ./hlab flash-all --exp-conf exp-control.conf && echo 'done.'"),
]

if "only-control" in argList:
    CommandList += ExtraCommandList

class Application(Frame):

    def create(self):
        self.buttonQuit = Button(self, text="QUIT", fg="red", command=self.quit)
        self.buttonQuit.pack({"side": "left"})
        
        self.buttonList = []
        for i,(name, command) in enumerate(CommandList):
            def _runCommand(command=command):
                self.runCommand(command)
            button = Button(self, text=name, command=_runCommand)
            #if i % 5 == 0:
            #    button.pack({"side":"left"})
            button.pack({"side":"top"})
            self.buttonList.append(button)

    def runCommand(self, command):
        command = command.replace("./hctl", "./hctl --mote-id %s" 
                                  % options.moteId)
        print "+", command
        os.system(command)

    def __init__(self, options, master=None):
        self.options = options
        Frame.__init__(self, master)
        self.pack()
        self.create()

root = Tk()
app = Application(options, master=root)
app.mainloop()
root.destroy()

#---------------------------------------------------------------------------

