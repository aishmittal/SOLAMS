import sqlite3




conn = sqlite3.connect('sams.db')
print "Opened database successfully";

TABLE_NAME="students"
cursor = conn.cursor()

def create_table():
	
	cursor.execute("""DROP TABLE students;""")
	command = """CREATE TABLE {TABLE_NAME}
	       (id INTEGER PRIMARY KEY   AUTOINCREMENT,
	       uname  VARCHAR(20)  NOT NULL,
	       fname  VARCHAR(30)  NOT NULL,
	       lname  VARCHAR(50)  NOT NULL,
	       dob 	  DATE 	NOT NULL,
	       gender CHAR(1) NOT NULL,		
	       pid    VARCHAR(40)  NOT NULL);""".format(TABLE_NAME=TABLE_NAME)
	
	print command       	
	cursor.execute(command)
	print "Table created successfully";

def insert_row(uname,fname,lname,dob,gender,pid):
	
	format_str = """INSERT INTO students (id,uname,fname,lname,dob,gender,pid) 
				 VALUES (NULL,"{uname}","{fname}","{lname}","{dob}","{gender}","{pid}");"""
	sql_command = format_str.format(uname=uname, fname=fname, lname=lname, dob=dob,gender=gender,pid=pid)
	print sql_command
	cursor.execute(sql_command)			 



if __name__ == '__main__':
	#create_table()
	
	#insert_row('abhi','Abhishek','Mittal','14-08-1995','M','bfe4ce34-6a88-4c14-925b-e8d85393929e')
	cursor.execute("SELECT * FROM students WHERE gender='F'")
	result = cursor.fetchall()
	for r in result: 
		print r[1] 

conn.commit()
conn.close()