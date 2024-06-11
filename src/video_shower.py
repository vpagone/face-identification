from threading import Thread
import cv2

from receive_frame_from_queue import ReceiveFrame

class VideoShow:
    """
    Class that continuously shows a frame using a dedicated thread.
    """

    def __init__(self, id, queue):

        self.id = id
        self.queue = queue
        self.stopped = False

        # self.receive_frame = ReceiveFrame(queue_name)
        # self.receive_frame.init_connection()

    def show(self):

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

    def stop(self):
        self.stopped = True

# test
if __name__ == '__main__':

    id = 'fi-02'
    fs = VideoShow(id + '_queue_out')
    fs.show()