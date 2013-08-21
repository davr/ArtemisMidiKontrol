import os, sys
import pygame
import pygame.midi
import pygame.fastevent
import array
from os import popen
from array import array
from pygame.locals import *

def _print_device_info():
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

# Controls:
# 0x00 - 0x07: sliders
# 0x10 - 0x17: knobs
# 0x20 - 0x27: S
# 0x30 - 0x37: M
# 0x40 - 0x47: R

class ArtMidi:
    """The Main PyMan Class - This class handles the main 
    initialization and creating of the Game."""
    
    def __init__(self, width=640,height=480):
        """Initialize"""
        """Initialize PyGame"""
        pygame.init()
        pygame.fastevent.init()
        pygame.midi.init()

        """Set the window Size"""
        self.width = width
        self.height = height
        """Create the Screen"""
#        self.screen = pygame.display.set_mode((self.width
#                                               , self.height))

    def light(self, btn, on):
        if on:
            out = 127
        else:
            out = 0
        self.midi_out.write_short(176, btn, out)

    def updateLEDs(self):
        for i, value in enumerate(self.datas[0:8]):
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
            elif value < 126:
                self.light(0x40 + i, True)
                self.light(0x30 + i, True)
                self.light(0x20 + i, True)
            else:
                self.blinken[i] = True

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
        """This is the Main Loop of the Game"""
        
        """tell pygame to keep sending up keystrokes when they are
        held down"""
        pygame.key.set_repeat(500, 30)
        
        """Create the background"""
#        self.background = pygame.Surface(self.screen.get_size())
#        self.background = self.background.convert()
#        self.background.fill((0,0,0))
        (in_device_id, out_device_id) = _print_device_info()

        if len(sys.argv) > 1:
            in_device_id = int(sys.argv[1])
        if len(sys.argv) > 2:
            out_device_id = int(sys.argv[2])

        if in_device_id is None:
            input_id = pygame.midi.get_default_input_id()
        else:
            input_id = in_device_id

        i = pygame.midi.Input( input_id )
        
        print "using input  id: %s" % input_id

        if out_device_id is None:
            port = pygame.midi.get_default_output_id()
        else:
            port = out_device_id

        self.midi_out = pygame.midi.Output(port, 0)

        print "using output id: %s" % port

        self.blinken = [False]*8
        self.last = pygame.time.get_ticks()

        self.datas = datas = [0]*0xFF

        with popen('cls') as f:
            clear = f.read()


        while 1:
            pygame.time.wait(1)
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    sys.exit()

            self.blinkLEDs()


            if i.poll():
                midi_events = i.read(10)
                midi_evs = pygame.midi.midis2events(midi_events, i.device_id)
                for me in midi_evs:
                    datas[me.data1] = me.data2
                    print("\n")
                    print(str(datas[0x00:0x08]))
                    print(str(datas[0x10:0x18]))
                    print "Ev: "+str(me.data1)+" - "+str(me.data2)
                self.updateLEDs()
                
                        
            """Do the Drawging"""               
            """self.screen.blit(self.background, (0, 0))     
            if pygame.font:
                font = pygame.font.Font(None, 36)
                text = font.render("Pellets %s" % self.pellets
                                    , 1, (255, 0, 0))
                textpos = text.get_rect(centerx=self.background.get_width()/2)
                self.screen.blit(text, textpos)
               
            self.pellet_sprites.draw(self.screen)
            self.snake_sprites.draw(self.screen)
            pygame.display.flip()"""
        print "done"


if __name__ == '__main__':
    am = ArtMidi()
    am.MainLoop()
