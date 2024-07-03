from threading import Thread
import cv2
import logging
import os
import base64
import json
import numpy as np

class VideoRecorder:
    """
    Class that continuously shows a frame using a dedicated thread.
    """

    def __init__(self, id, queue, fps, fragment_duration, log_dir, out_dir):

        self.id = id
        self.queue = queue
        self.fps = fps
        self.log_dir = log_dir
        self.out_dir = out_dir

        self.stopped = False

        self.frames_per_fragment = self.fps * fragment_duration

    def decode_frame(self, encoded_frame):
        frame_bytes = base64.b64decode(encoded_frame)
        frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
        return frame
 
    def record(self):

        self.logger = logging.getLogger(__name__)
        log_file_name=path=os.path.join(self.log_dir, __name__ + '.log')
        logging.basicConfig(format='%(levelname)-6s %(asctime)s [%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s', 
                            filename=log_file_name, 
                            level=logging.INFO)

        self.logger.info('Started')

        
        frame_counter = 0
        while not self.stopped:

            #frame = self.receive_frame.receive_frame_from_queue()
            #frame = self.queue.get()

            # Decode the JSON message
            message = self.queue.get()

            if ( message is None ):
                break

            data = json.loads(message)
    
            # Extract frame id
            frame_id = data['frame_id']

            if (frame_counter == 0):
                start_frame_id = frame_id
                tmp_file_name=path=os.path.join('/tmp', self.id + '-' + str(frame_id) + '.avi')
                video_out = cv2.VideoWriter(tmp_file_name,cv2.VideoWriter_fourcc('M','J','P','G'), self.fps, (640,480))
                setFaceNames = set()

            # Extract and decode the image
            frame = self.decode_frame(data['image'])

            # Extract names
            faceNames = data['names']
            for faceName in faceNames.values():
                setFaceNames.add(faceName)

            faceBoxes = data['boxes']

            faceScores = data['scores']

            self.logger.info('display frame: {}'.format(frame_id))
            self.logger.info('names: {}'.format(faceNames))
            self.logger.info('boxes: {}'.format(faceBoxes))            
            self.logger.info('scores: {}'.format(faceScores))

            for fid in faceBoxes.keys():

                    tracked_position = faceBoxes[fid]
                    
                    t_x = int(tracked_position[0])
                    t_y = int(tracked_position[1])
                    t_w = int(tracked_position[2])
                    t_h = int(tracked_position[3])

                    thickness = 2
                    scale = 0.6
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    green = (0, 255, 0)
                    orange = (0, 165, 255)

                    if fid in faceNames.keys():
                        cv2.rectangle(frame, (t_x, t_y),
                                        (t_x + t_w , t_y + t_h),
                                        (0, 255, 0) ,thickness, cv2.LINE_AA)
                        text = "{0} ({1:.2f})".format(faceNames[fid], faceScores[fid])
                        cv2.putText(frame, text, 
                                        (int(t_x + t_w/2), int(t_y)), 
                                        font,
                                        scale, green, thickness, cv2.LINE_AA)
                    else:
                        cv2.rectangle(frame, (t_x, t_y),
                                        (t_x + t_w , t_y + t_h),
                                        orange, thickness, cv2.LINE_AA)
                        
            # Writing frame of the video
            video_out.write(frame)

            frame_counter += 1

            if (frame_counter == self.frames_per_fragment):

                frame_counter = 0
                video_out.release()

                if ( len(setFaceNames) != 0 ):

                    fragment_file_name=path=os.path.join(self.out_dir, str(start_frame_id) + '.avi')
                    # mv tmp_file_name to out_dir
                    os.rename(tmp_file_name, fragment_file_name)

                    for faceName in setFaceNames:

                        face_name_dir_name = os.path.join(self.out_dir, faceName)
                        if not os.path.exists(face_name_dir_name):
                            os.makedirs(face_name_dir_name)

                        face_name_file = os.path.join(face_name_dir_name, str(start_frame_id) + '.avi')
                        os.symlink(fragment_file_name, face_name_file)

                    setFaceNames = set()

                else:

                    os.remove(tmp_file_name)

        video_out.release()
        file_name=path=os.path.join(self.out_dir, str(start_frame_id) + '.avi')
        # mv tmp_file_name to out_dir
        os.rename(tmp_file_name, file_name)

        self.logger.info('Finished')

    def stop(self):
        self.stopped = True
