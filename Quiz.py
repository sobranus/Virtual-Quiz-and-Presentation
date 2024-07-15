import cv2
import csv
import time
import numpy as np
import cvzone
from cvzone.HandTrackingModule import HandDetector
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot


prev_time = 0

class Data():
    def __init__(self, data):
        self.question_text = data["question_text"]
        self.question_image = data["question_image"]
        self.choice_type = data["choice_type"]
        self.answer = int(data["answer"])
        self.choice1 = data["choice1"]
        self.choice2 = data["choice2"]
        self.choice3 = data["choice3"]
        self.choice4 = data["choice4"]

        self.chosen_answer = None

    def update(self, fingers):
        if fingers == [0, 1, 0, 0, 0]:  # Jika 1 jari diangkat
            self.chosen_answer = 1
        elif fingers == [0, 1, 1, 0, 0]:  # Jika 2 jari diangkat
            self.chosen_answer = 2
        elif fingers == [0, 1, 1, 1, 0]:  # Jika 3 jari diangkat
            self.chosen_answer = 3
        elif fingers == [0, 1, 1, 1, 1]:  # Jika 4 jari diangkat
            self.chosen_answer = 4
        elif fingers == [1, 1, 1, 1, 1]:  # Jika 5 jari diangkat
            self.chosen_answer = None
             
# cv2.namedWindow("img")
# cv2.setMouseCallback("img", on_mouse_click)

class Quiz(QThread):
    quiz_name_signal = pyqtSignal(str)
    frame_signal = pyqtSignal(np.ndarray)
    question_signal = pyqtSignal(int)
    reset_signal = pyqtSignal(int)
    command_signal = pyqtSignal(str)
    finish_signal = pyqtSignal(str, float)
    stop_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.detector = HandDetector(detectionCon=0.8, maxHands=2)
        self.video = cv2.VideoCapture(1)
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 1200)
        self.window_name = 'window_name'
        
        self.quiz_name = ''
        self.ardlist = []
        self.running = True
        self.qNo = 0
        self.score = 0
        self.qTotal = 0
        
        self.last_execution_time = time.time()
        self.cooldown_period = 3
        
        self.quiz_name_signal.connect(self.import_quiz_data)
        self.command_signal.connect(self.handle_command)
        self.stop_signal.connect(self.stop_quiz)
        
    def import_quiz_data(self, quiz_name):
        self.quiz_name = quiz_name
        with open(f'quiz/{self.quiz_name}.csv', newline='') as file:
            reader = csv.DictReader(file)
            data = list(reader)
        for q in data:
            self.ardlist.append(Data(q))
        self.qTotal = len(data)

    def run(self):
        while self.running:
            ret, frame = self.video.read()
            frame = cv2.flip(frame, 1)
            hands, img = self.detector.findHands(frame)
            current_time = time.time()

            if self.qNo < self.qTotal:
                ard = self.ardlist[self.qNo]

                if hands and len(hands) > 0:
                    # lmList = hands[0]['lmList']
                    fingers = self.detector.fingersUp(hands[0])
                    ard.update(fingers)
                    
                    if current_time - self.last_execution_time >= self.cooldown_period:
                        if ard.chosen_answer is not None:
                            self.qNo += 1
                            if self.qNo != self.qTotal:
                                self.question_signal.emit(self.qNo)
                                
                            self.last_execution_time = time.time()

            elif self.qNo == self.qTotal:
                self.score = sum(1 for ard in self.ardlist if ard.answer == ard.chosen_answer)
                self.score = round((self.score / self.qTotal) * 100, 2)
                self.finish_signal.emit(self.quiz_name, self.score)
                self.stop_quiz()
                
            self.frame_signal.emit(img)
            
        cv2.destroyAllWindows()
    
    @pyqtSlot(str)
    def handle_command(self, command):
        if command == "undo":
            if self.qNo >= 1:
                self.qNo -= 1
            self.question_signal.emit(self.qNo)
        elif command == "reset":
            self.qNo = 0
            self.score = 0
            self.reset_signal.emit(self.qNo)
            
        self.last_execution_time = time.time()
        
    def stop_quiz(self):
        self.running = False
        self.video.release()
        

if __name__ == "__main__":
    quiz_cv = Quiz()
    quiz_cv.run()
