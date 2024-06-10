import os
import cv2
from core import FaceIdentifier
from threading import Thread, Lock
from multiprocessing import Process
import time
import argparse
from frame_producer import FrameProducer
from video_shower import VideoShow
from config_manager import load_yaml_config

def start_process(id, source, data_dir):
    fp_1 = FrameProducer(source, id + '_queue')
    fi_1 = FaceIdentifier(id, data_dir, source)
    fs_1 = VideoShow(id + '_queue_out')

    # start processes
    fp_proc_1 = Process(target = fp_1.produce)
    fp_proc_1.start()

    fi_proc_1 = Process(target = fi_1.detectAndTrackMultipleFaces)
    fi_proc_1.start()

    fs_proc_1 = Process(target = fs_1.show)
    fs_proc_1.start()

def run_config(config):

    general = config.get('general', {})

    # contain npy for embedings and registration photos
    data_dir = general[0]['data_dir']

    #local_sources = config.get('local_sources', [])
    # for local_source in local_sources:
    #     name = local_source.get('name', 'Unnamed')
    #     print(f"Local Source: {name}")

    #     webcams = local_source.get('webcams', [])
    #     for webcam in webcams:
    #         print(f"  Webcam Name: {webcam['webcam_name']}, Webcam Number: {webcam['webcam_number']}")
            
    #     video_files = local_source.get('video_files', [])
    #     for video_file in video_files:
    #         print(f"  Video File Name: {video_file['video_name']}, File: {video_file['location']}")
            
    # remote_sources = config.get('network_sources', [])
    # for remote_source in remote_sources:
    #     name = remote_source.get('name', 'Unnamed')
    #     print(f"Remore Source: {name}")
    #     webcams = remote_source.get('webcams', [])
    #     for webcam in webcams:
    #         print(f"  Webcam Name: {webcam['webcam_name']}, Webcam IP: {webcam['webcam_ip']}")

    process_list = []
    local_sources = config.get('local_sources', [])
    for local_source in local_sources:
        video_files = local_source.get('video_files', [])
        for video_file in video_files:
            print(f"  Video File Name: {video_file['video_name']}, File: {video_file['location']}, Enabled: {video_file['enabled']}")
            if (video_file['enabled']):
                fp,fi,fs = start_process(id=video_file['video_name'], 
                                            source=video_file['location'], 
                                            data_dir=data_dir)
                process_list.append(fp)
                process_list.append(fi)
                process_list.append(fs)

    for process in process_list:
        process.join()

    # #source = '/home/vito/r/videocamara/1692502753042.mp4'
    # #source = '/home/vito/r/videocamara/1692606706027.mp4'

    # source = '/home/vito/r/videocamara/1682921183173.mp4'
    # #source = 0
    # id = 'fi-01'
    # fp_1 = FrameProducer(source, id + '_queue')
    # fi_1 = FaceIdentifier(id, data_dir, source)
    # fs_1 = VideoShow(id + '_queue_out')

    # source = '/home/vito/r/videocamara/1692455074607.mp4'
    # #source = 0
    # id = 'fi-02'
    # fp_2 = FrameProducer(source, id + '_queue')
    # fi_2 = FaceIdentifier(id, data_dir, source)
    # fs_2 = VideoShow(id + '_queue_out')

 
    # # start processes
    # fp_proc_1 = Process(target = fp_1.produce)
    # fp_proc_1.start()

    # fi_proc_1 = Process(target = fi_1.detectAndTrackMultipleFaces)
    # fi_proc_1.start()

    # fs_proc_1 = Process(target = fs_1.show)
    # fs_proc_1.start()


    # fp_proc_2 = Process(target = fp_2.produce)
    # fp_proc_2.start()

    # fi_proc_2 = Process(target = fi_2.detectAndTrackMultipleFaces)
    # fi_proc_2.start()

    # fs_proc_2 = Process(target = fs_2.show)
    # fs_proc_2.start()
   
    # fp_proc_1.join()
    # fi_proc_1.join()
    # fs_proc_1.join()

    # fp_proc_2.join()
    # fi_proc_2.join()
    # fs_proc_2.join()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Face Identification System')
    parser.add_argument('-c','--config', help='Configuration file full path name', required=True)
    args = vars(parser.parse_args())

    config_path = args['config']
    config = load_yaml_config(config_path)

    run_config( config)





    




