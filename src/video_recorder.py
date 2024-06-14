from threading import Thread
import cv2
import logging
import os
import base64
import json
import numpy as np

class VideoRecorder:
    """
    Class that continuously shows a frame using a dedicated thread.
    """

    def __init__(self, id, queue, window_frame, log_dir, out_dir):

        self.id = id
        self.queue = queue
        self.stopped = False
        self.log_dir = log_dir
        self.out_dir = out_dir

        # self.receive_frame = ReceiveFrame(queue_name)
        # self.receive_frame.init_connection()

    def decode_frame(self, encoded_frame):
        frame_bytes = base64.b64decode(encoded_frame)
        frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
        return frame
 
    def record(self):

        self.logger = logging.getLogger(__name__)
        file_name=path=os.path.join(self.log_dir, __name__ + '.log')
        logging.basicConfig(format='%(levelname)-6s %(asctime)s [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s', 
                            filename=file_name, 
                            level=logging.INFO)

        self.logger.info('Started')

        while not self.stopped:

            #frame = self.receive_frame.receive_frame_from_queue()
            #frame = self.queue.get()

            # Decode the JSON message
            message = self.queue.get()
            data = json.loads(message)
    
            # Extract frame id
            frame_id = data['frame_id']

            names = data['names']
            
            # Extract and decode the image
            frame = self.decode_frame(data['image'])

            if ( frame is None ):
                break

            # #print(f'{self.id} before imshow')
            # cv2.imshow(self.id, frame)
            # #print(f'{self.id} after imshow')
            # if cv2.waitKey(1) == ord("q"):
            #     self.stopped = True

            self.logger.info('display frame: {} {}'.format(frame_id, names))

        self.logger.info('Finished')

    def stop(self):
        self.stopped = True
