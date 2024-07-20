import cv2
import numpy as np
import HandTrackingModule as htm
import time
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Controller as KeyboardController, Key
from screeninfo import get_monitors

class Mouse():
    def __init__(self, frameR=100, smoothening=5):
        super().__init__()
        self.frameR = frameR
        self.smoothening = smoothening
        self.pTime = 0
        self.plocX, self.plocY = 0, 0
        self.clocX, self.clocY = 0, 0
        
        self.cap = cv2.VideoCapture(1)
        self.wCam = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.hCam = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.detector = htm.HandDetector(maxHands=1)
        self.window_name = 'window_name'
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        
        self.running = True
        self.mouse_control = MouseController()
        for monitor in get_monitors():
            self.wScr = monitor.width
            self.hScr = monitor.height
        

    def run(self):
        while self.running:
            success, img = self.cap.read()
            img = cv2.flip(img, 1)
            allHands, img = self.detector.findHands(img)
            lmList, bbox = self.detector.findPosition(img)
            fingers = None

            if len(lmList) != 0:
                x1, y1 = lmList[8][1:]
                x2, y2 = lmList[12][1:]
                
                if allHands[0]['type'] == "Right":
                    fingers = self.detector.fingersUp(allHands[0])

                if fingers:
                    if fingers[1] == 1 and fingers[2] == 0:
                        x3 = np.interp(x1, (self.frameR, self.wCam - self.frameR), (0, self.wScr))
                        y3 = np.interp(y1, (self.frameR, self.hCam - self.frameR), (0, self.hScr))

                        self.clocX = self.plocX + (x3 - self.plocX) / self.smoothening
                        self.clocY = self.plocY + (y3 - self.plocY) / self.smoothening

                        self.mouse_control.position = (self.clocX, self.clocY)
                        self.plocX, self.plocY = self.clocX, self.clocY

                    elif fingers[1] == 1 and fingers[2] == 1:
                        length, lineInfo, img = self.detector.findDistance(8, 12, img)
                        if length < 30:
                            self.mouse_control.click(Button.left, 1)

            cTime = time.time()
            fps = 1 / (cTime - self.pTime)
            self.pTime = cTime
            
            cv2.rectangle(img, (self.frameR, 0), (self.wCam - self.frameR, self.hCam - self.frameR),
                              (255, 255, 255), 2)

            cv2.imshow(self.window_name, img)
            
            if cv2.waitKey(1) == ord('q'):
                self.running = False
                break
        
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    virtual_mouse = Mouse()
    virtual_mouse.run()
