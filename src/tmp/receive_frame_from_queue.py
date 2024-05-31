import pika
import cv2
import base64
import numpy as np

def decode_frame(encoded_frame):
    frame_bytes = base64.b64decode(encoded_frame)
    frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
    frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
    return frame

def callback(ch, method, properties, body):
    encoded_frame = body.decode('utf-8')
    frame = decode_frame(encoded_frame)

    # Display the frame
    cv2.imshow('Received Frame', frame)
    cv2.imwrite('received_frame.jpg', frame)  # Optionally save the frame
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    print("Frame received and displayed/saved as 'received_frame.jpg'")

def receive_frame_from_queue(queue_name='video_frame_queue'):
    # Connect to RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare a queue
    channel.queue_declare(queue=queue_name)

    # Set up subscription on the queue
    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

    print(f"Waiting for messages in queue {queue_name}. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    receive_frame_from_queue()
