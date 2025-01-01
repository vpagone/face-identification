import cv2
import logging
import os

import base64
import json
import time

from send_frame_to_queue import SendFrameToQueue

class FrameProducer:
    def __init__(self, video_path, frame_queue, logger, stop_event):
        self.video_path = video_path
        self.frame_queue = frame_queue
        self.stop_flag = False
        self.logger = logger
        self.stop_event = stop_event

    def encode_frame(self, frame):
        _, buffer = cv2.imencode('.jpg', frame)
        encoded_frame = base64.b64encode(buffer).decode('utf-8')
        return encoded_frame

    def read_frames(self):
        """Thread function to read frames from the video file and put them in the queue."""
        self.logger.info('Started')

        # # check id video_path is a number (local webcam)
        # if ( self.video_path.isnumeric() ):
        #     cap = cv2.VideoCapture(int(self.video_path))
        # else:
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            print("Error: Could not open " + self.video_path)
#            exit()

        frame_id = 1

#        while not self.stop_flag:
        while not self.stop_event.is_set():
            
            ret, frame = cap.read()
            if not ret:
                print(f"End of video: {self.video_path}")
                break

            resized = cv2.resize( frame, ( 640, 480) )

            #Encode the image to Base64
            encoded_image = self.encode_frame(resized)

            # self.frame_queue.put(frame)

            # Create the JSON object
            json_object = json.dumps({
                'frame_id' : frame_id,
                'names': [],
                'image': encoded_image
            })
    
            # Put the JSON object into the queue
            # while self.frame_queue.full():
            #     time.sleep(0.01)  # Sleep briefly if the queue is full
            #     if self.stop_event.is_set():
            #          break
                
            # if ( not self.frame_queue.full() ):
            #     self.frame_queue.put(json_object, )
            #     self.logger.info( 'Put frame {}'.format(frame_id) )
            #     frame_id += 1
            self.frame_queue.send_frame_to_queue(json_object)
            self.logger.info( 'Put frame {}'.format(frame_id) )
            frame_id += 1

        cap.release()
        
        # if ( not self.frame_queue.full() ):
        #     self.frame_queue.put(None)
        #self.frame_queue.send_frame_to_queue(None)

        self.frame_queue.send_frame_to_queue(None)

        self.logger.info('Stop')

    def stop(self):
        """Set the stop flag to stop the video reading thread."""
        self.stop_flag = True