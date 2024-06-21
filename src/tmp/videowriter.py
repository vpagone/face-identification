# Importing OpenCV
import cv2
 
# Reading the video from the webcam
video = cv2.VideoCapture(0)
 
# Checking whether the camera has been accessed using the isOpened function
if (video.isOpened() == False):
    print("Error opening the video file")
    
# Getting the frame width and frame height
frame_width = int(video.get(3))
frame_height = int(video.get(4)) 

# count the number of frames
fps = video.get(cv2.CAP_PROP_FPS)
totalNoFrames = video.get(cv2.CAP_PROP_FRAME_COUNT)
durationInSeconds = totalNoFrames / fps

print("Video fps: ", fps)
print("Number of frames: ", totalNoFrames)
print("Video Duration In Seconds:", durationInSeconds, "s")

    
# Writing the video using the cv2.VideoWriter function
video_out = cv2.VideoWriter(r'C:\\Users\\utente\\Desktop\\output.avi',cv2.VideoWriter_fourcc('M','J','P','G'), fps, (frame_width,frame_height))
 
# When the video has been opened successfully, we'll read each frame of the video using a loop
while(video.isOpened()):
    ret, frame = video.read()
    if ret == True:
        cv2.imshow('Frame',frame)
        
        # Writing each frame of the video
        video_out.write(frame)
 
        # Using waitKey to display each frame of the video for 1 ms
        key = cv2.waitKey(1)
        if key == ord('q'):
            break
 
video.release()
video_out.release()
cv2.destroyAllWindows()
