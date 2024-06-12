import numpy as np
import math
import cv2
from cvzone.HandTrackingModule import HandDetector

cap = cv2.VideoCapture(0)
detector = HandDetector(maxHands=1)

offset = 20
img_size = 300

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print("Image size:", width, "x", height)

while True:
    success, img = cap.read()
    hands, img = detector.findHands(img)
    
    if hands:
        hand = hands[0]
        x, y, w, h = hand['bbox']
        aspect_ratio = h / w
        
        img_white = np.ones((img_size, img_size, 3), np.uint8)
        if x - offset >= 0 and y - offset >= 0:
            img_crop = img[y-offset : y + h+offset, x-offset : x + w+offset]
        elif x - offset < 0 and y - offset >= 0:
            img_crop = img[y-offset : y + h+offset, 0 : x + w+offset]
        elif x - offset >= 0 and y - offset < 0:
            img_crop = img[0 : y + h+offset, x-offset : x + w+offset]
        else:
            img_crop = img[0 : y + h+offset, 0 : x + w+offset]
        
        if np.any(img_crop):
            if aspect_ratio > 1:
                k = img_size / h
                w_cal = math.floor(k * w)
                img_resize = cv2.resize(img_crop, (w_cal, img_size))
                img_resize_shape = img_resize.shape
                w_gap = math.ceil((img_size - w_cal)/2)
                img_white[:, w_gap:w_cal + w_gap] = img_resize
                
            elif aspect_ratio < 1:
                k = img_size / w
                h_cal = math.floor(k * h)
                img_resize = cv2.resize(img_crop, (img_size, h_cal))
                img_resize_shape = img_resize.shape
                h_gap = math.ceil((img_size - h_cal)/2)
                img_white[h_gap:h_cal + h_gap, :] = img_resize
        
        cv2.imshow("imageWhite", img_white[:, ::-1])
    
    cv2.imshow("image", img[:, ::-1])
    cv2.waitKey(1)
    