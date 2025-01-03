import sys
import cv2
import logging
import threading
import queue
import os
import json
import base64
import numpy as np
from PyQt5.QtCore import Qt, pyqtSlot, QMetaObject, Q_ARG
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QFileDialog, QListWidget

from config_manager import load_yaml_config, create_log_out_dir
from frame_producer import FrameProducer
from detector import FaceDetector
from recognizer import FaceRecognizer
from video_recorder import VideoRecorder
from video_shower import VideoShow
from simple_video_shower import SimpleVideoShow
from video_decorator import VideoDecorator

from rmq_queue_manager import RmqQueueManager

def get_thread_logger(log_dir, log_name):
    """Get or create a logger for the current thread."""
    if not hasattr(thread_local, 'logger'):
        # Generate a unique log file name based on the thread name
        log_file_name=path=os.path.join(log_dir, log_name + '.log')
        # print(log_dir)
        # print(log_file_name)

        # Create a logger
        logger = logging.getLogger(threading.current_thread().name)
        logger.setLevel(logging.DEBUG)

        # Create a file handler for the logger
        handler = logging.FileHandler(log_file_name)
        handler.setLevel(logging.INFO)

        # Create a logging format
        formatter = logging.Formatter('%(levelname)-6s %(asctime)s [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s')
        handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(handler)

        # Save the logger in the thread-local storage
        thread_local.logger = logger

    return thread_local.logger

class VideoPlayer(QWidget):

    def __init__(self):

        super().__init__()

        # Create 4 queue managers to hold video frames produced by readers
        self.frame_queues_1 = [RmqQueueManager("reader_output_queue_" + str(i)) for i in range(4)]
        for queue in self.frame_queues_1:
            queue.init_connection()

        # Create 4 queue managers to hold video frames produced by detectors
        self.frame_queues_2 = [RmqQueueManager("detector_output_queue_" + str(i)) for i in range(4)]
        for queue in self.frame_queues_2:
            queue.init_connection()

        # Create 4 queue managers to hold video frames produced by recognizers
        self.frame_queues_3 = [RmqQueueManager("recognizer_output_queue_" + str(i)) for i in range(4)]
        for queue in self.frame_queues_3:
            queue.init_connection()

        # Create 4 queue managers to hold video frames produced by decorators
        self.frame_queues_4 = [RmqQueueManager("decorator_output_queue_" + str(i)) for i in range(4)]
        for queue in self.frame_queues_4:
            queue.init_connection()

        # Create 4 queue managers to hold video frames produced by recorders
        self.frame_queues_5 = [RmqQueueManager("recorder_output_queue_" + str(i)) for i in range(4)]
        for queue in self.frame_queues_5:
            queue.init_connection()
        
        # # Create 4 queues to hold video frames produced by readers
        # frame_queues_1 = [queue.Queue(maxsize=100) for _ in range(4)]
        # self.frame_queues_1 = frame_queues_1

        # # Create 4 queues to hold video frames produced by detectors
        # frame_queues_2 = [queue.Queue(maxsize=100) for _ in range(4)]
        # self.frame_queues_2 = frame_queues_2

        # # Create 4 queues to hold video frames produced by recognizers
        # frame_queues_3 = [queue.Queue(maxsize=100) for _ in range(4)]
        # self.frame_queues_3 = frame_queues_3

        # # Create 4 queues to hold video frames produced by displayers
        # frame_queues_4 = [queue.Queue(maxsize=100) for _ in range(4)]
        # self.frame_queues_4 = frame_queues_4


        self.video_paths = [""] * 4  # Store paths to the video files
        self.fps         = [""] * 4  # Store paths to the video fps
        self.src_names   = [""] * 4  # Store paths to the log dir
        self.duration    = [""] * 4  # Store paths to the recording duration
        self.out_dirs    = [""] * 4  # Store paths to the output dir
        self.log_dirs    = [""] * 4  # Store paths to the log dir
        

        self.read_threads       = [None] * 4  # Store the threads
        self.detector_threads   = [None] * 4  # Store the threads
        self.recognizer_threads = [None] * 4  # Store the threads
        self.decorator_threads  = [None] * 4  # Store the threads
        self.recorder_threads   = [None] * 4  # Store the threads
        self.shower_threads     = [None] * 4  # Store the threads

        # Create the stop event
        self.stop_event = threading.Event()

        self.init_ui()

    def init_ui(self):
        # Set up the window
        self.setWindowTitle("4 Videos Player with Sources and Events")
        self.setGeometry(100, 100, 1400, 800)

        # Create 4 QLabel widgets to display the video frames
        self.video_labels = [QLabel(self) for _ in range(4)]

        # Set minimum size for video labels to make the video area bigger
        for label in self.video_labels:
            label.setMinimumSize(320, 240)  # Set minimum size for each video display

        # Grid layout to arrange the QLabel widgets in a 2x2 grid
        grid_layout = QGridLayout()
        grid_layout.addWidget(self.video_labels[0], 0, 0)  # Top-left
        grid_layout.addWidget(self.video_labels[1], 0, 1)  # Top-right
        grid_layout.addWidget(self.video_labels[2], 1, 0)  # Bottom-left
        grid_layout.addWidget(self.video_labels[3], 1, 1)  # Bottom-right

        # Create buttons for load, start, stop, and quit
        load_button  = QPushButton("Load",  self)
        start_button = QPushButton("Start", self)
        stop_button  = QPushButton("Stop",  self)
        quit_button  = QPushButton("Quit",  self)

        # Connect buttons to their respective functions
        load_button.clicked.connect(self.load_videos)
        start_button.clicked.connect(self.start_videos)
        stop_button.clicked.connect(self.stop_videos)
        quit_button.clicked.connect(QApplication.quit)  # Closes the application

        # Create a horizontal layout for the buttons (at the top)
        button_layout = QHBoxLayout()
        button_layout.addWidget(load_button)
        button_layout.addWidget(start_button)
        button_layout.addWidget(stop_button)
        button_layout.addWidget(quit_button)  # Add the Quit button

        # Create QLabel widgets to label the "Sources" and "Events" lists
        sources_label = QLabel("Sources", self)
        events_label = QLabel("Events", self)

        # Create two QListWidget for "Sources" and "Events"
        self.sources_list = QListWidget(self)
        #self.sources_list.addItems(["Source 1", "Source 2", "Source 3", "Source 4"])  # Example items
        self.events_list = QListWidget(self)
        
        # Set a larger minimum width for the "Events" list to make it wider
        self.events_list.setMinimumWidth(300)  # Set the minimum width for the "Events" list

        # Create a vertical layout for each list with their corresponding labels
        sources_layout = QVBoxLayout()
        sources_layout.addWidget(sources_label)
        sources_layout.addWidget(self.sources_list)

        events_layout = QVBoxLayout()
        events_layout.addWidget(events_label)
        events_layout.addWidget(self.events_list)

        # Create a horizontal layout for the Sources and Events lists (at the bottom)
        lists_layout = QHBoxLayout()
        lists_layout.addLayout(sources_layout)  # Add Sources list
        lists_layout.addLayout(events_layout)   # Add Events list

        # Add stretch factor to give more space to the Events list in the layout
        lists_layout.setStretch(0, 1)  # Sources list with less space
        lists_layout.setStretch(1, 2)  # Events list with more space

        # Create a vertical layout to stack everything: buttons -> videos -> lists
        main_layout = QVBoxLayout()
        main_layout.addLayout(button_layout)  # Add buttons at the top
        main_layout.addLayout(grid_layout)    # Add video grid in the center
        main_layout.addLayout(lists_layout)   # Add lists at the bottom

        self.setLayout(main_layout)

    def video_source(self, i, video_path, output_queue, log_dir, stop_event):
        logger = get_thread_logger(log_dir, 'FrameProducer')
        fp = FrameProducer(video_path, output_queue, logger, stop_event)
        fp.read_frames()

    def detector(self, i, data_dir, input_queue, output_queue, log_dir, stop_event):
        logger = get_thread_logger(log_dir, 'FaceDetector')
        fd = FaceDetector(id, data_dir, input_queue, output_queue, logger, stop_event)
        fd.detectAndTrackMultipleFaces()

    def recognizer(self, i, data_dir, input_queue, output_queue, log_dir, stop_event):
        logger = get_thread_logger(log_dir, 'FaceRecognizer')
        fr = FaceRecognizer(id, data_dir, input_queue, output_queue, logger, stop_event)
        fr.recognizeMultipleFaces()

    def video_decorator(self, i, input_queue, output_queue, log_dir, stop_event):
        logger = get_thread_logger(log_dir, 'VideoDecorator')
        vd = VideoDecorator(i, input_queue, output_queue, logger, stop_event)
        vd.decorate()

    def video_recorder(self, i, input_queue, output_queue, fps, duration, log_dir, out_dir, stop_event):
        logger = get_thread_logger(log_dir, 'VideoRecorder')
        vr = VideoRecorder(i, input_queue, output_queue, fps, duration, logger, out_dir, stop_event)
        vr.record()

    def video_shower(self, i, input_queue, fps, log_dir, label, list_widget, stop_event):
         logger = get_thread_logger(log_dir, 'VideoShower')
         vs = VideoShow(i, input_queue, fps, logger, label, list_widget, stop_event)
         vs.show()

    # def video_shower(self, i, input_queue, output_queue, fps, log_dir, label, list_widget, stop_event):
    #      logger = get_thread_logger(log_dir, 'SimpleVideoShower')
    #      vs = SimpleVideoShow(i, input_queue, output_queue, fps, logger, label, list_widget, stop_event)
    #      vs.show()

    def load_videos(self):

        config_file = QFileDialog.getOpenFileName(self, f"Select configuration")

        self.config = load_yaml_config(config_file[0])

        general = self.config.get('general', {})

        self.data_dir = general[0]['data_dir'] # contains npy for embedings and registration photos
        log_dir  = general[1]['log_dir']
        out_dir  = general[2]['output_dir']

        sources_list = []
        i = 0

        # remote sources
        remote_sources = self.config.get('remote_sources', [])

        for remote_source in remote_sources:
            ip_cams = remote_source.get('ip_cams', [])

            for ip_cam in ip_cams:
                print(f"  IP cam Name: {ip_cam['ip_cam_name']}\n \
                        URL: {ip_cam['url']},\n \
                        Enabled: {ip_cam['enabled']},\n \
                        Fragment duration: {ip_cam['fragment_duration']}, \n \
                        fps: {ip_cam['fps']}")
                if (ip_cam['enabled']):
                        
                        ldir,odir=create_log_out_dir(log_dir=log_dir,
                                                    out_dir=out_dir,
                                                    id=ip_cam['ip_cam_name'])

                        self.video_paths[i] = ip_cam['url']
                        self.video_labels[i].setText(ip_cam['ip_cam_name'])

                        self.fps[i] = ip_cam['fps']
                        self.duration[i] = ip_cam['fragment_duration']
                        self.out_dirs[i] = odir
                        self.log_dirs[i] = ldir
                        self.src_names[i] = ip_cam['ip_cam_name']

                        i = i + 1
                        self.sources_list.addItem(ip_cam['ip_cam_name'])

        # local sources
        local_sources = self.config.get('local_sources', [])

        for local_source in local_sources:

            ## local webcams
            webcams = local_source.get('webcams', [])

            for webcam in webcams:
                print(f"  Webcam Name: {webcam['webcam_name']}\n \
                        Webcam ID: {webcam['webcam_number']},\n \
                        Enabled: {webcam['enabled']},\n \
                        Fragment duration: {webcam['fragment_duration']}, \n \
                        fps: {webcam['fps']}")
                if (webcam['enabled']):
                        
                        ldir,odir=create_log_out_dir(log_dir=log_dir,
                                                    out_dir=out_dir,
                                                    id=webcam['webcam_name'])

                        self.video_paths[i] = webcam['webcam_number']
                        self.video_labels[i].setText(webcam['webcam_name'])

                        self.fps[i] = webcam['fps']
                        self.duration[i] = webcam['fragment_duration']
                        self.out_dirs[i] = odir
                        self.log_dirs[i] = ldir
                        self.src_names[i] = webcam['webcam_name']

                        i = i + 1
                        self.sources_list.addItem(webcam['webcam_name'])

            ## local video files
            video_files = local_source.get('video_files', [])

            for video_file in video_files:
                print(f"  Video File Name: {video_file['video_name']}\n \
                        File: {video_file['location']},\n \
                        Enabled: {video_file['enabled']},\n \
                        Fragment duration: {video_file['fragment_duration']}, \n \
                        fps: {video_file['fps']}")
                if (video_file['enabled']):
                        
                        ldir,odir=create_log_out_dir(log_dir=log_dir,
                                                    out_dir=out_dir,
                                                    id=video_file['video_name'])

                        self.video_paths[i] = video_file['location']
                        self.video_labels[i].setText(video_file['video_name'])

                        self.fps[i] = video_file['fps']
                        self.duration[i] = video_file['fragment_duration']
                        self.out_dirs[i] = odir
                        self.log_dirs[i] = ldir
                        self.src_names[i] = video_file['video_name']

                        i = i + 1
                        self.sources_list.addItem(video_file['video_name'])

    def start_videos(self):

        """Start playing the videos by launching reader threads."""
        for i in range(4):
            if self.video_paths[i] != "":
                self.read_threads[i] = threading.Thread(target=self.video_source, args=(i, 
                                                                                        self.video_paths[i], 
                                                                                        self.frame_queues_1[i], 
                                                                                        self.log_dirs[i], 
                                                                                        self.stop_event),
                                                                                        name='reader_' + str(i))
                self.read_threads[i].start()

        for i in range(4):
            if self.video_paths[i] != "":
                self.detector_threads[i] = threading.Thread(target=self.detector, args=(i, 
                                                                                        self.data_dir, 
                                                                                        self.frame_queues_1[i], 
                                                                                        self.frame_queues_2[i], 
                                                                                        self.log_dirs[i],
                                                                                        self.stop_event),
                                                                                        name='detector_' + str(i))
                self.detector_threads[i].start()

        for i in range(4):
            if self.video_paths[i] != "":
                self.recognizer_threads[i] = threading.Thread(target=self.recognizer, args=(i, 
                                                                                        self.data_dir, 
                                                                                        self.frame_queues_2[i], 
                                                                                        self.frame_queues_3[i], 
                                                                                        self.log_dirs[i],
                                                                                        self.stop_event),
                                                                                        name='recognizer_' + str(i))
                self.recognizer_threads[i].start()

        for i in range(4):
            if self.video_paths[i] != "":
                self.decorator_threads[i] = threading.Thread(target=self.video_decorator, args=(self.src_names[i], 
                                                                                          self.frame_queues_3[i],
                                                                                          self.frame_queues_4[i],
                                                                                          self.log_dirs[i],
                                                                                          self.stop_event),
                                                                                          name='decorator_' + str(i))
                self.decorator_threads[i].start()

        for i in range(4):
            if self.video_paths[i] != "":
                self.recorder_threads[i] = threading.Thread(target=self.video_recorder, args=(self.src_names[i], 
                                                                                          self.frame_queues_4[i],
                                                                                          self.frame_queues_5[i],
                                                                                          self.fps[i],
                                                                                          self.duration[i],
                                                                                          self.log_dirs[i],
                                                                                          self.out_dirs[i],
                                                                                          self.stop_event),
                                                                                          name='recorder_' + str(i))
                self.recorder_threads[i].start()

        for i in range(4):
            if self.video_paths[i] != "":
                self.shower_threads[i] = threading.Thread(target=self.video_shower, args=(self.src_names[i], 
                                                                                          self.frame_queues_5[i],
                                                                                          self.fps[i],
                                                                                          self.log_dirs[i],
                                                                                          self.video_labels[i],
                                                                                          self.events_list,
                                                                                          self.stop_event),
                                                                                          name='shower_' + str(i))  
                self.shower_threads[i].start()

    def stop_videos(self):

        #print("Main thread: Stopping the worker thread")
        self.stop_event.set()

        for thread in self.read_threads:
            if thread:
                thread.join()
        for thread in self.detector_threads:
            if thread:
                thread.join()
        for thread in self.recognizer_threads:
            if thread:
                thread.join()
        for thread in self.decorator_threads:
            if thread:
                thread.join()
        for thread in self.recorder_threads:
            if thread:
                thread.join()
        for thread in self.shower_threads:
            if thread:
                thread.join()


def main():

    app = QApplication(sys.argv)

    # Create the PyQt5 window and pass the frame queues
    player = VideoPlayer()
    player.show()

    # Run the PyQt5 application
    sys.exit(app.exec_())

if __name__ == '__main__':

    # Create a thread-local object to hold the loggers
    thread_local = threading.local()

    main()
