import numpy as np
import math
import time
import cv2
from HandTrackingModule import HandDetector

cap = cv2.VideoCapture(0)
detector = HandDetector(maxHands=1)

offset = 20
img_size = 300

folder = "data"
counter = 0

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print("Image size:", width, "x", height)

while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)
    hands, img, blankImg = detector.findHands(img, getBlank=True, draw=False)
    
    if hands:
        hand = hands[0]
        x, y, w, h = hand['bbox']
        aspect_ratio = h / w
        
        img_blank = np.ones((img_size, img_size, 3), np.uint8)
        if x - offset >= 0 and y - offset >= 0:
            img_crop = blankImg[y-offset : y + h+offset, x-offset : x + w+offset]
        elif x - offset < 0 and y - offset >= 0:
            img_crop = blankImg[y-offset : y + h+offset, 0 : x + w+offset]
        elif x - offset >= 0 and y - offset < 0:
            img_crop = blankImg[0 : y + h+offset, x-offset : x + w+offset]
        else:
            img_crop = blankImg[0 : y + h+offset, 0 : x + w+offset]
        
        if np.any(img_crop):
            if aspect_ratio > 1:
                k = img_size / h
                w_cal = math.floor(k * w)
                img_resize = cv2.resize(img_crop, (w_cal, img_size))
                img_resize_shape = img_resize.shape
                w_gap = math.ceil((img_size - w_cal)/2)
                img_blank[:, w_gap:w_cal + w_gap] = img_resize
                
            elif aspect_ratio < 1:
                k = img_size / w
                h_cal = math.floor(k * h)
                img_resize = cv2.resize(img_crop, (img_size, h_cal))
                img_resize_shape = img_resize.shape
                h_gap = math.ceil((img_size - h_cal)/2)
                img_blank[h_gap:h_cal + h_gap, :] = img_resize
        
        cv2.imshow("imageWhite", img_blank)
    
    gray_frame = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imshow("image", gray_frame)
    key = cv2.waitKey(1)
    if key == ord("s"):
        counter += 1
        cv2.imwrite(f'{folder}/image_{time.time()}.jpg', img_blank)
        print(counter)