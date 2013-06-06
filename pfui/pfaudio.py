import numpy as np
import scikits.audiolab as aulab
from .pfwindow import PfAudioView

class PfAudio(object):
    def __init__(self,filename,mode='r',format=None,channels=0,samplerate=0):
        if 'w' in mode:
            if '.wav' in filename:
                format = aulab.Format()
            elif '.ogg' in filename:
                format = aulab.Format(type="ogg",encoding="vorbis",endianness="file")

        self.snd = aulab.Sndfile(filename,mode=mode,format=format,\
                                 channels=channels,samplerate=samplerate)
        self.freq = self.snd.samplerate

        if 'w' not in mode:
            self.frames = self.snd.nframes
            self.data = self.snd.read_frames(self.frames)
            self.drawdata = None
            if self.snd.channels != 1:
                self.data = self.data[:,0]

        self.av,self.window = None,None
        #print self.snd
        
    def play(self,start=0,frames=0):
        if frames == 0:
            frames = self.frames
        aulab.play(self.data[start:frames],fs=self.freq)
    
    def view(self,width=1000,height=400):
        return PfAudioView(self,width,height,False)

    def view_all(self,width=1000,height=400):
        return PfAudioView(self,width,height)

    def edit(self,d):
        self.av = augtk.refresh(self.window,self.av,d)
        return augtk.AudioView(self,width,height,True)

