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
        self.ins.__getattribute__(self.name).__setitem__(key,value)

        if self.rebuild :
            self.ins.rebuild(self.name)
        if self.refresh :
            self.ins.refresh()

    def autore(self,enable):
        self.refresh = enable
        self.rebuild = enable

    def duplicate(self):
        return self[:,:,:].copy()

    def do(self,func,*args):
        self.autore(False)
        self[:,:,0] = func(self[:,:,0],*args)
        self[:,:,1] = func(self[:,:,1],*args)
        self[:,:,2] = func(self[:,:,2],*args)
        self.autore(True)

        self.ins.rebuild(self.name)
        self.ins.refresh()

class PfBridge:
    def __init__(self,ins,name,viewer,index):
        self.name = name
        self.ins = ins
        self.viewer = viewer
        self.index = index

        self.viewer.add_bridge(self)
        self.refresh()

    def refresh(self):
        self.viewer.view(self.index,self.ins.get_field(self.name))

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
        #self.windows = []

        self.field_dict = {
            "_rgb" : lambda x : x._rgb ,
            "_fft" : lambda x : np.real(x._fft),
            "_fft_ps" : lambda x : ip.gray2rgb(ip.fft2spect(x._fft)) ,
            "_r" : lambda x : ip.gray2rgb(x._rgb[:,:,0]) ,
            "_g" : lambda x : ip.gray2rgb(x._rgb[:,:,1]) ,
            "_b" : lambda x : ip.gray2rgb(x._rgb[:,:,2]) ,
        }

    def refresh(self,changed=None):
        if changed == None :
            for bridge in self.bridges :
                bridge.refresh()

    def rebuild(self,name):
        if name == "_rgb":
            self._fft = ip.rgb.fft2(self._rgb)
        elif name == "_fft":
            self._rgb = np.real(ip.rgb.ifft2(self._fft)).astype(np.uint8)

    def get_field(self,name):
        if name in self.field_dict :
            return self.field_dict[name](self)

    def view(self,shape,window_size,imgs):
        window = PfWindow(window_size,shape)
        #self.windows += [window]

        for r in range(len(imgs)):
            for c in range(len(imgs[r])):
                bridge = PfBridge(self,imgs[r][c],window,(r,c))
                self.add_bridge(bridge)

        return window

    def add_bridge(self,bridge):
        self.bridges += [bridge]

    def remove_bridge(self,bridge):
        self.bridges.remove(bridge)

    @property
    def rgb(self):
        return self._rgbif

    @property
    def fft(self):
        return self._fftif
    
    """
    @rgb.setter
    def rgb(self,val):
        if isinstance(val,np.ndarray) :
            if self._rgb.shape == val.shape :
                self._rgb = val.copy()
                self.refresh()
        elif isinstance(val,PfRGB_Interface):
            self.refresh()
            self._rgb = val.ins._rgb.copy()
    """

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
        isize = self.get_imsize((imarr.shape[0],imarr.shape[1]))
        im = scipy.misc.imresize(imarr,isize,"nearest","RGB")
        self.imagev[ind[0]][ind[1]].set_usize(isize[1],isize[0])
        self.imagev[ind[0]][ind[1]].set_from_pixbuf(
                        gtk.gdk.pixbuf_new_from_array(np.clip(im,0,255).astype(np.uint8),
                        gtk.gdk.COLORSPACE_RGB,8))

