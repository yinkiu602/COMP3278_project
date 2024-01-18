from flask import Flask, render_template, Response, redirect, url_for, make_response, request
import cv2
import numpy as np
import mysql.connector
import cv2
import pyttsx3
import pickle
from datetime import datetime
import json
import time

app = Flask(__name__)
myconn = mysql.connector.connect(host="192.168.0.130", user="root", passwd="", database="comp3278_project")
date = datetime.utcnow()
now = datetime.now()
current_time = now.strftime("%H:%M:%S")
cursor = myconn.cursor()
camera = cv2.VideoCapture(0)

# Face recognition starts#
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("train.yml")
camera_status = {"face_detected": False, "face_recognized": False}
face_id = -1
labels = {"person_name": 1}
with open("labels.pickle", "rb") as f:
    labels = pickle.load(f)
    labels = {v: k for k, v in labels.items()}

face_cascade = cv2.CascadeClassifier('haarcascade/haarcascade_frontalface_default.xml')
# Face recongition ends  #

def fetch_sql(query_string):
    local_connection = mysql.connector.connect(host="192.168.0.130", user="root", passwd="", database="comp3278_project")
    local_cursor = local_connection.cursor()
    print(query_string)
    local_cursor.execute(query_string)
    result = local_cursor.fetchall()
    local_cursor.close()
    local_connection.close()
    return result

def fetch_event(student_id):
    result = fetch_sql(f"SELECT C.course_id, C.classroom_address, C.start_time, C.end_time FROM Enroll E, Course_schedule C WHERE E.student_id = {student_id} AND E.course_id = C.course_id AND C.weekday = {datetime.now().weekday()} AND start_time BETWEEN CURRENT_TIME() AND ADDTIME(CURRENT_TIME(), '01:00:00')")
    # When testing use #TODO
    #result = fetch_sql(f"SELECT C.course_id, C.classroom_address, C.start_time, C.end_time FROM Enroll E, Course_schedule C WHERE E.student_id = {student_id} AND E.course_id = C.course_id AND C.weekday = 1")
    for i in range(len(result)):
        result[i] = list(result[i])
        result[i][2] = str(result[i][2])
        result[i][3] = str(result[i][3])
    output = ""
    for i in result:
        output += f"{i[0]} Room: {i[1]} Start time: {i[2]}<br>"
    return output

def record_login_logout(id, action):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    if (action == "login"):
        query = f"INSERT INTO Login_record(student_id, login_time) VALUES ('{id}', '{timestamp}')"
        cursor.execute(query)
        myconn.commit()
    else:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        query = f"UPDATE Login_record SET logout_time = '{timestamp}' WHERE record_id = '{id}'"
        cursor.execute(query)
        myconn.commit()

def camera_frame():
    global face_id
    while (camera_status["face_recognized"] == False):
        success, frame = camera.read()  # read the camera frame
        if (success):
            ret, buffer = cv2.imencode('.jpg', frame)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.5, minNeighbors=5)
            if (isinstance(faces, tuple)):
                camera_status["face_detected"] = False
            else:
                camera_status["face_detected"] = True
            for (x, y, w, h) in faces:
                print(x, w, y, h)
                roi_gray = gray[y:y + h, x:x + w]
                # predict the id and confidence for faces
                id_, loss = recognizer.predict(roi_gray)
                # Lower conf == more confident detected someone 
                if loss <= 70:
                    face_id = id_
                    camera_status["face_recognized"] = True

            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    return "HI"
            

@app.route("/test")
def test():
    return json.dumps([{"detected": "false", "face": "None"}])

@app.route("/")
def home():
    global camera
    camera_status["face_detected"] = False
    camera_status["face_recognized"] = False
    return render_template('index.html')

# Send the camera capture
@app.route("/capture")
def capture():
    output = camera_frame()
    print(output)
    return Response(camera_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Return the detected status to allow the client be redirected
@app.route("/detect")
def detect():
    if (camera_status["face_recognized"] == True):
        response = make_response(json.dumps(camera_status), 200)
        response.set_cookie("face_id", str(face_id))
        return response
    else:
        return json.dumps(camera_status)
    
@app.route("/whoami")
def whoami():
    if "face_id" not in request.cookies:
        return redirect("/")
    name = labels[int(request.cookies["face_id"])]
    return name
    
@app.route("/logout")
def logout():
    response = make_response("")
    record_login_logout(request.cookies["login_id"], "logout")
    response.set_cookie("face_id", expires=0)
    response.set_cookie("student_id", expires=0)
    response.set_cookie("login_id", expires=0)
    return response

@app.route("/fetch_session_login_time")
def fetch_session_login_time():
    student_id = request.cookies["student_id"]
    result = fetch_sql(f"SELECT login_time FROM Login_record WHERE student_id = {student_id} ORDER BY record_id DESC LIMIT 1")
    if (len(result) == 0):
        return ""
    else:
        return str(result[0][0])

@app.route('/fetch_all')
def fetch_all():
    student_id = request.cookies["student_id"]
    #result = fetch_sql(f"SELECT C.course_id, C.classroom_address, C.start_time, C.end_time FROM Enroll E, Course_schedule C WHERE E.student_id = {student_id} AND E.course_id = C.course_id AND C.weekday = {datetime.now().weekday()}")
    result = fetch_sql(f"SELECT weekday, start_time, end_time, C.course_id, classroom_address FROM Course_schedule C, Enroll E WHERE E.student_id = '{student_id}' AND E.course_id = C.course_id")
    for i in range(len(result)):
        result[i] = list(result[i])
        result[i][1] = str(result[i][1]).split(":")[0]
        result[i][2] = str(result[i][2]).split(":")[0]
    return json.dumps(result)

@app.route('/fetch_material')
def fetch_material():
    output = {}
    upcoming_course = fetch_sql(f"SELECT C.course_id, C.classroom_address, C.start_time, C.end_time FROM Enroll E, Course_schedule C WHERE E.student_id = {request.cookies['student_id']} AND E.course_id = C.course_id AND C.weekday = {datetime.now().weekday()} AND start_time BETWEEN CURRENT_TIME() AND ADDTIME(CURRENT_TIME(), '01:00:00')")
    # Testing use #TODO
    #upcoming_course = fetch_sql(f"SELECT C.course_id, C.classroom_address, C.start_time, C.end_time FROM Enroll E, Course_schedule C WHERE E.student_id = {request.cookies['student_id']} AND E.course_id = C.course_id AND C.weekday = 1")
    for i in range(len(upcoming_course)):
        upcoming_course[i] = list(upcoming_course[i])
        upcoming_course[i][2] = str(upcoming_course[i][2])
        upcoming_course[i][3] = str(upcoming_course[i][3])
    
    for i in range(len(upcoming_course)):
        output[str(upcoming_course[i][0])] = {"Room": upcoming_course[i][1], "Start time": upcoming_course[i][2], "End time": upcoming_course[i][3], "Material": []}

    course_list = [i[0] for i in upcoming_course]
    for i in course_list:
        course_link = fetch_sql(f"SELECT zoom_link FROM Course WHERE course_id = '{i}'")
        output[i]["zoom_link"] = course_link[0][0]
        material = fetch_sql(f"SELECT * FROM Material WHERE course_id = '{i}' ORDER BY type, material_id")
        for j in range(len(material)):
            material[j] = list(material[j])
            material[j][2] = str(material[j][2])
            material[j][3] = str(material[j][3])
            material[j][4] = str(material[j][4])
            output[i]["Material"].append({"type": material[j][2], "name": material[j][3], "link": material[j][4]})

    return json.dumps(output)

@app.route("/main")
def main_site():
    if "face_id" not in request.cookies:
        return redirect("/")
    global camera

    face_id = request.cookies["face_id"]
    student_id = fetch_sql(f"SELECT student_id FROM Student WHERE face_id = {face_id}")[0][0]
    last_login = fetch_sql(f"SELECT login_time FROM Login_record WHERE student_id = {student_id} ORDER BY record_id DESC LIMIT 1")
    if (len(last_login) != 0):
        response = make_response(render_template('main.html', text=fetch_event(student_id), name=labels[int(face_id)], login_history=str(last_login[0][0])))
    else:
        response = make_response(render_template('main.html', text=fetch_event(student_id), name=labels[int(face_id)]))
    response.set_cookie("student_id", str(student_id))
    record_login_logout(student_id, "login")
    cursor.execute("SELECT LAST_INSERT_ID()")
    response.set_cookie("login_id", str((cursor.fetchall())[0][0]))
    return response

# adds host="0.0.0.0" to make the server publicly available
app.run(host="127.0.0.1")
