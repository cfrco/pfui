import pygtk
pygtk.require('2.0')
import gtk
import numpy as np

import pyiptk as ip

PfRender = {
    "RGB" : lambda im,ins : im,
    "R" : lambda im,ins : ip.gray2rgb(im[:,:,0]),
    "G" : lambda im,ins : ip.gray2rgb(im[:,:,1]),
    "B" : lambda im,ins : ip.gray2rgb(im[:,:,2]),
    "FFTPS" : lambda im,ins : ip.gray2rgb(ip.four_spect(im)),
    "FFT" : lambda im,ins : np.real(ip.rgb.fft2(im)),
}

class PfBridge:
    def __init__(self,ins,viewer,index,render):
        self.ins = ins
        self.viewer = viewer
        self.index = index
        self.render = render

        self.viewer.add_bridge(self)
        self.refresh()

    def refresh(self):
        isize = self.viewer.get_imsize(self.ins._rgb.shape[:-1])
        thumbnail = self.ins.get_thumbnail(isize)
        self.viewer.view(self.index,self.render(thumbnail,self.ins))

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
        #event.x, event.y
        pass

    def __init__(self,window_size,shape=(1,1),name="Image"):
        self.bridges = []
        self.shape = shape

        #Window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title(name)
        self.window.resize(window_size[1],window_size[0])
        self.window.set_border_width(0)
        self.window.connect("delete_event",self.delete_event)
        self.window.connect("destroy",self.destroy)

        #window mouse-event
        self.window.add_events(gtk.gdk.MOTION_NOTIFY|gtk.gdk.BUTTON_PRESS)
        self.window.connect("motion_notify_event", self.motion_notify)

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
        size = (size[1]/self.shape[0],size[0]/self.shape[1])
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
        self.imagev[ind[0]][ind[1]].set_from_pixbuf(
                        gtk.gdk.pixbuf_new_from_array(imarr.astype(np.uint8),
                        gtk.gdk.COLORSPACE_RGB,8))

window_templates = {
    "basic" : ((2,1),[["RGB"],["FFTPS"]]),
    "im"    : ((1,1),[["RGB"]]),
    "rgb_v" : ((3,1),[["R"],["G"],["B"]]),
    "rgb_h" : ((1,3),[["R","G","B"]]),
    "full"  : ((2,3),[["RGB","FFTPS","FFT"],["R","G","B"]]),
}
