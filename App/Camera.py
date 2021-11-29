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
import FaceDetector
import FaceExtracter

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

        self.detectFace = FaceDetector.FaceDetector()

        self.processing_frame = None
        self.tempFrame = None
        self.captureFrame  = None
        self.count = 0

        self.peopleDictLock = threading.Lock() # Used to block concurrent access to people dictionary
        self.captureEvent = threading.Event()
        self.captureEvent.set()

        # Variables
        self.url = camURL
        self.placeholder = os.path.join(assetImageDir, 'stream_placeholder.jpg')
        self.stop = True
        self.stopThread = False
        self.captureLock = threading.Lock()

        # Stream Capture Details and settings
        self.video = cv2.VideoCapture(camURL)
        self.video.set(cv2.CAP_PROP_BUFFERSIZE, 3)
        self.FPS = 1/30
        self.FPS_MS = int(self.FPS * 1000)
        if not self.video.isOpened():
            self.video.open()

        # Start frame retrieval thread
        self.thread = threading.Thread(target=self.get_frame, args=())
        self.thread.daemon = True
        self.thread.start()

    def __del__(self):
        self.video.release()

    # Get frame from video Stream and save to global captureFrame
    def get_frame(self):
        # Set FPS of the stream
        self.FPS = 1/self.video.get(cv2.CAP_PROP_FPS)

        while True:
            if self.stop is True:
                continue

            if self.video.isOpened():
                (self.status, frame) = self.video.read()
                self.captureFrame = ImageUtils.resize(frame)
                threading.Thread(target=self.extract_face).start()


                if not self.status:
                    continue

                self.captureEvent.set()


            if self.stopThread is True:
                break
            time.sleep(self.FPS)

    # Read standard frame
    def read_frame(self):
        capture_blocker = None
        frame = None
        capture_blocker = self.captureEvent.wait()
        frame = self.captureFrame
        return frame

    # Read Frame After ot has been processed
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

    def extract_face(self):
        self.faceBoxes = self.detectFace.detect_faces(self.captureFrame,False)
        if len(self.faceBoxes) > 0:
            frame = ImageUtils.draw_boxes(self.captureFrame, self.faceBoxes, False)
            for face_bb in self.faceBoxes:
                x, y, w, h = face_bb
                face_bb = dlib.rectangle(int(x), int(y), int(x+w), int(y+h))
                faceimg = ImageUtils.crop(self.captureFrame, face_bb, dlibRect = True)
                #if len(self.detectFace.detect_cascadeface_accurate(faceimg)) == 0:
                #    continue
                print("Face Found")
                cv2.imwrite("test/frame-%d.jpg" % self.count, frame)     # save frame as JPEG file
                cv2.imwrite("test/face-%d.jpg" % self.count, faceimg)     # save frame as JPEG file
                self.count += 1


