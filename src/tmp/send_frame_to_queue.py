import pika
import cv2
import base64

def encode_frame(frame):
    _, buffer = cv2.imencode('.jpg', frame)
    encoded_frame = base64.b64encode(buffer).decode('utf-8')
    return encoded_frame

def send_frame_to_queue(video_path, queue_name='video_frame_queue'):
    # Read video frame
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("Failed to capture video frame.")
        return

    encoded_frame = encode_frame(frame)

    # Connect to RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare a queue
    channel.queue_declare(queue=queue_name)

    # Send the encoded frame to the queue
    channel.basic_publish(exchange='',
                          routing_key=queue_name,
                          body=encoded_frame)

    print(f"Frame sent to queue {queue_name}")
    connection.close()

if __name__ == "__main__":
    video_path = 'path/to/your/video.mp4'  # Replace with your video path
    send_frame_to_queue(video_path)
