import sys
import math
import numpy as np
import csv
import cv2
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.uic import loadUi
from PyQt5.QtCore import Qt, QObject, QTimer, pyqtSlot
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
    def __init__(self):
        super().__init__()
        loadUi("ui/quiz_edit.ui", self)
        self.pushButton_3.clicked.connect(self.to_quiz_menu)
        self.pushButton_4.clicked.connect(self.to_path_widget)
        
        self.quiz_pack = []
        
    def to_quiz_menu(self):
        quiz_menu = QuizMenu()
        widget.addWidget(quiz_menu)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        
    def to_path_widget(self):
        filepath = QFileDialog.getOpenFileName(self, "Open File", "", "CSV Files (*.csv);;All Files (*)")
        if filepath:
            self.textEdit_6.setText(filepath[0])
            
            
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
