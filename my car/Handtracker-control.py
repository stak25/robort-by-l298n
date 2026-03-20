import cv2
import mediapipe as mp #short a lakha
import math
import socket

robotAddressPort = ("192.168.1.2", 12345) #vhaiti akhanay ghorar chabi

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

cap = cv2.VideoCapture(0) # 0 means use the default webcam. #gorib achi bolay ak tai achay
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

cv2.namedWindow('Hand Tracking', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Hand Tracking', 1280, 720) #camera ta dakhar jonno

height = 720
width = 1280

center_x = width // 2
center_y = height // 2

top_box_top_left = (center_x - 100, 0)
top_box_bottom_right = (center_x + 100, 200) #Top box = forward

bottom_box_top_left = (center_x - 100, height - 200)
bottom_box_bottom_right = (center_x + 100, height) # Bottom box = back

"""
 ┌─────────────┐
 │   FORWARD   │
 └─────────────┘

      camera

 ┌─────────────┐
 │    BACK     │
 └─────────────┘
 """

while cap.isOpened():#Keep running until the camera stops.
    global turn
    ret, frame = cap.read() #The camera takes one picture (frame).
    if not ret:
        break

    frame = cv2.flip(frame, 1) #mirror

    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) #RGB images

    results = hands.process(image) #landmarks

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing = mp.solutions.drawing_utils
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            landmarks = []
            for landmark in hand_landmarks.landmark:
                x, y, _ = image.shape
                landmarks.append((int(landmark.x * y), int(landmark.y * x)))

            thumb_tip = landmarks[4]
            index_tip = landmarks[8]
            middle_tip = landmarks[12]
            pinky_tip = landmarks[20]

            dist_thumb_index = thumb_tip[0] - index_tip[0]
            dist_index_middle = index_tip[0] - middle_tip[0]
            dist_middle_pinky = middle_tip[0] - pinky_tip[0]

            if dist_thumb_index < 0 and dist_index_middle < 0 and dist_middle_pinky < 0:
                hand_label = "Right Hand"
            else:
                wrist = landmarks[0]
                middle_mcp = landmarks[9]
                cv2.line(frame, wrist, middle_mcp, (0, 255, 0), 2)

                angle = math.atan2(wrist[1] - middle_mcp[1], wrist[0] - middle_mcp[0])
                angle = math.degrees(angle)
                angle -= 90
                if angle <= -180:
                    angle += 360
                elif angle > 180:
                    angle -= 360

                cv2.putText(frame, f"Rotation Angle: {angle:.2f}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

                if angle > 20:
                    hand_label = "Right"
                    turn = True
                    sendTorobot("r")
                elif angle < -20:
                    hand_label = "Left"
                    turn = True
                    sendTorobot("l")
                else:
                    turn = False
                    hand_label = ""

                if (top_box_top_left[0] < landmarks[9][0] < top_box_bottom_right[0] and
                    top_box_top_left[1] < landmarks[9][1] < top_box_bottom_right[1]) and \
                   (top_box_top_left[0] < landmarks[13][0] < top_box_bottom_right[0] and
                    top_box_top_left[1] < landmarks[13][1] < top_box_bottom_right[1]):

                    cv2.putText(frame, f"Forward", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
                    sendTorobot("f")
                    print("Forward")

                elif (bottom_box_top_left[0] < landmarks[9][0] < bottom_box_bottom_right[0] and
                      bottom_box_top_left[1] < landmarks[9][1] < bottom_box_bottom_right[1]) and \
                     (bottom_box_top_left[0] < landmarks[13][0] < bottom_box_bottom_right[0] and
                      bottom_box_top_left[1] < landmarks[13][1] < bottom_box_bottom_right[1]):

                    cv2.putText(frame, f"Back", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
                    sendTorobot("b")
                    print("Back")

                elif turn != True:
                    cv2.putText(frame, f"Stop", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
                    sendTorobot("s")
                    print("Stop")

            cv2.putText(frame, hand_label, (landmarks[0][0], landmarks[0][1]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)

    cv2.rectangle(frame, top_box_top_left, top_box_bottom_right, (0, 0, 255), 2)
    cv2.rectangle(frame, bottom_box_top_left, bottom_box_bottom_right, (0, 0, 255), 2)

    def sendTorobot(move):
        msg4robot = ','.join([move, '150,0,0,0'])
        print(msg4robot)
        bytesToSend = str.encode(msg4robot)
        bufferSize = 1024
        UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        UDPClientSocket.sendto(bytesToSend, robotAddressPort)

    cv2.imshow('Hand Tracking', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()