import cv2

detector = cv2.FaceDetectorYN.create(
    "models/yunet.onnx",
    "",
    (320,320)
)

print("YuNet Loaded Successfully ✅")