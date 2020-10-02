#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
    #GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    for port in ports:
        GPIO.setup(port, GPIO.OUT)
        GPIO.output(port, GPIO.LOW)

setup(M1_RIGHT, M1_LEFT, M2_RIGHT, M2_LEFT)

def stop_all():
    GPIO.output(M1_LEFT, GPIO.LOW)
    GPIO.output(M1_RIGHT, GPIO.LOW)
    GPIO.output(M2_LEFT, GPIO.LOW)
    GPIO.output(M2_RIGHT, GPIO.LOW)

ap = argparse.ArgumentParser()
ap.add_argument("-b", "--buffer", type=int, default=2,
    help="max buffer size")
args = vars(ap.parse_args())

greenUpper = (195, 100, 153)
greenLower = (101, 56, 27)
pts = deque(maxlen=args["buffer"])
vs = VideoStream(src=0).start()
time.sleep(0.5)
x_eps = 10

while True:
    frame = vs.read()
    if frame is None:
        break
    frame = imutils.resize(frame, width=600)
    blurred = cv2.GaussianBlur(frame, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

    mask = cv2.inRange(hsv, greenLower, greenUpper)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

# find contours in the mask and initialize the current
    # (x, y) center of the ball
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    center = None
    if len(cnts) > 0:
        # find the largest contour in the mask, then use
        # it to compute the minimum enclosing circle and
        # centroid
        c = max(cnts, key=cv2.contourArea)
        ((x, y), radius) = cv2.minEnclosingCircle(c)
        M = cv2.moments(c)
        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        if radius > 10:
            cv2.circle(frame, (int(x), int(y)), int(radius),
                (0, 255, 255), 2)
            cv2.circle(frame, center, 5, (0, 0, 255), -1)
    pts.appendleft(center)
    if len(pts) >= 2:
        if pts[0] is None or pts[1] is None:
            continue
        else:
            x_diff = pts[1][1] - pts[0][1]
            if (x_diff < x_eps) and (x_diff > x_eps):
                stop_all()
            elif x_diff > x_eps:
                GPIO.output(27, GPIO. HIGH)
                GPIO.output(4, GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(27, GPIO.LOW)
                GPIO.output(4, GPIO.LOW)
                time.sleep(0.1)
            elif x_diff < -x_eps:
            elif x_diff < -x_eps:
            elif x_diff < -x_eps:
                GPIO.output(22, GPIO.HIGH)
                GPIO.output(17, GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(22, GPIO.LOW)
                GPIO.output(17, GPIO.LOW)
                time.sleep(0.1)
# loop over the set of tracked points
    for i in range(1, len(pts)):
        if pts[i - 1] is None or pts[i] is None:
            continue
        thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
        cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
GPIO.cleanup()
vs.stop()
cv2.destroyAllWindows()



