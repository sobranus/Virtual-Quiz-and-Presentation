import math
import time
import cv2
import numpy as np
from HandTrackingModule import HandDetector
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController
from screeninfo import get_monitors
from PyQt5.QtCore import QThread, pyqtSignal

class Presentation(QThread):
    frame_signal = pyqtSignal(np.ndarray)
    finished = pyqtSignal()
    stop_presentation = pyqtSignal()
    
    def __init__(self, camera_source=0, smoothening=5):
        super().__init__()
        self.frameX = 150
        self.frameY = 125
        self.smoothening = smoothening
        self.plocX, self.plocY = 0, 0
        self.clocX, self.clocY = 0, 0
        
        self.cap = cv2.VideoCapture(camera_source)
        self.detector = HandDetector(maxHands=1)
        self.wCam = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.hCam = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.window_name = 'window_name'
        
        self.key_mode = False
        self.detected_answer = str()
        self.running = True
        self.last_execution_time = time.time()
        self.detection_time = time.time()
        self.cooldown = time.time()
        self.double_detection = False
        self.mouse_control = MouseController()
        self.key_control = KeyboardController()
        for monitor in get_monitors():
            self.wScr = monitor.width
            self.hScr = monitor.height
            
        self.stop_presentation.connect(self.stop)
            
    def key_detection(self, hand):
        current_time = time.time()
            
        if current_time > self.cooldown + 1:
            if not self.double_detection:
                self.detected_answer = self.key_check(hand)
                self.detection_time = time.time()
                self.double_detection = True
                
            elif current_time > self.detection_time + 1:
                key = self.key_check(hand)
                if self.detected_answer == key:
                    if hand['type'] == "Right":
                        if key == 'esc':
                            self.press_key(Key.esc)
                        elif key == 'b':
                            self.press_key('b')
                        elif key == 'right':
                            self.press_key(Key.right)
                        elif key == 'left':
                            self.press_key(Key.left)
                        elif key == 'switch':
                            self.key_mode = False
                        print(key)
                        if key:
                            self.cooldown = time.time()
                        
                self.double_detection = False
            
    def key_check(self, hand):
        tips_up = self.detector.tipsUp(hand)
        tips_side = self.detector.tipsSide(hand)
        fingers_up = self.detector.fingersUp(hand)
        fingers_side = self.detector.fingersSide(hand)
        thumb_above_mid_tip = self.detector.thumbsAboveMidTip(hand)
        thumb_right_point = self.detector.thumbsRightPoint(hand)
        key = str()
        
        if tips_up[0] == 1 and tips_up[1] == 0 and tips_side[0] == 1 and thumb_right_point == 1:
            key = 'esc'
        elif tips_up[1] == 1 and tips_up[4] == 1 and fingers_side == 1 and thumb_above_mid_tip == 0 and thumb_right_point == 1:
            key = 'b'
        elif tips_side[1] == 1 and tips_side[4] == 0 and fingers_up == 1 and thumb_above_mid_tip == 1:
            key = 'right'
        elif tips_side[1] == 0 and tips_side[4] == 1 and fingers_up == 1 and thumb_above_mid_tip == 1:
            key = 'left'
        elif tips_up[1] == 1 and tips_up[4] == 0 and tips_up[0] == 1 and fingers_side == 1:
            key = 'switch'
            
        return key
                
    def press_key(self, key):
        self.key_control.press(key)
        self.key_control.release(key)
        
    def cursor_control(self, img):
        current_time = time.time()
        hands, img = self.detector.findHands(img)
        lmList, bbox = self.detector.findPosition(img, draw=False, drawTip=1)
        fingers = []
        if len(lmList) != 0:
            x1, y1 = lmList[8][1:]
            
            if hands[0]['type'] == "Right":
                fingers = self.detector.tipsUp(hands[0])

            if fingers:
                if fingers[0] == 1:
                    x3 = np.interp(x1, (25, self.wCam - self.frameX), (0, self.wScr))
                    y3 = np.interp(y1, (25, self.hCam - self.frameY), (0, self.hScr))

                    self.clocX = self.plocX + (x3 - self.plocX) / self.smoothening
                    self.clocY = self.plocY + (y3 - self.plocY) / self.smoothening

                    self.mouse_control.position = (self.clocX, self.clocY)
                    self.plocX, self.plocY = self.clocX, self.clocY
                
                elif fingers[0] == 0:
                    if current_time - self.last_execution_time >= 0.4:
                        if fingers[1] == 0:
                            self.mouse_control.click(Button.left, 1)
                            self.last_execution_time = time.time()
                        elif fingers[2] == 0:
                            self.mouse_control.click(Button.right, 1)
                            self.last_execution_time = time.time()
                        elif fingers[4] == 1:
                            if not self.double_detection:
                                self.double_detection = True
                                self.detection_time = time.time()
                            elif current_time > self.detection_time + 1.5:
                                self.key_mode = True
                                self.double_detection = False

    def run(self):
        while self.running:
            success, img = self.cap.read()
            img = cv2.flip(img, 1)
            
            if self.key_mode:
                hands, img = self.detector.findHands(img)
                if hands:
                    hand = hands[0]
                    self.key_detection(hand)
                
            else:
                self.cursor_control(img)
                cv2.rectangle(img, (25, 25), (self.wCam - self.frameX, self.hCam - self.frameY),
                              (255, 255, 255), 1)
                cv2.putText(img, "screen", (25, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                            (255, 255, 255), 1)
            
            self.frame_signal.emit(img)
            
            if cv2.waitKey(1) == ord('q'):
                self.stop()
                
        self.cap.release()
        cv2.destroyAllWindows()
        
    def stop(self):
        self.running = False
        self.finished.emit()
        

