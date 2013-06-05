import pfui
import numpy as np
import scipy.ndimage as scii

#open
im = pfui.PfImage("lena.png")
im.origin()

#render
pfrender_highpass = lambda im,ins : pfui.qresize(im,pfui.qimg(ins._origin.astype(np.int)-ins._rgb))
pfrender_enhance = lambda im,ins : pfui.qresize(im,pfui.qimg(ins._origin.astype(np.int)*2-ins._rgb))

#window
im.window((3,1),(768,256),[["RGB"],[pfrender_highpass],[pfrender_enhance]])

#im.fft.do(scii.fourier_gaussian,4)

