import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QFileDialog
from PyQt5.QtGui import QMovie
from PyQt5.uic import loadUi
import Mouse


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        loadUi("main_window.ui", self)
        self.pushButton.clicked.connect(self.to_presentation)
        self.pushButton_2.clicked.connect(self.to_quiz_panel)
        
    def to_quiz_panel(self):
        quiz_panel = QuizPanel()
        widget.addWidget(quiz_panel)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        
    def to_presentation(self):
        self.virtual_mouse = Mouse.Mouse()
        self.virtual_mouse.run()
        
        
class QuizPanel(QWidget):
    def __init__(self):
        super().__init__()
        loadUi("quiz.ui", self)
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
        super().__init__()
        loadUi("quiz_start.ui", self)
        self.pushButton_2.clicked.connect(self.to_quiz_panel)
        
    def to_quiz_panel(self):
        quiz_panel = QuizPanel()
        widget.addWidget(quiz_panel)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        

class QuizEdit(QWidget):
    def __init__(self):
        super().__init__()
        loadUi("quiz_edit.ui", self)
        self.pushButton_3.clicked.connect(self.to_quiz_panel)
        self.pushButton_4.clicked.connect(self.to_path_widget)
        
    def to_quiz_panel(self):
        quiz_panel = QuizPanel()
        widget.addWidget(quiz_panel)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        
    def to_path_widget(self):
        filepath = QFileDialog.getOpenFileName(self, "Open File", "", "CSV Files (*.csv);;All Files (*)")
        if filepath:
            self.textEdit_6.setText(filepath[0])
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    widget = QtWidgets.QStackedWidget()
    widget.addWidget(window)
    widget.setGeometry(600, 200, 640, 480)
    widget.show()
    sys.exit(app.exec_())
