#!/usr/bin/python

#Import the OpenCV and dlib libraries
from threading import Thread
import os
import time
import cv2
import numpy as np
from pathlib import Path
import logging
import base64
import json

from encoding_db import encode_known_faces, load_encoded_known_faces
from receive_frame_from_queue import ReceiveFrame
from send_frame_to_queue import SendFrameToQueue
from constants import FRAME_INTERVAL

COSINE_THRESHOLD = 0.45

class FaceDetector():
  
    def __init__(self, id, directory, input_queue, output_queue, logger, stop_event):

        super().__init__()

        self.id = id
        self.input_queue  = input_queue
        self.output_queue = output_queue
        self.logger = logger
        self.stop_event = stop_event

        # Init models face detection & recognition
        weights = os.path.join(directory, 'models',
                            'face_detection_yunet_2022mar.onnx')

        self.face_detector = cv2.FaceDetectorYN_create(weights, "", (0, 0))
        self.face_detector.setScoreThreshold(0.87)

        weights = os.path.join(directory, 'models', 
                        'face_recognizer_fast.onnx')

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

    def detect_faces(self, image):

            channels = 1 if len(image.shape) == 2 else image.shape[2]
            if channels == 1:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            if channels == 4:
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

            if image.shape[0] > 1000:
                image = cv2.resize(image, (0, 0),
                                fx=500 / image.shape[0], fy=500 / image.shape[0])

            height, width, _ = image.shape
            self.face_detector.setInputSize((width, height))
            try:
                dts = time.time()
                _, faces = self.face_detector.detect(image)

                faces = faces if faces is not None else []
        
                self.logger.info("time detection = {:.3f}".format(time.time() - dts))

                return faces
            except Exception as e:
                self.logger.error(e)
                return None

    def detectAndTrackMultipleFaces(self):

        # self.logger = logging.getLogger(type(self).__name__)

        # file_name=path=os.path.join(self.log_dir, type(self).__name__ + '.log')
        # logging.basicConfig(format='%(levelname)-6s %(asctime)s [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s', 
        #                     filename=file_name, 
        #                     level=logging.INFO)

        self.logger.info('Started')

        #variables holding the current frame number and the current faceid
        currentFaceID = 1

        #Variables holding the correlation trackers and the name per faceid
        faceTrackers = {}
        faceBoxes    = {}
        facesDetect  = {}

        try:

            #while not self.stop_flag:
            while not self.stop_event.is_set():

                dtot = time.time()

                # Decode the JSON message
                #message = self.input_queue.get(True)
                message = self.input_queue.receive_frame_from_queue()

                if ( message is None ):
                    time.sleep(0.01)
                    continue

                data = json.loads(message)

                # Extract frame id
                frame_id = data['frame_id']

                self.logger.info( 'Get frame {}'.format(frame_id) )

                baseImage = self.decode_frame(data['image'])

                resultImage = baseImage.copy()

                #STEPS:
                # * Update all trackers and remove the ones that are not 
                #   relevant anymore
                # * Every 10 frames:
                #       + Use face detection on the current frame and look
                #         for faces. 
                #       + For each found face, check if centerpoint is within
                #         existing tracked box. If so, nothing to do
                #       + If centerpoint is NOT in existing tracked box, then
                #         we add a new tracker with a new face-id

                #Update all the trackers and remove the ones for which the update
                #indicated the quality was not good enough
                fidsToDelete = []
                dtu = time.time()
                for fid in faceTrackers.keys():
                    
                    #print(f'{self.id} before update')
                    ok, tracked_position = faceTrackers[ fid ].update(baseImage)
                    #print(f'{self.id} after update')

                    #If the tracking quality is good enough, we must delete
                    #this tracker
                    if not ok:
                        fidsToDelete.append( fid )
                    else:
                        faceBoxes[fid] = tracked_position
                #print(f'{time.time()} time update = {time.time() - dtu}')

                for fid in fidsToDelete:

                    #print(f'{self.id} Removing fid " + {str(fid)} from list of trackers')
                    faceTrackers.pop( fid , None )
                    faceBoxes.pop(fid, None)

                #Every 10 frames, we will have to determine which faces
                #are present in the frame
                if (frame_id % FRAME_INTERVAL) == 0:

                    #For the face detection, we need to make use of a gray
                    #colored image so we will convert the baseImage to a
                    #gray-based image
                    #gray = cv2.cvtColor(baseImage, cv2.COLOR_BGR2GRAY)
                    #Now use the haar cascade detector to find all faces
                    #in the image
                    faces = self.detect_faces(baseImage)
                    #faces = faceCascade.detectMultiScale(gray, 1.3, 5)



                    #Loop over all faces and check if the area for this
                    #face is the largest so far
                    #We need to convert it to int here because of the
                    #requirement of the dlib tracker. If we omit the cast to
                    #int here, you will get cast errors since the detector
                    #returns numpy.int32 and the tracker requires an int

                    unusedTrackers = []
                    for fid in faceTrackers.keys():
                        unusedTrackers.append(fid)

                    for face in faces:
                        

                        box = list(map(int, face[:4]))
                        (x,y,w,h) = box


                        #calculate the centerpoint
                        x_bar = x + 0.5 * w
                        y_bar = y + 0.5 * h


                        #Variable holding information which faceid we 
                        #matched with
                        matchedFid = None

                        #Now loop over all the trackers and check if the 
                        #centerpoint of the face is within the box of a 
                        #tracker
                        for fid in faceTrackers.keys():

                            #ok, tracked_position = tracker.update(baseImage)
                            tracked_position = faceBoxes[fid]
                            t_x = int(tracked_position[0])
                            t_y = int(tracked_position[1])
                            t_w = int(tracked_position[2])
                            t_h = int(tracked_position[3])

                            #calculate the centerpoint
                            t_x_bar = t_x + 0.5 * t_w
                            t_y_bar = t_y + 0.5 * t_h

                            #check if the centerpoint of the face is within the 
                            #rectangleof a tracker region. Also, the centerpoint
                            #of the tracker region must be within the region 
                            #detected as a face. If both of these conditions hold
                            #we have a match
                            if ( ( t_x <= x_bar   <= (t_x + t_w)) and 
                                ( t_y <= y_bar   <= (t_y + t_h)) and 
                                ( x   <= t_x_bar <= (x   + w  )) and 
                                ( y   <= t_y_bar <= (y   + h  ))):
                                matchedFid = fid

                        #If no matched fid, then we have to create a new tracker
                        if matchedFid is None:

                            #print(f'{self.id} Creating new tracker {str(currentFaceID)}')

                            #Create and store the tracker
                            # Choose the tracker you want to use, for example, KCF or CSRT
                            #tracker = cv2.TrackerKCF_create()  # no!
                            #tracker = cv2.TrackerCSRT_create()  # lento, pero bueno
                            #tracker = cv2.legacy.TrackerMOSSE_create()
                            tracker = cv2.legacy.TrackerMedianFlow_create() # bueno!!!
                            tracker.init(baseImage, box)
                            # tracker = dlib.correlation_tracker()
                            # tracker.start_track(baseImage,
                            #                     dlib.rectangle( x-10,
                            #                                     y-20,
                            #                                     x+w+10,
                            #                                     y+h+20))

                            # self.logger.info(f'face:\n {face}')
                            # self.logger.info(f'face.tolist:\n {face.tolist()}')

                            faceTrackers[ currentFaceID ] = tracker
                            faceBoxes[ currentFaceID ]    = box
                            facesDetect[ currentFaceID ]  = face.tolist()

                            #Increase the currentFaceID counter
                            currentFaceID += 1
                        else:
                            if matchedFid in unusedTrackers:
                                unusedTrackers.remove(matchedFid)
                            facesDetect[ matchedFid ]  = face.tolist()
                          

                    for fid in unusedTrackers:
                        #print(f'{self.id} Removing fid " + {str(fid)} from list of trackers')
                        faceTrackers.pop( fid , None )
                        faceBoxes.pop(fid, None)

                                
                # Create the JSON object
                # json_object = json.dumps({
                #     'frame_id'     : frame_id,
                #     'boxes'        : faceBoxes,
                #     'facesDetect'  : facesDetect,
                #     'image'        : encoded_image
                # })
                data['facesDetect'] = facesDetect
                data['boxes'] = faceBoxes
                json_object = json.dumps(data)

                #self.output_queue.put(json_object)

                # Put the JSON object into the queue
                # while self.output_queue.full():
                #     time.sleep(0.01)  # Sleep briefly if the queue is full
                #     if self.stop_event.is_set():
                #         break
                    
                # if ( not self.output_queue.full() ):
                #     self.output_queue.put(json_object)
                #     self.logger.info( 'Put frame {}'.format(frame_id) )

                elapsed = time.time() - dtot
                #self.logger.info(f'time total = {elapsed} estimated fps: {1/elapsed}')
                self.logger.info("time total = {:.3f} estimated fps: {:.3f}".format(elapsed, 1/elapsed))

                self.output_queue.send_frame_to_queue(json_object)
                self.logger.info( 'Put frame {}'.format(frame_id) )

        #To ensure we can also deal with the user pressing Ctrl-C in the console
        #we have to check for the KeyboardInterrupt exception and break out of
        #the main loop
        except KeyboardInterrupt as e:
            pass

        #Destroy any OpenCV windows and exit the application
        #cv2.destroyAllWindows()
        #exit(0)

        self.output_queue.send_frame_to_queue(None)

        self.logger.info('Stop')


