import cv2
import numpy as np
import HandTrackingModule as htm
import time
import pyautogui

class Mouse:
    def __init__(self, wCam=640, hCam=480, frameR=100, smoothening=5):
        self.wCam = wCam
        self.hCam = hCam
        self.frameR = frameR
        self.smoothening = smoothening
        self.pTime = 0
        self.plocX, self.plocY = 0, 0
        self.clocX, self.clocY = 0, 0
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, self.wCam)
        self.cap.set(4, self.hCam)
        self.detector = htm.handDetector(maxHands=1)
        self.wScr, self.hScr = pyautogui.size()
        self.running = True

    def run(self):
        while self.running:
            success, img = self.cap.read()
            img = cv2.flip(img, 1)
            img = self.detector.findHands(img)
            lmList, bbox = self.detector.findPosition(img)

            if len(lmList) != 0:
                x1, y1 = lmList[8][1:]
                x2, y2 = lmList[12][1:]

                fingers = self.detector.fingersUp()
                cv2.rectangle(img, (self.frameR, self.frameR), (self.wCam - self.frameR, self.hCam - self.frameR),
                              (255, 255, 255), 2)

                if fingers:
                    if fingers[0] == 1 and fingers[1] == 0:
                        x3 = np.interp(x1, (self.frameR, self.wCam - self.frameR), (0, self.wScr))
                        y3 = np.interp(y1, (self.frameR, self.hCam - self.frameR), (0, self.hScr))

                        self.clocX = self.plocX + (x3 - self.plocX) / self.smoothening
                        self.clocY = self.plocY + (y3 - self.plocY) / self.smoothening

                        pyautogui.moveTo(self.clocX, self.clocY)
                        cv2.circle(img, (x1, y1), 15, (0, 0, 255), cv2.FILLED)
                        self.plocX, self.plocY = self.clocX, self.clocY

                    elif fingers[0] == 1 and fingers[1] == 1:
                        length, img, lineInfo = self.detector.findDistance(8, 12, img)
                        if length < 30:
                            cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                            pyautogui.click()

            cTime = time.time()
            fps = 1 / (cTime - self.pTime)
            self.pTime = cTime
            cv2.putText(img, str(int(fps)), (20, 50), cv2.FONT_HERSHEY_PLAIN, 3,
                        (0, 255, 0), 3)

            cv2.imshow("Image", img)
            
            if cv2.waitKey(1) == ord('q'):
                self.running = False
                break
        
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    virtual_mouse = Mouse()
    virtual_mouse.run()



    
    
    
    