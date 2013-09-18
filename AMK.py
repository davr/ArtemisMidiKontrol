import os, sys
import pygame
import pygame.midi
import pygame.fastevent
import array
import ctypes
import math
import time
import ImageGrab
from os import popen
from array import array
from pygame.locals import *

# Controls:
# 0x00 - 0x07: sliders
# 0x10 - 0x17: knobs
# 0x20 - 0x27: S buttons
# 0x30 - 0x37: M buttons
# 0x40 - 0x47: R buttons

# Slider location:
# Y: 525 - 775
# X: 51 + 157*n
# Coolant: (to get to 0, have to click 1 then 0)
# Y: 577 + 26*(8-n)
# X: 94 + 157*n
# Heat:
# Y: 484 - 525
# X: 85 + 157*n

# magic numbers
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP   = 0x0004
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_MOVE     = 0x0001

SLIDEBOT = 775.0+5
SLIDETOP = 525.0+3
SLIDELEFT = 51
SLIDESPACE = 157

COOLTOP = 577
COOLYSPACE = 26
COOLLEFT = 94
COOLXSPACE = 157

HEATTOP = 485
HEATBOT = 524
HEATLEFT = 85
HEATSPACE = 157


class _point_t(ctypes.Structure):
    _fields_ = [
                ('x',  ctypes.c_long),
                ('y',  ctypes.c_long),
               ]


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
        self.sliders[id] = value
        x = SLIDELEFT + SLIDESPACE * id
        y = value * (SLIDEBOT - SLIDETOP)
        y /= 300
        y = SLIDEBOT - y
        print "%d -> %d" % (value, y)
        self.click(x, y)

    # Set coolant #id to #value (0-8)
    # If we set to 0, we need to first set to 1 then click arrow down to 0
    def setCoolant(self, id, value):

        if value == 0:
            self.coolant[id] = 0
            self.setCoolant(id, 1)

        if self.coolant[id] == value:
            return

        x = COOLLEFT + COOLXSPACE * id
        y = COOLTOP + COOLYSPACE * (8-value)
        self.click(x, y)

    def coolUp(self, id):
        x = COOLLEFT + COOLXSPACE * id
        y = COOLTOP - COOLYSPACE
        self.click(x, y)

    def coolDown(self, id):
        x = COOLLEFT + COOLXSPACE * id
        y = COOLTOP + COOLYSPACE * 8
        self.click(x, y)
        

    # move the mouse to specific location
    def move(self, x, y):
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, int((x*65535)/self.screenW), int((y*65535)/self.screenH),0,0)

    def move2(self, x, y):
        ctypes.windll.user32.SetCursorPos(x, y)

    # click the mouse at a specific location
    def click(self, x, y):
        self.move(x,y)
        pygame.time.wait(10)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN,int(x),int(y),0,0)
        pygame.time.wait(10)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP,int(x),int(y),0,0)

    def get_screen_size():
        '''
        screen size in Windows retrun w,h of size
        '''
        w = ctypes.windll.user32.GetSystemMetrics(0)
        h = ctypes.windll.user32.GetSystemMetrics(1)
        return w,h
                   
    def get_cursor_position():
        '''getting position cursor in windows return coords x,y
        >(1024,768)
        '''
        point = _point_t()
        result = ctypes.windll.user32.GetCursorPos(ctypes.pointer(point))
        if result:
          return (point.x, point.y)
        else:
          return None

# Y: 484 - 525
# X: 85 + 157*n
    def getHeat(self):
        px=ImageGrab.grab().load()
        color = 0
        for i in range(0,8):
            x = HEATLEFT + HEATSPACE*i
            total = 0
            for y in range(HEATBOT, HEATTOP, -1):
                if sum(px[x,y]) > 200:
                    total+=1
            self.heat[i] = 100 * total/(HEATBOT - HEATTOP)
        print "Heat: " + str(self.heat)


    # both display all attached midi devices, and look for ones matching nanoKONTROL2
    def findNanoKontrol(self):
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

            if name == "nanoKONTROL2" and input:
                in_id = i
            elif name == "nanoKONTROL2" and output:
                out_id = i

            print ("%2i: interface :%s:, name :%s:, opened :%s:  %s" %
                   (i, interf, name, opened, in_out))

        return (in_id, out_id)

    # turn a LED on or off
    def light(self, btn, on):
        if on:
            out = 127
        else:
            out = 0
        self.midi_out.write_short(176, btn, out)

    # Update LEDs based on heat of each station
    # More heat = more LEDs turned on. max heat = set blink flag
    def updateLEDs(self):
        for i, value in enumerate(self.heat):
            self.blinken[i] = False
            if value < 20:
                self.light(0x40 + i, False)
                self.light(0x30 + i, False)
                self.light(0x20 + i, False)
            elif value < 40:
                self.light(0x40 + i, True)
                self.light(0x30 + i, False)
                self.light(0x20 + i, False)
            elif value < 60:
                self.light(0x40 + i, True)
                self.light(0x30 + i, True)
                self.light(0x20 + i, False)
            elif value < 80:
                self.light(0x40 + i, True)
                self.light(0x30 + i, True)
                self.light(0x20 + i, True)
            else: # overheatin' time to blinken
                self.blinken[i] = True

    # Blink LEDs on and off if their blinken flag is set
    def blinkLEDs(self):
        for i, blink in enumerate(self.blinken):
            if blink:
                diff = pygame.time.get_ticks() - self.last 
                if diff < 100:
                    self.light(0x40 + i, True)
                    self.light(0x30 + i, True)
                    self.light(0x20 + i, True)
                elif diff < 200:
                    self.light(0x40 + i, False)
                    self.light(0x30 + i, False)
                    self.light(0x20 + i, False)
                else:
                    self.last = pygame.time.get_ticks()


    def MainLoop(self):
        # attempt to autodetect nanokontrol
        (in_device_id, out_device_id) = self.findNanoKontrol()

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

        midi_in = self.midi_in = pygame.midi.Input( in_device_id )
        
        print "using input  id: %s" % in_device_id

        midi_out = self.midi_out = pygame.midi.Output(out_device_id, 0)

        print "using output id: %s" % out_device_id

        # init some vars
        self.blinken = [False]*8
        self.datas = datas = [0]*0xFF
        self.last = pygame.time.get_ticks()
        self.heat = [0]*8

        ctr = 0
        ctr2 = 0

        coolers = dict(zip(range(0,8), [0]*8))
        self.coolant = dict(zip(range(0,8), [0]*8))
        self.sliders = dict(zip(range(0,8), [0]*8))

        # Loop forever and ever
        while True:
            # waste time so that we don't eat too much CPU
            pygame.time.wait(1)

            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    sys.exit()

            self.blinkLEDs()

            ctr += 1
            if ctr > 200:
                self.getHeat()
                self.updateLEDs()
                ctr = 0

            ctr2 += 1
            if ctr2 > 2000:
                print "Sliders: "+str(self.sliders)
                for id,value in enumerate(self.sliders):
                    self.setSlider(id, value)
                ctr2 = 0
                    

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

                    # map midi sliders to engineering sliders
                    if me.data1 >= 0x00 and me.data1 <= 0x07:
                        sliders[me.data1] = me.data2 * 300/127

                    # map midi knobs to engineering coolant
                    if me.data1 >= 0x10 and me.data1 <= 0x17:
                        newval = math.floor(me.data2 * 8 / 127.0)
                        coolers[me.data1 - 0x10] = newval
                        changedCoolers = True

                    if me.data1 >= 0x20 and me.data1 <= 0x27 and me.data2 == 127:
                        self.coolUp(me.data1 - 0x20)

                    if me.data1 >= 0x40 and me.data1 <= 0x47 and me.data2 == 127:
                        self.coolDown(me.data1 - 0x40)

                print "Slides: " + str(sliders)
                print "Cools: " + str(coolers)

                for id,value in sliders.iteritems():
                        self.setSlider(id, value)

                if changedCoolers:
                        for id,value in coolers.iteritems():
                                self.setCoolant(id, value)


if __name__ == '__main__':
    am = AMK()
    am.MainLoop()
