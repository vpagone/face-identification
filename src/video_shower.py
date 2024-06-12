from threading import Thread
import cv2
import logging
import os

from receive_frame_from_queue import ReceiveFrame

class VideoShow:
    """
    Class that continuously shows a frame using a dedicated thread.
    """

    def __init__(self, id, queue, log_dir):

        self.id = id
        self.queue = queue
        self.stopped = False
        self.log_dir = log_dir

        # self.receive_frame = ReceiveFrame(queue_name)
        # self.receive_frame.init_connection()

 
    def show(self):

        self.logger = logging.getLogger(__name__)
        file_name=path=os.path.join(self.log_dir, __name__ + '.log')
        logging.basicConfig(format='%(levelname)-6s %(asctime)s [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s', 
                            filename=file_name, 
                            level=logging.INFO)

        self.logger.info('Started')

        while not self.stopped:

            #frame = self.receive_frame.receive_frame_from_queue()
            frame = self.queue.get()

            if ( frame is None ):
                break

            #print(f'{self.id} before imshow')
            cv2.imshow(self.id, frame)
            #print(f'{self.id} after imshow')
            if cv2.waitKey(1) == ord("q"):
                self.stopped = True

        self.logger.info('Finished')

    def stop(self):
        self.stopped = True
