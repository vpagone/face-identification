from threading import Thread
import cv2
import logging
import os
import base64
import json
import numpy as np

from receive_frame_from_queue import ReceiveFrame

class VideoShow:
    """
    Class that continuously shows a frame using a dedicated thread.
    """

    def __init__(self, id, queue, fps, log_dir):

        self.id = id
        self.queue = queue
        self.fps = fps
        self.log_dir = log_dir

        self.stopped = False

        # self.receive_frame = ReceiveFrame(queue_name)
        # self.receive_frame.init_connection()

    def decode_frame(self, encoded_frame):
        frame_bytes = base64.b64decode(encoded_frame)
        frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
        return frame
 
    def show(self):

        self.logger = logging.getLogger(__name__)
        file_name=path=os.path.join(self.log_dir, __name__ + '.log')
        logging.basicConfig(format='%(levelname)-6s %(asctime)s [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s', 
                            filename=file_name, 
                            level=logging.INFO)

        self.logger.info('Started')

        raw_frame_window = self.id + '_raw'

        while not self.stopped:

            #frame = self.receive_frame.receive_frame_from_queue()
            #frame = self.queue.get()

            # Decode the JSON message
            message = self.queue.get()

            if ( message is None ):
                break

            data = json.loads(message)
    
            # Extract frame id
            frame_id = data['frame_id']
            
            # Extract and decode the image
            frame = self.decode_frame(data['image'])

            # Extract names
            faceNames = data['names']

            faceBoxes = data['boxes']

            faceScores = data['scores']



            self.logger.info('display frame: {}'.format(frame_id))
            self.logger.info('names: {}'.format(faceNames))
            self.logger.info('boxes: {}'.format(faceBoxes))            
            self.logger.info('scores: {}'.format(faceScores))

            cv2.imshow(raw_frame_window, cv2.resize( frame, ( 320, 240) ))

            for fid in faceBoxes.keys():

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
                        cv2.rectangle(frame, (t_x, t_y),
                                        (t_x + t_w , t_y + t_h),
                                        (0, 255, 0) ,thickness, cv2.LINE_AA)
                        text = "{0} ({1:.2f})".format(faceNames[fid], faceScores[fid])
                        cv2.putText(frame, text, 
                                        (int(t_x + t_w/2), int(t_y)), 
                                        font,
                                        scale, green, thickness, cv2.LINE_AA)
                    else:
                        cv2.rectangle(frame, (t_x, t_y),
                                        (t_x + t_w , t_y + t_h),
                                        orange, thickness, cv2.LINE_AA)
                        
            #print(f'{self.id} before imshow')
            cv2.imshow(self.id, frame)
            #print(f'{self.id} after imshow')
            if cv2.waitKey(int(1000/self.fps)) == ord("q"):
                self.stopped = True

        self.logger.info('Finished')

    def stop(self):
        self.stopped = True
