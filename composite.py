import sys
import os
import shutil
import math
import time
import numpy as np
import csv
import cv2
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController
from screeninfo import get_monitors
from tensorflow.keras.models import load_model
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog
from PyQt5.QtGui import QPixmap, QImage, QIcon
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal, pyqtSlot
from HandTrackingModule import HandDetector


for i in range(3, -1, -1):
    video = cv2.VideoCapture(i)
    if video.isOpened():
        available_camera = i
        break

def fit_pixmap(pixmap, label_height, label_width):
    width = pixmap.width()
    height = pixmap.height()
    pixmap_aspect_ratio = height / width
    label_aspect_ratio = label_height / label_width
    
    if pixmap_aspect_ratio > label_aspect_ratio:
        k = label_height / height
        w_cal = math.floor(k * width)
        img_resize = pixmap.scaled(w_cal, label_height)
        
    elif pixmap_aspect_ratio <= label_aspect_ratio:
        k = label_width / width
        h_cal = math.floor(k * height)
        img_resize = pixmap.scaled(label_width, h_cal)
        
    return img_resize



class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        loadUi("ui/main_window.ui", self)
        
        self.available_camera = available_camera
        self.original_geometry = self.geometry()
        self.presentation = Presentation(camera_source=self.available_camera)
        self.key_control = KeyboardController()
        self.presentation.frame_signal.connect(self.computer_vision)
        self.presentation.finished.connect(self.show_menu)
        self.label.hide()
        self.pushButton_3.hide()
        
        self.pushButton.clicked.connect(self.to_presentation)
        self.pushButton_2.clicked.connect(self.to_quiz_menu)
        self.pushButton_3.clicked.connect(self.stop_presentation)
        self.pushButton_4.clicked.connect(self.close_app)
        
    def to_quiz_menu(self):
        quiz_menu = QuizMenu(self.available_camera)
        widget.addWidget(quiz_menu)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        
    def to_presentation(self):
        self.pushButton.hide()
        self.pushButton_2.hide()
        self.pushButton_4.hide()
        self.label_2.hide()
        widget.setWindowFlag(Qt.WindowCloseButtonHint, False)
        widget.showNormal()
        widget.setWindowTitle('Presentation')
        widget.setGeometry(600, 200, 300, 200)
        self.pushButton_3.show()
        self.label.show()
        self.presentation.run()
        
    @pyqtSlot(np.ndarray)
    def computer_vision(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(q_img))
        
    def stop_presentation(self):
        self.presentation.stop_presentation.emit()
    
    def show_menu(self):
        self.pushButton_3.hide()
        self.label.hide()
        self.label_2.show()
        self.pushButton.show()
        self.pushButton_2.show()
        self.pushButton_4.show()
        widget.showFullScreen()
        self.presentation = Presentation(camera_source=self.available_camera)
        self.presentation.frame_signal.connect(self.computer_vision)
        self.presentation.finished.connect(self.show_menu)
        
    def close_app(self):
        self.key_control.press('q')
        self.key_control.release('q')
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q:
            self.close()



class QuizMenu(QWidget):
    def __init__(self, available_camera):
        super().__init__()
        loadUi("ui/quiz_menu.ui", self)
        self.load_quiz_list()
        self.available_camera = available_camera
        
        self.pushButton.clicked.connect(self.to_main_window)
        self.pushButton_2.clicked.connect(self.to_quiz_edit)
        self.pushButton_3.clicked.connect(self.to_quiz_window)
        
    def to_main_window(self):
        window = MainWindow()
        widget.addWidget(window)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        
    def to_quiz_edit(self):
        quiz_edit = QuizEdit(self.available_camera)
        widget.addWidget(quiz_edit)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        quiz_edit.quiz_index_from_menu.emit(self.comboBox.currentIndex())
        
    def to_quiz_window(self):
        quiz_window = QuizWindow(self.available_camera)
        widget.addWidget(quiz_window)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        quiz_window.quiz_name_from_menu.emit(self.comboBox.currentText())
        
    def load_quiz_list(self):
        existing_files = [self.comboBox.itemText(i) for i in range(self.comboBox.count())]
        if not os.path.exists('quiz'):
                os.makedirs('quiz')
        all_files = os.listdir('quiz')
        csv_files = [os.path.splitext(file)[0] for file in all_files if file.endswith('.csv')]
        
        for file in csv_files:
            if file not in existing_files:
                self.comboBox.addItem(file)



class QuizWindow(QWidget):
    quiz_name_from_menu = pyqtSignal(str)
    
    def __init__(self, available_camera):
        super().__init__()
        loadUi("ui/quiz.ui", self)
        
        self.available_camera = available_camera
        self.quiz_name = str()
        self.question_list = list()
        self.question = 0
        self.execution_time = time.time()
        
        self.thread = Quiz(camera_source=self.available_camera)
        self.quiz_name_from_menu.connect(self.quiz_data)
        self.quiz_name_from_menu.connect(self.thread.quiz_name_signal.emit)
        self.thread.frame_signal.connect(self.computer_vision)
        self.thread.indicator_signal.connect(self.handle_indicator)
        self.thread.question_signal.connect(self.handle_question)
        self.thread.reset_signal.connect(self.handle_question)
        self.thread.finish_signal.connect(self.finish_quiz)
        self.thread.start()
        
        self.pushButton.clicked.connect(self.undo_question)
        self.pushButton_2.clicked.connect(self.reset_question)
        self.pushButton_3.clicked.connect(self.to_quiz_menu)
        
    def to_quiz_menu(self):
        quiz_menu = QuizMenu(self.available_camera)
        widget.addWidget(quiz_menu)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        self.thread.stop_signal.emit()
        
    def quiz_data(self, quiz_name):
        self.quiz_name = quiz_name
        with open(f'quiz/{self.quiz_name}.csv', 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            self.question_list = list(reader)
        
        self.progressBar.setMaximum(len(self.question_list) - 1)
        self.progressBar.setMinimum(0)
        self.reset_question()
    
    @pyqtSlot(np.ndarray)
    def computer_vision(self, frame):
        cv_label_width = self.label.width()
        cv_label_height = math.ceil(cv_label_width * 9 / 16)
        resized_frame = cv2.resize(frame, (cv_label_width, cv_label_height))
        rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(q_img))
        
    def handle_indicator(self, indicator_color):
        self.label_11.setStyleSheet(f"""
                                    color: {indicator_color};
                                    background-color: {indicator_color};
                                    border-radius: 12px;
                                    min-width: 20px;
                                    min-height: 20px;
                                    """)
        
    def handle_question(self, question_index):
        self.question = question_index
        self.progressBar.setValue(self.question)
        question_data = self.question_list[self.question + 1]
        self.label_10.setText(question_data[0])
        
        if question_data[1]:
            self.set_image(self.label_1, question_data[1])
        else:
            self.label_1.clear()
            
        if question_data[2] == 'text':
            self.label_2.setText(question_data[4])
            self.label_3.setText(question_data[5])
            self.label_4.setText(question_data[6])
            self.label_5.setText(question_data[7])
        elif question_data[2] == 'image':
            self.set_image(self.label_2, question_data[4])
            self.set_image(self.label_3, question_data[5])
            self.set_image(self.label_4, question_data[6])
            self.set_image(self.label_5, question_data[7])
        
    def undo_question(self):
        if self.question >= 1:
            self.question -= 1
        self.thread.command_signal.emit("undo")
        
    def reset_question(self):
        self.question = 0
        self.thread.command_signal.emit("reset")
        
    def finish_quiz(self, quiz_name, score):
        quiz_finish = QuizFinish(self.available_camera)
        widget.addWidget(quiz_finish)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        quiz_finish.score_signal.emit(quiz_name, score)
        
    def set_image(self, label, image_path):
        if image_path.lower().endswith(('.png', '.jpg', 'jpeg')):
            label_height = label.height()
            label_width = label.width()
            pixmap = QPixmap(image_path)
            pixmap_resized = fit_pixmap(pixmap, label_height, label_width)
            label.setPixmap(pixmap_resized)
            label.setAlignment(Qt.AlignCenter)
        else:
            label.clear()



class QuizFinish(QWidget):
    score_signal = pyqtSignal(str, float)
    
    def __init__(self, available_camera):
        super().__init__()
        loadUi("ui/quiz_finish.ui", self)
        
        self.available_camera = available_camera
        self.quiz_name = ''
        self.score_signal.connect(self.show_result)
        
        self.pushButton.clicked.connect(self.restart_quiz)
        self.pushButton_2.clicked.connect(self.to_quiz_menu)
        
    def show_result(self, quiz_name, score):
        self.quiz_name = quiz_name
        self.label_2.setText(f"Congratulations! You have finished Quiz: \"{self.quiz_name}\"")
        self.label.setText(f"Score: {score}")
        
    def to_quiz_menu(self):
        quiz_menu = QuizMenu(self.available_camera)
        widget.addWidget(quiz_menu)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        
    def restart_quiz(self):
        quiz_window = QuizWindow(self.available_camera)
        widget.addWidget(quiz_window)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        quiz_window.quiz_name_from_menu.emit(self.quiz_name)



class QuizEdit(QWidget):
    quiz_index_from_menu = pyqtSignal(int)
    closed = pyqtSignal()
    
    def __init__(self, available_camera):
        super().__init__()
        loadUi("ui/quiz_edit.ui", self)
        
        self.available_camera = available_camera
        self.quiz_name = str()
        self.disable_choice_type()
        self.load_quiz_list()
        if not self.comboBox.currentText():
            self.new_quiz_window()
        else:
            self.load_question()
        self.quiz_index_from_menu.connect(self.comboBox.setCurrentIndex)
        
        self.pushButton_2.clicked.connect(self.delete_question)
        self.pushButton_3.clicked.connect(self.to_quiz_menu)
        self.pushButton_4.clicked.connect(self.new_quiz_window)
        self.pushButton_5.clicked.connect(self.question_number_handle)
        self.pushButton_6.clicked.connect(self.question_number_handle)
        self.pushButton_7.clicked.connect(self.delete_quiz)
        self.upload_0.clicked.connect(self.image_upload)
        self.upload_1.clicked.connect(self.image_upload)
        self.upload_2.clicked.connect(self.image_upload)
        self.upload_3.clicked.connect(self.image_upload)
        self.upload_4.clicked.connect(self.image_upload)
        self.comboBox.currentIndexChanged.connect(self.select_quiz_handle)
        self.pushButton.clicked.connect(self.save_inputs)
        self.radioButton.toggled.connect(self.disable_choice_type)
        self.radioButton_2.toggled.connect(self.disable_choice_type)
        
    def to_quiz_menu(self):
        quiz_menu = QuizMenu(self.available_camera)
        widget.addWidget(quiz_menu)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        
    def new_quiz_window(self):
        self.new_quiz = NewQuiz(self.available_camera)
        self.new_quiz.closed.connect(self.load_quiz_list)
        self.new_quiz.show()
        self.new_quiz.raise_()
        self.new_quiz.activateWindow()
        
    def select_quiz_handle(self):
        self.label_11.setText('1')
        if self.comboBox.count() > 0:
            self.load_question()
        
    def question_number_handle(self):
        button = self.sender().objectName()
        current_number = int(self.label_11.text())
            
        if button[-1] == '5':
            if current_number > 1:
                number = str(current_number - 1)
                self.label_11.setText(number)
        elif button[-1] == '6':
            with open(f'quiz/{self.comboBox.currentText()}.csv', 'r', newline='', encoding='utf-8') as file:
                reader = csv.reader(file)
                rows = list(reader)
                if current_number < len(rows):
                    number = str(current_number + 1)
                    self.label_11.setText(number)
        
        self.load_question()
    
    def disable_choice_type(self):
        if self.radioButton.isChecked() and not self.radioButton_2.isChecked():
            text_type = True
            image_type = False
        elif self.radioButton_2.isChecked() and not self.radioButton.isChecked():
            text_type = False
            image_type = True
        
        self.choice_1.setEnabled(text_type)
        self.choice_2.setEnabled(text_type)
        self.choice_3.setEnabled(text_type)
        self.choice_4.setEnabled(text_type)
        self.upload_1.setEnabled(image_type)
        self.upload_2.setEnabled(image_type)
        self.upload_3.setEnabled(image_type)
        self.upload_4.setEnabled(image_type)
        
    def load_quiz_list(self):
        existing_files = [self.comboBox.itemText(i) for i in range(self.comboBox.count())]
        all_files = os.listdir('quiz')
        csv_files = [os.path.splitext(file)[0] for file in all_files if file.endswith('.csv')]
        
        for file in csv_files:
            if file not in existing_files:
                self.comboBox.addItem(file)
                
    def load_image(self, image_path, label):
        if image_path.lower().endswith(('.png', '.jpg', 'jpeg')):
            label_height = label.height()
            label_width = label.width()
            pixmap = QPixmap(image_path)
            pixmap = fit_pixmap(pixmap, label_height, label_width)
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignCenter)
        else:
            label.clear()
    
    def load_question(self):
        self.quiz_name = self.comboBox.currentText()
        question_number = int(self.label_11.text())
        question_data = ['', '', 'text', '1', '', '', '', '']
            
        with open(f'quiz/{self.quiz_name}.csv', 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for i, row in enumerate(reader):
                if i == question_number:
                    question_data = row
                    
            self.questionText.setPlainText(question_data[0])
            self.comboBox_2.setCurrentIndex(int(question_data[3]) - 1)
            self.label_6.setText(question_data[1])
            self.load_image(question_data[1], self.label)
            
            self.choice_1.clear()
            self.choice_2.clear()
            self.choice_3.clear()
            self.choice_4.clear()
            self.label_7.clear()
            self.label_8.clear()
            self.label_9.clear()
            self.label_10.clear()
            
            if question_data[2] == 'text':
                self.radioButton.setChecked(True)
                self.choice_1.setPlainText(question_data[4])
                self.choice_2.setPlainText(question_data[5])
                self.choice_3.setPlainText(question_data[6])
                self.choice_4.setPlainText(question_data[7])
            elif question_data[2] == 'image':
                self.radioButton_2.setChecked(True)
                self.label_7.setText(question_data[4])
                self.label_8.setText(question_data[5])
                self.label_9.setText(question_data[6])
                self.label_10.setText(question_data[7])
            
            self.load_image(question_data[4], self.label_2)
            self.load_image(question_data[5], self.label_3)
            self.load_image(question_data[6], self.label_4)
            self.load_image(question_data[7], self.label_5)
        
    def save_inputs(self):
        question_number = int(self.label_11.text())
        question_text = self.questionText.toPlainText()
        question_image = self.label_6.text()
        answer = int(self.comboBox_2.currentText())
        choices = []
        
        if self.radioButton.isChecked() and not self.radioButton_2.isChecked():
                choice_type = 'text'
        elif self.radioButton_2.isChecked() and not self.radioButton.isChecked():
                choice_type = 'image'
                
        if choice_type == 'text':
                choices.extend([
                self.choice_1.toPlainText(),
                self.choice_2.toPlainText(),
                self.choice_3.toPlainText(),
                self.choice_4.toPlainText()
            ])
        elif choice_type == 'image':
                choices.extend([
                self.label_7.text(),
                self.label_8.text(),
                self.label_9.text(),
                self.label_10.text()
            ])
        
        with open(f'quiz/{self.quiz_name}.csv', 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
            
            row = [
                question_text,
                question_image,
                choice_type,
                answer
            ]
            for choice in choices:
                row.append(choice)
            if question_number < len(rows):
                rows[question_number] = row
            else:
                rows.append(row)
            
            with open(f'quiz/{self.quiz_name}.csv', mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerows(rows)
                
    def delete_quiz(self):
        quiz_path = f'quiz/{self.quiz_name}.csv'
        quiz_index = self.comboBox.currentIndex()
        if os.path.exists(quiz_path):
            os.remove(quiz_path)
            self.comboBox.removeItem(quiz_index)
            if quiz_index > 0:
                self.comboBox.setCurrentIndex(quiz_index - 1)
            else:
                self.new_quiz_window()
            
    def delete_question(self):
        question_number = int(self.label_11.text())
        rows = []
        with open(f'quiz/{self.quiz_name}.csv', mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for index, row in enumerate(reader):
                if index != question_number:
                    rows.append(row)

        with open(f'quiz/{self.quiz_name}.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(rows)
            
        if question_number >= 2:
            self.label_11.setText(str(question_number - 1))
        self.load_question()
        
    def image_upload(self):
        button = self.sender().objectName()
        image_formats = "All Supported Files (*.png *.jpg *.jpeg);;PNG Files (*.png);;JPG Files (*.jpg);;JPEG Files (*.jpeg)"
        
        filepath, _ = QFileDialog.getOpenFileName(self, "Open File", "", image_formats)
        if filepath:
            target_directory = 'quiz/images'
            if not os.path.exists(target_directory):
                os.makedirs(target_directory)
            
            try:
                copied_path = shutil.copy(filepath, target_directory)
                normalized_path = copied_path.replace(os.sep, '/')
            except Exception as e:
                print(f'Error copying file: {e}')
            
            if button[-1] == '0':
                self.label_6.setText(normalized_path)
                self.load_image(normalized_path, self.label)
            elif button[-1] == '1':
                self.label_7.setText(normalized_path)
                self.load_image(normalized_path, self.label_2)
            elif button[-1] == '2':
                self.label_8.setText(normalized_path)
                self.load_image(normalized_path, self.label_3)
            elif button[-1] == '3':
                self.label_9.setText(normalized_path)
                self.load_image(normalized_path, self.label_4)
            elif button[-1] == '4':
                self.label_10.setText(normalized_path)
                self.load_image(normalized_path, self.label_5)



class NewQuiz(QWidget):
    closed = pyqtSignal()
    
    def __init__(self, available_camera):
        super().__init__()
        loadUi("ui/new_quiz.ui", self)
        
        self.available_camera = available_camera
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setWindowModality(Qt.ApplicationModal)
        self.all_files = os.listdir('quiz')
        
        self.pushButton.clicked.connect(self.save_quiz)
        self.pushButton_2.clicked.connect(self.cancel_button)
        self.pushButton_3.clicked.connect(self.to_quiz_menu)
        
    def to_quiz_menu(self):
        quiz_menu = QuizMenu(self.available_camera)
        widget.addWidget(quiz_menu)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        self.close()
        
    def cancel_button(self):
        csv_files = [file for file in self.all_files if file.endswith('.csv')]
        
        if not csv_files:
            self.label_2.setText('There is no Quiz to edit, Create one to edit.')
        elif csv_files:
            self.close()
        
    def save_quiz(self):
        quiz_name = self.lineEdit.text()
        csv_files = [os.path.splitext(file)[0] for file in self.all_files if file.endswith('.csv')]
        
        if quiz_name:
            if quiz_name in csv_files:
                self.label_2.setText('There is already a Quiz with that name.')
            else:
                with open(f'quiz/{quiz_name}.csv', 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(['question_text', 'question_image', 'choice_type', 'answer', 'choice1', 'choice2', 
                                    'choice3', 'choice4'])
                self.close()
                self.closed.emit()
        else:
            self.label_2.setText('Invalid Quiz name.')



class EscapeFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == event.KeyPress and event.key() == Qt.Key_Q:
            QApplication.quit()
            return True
        return super().eventFilter(obj, event)



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
        
        # Disable scientific notation for clarity
        np.set_printoptions(suppress=True)
        # Load the model
        self.model = load_model("model/presentation_keys.h5")
        self.offset = 20
        self.img_size = 256
        
        self.video = video
        self.detector = HandDetector(maxHands=1)
        self.wCam = int(self.video.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.hCam = int(self.video.get(cv2.CAP_PROP_FRAME_HEIGHT))
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
        self.responses = []
        self.start_time = time.time()
        for monitor in get_monitors():
            self.wScr = monitor.width
            self.hScr = monitor.height
            
        self.stop_presentation.connect(self.stop)
            
    def key_detection(self, hand, blank_lm):
        current_time = time.time()
            
        if current_time > self.cooldown + 1:
            if not self.double_detection:
                self.detected_answer = self.key_check(hand)
                self.detection_time = time.time()
                self.double_detection = True
                
            elif current_time > self.detection_time + 0.5:
                key = self.key_check(hand)
                prediction = self.key_prediction(hand, blank_lm)
                response = time.time() - self.start_time
                self.responses.append(response)
                print(f"Response: {response}")
                if self.detected_answer == key:
                    if hand['type'] == "Right":
                        if key == 'esc' and prediction[0][1] >= 0.7:
                            self.press_key(Key.esc)
                            print('esc')
                        elif key == 'b' and prediction[0][0] >= 0.7:
                            self.press_key('b')
                            print('b')
                        elif key == 'right' and prediction[0][3] >= 0.7:
                            self.press_key(Key.right)
                            print('R')
                        elif key == 'left' and prediction[0][2] >= 0.7:
                            self.press_key(Key.left)
                            print('L')
                        elif key == 'switch' and prediction[0][4] >= 0.7:
                            self.key_mode = False
                            print('switch')
                        print(key, prediction)
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
    
    def key_prediction(self, hand, blank_lm):
        x, y, w, h = hand['bbox']
        aspect_ratio = h / w
        blank_img = np.ones((self.img_size, self.img_size, 3), np.uint8)
        
        if x - self.offset >= 0 and y - self.offset >= 0:
            blank_lm_crop = blank_lm[y-self.offset : y + h+self.offset, x-self.offset : x + w+self.offset]
        elif x - self.offset < 0 and y - self.offset >= 0:
            blank_lm_crop = blank_lm[y-self.offset : y + h+self.offset, 0 : x + w+self.offset]
        elif x - self.offset >= 0 and y - self.offset < 0:
            blank_lm_crop = blank_lm[0 : y + h+self.offset, x-self.offset : x + w+self.offset]
        else:
            blank_lm_crop = blank_lm[0 : y + h+self.offset, 0 : x + w+self.offset]
            
        if np.any(blank_lm_crop):
            if aspect_ratio > 1:
                k = self.img_size / h
                w_cal = math.floor(k * w)
                img_resize = cv2.resize(blank_lm_crop, (w_cal, self.img_size))
                w_gap = math.ceil((self.img_size - w_cal)/2)
                blank_img[:, w_gap:w_cal + w_gap] = img_resize
                
                img_test = cv2.resize(blank_img, (256, 256), interpolation=cv2.INTER_AREA)
                prediction = self.model.predict(np.expand_dims(img_test/255, 0))
                
            elif aspect_ratio < 1:
                k = self.img_size / w
                h_cal = math.floor(k * h)
                img_resize = cv2.resize(blank_lm_crop, (self.img_size, h_cal))
                h_gap = math.ceil((self.img_size - h_cal)/2)
                blank_img[h_gap:h_cal + h_gap, :] = img_resize
                
                img_test = cv2.resize(blank_img, (256, 256), interpolation=cv2.INTER_AREA)
                prediction = self.model.predict(np.expand_dims(img_test/255, 0))
                
            else:
                prediction = [[0.0, 0.0, 0.0, 0.0, 0.0]]
                
            return prediction
                
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
            self.start_time = time.time()
            success, img = self.video.read()
            img = cv2.flip(img, 1)
            
            if self.key_mode:
                hands, img, blank_lm = self.detector.findHands(img, getBlank=True)
                if hands:
                    hand = hands[0]
                    self.key_detection(hand, blank_lm)
                
            else:
                self.cursor_control(img)
                cv2.rectangle(img, (25, 25), (self.wCam - self.frameX, self.hCam - self.frameY),
                              (0, 255, 0), 1)
                cv2.putText(img, "screen", (25, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                            (0, 255, 0), 1)
            
            self.frame_signal.emit(img)
            
            if cv2.waitKey(1) == ord('q'):
                self.stop()
                
        # print("Avg. Response: ", sum(self.responses) / len(self.responses))
        
    def stop(self):
        self.running = False
        self.finished.emit()



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
        else:  # Jika 5 jari diangkat
            self.chosen_answer = None
             
# cv2.namedWindow("img")
# cv2.setMouseCallback("img", on_mouse_click)

class Quiz(QThread):
    quiz_name_signal = pyqtSignal(str)
    frame_signal = pyqtSignal(np.ndarray)
    indicator_signal = pyqtSignal(str)
    question_signal = pyqtSignal(int)
    reset_signal = pyqtSignal(int)
    command_signal = pyqtSignal(str)
    finish_signal = pyqtSignal(str, float)
    stop_signal = pyqtSignal()
    
    def __init__(self, camera_source=0):
        super().__init__()
        self.detector = HandDetector(detectionCon=0.8, maxHands=2)
        self.video = video
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 1200)
        self.window_name = 'window_name'
        
        self.quiz_name = str()
        self.ardlist = []
        self.running = True
        self.qNo = 0
        self.score = 0
        self.qTotal = 0
        
        self.last_execution_time = time.time()
        self.detection_time = time.time()
        self.cooldown_period = 3
        self.on_cooldown = True
        self.detected_answer = None
        self.double_detection = False
        
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
            current_time = time.time()
            ret, frame = self.video.read()
            frame = cv2.flip(frame, 1)
            hands, img = self.detector.findHands(frame)
            
            if self.on_cooldown:
                if current_time - self.last_execution_time >= self.cooldown_period:
                    self.on_cooldown = False
                    self.indicator_signal.emit('rgba(0, 0, 0, 0)')
            
            elif self.qNo < self.qTotal:
                ard = self.ardlist[self.qNo]

                if hands and len(hands) > 0:
                    # lmList = hands[0]['lmList']
                    fingers = self.detector.tipsUp(hands[0])
                    ard.update(fingers)
                    answer = ard.chosen_answer
                    
                    if answer:
                        if not self.double_detection:
                            self.detected_answer = answer
                            self.detection_time = time.time()
                            self.double_detection = True
                            self.indicator_signal.emit('rgb(0, 255, 0)')
                        
                        elif current_time > self.detection_time + 1:
                            self.double_detection = False
                            if answer == self.detected_answer:
                                self.qNo += 1
                                if self.qNo != self.qTotal:
                                    self.question_signal.emit(self.qNo)
                                self.indicator_signal.emit('red')
                                self.on_cooldown = True
                                self.last_execution_time = time.time()
                    else:
                        self.indicator_signal.emit('rgba(0, 0, 0, 0)')
                        self.detected_answer = None
                else:
                    self.indicator_signal.emit('rgba(0, 0, 0, 0)')
                    self.detected_answer = None

            if self.qNo == self.qTotal:
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




if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = QtWidgets.QStackedWidget()
    window = MainWindow()
    widget.addWidget(window)
    widget.setWindowTitle('Window')
    widget.setWindowIcon(QIcon('logo_upi.ico'))
    # widget.setGeometry(600, 200, 640, 480)
    widget.showFullScreen()
    widget.show()
    
    escape_filter = EscapeFilter()
    app.installEventFilter(escape_filter)
    
    sys.exit(app.exec_())
