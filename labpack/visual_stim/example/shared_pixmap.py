from stimpack.visual_stim.shared_pixmap import SharedPixMapStimulus
from stimpack.visual_stim.stimuli import BaseProgram

from multiprocessing import shared_memory
import os
import glob
import multiprocessing
import cv2
import numpy as np
import time
import sched
import threading


class StreamMovie(SharedPixMapStimulus):
    def __init__(self, memname, filepath, nominal_frame_rate, duration, start_frame=0):
        dur = duration

        self.nominal_frame_rate = nominal_frame_rate
        self.dur = dur
       
        self.cap = cv2.VideoCapture(filepath)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        ret = False

        while ret is False:
            ret, frame = self.cap.read()

        dummy = np.zeros(frame.shape)*255
        dummy = dummy.astype(np.uint8)

        self.frame_shape = frame.shape
        super().__init__(memname = memname, shape=self.frame_shape)

        self.load_stream()
        
        # check if temp file exists
        # if so, delete it
        # if not, create it
        # make a config directory

    def genframe(self):
        ret = False

        while ret is False:
            ret, img = self.cap.read()
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.uint8)

        fr = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        self.global_frame[:] = img

        t = time.time() - self.t
        with open(self.filepath, 'a') as f:
            f.write(str(fr)+' '+str(t)+'\n')

