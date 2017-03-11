#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division

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
import string
import random
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
cloudinary_dataset = 'http://res.cloudinary.com/aish/image/upload/v1488457817/SOLAMS/dataset'
cloudinary_tmp = 'http://res.cloudinary.com/aish/image/upload/v1488457817/SOLAMS/tmp'
camera_port = 1
cascPath = 'haarcascade_frontalface_default.xml'
faceCascade = cv2.CascadeClassifier(cascPath) 
    
current_user={
    'userid':1,
    'uname':'',
    'fname':'',
    'lname':'',
    'email':'',
    'gender':'',
    'dob':'',
    'personid':''
}

userLoggedIn = False
conn = sqlite3.connect('solams.db')
TABLE_NAME="students"
cursor = conn.cursor()

def query(comm,params=None):
    conn.execute(comm,params)
    conn.commit()
    return cursor

def multiple_select_query(comm,params=()):
    cursor.execute(comm,params)
    res = cursor.fetchall()
    return res


def select_query(comm,params=()):
    cursor.execute(comm,params)
    res = cursor.fetchall()
    res =[x[0].encode('utf8') for x in res]
    return res

def int_select_query(comm,params=()):
    cursor.execute(comm,params)
    res = cursor.fetchall()
    res =[x[0] for x in res]
    return res

def get_courses():
    comm = "SELECT name FROM courses"
    return select_qyery(comm,())

def id_generator(size=20, chars=string.ascii_lowercase + string.digits + string.ascii_uppercase):
    return ''.join(random.choice(chars) for _ in range(size))


class WebPluginFactory(QWebPluginFactory):

    def __init__(self, parent = None):
        QWebPluginFactory.__init__(self, parent)
    
    def create(self, mimeType, url, names, values):
        if mimeType == "x-pyqt/widget":
            return WebWidget()
    
    def plugins(self):
        plugin = QWebPluginFactory.Plugin()
        plugin.name = "PyQt Widget"
        plugin.description = "An example Web plugin written with PyQt."
        mimeType = QWebPluginFactory.MimeType()
        mimeType.name = "x-pyqt/widget"
        mimeType.description = "PyQt widget"
        mimeType.fileExtensions = []
        plugin.mimeTypes = [mimeType]
        print "plugins"
        return [plugin]

class Browser(QWebView):

    def __init__(self):
        QWebView.__init__(self)
        self.loadFinished.connect(self._result_available)

    def _result_available(self, ok):
        frame = self.page().mainFrame()
        #print unicode(frame.toHtml()).encode('utf-8')   


class LectureTab(QWidget):
    def __init__(self, parent, *args, **kwargs):
        super(LectureTab, self).__init__()
        
        self.capturing=False
        self.userLoggedIn = False
        
        # 1 min = 60*1000 = 60000 msec
        self.detectionInterval = 20000
        self.detectionCount = 0
        self.maxDetectionCount = 0
        self.lectureCompleted = False
        self.currentCourseNo = 1
        self.currentLectureNo = 1
        self.lectureDuration = 0
        self.currentAttendanceId = 0
        self.percent_completed = 0.0

        self.initUI()

    def initUI(self):
        self.hbox=QHBoxLayout()
        self.vbox1= QVBoxLayout()
        self.vbox2= QVBoxLayout()
        
        self.left = QFrame()
        self.right = QFrame()
        self.left.setFrameShape(QFrame.StyledPanel)
        self.right.setFrameShape(QFrame.StyledPanel)
        self.left.setLayout(self.vbox1)
        self.right.setLayout(self.vbox2)

        self.splitter1 = QSplitter(Qt.Horizontal)
        self.splitter1.addWidget(self.left)
        self.splitter1.addWidget(self.right)
        self.splitter1.setSizes([550,150])
        self.vvbox = QVBoxLayout()
        self.vvbox.addWidget(self.splitter1)
        self.setLayout(self.vvbox)

        self.fbox=QFormLayout()
        self.fbox.setSpacing(20)
        self.unameLbl = QLabel('User Name')
        self.unameEdt = QLineEdit()
        self.loginButton = QPushButton('Login')
        self.loginButton.clicked.connect(self.user_login)
        self.courseLbl = QLabel('Select Course')
        self.courses = select_query("SELECT name FROM courses",())
        self.courseSelect = QComboBox()
        
        for i in self.courses:
            self.courseSelect.addItem(i)

        
        self.lectureLbl = QLabel('Lecture No.')
        self.lectureSelect = QComboBox()
        self.lectures = []
        self.get_lectures()
        self.courseSelect.currentIndexChanged.connect(self.get_lectures)

        self.currentCourse = str(self.courseSelect.currentText())
        self.currentCourseNo = self.courseSelect.currentIndex()+1
        self.currentLectureNo = self.lectureSelect.currentIndex()+1 

        self.startButton = QPushButton('Start Lecture')
        self.startButton.clicked.connect(self.start_new_lecture)

        self.fbox.addRow(self.unameLbl)
        self.fbox.addRow(self.unameEdt)
        self.fbox.addRow(self.loginButton)
        self.fbox.addRow(self.courseLbl)
        self.fbox.addRow(self.courseSelect)
        self.fbox.addRow(self.lectureLbl)
        self.fbox.addRow(self.lectureSelect)
        self.fbox.addRow(self.startButton)
        self.vbox2.addLayout(self.fbox)

        self.video = Browser()
        self.lectureUrl =  'https://www.youtube.com/embed/HJUI2Il3xnI'
        self.currentLectureNo = 1
        #self.video = QWebView()
        #self.factory = WebPluginFactory()
        #self.video.page().setPluginFactory(self.factory)
        # self.video.setHtml("<iframe width='450' height='300'\
        # src='https://www.youtube.com/embed/XGSy3_Czz8k'>\
        # </iframe>")
        self.video.load(QtCore.QUrl(self.lectureUrl))
        #sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        #sizePolicy.setHeightForWidth(True)
        #self.video.setSizePolicy(sizePolicy)
        self.vbox1.setContentsMargins(5,50,5,50)
        self.vbox1.addWidget(self.video,Qt.AlignCenter,Qt.AlignCenter)


    def heightForWidth(self, width):
        return width * 1.5

    def user_login(self):
        #self.userLoggedIn = False
        if not self.unameEdt.text():
            print "Enter username !"
            return

        uname = str(self.unameEdt.text())

        sql_command = """SELECT * FROM students WHERE uname = '%s' """ % uname
        #print sql_command
        cursor.execute(sql_command)
        res = cursor.fetchone()
        if res:
            #print res
            personid = res[6]
            #print personid
            v = self.face_verify(personid)
            if  v == True :
                self.userLoggedIn = True
                print "Login Successful !"
                print "current user:"+ uname
                current_user['userid'] = res[0]
                current_user['uname'] = uname
                current_user['fname'] = res[2]
                current_user['lname'] = res[3]
                current_user['dob'] = res[4]
                current_user['gender'] = res[5]
                current_user['personid'] = res[6]
                print current_user
            else:
                print "Login Failed !"
                print "Please try again!"                
            

        else:
            print 'user does not exist, get yourself registered!'
            

    def get_lectures(self):
        self.currentCourseNo = self.courseSelect.currentIndex()+1
        self.lectureSelect.clear()
        comm = "SELECT titlelbl FROM lectures WHERE courseid = %d ORDER BY lectureno" % self.currentCourseNo
        s = select_query(comm)
        if len(s)>0:
            self.lectures= s
        for i in self.lectures:
            self.lectureSelect.addItem(str(i))

    def start_new_lecture(self):
        # if self.userLoggedIn == False:
        #     print "Login first !"
        #     return

        self.currentCourseNo = self.courseSelect.currentIndex()+1
        self.currentLectureNo = self.lectureSelect.currentIndex()+1
        #print self.currentCourseNo , self.currentLectureNo 
        comm = """SELECT url,duration FROM lectures WHERE courseid = ? AND lectureno = ?"""
        res  = multiple_select_query(comm,(self.currentCourseNo,self.currentLectureNo))
        res = res[0]
        #print res
        self.lectureUrl = res[0]
        self.lectureDuration = res[1]
        self.maxDetectionCount = (self.lectureDuration * 60000) / self.detectionInterval
        print "maxDetectionCount %d " % self.maxDetectionCount
        self.detectionCount = 0
        self.video.load(QtCore.QUrl(self.lectureUrl))

        comm = "INSERT INTO attendance (userid,courseid,lectureno,percent_completed) VALUES (?,?,?,?)"
        cur = query(comm,(current_user['userid'],self.currentCourseNo,self.currentLectureNo,0))
        comm = "SELECT last_insert_rowid()"
        rowid = int_select_query(comm)
        self.currentAttendanceId = rowid[0]
        #print  self.currentAttendanceId

        self.startCapture()

    def startCapture(self):

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.mark_attendance)
        self.timer.start(self.detectionInterval)
        #self.mark_attendance()

    def stopCapture(self):
        try:
            self.capturing = False
            
            self.timer.stop()
            cv2.destroyAllWindows()
        except Exception as e:
            print e

    def mark_attendance(self):
        print "mark_attendance started"
        if self.detectionCount <= self.maxDetectionCount:
            check = self.face_verify(current_user['personid'])
            if check == True:
                self.detectionCount = self.detectionCount + 1
                print "detectionCount %d " % self.detectionCount  
                self.percent_completed = (self.detectionCount * self.detectionInterval * 100) / (self.lectureDuration * 60000)

                comm = "UPDATE attendance SET percent_completed= ? WHERE id = ?"
                cur = query(comm,(self.percent_completed,self.currentAttendanceId))
                print "attendence updated"


    
    def face_verify(self,personid):
        
        print "Face identification started .........."
        self.capture = cv2.VideoCapture(camera_port)
        self.capturing = True
        faceid = ''
        detected_personid = '' 
        try:
            r , frame = self.capture.read()
            frame = cv2.flip(frame, 1)
            #cv2.imshow('Video', frame)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = faceCascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(100, 100),
                flags=cv2.cv.CV_HAAR_SCALE_IMAGE
            )
            if len(faces)>0:
                
                max_area = 0
                mx = 0
                my = 0 
                mh = 0 
                mw = 0
                for (x, y, w, h) in faces:
                    if w*h > max_area:
                        mx = x
                        my = y
                        mh = h
                        mw = w
                        max_area=w*h
                        print max_area    
                
                image_crop = frame[my:my+mh,mx:mx+mw]
                file_name = id_generator()+'.jpg'
                file = os.path.join(tmp_path,file_name)
                cloudinary_url=cloudinary_tmp + '/' + file_name        
                cv2.imwrite(file, image_crop)
                imup.upload_image(file,file_name)
                
                faceid=msface.face_detect(cloudinary_url)
                
                print "faceId = " + str(faceid)
                detected_personid = msface.face_identify(faceid)
                print "detected_personid = " + str(detected_personid)
                print "personid = " + str(personid)

                if detected_personid:
                    if detected_personid == personid :
                        print "Face verified sucessfully"
                        self.capture.release()
                        return True
                    else:
                        print "Other person found"
                        self.capture.release()
                        return False
                else:
                    print "Unknown person found"
                    self.capture.release()
                    return False
            else:
                print "No person found"
                self.capture.release()
                return False
                    
        except Exception as e:
            print "Errors occured !"
            print e
            self.capture.release()
            return False



class RecordsTab(QWidget):
    def __init__(self, parent, *args, **kwargs):
        super(RecordsTab, self).__init__()
        self.initUI()

    def initUI(self):
        a=1

    
class MainWindow:
    def __init__(self): 
        self.qt = QTabWidget()
        self.qt.setGeometry(window_x, window_y, window_width, window_height)
        self.pal=QPalette()
        self.pal.setColor(QPalette.Background,Qt.white)
        self.pal.setColor(QPalette.Foreground,Qt.black)
        self.qt.setPalette(self.pal)
    
        self.tab1 = QWidget()
        self.LectureTab=LectureTab(self.tab1)
        self.qt.addTab(self.LectureTab,"Leture")
    
        self.tab2 = QWidget()
        self.RecordsTab=RecordsTab(self.tab2)
        self.qt.addTab(self.RecordsTab,"Records")
        self.qt.show()



if __name__ == '__main__':
    a = QApplication(sys.argv)
    w = MainWindow(),sys.exit(a.exec_())
