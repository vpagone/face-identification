import pickle
import os
import glob
import cv2
import numpy as np
from tqdm import tqdm
from pathlib import Path
from core import recognize_face

def encode_known_faces( directory, face_detector, face_recognizer ):

    names = []
    encodings = []

    encodings_location = os.path.join(directory, "output", "encodings.pkl")

    names = []
    encodings = []
    for filepath in tqdm(Path("data/images").glob("*/*")):
        name = filepath.parent.name
        file = os.path.join("data/images", filepath.parent.name, filepath.name)
        image = cv2.imread(file)
        features, faces = recognize_face(image, face_detector, face_recognizer, file)
        if faces is None:
            continue

        names.append(name)
        encodings.append(features[0])
        
    name_encodings = {"names": names, "encodings": encodings}
    print(len(names))
    print(len(encodings))
    with Path(encodings_location).open(mode="wb") as f:
        pickle.dump(name_encodings, f)


def load_encoded_known_faces(directory):

    encodings_location = os.path.join(directory, "output", "encodings.pkl")

    with Path(encodings_location).open(mode="rb") as f:
        loaded_encodings = pickle.load(f)

    return loaded_encodings['names'], loaded_encodings['encodings']


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

    encode_known_faces( directory, face_detector, face_recognizer )
    
