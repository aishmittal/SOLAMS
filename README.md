# SOLAMS (Smart Online Lecture Attendance Management System)
SOLAMS is an Face Identification based automatic attendance management system which is useful for universities and educational websites
which offers online lecture to students but wants to keep track of their attendance to ensure that students are taking 
lectures. It consists of two applications i.e. register user and main application. 

### New User Registration
Register application used to register the new user by taking some information about user and storing the information in a 
database and creating personid using Microsoft Face APIs. After the Face Dataset is generated using Opencv2. this generated face dataset is later uploaded to cloudinary and Microsoft 
cognitive service face APIs. after uploading dataset to microsoft cognitive service a model is build and trained.

### Attendance during lecture
All registered users can login with there userid in main app. Login is face identification based so no password is required. After login user can select the course and lecture according to their choice and start lecture. Attendance is taken by capturing face at regular interval of time and verifying the detected personid with loggedin personid. Based on these regular attendance aggregate percent attendace is calculated according to total lecture duration and detection time interval. this aggregate percent attendence is then stored in database. Attendance for the lecture is marked as completed if percent attendance is greater tha 60 percent
 
### Attendance Records
All users can view there attendance records by selecting the cource in records tab in main app. It also gives the information of total course attendance
 
## Language used
 
 Python 2.7
 
## Python Packages Required
 1. Opencv 2
 2. PtQt 4
 3. Sqlite3
 4. PIL
 
 
## APIs used
 1. Microsoft Cognitive Services Face APIs (for building face identification model)
 2. Cloudinary APIs (for storing dataset)
 3. YouTube APIs (for getting video information of playlists)
 
## Database used
 sqlite3
 
## Database Structure
* sudents
 * id -> userid
 * uname -> user name
 * fname -> first name
 * lname -> last name
 * dob -> date of birth
 * email -> user email id
 * gender -> gender
 * personid -> id of user in MS Face APIs
 * created at -> time stamp of user entry creation
  
* courses
 * id -> courseid
 * name -> course name
 * code -> university code of course
 * shortname -> shortname of the course
 * instructor -> instructor name
 * totallectures -> total no of lectures
 * url -> url of course playlist on youtube
 * description -> description of course
 * created -> timestamp
 
* lectures
 * id -> rowid
 * courseid -> froreign key from courses
 * lectureno -> lecture no
 * duration -> total duration of lecture in minutes
 * title -> lecture title
 * tilelbl -> lecture title label
 * videoid -> id of lecture video on youtube
 * description -> embed youtube url of lecture video
 * created -> timestamp
 
* attendance
 * id -> rowid
 * userid -> froreign key from students
 * courseid -> froreign key from courses
 * lectureno -> lecture no
 * percent_completed -> aggregate percent of lecture completion
 * start_time -> timestamp
 
 
