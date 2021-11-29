import cv2
import numpy as np
import os
import glob
import dlib
import sys
import argparse
from PIL import Image
import math
import datetime
import threading
import logging
import ImageUtils
import FaceDetector

class FaceExtracter(object):
    def __init__(self,image):
        self.imageCheck = image
        self.detectFace = FaceDetector.FaceDetector()
        self.faceBoxes  = 0

        self.faceBoxes = self.detectFace.detect_faces(self.imageCheck,False)
        if len(self.faceBoxes) > 0:
            print("Face Found")

        ## Start frame retrieval thread
        #self.thread = threading.Thread(target=self.extract_face, args=())
        #self.thread.daemon = True
        #self.thread.start()

    def extract_face(self):
        self.faceBoxes = self.detectFace.detect_faces(self.imageCheck,False)
        if len(self.faceBoxes) > 0:
            print("Face Found")
