import os
import glob
import cv2
import numpy as np
from tqdm import tqdm
from pathlib import Path
import time
from opensearchpy import OpenSearch

def recognize_face(image, file_name=None):
        channels = 1 if len(image.shape) == 2 else image.shape[2]
        if channels == 1:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        if channels == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        if image.shape[0] > 1000:
            image = cv2.resize(image, (0, 0),
                            fx=500 / image.shape[0], fy=500 / image.shape[0])

        height, width, _ = image.shape
        face_detector.setInputSize((width, height))
        try:
            dts = time.time()
            _, faces = face_detector.detect(image)
            if file_name is not None:
                assert len(faces) > 0, f'the file {file_name} has no face'

            faces = faces if faces is not None else []
            features = []
            ## print(f'{time.time()} time detection  = {time.time() - dts}')
            for face in faces:
                rts = time.time()

                aligned_face = face_recognizer.alignCrop(image, face)
                feat = face_recognizer.feature(aligned_face)
                ## print(f'{time.time()} time recognition  = {time.time() - rts}')

                features.append(feat)
            return features, faces
        except Exception as e:
            print(e)
            print(file_name)
            return None, None

def encode_known_faces( face_detector, face_recognizer ):

    names = []
    encodings = []

    dir = '/home/vito/dev/datasets/archive/lfw-deepfunneled/lfw-deepfunneled'
    for filepath in tqdm(Path(dir).glob("*/*")):
        name = filepath.parent.name
        file = os.path.join(dir, filepath.parent.name, filepath.name)
        image = cv2.imread(file)
        features, faces = recognize_face(image, file)
        if faces is None:
            continue

        index_encoding(name, features[0])

def index_encoding(person_name, face_encoding):

    # Document to insert
    doc = {
        "face_name": person_name,
        "face_encoding": face_encoding[0]
    }

    print(len(face_encoding[0]))
    # Insert the document into the index
    response = client.index(index='face_encodings', body=doc)

    # Print response for confirmation
    print("Document indexed:", response)

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

    #opensearch connection
    client = OpenSearch(
        hosts=[{'host': 'localhost', 'port': 9200}],
        http_auth=('admin', 'Caracas3167!'),
        use_ssl=True,
        verify_certs=False  # Only for testing
    )

    encode_known_faces( face_detector, face_recognizer )
