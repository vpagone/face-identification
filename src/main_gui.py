import tkinter as tk
from tkinter import filedialog, Listbox, Scrollbar, Label
from tkinter import Label
import cv2
import threading
from PIL import Image, ImageTk
from queue import Queue
import json
import base64
import numpy as np
import os

from config_manager import load_yaml_config, create_log_out_dir
from frame_producer import FrameProducer
from detector import FaceDetector
from recognizer import FaceRecognizer
from video_recorder import VideoRecorder

import logging
import threading
import time
from threading import Thread

def get_thread_logger(log_dir, log_name):
    """Get or create a logger for the current thread."""
    if not hasattr(thread_local, 'logger'):
        # Generate a unique log file name based on the thread name
        log_file_name=path=os.path.join(log_dir, log_name + '.log')

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

def load_file(self):

    self.config = load_yaml_config('/home/vito/dev/fr-w-sface/cfg')

    sources_list = []
    local_sources = self.config.get('local_sources', [])

    for local_source in local_sources:
        video_files = local_source.get('video_files', [])

        for video_file in video_files:
            print(f"  Video File Name: {video_file['video_name']},\n \
                    File: {video_file['location']},\n \
                    Enabled: {video_file['enabled']},\n \
                    Fragment duration: {video_file['fragment_duration']}, \n \
                    fps: {video_file['fps']}")
            if (video_file['enabled']):
                    sources_list.append(video_file['video_name'])

    return sources_list
    
def decode_frame(encoded_frame):
    frame_bytes = base64.b64decode(encoded_frame)
    frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
    frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
    return frame

# Function to display video frames from a queue on a specific label
def play_video_from_queue(input_queue, output_queue, label):

    setFaceNames    = {}
    setFaceScores   = {}

    thickness = 2
    scale = 0.6
    font = cv2.FONT_HERSHEY_SIMPLEX
    green = (0, 255, 0)
    orange = (0, 165, 255)

    while True:
        # Get the frame from the queue
        message = input_queue.get()

        if ( message is None ):
            return

        data = json.loads(message)

        # Extract frame id
        frame_id = data['frame_id']

        # Extract and decode the image
        frame = decode_frame(data['image'])

        faceBoxesByFrame  = data['boxes']

        faceNamesByFrame  = data['names']
        faceScoresByFrame = data['scores']

        for id in faceNamesByFrame.keys():
            if ( not faceNamesByFrame[id] in setFaceNames ):
                setFaceNames[id] = faceNamesByFrame[id]
        for id in faceScoresByFrame.keys():
            if ( not faceScoresByFrame[id] in faceScoresByFrame ):
                setFaceScores[id] = faceScoresByFrame[id]

        # self.logger.info('display frame: {}'.format(frame_id))
        # self.logger.info('names: {}'.format(faceNamesByFrame))
        # self.logger.info('boxes: {}'.format(faceBoxesByFrame))            
        # self.logger.info('scores: {}'.format(faceScoresByFrame))

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

        # Convert the frame from BGR (OpenCV format) to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Convert the frame to an image format compatible with Tkinter
        image = Image.fromarray(frame)
        image = ImageTk.PhotoImage(image)

        # Update the label with the new frame
        label.config(image=image)
        label.image = image

        # Slow down the frame rate to 30fps
        #label.update()

        # Allow GUI to process other events
        label.update_idletasks()

        #output_queue.put(message)
        json_object = json.dumps(data)
        output_queue.put(json_object)

def video_source(i, video_path, output_queue, log_dir):
    logger = get_thread_logger(log_dir, 'FrameProducer')
    fp = FrameProducer(i, video_path, output_queue, logger)
    fp.produce()

def detector(i, data_dir, input_queue, output_queue, log_dir):
    logger = get_thread_logger(log_dir, 'FaceDetector')
    fd = FaceDetector(id, data_dir, input_queue, output_queue, logger)
    fd.detectAndTrackMultipleFaces()

def recognizer(i, data_dir, input_queue, output_queue, log_dir):
    logger = get_thread_logger(log_dir, 'FaceRecognizer')
    fr = FaceRecognizer(id, data_dir, input_queue, output_queue, logger)
    fr.recognizeMultipleFaces()

def video_recorder(i, input_queue, fps, duration, log_dir, out_dir):
    logger = get_thread_logger(log_dir, 'VideoRecorder')
    vr = VideoRecorder(i, input_queue, fps, duration, logger, out_dir)
    vr.record()

if __name__ == "__main__":

    # Create a thread-local object to hold the loggers
    thread_local = threading.local()

    config = load_yaml_config('/home/vito/dev/fr-w-sface/cfg/config.yaml')
    general = config.get('general', {})

    data_dir = general[0]['data_dir'] # contains npy for embedings and registration photos
    log_dir  = general[1]['log_dir']
    out_dir  = general[2]['output_dir']

    #create log dir and output dir
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    videos = []
    fps = []
    duration = []
    out_dirs = []
    log_dirs = []
    local_sources = config.get('local_sources', [])
    for local_source in local_sources:
        video_files = local_source.get('video_files', [])

        for video_file in video_files:
            print(f"  Video File Name: {video_file['video_name']},\n \
                        File: {video_file['location']},\n \
                        Enabled: {video_file['enabled']},\n \
                        Fragment duration: {video_file['fragment_duration']}, \n \
                        fps: {video_file['fps']}")
            if (video_file['enabled']):
                ldir,odir=create_log_out_dir(log_dir=log_dir,
                                                out_dir=out_dir,
                                                id=video_file['video_name'])
                videos.append(video_file['location'])
                fps.append(video_file['fps'])
                duration.append(video_file['fragment_duration'])
                out_dirs.append(odir)
                log_dirs.append(ldir)

    # Create the main application window
    root = tk.Tk()
    root.title("Face Identification Project")

###############

    # Frames for layout
    top_frame = tk.Frame(root)
    top_frame.pack(side=tk.TOP, fill=tk.X)

    left_frame = tk.Frame(root)
    left_frame.pack(side=tk.LEFT, fill=tk.Y)

    right_frame = tk.Frame(root, width=640, height=480)
    right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    top_left_frame = tk.Frame(left_frame)
    top_left_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    bottom_left_frame = tk.Frame(left_frame)
    bottom_left_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    # Buttons
    load_button = tk.Button(top_frame, text="Load", command=load_file)
    load_button.pack(side=tk.LEFT)

    start_button = tk.Button(top_frame, text="Start")
    start_button.pack(side=tk.LEFT)

    stop_button = tk.Button(top_frame, text="Stop")
    stop_button.pack(side=tk.LEFT)

    # Labels and Listboxes with scrollbars
    sources_label = tk.Label(top_left_frame, text="Sources")
    sources_label.pack(side=tk.TOP, anchor='w')

    sources_listbox = Listbox(top_left_frame)
    sources_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    top_left_scrollbar = Scrollbar(top_left_frame, command=sources_listbox.yview)
    top_left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    sources_listbox.config(yscrollcommand=top_left_scrollbar.set)

    events_label = tk.Label(bottom_left_frame, text="Events")
    events_label.pack(side=tk.TOP, anchor='w')

    events_listbox = Listbox(bottom_left_frame)
    events_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    bottom_left_scrollbar = Scrollbar(bottom_left_frame, command=events_listbox.yview)
    bottom_left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    events_listbox.config(yscrollcommand=bottom_left_scrollbar.set)


###############





    # Create 4 labels to show the videos
    labels = [Label(right_frame), Label(right_frame), Label(right_frame), Label(right_frame)]
    for i, label in enumerate(labels):
        label.grid(row=i // 2, column=i % 2)

    # Create 4 queues, one for each video source
    output_video_source_queues = [Queue(maxsize=10) for _ in range(len(videos))]

    # Start video source threads
    source_threads = []
    for i in range(len(videos)):
        thread = threading.Thread(target=video_source, args=(i, videos[i], output_video_source_queues[i], log_dirs[i]))
        thread.start()
        source_threads.append(thread)

    # Create 4 queues, one for each detector
    detectort_output_queues = [Queue(maxsize=10) for _ in range(len(videos))]

    # Start detector threads
    detector_threads = []
    for i in range(len(videos)):
        thread = threading.Thread(target=detector, args=(i, data_dir, output_video_source_queues[i], detectort_output_queues[i], log_dirs[i]))
        thread.start()
        detector_threads.append(thread)

    # Create 4 queues, one for each recgnizer
    recognizer_output_queues = [Queue(maxsize=10) for _ in range(len(videos))]

    # Start recognizer threads
    recognizer_threads = []
    for i in range(len(videos)):
        thread = threading.Thread(target=recognizer, args=(i, data_dir, detectort_output_queues[i], recognizer_output_queues[i], log_dirs[i]))
        thread.start()
        recognizer_threads.append(thread)

    # Create 4 queues, one for each player
    video_player_output_queues = [Queue(maxsize=10) for _ in range(len(videos))]

    # Start display threads (these consume from the queues)
    display_threads = []
    for i in range(len(videos)):
        thread = threading.Thread(target=play_video_from_queue, args=(recognizer_output_queues[i], video_player_output_queues[i], labels[i]))
        thread.start()
        display_threads.append(thread)

    # Start recorder threads (these consume from the queues)
    recorder_threads = []
    for i in range(len(videos)):
        thread = threading.Thread(target=video_recorder, args=(i, video_player_output_queues[i], fps[i], duration[i], log_dirs[i], out_dirs[i]))
        thread.start()
        recorder_threads.append(thread)


    # Start the Tkinter main loop
    root.mainloop()

    # Wait for all threads to finish
    for thread in source_threads:
        thread.join()

    for thread in detector_threads:
        thread.join()

    for thread in recognizer_threads:
        thread.join()

    for thread in display_threads:
        thread.join()

    for thread in recorder_threads:
        thread.join()
