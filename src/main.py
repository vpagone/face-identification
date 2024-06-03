import os
import cv2
from core import FaceIdentifier
from threading import Thread, Lock
from multiprocessing import Process
import time
from frame_producer import FrameProducer

if __name__ == '__main__':

    #load configuration file
    # contain npy for embedings and registration photos
    directory = 'data'

    #source = '/home/vito/r/videocamara/1692502753042.mp4'
    #source = '/home/vito/r/videocamara/1692606706027.mp4'

    source = '/home/vito/r/videocamara/1682921183173.mp4'
    #source = 0
    id = 'fi-01'
    fp_1 = FrameProducer(source, id + '_queue')
    fi_1 = FaceIdentifier(id, directory, source)

    source = '/home/vito/r/videocamara/1692455074607.mp4'
    #source = 0
    id = 'fi-02'
    fp_2 = FrameProducer(source, id + '_queue')
    fi_2 = FaceIdentifier(id, directory, source)

 
    # start processes
    fp_proc_1 = Process(target = fp_1.produce)
    fp_proc_1.start()
    time.sleep(1)
    fi_proc_1 = Process(target = fi_1.detectAndTrackMultipleFaces)
    fi_proc_1.start()

    fp_proc_2 = Process(target = fp_2.produce)
    fp_proc_2.start()
    time.sleep(1)
    fi_proc_2 = Process(target = fi_2.detectAndTrackMultipleFaces)
    fi_proc_2.start()
   
    fp_proc_1.join()
    fi_proc_1.join()

    fp_proc_2.join()
    fi_proc_2.join()

    




