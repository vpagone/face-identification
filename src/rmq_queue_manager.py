import pika
import cv2
import base64
import numpy as np

class RmqQueueManager():

    def __init__(self, queue_name):

        self.queue_name = queue_name
    
        self.producer = RmqQueueProducer( self.queue_name )
        self.consumer = RmqQueueConsumer( self.queue_name )


    def init_connection(self):
        
        self.producer.init_connection()
        self.consumer.init_connection()


    def send_frame_to_queue(self, frame):

        self.producer.put(frame)


    def receive_frame_from_queue(self):
        
        return self.consumer.get()
    

class RmqQueueProducer():

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

        #channel.start_consuming()

    # def encode_frame(self, frame):
    #     _, buffer = cv2.imencode('.jpg', frame)
    #     encoded_frame = base64.b64encode(buffer).decode('utf-8')
    #     return encoded_frame
    
    # def decode_frame(self, encoded_frame):
    #     frame_bytes = base64.b64decode(encoded_frame)
    #     frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
    #     frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
    #     return frame

    def put(self, frame):

        #encoded_frame = self.encode_frame(frame)

        # Send the encoded frame to the queue
        self.channel.basic_publish(exchange='',
                            routing_key=self.queue_name,
                            body=frame)


class RmqQueueConsumer():

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


    def get(self):
    
        # Retrieve a single message from the specified queue
        method_frame, header_frame, body = self.channel.basic_get(queue=self.queue_name)
        
        if method_frame:
            # Acknowledge the message was received and processed
            self.channel.basic_ack(method_frame.delivery_tag)
            
            # Return the message body
            #encoded_frame = body.decode('utf-8')
            #frame = self.decode_frame(frame)
            return body
        else:
            return None



