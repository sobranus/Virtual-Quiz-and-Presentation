import sys
import os
import shutil
import math
import numpy as np
import csv
import cv2
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt, QObject, QTimer, pyqtSignal, pyqtSlot
import Mouse
import Quiz


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
        self.pushButton.clicked.connect(self.to_presentation)
        self.pushButton_2.clicked.connect(self.to_quiz_menu)
        
    def to_quiz_menu(self):
        quiz_menu = QuizMenu()
        widget.addWidget(quiz_menu)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        
    def to_presentation(self):
        self.virtual_mouse = Mouse.Mouse()
        self.virtual_mouse.run()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        
        
class QuizMenu(QWidget):
    def __init__(self):
        super().__init__()
        loadUi("ui/quiz.ui", self)
        self.pushButton.clicked.connect(self.to_main_screen)
        self.pushButton_2.clicked.connect(self.to_quiz_edit)
        self.pushButton_3.clicked.connect(self.to_quiz_start)
        
    def to_main_screen(self):
        window = MainWindow()
        widget.addWidget(window)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        
    def to_quiz_edit(self):
        quiz_edit = QuizEdit()
        widget.addWidget(quiz_edit)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        
    def to_quiz_start(self):
        quiz_start = QuizStart()
        widget.addWidget(quiz_start)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        

class QuizStart(QWidget):
    def __init__(self):
        self.question = 0
        super().__init__()
        loadUi("ui/quiz_start.ui", self)
        
        self.pixmap_a = QPixmap()
        self.pixmap_b = QPixmap()
        self.pixmap_c = QPixmap()
        self.pixmap_d = QPixmap()
        
        QTimer.singleShot(3000, self.undo_question)
        self.pushButton.clicked.connect(self.undo_question)
        self.pushButton_2.clicked.connect(self.next_question)
        self.pushButton_3.clicked.connect(self.to_quiz_menu)
        
        self.thread = Quiz.Quiz()
        self.thread.frame_signal.connect(self.computer_vision)
        self.thread.question_signal.connect(self.handle_question)
        self.thread.reset_signal.connect(self.handle_question)
        self.thread.start()
    
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
        
    def handle_question(self, qNo):
        self.question_cv = qNo
        self.pixmap_a = QPixmap(f'quiz/question{self.question_cv}/a.png')
        self.pixmap_b = QPixmap(f'quiz/question{self.question_cv}/b.png')
        self.pixmap_c = QPixmap(f'quiz/question{self.question_cv}/c.png')
        self.pixmap_d = QPixmap(f'quiz/question{self.question_cv}/d.png')
        QTimer.singleShot(0, self.set_image)
        
    def undo_question(self):
        self.thread.command_signal.emit("undo")
        if self.question >= 1:
            self.question -= 1
        
    def next_question(self):
        self.thread.command_signal.emit("reset")
        self.question = 0
        
    def set_image(self):
        label_height = self.label_2.height()
        label_width = self.label_2.width()
        pixmap_a = fit_pixmap(self.pixmap_a, label_height, label_width)
        pixmap_b = fit_pixmap(self.pixmap_b, label_height, label_width)
        pixmap_c = fit_pixmap(self.pixmap_c, label_height, label_width)
        pixmap_d = fit_pixmap(self.pixmap_d, label_height, label_width)
        self.set_pixmap(pixmap_a, self.label_2)
        self.set_pixmap(pixmap_b, self.label_3)
        self.set_pixmap(pixmap_c, self.label_4)
        self.set_pixmap(pixmap_d, self.label_5)
        
    def to_quiz_menu(self):
        quiz_menu = QuizMenu()
        widget.addWidget(quiz_menu)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        
    def resizeEvent(self, event):
        QTimer.singleShot(1000, self.set_image)
        super().resizeEvent(event)
        
    def set_pixmap(self, pixmap, label):
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignCenter)
        # for i in range(1, 6):
        #     var_name = f"label_{i}"
        #     if hasattr(self, var_name):
        #         getattr(self, var_name).setPixmap(pixmap)
        #         getattr(self, var_name).setAlignment(Qt.AlignCenter)
        

class QuizEdit(QWidget):
    
    closed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        loadUi("ui/quiz_edit.ui", self)
        QTimer.singleShot(0, self.disable_choice_type)
        QTimer.singleShot(0, self.load_quiz_list)
        
        self.pushButton.clicked.connect(self.save_inputs)
        self.pushButton_3.clicked.connect(self.to_quiz_menu)
        self.pushButton_4.clicked.connect(self.new_quiz_window)
        self.pushButton_5.clicked.connect(self.load_question)
        self.pushButton_6.clicked.connect(self.load_question)
        self.upload_0.clicked.connect(self.image_upload)
        self.upload_1.clicked.connect(self.image_upload)
        self.upload_2.clicked.connect(self.image_upload)
        self.upload_3.clicked.connect(self.image_upload)
        self.upload_4.clicked.connect(self.image_upload)
        self.radioButton.toggled.connect(self.disable_choice_type)
        self.radioButton_2.toggled.connect(self.disable_choice_type)
        
    def to_quiz_menu(self):
        quiz_menu = QuizMenu()
        widget.addWidget(quiz_menu)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        
    def new_quiz_window(self):
        self.new_quiz = NewQuiz()
        self.new_quiz.closed.connect(self.load_quiz_list)
        self.new_quiz.show()
        self.new_quiz.raise_()
        self.new_quiz.activateWindow()
        
    def load_question(self):
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
        
    def save_inputs(self):
        quiz_name = self.comboBox.currentText()
        question_number = int(self.label_11.text())
        question_text = self.questionText.toPlainText()
        question_image = self.label_6.text()
        true_choice = int(self.comboBox_2.currentText())
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
        
        with open(f'quiz/{quiz_name}.csv', 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            rows = list(reader)
            
            row = [
                question_number,
                question_text,
                question_image,
                choice_type,
                true_choice
            ]
            for choice in choices:
                row.append(choice)
            if question_number < len(rows):
                rows[question_number] = row
            else:
                rows.append(row)
            
            with open(f'quiz/{quiz_name}.csv', mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerows(rows)
        
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
            except Exception as e:
                print(f'Error copying file: {e}')
                
            label_height = self.label.height()
            label_width = self.label.width()
            pixmap = QPixmap(copied_path)
            pixmap = fit_pixmap(pixmap, label_height, label_width)
            
            if button[-1] == '0':
                self.label_6.setText(copied_path)
                display_label = self.label   
            elif button[-1] == '1':
                self.label_7.setText(copied_path)
                display_label = self.label_2
            elif button[-1] == '2':
                self.label_8.setText(copied_path)
                display_label = self.label_3
            elif button[-1] == '3':
                self.label_9.setText(copied_path)
                display_label = self.label_4
            elif button[-1] == '4':
                self.label_10.setText(copied_path)
                display_label = self.label_5
            
            display_label.setPixmap(pixmap)
            display_label.setAlignment(Qt.AlignCenter)
            
            
class NewQuiz(QWidget):
    closed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        loadUi("ui/new_quiz.ui", self)
        self.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setWindowModality(Qt.ApplicationModal)
        self.quiz_edit = QuizEdit()
        self.all_files = os.listdir('quiz')
        
        self.pushButton.clicked.connect(self.save_quiz)
        self.pushButton_2.clicked.connect(self.cancel_button)
        
    def save_quiz(self):
        quiz_name = self.lineEdit.text()
        csv_files = [os.path.splitext(file)[0] for file in self.all_files if file.endswith('.csv')]
        
        if quiz_name:
            if quiz_name in csv_files:
                self.label_2.setText('There is already a Quiz with that name.')
            else:
                with open(f'quiz/{quiz_name}.csv', 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(['number', 'question_text', 'question_image', 'choice_type', 'true_choice', 'choice1', 'choice2', 
                                    'choice3', 'choice4'])
                self.close()
                self.closed.emit()
        else:
            self.label_2.setText('Invalid Quiz name.')
        
    def cancel_button(self):
        csv_files = [file for file in self.all_files if file.endswith('.csv')]
        
        if not csv_files:
            self.label_2.setText('There is no Quiz to edit, Create one to edit.')
        elif csv_files:
            self.close()


class EscapeFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == event.KeyPress and event.key() == Qt.Key_Escape:
            QApplication.quit()
            return True
        return super().eventFilter(obj, event)
    
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    widget = QtWidgets.QStackedWidget()
    widget.addWidget(window)
    widget.setGeometry(600, 200, 640, 480)
    # widget.showFullScreen()
    widget.show()
    
    escape_filter = EscapeFilter()
    app.installEventFilter(escape_filter)
    
    sys.exit(app.exec_())
