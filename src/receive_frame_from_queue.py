import pika
import cv2
import base64
import numpy as np

class ReceiveFrame():


    def __init__(self, queue_name):

        self.queue_name = queue_name    


    def init_connection(self):

        # Connect to RabbitMQ
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = connection.channel()

        # Declare a queue
        self.channel.queue_declare(queue=self.queue_name)
        

        # Set up subscription on the queue
        #channel.basic_consume(queue=self.queue_name, on_message_callback=self.callback, auto_ack=True)

        print(f"Waiting for messages in queue {self.queue_name}. To exit press CTRL+C")
        #channel.start_consuming()


    def decode_frame(self, encoded_frame):
        frame_bytes = base64.b64decode(encoded_frame)
        frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
        return frame


    def callback(self, ch, method, properties, body):
        encoded_frame = body.decode('utf-8')
        frame = self.decode_frame(self, encoded_frame)


    def receive_frame_from_queue(self):
    
        # Retrieve a single message from the specified queue
        method_frame, header_frame, body = self.channel.basic_get(queue=self.queue_name)
        
        if method_frame:
            # Acknowledge the message was received and processed
            self.channel.basic_ack(method_frame.delivery_tag)
            
            # Return the message body
            encoded_frame = body.decode('utf-8')
            frame = self.decode_frame(encoded_frame)
            return frame
        else:
            return None


if __name__ == "__main__":


    fr = ReceiveFrame('fi-01_queue')
    fr.init_connection()

    while True:

     frame = fr.receive_frame_from_queue()

     if frame is None:
         break

    # queue_name = 'my_queue'  # Replace with your queue name
    # message = get_message_from_queue(queue_name)
    # if message:
    #     print("Received message:", message)
    # else:
    #     print("No message in queue")


