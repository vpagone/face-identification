import cv2

from send_frame_to_queue import SendFrameToQueue

class FrameProducer():


    def __init__(self, source, queue_name):
                
        self.source = source
        self.queue_name = queue_name


    def produce(self):

        sendFrame = SendFrameToQueue(self.queue_name)
        sendFrame.init_connection()

        # Create a VideoCapture object
        cap = cv2.VideoCapture(self.source)

        # Check if the video file was opened successfully
        if not cap.isOpened():
            print("Error: Could not open video.")
            exit()

        # Read until the video is completed
        while cap.isOpened():
            # Capture frame-by-frame
            ret, frame = cap.read()

            if not ret:
                print("End of video or error in frame capture.")
                break

            # send frame to queue
            resized = cv2.resize( frame, ( 640, 480) )
            sendFrame.send_frame_to_queue(resized)
            #cv2.imshow(self.queue_name, frame)

            # Press 'q' on the keyboard to exit the loop
            #if cv2.waitKey(25) & 0xFF == ord('q'):
            #    break

        # When everything is done, release the video capture object and close all OpenCV windows
        cap.release()

# test
if __name__ == '__main__':
    source = '/home/vito/r/videocamara/1692455074607.mp4'
    # source = 0
    id = 'fi-01'
    fp = FrameProducer(source, id + '_queue')
    fp.produce()

#     sendFrame = SendFrameToQueue(id + '_queue')
#     sendFrame.init_connection()

#     # Open the video file
#     cap = cv2.VideoCapture(source)

#     # Check if video opened successfully
#     if not cap.isOpened():
#         print("Error: Could not open video.")
#         exit()

#     # Read until video is completed
#     while cap.isOpened():
#         # Capture frame-by-frame
#         ret, frame = cap.read()
        
        
#         if ret:

#             baseImage = cv2.resize( frame, ( 640, 480) )

#             sendFrame.send_frame_to_queue(baseImage)

#             # Display the resulting frame
#             #cv2.imshow('Video', baseImage)

#             # Press 'q' to exit the video window early
#             if cv2.waitKey(25) & 0xFF == ord('q'):
#                 break
#         else:
#             break

#     # When everything done, release the video capture object
#     cap.release()

# # Close all OpenCV windows
# cv2.destroyAllWindows()
