import sys

from numpy.lib.shape_base import get_array_wrap
#use the local dji tellopy
sys.path.insert(0, './../')

from djitellopy import tello
import time
import cv2
import numpy as np

import keyPressModule as kp

DRONECAM = True  # using drone or computer cam

FRONTCAM = True  # get stream from front camera

if FRONTCAM:
    w, h = 360, 240  # width and height of video frame
else:
    w, h = 321, 240  # width and height of video frame

obstacle_shapes = {
    "none": 0,
    "rectangle": 1,
    "circle": 2,
    "triangle": 3 
}

def init(tello):
    """
        initializing the obstacle avoidance, should be called first before calling
        trackObject()
    """
    print("obstacle avoidance initializing...")

    if tello.is_flying is False:
        raise Exception('drone is not flying, can\'t start mission')

        # move to set height above the ground
    flight_height = 40  # fly at this level above the ground

    curr_height = tello.get_height()

    go_to_height_v = 0  # velocity for going to mission flight height
    if (flight_height - curr_height) > 0:
        go_to_height_v = 20
    else:
        go_to_height_v = -20

    while True:
        if kp.getKey("q"):  # Allow press 'q' to land in case of emergency
            tello.land()

        curr_height = tello.get_height()

        print(f'flying at {curr_height}cm')

        if curr_height == flight_height:
            tello.send_rc_control(0, 0, 0, 0)
            break

        tello.send_rc_control(0, 0, go_to_height_v, 0)

    print("Reached obstacle avoidance mission height of: {} cm".format(tello.get_height()))


def thresRed(img):
    """for thresholding the red color from the color image"""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask1 = cv2.inRange(hsv, np.array([0, 70, 50]), np.array([10, 255, 255]))
    mask2 = cv2.inRange(hsv, np.array([170, 70, 50]), np.array([180, 255, 255]))
    mask = mask1 | mask2
    return mask


def getContours(imgThres, img, color=(255, 0, 255)):
    """
    :param imgThres: black and white image with target from thresholding function
    :param img: colored image
    :return:
    """
    cx = 0
    area = 0
    white_to_black_ratio = -1
    contours, hierachy = cv2.findContours(imgThres, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if len(contours) != 0:
        biggest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(biggest)
        cx = x + w // 2
        cy = y + h // 2
        area = w * h  # area of bounding box

        if area < 10000: # threshold area for all shapes
            return cx, area, white_to_black_ratio # if area is below thres return
            
        cv2.drawContours(img, biggest, -1, color, 7)
        cv2.circle(img, (cx, cy), 10, (0, 255,), cv2.FILLED)

        # cut out the region of interest in the threshold
        roi = imgThres[y:(y+h), x:(x+w)]
        cv2.imshow("roi", roi)
        total_white_of_roi = cv2.countNonZero(roi)

        # get the  non white area inside the contour if any ie for cicle and triangle
        contour_mask = np.zeros((thresImg.shape[0], thresImg.shape[1], 1), dtype="uint8")
        cv2.fillConvexPoly(contour_mask, biggest, 255)
        ret, contour_mask = cv2.threshold(contour_mask, 127, 255, cv2.THRESH_BINARY)
        x, y, w, h = cv2.boundingRect(contour_mask)
        roi_contour_mask = contour_mask[y:(y + h), x:(x + w)]
        cv2.imshow("roi_contour_mask", roi_contour_mask)
        # total_white_inside_contour = cv2.countNonZero(roi_contour_mask)

        # black region inside region of interest
        roi_black = roi_contour_mask-roi
        black_inside_roi = cv2.countNonZero(roi_black)
        print(f"white:{total_white_of_roi}, black: {black_inside_roi}")
        cv2.imshow("black area", roi_black )

        # get ratio
        white_to_black_ratio = black_inside_roi/total_white_of_roi

    print(f"contour color: {color} center:{cx}, area:{area}, white/black ratio: {white_to_black_ratio}")

    return cx, area, white_to_black_ratio

def isEndMission(img):
    """check if there is a green ball to be followed in image"""


def getSensorOutput(cx, area):
    """
    get sensor output

    :param cx: center of found contour
    :param area: of found contour
    :return: senOut
    """
    imgs = np.hsplit(imgThres, sensors)
    totalPixels = imgThres.shape[1] // sensors * imgThres.shape[0]
    senOut = []
    for x, im in enumerate(imgs):
        pixelCount = cv2.countNonZero(im)
        if pixelCount > thresholdPixels * totalPixels:
            senOut.append(1)
        else:
            senOut.append(0)
        # cv2.imshow(str(x), im)
    print(senOut)

    return senOut

def sendCommands(tello, senOut, cx):
    """
    send commands to the tello drone

    :param senOut: sensor output
    :param cx: center of the detected yellow patch
    :return: None
    """
    # Translation
    lr = 0
    ud = 0
    fb = 0

    motionspeed = 15

    # Rotation
    if senOut == "up":
        ud = motionspeed
    elif senOut == "down":
        ud = -motionspeed
    elif senOut == "forward":
        fb = motionspeed
    elif senOut == "backward":
        fb = -motionspeed
    elif senOut == "left":
        lr = motionspeed
    elif senOut == "right":
        lr = -motionspeed

    print(f"moving up/down:{ud}, forward/backward:{fb}, left/right:{lr}")

    if DRONECAM:
        #tello.send_rc_control(lr, fb, ud, 0)
        _ = 0

def _avoidObstacles(tello,cap=None):
    """
        initializing the obstacle avoidance, should be called after calling
        init(), shouldn't be called outside this file
    """
    print("obstacle avoidance launched...")
    while True:
        if kp.getKey("q"):  # Allow press 'q' to land in case of emergency
            tello.land()

        if DRONECAM:
            img = tello.get_frame_read().frame

            if not FRONTCAM:
                img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
                cv2.imshow("output-0", img)

            print("got drone camera stream")

            gotStream = True
        else:
            _, img = cap.read()
            print("got web cam stream")

        if gotStream:
            avoidObstacles(tello, img)
            cv2.waitKey(1)
        else:
            print("waiting stream...")


def go_through_circle(tello):
    """ handles operation of going through the circle """
    print("submission going through circle launched...")


imgCount = 0 #image count

avoided_shapes = { #shapes that have been avoided
    "rectangle": False,
    "circle": False,
    "triangle": False
} 

def avoidObstacles(tello,frame):
    """
        initializing the obstacle avoidance, should be called after calling
        init()
    """
    print("obstacle avoidance launched...")

    img = cv2.resize(frame, (w, h)) #resize image

    imgThres = thresRed(img)  # color image thresholding

    # avoid obstacles
    cx, area, white_to_black_ratio = getContours(imgThres, img)  # image translation

    shape = obstacle_shapes["none"] #get trype of shape
    is_avoided = False #avoidance state

    #check if any red obstacle was detected
    if white_to_black_ratio == -1:  # no red obstacle
        return shape, is_avoided    # if no red obstacle return from here
    elif white_to_black_ratio > 1:  # circle or triagle
        if not avoided_shapes["rectangle"] and not avoided_shapes["circle"]  and not avoided_shapes["triangle"]:
            # this is a cirle
            go_through_circle(tello) 

             # by this time, we assume we have moved passed the triangle
            shape = obstacle_shapes["circle"] #get trype of shape
            is_avoided = True #avoidance state
            avoided_shapes["circle"] = True

        elif avoided_shapes["rectangle"]  and not avoided_shapes["circle"] and not avoided_shapes["triangle"]:
            # this is a cirle
            go_through_circle(tello)

            # by this time, we assume we have moved passed the triangle
            shape = obstacle_shapes["circle"] #get trype of shape
            is_avoided = True #avoidance state
            avoided_shapes["circle"] = True

        else:
            # this is a rectangle
            tello.move_right(20)
            tello.move_forward(20)
            tello.move_left(20)

             # by this time, we assume we have moved passed the triangle
            shape = obstacle_shapes["triangle"] #get trype of shape
            is_avoided = True #avoidance state
            avoided_shapes["triangle"] = True

    elif white_to_black_ratio < 1:  # rectangle detected, avoid it from the left side
        tello.move_right(50)
        tello.move_forward(20)
        tello.move_left(50)

        # by this time, we assume we have moved passed the rectangle
        shape = obstacle_shapes["rectangle"] #get trype of shape
        is_avoided = True #avoidance state
        avoided_shapes["rectangle"] = True

    senOut = getSensorOutput(cx, area) 

    sendCommands(tello, senOut, cx)

    # visualize progress
    cv2.imwrite("./image_feed/obstacle/" + str(imgCount) + ".jpg", img)
    imgCount = imgCount + 1
    # cv2.imshow("Thres", imgThres)

    return shape,is_avoided

      

def deinit():
    """
        deinitializing the obstacle avoidance mission
    """
    print("obstacle avoidance deinitializing...")


if __name__ == "__main__":
    kp.init()  # initialize pygame keypress module

    tello = tello.Tello()
    tello.connect()
    time.sleep(1)

    tello.streamon_front()
    time.sleep(3)

    print("battery level is {}".format(tello.get_battery()))

    tello.send_rc_control(0, 0, 0, 0)

    tello.takeoff()
    time.sleep(3)

    init(tello)
    _avoidObstacles(tello)
    deinit()
