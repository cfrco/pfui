import pygtk
pygtk.require('2.0')
import gtk
import numpy as np

import Image
        
import scipy.ndimage as scii

def rgb2hex(rgb):
    return "%02X%02X%02X" % (rgb[0],rgb[1],rgb[2])

def ifkey(event,key,mask=gtk.gdk.MODIFIER_MASK):
    if event.keyval == ord(key):
        if event.get_state() & mask > 0:
            return True
    return False
        
def arr2pixbuf(imarr):
    return gtk.gdk.pixbuf_new_from_array(imarr,gtk.gdk.COLORSPACE_RGB,8)

class PfInputBox:
    def destroy(self,widget,data=None):
        self.parent.iflag = False

    def delete_event(self,widget,event,data=None):
        self.parent.iflag = False
        return False

    def keypress(self,widget,event):
        if event.keyval == 65293 : #Enter
            self.callback(self.textbox.get_text())
            self.window.destroy()
        elif event.keyval == 65307 : #Esc
            self.window.destroy()

    def __init__(self,parent,callback,message="InputBox"):
        self.parent = parent
        self.parent.iflag = True

        self.callback = callback
        self.window = gtk.Window()
        self.window.set_title(message)
        self.window.connect("delete_event",self.delete_event)
        self.window.connect("destroy",self.destroy)
        self.window.connect("key_press_event",self.keypress)
        self.textbox = gtk.Entry()
        self.window.add(self.textbox)

        self.window.show_all()
        self.window.set_usize(250,self.window.get_size()[1])

class PfBridge:
    def __init__(self,ins,viewer,index,render):
        self.ins = ins
        self.viewer = viewer
        self.index = index
        self.render = render
        self.dview = None

        self.viewer.add_bridge(self)
        self.refresh()

    def refresh(self):
        isize = self.viewer.get_imsize(self.ins._rgb.shape[:-1])
        thumbnail = self.ins.get_thumbnail(isize)
        self.viewer.view(self.index,self.render(thumbnail,self.ins))

class PfVar:
    def __init__(self,name,vrange,val=0,vinc=(1,5)):
        self.name = name
        self.vrange = vrange
        self.vinc = vinc
        self.val = val

def qvar(name,mi,ma):
    return PfVar(name,(mi,ma),val=mi)

def test_change_func(view,args):
    out = view.imarr.copy()

    out[:,:,0] = scii.gaussian_filter(out[:,:,0],args[0])
    out[:,:,1] = scii.gaussian_filter(out[:,:,1],args[1])
    out[:,:,2] = scii.gaussian_filter(out[:,:,2],args[2])

    view.imagev.set_from_pixbuf(arr2pixbuf(out))
    view.nowimarr = out

class PfsView:
    def delete_event(self,widget,event,data=None):
        return False

    def change(self,widget):
        args = []
        for hscale in self.hscales :
            args += [hscale.get_value()]
        
        self.func(self,args)

    def write_back(self):
        self.im.rgb[:,:,:] = self.nowimarr

    def keyrelease(self,widget,event):
        if ifkey(event,'q',gtk.gdk.CONTROL_MASK):
            self.window.destroy()
        elif ifkey(event,'w',gtk.gdk.CONTROL_MASK):
            self.write_back()

    def __init__(self,im,var,func=test_change_func):
        self.func = func
        self.im = im

        self.window = gtk.Window()
        self.window.set_title("DynamicView")
        self.window.set_border_width(0)
        self.window.connect("delete_event",self.delete_event)
        self.window.add_events(gtk.gdk.MOTION_NOTIFY|
                               gtk.gdk.BUTTON_PRESS|
                               gtk.gdk.BUTTON_PRESS_MASK)
        self.window.connect("key_release_event",self.keyrelease)

        self.vbox = gtk.VBox()
        self.window.add(self.vbox)

        #Image
        self.imagev = gtk.Image()
        self.imagev.set_usize(im._rgb.shape[1],im._rgb.shape[0])
        self.imarr = im.rgb.duplicate()
        self.outimarr = self.imarr
        self.imagev.set_from_pixbuf(arr2pixbuf(self.imarr))
        self.vbox.pack_start(self.imagev,False,False,0)
        
        #Scale
        self.hscales = []
        for v in var : 
            hbox = gtk.HBox()
            label = gtk.Label()
            label.set_text(v.name)
            hbox.pack_start(label,False,False,5)

            hscale = gtk.HScale()
            hscale.set_range(*v.vrange)
            hscale.set_increments(*v.vinc)
            hscale.set_update_policy(gtk.UPDATE_DELAYED)
            hscale.set_value(v.val)
            hscale.connect("value-changed",self.change)
            hbox.pack_start(hscale,True,True,10)
            self.hscales += [hscale]

            self.vbox.pack_start(hbox)

        self.window.show_all()

class PfdView:
    def destroy(self,widget,data=None):
        try :
            gtk.main_quit()
        except RuntimeError:
            pass
        
        self.bridge.dview = None
    
    def delete_event(self,widget,event,data=None):
        return False
        
    def motion_notify(self,widget,event):
        x = int(event.x)
        y = int(event.y)
        if x >= self.imarr.shape[1] or y >= self.imarr.shape[0]:
            self.statusbar_text.set_text("")
        else :
            self.statusbar_text.set_text("("+str(x)+","+str(y)+") #"+rgb2hex(self.imarr[y,x,:]))

            self.nowcolor[:,:,:] = self.imarr[y,x,:] 
            self.statusbar_color.set_from_pixbuf(arr2pixbuf(self.nowcolor.astype(np.uint8)))
    
    def click(self,widget,event):
        if event.type == gtk.gdk._2BUTTON_PRESS :
            self.refresh()
    
    def _set_title(self,title):
        self.window.set_title(title)
        if self.iflag :
            self.iflag = False

    def _savefile(self,filename):
        Image.fromarray(self.imarr).save(filename,quality=100)

    def keyrelease(self,widget,event):
        if ifkey(event,'r') and not self.iflag :
            PfInputBox(self,self._set_title)
        elif ifkey(event,'s') and not self.iflag :
            PfInputBox(self,self._savefile)
        elif ifkey(event,'q',gtk.gdk.CONTROL_MASK):
            self.window.destroy()

    def __init__(self,bridge):
        self.bridge = bridge
        self.iflag  = False

        self.window = gtk.Window()
        self.window.set_title("DetailView")
        self.window.set_border_width(0)
        self.window.connect("delete_event",self.delete_event)
        self.window.connect("destroy",self.destroy)
        self.window.add_events(gtk.gdk.MOTION_NOTIFY|
                               gtk.gdk.BUTTON_PRESS|
                               gtk.gdk.BUTTON_PRESS_MASK)
        self.window.connect("motion_notify_event", self.motion_notify)
        self.window.connect("button_press_event",self.click)
        self.window.connect("key_release_event",self.keyrelease)
        
        #VBox
        self.vbox = gtk.VBox()
        self.window.add(self.vbox)

        #Image
        self.imagev = gtk.Image()
        self.imagev.set_usize(bridge.ins._rgb.shape[1],bridge.ins._rgb.shape[0])
        self.imarr = bridge.render(bridge.ins._rgb,bridge.ins).astype(np.uint8)
        self.imagev.set_from_pixbuf(arr2pixbuf(self.imarr))
        self.vbox.pack_start(self.imagev,False,False,0)
        
        #Statusbar
        self.statusbar = gtk.HBox()
        self.vbox.pack_start(self.statusbar,False,False,2)
        
        self.statusbar_text = gtk.Label()
        self.statusbar_color = gtk.Image()
        self.statusbar_color.set_usize(17,17)
        self.nowcolor = np.ndarray((17,17,3),dtype=np.uint8)
        self.statusbar.pack_start(self.statusbar_color,False,False,0)
        self.statusbar.pack_start(self.statusbar_text,True,False,0)
        
        self.window.show_all()

    def refresh(self):
        self.imarr = self.bridge.render(self.bridge.ins._rgb,self.bridge.ins).astype(np.uint8)
        self.imagev.set_from_pixbuf(arr2pixbuf(self.imarr))

class PfWindow:
    def destroy(self,widget,data=None):
        for bridge in self.bridges :
            bridge.ins.remove_bridge(bridge)

        try :
            gtk.main_quit()
        except RuntimeError:
            pass
    
    def delete_event(self,widget,event,data=None):
        return False
    
    def motion_notify(self,widget,event):
        pass

    def get_image(self):
        """
            TODO[bug]@cfrco:
            may output wrong image
        """
        size = self.window.get_size()
        output = np.ndarray((size[1],size[0],3),dtype=np.uint8)
        output[:,:,:] = 0
        size = (size[1]/self.shape[0],
                size[0]/self.shape[1])

        for r in range(self.shape[0]):
            for c in range(self.shape[1]):
                pb = self.imagev[r][c].get_pixbuf()
                pa = pb.get_pixels_array()
                
                if pb != None :
                    output[r*size[0]:r*size[0]+len(pa),
                           c*size[1]:c*size[1]+len(pa[0]),:] = pa

        return output

    def save_image(self,filename,quality=100):
        return Image.fromarray(self.get_image()).save(filename,quality=quality)

    def click(self,widget,event):
        size = self.window.get_size()
        size = (size[1]/self.shape[0],
                size[0]/self.shape[1])
        r = int(event.y)/size[0]
        c = int(event.x)/size[1]
        
        if event.type == gtk.gdk._2BUTTON_PRESS and event.button == 1:
            for bridge in self.bridges :
                if (r,c) == bridge.index and bridge.dview == None :
                        bridge.dview = PfdView(bridge)

    def _set_title(self,title):
        self.window.set_title(title)
        if self.iflag :
            self.iflag = False

    def keyrelease(self,widget,event):
        if ifkey(event,'r') and not self.iflag :
            inputbox = PfInputBox(self,self._set_title)
        elif ifkey(event,'q',gtk.gdk.CONTROL_MASK):
            self.window.destroy()
        elif ifkey(event,'s'):
            inputbox = PfInputBox(self,self.save_image)
                    
    def __init__(self,window_size,shape=(1,1),name="Image"):
        self.bridges = []
        self.shape = shape
        self.iflag = False

        #Window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title(name)
        self.window.resize(window_size[1],window_size[0])
        self.window.set_border_width(0)
        self.window.connect("delete_event",self.delete_event)
        self.window.connect("destroy",self.destroy)

        #window mouse-event
        self.window.add_events(gtk.gdk.MOTION_NOTIFY|
                               gtk.gdk.BUTTON_PRESS|
                               gtk.gdk.BUTTON_PRESS_MASK)
        self.window.connect("motion_notify_event", self.motion_notify)
        self.window.connect("button_press_event",self.click)
        self.window.connect("key_release_event",self.keyrelease)

        #ImageViewer
        self.ibox = gtk.VBox()
        self.window.add(self.ibox)
        self.imagev = []

        for r in range(shape[0]):
            self.imagev += [[]]
            hbox = gtk.HBox()
            self.ibox.pack_start(hbox,False,False,0)
            for c in range(shape[1]):
                imagev = gtk.Image()
                imagev.set_usize(window_size[1]/shape[1],window_size[0]/shape[0])
                hbox.pack_start(imagev,False,False,0)
                self.imagev[r] += [imagev]

        self.window.show_all()

    def add_bridge(self,bridge):
        self.bridges += [bridge]

    def remove_bridge(self,bridge):
        self.bridges.remove(bridge)

    def get_imsize(self,imsize):
        size = self.window.get_size()
        size = (size[1]/self.shape[0],
                size[0]/self.shape[1])
        imr = float(imsize[0])/imsize[1]
        sr  = float(size[0])/size[1]
        osize = [0,0]

        if sr >= imr :
            osize[1] = size[1]
            osize[0] = imsize[0]*size[1]/imsize[1]
        else :
            osize[0] = size[0]
            osize[1] = imsize[1]*size[0]/imsize[0]
        
        return tuple(osize)

    def view(self,ind,imarr):
        self.imagev[ind[0]][ind[1]].set_usize(imarr.shape[1],imarr.shape[0])
        self.imagev[ind[0]][ind[1]].set_from_pixbuf(arr2pixbuf(imarr.astype(np.uint8)))

window_templates = {
    "basic" : ((2,1),[["RGB"],["FFTPS"]]),
    "im"    : ((1,1),[["RGB"]]),
    "rgb_v" : ((3,1),[["R"],["G"],["B"]]),
    "rgb_h" : ((1,3),[["R","G","B"]]),
    "full"  : ((2,3),[["RGB","FFTPS","FFT"],["R","G","B"]]),
}

#Audio
from math import ceil

class PfAudioView():
    #Event
    def change(self,widget):
        start = widget.get_value()*self.width
        self.draw_range = (start,start+self.width)
        self.func_do = self._draw_wave
        self.refresh()

    def expose(self, widget, event):
        self.cr = widget.window.cairo_create()

        if self.func_do:
            self.func_do()
    
    def __init__(self,pfaudio,width,height,view_all=True):
        self.pfaudio = pfaudio
        self.width = width
        self.height = height

        #window
        self.window = gtk.Window(type=gtk.WINDOW_TOPLEVEL)
        self.window.set_title("Audio View")
        self.window.set_default_size(width,height)
        self.window.set_resizable(False)
        self.window.connect("destroy", gtk.main_quit)
        
        #vbox
        self.vbox = gtk.VBox()
        self.window.add(self.vbox)

        #draw area
        self.draw_area = gtk.DrawingArea()
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
       
        #color
        self.bg_color = (0,0,0)
        self.line_color = (1.0,1.0,1.0)

        self.func_do = self._draw_wave
        self.refresh()

    def refresh(self):
        self.draw_area.queue_draw()
        while gtk.events_pending():
            gtk.main_iteration_do(True)
    
    def set_bg(self,width,height,color):
        self.cr.set_source_rgb(*color)
        self.cr.rectangle(0, 0, width, height)
        self.cr.fill()

    def _draw_wave(self):
        c = int(ceil(float(self.draw_range[1]-self.draw_range[0])/self.width))
        data = self.pfaudio.data[self.draw_range[0]:self.draw_range[1]:c].copy()
        #time = data.size/self.pfaudio.freq

        data *= 1000
        data += self.height/2

        self.set_bg(self.width,self.height,self.bg_color)
        self.cr.set_source_rgb(*self.line_color)
        if data!=None and len(data)!=0:
            self.cr.move_to(0,data[0])
            i = 1
            for a in data[1:]:
                self.cr.line_to(i,a)
                i += 1
            self.cr.stroke()
