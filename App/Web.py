from flask import Flask, render_template, Response, redirect, url_for, request, jsonify, send_file, session, g
import Camera
from flask_socketio import SocketIO, send, emit
import Surveillance
import json
import logging
from logging.handlers import RotatingFileHandler
import threading
import time
from random import random
import os
import sys
import cv2
import psutil

LOG_FILE = 'logs/WebApp.log'

# System Variables


# Initialises system variables, this object is the heart of the application
HomeSurveillance = Surveillance.SurveillanceSystem()

# Threads used to continuously push data to the client
facesUpdateThread = threading.Thread()
monitoringThread = threading.Thread()
facesUpdateThread.daemon = False
monitoringThread.daemon = False

# Flask setup
app = Flask('FacialRecognitionServer', template_folder='../Web/',
            static_url_path="", static_folder="../Web/assets/")
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app)


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route('/cameras', methods=['GET', 'POST'])
def cameras():
    return render_template('camera.html')

@app.route('/add_camera', methods=['POST'])
def add_camera():
    """Adds camera new camera to SurveillanceSystem's cameras array"""
    camURL = request.form.get('camURL')
    streamCheck = cv2.VideoCapture(camURL)
    ret,frame = streamCheck.read()
    if ret:
        with HomeSurveillance.camerasLock:
            HomeSurveillance.add_camera(Surveillance.Camera.IPCamera(camURL))
            HomeSurveillance.cameras[len(HomeSurveillance.cameras) - 1].start_camera()

        data = {"camNum": len(HomeSurveillance.cameras) - 1}
        return jsonify(data)
    data = {'error': 'No Stream found and this URL'}
    return jsonify(data)

@app.route('/video_streamer/<camNum>')
def video_streamer(camNum):
    """Used to stream frames to client, camNum represents the camera index in the cameras array"""
    return Response(genFrame(HomeSurveillance.cameras[int(camNum)]),
                    mimetype='multipart/x-mixed-replace; boundary=frame')  # A stream where each part replaces the previous part the multipart/x-mixed-replace content type must be used.

@app.route('/setcamera', methods=['POST'])
def setcamera():
    """Adds camera new camera to SurveillanceSystem's cameras array"""
    camNum = request.form.get('camID')
    action = request.form.get('action')

    if action == 'start':
        HomeSurveillance.cameras[int(camNum)].start_camera()

    if action == 'stop':
        HomeSurveillance.cameras[int(camNum)].stop_camera()

    data = {'success': 'Successful'}
    return jsonify(data)

def genFrame(camera):

    if camera.stop is True:
        frame = camera.read_processed()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

    while True:
        if camera.stop is True:
            frame = camera.read_processed()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
            break

        frame = camera.read_processed()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


def system_monitoring():
    """Pushes system monitoring data to client"""
    while True:
        cameraProcessingFPS = []
        for camera in HomeSurveillance.cameras:
            cameraProcessingFPS.append("{0:.2f}".format(camera.processingFPS))

        systemState = {'cpu': cpu_usage(), 'memory': memory_usage(),
                       'processingFPS': cameraProcessingFPS}
        socketio.emit('system_monitoring', json.dumps(
            systemState), namespace='/surveillance')
        time.sleep(3)


def cpu_usage():
    # ignore first call - often returns 0
    psutil.cpu_percent(interval=1, percpu=False)
    time.sleep(0.12)
    cpu_load = psutil.cpu_percent(interval=1, percpu=False)
    return cpu_load


def memory_usage():
    mem_usage = psutil.virtual_memory().percent
    return mem_usage

@socketio.on('connect', namespace='/surveillance')
def connect():
    global monitoringThread

    if not monitoringThread.isAlive():
        # print "Starting monitoringThread"
        app.logger.info("Starting monitoringThread")
        monitoringThread = threading.Thread(
            name='monitoring_process_thread_', target=system_monitoring, args=())
        monitoringThread.start()

    cameraData = {}
    cameras = []

    with HomeSurveillance.camerasLock:
        for i, camera in enumerate(HomeSurveillance.cameras):
            with HomeSurveillance.cameras[i].peopleDictLock:
                cameraData = {'camNum': i, 'url': camera.url}
                cameras.append(cameraData)

    systemData = {'camNum': len(HomeSurveillance.cameras),
                  'cameras': cameras, 'onConnect': True}
    socketio.emit('system_data', json.dumps(
        systemData), namespace='/surveillance')


@socketio.on('disconnect', namespace='/surveillance')
def disconnect():
    app.logger.info("Client disconnected")


if __name__ == '__main__':
    # Starts server on default port 5000 and makes socket connection available to other hosts (host = '0.0.0.0')
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = RotatingFileHandler(LOG_FILE, maxBytes=1000000, backupCount=10)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)

    log = logging.getLogger('noremac')
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)
    socketio.run(app, host='0.0.0.0', debug=True, use_reloader=False)
