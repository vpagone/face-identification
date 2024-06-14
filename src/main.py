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
from config_manager import load_yaml_config
import logging
import errno

def start_process(id, source, data_dir, window_frame, log_dir, out_dir):

    input_frame_queue       = Queue(maxsize=100)
    procecessed_frame_queue = Queue(maxsize=100)
 
    fp = FrameProducer(id, source, input_frame_queue, log_dir)
    fi = FaceIdentifier(id, data_dir, input_frame_queue, procecessed_frame_queue, log_dir)
    fs = VideoShow(id, procecessed_frame_queue, log_dir)
    fr = VideoRecorder(id, procecessed_frame_queue, window_frame, log_dir, out_dir)

    # start processes
    fp_proc = Process(target = fp.produce)
    fp_proc.start()

    fi_proc = Process(target = fi.detectAndTrackMultipleFaces)
    fi_proc.start()

    fs_proc = Process(target = fs.show)
    fs_proc.start()

    fr_proc = Process(target = fr.record)
    fr_proc.start()

    return fp_proc, fi_proc, fs_proc, fr_proc

def create_log_dir(log_dir, id):
    try:
        path=os.path.join(log_dir, id)
        os.makedirs(path, exist_ok=True)  # Python>3.2
        return path
    except TypeError:
        try:
            os.makedirs(path)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else: raise

def run_config(config):

    general = config.get('general', {})
    # contain npy for embedings and registration photos
    data_dir = general[0]['data_dir']
    log_dir  = general[1]['log_dir']
    out_dir  = general[2]['output_dir']

    process_list = []
    local_sources = config.get('local_sources', [])
    for local_source in local_sources:
        video_files = local_source.get('video_files', [])
        for video_file in video_files:
            print(f"  Video File Name: {video_file['video_name']},\n \
                      File: {video_file['location']},\n \
                      Enabled: {video_file['enabled']},\n \
                      Recording duration: {video_file['recording_duration']}, \n \
                      fps: {video_file['fps']}")
            if (video_file['enabled']):
                ldir=create_log_dir(log_dir=log_dir,
                                       id=video_file['video_name'])
                window_frame=video_file['fps']*video_file['recording_duration']
                fp,fi,fs,fr = start_process(id=video_file['video_name'], 
                                            source=video_file['location'],
                                            window_frame=window_frame, 
                                            data_dir=data_dir,
                                            log_dir=ldir,
                                            out_dir=out_dir)
                process_list.append(fp)
                process_list.append(fi)
                process_list.append(fs)
                process_list.append(fr)

    for process in process_list:
        process.join()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Face Identification System')
    parser.add_argument('-c','--config', help='Configuration file full path name', required=True)
    args = vars(parser.parse_args())

    config_path = args['config']
    config = load_yaml_config(config_path)

    run_config(config)





    




