"""
    Py Image Processing Tool Kit.
    
    It's a tool kit for my Multimedia course.
    Need some package : numpy,PIL,(scipy)
"""
import Image
import numpy as np
import scipy.ndimage as scii
from scipy import mgrid

def open2array(filename,gray=False):
    im = Image.open(filename)
    if gray:
        im = im.convert('L')
    return np.asarray(im)

def show_array(arr,autoastype=True):
    if autoastype:
        im = Image.fromarray(arr.astype(np.uint8))
    else :
        im = Image.fromarray(arr)
    im.show()

def four_spect(src):
    """Return Fourier Specturm (array).
    :src: can be a string as filename, or a array.
    """
    if isinstance(src,str):
        src = open2array(src)
    
    src = np.mean(src,2)
    return np.log( np.abs( np.fft.fftshift( np.fft.fft2(src) ) )+1 )**2

def fft2spect(src):
    src = np.mean(src,2)
    return np.log( np.abs( np.fft.fftshift(src) )+1 )**2


def ffts(arr):
    """ do fft2 and fftshift. """
    return np.fft.fftshift(np.fft.fft2(arr))

def iffts(arr):
    """ do ifftshift , ifft2 and real. """
    return np.real( np.fft.ifft2( np.fft.ifftshift(arr) ) )

class rgb:
    @staticmethod
    def fft2(arr):
        out = np.ndarray(arr.shape,dtype=np.complex)
        for i in range(3):
            out[:,:,i] = np.fft.fft2(arr[:,:,i])
        return out

    @staticmethod
    def fftshift(arr):
        out = np.ndarray(arr.shape,dtype=np.complex)
        for i in range(3):
            out[:,:,i] = np.fft.fftshift(arr[:,:,i])
        return out

    @staticmethod
    def ifft2(arr):
        out = np.ndarray(arr.shape,dtype=np.complex)
        for i in range(3):
            out[:,:,i] = np.fft.ifft2(arr[:,:,i])
        return out

    @staticmethod
    def ifftshift(arr):
        out = np.ndarray(arr.shape,dtype=np.complex)
        for i in range(3):
            out[:,:,i] = np.fft.ifftshift(arr[:,:,i])
        return out

    @staticmethod
    def ffts(arr):
        return rgb.fftshift(rgb.fft2(arr))

    @staticmethod
    def iffts(arr):
        return rgb.ifft2(rgb.ifftshift(arr))

    @staticmethod
    def convolve(arr1,arr2):
        out = np.ndarray(arr1.shape,dtype=np.double)
        for i in range(3):
            out[:,:,i] = scii.convolve(arr1[:,:,i],arr2)
        return out

    @staticmethod
    def do(func,arr,*args):
        out = np.ndarray(arr.shape,dtype=arr.dtype)
        for i in range(3):
            out[:,:,i] = func(arr[:,:,i],*args)
        return out

    @staticmethod
    def phase2complex(arr):
        out = np.ndarray(arr.shape,dtype=np.complex)
        for r in range(arr.shape[0]):
            for c in range(arr.shape[1]):
                for i in range(3):
                    out[r][c][i] = np.cos(arr[r][c][i])+1j*np.sin(arr[r][c][i])
        return out

def array_gray(arr):
    """ too slow,may need write in c. """
    out = np.ndarray(arr.shape[:2],dtype=np.uint8,order='C')
    for r in range(arr.shape[0]) :
        for c in range(arr.shape[1]):
            R = arr[r][c][0]
            G = arr[r][c][1]
            B = arr[r][c][2]

            out[r][c] = 0.299*R+0.587*G+0.114*B

    return out

def gray2rgb(arr):
    out = np.ndarray((arr.shape[0],arr.shape[1],3),dtype=arr.dtype)
    for i in range(3):
        out[:,:,i] = arr
    return out

class filter:
    @staticmethod
    def filowp(arr,rad):
        h = arr.shape[0]
        w = arr.shape[1]
        R = rad*rad
        out = np.ndarray(arr.shape,dtype=arr.dtype)
        for r in range(0,h):
            for c in range(0,w):
                x = c-w/2
                y = r-h/2

                if x*x + y*y > R :
                    out[r][c] = 0
                else :
                    out[r][c] = arr[r][c]
        return out

    @staticmethod
    def fihighp(arr,rad):
        h = arr.shape[0]
        w = arr.shape[1]
        R = rad*rad
        out = np.ndarray(arr.shape,dtype=arr.dtype)
        for r in range(0,h):
            for c in range(0,w):
                x = c-w/2
                y = r-h/2

                if x*x + y*y > R :
                    out[r][c] = arr[r][c]
                else :
                    out[r][c] = 0
        return out

def gauss_kern(size, sizey=None):
    """ Returns a normalized 2D gauss kernel array for convolutions """
    size = int(size)
    if not sizey:
        sizey = size
    else:
        sizey = int(sizey)
    x, y = mgrid[-size:size+1, -sizey:sizey+1]
    g = np.exp(-(x**2/float(size)+y**2/float(sizey)))
    return g / g.max()

def gauss_kern2(size, sizey=None):
    """ Returns a normalized 2D gauss kernel array for convolutions """
    size = int(size)
    if not sizey:
        sizey = size
    else:
        sizey = int(sizey)
    x, y = mgrid[-size:size+1, -sizey:sizey+1]
    g = np.exp(-(x**2/float(size)+y**2/float(sizey)))
    return g / g.sum()
