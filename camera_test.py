# import cv2
# import numpy as np
# import time
#
# recognition_running = False
#
# def get_active_event():
#     try:
#         with open("current_event.txt", "r") as f:
#             data = f.read().strip()
#
#         if data == "":
#             return None
#
#         return int(data)
#
#     except:
#         return None
#
#
# video = cv2.VideoCapture(0)
#
# def generate_frames():
#
#     global recognition_running
#
#     while True:
#
#         if not recognition_running:
#
#             blank = np.ones((480,640,3), dtype=np.uint8) * 200
#             cv2.putText(blank,"Recognition Stopped",(120,240),
#                         cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2)
#
#             ret, buffer = cv2.imencode('.jpg', blank)
#             frame = buffer.tobytes()
#
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#
#             time.sleep(0.2)
#             continue
#
#
#         success, frame = video.read()
#
#         if not success:
#             print("Camera read failed")
#             continue
#
#         ret, buffer = cv2.imencode('.jpg', frame)
#
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

import cv2

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Camera error")
        break

    cv2.imshow("Test", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()