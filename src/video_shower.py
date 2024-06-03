from threading import Thread
import cv2

class VideoShow:
    """
    Class that continuously shows a frame using a dedicated thread.
    """

    def __init__(self, id, frame=None):
        self.id = id
        self.frame = frame
        self.stopped = False

    def start(self):
        Thread(target=self.show, args=()).start()
        return self

    def show(self):
        while not self.stopped:
            if (self.frame is not None):
                #print(f'{self.id} before imshow')
                cv2.imshow("Video " + self.id, self.frame)
                #print(f'{self.id} after imshow')
                if cv2.waitKey(1) == ord("q"):
                    self.stopped = True

    def stop(self):
        self.stopped = True