#! /usr/bin/python
#---------------------------------------------------------------------------

import Tkinter
from Tkinter import *

import sys, os
import argparse

parser = argparse.ArgumentParser()
#parser.add_option("--mote-id", dest="moteId", action="store", default=0,
#     type="int")
args = parser.parse_args()

CommandList = [    
    ("Remote Tunnel(s)", None),
    ("forw.ports", "./expctl ssh-forward"),

    ("Contiki RPL Exp.", None),
    ("tunslip6", "./expctl tunslip6"),
    ("reset BR", "./expctl reset contiki-border-router"),

    ("Contiki and RIOT RPL Exp.", None),
    ("foren6-sniffers", "./expctl foren6-sniffers"),
    ("foren6", "./expctl foren6"),
    ("wireshark-icmpv6", 'sudo wireshark -k -i lo -Y "zep and icmpv6" &'),
    ("wireshark", 'sudo wireshark -k -i lo -Y "zep" &'),

    ("RIOT", None),
    ("riot-tv anchor", "./expctl riot-tv-anchor"),
    
    ("General", None),
    ("gui", "./expctl gui &"),
    ("web-view", "./expctl web-view"),
    ("info", "./expctl info"),

    ("Hacks", None),
    ("shake", """roxterm --fork -T shake -e bash -c 'W=$(wmctrl -l | grep -i foren6 | cut "-d " -f1); echo "moving window $W (foren6) constantly" ; D=0.1 ; U=350; V=351 ; while true ; do wmctrl -i -r $W -e 0,-1,$U,-1,-1 ; wmctrl -i -r $W -e 0,-1,$V,-1,-1 ; sleep $D ; done'"""),
    ("shake2", """roxterm --fork -T shake -e bash -c 'W=$(wmctrl -l | grep -i foren6 | cut "-d " -f1); echo "moving window $W (foren6) constantly" ; D=0.1 ; U=450; V=$(($U+1)) ; while true ; do wmctrl -i -r $W -e 0,-1,$U,-1,-1 ; wmctrl -i -r $W -e 0,-1,$V,-1,-1 ; sleep $D ; done'"""),
    #("!smartrf-sniffer", "./expctl foren6-sniffers --output wireshark+smartrf"),
    #("!wireshark-zep", 'sudo wireshark -k -i lo -Y "zep" &')
]


class Application(Frame):

    def create(self):
        self.controlFrame = Frame(self)
        self.controlFrame.pack({"side": "left"})
        self.buttonQuit = Button(self.controlFrame, text="QUIT", fg="red", 
                                 command=self.quit)
        self.buttonQuit.pack({"side": "top", "fill": "x"})
        self.buttonQuit = Button(self.controlFrame, text="restart", #fg="red", 
                                 command=self.restart)
        self.buttonQuit.pack({"side": "left", "fill": "x"})

        
        currentFrame = self
        self.buttonList = []
        for i,(name, command) in enumerate(CommandList):
            if command != None:
                def _runCommand(command=command):
                    self.runCommand(command)
                button = Button(currentFrame, text=name, command=_runCommand)
                #if i % 5 == 0:
                #    button.pack({"side":"left"})
                button.pack({"side":"top", "fill": "x"})
                self.buttonList.append(button)
            else:
                #currentFrame = Frame(self, bd=3, relief=RIDGE)
                #currentFrame.pack({"side":"top", "fill":"x"})
                #label = Label(currentFrame, text=name)
                #label.pack({"side":"top", "fill": "x"})
                currentFrame = LabelFrame(self, text = name)
                currentFrame.pack({"side":"top", "fill":"x"})

    def restart(self):
        argList = ["python", "python"] + sys.argv
        os.execlp(*argList)

    def runCommand(self, command):
        print "+", command
        os.system(command)

    def __init__(self, args, master=None):
        self.args = args
        Frame.__init__(self, master)
        self.pack()
        self.create()

root = Tk()
bgColor = "#d1e3f2"
activeBgColor = "#428bca"
root.wm_title("Exp. Tools")
root.tk_setPalette(background=bgColor, foreground='black',
                   activeBackground=activeBgColor, 
                   activeForeground=bgColor)
app = Application(args, master=root)
app.mainloop()
root.destroy()

#---------------------------------------------------------------------------
