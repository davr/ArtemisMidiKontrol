import os, sys
import pygame
import pygame.midi
import pygame.fastevent
import array
import ctypes
import math
import time
from os import popen
from array import array
from pygame.locals import *

# Controls:
# 0x00 - 0x07: sliders
# 0x10 - 0x17: knobs
# 0x20 - 0x27: S
# 0x30 - 0x37: M
# 0x40 - 0x47: R

# magic numbers
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP   = 0x0004
MOUSEEVENTF_ABSOLUTE = 0x8000
MOUSEEVENTF_MOVE     = 0x0001

class AMK:
    
    def __init__(self, width=640,height=480):
        pygame.init()
        pygame.fastevent.init()
        pygame.midi.init()
        print "pygame: "+str(pygame.display.Info())
        self.screenW = pygame.display.Info().current_w
        self.screenH = pygame.display.Info().current_h

    def move(self, x, y):
        print "move: "+str(x)+","+str(y)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, int((x*65535)/self.screenW), int((y*65535)/self.screenH),0,0)

    def click(self, x, y):
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE, int((x*65535)/self.screenW), int((y*65535)/self.screenH),0,0)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN,x,y,0,0)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP,x,y,0,0)


    # both display all attached midi devices, and look for ones matching nanoKONTROL2
    def findNanoKontrol(self):
        print "ID: Device Info"
        print "---------------"
        in_id = None
        out_id = None
        for i in range(500):
            x = 500+math.sin(math.pi*i/1000.0)*500
            y = 500+math.cos(i/10.0)*100
            self.move(x,y)
            time.sleep(.001)
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

    def light(self, btn, on):
        if on:
            out = 127
        else:
            out = 0
        self.midi_out.write_short(176, btn, out)

    # Update LEDs based on heat of each station
    def updateLEDs(self):
        for i, value in enumerate(self.heat):
            self.blinken[i] = False
            if value < 5:
                self.light(0x40 + i, False)
                self.light(0x30 + i, False)
                self.light(0x20 + i, False)
            elif value < 42:
                self.light(0x40 + i, True)
                self.light(0x30 + i, False)
                self.light(0x20 + i, False)
            elif value < 84:
                self.light(0x40 + i, True)
                self.light(0x30 + i, True)
                self.light(0x20 + i, False)
            elif value < 120:
                self.light(0x40 + i, True)
                self.light(0x30 + i, True)
                self.light(0x20 + i, True)
            else: # overheatin' time to blinken
                self.blinken[i] = True

    # Blink LEDs on and off if needed
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

        # Loop forever and ever
        while True:
            pygame.time.wait(1)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    sys.exit()

            self.blinkLEDs()


            if midi_in.poll():
                midi_events = midi_in.read(10)
                midi_evs = pygame.midi.midis2events(midi_events, midi_in.device_id)
                for me in midi_evs:
                    datas[me.data1] = me.data2
                    if me.data1 == 0x10 or me.data1 == 0x17:
                        self.move(datas[0x10]*10, (127-datas[0x17])*10)
                    print("\n")
                    print(str(datas[0x00:0x08]))
                    print(str(datas[0x10:0x18]))
                    print "Ev: "+str(me.data1)+" - "+str(me.data2)
                self.heat = datas[0:8]
                self.updateLEDs()
                
                        

if __name__ == '__main__':
    am = AMK()
    am.MainLoop()
