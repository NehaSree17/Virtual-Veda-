import eel
import socket

eel.init('web')
import ipaddress

@eel.expose
def getIP4():
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)
    IPAddr= int(ipaddress.ip_address(IPAddr))
    return IPAddr


# student
student_name = None
student_classip = None

import cv2
import dlib
from math import sqrt
import os
from threading import Thread
from queue import Queue

import pyttsx3

def alertvoice():
    global student_name
    engine = pyttsx3.init()
    message= student_name + ", be attentive in the class!!"
    engine.say(message)
    engine.runAndWait()

def midpoint(p1, p2):
    return int((p1.x + p2.x) / 2), int((p1.y + p2.y) / 2)


def lenth_of_line(x1, y1, x2, y2):
    return sqrt(((x1 - x2) ** 2) + ((y1 - y2) ** 2))


def get_blinking_ratio(eye_points, facial_landmarks):
    left_point = (facial_landmarks.part(eye_points[0]).x, facial_landmarks.part(eye_points[0]).y)
    right_point = (facial_landmarks.part(eye_points[3]).x, facial_landmarks.part(eye_points[3]).y)

    center_top = midpoint(facial_landmarks.part(eye_points[1]), facial_landmarks.part(eye_points[2]))
    center_bottom = midpoint(facial_landmarks.part(eye_points[5]), facial_landmarks.part(eye_points[4]))

    ver_length = lenth_of_line(center_top[0], center_top[1], center_bottom[0], center_bottom[1])
    hor_length = lenth_of_line(left_point[0], left_point[1], right_point[0], right_point[1])

    ratio = (hor_length / ver_length)
    return ratio

def attention_trac(q):
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)
    cap.set(10, 100)

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

    attention = 0
    is_first = 1

    eye_closed = 0
    not_in_center = 0
    no_face = 0

    while True:
        success, img = cap.read()

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        if faces:
            for face in faces:
                if no_face != 0:
                    no_face = 0
                if is_first == 1:
                    attention = 100
                    is_first = 0

                landmarks = predictor(gray, face)
                # detect blinking

                # print(landmarks)
                # cv2.circle(img, (landmarks.part(36).x,landmarks.part(36).y), 2, (0,255,0))
                for i in range(0, 68):
                    cv2.circle(img, (landmarks.part(i).x, landmarks.part(i).y), 1, (0, 255, 0))

                left_eye_ratio = get_blinking_ratio([36, 37, 38, 39, 40, 41], landmarks)
                right_eye_ratio = get_blinking_ratio([42, 43, 44, 45, 46, 47], landmarks)

                if (left_eye_ratio + right_eye_ratio) / 2 > 5:
                    cv2.putText(img, "EYE CLOSED", (50, 350), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 0))
                    eye_closed = eye_closed + 1

                else:
                    if eye_closed != 0:
                        eye_closed = 0

                left_ear_eye = lenth_of_line(landmarks.part(0).x, landmarks.part(36).x, landmarks.part(0).y,
                                             landmarks.part(36).y)
                right_ear_eye = lenth_of_line(landmarks.part(16).x, landmarks.part(45).x, landmarks.part(16).y,
                                              landmarks.part(45).y)

                ratio = left_ear_eye / right_ear_eye
                cv2.putText(img, str(ratio), (50, 150), cv2.FONT_HERSHEY_PLAIN, 7, (255, 0, 0))

                if ratio < 0.45:
                    # print("CENTER")
                    cv2.putText(img, "CENTER", (100, 200), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 3)
                    if not_in_center != 0:
                        not_in_center = 0
                else:
                    # print("NOT IN CENTER")
                    cv2.putText(img, "NOT IN CENTER", (100, 200), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 3)
                    not_in_center = not_in_center + 1

        else:
            # print("NO face detected")
            no_face = no_face + 1

        attention = 100 - not_in_center - no_face * 3 - eye_closed

        if attention < 0:
            attention = 0

        # print("level of attention is " + str(attention) + " %")
        q.put(attention)

        eel.render("Your Attention is: " + str(attention) + "%")

        if attention==0:
            alertvoice()
        # cv2.imshow("Video", img)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #print("closevideo")
        #break

    cap.release()
    cv2.destroyAllWindows()


def connection(q):
    HEADER_LENGTH = 100
    global student_classip, student_name
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Connect to a given ip and port
        client_socket.connect((student_classip, 1234))

        client_socket.setblocking(False)
    except:
        #eel.alertstudent("Your Teacher is not present! \r\n If this is a mistake, try contacting your teacher.","joinclass.html")
        print("Teacher not Present")
        eel.teachernotpresent()

    username = student_name.encode('utf-8')
    username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket.send(username_header + username)

    t1 = Thread(target=attention_trac, args=(q,))
    t1.start()

    while True:
        try:
            data = str(q.get())
            # Encode message to bytes, prepare header and convert to bytes, like for username above, then send
            data = data.encode('utf-8')
            message_header = f"{len(data):<{HEADER_LENGTH}}".encode('utf-8')
            client_socket.send(message_header + data)
        except:
            eel.alertstudent("The class has ended.", "")
            print("connection is closed")
            client_socket.close()
            break

@eel.expose
def joinclass(name, ip):
    global student_name
    global student_classip

    student_name = name
    ip=int(ip)
    student_classip= ipaddress.ip_address(ip).__str__()
    print(student_name, student_classip)
    q = Queue()
    t2 = Thread(target=connection, args=(q,))
    t2.start()


# teacher
import select

exitteacher=None
@eel.expose
def newclass():
    IP = ""
    PORT = 1234
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((IP, PORT))
    server_socket.listen()

    sockets_list = [server_socket]

    clients = {}
    status = 0

    print(f'Listening for connections on {IP}:{PORT}...')
    global exitteacher
    exitteacher=0
    while exitteacher==0:
        read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

        # Iterate over notified sockets
        for notified_socket in read_sockets:
            if notified_socket == server_socket:

                client_socket, client_address = server_socket.accept()
                user = receive_message(client_socket)

                if user is False:
                    continue

                sockets_list.append(client_socket)

                clients[client_socket] = user

                print('Accepted new connection from {}:{}, username: {}'.format(*client_address,
                                                                                user['data'].decode('utf-8')))
                if status == 0:
                    eel.createtable()
                    status = 1

                eel.adduser(user['data'].decode("utf-8"))
            else:
                # Receive message
                message = receive_message(notified_socket)

                if message is False:
                    print('Closed connection from: {}'.format(clients[notified_socket]['data'].decode('utf-8')))
                    eel.deletestudent(clients[notified_socket]['data'].decode('utf-8'))

                    # Remove from list for socket.socket()
                    sockets_list.remove(notified_socket)

                    # Remove from our list of users
                    del clients[notified_socket]

                    continue

                # Get user by notified socket, so we will know who sent the message
                user = clients[notified_socket]

                print(f'attention level of {user["data"].decode("utf-8")} is {message["data"].decode("utf-8")} %')
                attn = message["data"].decode("utf-8") + " %"
                eel.appendattention(user["data"].decode("utf-8"), attn)
        # It's not really necessary to have this, but will handle some socket exceptions just in case
        for notified_socket in exception_sockets:
            # Remove from list for socket.socket()
            sockets_list.remove(notified_socket)

            # Remove from our list of users
            del clients[notified_socket]


# Handles message receiving
def receive_message(client_socket):
    HEADER_LENGTH = 100
    try:

        # Receive our "header" containing message length, it's size is defined and constant
        message_header = client_socket.recv(HEADER_LENGTH)

        if not len(message_header):
            return False

        # Convert header to int value
        message_length = int(message_header.decode('utf-8').strip())

        return {'header': message_header, 'data': client_socket.recv(message_length)}

    except:
        return False


try:
    eel.start('f1.html', size=(1000, 800),)
except(SystemExit, MemoryError,KeyboardInterrupt):
    exitteacher=1
    os._exit(0)
