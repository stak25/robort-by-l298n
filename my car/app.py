from flask import Flask, Response
import cv2
import mediapipe as mp
import math
import socket

app = Flask(__name__)

robotAddressPort = ("192.168.1.2", 12345)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

height = 720
width = 1280

center_x = width // 2
center_y = height // 2

top_box_top_left = (center_x - 100, 0)
top_box_bottom_right = (center_x + 100, 200)

bottom_box_top_left = (center_x - 100, height - 200)
bottom_box_bottom_right = (center_x + 100, height)

def sendTorobot(move):
    msg4robot = ','.join([move, '150,0,0,0'])
    bytesToSend = str.encode(msg4robot)

    UDPClientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    UDPClientSocket.sendto(bytesToSend, robotAddressPort)

def generate():

    while True:

        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame,1)

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(image)

        if results.multi_hand_landmarks:

            for hand_landmarks in results.multi_hand_landmarks:

                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

                landmarks = []

                for landmark in hand_landmarks.landmark:
                    h, w, _ = frame.shape
                    landmarks.append((int(landmark.x * w), int(landmark.y * h)))

                wrist = landmarks[0]
                middle_mcp = landmarks[9]

                cv2.line(frame, wrist, middle_mcp, (0,255,0),2)

                angle = math.atan2(
                    wrist[1] - middle_mcp[1],
                    wrist[0] - middle_mcp[0]
                )

                angle = math.degrees(angle) - 90

                if angle > 20:
                    sendTorobot("r")
                    cv2.putText(frame,"Right",(50,50),
                                cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2)

                elif angle < -20:
                    sendTorobot("l")
                    cv2.putText(frame,"Left",(50,50),
                                cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2)

        cv2.rectangle(frame, top_box_top_left, top_box_bottom_right,(0,0,255),2)
        cv2.rectangle(frame, bottom_box_top_left, bottom_box_bottom_right,(0,0,255),2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' +
               frame + b'\r\n')

@app.route('/')
def video():
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)