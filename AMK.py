import os, sys
import pygame
import pygame.midi
import pygame.fastevent
import array
import ctypes
import math
import time
import shelve
from os import popen
from array import array
from pygame.locals import *

# magic numbers
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP   = 0x0004
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_MOVE     = 0x0001

# top y coordinate of the first slider on the screen
SLIDETOP = 660.0
# bottom y coordinate of the first slider on the screen
SLIDEBOT = 997.0
# x coordinate of the first slider on the screen, in my case its on the second screen
SLIDELEFT = 1450
# space between each slider on the screen
SLIDESPACE = 157

# y coordinate of the first coolant up button on the screen
COOLTOP = 695
# y coordinate of the first coolant down button on the screen
COOLBOT = 1003
# x coordinate of the first coolant on the screen, in my case its on the second screen
COOLLEFT = 1495
# space between the coolants
COOLSPACE = 157


class AMK:
    
    def __init__(self, width=640,height=480):
        pygame.init()
        pygame.fastevent.init()
        pygame.midi.init()
        print "pygame: "+str(pygame.display.Info())
        self.screenW = pygame.display.Info().current_w
        self.screenH = pygame.display.Info().current_h

    # Set slider #id to #value (0-300)
    def setSlider(self, id, value):
        # my midi ids of the hardwaresliders are from 44 to 51
        id = id - 44
        x = SLIDELEFT + SLIDESPACE * id
        y = value * (SLIDEBOT - SLIDETOP)
        y /= 300
        y = SLIDEBOT - y
        #print "%d : %d %d" % (value, x, y)
        self.click(x, y)


    def resetSlider(self, id, value):
        #zero = 42 # 100% for artemis
        #magic packetssss begin
        self.midi_out.write_short(0xbf, 99, 27)
        #object
        self.midi_out.write_short(0xbf, 98, id)
        #wert
        self.midi_out.write_short(0xbf, 6, value)
        #ende
        self.midi_out.write_short(0xbf, 38, 106)
        #print "resetted slider id: " + str(id)
        slidervalue = float(value) * 300/125
        self.setSlider(id, int(slidervalue))
        #print str(id) + " - " + str(value)
        

    # Set coolant #id up or down
    def setCoolant(self, id, value):
        # my midi ids of the knobs i use are from 116 to 123
        id = id - 116
        x = COOLLEFT + COOLSPACE * id
        if value == 127:
            y = COOLBOT
        if value == 0:
            y = COOLTOP
        #print "%d : %d %d" % (value, x, y)            
        self.click(x, y)

    def removeWarnings(self):
        # click away "damcon casulties!" warning popup
        # unfortunatly hardcoded values...
        self.click(2309, 731)

    # move the mouse to specific location
    def move(self, x, y):
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, int((x*65535)/self.screenW), int((y*65535)/self.screenH),0,0)

    # click the mouse at a specific location
    def click(self, x, y):
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, int((x*65535)/self.screenW), int((y*65535)/self.screenH),0,0)
        pygame.time.wait(25)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN,int(x),int(y),0,0)
        pygame.time.wait(25)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP,int(x),int(y),0,0)

    # list of keycodes: http://msdn.microsoft.com/en-us/library/ms927178.aspx
    def resetCoolants(self):
        ctypes.windll.user32.keybd_event(0x0D, 0, 0, 0) #key down
        pygame.time.wait(25)
        ctypes.windll.user32.keybd_event(0x0D, 0, 0x0002, 0) #key up
        #print "resettet coolants"

    # read presets
    def readPreset(self, preset):
        # my midi ids of the buttons i use are from 68 to 75
        bank = str(preset - 67)
        configdata = shelve.open("presets.cfg")
        configdatavalue = configdata[str(preset)]
        #print configdatavalue
        configdatavalue = configdatavalue.split(',')
        for fadervalue in configdatavalue:
            fadervalue = fadervalue.split('-')
            fadervaluefloat = float(fadervalue[1]) / 300 * 125
            #print fadervaluefloat
            #print bank + " fader " + fadervalue[0] + " value " + fadervalue[1] + " int " + str(fadervaluefloat)
            self.resetSlider(int(fadervalue[0]), int(fadervaluefloat))
        ctypes.windll.user32.keybd_event(ord(bank), 0, 0, 0) #key down
        pygame.time.wait(25)
        ctypes.windll.user32.keybd_event(ord(bank), 0, 0x0002, 0) #key up
        configdata.close()

    # store presets
    def storePreset(self, preset):
        # my midi ids of the buttons i use are from 68 to 75
        bank = str(preset - 67)
        configdata = shelve.open("presets.cfg")
        configdata[str(preset)] = ""
        configdatavalue = ""
        # iterate through all values in the array sliderValue
        for id,value in sliderValue.iteritems():
            #print "storing " + str(bank) + ": " + str(id) + "-" + str(sliderValue[id])
            if configdatavalue <> "":
               configdatavalue = configdatavalue + "," 
            configdatavalue = configdatavalue + str(id) + "-" + str(sliderValue[id])
        configdata[str(preset)] = configdatavalue
        configdata.close()
        ctypes.windll.user32.keybd_event(0x10, 0, 0, 0) #key down
        pygame.time.wait(25)
        ctypes.windll.user32.keybd_event(ord(bank), 0, 0, 0) #key down
        pygame.time.wait(25)
        ctypes.windll.user32.keybd_event(ord(bank), 0, 0x0002, 0) #key up
        pygame.time.wait(25)
        ctypes.windll.user32.keybd_event(0x10, 0, 0x0002, 0) #key up

    # both display all attached midi devices, and look for ones matching your interface
    def findMIDIInterface(self):
        print "ID: Device Info"
        print "---------------"
        in_id = None
        out_id = None
        
        for i in range( pygame.midi.get_count() ):
            r = pygame.midi.get_device_info(i)
            (interf, name, input, output, opened) = r

            in_out = ""
            if input:
                in_out = "(input)"
            if output:
                in_out = "(output)"

            # my midi device is named "USB2.0-MIDI"
            if name == "USB2.0-MIDI" and input:
            #if name == "In From MIDI Yoke:  1" and input:
                in_id = i
            elif name == "USB2.0-MIDI" and output:
            #elif name == "Out To MIDI Yoke:  2" and output:
                out_id = i

            print ("%2i: interface :%s:, name :%s:, opened :%s:  %s" %
                   (i, interf, name, opened, in_out))

        return (in_id, out_id)


    def MainLoop(self):
        
        # attempt to autodetect interface
        (in_device_id, out_device_id) = self.findMIDIInterface()

        # allow IDs to be passed in on commandline
        if len(sys.argv) > 1:
            in_device_id = int(sys.argv[1])
        if len(sys.argv) > 2:
            out_device_id = int(sys.argv[2])
    
        # if none of the above, use system default IDs
        if in_device_id is None:
            in_device_id = pygame.midi.get_default_input_id()

        if out_device_id is None:
            out_device_id = pygame.midi.get_default_output_id()

        print "using input  id: %s" % in_device_id

        midi_in = self.midi_in = pygame.midi.Input( in_device_id )
        
        print "using output id: %s" % out_device_id 

        midi_out = self.midi_out = pygame.midi.Output(out_device_id, 0)

        # init some vars
        self.datas = datas = [0]*0xFF
        self.last = pygame.time.get_ticks()

        ctr = 0

        coolers = dict(zip(range(0,8), [0]*8))
        self.coolant = dict(zip(range(0,8), [0]*8))
        self.sliders = dict(zip(range(0,8), [0]*8))
        sliderValue = {}
        store = 0
        read = 0

        # Loop forever and ever
        while True:
            # waste time so that we don't eat too much CPU
            pygame.time.wait(1)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    sys.exit()

            ctr += 1
            if ctr > 200:
                ctr = 0

            # Look for midi events
            if midi_in.poll():
                midi_events = midi_in.read(100)
                midi_evs = pygame.midi.midis2events(midi_events, midi_in.device_id)

                # process all recieved events
                sliders = {}
                coolers = {}
                changedCoolers = False
                for me in midi_evs:
                    # store event data
                    datas[me.data1] = me.data2

                    if me.data1 == 99:
                        # my midi mixer sends first a packet with data1=99
                        #print "packet start!"
                        id = ()
                        value = ()
                        packetsent = 0

                    if me.data1 == 98:
                        # the id of the slider slid or button pushed...
                        id = me.data2

                    if me.data1 == 6:
                        # and the value
                        value = me.data2

                    if packetsent == 0 and id <> () and value <> ():
                        # if we got an id and value, process the packet
                        #print "ID: " + str(id) + " - Value: " + str(value)
                        packetsent = 1

                        # store presets
                        # i use button 8 to indicate that we want to store a preset
                        if id == 8 and value == 0:
                            store = 1
                        if id == 8 and value == 127:
                            store = 0

                        # read presets
                        # i use button 12 to indicate that we want to read a preset
                        if id == 12 and value == 0:
                            read = 1
                        if id == 12 and value == 127:
                            read = 0
                            
                        # map midi sliders to engineering sliders
                        if id >= 44 and id <= 51:
                            sliders[id] = value * 300/125
                            
                        # map midi knobs to engineering coolant
                        if id >= 116 and id <= 123:
                            coolers[id] = value
                           # changedCoolers = True
                           
                        # map midi buttons to reset
                        if id >= 68 and id <= 75 and value == 0 and store == 0 and read == 0:
                            self.resetSlider(id - 24, 42)
                        if id >= 68 and id <= 75 and value == 0 and store == 1 and read == 0:
                            self.storePreset(id)
                        if id >= 68 and id <= 75 and value == 0 and store == 0 and read == 1:
                            self.readPreset(id)
                            
                        # reset all sliders
                        if id == 22 and value == 0:
                            for i in range(0, 8):
                                self.resetSlider(i + 44, 42)
                                
                        # reset coolants
                        if id == 20 and value == 0:
                            self.resetCoolants()

                        # remove warnings
                        if id == 10 and value == 0:
                            self.removeWarnings()

                for id,value in sliders.iteritems():
                        self.setSlider(id, value)
                        global sliderValue
                        # store the current slidervalue in the array sliderValue[id], used for saving presets
                        sliderValue[id] = value

                for id,value in coolers.iteritems():
                        self.setCoolant(id, value)


if __name__ == '__main__':
    am = AMK()
    am.MainLoop()
