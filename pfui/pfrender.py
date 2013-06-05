import scipy.misc
#import pyiptk as ip
from .pyiptk import gray2rgb,fft2spect,four_spect
from .pyiptk import rgb as iprgb
import numpy as np

def qimg(imarr):
    return np.clip(imarr,0,255).astype(np.uint8)

def qresize(im,out):
    if out.shape[0] == im.shape[0] and out.shape[1] == im.shape[1]:
        return out
    return scipy.misc.imresize(out,(im.shape[0],im.shape[1]))

def pfrender_ghpass(im,ins):
    if not "_origin" in ins.__dict__:
        return im
    
    t = qresize(im,ins._origin)
    return np.clip(im.astype(np.float)-t,0,255).astype(np.uint8)

def pfrender_fftps(im,ins):
    if ins.fft == None :
        return gray2rgb(four_spect(im))
    return qresize(im,gray2rgb(fft2spect(ins._fft)))

def pfrender_fft(im,ins):
    if ins.fft == None :
        return np.real(iprgb.fft2(im))
    return qresize(im,np.real(ins._fft).astype(np.uint8))

PfRender = {
    "RGB" : lambda im,ins : im,
    "R" : lambda im,ins : gray2rgb(im[:,:,0]),
    "G" : lambda im,ins : gray2rgb(im[:,:,1]),
    "B" : lambda im,ins : gray2rgb(im[:,:,2]),
    "FFTPS" : pfrender_fftps,
    "FFT" : pfrender_fft,
    "ghpass" : pfrender_ghpass,
}
