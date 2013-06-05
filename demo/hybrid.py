import pfui
import Image
import numpy as np
import scipy.ndimage as scii
from pfui.pfwindow import arr2pixbuf

#open/init
im = pfui.PfImage((300,400))
im.hi = np.asarray(Image.open("h1.jpg").convert("L"))
im.low = np.asarray(Image.open("h2.jpg").convert("L"))
im.rgb[:,:,:] = pfui.pyiptk.gray2rgb(im.low)

def hybrid_func(view,args,hi=im.hi,low=im.low):
    hi_t = scii.gaussian_filter(hi,args[0])
    hi = np.clip(hi.astype(np.int)-hi_t,0,255)
    low = scii.gaussian_filter(low,args[1])

    out = pfui.pyiptk.gray2rgb(np.clip(hi+low,0,255).astype(np.uint8))
    view.imagev.set_from_pixbuf(arr2pixbuf(out))
    view.nowimarr = out

w = pfui.pfwindow.PfsView(im,[pfui.qvar("hi-sigma",0,20),
                              pfui.qvar("low-sigma",0,20)],
                          hybrid_func)
