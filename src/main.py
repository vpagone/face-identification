import os
import cv2
import threading

from encoding_db import encode_known_faces, load_encoded_known_faces
from core import detectAndTrackMultipleFaces


if __name__ == '__main__':

    # contain npy for embedings and registration photos
    directory = 'data'

    # Init models face detection & recognition
    weights = os.path.join(directory, "models",
                           "face_detection_yunet_2022mar.onnx")
    face_detector = cv2.FaceDetectorYN_create(weights, "", (0, 0))
    face_detector.setScoreThreshold(0.87)

    weights = os.path.join(directory, "models", "face_recognizer_fast.onnx")
    face_recognizer = cv2.FaceRecognizerSF_create(weights, "")

    names, encodings = load_encoded_known_faces(directory)

    #source = 0 # first webcam
    source = '/home/vito/r/videocamara/1682921183173.mp4'
    #source = '/home/vito/r/videocamara/1692455074607.mp4'
    #source = '/home/vito/r/videocamara/1692502753042.mp4'
    #source = '/home/vito/r/videocamara/1692606706027.mp4'

    t = threading.Thread( target = detectAndTrackMultipleFaces,
                    args=(source, face_detector, face_recognizer, names, encodings))
    t.start()
    #detectAndTrackMultipleFaces(source, face_detector, face_recognizer, names, encodings)

