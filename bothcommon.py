import eel
import socket
import ipaddress
import cv2
import mediapipe as mp
import numpy as np
import os
from threading import Thread
from queue import Queue
import pyttsx3
import select
import asyncio
import webbrowser

# ========== EEL Setup ==========
eel.init('web')

@eel.expose
def getIP4():
    hostname = socket.gethostname()
    IPAddr = socket.gethostbyname(hostname)
    IPAddr = int(ipaddress.ip_address(IPAddr))
    return IPAddr

# ========== Global Variables ==========
student_name = None
student_classip = None
exitteacher = 0

# ========== Text-to-Speech Alert ==========
def alertvoice():
    global student_name
    engine = pyttsx3.init()
    message = student_name + ", be attentive in the class!!"
    engine.say(message)
    engine.runAndWait()

# ========== Attention Tracking ==========
def eye_aspect_ratio(landmarks, eye_indices):
    eye = np.array([landmarks[i] for i in eye_indices])
    vertical1 = np.linalg.norm(eye[1] - eye[5])
    vertical2 = np.linalg.norm(eye[2] - eye[4])
    horizontal = np.linalg.norm(eye[0] - eye[3])
    return (vertical1 + vertical2) / (2.0 * horizontal)

def attention_trac(q):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot open camera.")
        return

    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(refine_landmarks=True)

    attention = 100
    no_face = 0
    eye_closed = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = face_mesh.process(rgb)
        frame_h, frame_w = frame.shape[:2]

        if result.multi_face_landmarks:
            face_landmarks = result.multi_face_landmarks[0]
            landmarks = [(int(p.x * frame_w), int(p.y * frame_h)) for p in face_landmarks.landmark]

            LEFT_EYE = [33, 160, 158, 133, 153, 144]
            RIGHT_EYE = [263, 387, 385, 362, 380, 373]
            left_ear = eye_aspect_ratio(landmarks, LEFT_EYE)
            right_ear = eye_aspect_ratio(landmarks, RIGHT_EYE)

            avg_ear = (left_ear + right_ear) / 2

            if avg_ear < 0.23:
                eye_closed += 1
                cv2.putText(frame, "EYE CLOSED", (50, 350), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            else:
                eye_closed = 0

            no_face = 0
        else:
            no_face += 1

        attention = max(0, 100 - eye_closed*2 - no_face*5)
        q.put(attention)

        eel.render("Your Attention is: " + str(attention) + "%")
        if attention == 0:
            alertvoice()

        cv2.imshow('Attention Monitor', frame)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

# ========== Client (Student) ==========
def connection(q):
    HEADER_LENGTH = 100
    global student_classip, student_name
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((student_classip, 1234))
        client_socket.setblocking(False)
    except Exception as e:
        print(f"Connection Error: {e}")
        eel.teachernotpresent()
        return

    username = student_name.encode('utf-8')
    username_header = f"{len(username):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket.send(username_header + username)

    t1 = Thread(target=attention_trac, args=(q,))
    t1.start()

    while True:
        try:
            data = str(q.get())
            data = data.encode('utf-8')
            message_header = f"{len(data):<{HEADER_LENGTH}}".encode('utf-8')
            client_socket.send(message_header + data)
        except:
            eel.alertstudent("The class has ended.", "f1.html")
            print("connection is closed")
            client_socket.close()
            break

@eel.expose
def joinclass(name, ip):
    global student_name
    global student_classip

    student_name = name
    ip = int(ip)
    student_classip = ipaddress.ip_address(ip).__str__()
    print(student_name, student_classip)
    q = Queue()
    t2 = Thread(target=connection, args=(q,))
    t2.start()

# ========== Teacher ==========
def receive_message(client_socket):
    HEADER_LENGTH = 100
    try:
        message_header = client_socket.recv(HEADER_LENGTH)
        if not len(message_header):
            return False
        message_length = int(message_header.decode('utf-8').strip())
        return {'header': message_header, 'data': client_socket.recv(message_length)}
    except:
        return False

def newclass_server_loop():
    IP = ""
    PORT = 1234
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((IP, PORT))
    server_socket.listen()

    sockets_list = [server_socket]
    clients = {}
    status = 0

    global exitteacher
    exitteacher = 0

    while exitteacher == 0:
        read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

        for notified_socket in read_sockets:
            if notified_socket == server_socket:
                client_socket, client_address = server_socket.accept()
                user = receive_message(client_socket)
                if user is False:
                    continue
                sockets_list.append(client_socket)
                clients[client_socket] = user
                if status == 0:
                    eel.createtable()
                    status = 1
                eel.adduser(user['data'].decode("utf-8"))
            else:
                message = receive_message(notified_socket)
                if message is False:
                    eel.deletestudent(clients[notified_socket]['data'].decode('utf-8'))
                    sockets_list.remove(notified_socket)
                    del clients[notified_socket]
                    continue
                user = clients[notified_socket]
                attn = message["data"].decode("utf-8") + " %"
                eel.appendattention(user["data"].decode("utf-8"), attn)

        for notified_socket in exception_sockets:
            sockets_list.remove(notified_socket)
            del clients[notified_socket]

@eel.expose
def newclass():
    server_thread = Thread(target=newclass_server_loop)
    server_thread.daemon = True
    server_thread.start()

# ========== MAIN ==========
if __name__ == '__main__':
    # Get local IP
    host = socket.gethostbyname(socket.gethostname())
    port = 8000
    url = f"http://{host}:{port}/f1.html"

    print("\n📡 Open this URL on your browser or tablet to join the class:")
    print(f"👉 {url}\n")

    # Try opening in Chrome, fallback to system browser
    try:
        chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe %s"
        webbrowser.get(chrome_path).open(url)
    except:
        webbrowser.open(url)

    eel.start('f1.html', mode=None, host=host, port=port, size=(1000, 700))

    async def keep_running():
        while not exitteacher:
            await asyncio.sleep(1)

    try:
        asyncio.run(keep_running())
    except (SystemExit, MemoryError, KeyboardInterrupt):
        exitteacher = 1
        os._exit(0)
