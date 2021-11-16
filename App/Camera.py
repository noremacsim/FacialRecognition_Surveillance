import threading
import time
import numpy as np
import cv2
import ImageUtils
import dlib
import openface
import os
import argparse
import logging
import Surveillance
import MotionDetector
import FaceDetector

HomeSurveillance = Surveillance.SurveillanceSystem()
logger = logging.getLogger(__name__)
fileDir = os.path.dirname(os.path.realpath(__file__))
modelDir = os.path.join(fileDir, '..', 'models')
assetImageDir = os.path.join(fileDir, '..', 'Web/assets/img')
dlibModelDir = os.path.join(modelDir, 'dlib')
openfaceModelDir = os.path.join(modelDir, 'openface')
parser = argparse.ArgumentParser()
parser.add_argument('--networkModel', type=str, help="Path to Torch network model.",default=os.path.join(openfaceModelDir, 'nn4.small2.v1.t7'))
parser.add_argument('--imgDim', type=int,help="Default image dimension.", default=96)
parser.add_argument('--cuda', action='store_true')
args = parser.parse_args()

CAPTURE_HZ = 30.0 # Determines frame rate at which frames are captured from IP camera

class IPCamera(object):
    def __init__(self,camURL):
        print("Loading Stream From IP Camera: " + camURL)
        self.motionDetector = MotionDetector.MotionDetector()
        self.faceDetector = FaceDetector.FaceDetector()
        self.processing_frame = None
        self.tempFrame = None
        self.captureFrame  = None
        self.streamingFPS = 0 # Streaming frame rate per second
        self.processingFPS = 0
        self.FPSstart = time.time()
        self.FPScount = 0
        self.motion = False # Used for alerts and transistion between system states i.e from motion detection to face detection
        self.people = {} # Holds person ID and corresponding person object
        self.trackers = [] # Holds all alive trackers
        self.rgbFrame = None
        self.faceBoxes = None
        self.captureEvent = threading.Event()
        self.captureEvent.set()
        self.peopleDictLock = threading.Lock() # Used to block concurrent access to people dictionary
        self.video = cv2.VideoCapture(camURL)
        self.url = camURL
        if not self.video.isOpened():
            self.video.open()
        self.placeholder = os.path.join(assetImageDir, 'stream_placeholder.jpg')
        self.stop = True
        self.captureLock = threading.Lock()

        # Start Camera Thread and append to HomeSurvilence Object
        thread = threading.Thread(name='frame_process_thread_' + str(len(HomeSurveillance.cameras)),target=self.get_frame, daemon=True)
        thread.daemon = True
        thread.start()
        thread.stop = False
        HomeSurveillance.cameraProcessingThreads.append(thread)

    def __del__(self):
        self.video.release()

    def get_frame(self):
        frame = None
        FPScount = 0
        FPSstart = time.time()

        while True:

            if self.stop is True:
                continue

            success, frame = self.video.read()
            self.captureEvent.clear()

            if not success:
                continue

            if success:
                self.captureFrame  = frame
                self.captureEvent.set()

            FPScount += 1

            if FPScount == 5:
                self.streamingFPS = 5/(time.time() - FPSstart)
                FPSstart = time.time()
                FPScount = 0


    def read_frame(self):
        capture_blocker = None
        frame = None
        capture_blocker = self.captureEvent.wait()
        frame = self.captureFrame
        return frame

    def read_processed(self):
        if self.stop is True:
            return open(self.placeholder, 'rb').read()

        frame = None
        jpeg  = None
        ret = None
        with self.captureLock:
            frame = self.read_frame()
        while frame is None:
            with self.captureLock:
                frame = self.read_frame()

        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tostring()

    def start_camera(self):
        self.stop = False

    def stop_camera(self):
        self.stop = True

