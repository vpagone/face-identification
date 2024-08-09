import os
import cv2
from core import FaceIdentifier
from threading import Thread, Lock
from multiprocessing import Process
from multiprocessing import Queue
import time
import argparse
from frame_producer import FrameProducer
from video_shower import VideoShow
from video_recorder import VideoRecorder
from detector import FaceDetector
from recognizer import FaceRecognizer

import logging
import errno
import shutil
from config_manager import load_yaml_config
from config_manager import run_config

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Face Identification System')
    parser.add_argument('-c','--config', help='Configuration file full path name', required=True)
    args = vars(parser.parse_args())

    config_path = args['config']
    config = load_yaml_config(config_path)

    run_config(config)


    




