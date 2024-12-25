from threading import Thread
import cv2
import logging
import os
import base64
import json
import numpy as np
import time
from PyQt5.QtCore import Qt, pyqtSlot, QMetaObject, Q_ARG
from PyQt5.QtGui import QImage, QPixmap

from PIL import Image, ImageTk

class SimpleVideoShow:
    """
    Class that continuously shows a frame using a dedicated thread.
    """

    def __init__(self, id, input_queue, output_queue, fps, logger, label, list_widget, stop_event):

        self.id = id
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.fps = fps
        self.logger = logger
        self.label = label
        self.list_widget = list_widget
        self.stop_event = stop_event

        # self.receive_frame = ReceiveFrame(queue_name)
        # self.receive_frame.init_connection()

    def decode_frame(self, encoded_frame):
        frame_bytes = base64.b64decode(encoded_frame)
        frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
        return frame
 
    def show(self):

        # self.logger = logging.getLogger(__name__)
        # file_name=path=os.path.join(self.log_dir, __name__ + '.log')
        # logging.basicConfig(format='%(levelname)-6s %(asctime)s [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s', 
        #                     filename=file_name, 
        #                     level=logging.INFO)

        self.logger.info('Started')

        thickness = 2
        scale = 0.6
        font = cv2.FONT_HERSHEY_SIMPLEX
        green = (0, 255, 0)
        orange = (0, 165, 255)

#        while not self.stopped:
        while not self.stop_event.is_set():

            # Start timer
            start_time = time.time() 

            # Decode the JSON message

            #message = self.input_queue.get(True)
            message = self.input_queue.receive_frame_from_queue()

            if ( message is None ):
                time.sleep(0.01)
                continue

            # Decode the JSON message
            data = json.loads(message)
    
            # Extract frame id
            frame_id = data['frame_id']

            self.logger.info( 'Get frame {}'.format(frame_id) )
            
            # Extract and decode the image
            frame = self.decode_frame(data['image'])

            seconds, _ = divmod(frame_id, self.fps)
            minutes, remaining_seconds = divmod(seconds, 60)

            # Convert the frame from OpenCV (BGR) to QImage (RGB)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = frame_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)

            # Update the QLabel in the main thread using QMetaObject.invokeMethod
            QMetaObject.invokeMethod(
                self.label, "setPixmap", Qt.QueuedConnection,
                Q_ARG(QPixmap, QPixmap.fromImage(qt_image))
            )

            # End timer
            end_time = time.time()
            elapsed_time = end_time - start_time

            self.logger.info('display time: {:.3f} '.format(elapsed_time))

            if ( elapsed_time < (1/self.fps)):
                 sleep_time = ((1/self.fps) - elapsed_time )
                 #time.sleep( sleep_time )
                 #self.logger.info('sleeping for: {:.3f} '.format(sleep_time))
 
            self.output_queue.send_frame_to_queue(message)

        self.logger.info('Stop')
#        self.output_queue.send_frame_to_queue(None)

    def stop(self):
        self.stopped = True
