import sys
import os
import cv2

from PyQt4.QtCore import QSize, Qt
import PyQt4.QtCore as QtCore 
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *

import locale
import threading
import time
import requests
import json
import traceback
import feedparser
import sqlite3

from PIL import Image, ImageTk
from contextlib import contextmanager

import imageUpload as imup
import MSFaceAPI as msface

LOCALE_LOCK = threading.Lock()

window_width = 700
window_height = 450
window_x = 400
window_y = 150
ip = '<IP>'
ui_locale = '' # e.g. 'fr_FR' fro French, '' as default
time_format = "hh:mm:ss" # 12 or 24
date_format = "dd-MM-YYYY" # check python doc for strftime() for options
large_text_size = 28
medium_text_size = 18
small_text_size = 10

base_path = os.path.dirname(os.path.realpath(__file__))
dataset_path = os.path.join(base_path,'dataset')
tmp_path = os.path.join(base_path,'tmp')
cloudinary_dataset = 'http://res.cloudinary.com/aish/image/upload/v1488457817/SAMS/dataset'
cloudinary_tmp = 'http://res.cloudinary.com/aish/image/upload/v1488457817/SAMS/tmp'

camera_port = 1
user={
    'uname':'',
    'fname':'',
    'lname':'',
    'email':'',
    'gender':'',
    'dob':'',
    'personid':''

}

conn = sqlite3.connect('sams.db')
TABLE_NAME="students"
cursor = conn.cursor()




     
    
class MainWindow:

    def __init__(self): 
        self.qt = QWidget()
        self.qt.setGeometry(window_x, window_y, window_width, window_height)
        self.pal=QPalette()
        self.pal.setColor(QPalette.Background,Qt.white)
        self.pal.setColor(QPalette.Foreground,Qt.black)
        self.qt.setPalette(self.pal)
        self.vbox= QVBoxLayout()
        
        # self.tab1 = QWidget()
        # self.DetailsTab=AddDetailsTab(self.tab1)
        # self.qt.addTab(self.DetailsTab,"Add Details")
    
        # self.tab2 = QWidget()
        # self.DatasetTab=GenerateDatasetTab(self.tab2)
        # self.qt.addTab(self.DatasetTab,"Generate Face Dataset"),self.qt.show()



if __name__ == '__main__':
    a = QApplication(sys.argv)
    w = MainWindow()
    sys.exit(a.exec_())
