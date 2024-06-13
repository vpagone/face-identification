import multiprocessing as mp
import json
import base64
from io import BytesIO
from PIL import Image

def encode_image_to_base64(image_path):
    with Image.open(image_path) as img:
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

def create_json_with_image(image_path):
    base64_image = encode_image_to_base64(image_path)
    data = {
        "name": "Alice",
        "age": 30,
        "city": "New York",
        "image": base64_image
    }
    return json.dumps(data)

def producer(queue, image_path):
    json_data = create_json_with_image(image_path)
    queue.put(json_data)
    queue.put(None)  # Sentinel value to indicate end of data

def decode_base64_to_image(base64_string, output_path):
    image_data = base64.b64decode(base64_string)
    with open(output_path, "wb") as out_file:
        out_file.write(image_data)

def process_json_with_image(json_data):
    data = json.loads(json_data)
    print(f"Received data: {data['name']}, {data['age']}, {data['city']}")
    decode_base64_to_image(data['image'], "output_image.png")
    print("Image saved as output_image.png")

def consumer(queue):
    while True:
        json_data = queue.get()
        if json_data is None:
            break
        process_json_with_image(json_data)

def main():
    queue = mp.Queue()
    image_path = 'path/to/your/image.png'

    # Create and start producer and consumer processes
    producer_process = mp.Process(target=producer, args=(queue, image_path))
    consumer_process = mp.Process(target=consumer, args=(queue,))

    producer_process.start()
    consumer_process.start()

    producer_process.join()
    consumer_process.join()

if __name__ == '__main__':
    main()
