#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# import the necessary packages
from collections import deque
from imutils.video import VideoStream
import numpy as np
import argparse
import cv2
import imutils
import time
import RPi.GPIO as GPIO

GPIO.setwarnings(False)

M1_RIGHT = 4
M1_LEFT = 17
M2_RIGHT = 27
M2_LEFT = 22

def setup(*ports):
    GPIO.cleanup()
    # Режим именования пинов по названию, а не по номеру на плате
    GPIO.setmode(GPIO.BCM)
    for port in ports:
        # Установка пина на вывод + низкий уровень "0"
        GPIO.setup(port, GPIO.OUT)
        GPIO.output(port, GPIO.LOW)

setup(M1_RIGHT, M1_LEFT, M2_RIGHT, M2_LEFT)

def stop_all():
    GPIO.output(M1_LEFT, GPIO.LOW)
    GPIO.output(M1_RIGHT, GPIO.LOW)
    GPIO.output(M2_LEFT, GPIO.LOW)
    GPIO.output(M2_RIGHT, GPIO.LOW)

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video",
    help="path to the (optional) video file")
ap.add_argument("-b", "--buffer", type=int, default=64,
    help="max buffer size")
args = vars(ap.parse_args())


# define the lower and upper boundaries of the "green"
# ball in the HSV color space, then initialize the
# list of tracked points
greenUpper = (195, 100, 153)
greenLower = (101, 56, 27) 
pts = deque(maxlen=args["buffer"])
# if a video path was not supplied, grab the reference
# to the webcam
if not args.get("video", False):
    vs = VideoStream(src=1).start()
# otherwise, grab a reference to the video file
else:
    vs = cv2.VideoCapture(args["video"])
# allow the camera or video file to warm up
time.sleep(0.5)

j = 0
# keep looping
while True:
    # grab the current frame
    frame = vs.read()
    # handle the frame from VideoCapture or VideoStream
    frame = frame[1] if args.get("video", False) else frame
    # if we are viewing a video and we did not grab a frame,
    # then we have reached the end of the video
    if frame is None:
        break
    # resize the frame, blur it, and convert it to the HSV
    # color space
    frame = imutils.resize(frame, width=600)
    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    # construct a mask for the color "green", then perform
    # a series of dilations and erosions to remove any small
    # blobs left in the mask
    mask = cv2.inRange(hsv, greenLower, greenUpper)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)


# find contours in the mask and initialize the current
    # (x, y) center of the ball
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    center = None
    # only proceed if at least one contour was found
    if len(cnts) > 0:
        # find the largest contour in the mask, then use
        # it to compute the minimum enclosing circle and
        # centroid
        c = max(cnts, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        M = cv2.moments(c)
        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        # only proceed if the radius meets a minimum size
        if radius > 10:
            # draw the circle and centroid on the frame,
            # then update the list of tracked points
            cv2.circle(frame, (int(x), int(y)), int(radius),
                (0, 255, 255), 2)
            cv2.circle(frame, center, 5, (0, 0, 255), -1)
    # update the points queue
    print(1)
    a = pts.appendleft(center)
    print(a)
    a = 3
    print(a)
    if a == True:
        j += 1
    if pts[j] is None or pts[j - 1] is None:
        break
    else:
        if (pts[j-1][1] - pts[j][1] < 100) and (pts[j-1][1] - pts[j][1] > -100):
            stop_all()
        elif pts[j-1][1] - pts[j][1] > 100:
            GPIO.output(27, GPIO. HIGH)
            GPIO.output(4, GPIO.HIGH)
            time.sleep(0.2)
            GPIO.output(27, GPIO.LOW)
            GPIO.output(4, GPIO.LOW)
            time.sleep(0.1)
        elif pts[j-1][1] - pts[j][1] < -100:
            GPIO.output(22, GPIO.HIGH)
            GPIO.output(17, GPIO.HIGH)
            time.sleep(0.2)
            GPIO.output(22, GPIO.LOW)
            GPIO.output(17, GPIO.LOW)
            time.sleep(0.1)

# loop over the set of tracked points
    for i in range(1, len(pts)):
        # if either of the tracked points are None, ignore
        # them
        if pts[i - 1] is None or pts[i] is None:
            continue        
        # otherwise, compute the thickness of the line and
        # draw the connecting lines
        thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
        cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)
    # show the frame to our screen
    #cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF
    # if the 'q' key is pressed, stop the loop
    if key == ord("q"):
        break
print(pts)
GPIO.cleanup()        
# if we are not using a video file, stop the camera video stream
if not args.get("video", False):
    vs.stop()
# otherwise, release the camera
else:
    vs.release()
# close all windows
cv2.destroyAllWindows()



