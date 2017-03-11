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

from PIL import Image, ImageTk
from contextlib import contextmanager

LOCALE_LOCK = threading.Lock()

window_width = 540
window_height = 960
ip = '<IP>'
ui_locale = '' # e.g. 'fr_FR' fro French, '' as default
time_format = 12 # 12 or 24
date_format = "%b %d, %Y" # check python doc for strftime() for options
xlarge_text_size = 48
large_text_size = 28
medium_text_size = 18
small_text_size = 10



class Clock(QFrame):
    def __init__(self, parent, *args, **kwargs):
        super(Clock, self).__init__()
        # initialize time label
        self.initUI()

    def initUI(self):    
        self.vbox = QVBoxLayout()
        font1 = QFont('Helvetica', large_text_size)
        font2 = QFont('Helvetica', small_text_size)
        self.time1 = ''
        self.timeLbl = QLabel('')
        self.timeLbl.setAlignment(Qt.AlignRight)
        self.timeLbl.setFont(font1)
        
        # initialize day of week
        self.day_of_week1 = ''
        self.dayOWLbl = QLabel('')
        self.dayOWLbl.setAlignment(Qt.AlignRight)
        
        # initialize date label
        self.date1 = ''
        self.dateLbl = QLabel('')
        self.dateLbl.setAlignment(Qt.AlignRight)

        self.vbox.addWidget(self.timeLbl)
        self.vbox.addWidget(self.dayOWLbl)
        self.vbox.addWidget(self.dateLbl)
        self.setLayout(self.vbox)
        self.tick()

    def tick(self):
        with setlocale(ui_locale):
            if time_format == 12:
                time2 = time.strftime('%I:%M %p') #hour in 12h format
            else:
                time2 = time.strftime('%H:%M') #hour in 24h format

            day_of_week2 = time.strftime('%A')
            date2 = time.strftime(date_format)
            # if time string has changed, update it
            if time2 != self.time1:
                self.time1 = time2
                self.timeLbl.setText(time2)
            if day_of_week2 != self.day_of_week1:
                self.day_of_week1 = day_of_week2
                self.dayOWLbl.setText(day_of_week2)
            if date2 != self.date1:
                self.date1 = date2
                self.dateLbl.setText(date2)
            # calls itself every 200 milliseconds
            # to update the time display as needed
            # could use >200 ms, but display gets jerky
            self.timer = QtCore.QTimer(self)
            self.timer.timeout.connect(self.tick)
            self.timer.start(1000)




class FullscreenWindow:

    def __init__(self):
		
		self.qt = QWidget()
		self.qt.resize(window_width, window_height)
		self.pal=QPalette()
		self.pal.setColor(QPalette.Background,Qt.black)
		self.pal.setColor(QPalette.Foreground,Qt.white)
		self.qt.setPalette(self.pal)
		# for wheather and clock 
		self.qt.hbox1 = QHBoxLayout()
		self.qt.Clockframe = QFrame()
		self.qt.Clockframe.setStyleSheet("background-color: black")
		self.qt.Clockframe.setStyleSheet("color: white")
		self.clock = Clock(self.qt.Clockframe)
		
		self.qt.hbox1.addStretch(1)
		self.qt.hbox1.addWidget(self.clock)

		# for stocks
		self.qt.hbox2 = QHBoxLayout()
		self.qt.Stocksframe = QFrame()
		self.qt.Stocksframe.setStyleSheet("background-color: red")
		#self.qt.hbox2.addStretch(1)
		self.qt.hbox2.addWidget(self.qt.Stocksframe)

		# for calender event
		self.qt.hbox3 = QHBoxLayout()
		self.qt.Eventframe = QFrame()
		self.qt.Eventframe.setStyleSheet("background-color: green")
		self.qt.hbox3.addWidget(self.qt.Eventframe)

		self.qt.hbox4 = QHBoxLayout() # dynamic area
		self.qt.Dynamicframe = QFrame()
		self.qt.Dynamicframe.setStyleSheet("background-color: white")
		self.qt.hbox4.addWidget(self.qt.Dynamicframe)


		self.qt.vbox  =	QVBoxLayout()
		self.qt.vbox.addLayout(self.qt.hbox1)
		self.qt.vbox.addLayout(self.qt.hbox2)
		self.qt.vbox.addLayout(self.qt.hbox3)
		self.qt.vbox.addLayout(self.qt.hbox4)
		self.qt.vbox.addLayout(self.qt.hbox5)
		self.qt.vbox.addLayout(self.qt.hbox6)

		self.qt.setLayout(self.qt.vbox)
		self.qt.show()

"""

self.topFrame = Frame(self.tk, background = 'black')
self.middleFrame = Frame(self.tk, background = 'black')
self.bottomFrame = Frame(self.tk, background = 'black')
self.topFrame.pack(side = TOP, fill=BOTH, expand = YES)
self.middleFrame.pack(side = TOP, fill=BOTH, expand = YES)
self.bottomFrame.pack(side = BOTTOM, fill=BOTH, expand = YES)
self.state = False
self.tk.bind("<Return>", self.toggle_fullscreen)
self.tk.bind("<Escape>", self.end_fullscreen)
# clock
self.clock = Clock(self.topFrame)
self.clock.pack(side=RIGHT, anchor=N, padx=100, pady=60)
# weather
self.weather = Weather(self.topFrame)
self.weather.pack(side=LEFT, anchor=N, padx=100, pady=60)
# news
self.news = News(self.bottomFrame)
self.news.pack(side=LEFT, anchor=S, padx=20, pady=60)
calender - removing for now
self.calender = Calendar(self.bottomFrame)
self.calender.pack(side = RIGHT, anchor=S, padx=100, pady=60)
"""

if __name__ == '__main__':
	a = QApplication(sys.argv)
	w = FullscreenWindow()
	sys.exit(a.exec_())