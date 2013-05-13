import pygtk
pygtk.require('2.0')
import gtk
import Image
import numpy as np
import scipy.misc

import pyiptk as ip

class PfRGB_Interface(object):
    def __init__(self,ins,name):
        self.ins = ins
        self.name = name
        self.autore(True)

    def __getitem__(self,key):
        return self.ins.__getattribute__(self.name).__getitem__(key)

    def __setitem__(self,key,value):
        if self.autopush :
            self.ins.push((self.name,self.duplicate()))
        
        self.ins.__getattribute__(self.name).__setitem__(key,value)

        if self.rebuild :
            self.ins.rebuild(self.name)
        if self.refresh :
            self.ins.refresh()

    def autore(self,enable):
        self.refresh = enable
        self.rebuild = enable
        self.autopush = enable

    def duplicate(self):
        return self[:,:,:].copy()

    def do(self,func,*args):
        self.autore(False)
        self.ins.push((self.name,self.duplicate()))
        self[:,:,0] = func(self[:,:,0],*args)
        self[:,:,1] = func(self[:,:,1],*args)
        self[:,:,2] = func(self[:,:,2],*args)
        self.autore(True)
        
        self.ins.rebuild(self.name)
        self.ins.refresh()

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

class PfImage(object):
    def __init__(self,im):
        if isinstance(im,str):
            im = Image.open(im)

        if isinstance(im,Image.Image):
            if im.mode != "RGB":
                im = im.convert("RGB")
            rgb = np.asarray(im).copy()
        elif isinstance(im,np.ndarray) and len(im) == 3 and im.shape[2] == 3:
            rgb = im.copy()
        else :
            raise Exception("Not supported type.")
        
        self._rgb = rgb
        self._fft = ip.rgb.fft2(rgb)
        self._rgbif = PfRGB_Interface(self,"_rgb")
        self._fftif = PfRGB_Interface(self,"_fft")

        self.bridges = []
        self.thumbnails = {}
        self.stages = []
        self.stages_limit = 5
        #self.windows = []

    def refresh(self,changed=None):
        if changed == None :
            for bridge in self.bridges :
                #_taskworker.add_task(bridge.refresh)
                bridge.refresh()

    def rebuild(self,name):
        if name == "_rgb":
            self._fft = ip.rgb.fft2(self._rgb)
        elif name == "_fft":
            self._rgb = np.real(ip.rgb.ifft2(self._fft)).astype(np.uint8)

        self.thumbnails = {} # clean thumbnail

    def get_field(self,name):
        if name in self.field_dict :
            return self.field_dict[name](self)

    def window(self,shape,window_size,imgs,name="Image"):
        window = PfWindow(window_size,shape,name)
        #self.windows += [window]

        for r in range(len(imgs)):
            for c in range(len(imgs[r])):
                if imgs[r][c].__class__ == "funciton":
                    bridge = PfBridge(self,window,(r,c),imgs[r][c])
                else :
                    bridge = PfBridge(self,window,(r,c),PfRender[imgs[r][c]])
                self.add_bridge(bridge)

        return window

    def add_bridge(self,bridge):
        self.bridges += [bridge]

    def remove_bridge(self,bridge):
        self.bridges.remove(bridge)

    def get_thumbnail(self,size):
        if not size in self.thumbnails:
            self.thumbnails[size] = scipy.misc.imresize(self._rgb,size,"nearest","RGB")
        return self.thumbnails[size]

    def push(self,stage=None):
        if len(self.stages) >= self.stages_limit:
            self.stages.pop(0)

        if stage:
            self.stages.append(stage)
        else :
            self.stages.append(("_rgb",self._rgb.duplicate()))

    def pop(self):
        if len(self.stages) <= 0:
            return 

        stage = self.stages.pop()
        print stage

        if stage[0] == "_rgb":
            self._rgb[:,:,:] = stage[1]
        elif  stage[0] == "_fft":
            self._fft[:,:,:] = stage[1]

        self.rebuild(stage[0])
        self.refresh()

    @property
    def rgb(self):
        return self._rgbif

    @property
    def fft(self):
        return self._fftif

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

