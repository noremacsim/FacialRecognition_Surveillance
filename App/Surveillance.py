import time
import argparse
import cv2
import os
import numpy as np
import dlib
import os.path
import sys
import logging
from logging.handlers import RotatingFileHandler
import threading
import time
import Camera
import openface
import ImageUtils


fileDir             = os.path.dirname(os.path.realpath(__file__))
luaDir              = os.path.join(fileDir, '..', 'batch-represent')
modelDir            = os.path.join(fileDir, '..', 'Data/models')
dlibModelDir        = os.path.join(modelDir, 'dlib')
openfaceModelDir    = os.path.join(modelDir, 'openface')

parser = argparse.ArgumentParser()
parser.add_argument('--dlibFacePredictor',type=str, help="Path to dlib's face predictor.",default=os.path.join(dlibModelDir , "shape_predictor_68_face_landmarks.dat"))
parser.add_argument('--networkModel',type=str, help="Path to Torch network model.",default=os.path.join(openfaceModelDir, 'nn4.small2.v1.t7'))
parser.add_argument('--imgDim', type=int, help="Default image dimension.", default=96)
parser.add_argument('--cuda', action='store_true')
parser.add_argument('--unknown', type=bool, default=False, help='Try to predict unknown people')
args = parser.parse_args()

start = time.time()
np.set_printoptions(precision=2)

logger = logging.getLogger()
formatter = logging.Formatter("(%(threadName)-10s) %(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = RotatingFileHandler("logs/surveillance.log", maxBytes=10000000, backupCount=10)

handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class SurveillanceSystem(object):
   def __init__(self):
        self.drawing = True
        self.camerasLock = threading.Lock()
        self.cameras = [] # Holds all system cameras
        self.cameraProcessingThreads = []

   def add_camera(self, camera):
        self.cameras.append(camera)
        self.cameraProcessingThreads.append(camera.thread)
        #thread = threading.Thread(name='frame_process_thread_' +
        #                         str(len(self.cameras)),
        #                         target=self.process_frame,
        #                         args=(self.cameras[-1],))
        #thread.daemon = False
        #self.cameraProcessingThreads.append(thread)
        #thread.start()

   def remove_camera(self, camID):
        self.cameras[int(camID)].stopThread = True
        self.cameraProcessingThreads[int(camID)].stop = True
        self.cameraProcessingThreads.pop(int(camID))
        self.cameras[int(camID)].stop_camera = True
        self.cameras[int(camID)].thread.stop  = True
        self.cameras.pop(int(camID))


   #def process_frame(self,camera):
   #     logger.debug('Processing Frames')

   #     state = 1
   #     frame_count = 0
   #     FPScount = 0
   #     FPSstart = time.time()
   #     start = time.time()
   #     #stop = camera.captureThread.stop

   #     while True:
   #         frame_count +=1
   #         frame = camera.read_frame()
   #         if frame is None or np.all(frame == camera.tempFrame):
   #             continue

            # Resize the frame for better processing performance
            # Look at a way of processing a smaller frame but overlay on a larger
            #frame = ImageUtils.resize(frame)

            # Frame rate calculation
   #         if FPScount == 6:
   #             camera.processingFPS = 6/(time.time() - FPSstart)
   #             FPSstart = time.time()
   #             FPScount = 0

   #         FPScount += 1
   #         camera.tempFrame = frame

            # We will process every 5th frame for detection there is avarage 20 frames
            # per input of cctv this means we will be detecting 4 times minimuim per second
            # and improve output
   #         if frame_count % 5 == 0:

                # Get FaceBoxes of the detected areas
   #             camera.faceBoxes = camera.faceDetector.detect_faces(frame,True)

                # If faces found is more than 0 well draw on frame
   #             if len(camera.faceBoxes) > 0:

                    # We Will Draw the Boxes around the faces on the frame
   #                 if self.drawing == True:
   #                     facialFrame = ImageUtils.draw_boxes(frame, camera.faceBoxes, True)
   #                     frame = facialFrame

   #             # TODO: Crop face from rendered area and submit to recognition service. We don't need todo
                # This live and can start a new thread so we arent slowing down the stream

   #        camera.processing_frame = frame