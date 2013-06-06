#!/usr/bin/env python
import gtk
from math import ceil
import threading as thrd
from copy import copy

class AudioView():
    def change(self,widget):
        start = widget.get_value()*self.width
        self.draw_range = (start,start+self.width)
        self.func_do = self._draw_wave
        self.refresh()

    def __init__(self,pfaudio,width,height,view_all=True):
        self.pfaudio = pfaudio

        #window
        self.window = gtk.Window(type=gtk.WINDOW_TOPLEVEL)
        self.window.set_title("Audio View")
        self.window.set_default_size(width,height)
        self.window.set_resizable(False)
        self.window.connect("destroy", gtk.main_quit)
        
        self.vbox = gtk.VBox()
        self.window.add(self.vbox)

        #draw area
        self.draw_area = gtk.DrawingArea()
        self.width = width
        self.height = height
        self.draw_area.set_size_request(self.width,self.height)
        self.draw_area.connect("expose_event", self.expose)
        self.vbox.pack_start(self.draw_area,True,True,0)
        
        #srollbar
        if not view_all:
            size = self.pfaudio.data.size/self.width
            adj = gtk.Adjustment(value=0,lower=0,upper=size-1,
                                 step_incr=size/10.0,page_incr=width)
            self.scroller = gtk.HScrollbar(adjustment=adj)
            self.scroller.connect("value-changed",self.change)
            self.vbox.pack_start(self.scroller,True,True,0)
            self.draw_range = (0,self.width)
        else :
            self.draw_range = (0,self.pfaudio.data.size)
        
        self.window.show_all()
        
        self.func_do = self._draw_wave
        self.refresh()

    def expose(self, widget, event):
        self.cr = widget.window.cairo_create()

        if self.func_do:
            self.func_do()
    
    def set_bg(self,width,height):
        self.cr.set_source_rgb(0, 0, 0)
        self.cr.rectangle(0, 0, width, height)
        self.cr.fill()

    def _draw_wave(self):
        c = int(ceil(float(self.draw_range[1]-self.draw_range[0])/self.width))
        data = self.pfaudio.data[self.draw_range[0]:self.draw_range[1]:c].copy()
        time = data.size/self.pfaudio.freq

        data *= 1000
        data += self.height/2

        self.set_bg(self.width,self.height)
        if data!=None and len(data)!=0:
            self.cr.set_source_rgb(1.0,1.0,1.0)
            self.cr.move_to(0,data[0])
            i = 1
            for a in data[1:]:
                self.cr.line_to(i,a)
                i += 1
            self.cr.stroke()

        return False

    def _clear(self):
        self.cr.set_source_rgb(0, 0, 0)
        self.cr.rectangle(0, 0, self.width, self.height)
        self.cr.fill()

    def clear(self):
        self.func_do = self._clear
        self.refresh()

    def refresh(self):
        self.draw_area.queue_draw()
        while gtk.events_pending():
            gtk.main_iteration_do(True)
