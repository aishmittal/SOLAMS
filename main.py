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
large_text_size = 14
medium_text_size = 12
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
    'userid':0,
    'uname':'',
    'fname':'',
    'lname':'',
    'email':'',
    'gender':'',
    'dob':'',
    'personid':''
}

login_status = False
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
        font1 = QFont('Helvetica', small_text_size)
        font2 = QFont('Helvetica', medium_text_size)
        font3 = QFont('Helvetica', large_text_size)

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
        self.splitter1.setStretchFactor(10, 1)

        self.vvbox = QVBoxLayout()
        self.vvbox.setAlignment(Qt.AlignCenter)
        self.vvbox.setContentsMargins(0,0,0,0)
        self.vvbox.setSpacing(0)
        self.vvbox.addWidget(self.splitter1)
        self.setLayout(self.vvbox)


        self.userMessageLbl = QLabel('')
        self.userMessageLbl.setFont(font3)
        self.userMessageLbl.setContentsMargins(5,20,5,20)
        #self.userMessageLbl.setFixedWidth(40)

        self.fbox1=QFormLayout()
        self.fbox1.setAlignment(Qt.AlignCenter)
        self.fbox1.setSpacing(15)
        self.unameLbl = QLabel('User Name')
        self.unameEdt = QLineEdit()
        self.loginMessageLbl = QLabel('')
        
        self.loginMessageLbl.setFont(font1)
        self.loginMessageLbl.setAlignment(Qt.AlignCenter)
        self.loginButton = QPushButton('Login')

        self.loginButton.clicked.connect(self.user_login)
        self.courseLbl = QLabel('Select Course')
        self.courses = select_query("SELECT name FROM courses",())
        self.courseSelect = QComboBox()
        
        for i in self.courses:
            self.courseSelect.addItem(i)

        self.fbox2=QFormLayout()
        self.fbox2.setSpacing(15)
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
        self.stopButton = QPushButton('Leave Lecture')
        self.stopButton.clicked.connect(self.stopLecture)
        self.quitButton = QPushButton('Quit')
        self.quitButton.clicked.connect(self.quitApp)
        

        self.fbox1.addRow(self.unameLbl)
        self.fbox1.addRow(self.unameEdt)
        self.fbox1.addRow(self.loginButton)
        self.fbox1.addRow(self.loginMessageLbl)
        self.fbox1.setContentsMargins(60,10,60,10)
        
        self.fbox2.addRow(self.userMessageLbl)
        self.fbox2.addRow(self.courseLbl)
        self.fbox2.addRow(self.courseSelect)
        self.fbox2.addRow(self.lectureLbl)
        self.fbox2.addRow(self.lectureSelect)
        self.fbox2.addRow(self.startButton)
        self.fbox2.addRow(self.stopButton)
        self.fbox2.addRow(self.quitButton)
        self.fbox2.setContentsMargins(10,10,10,10)
        
        self.fbox3 = QFormLayout()
        self.dcntLbl = QLabel('Current Detection Count: ')
        self.dcnt = QLabel('') 
        self.tdcntLbl = QLabel('Total Detections: ')
        self.tdcnt = QLabel('') 
        self.lpLbl = QLabel('Percent Attendance: ')
        self.lp = QLabel('')
        self.dcntLbl.setFont(font2)
        self.dcnt.setFont(font2)
        self.tdcntLbl.setFont(font2)
        self.tdcnt.setFont(font2)
        self.lpLbl.setFont(font2)
        self.lp.setFont(font2)

        


        self.fbox3.addRow(self.dcntLbl,self.dcnt)
        self.fbox3.addRow(self.tdcntLbl,self.tdcnt)
        self.fbox3.addRow(self.lpLbl,self.lp)
        

        self.fbox3.setContentsMargins(5,40,5,20)

        self.topRight = QFrame()
        self.topRight.setObjectName("box-border")
        self.middleRight = QFrame()
        self.bottomRight = QFrame()
        self.topRight.setLayout(self.fbox1)
        self.middleRight.setLayout(self.fbox2)
        self.bottomRight.setLayout(self.fbox3)
        
        
        self.vbox2.addWidget(self.topRight)
        self.vbox2.addWidget(self.middleRight)
        self.vbox2.addWidget(self.bottomRight)

        self.video = Browser()
        self.lectureUrl =  'https://www.youtube.com/embed/HJUI2Il3xnI?autoplay=1'
        self.currentLectureNo = 1
        #self.video = QWebView()
        #self.factory = WebPluginFactory()
        #self.video.page().setPluginFactory(self.factory)
        # self.video.setHtml("<iframe width='450' height='300'\
        # src='https://www.youtube.com/embed/XGSy3_Czz8k'>\
        # </iframe>")
        self.video.load(QtCore.QUrl(self.lectureUrl))
        self.vbox1.setContentsMargins(10,50,10,50)
        self.vbox1.addWidget(self.video)

    def quitApp(self):
        quit_msg = "Are you sure you want to exit the program?"
        reply = QMessageBox.question(self, 'Message', 
                         quit_msg, QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            QtCore.QCoreApplication.instance().quit()
        else:
            # Nothing
            a=1



    def heightForWidth(self, width):
        return width * 1.5

    def user_login(self):
        #self.userLoggedIn = False
        global login_status
        login_status = False
        if not self.unameEdt.text():
            self.loginMessageLbl.setText('Warning: Enter username!')
            print "Enter username !"
            return

        uname = str(self.unameEdt.text())

        sql_command = """SELECT * FROM students WHERE uname = '%s' """ % uname
        #print sql_command
        cursor.execute(sql_command)
        res = cursor.fetchone()
        if res:
            #print res
            personid = res[7]
            #print personid
            v = self.face_verify(personid)
            if  v == True :
                
                self.userLoggedIn = True
                login_status = True
                self.loginMessageLbl.setText('Success: Login Successful !')
                print "Login Successful !"
                print "current user:"+ uname
                current_user['userid'] = res[0]
                current_user['uname'] = uname
                current_user['fname'] = res[2]
                current_user['lname'] = res[3]
                current_user['dob'] = res[4]
                current_user['email'] = res[5]
                current_user['gender'] = res[6]
                current_user['personid'] = res[7]
                self.userMessageLbl.setText('Welcome %s !' % current_user['fname'])
                #print current_user
            else:
                self.loginMessageLbl.setText('Error: Login Failed , try again !')
                print "Login Failed !"
                print "Please try again!"                
            

        else:
            self.loginMessageLbl.setText('Error: Username not found !')
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
        global login_status
        if login_status == True:
            
            self.currentCourseNo = self.courseSelect.currentIndex()+1
            self.currentLectureNo = self.lectureSelect.currentIndex()+1
            
            comm = """SELECT url,duration FROM lectures WHERE courseid = ? AND lectureno = ?"""
            res  = multiple_select_query(comm,(self.currentCourseNo,self.currentLectureNo))
            res = res[0]
            #print res
            
            self.lectureUrl = res[0]
            self.lectureDuration = res[1]
            self.maxDetectionCount = (self.lectureDuration * 60000) / self.detectionInterval
            self.tdcnt.setText(str(int(self.maxDetectionCount)))
            self.dcnt.setText('0')
            self.lp.setText('0.00')
            #print "maxDetectionCount %d " % self.maxDetectionCount
            
            self.detectionCount = 0
            self.video.load(QtCore.QUrl(self.lectureUrl+'&autoplay=1'))

            comm = "INSERT INTO attendance (userid,courseid,lectureno,percent_completed) VALUES (?,?,?,?)"
            cur = query(comm,(current_user['userid'],self.currentCourseNo,self.currentLectureNo,0))
            comm = "SELECT last_insert_rowid()"
            rowid = int_select_query(comm)
            
            self.currentAttendanceId = rowid[0]
            self.startCapture()

        else :
            self.loginMessageLbl.setText('Error: Login first to start lecture!')

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

    def stopLecture(self):
        self.stopCapture()
        self.detectionCount = 0
        self.maxDetectionCount = 0
        self.dcnt.setText(str(self.detectionCount))
        self.lp.setText("0.00 %")
        self.tdcnt.setText("0")
        self.video.load(QtCore.QUrl('https://www.youtube.com/embed/HJUI2Il3xnI'))

    def mark_attendance(self):
        print "mark_attendance started"
        if self.detectionCount <= self.maxDetectionCount:
            check = self.face_verify(current_user['personid'])
            if check == True:
                self.detectionCount = self.detectionCount + 1
                self.dcnt.setText(str(self.detectionCount))
                print "detectionCount %d " % self.detectionCount  
                self.percent_completed = (self.detectionCount * self.detectionInterval * 100) / (self.lectureDuration * 60000)
                p = '%.2f ' % self.percent_completed
                self.lp.setText(p + "%")
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

        font1 = QFont('Helvetica', small_text_size)
        font2 = QFont('Helvetica', medium_text_size)
        font3 = QFont('Helvetica', large_text_size)

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
        self.splitter1.setSizes([600,100])
        #self.splitter1.setStretchFactor(10, 1)
        self.vvbox = QVBoxLayout()
        self.vvbox.addWidget(self.splitter1)
        self.setLayout(self.vvbox)
        self.recordsTable = QTableWidget()

        #self.recordsTable.setScaledContents(True)
        #self.recordsTable.resizeColumnsToContents()
        #self.recordsTable.resizeRowsToContents()
        
        self.tableHeaders = ['Lecture No','Title','Duration','Percent Attendance', 'Lecture Status','Lecture date']
        self.recordsTable.setRowCount(30)
        self.recordsTable.setColumnCount(len(self.tableHeaders))
        self.recordsTable.setHorizontalHeaderLabels(self.tableHeaders)
        self.header = self.recordsTable.horizontalHeader()
        #self.header.setResizeMode(QHeaderView.ResizeToContents)
        self.header.setResizeMode(QHeaderView.Stretch)
        #self.header.setSectionResizeMode(QHeaderView.Stretch)
        #self.header.setStretchLastSection(True)

        #self.recordsTable.horizontalHeader().setStretchLastSection(True)
        self.recordsTable.setContentsMargins(5,5,5,5)
        self.vbox1.addWidget(self.recordsTable)
        self.courseLbl = QLabel('Select Course')
        self.courses = select_query("SELECT name FROM courses",())
        self.courseSelect = QComboBox()
        for i in self.courses:
            self.courseSelect.addItem(i)
        self.showRecordsButton = QPushButton('Show Records')
        self.showRecordsButton.clicked.connect(self.fetch_attendance_records)
        self.errorMessageLbl = QLabel('')
        self.errorMessageLbl.setFont(font1)
        self.errorMessageLbl.setAlignment(Qt.AlignCenter)
        self.fbox1 = QFormLayout()
        self.fbox1.addRow(self.courseLbl)
        self.fbox1.addRow(self.courseSelect)
        self.fbox1.addRow(self.errorMessageLbl)
        self.fbox1.addRow(self.showRecordsButton)
        self.fbox1.setContentsMargins(20,50,20,50)
        self.fbox1.setSpacing(20)
        
        self.tlecLbl = QLabel('Total Lectures: ')
        self.tlecLbl.setFont(font3)
        self.tlec = QLabel('')
        self.tlec.setFont(font2)
        self.clecLbl = QLabel('Completed Lectures: ')
        self.clecLbl.setFont(font3)
        self.clec = QLabel('')
        self.clec.setFont(font2)
        self.percentLbl = QLabel('Percentage Attendance: ')
        self.percentLbl.setFont(font3)
        self.percent = QLabel('')
        self.percent.setFont(font2)

        self.fbox2 = QFormLayout()
        self.fbox2.addRow(self.tlecLbl)
        self.fbox2.addRow(self.tlec)
        self.fbox2.addRow(self.clecLbl)
        self.fbox2.addRow(self.clec)
        self.fbox2.addRow(self.percentLbl)
        self.fbox2.addRow(self.percent)
        self.fbox2.setContentsMargins(10,10,10,10)


        self.vbox2.addLayout(self.fbox1)
        self.vbox2.addLayout(self.fbox2)
        #self.vbox2.addStretch(2)

    def fetch_attendance_records(self):
        global login_status
        self.currentCourseNo =  self.courseSelect.currentIndex()+1
        if login_status == True and current_user['userid']!=0:
            self.recordsTable.clearContents()

            comm = "SELECT lectureno ,title, duration FROM lectures WHERE courseid = ? ORDER BY lectureno"
            res = multiple_select_query(comm,(str(self.currentCourseNo)))
            lecturenos = []
            titles = []
            durations = []
            #print res
            self.recordsTable.setRowCount(len(res))
            totalLectures = len(res)
            self.tlec.setText(str(len(res)))
            completed = 0
            
            for row in res:
                lecturenos.append(row[0])
                titles.append(row[1])
                durations.append(row[2])

            completed = 0    
            for idx,lectureno in enumerate(lecturenos):

                comm = "SELECT COUNT(*) FROM attendance WHERE userid =? AND courseid = ? AND lectureno = ?"
                cnt = int_select_query(comm,(current_user['userid'],self.currentCourseNo,lectureno))
                cnt = cnt[0]
                #print "Lecture No. ",lectureno
                if cnt==0:
                    #print "Attendance not found"
                    row_content = [lectureno, titles[idx],durations[idx],'0.0','Remaning','NULL']
                    #print row_content
                    for pos , item in enumerate(row_content):
                        self.recordsTable.setItem(lectureno-1, pos , QTableWidgetItem(str(item)))

                else:
                    comm = "SELECT MAX(percent_completed), start_time FROM attendance WHERE userid =? AND courseid = ? AND lectureno = ?"
                    res = multiple_select_query(comm,(current_user['userid'],self.currentCourseNo,lectureno))[0]
                    
                    percent = res[0]
                    completion_day = res[1]
                    #print "Attendance found " ,lectureno, res
                    #print completion_day
                    sp = '%.2f' % res[0]
                    row_content = [lectureno, titles[idx],durations[idx],sp,'Remaning',completion_day[0:10]]
                    if percent >= 60:
                        completed = completed + 1
                        row_content[4] = "Completed"

                    for pos , item in enumerate(row_content):
                        self.recordsTable.setItem(lectureno-1, pos , QTableWidgetItem(str(item)))

            percent = (completed/totalLectures)*100
            self.clec.setText(str(completed))
            s =   '%.2f' % percent
            self.percent.setText(s+' %')          

        else:
            self.errorMessageLbl.setText('Error: User not logged in!')                
    
class MainWindow:
    def __init__(self): 
        self.qt = QTabWidget()
        geom = QDesktopWidget().availableGeometry()
        self.qt.setGeometry(geom)
        #self.qt.setGeometry(window_x, window_y, window_width, window_height)
        self.pal=QPalette()
        self.pal.setColor(QPalette.Background,Qt.white)
        self.pal.setColor(QPalette.Foreground,Qt.black)
        self.qt.setPalette(self.pal)
    
        self.tab1 = QWidget()
        self.LectureTab=LectureTab(self.tab1)
        self.qt.addTab(self.LectureTab,"Leture")
    
        self.tab2 = QWidget()
        self.RecordsTab=RecordsTab(self.tab2)
        self.qt.addTab(self.RecordsTab,"Attendance Records")
        self.qt.setStyleSheet("""
        #box-border {
            border-style : solid;
            border-color : #BFC9CA;
            border-width : 2px;
            border-radius: 5px;

            
            }
        """)
        
        self.qt.setMouseTracking(True)
        #self.qt.showFullScreen()
        self.qt.show()
        
    def setMouseTracking(self, flag):
        def recursive_set(parent):
            for child in parent.findChildren(QtCore.QObject):
                try:
                    child.setMouseTracking(flag)
                except:
                    pass
                recursive_set(child)
        QtGui.QWidget.setMouseTracking(self, flag)
        recursive_set(self)

    def mouseMoveEvent(self, event):
        print 'mouseMoveEvent: x=%d, y=%d' % (event.x(), event.y())    


if __name__ == '__main__':
    a = QApplication(sys.argv)
    w = MainWindow()
   

    sys.exit(a.exec_())
