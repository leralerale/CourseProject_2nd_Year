#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
from collections import deque
from imutils.video import VideoStream
import numpy as np
import argparse
import cv2
import imutils
import time

M1_RIGHT = 4
M1_LEFT = 17
M2_RIGHT = 27
M2_LEFT = 22

def setup(*ports):
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    for port in ports:
        GPIO.setup(port, GPIO.OUT)
        GPIO.output(port, GPIO.LOW)

def stop_all():
    GPIO.output(M1_LEFT, GPIO.LOW)
    GPIO.output(M1_RIGHT, GPIO.LOW)
    GPIO.output(M2_LEFT, GPIO.LOW)
    GPIO.output(M2_RIGHT, GPIO.LOW)

def rotate(motor=1, mode='s'):
    stop_all()
    if motor == 1:
        if mode == 'r':
            GPIO.output(M1_RIGHT, GPIO.HIGH)
        elif mode == 'l':
            GPIO.output(M1_LEFT, GPIO.HIGH)
    elif motor == 2:
        if mode == 'r':
            GPIO.output(M2_RIGHT, GPIO.HIGH)
        elif mode == 'l':
            GPIO.output(M2_LEFT, GPIO.HIGH)

setup(M1_RIGHT, M1_LEFT, M2_RIGHT, M2_LEFT)

ap = argparse.ArgumentParser()
ap.add_argument("-b", "--buffer", type=int, default=32,
	help="max buffer size")
args = vars(ap.parse_args())
greenLower = (195, 100, 253)
greenUpper = (101, 56, 27)
pts = deque(maxlen=args["buffer"])
counter = 0
(dX, dY) = (0, 0)
direction = ""
if not args.get("video", False):
	vs = VideoStream(src=0).start()
else:
	vs = cv2.VideoCapture(args["video"])
time.sleep(2.0)

while True:
	frame = vs.read()
	frame = frame[1] if args.get("video", False) else frame
	if frame is None:
		break
	frame = imutils.resize(frame, width=600)
	blurred = cv2.GaussianBlur(frame, (11, 11), 0)
	hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
	mask = cv2.inRange(hsv, greenLower, greenUpper)
	mask = cv2.erode(mask, None, iterations=2)
	mask = cv2.dilate(mask, None, iterations=2)
	cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)
	center = None
	if len(cnts) > 0:
		c = max(cnts, key=cv2.contourArea)
		((x, y), radius) = cv2.minEnclosingCircle(c)
		M = cv2.moments(c)
		center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
		if radius > 10:
			cv2.circle(frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
			cv2.circle(frame, center, 5, (0, 0, 255), -1)
			pts.appendleft(center)
	for i in np.arange(1, len(pts)):
		if pts[i - 1] is None or pts[i] is None:
			continue
		if counter >= 10 and i == 1 and pts[-10] is not None:
			dX = pts[-10][0] - pts[i][0]
			dY = pts[-10][1] - pts[i][1]
			(dirX, dirY) = ("", "")
			if np.abs(dX) > 20:
				if np.sign(dX) == 1:
					dirX = "East"
				else:
					dirX = "West"
			# ensure there is significant movement in the y-direction
			if np.abs(dY) > 20:
				if np.sign(dY) == 1:
					dirY = "North"
					rotate(1, r)
					rotate(2, r)
				else:
					dirY = "South"
					rotate(1, l)
					rotate(2, l)
			# handle when both directions are non-empty
			if dirX != "" and dirY != "":
				direction = "{}-{}".format(dirY, dirX)
			# otherwise, only one direction is non-empty
			else:
				direction = dirX if dirX != "" else dirY
		thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
		cv2.line(frame, pts[i - 1], pts[i], (0, 0, 255), thickness)
	cv2.putText(frame, direction, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
		0.65, (0, 0, 255), 3)
	cv2.putText(frame, "dx: {}, dy: {}".format(dX, dY),
		(10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX,
		0.35, (0, 0, 255), 1)
	cv2.imshow("Frame", frame)
	key = cv2.waitKey(1) & 0xFF
	counter += 1


	if key == ord("q"):
		break
if not args.get("video", False):
	vs.stop()
else:
	vs.release()
cv2.destroyAllWindows()
