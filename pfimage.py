import Image
import numpy as np
import scipy.misc

import pyiptk as ip

#from pfwindow import PfWindow,PfBridge,PfRender,window_templates
from pfwindow import *

class PfRGB_Interface(object):
    def __init__(self,ins,name):
        self.ins = ins
        self.name = name
        self.autore(True)

    def __getitem__(self,key):
        return self.ins.__getattribute__(self.name).__getitem__(key)

    def __setitem__(self,key,value):
        if self.autopush :
            self.ins.push()
        
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
        self.ins.push()
        self[:,:,0] = func(self[:,:,0],*args)
        self[:,:,1] = func(self[:,:,1],*args)
        self[:,:,2] = func(self[:,:,2],*args)
        self.autore(True)
        
        self.ins.rebuild(self.name)
        self.ins.refresh()

class PfImage(object):
    @staticmethod
    def __create(indata):
        #filename
        if isinstance(indata,str):
            indata = Image.open(indata)
        
        #Image
        if isinstance(indata,Image.Image):
            if indata.mode != "RGB":
                indata = indata.convert("RGB")
            rgb = np.asarray(indata).copy()

        #np.ndarray
        elif isinstance(indata,np.ndarray) and len(indata.shape) == 3 and indata.shape[2] == 3:
            rgb = indata.copy()

        #PfImage
        elif isinstance(indata,PfImage):
            rgb = indata.rgb.duplicate()

        #Tuple(row,col) , an empty image
        elif isinstance(indata,tuple) and len(indata) == 2 and \
             isinstance(indata[0],int) and isinstance(indata[1],int):
            rgb = np.ndarray((indata[0],indata[1],3),dtype=np.uint8)
            rgb[:,:,:] = 0

        else :
            raise Exception("Not supported type.")

        return rgb

    def __init__(self,im,fft=True):
        rgb = PfImage.__create(im)
        
        self._rgb = rgb
        self._rgbif = PfRGB_Interface(self,"_rgb")
        
        self.fftsupport = fft
        if fft :
            self._fft = ip.rgb.fft2(rgb)
            self._fftif = PfRGB_Interface(self,"_fft")
        else :
            self._ffiif = None

        self.bridges = []
        self.thumbnails = {}

        # stages
        self.stages = []
        self.rstages = []
        self.stages_limit = 5
        #self.windows = []

    @property
    def rgb(self):
        return self._rgbif

    @property
    def fft(self):
        return self._fftif

    def refresh(self,changed=None):
        if changed == None :
            for bridge in self.bridges :
                #_taskworker.add_task(bridge.refresh)
                bridge.refresh()

    def rebuild(self,name):
        self.thumbnails = {} # clean thumbnail

        if not self.fftsupport :
            return 

        if name == "_rgb":
            self._fft = ip.rgb.fft2(self._rgb)
        elif name == "_fft":
            self._rgb = np.real(ip.rgb.ifft2(self._fft)).astype(np.uint8)
    
    def add_bridge(self,bridge):
        self.bridges += [bridge]

    def remove_bridge(self,bridge):
        self.bridges.remove(bridge)

    def get_thumbnail(self,size):
        if not size in self.thumbnails:
            self.thumbnails[size] = scipy.misc.imresize(self._rgb,size,"nearest","RGB")
        return self.thumbnails[size]

    #Window
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

    def view(self,tname="basic",size=None,scale=1,name="Image"):
        if isinstance(tname,str):
            if not tname in window_templates:
                return 
            template = window_templates[tname]
        elif isinstance(tname,tuple) and len(tname) == 2 :
            template = tname

        if size == None :
            size = (self._rgb.shape[0]*scale,self._rgb.shape[1]*scale)

        size = (int(size[0]*template[0][0]),int(size[1]*template[0][1]))

        return self.window(template[0],size,template[1],name)
    
    #Stage
    def push(self,stage=None):
        if len(self.stages) >= self.stages_limit:
            self.stages.pop(0)
        
        # clean redo list
        del self.rstages
        self.rstages = []

        if stage:
            self.stages.append(stage)
        else :
            self.stages.append(self.rgb.duplicate())

    def pop(self,stack,astack):
        if len(stack) <= 0:
            return False

        astack.append(self.rgb.duplicate())

        stage = stack.pop()
        self._rgb[:,:,:] = stage

        self.rebuild("_rgb")
        self.refresh()
        return True

    def undo(self):
        return self.pop(self.stages,self.rstages)

    def redo(self):
        return self.pop(self.rstages,self.stages)
    
    #Misc
    def get_resize(self,size,mod="bilinear"):
        return scipy.misc.imresize(self._rgb,size,mod)

