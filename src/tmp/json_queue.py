import base64
import json
from multiprocessing import Process, Queue

def main(queue):
    # Read the image file
    #with open(r'C:\\Users\\utente\\Desktop\\IMG20240308160950.jpg', 'rb') as image_file:
    with open(r'Marilyn_Monroe_0002.jpg', 'rb') as image_file:
        image_data = image_file.read()
    
    # Encode the image to Base64
    encoded_image = base64.b64encode(image_data).decode('utf-8')
    
    # Create the JSON object
    json_object = json.dumps({
        'image': encoded_image,
        'description': 'This is an example image.'
    })
    
    # Put the JSON object into the queue
    queue.put(json_object)
    
    # Signal the worker to stop
    queue.put("STOP")

def worker(queue):
    while True:
        message = queue.get()
        if message == "STOP":
            break
        
        # Decode the JSON message
        data = json.loads(message)
        
        # Extract and decode the image
        image_data = base64.b64decode(data['image'])
        
        # Save the image (for demonstration purposes)
        with open('received_image.png', 'wb') as image_file:
            image_file.write(image_data)
        
        print("Image received and saved.")

if __name__ == "__main__":
    queue = Queue()
    
    # Start the worker process
    worker_process = Process(target=worker, args=(queue,))
    worker_process.start()
    
    # Run the main function
    main(queue)
    
    # Wait for the worker to finish
    worker_process.join()
