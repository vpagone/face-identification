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

class VideoShow:
    """
    Class that continuously shows a frame using a dedicated thread.
    """

    def __init__(self, id, queue, fps, logger, label, stop_event):

        self.id = id
        self.queue = queue
        self.fps = fps
        self.logger = logger
        self.label = label
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

        #raw_frame_window = self.id + '_raw'

        setFaceNames    = {}
        setFaceScores   = {}

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
            message = self.queue.get(timeout=1)

            if ( message is None ):
                break

            data = json.loads(message)
    
            # Extract frame id
            frame_id = data['frame_id']
            
            # Extract and decode the image
            frame = self.decode_frame(data['image'])

            faceBoxesByFrame  = data['boxes']

            faceNamesByFrame  = data['names']
            faceScoresByFrame = data['scores']

            for id in faceNamesByFrame.keys():
                if ( not faceNamesByFrame[id] in setFaceNames ):
                    setFaceNames[id] = faceNamesByFrame[id]
            for id in faceScoresByFrame.keys():
                if ( not faceScoresByFrame[id] in faceScoresByFrame ):
                    setFaceScores[id] = faceScoresByFrame[id]

            self.logger.info('display frame: {}'.format(frame_id))
            self.logger.info('names: {}'.format(faceNamesByFrame))
            self.logger.info('boxes: {}'.format(faceBoxesByFrame))            
            self.logger.info('scores: {}'.format(faceScoresByFrame))

            #cv2.imshow(raw_frame_window, cv2.resize( frame, ( 320, 240) ))

            for fid in faceBoxesByFrame.keys():

                    tracked_position = faceBoxesByFrame[fid]
                    
                    t_x = int(tracked_position[0])
                    t_y = int(tracked_position[1])
                    t_w = int(tracked_position[2])
                    t_h = int(tracked_position[3])

                    if fid in setFaceNames.keys():
                        cv2.rectangle(frame, (t_x, t_y),
                                        (t_x + t_w , t_y + t_h),
                                        (0, 255, 0) ,thickness, cv2.LINE_AA)
                        text = "{0} ({1:.2f})".format(setFaceNames[fid], setFaceScores[fid])
                        cv2.putText(frame, text, 
                                        (int(t_x + t_w/2), int(t_y)), 
                                        font,
                                        scale, green, thickness, cv2.LINE_AA)
                    else:
                        cv2.rectangle(frame, (t_x, t_y),
                                        (t_x + t_w , t_y + t_h),
                                        orange, thickness, cv2.LINE_AA)
                        
            # #print(f'{self.id} before imshow')
            #cv2.imshow(self.id, frame)
            #print(f'{self.id} after imshow')

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

            # 
            if ( elapsed_time < (1/self.fps)):
                 sleep_time = ((1/self.fps) - elapsed_time )
                 time.sleep( sleep_time )
                 self.logger.info('sleeping for: {:.3f} '.format(sleep_time))
 
            # start_time = time.time() 
            # #time.sleep(1/self.fps)  # Update at roughly 20 FPS 
            # #time.sleep(1)
            # # End timer
            # end_time = time.time()
            # print('Woke up after', str(end_time - start_time), 'seconds')


            # if cv2.waitKey(int(1000/self.fps)) == ord("q"):
            #      self.stopped = True
            # img = cv2.resize(frame, (self.canvas.winfo_width(), self.canvas.winfo_height()))
            # img = ImageTk.PhotoImage(image=Image.fromarray(img))

            #img = ImageTk.PhotoImage(image=Image.fromarray(frame))
            #self.canvas.create_image(0, 0, anchor=tk.NW, image=img)
            #self.canvas.image = img

        # if ( not self.output_queue.full() ):
        #     self.output_queue.put(None)
        self.logger.info('Stop')

    def stop(self):
        self.stopped = True
