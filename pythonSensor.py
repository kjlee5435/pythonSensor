#!/usr/bin/env python
import RPi.GPIO as GPIO
import subprocess
import threading
import picamera
import urllib
from threading import Timer
from array import *
from time import sleep
usleep = lambda x: sleep(x/2000000.0)

temperature = -1.0
humid = -1.0

def runSyncTimer():
    print(threading.currentThread())
    if (humid > 0) and (temperature > 0):
        urllib.urlopen("http://kjkj.me:8000/sensorLoggingApi/submit/?key=KgDWaHd3Vy8&humid={0}&temperature={1}".format(humid, temperature))
    Timer(5 * 60, runSyncTimer, ()).start()

def readDHT11():
    global humid, temperature
    p = subprocess.Popen(['./tempSensor.out'], stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE)
    out, err = p.communicate()
    # Data format : RESULT, 33.0,27.0
    if "RESULT" in out:
        dataArray = out.split(",")
        humid = float(dataArray[1])
        temperature = float(dataArray[2])
    
    print(out)
    print("{0}, {1}".format(humid, temperature))
    print(threading.currentThread())


def motion_callback(channel):
    print("motion detect = {0}".format(GPIO.input(23)))
    print(threading.currentThread())
    camera = picamera.PiCamera()
    camera.rotation = -90
    camera.start_recording('video.h264')
    sleep(15)
    camera.stop_recording()
    
    print("Recording end")


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
