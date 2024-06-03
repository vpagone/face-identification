import pika
import cv2
import base64

class SendFrameToQueue():

    def __init__(self, queue_name):

        self.id = id
        self.queue_name = queue_name

    def init_connection(self):

        # Connect to RabbitMQ
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()

        # Declare a queue
        self.channel.queue_declare(queue=self.queue_name)

    def encode_frame(self, frame):
        _, buffer = cv2.imencode('.jpg', frame)
        encoded_frame = base64.b64encode(buffer).decode('utf-8')
        return encoded_frame

    def send_frame_to_queue(self, frame):

        encoded_frame = self.encode_frame(frame)

        # Send the encoded frame to the queue
        self.channel.basic_publish(exchange='',
                            routing_key=self.queue_name,
                            body=encoded_frame)

        #print(f"Frame sent to queue {self.queue_name}")
#        self.connection.close()

# if __name__ == "__main__":
#     video_path = '/home/vito/r/videocamara/1692502753042.mp4'  # Replace with your video path
#     send_frame_to_queue(video_path)
