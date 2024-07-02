#!/usr/bin/python

#Import the OpenCV and dlib libraries
from threading import Thread
import os
import sys
import glob
import time
import math
import cv2
import numpy as np
from tqdm import tqdm
import pickle
from pathlib import Path
import logging
import base64
import json
import hashlib

from encoding_db import encode_known_faces, load_encoded_known_faces
from receive_frame_from_queue import ReceiveFrame
from send_frame_to_queue import SendFrameToQueue

#COSINE_THRESHOLD = 0.5
COSINE_THRESHOLD = 0.45

#The deisred output width and height
OUTPUT_SIZE_WIDTH = 640
OUTPUT_SIZE_HEIGHT = 480

class FaceRecognizer():
  
    def __init__(self, id, directory, input_queue, output_queue_list, log_dir):

        super().__init__()

        self.id = id
        self.input_queue  = input_queue
        self.output_queue_list = output_queue_list
        self.log_dir = log_dir

        # Init models face detection & recognition
        weights = os.path.join(directory, 'models',
                            'face_detection_yunet_2022mar.onnx')

        # self.face_detector = cv2.FaceDetectorYN_create(weights, "", (0, 0))
        # self.face_detector.setScoreThreshold(0.87)

        weights = os.path.join(directory, 'models', 
                        'face_recognizer_fast.onnx')

        self.face_recognizer = cv2.FaceRecognizerSF_create(weights, "")

        self.names, self.encodings = load_encoded_known_faces(directory)

        # self.receive_frame = ReceiveFrame(id + '_queue')
        # self.receive_frame.init_connection()

        # self.send_frame = SendFrameToQueue(id + '_queue_out')
        # self.send_frame.init_connection()

    def encode_frame(self, frame):
        _, buffer = cv2.imencode('.jpg', frame)
        encoded_frame = base64.b64encode(buffer).decode('utf-8')
        return encoded_frame

    def decode_frame(self, encoded_frame):
        frame_bytes = base64.b64decode(encoded_frame)
        frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
        return frame

    # #We are not doing really face recognition
    # def doRecognizePerson(faceNames, fid):
    #     time.sleep(2)
    #     faceNames[ fid ] = "Person " + str(fid)


    def match(self, feature1):

            max_score = 0.0
            sim_user_id = ""
            for user_id, feature2 in zip(self.names, self.encodings):
                score = self.face_recognizer.match(
                    feature1, feature2, cv2.FaceRecognizerSF_FR_COSINE)
                if score >= max_score:
                    max_score = score
                    sim_user_id = user_id

#           self.logger.info(f'match: feature1 = {feature1}\nscore = {max_score}')

            if max_score < COSINE_THRESHOLD:
                #print(f'{time.time()} match: low score = {max_score}')
                return False, ("", 0.0)
            return True, (sim_user_id, max_score)

    def identify_face(self, image, face, faceID, faceNames, faceScores):

        # channels = 1 if len(image.shape) == 2 else image.shape[2]
        # if channels == 1:
        #     image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        # if channels == 4:
        #     image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        # if image.shape[0] > 1000:
        #     image = cv2.resize(image, (0, 0),
        #                     fx=500 / image.shape[0], fy=500 / image.shape[0])
    
        self.logger.info(f' faceID = {faceID} face = {face}')

        # readable_hash = hashlib.md5(image).hexdigest()
        # self.logger.info(f' readable_hash = {readable_hash}')

        try:
            dts = time.time()

            #faces = faces if faces is not None else []
            features = []

            face = np.float32(face)
            aligned_face = self.face_recognizer.alignCrop(image, face)

#            self.logger.info(f' aligned face = {aligned_face}')

            feat = self.face_recognizer.feature(aligned_face)

            rts = time.time()

            result, (sim_user_id, max_score) = self.match(feat)

            if result:
                faceNames[ faceID ]  = sim_user_id
                faceScores[ faceID ] = max_score         

            rts = time.time()

            self.logger.info(f' time identification  = {time.time() - rts}')

            return result  
        except Exception as e:
            self.logger.error(e)
            return None

    def recognizeMultipleFaces(self):

        self.logger = logging.getLogger(__name__)
        file_name=path=os.path.join(self.log_dir, __name__ + '.log')
        logging.basicConfig(format='%(levelname)-6s %(asctime)s [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s', 
                            filename=file_name, 
                            level=logging.INFO)

        self.logger.info('Started')

        #Variables holding the correlation trackers and the name per faceid
        faceNames    = {}
        faceScores   = {}

        try:

            while True:



                dtot = time.time()

                # Decode the JSON message
                message = self.input_queue.get()

                if ( message is None ):
                    break

                data = json.loads(message)
        
                # Extract frame id
                frame_id = data['frame_id']
                self.logger.info( 'Get frame {}'.format(frame_id) )

                baseImage = self.decode_frame(data['image'])

                #For the face detection, we need to make use of a gray
                #colored image so we will convert the baseImage to a
                #gray-based image
                #gray = cv2.cvtColor(baseImage, cv2.COLOR_BGR2GRAY)
                #Now use the haar cascade detector to find all faces
                #in the image
                faceBoxes   = data['boxes']
                facesDetect = data['facesDetect']

                self.logger.info('display frame: {}'.format(frame_id))
                self.logger.info('detect: {}'.format(facesDetect))
                self.logger.info('boxes: {}'.format(faceBoxes))            

                if ( frame_id % 10 == 0):
                    for faceId in faceBoxes.keys():
                        self.identify_face(baseImage, np.array(facesDetect[faceId]), faceId, faceNames, faceScores)

                encoded_image = self.encode_frame(baseImage)
                
                # Create the JSON object
                json_object = json.dumps({
                    'frame_id' : frame_id,
                    'names'  : faceNames,
                    'boxes'  : faceBoxes,
                    'scores' : faceScores,
                    'image'  : encoded_image
                })

                for output_queue in self.output_queue_list:
                    output_queue.put(json_object)

                elapsed = time.time() - dtot
                self.logger.info(f'time total = {elapsed} estimated fps: {1/elapsed}')


        #To ensure we can also deal with the user pressing Ctrl-C in the console
        #we have to check for the KeyboardInterrupt exception and break out of
        #the main loop
        except KeyboardInterrupt as e:
            pass

        #Destroy any OpenCV windows and exit the application
        #cv2.destroyAllWindows()
        #exit(0)
