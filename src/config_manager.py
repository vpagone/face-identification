import yaml
import os
import cv2
from core import FaceIdentifier
from threading import Thread, Lock
from multiprocessing import Process
from multiprocessing import Queue
# from frame_producer import FrameProducer
# from video_shower_new import start_video_player
# from video_recorder import VideoRecorder
# from detector import FaceDetector
# from recognizer import FaceRecognizer
import logging
import errno
import shutil

output_queues_dict = {}

def load_yaml_config(file_path):
    with open(file_path, 'r') as file:
        config = yaml.safe_load(file)
        return config

def start_process(id, source, data_dir, fps, fragment_duration, log_dir, out_dir):

    input_frame_queue        = Queue(maxsize=100)
    procecessed_frame_queue1 = Queue(maxsize=100)
    procecessed_frame_queue2 = Queue(maxsize=100)
    procecessed_frame_queue3 = Queue(maxsize=100)

    output_queues_dict[id] = procecessed_frame_queue1

    processed_frames_queue_list = []
    processed_frames_queue_list.append(procecessed_frame_queue1)
    processed_frames_queue_list.append(procecessed_frame_queue2)
 
    fp = FrameProducer(id, source, input_frame_queue, log_dir)
    fd = FaceDetector(id, data_dir, input_frame_queue, procecessed_frame_queue3, log_dir)
    fr = FaceRecognizer(id, data_dir, procecessed_frame_queue3, processed_frames_queue_list, log_dir)
    #vs = VideoShow(id, procecessed_frame_queue1, fps, log_dir)
    #vs = VideoShow(procecessed_frame_queue1)
    vr = VideoRecorder(id, procecessed_frame_queue2, fps, fragment_duration, log_dir, out_dir)

    # start processes
    fp_proc = Process(target = fp.produce)
    fp_proc.start()

    fd_proc = Process(target = fd.detectAndTrackMultipleFaces)
    fd_proc.start()

    fr_proc = Process(target = fr.recognizeMultipleFaces)
    fr_proc.start()

    #vs_proc = Process(target = vs.show)
    # vs_proc = Process(target=start_video_player, args=(procecessed_frame_queue2,))
    # vs_proc.start()
 
    vr_proc = Process(target = vr.record)
    vr_proc.start()

    #return fp_proc, fd_proc, fr_proc, vs_proc, vr_proc
    return fp_proc, fd_proc, fr_proc, vr_proc

def create_log_out_dir(log_dir, out_dir, id):
    try:
        log_path=os.path.join(log_dir, id)
        if os.path.exists(log_path):
            shutil.rmtree(log_path)
        os.makedirs(log_path)
        shutil.rmtree(log_path)
        os.makedirs(log_path, exist_ok=True)  # Python>3.2
    except TypeError:
        try:
            os.makedirs(log_path)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(log_path):
                pass
            else: raise

    try:
        out_path=os.path.join(out_dir, id)        
        if os.path.exists(out_path):
            shutil.rmtree(out_path)
        os.makedirs(out_path, exist_ok=True)  # Python>3.2
    except TypeError:
        try:
            os.makedirs(out_path)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(out_path):
                pass
            else: raise

    return log_path, out_path

def run_config(config):

    general = config.get('general', {})
    # contain npy for embedings and registration photos
    data_dir = general[0]['data_dir']
    log_dir  = general[1]['log_dir']
    out_dir  = general[2]['output_dir']

    #create log dir and output dir
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    process_list = []
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
                #fp,fd,fr,vs,vr = start_process(id=video_file['video_name'],
                fp,fd,fr,vr = start_process(id=video_file['video_name'], 
                                            source=video_file['location'],
                                            fps = video_file['fps'],
                                            fragment_duration = video_file['fragment_duration'],
                                            data_dir=data_dir,
                                            log_dir=ldir,
                                            out_dir=odir)
                process_list.append(fp)
                process_list.append(fd)
                process_list.append(fr)
                #process_list.append(vs)
                process_list.append(vr)

    # for process in process_list:
    #     process.join()

def get_output_queues():
    return output_queues_dict

if __name__ == "__main__":
    config_path = 'cfg/config.yaml'
    config = load_yaml_config(config_path)
       
    local_sources = config.get('local_sources', [])
    for local_source in local_sources:
        name = local_source.get('name', 'Unnamed')
        print(f"Local Source: {name}")
        webcams = local_source.get('webcams', [])
        for webcam in webcams:
            print(f"  Webcam Name: {webcam['webcam_name']}, Webcam Number: {webcam['webcam_number']}")
            
        video_files = local_source.get('video_files', [])
        for video_file in video_files:
            print(f"  Video File Name: {video_file['video_name']}, File: {video_file['location']}")
            
    remote_sources = config.get('network_sources', [])
    for remote_source in remote_sources:
        name = remote_source.get('name', 'Unnamed')
        print(f"Remore Source: {name}")
        webcams = remote_source.get('webcams', [])
        for webcam in webcams:
            print(f"  Webcam Name: {webcam['webcam_name']}, Webcam IP: {webcam['webcam_ip']}")
    
