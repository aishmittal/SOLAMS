import cv2
from PyQt4 import QtGui, QtCore
import os

from PIL import Image, ImageTk
from contextlib import contextmanager

class Capture():
    def __init__(self, parent, *args, **kwargs):
        super(Capture, self).__init__()
        # initialize time label
        self.capturing = False
        self.c = cv2.VideoCapture(0)

    def startCapture(self):
        print "pressed start"
        self.capturing = True
        cap = self.c
        while(self.capturing):
            ret, frame = cap.read()
            parent.pic.setPixmap(frame)
            #cv2.imshow("Capture", frame)
            cv2.waitKey(5)
        cv2.destroyAllWindows()

    def endCapture(self):
        print "pressed End"
        self.capturing = False

    def quitCapture(self):
        print "pressed Quit"
        cap = self.c
        cv2.destroyAllWindows()
        cap.release()
        QtCore.QCoreApplication.quit()


class Window(QtGui.QWidget):
    def __init__(self):

        QtGui.QWidget.__init__(self)
        self.setWindowTitle('Control Panel')

        #self.capture = Capture()
        self.start_button = QtGui.QPushButton('Start',self)
        #self.start_button.clicked.connect(self.capture.startCapture)

        self.end_button = QtGui.QPushButton('End',self)
        #self.end_button.clicked.connect(self.capture.endCapture)

        self.quit_button = QtGui.QPushButton('Quit',self)
        #self.quit_button.clicked.connect(self.capture.quitCapture)

        self.pic = QtGui.QLabel()
        self.pic.setGeometry(10, 10, 200, 200)   
        
        

        vbox = QtGui.QVBoxLayout(self)
        vbox.addWidget(self.pic)
        vbox.addWidget(self.start_button)
        vbox.addWidget(self.end_button)
        vbox.addWidget(self.quit_button)

        self.setLayout(vbox)
        self.setGeometry(100,100,200,200)
        self.show()

        self.capturing = True
        self.c = cv2.VideoCapture(0)
        cap = self.c
        while(self.capturing):
            ret, frame = cap.read()
            
            img = Image.fromarray(frame, 'RGB')
            img.save('my.png')
            self.pic.setPixmap(QtGui.QPixmap(os.getcwd() + "/my.png"))

            #cv2.imshow("Capture", frame)
            cv2.waitKey(5)
        cv2.destroyAllWindows()


if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec_())