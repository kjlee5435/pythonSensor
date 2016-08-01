#!/usr/bin/env python
import RPi.GPIO as GPIO
import subprocess
import threading
import picamera
import urllib
import logging
import logging.handlers
import requests
import time
from threading import Timer
from array import *
from time import sleep
usleep = lambda x: sleep(x/2000000.0)
current_milli_time = lambda: int(round(time.time() * 1000))

temperature = -1.0
humid = -1.0
my_logger = logging.getLogger('MyLogger')
LOG_FILENAME = '/var/log/sensor_working.log'
my_logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=1024000, backupCount=5)
my_logger.addHandler(handler)
lastTime = 0

def runSyncTimer():
    global my_logger    
    my_logger.debug(threading.currentThread())
    if (humid > 0) and (temperature > 0):
        urllib.urlopen("http://kjkj.me:8000/sensorLoggingApi/submit/?key=KgDWaHd3Vy8&humid={0}&temperature={1}".format(humid, temperature))
    Timer(5 * 60, runSyncTimer, ()).start()

def readDHT11():
    global humid, temperature, mylogger
    #tempSensor.out should be in /usr/bin
    p = subprocess.Popen(['tempSensor.out'], stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE)
    out, err = p.communicate()
    # Data format : RESULT, 33.0,27.0
    if "RESULT" in out:
        dataArray = out.split(",")
        humid = float(dataArray[1])
        temperature = float(dataArray[2])
    
    my_logger.debug(out)
    my_logger.debug("{0}, {1}".format(humid, temperature))
    my_logger.debug(threading.currentThread())
 
    if p.wait() != 0:
        my_logger.debug("There were some errors")
    
    # kill the process if open
    try:
        p.kill()
    except OSError:
        # can't kill a dead proc
        pass


def motion_callback(channel):
    global my_logger, lastTime

    my_logger.debug("[REC] in")

    timeGap = current_milli_time() - lastTime
    if timeGap < 60 * 5 * 1000:
        print("SKIP time gap = {0}".format(timeGap))
	return

    lastTime = current_milli_time()

    my_logger.debug("[REC] motion detect = {0}".format(GPIO.input(23)))
    my_logger.debug(threading.currentThread())

    p = subprocess.Popen(['rm', '-rf', 'video.mp4', 'video.h264'], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)

    if p.wait() != 0:
        my_logger.debug("There were some errors")

    # kill the process if open
    try:
        p.kill()
    except OSError:
        # can't kill a dead proc
        pass

    with picamera.PiCamera() as camera:
        camera.rotation = 90
        camera.start_recording('video.h264')
        camera.wait_recording(15)
        camera.stop_recording()
    
    my_logger.debug("[REC] Recording end")

    #convert h.264 to mp4
    p = subprocess.Popen(['MP4Box', '-add', 'video.h264', 'video.mp4'], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
    
    if p.wait() != 0:
        my_logger.debug("There were some errors")

    # kill the process if open
    try:
        p.kill()
    except OSError:
        # can't kill a dead proc
        pass
 
    my_logger.debug("[REC] mp4 converting end")
    #upload file to server
    url = "http://kjkj.me:8000/sensorLoggingApi/postfile/"
    files = {'upload_file': open('video.mp4','rb')}
    r = requests.post(url, files=files)
    my_logger.debug("[REC]upload end {0}".format(r))

def registerMotionCallback():
    MOTION = 23
    GPIO.setup(MOTION, GPIO.IN)
    GPIO.add_event_detect(MOTION, GPIO.RISING)
    GPIO.add_event_callback(MOTION, motion_callback)

def main():
    runSyncTimer()
    GPIO.setmode(GPIO.BCM)
    registerMotionCallback()
    while True:
        readDHT11()
        sleep(1)

if __name__ == "__main__":
    main()
