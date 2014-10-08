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
    ("reset BR", "./expctl reset contiki-border-router"),
    ("foren6-sniffers", "./expctl foren6-sniffers"),
    ("foren6", "./expctl foren6"),
    ("wireshark", 'sudo wireshark -k -i lo -Y "zep and icmpv6" &'),
    ("gui", "./expctl gui &"),
    ("shake", """roxterm --fork -T shake -e bash -c 'W=$(wmctrl -l | grep -i foren6 | cut "-d " -f1); echo "moving window $W (foren6) constantly" ; D=0.1 ; U=350; V=351 ; while true ; do wmctrl -i -r $W -e 0,-1,$U,-1,-1 ; wmctrl -i -r $W -e 0,-1,$V,-1,-1 ; sleep $D ; done'"""),
    ("shake2", """roxterm --fork -T shake -e bash -c 'W=$(wmctrl -l | grep -i foren6 | cut "-d " -f1); echo "moving window $W (foren6) constantly" ; D=0.1 ; U=450; V=$(($U+1)) ; while true ; do wmctrl -i -r $W -e 0,-1,$U,-1,-1 ; wmctrl -i -r $W -e 0,-1,$V,-1,-1 ; sleep $D ; done'"""),

    ("!smartrf-sniffer", "./expctl foren6-sniffers --output wireshark+smartrf"),
    ("!wireshark-zep", 'sudo wireshark -k -i lo -Y "zep" &')
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

