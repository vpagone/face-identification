import cv2
import logging
import os

import base64
import json

from send_frame_to_queue import SendFrameToQueue

class FrameProducer():

    def __init__(self, id, source, queue, logger):
                
        self.id = id
        self.source = source
        self.queue = queue
        self.logger = logger

    def encode_frame(self, frame):
        _, buffer = cv2.imencode('.jpg', frame)
        encoded_frame = base64.b64encode(buffer).decode('utf-8')
        return encoded_frame

    def produce(self):

        # self.logger = logging.getLogger(type(self).__name__)

        # file_name=path=os.path.join(self.log_dir, type(self).__name__ + '.log')
        # logging.basicConfig(format='%(levelname)-6s %(asctime)s [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s', 
        #                     filename=file_name, 
        #                     level=logging.INFO)

        self.logger.info('Started')

        # sendFrame = SendFrameToQueue(self.queue_name)
        # sendFrame.init_connection()

        # Create a VideoCapture object
        cap = cv2.VideoCapture(self.source)

        fps = cap.get(cv2.CAP_PROP_FPS)
        self.logger.info("Frames per second: {}".format(fps))

        # Check if the video file was opened successfully
        if not cap.isOpened():
            self.logger.fatal("Error: Could not open video.")
            exit()

        frame_id = 1
        # Read until the video is completed
        while cap.isOpened():
            # Capture frame-by-frame
            ret, frame = cap.read()

            if not ret:
                self.logger.info("End of video or error in frame capture.")
                break

            # send frame to queue
            resized = cv2.resize( frame, ( 640, 480) )
            #sendFrame.send_frame_to_queue(resized)
            #cv2.imshow(self.queue_name, frame)
            #self.queue.put(resized)

            # Encode the image to Base64
            encoded_image = self.encode_frame(resized)
            
            # Create the JSON object
            json_object = json.dumps({
                'frame_id' : frame_id,
                'names': [],
                'image': encoded_image
            })
    
            # Put the JSON object into the queue
            self.queue.put(json_object)

            self.logger.info( 'Put frame {}'.format(frame_id) )

            frame_id += 1

            # Press 'q' on the keyboard to exit the loop
            if cv2.waitKey(25) & 0xFF == ord('q'):
               break

        # When everything is done, release the video capture object and close all OpenCV windows
        cap.release()
        self.queue.put(None)

        self.logger.info('Finished')

# test
if __name__ == '__main__':
    source = '/home/vito/r/videocamara/1692455074607.mp4'
    # source = 0
    id = 'fi-01'
    fp = FrameProducer(source, id + '_queue')
    fp.produce()

#     sendFrame = SendFrameToQueue(id + '_queue')
#     sendFrame.init_connection()

#     # Open the video file
#     cap = cv2.VideoCapture(source)

#     # Check if video opened successfully
#     if not cap.isOpened():
#         print("Error: Could not open video.")
#         exit()

#     # Read until video is completed
#     while cap.isOpened():
#         # Capture frame-by-frame
#         ret, frame = cap.read()
        
        
#         if ret:

#             baseImage = cv2.resize( frame, ( 640, 480) )

#             sendFrame.send_frame_to_queue(baseImage)

#             # Display the resulting frame
#             #cv2.imshow('Video', baseImage)

#             # Press 'q' to exit the video window early
#             if cv2.waitKey(25) & 0xFF == ord('q'):
#                 break
#         else:
#             break

#     # When everything done, release the video capture object
#     cap.release()

# # Close all OpenCV windows
# cv2.destroyAllWindows()
