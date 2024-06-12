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

from encoding_db import encode_known_faces, load_encoded_known_faces
from receive_frame_from_queue import ReceiveFrame
from send_frame_to_queue import SendFrameToQueue

#COSINE_THRESHOLD = 0.5
COSINE_THRESHOLD = 0.45

#The deisred output width and height
OUTPUT_SIZE_WIDTH = 640
OUTPUT_SIZE_HEIGHT = 480

class FaceIdentifier():
  
    def __init__(self, id, directory, input_queue, output_queue, log_dir):

        super().__init__()

        self.id = id
        self.input_queue  = input_queue
        self.output_queue = output_queue
        self.log_dir = log_dir

        # Init models face detection & recognition
        weights = os.path.join(directory, 'models',
                            'face_detection_yunet_2022mar.onnx')

        self.face_detector = cv2.FaceDetectorYN_create(weights, "", (0, 0))
        self.face_detector.setScoreThreshold(0.87)

        weights = os.path.join(directory, 'models', 
                        'face_recognizer_fast.onnx')

        self.face_recognizer = cv2.FaceRecognizerSF_create(weights, "")

        self.names, self.encodings = load_encoded_known_faces(directory)

        # self.receive_frame = ReceiveFrame(id + '_queue')
        # self.receive_frame.init_connection()

        # self.send_frame = SendFrameToQueue(id + '_queue_out')
        # self.send_frame.init_connection()


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
        
                self.logger.info(f' time detection  = {time.time() - dts}')

                return faces
            except Exception as e:
                self.loger.error(e)
                return None


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
            if max_score < COSINE_THRESHOLD:
                #print(f'{time.time()} match: low score = {max_score}')
                return False, ("", 0.0)
            self.logger.info(f' match: score = {max_score}')
            return True, (sim_user_id, max_score)

    def identify_face(self, image, face, faceID, faceNames, faceScores):
    
        #print(f'{time.time()} trying to identify fid: {faceID}')

        # channels = 1 if len(image.shape) == 2 else image.shape[2]
        # if channels == 1:
        #     image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        # if channels == 4:
        #     image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        # if image.shape[0] > 1000:
        #     image = cv2.resize(image, (0, 0),
        #                        fx=500 / image.shape[0], fy=500 / image.shape[0])

        try:
            dts = time.time()

            #faces = faces if faces is not None else []
            features = []

            aligned_face = self.face_recognizer.alignCrop(image, face)
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

    def detectAndTrackMultipleFaces(self):

        self.logger = logging.getLogger(__name__)
        file_name=path=os.path.join(self.log_dir, __name__ + '.log')
        logging.basicConfig(format='%(levelname)-6s %(asctime)s [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s', 
                            filename=file_name, 
                            level=logging.INFO)

        self.logger.info('Started')

        #print(f'{self.id} before capture')

        #capture = cv2.VideoCapture(self.source)



#        self.video_shower.start()

 

        #fps = capture.get(cv2.CAP_PROP_FPS)
        #print("Frames per second using video.get(cv2.CAP_PROP_FPS) : {0}".format(fps))

        #Create two opencv named windows
        #cv2.namedWindow("base-image", cv2.WINDOW_AUTOSIZE)
        #cv2.namedWindow(self.id, cv2.WINDOW_AUTOSIZE)





        #Position the windows next to eachother
        #cv2.moveWindow("base-image",0,100)
        #cv2.moveWindow("result-image",400,100)

        #Start the window thread for the two windows we are using
        #cv2.startWindowThread()

        #The color of the rectangle we draw around the face
        rectangleColor = (0,165,255)

        #variables holding the current frame number and the current faceid
        frameCounter = 0
        currentFaceID = 1

        #Variables holding the correlation trackers and the name per faceid
        faceTrackers = {}
        faceNames    = {}
        faceBoxes    = {}
        faceScores   = {}

        try:

            while True:

                dtot = time.time()

                #Retrieve the latest image from the webcam
                #rc,fullSizeBaseImage = capture.read()

                #fullSizeBaseImage = self.receive_frame.receive_frame_from_queue()
                #baseImage = self.receive_frame.receive_frame_from_queue()
                baseImage = self.input_queue.get()

                if ( baseImage is None ):
                    break

                #Resize the image to 320x240
                #baseImage = cv2.resize( fullSizeBaseImage, ( 320, 240))
                #baseImage = cv2.resize( fullSizeBaseImage, ( 640, 480))

                #baseImage = fullSizeBaseImage.copy()

                #Check if a key was pressed and if it was Q, then break
                #from the infinite loop
                #pressedKey = cv2.waitKey(2)
                #if pressedKey == ord('Q'):
                #    break


                #Result image is the image we will show the user, which is a
                #combination of the original image from the webcam and the
                #overlayed rectangle for the largest face
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


                #Increase the framecounter
                frameCounter += 1 



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
                    faceNames.pop(fid, None)
                    faceScores.pop(fid, None)


                #Every 10 frames, we will have to determine which faces
                #are present in the frame
                if (frameCounter % 10) == 0:


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

                            faceTrackers[ currentFaceID ] = tracker
                            faceBoxes[ currentFaceID ] = box

                            #Start a new thread that is used to simulate 
                            #face recognition. This is not yet implemented in this
                            #version :)
                            #t = threading.Thread( target = identify_face,
                            #                        args=(baseImage, face, face_recognizer, currentFaceID, faceNames, faceScores))
                            #t.start()
                            self.identify_face(baseImage, face, currentFaceID, faceNames, faceScores)

                            #Increase the currentFaceID counter
                            currentFaceID += 1
                        else:
                            if matchedFid in unusedTrackers:
                                unusedTrackers.remove(matchedFid)
                            if not (matchedFid in faceNames) :
                            #     t = threading.Thread( target = identify_face,
                            #                        args=(baseImage, face, face_recognizer, matchedFid, faceNames, faceScores))
                            #     t.start()
                                self.identify_face(baseImage, face, matchedFid, faceNames, faceScores)

                    for fid in unusedTrackers:
                        #print(f'{self.id} Removing fid " + {str(fid)} from list of trackers')
                        faceTrackers.pop( fid , None )
                        faceBoxes.pop(fid, None)
                        faceNames.pop(fid, None)
                        faceScores.pop(fid, None)

                #Now loop over all the trackers we have and draw the rectangle
                #around the detected faces. If we 'know' the name for this person
                #(i.e. the recognition thread is finished), we print the name
                #of the person, otherwise the message indicating we are detecting
                #the name of the person
                for fid in faceTrackers.keys():

                    tracked_position = faceBoxes[fid]
                    
                    t_x = int(tracked_position[0])
                    t_y = int(tracked_position[1])
                    t_w = int(tracked_position[2])
                    t_h = int(tracked_position[3])

                    thickness = 2
                    scale = 0.6
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    green = (0, 255, 0)
                    orange = (0, 165, 255)

                    if fid in faceNames.keys():
                        cv2.rectangle(resultImage, (t_x, t_y),
                                        (t_x + t_w , t_y + t_h),
                                        (0, 255, 0) ,thickness, cv2.LINE_AA)
                        text = "{0} ({1:.2f})".format(faceNames[fid], faceScores[fid])
                        cv2.putText(resultImage, text, 
                                        (int(t_x + t_w/2), int(t_y)), 
                                        font,
                                        scale, green, thickness, cv2.LINE_AA)
                    else:
                        cv2.rectangle(resultImage, (t_x, t_y),
                                        (t_x + t_w , t_y + t_h),
                                        orange, thickness, cv2.LINE_AA)
                        #cv2.putText(resultImage, "???" , 
                        #                (int(t_x + t_w/2), int(t_y)), 
                        #                font,
                        #                scale, (0, 165, 255), thickness, cv2.LINE_AA)

                #Since we want to show something larger on the screen than the
                #original 320x240, we resize the image again
                #
                #Note that it would also be possible to keep the large version
                #of the baseimage and make the result image a copy of this large
                #base image and use the scaling factor to draw the rectangle
                #at the right coordinates.

                largeResult = cv2.resize(resultImage,
                                        (OUTPUT_SIZE_WIDTH,OUTPUT_SIZE_HEIGHT))
                


                #Finally, we want to show the images on the screen
                #cv2.imshow("base-image", baseImage)
                #if (self.id == 'fi-01'):
                #    cv2.imshow(self.id, largeResult)
                #self.video_shower.frame = largeResult
                #self.send_frame.send_frame_to_queue(resultImage)
                self.output_queue.put(resultImage)
                

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

