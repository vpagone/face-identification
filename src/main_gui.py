import tkinter as tk
from tkinter import filedialog, Listbox, Scrollbar
import cv2
from PIL import Image, ImageTk
import threading
import queue
import yaml
import base64
import json
import numpy as np

from config_manager import load_yaml_config
from config_manager import run_config
from config_manager import get_output_queue

class VideoPlayer(tk.Frame):
    def __init__(self, master, frame_queue):
        super().__init__(master)
        self.master = master
        self.frame_queue = frame_queue

        self.canvas = tk.Canvas(self, width=640, height=480)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.pack(fill=tk.BOTH, expand=True)

    # def update_video_frame(self):
    #     if not self.frame_queue.empty():
    #         frame = self.frame_queue.get()
    #         frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    #         img = Image.fromarray(frame)
    #         imgtk = ImageTk.PhotoImage(image=img)
    #         self.canvas.create_image(0, 0, anchor='nw', image=imgtk)
    #         self.imgtk = imgtk
    #     self.after(10, self.update_video_frame)

    def update_video_frame(self):

        if not self.frame_queue.empty():
            
            message = self.frame_queue.get()

            if ( message is None ):
                return

            data = json.loads(message)

            # Extract frame id
            frame_id = data['frame_id']
            
            # Extract and decode the image
            frame = decode_frame(data['image'])

            # ret, frame = cap.read()
            # if not ret:
            #     break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.canvas.create_image(0, 0, anchor='nw', image=imgtk)
            self.imgtk = imgtk

        self.after(10, self.update_video_frame)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("GUI Application")

        # Frames for layout
        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(side=tk.TOP, fill=tk.X)

        self.left_frame = tk.Frame(self.root)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.right_frame = tk.Frame(self.root, width=640, height=480)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.top_left_frame = tk.Frame(self.left_frame)
        self.top_left_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.bottom_left_frame = tk.Frame(self.left_frame)
        self.bottom_left_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        # Buttons
        self.load_button = tk.Button(self.top_frame, text="Load", command=self.load_file)
        self.load_button.pack(side=tk.LEFT)

        self.start_button = tk.Button(self.top_frame, text="Start", command=self.start_video)
        self.start_button.pack(side=tk.LEFT)

        self.stop_button = tk.Button(self.top_frame, text="Stop", command=self.stop_video)
        self.stop_button.pack(side=tk.LEFT)

        # Labels and Listboxes with scrollbars
        self.sources_label = tk.Label(self.top_left_frame, text="Sources")
        self.sources_label.pack(side=tk.TOP, anchor='w')

        self.sources_listbox = Listbox(self.top_left_frame)
        self.sources_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.top_left_scrollbar = Scrollbar(self.top_left_frame, command=self.sources_listbox.yview)
        self.top_left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sources_listbox.config(yscrollcommand=self.top_left_scrollbar.set)

        self.events_label = tk.Label(self.bottom_left_frame, text="Events")
        self.events_label.pack(side=tk.TOP, anchor='w')

        self.events_listbox = Listbox(self.bottom_left_frame)
        self.events_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.bottom_left_scrollbar = Scrollbar(self.bottom_left_frame, command=self.events_listbox.yview)
        self.bottom_left_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.events_listbox.config(yscrollcommand=self.bottom_left_scrollbar.set)

    def load_file(self):

        file_path = filedialog.askopenfilename(filetypes=[("YAML files", "*.yaml")])
        if not file_path:
            return

        self.config = load_yaml_config(file_path)

        sources_list = []
        local_sources = self.config.get('local_sources', [])

        for local_source in local_sources:
            video_files = local_source.get('video_files', [])

            for video_file in video_files:
                print(f"  Video File Name: {video_file['video_name']},\n \
                        File: {video_file['location']},\n \
                        Enabled: {video_file['enabled']},\n \
                        Fragment duration: {video_file['fragment_duration']}, \n \
                        fps: {video_file['fps']}")
                if (video_file['enabled']):
                        self.add_sources_listbox(video_file['video_name'])


        # file_path = filedialog.askopenfilename(filetypes=[("YAML files", "*.yaml")])
        # if file_path:
        #     with open(file_path, 'r') as file:
        #         data = yaml.safe_load(file)
        #         self.populate_listboxes(data)

    def add_sources_listbox(self, item):
        self.sources_listbox.insert(tk.END, item)

    def populate_sources_listbox(self, data):
        self.sources_listbox.delete(0, tk.END)
        for item in data:
            self.sources_listbox.insert(tk.END, item)

    def populate_events_listbox(self, data):
        self.events_listbox.delete(0, tk.END)
        for item in data:
            self.events_listbox.insert(tk.END, item)

    def start_video(self):
        
        # Variables
        #self.frame_queue = Queue(maxsize=10)
        self.stop_event = threading.Event()
        self.video_thread = None


        
        # if not self.video_thread or not self.video_thread.is_alive():
        #     self.stop_event.clear()
        #     #video_source = "path_to_your_video.mp4"  # Replace with the actual video path
        #     #video_source = 0
        #     #self.video_thread = threading.Thread(target=self.read_video, args=(video_source,))

        #     self.video_thread = threading.Thread(target=self.read_video, args=(queue,))
        #     self.video_thread.start()

        run_config(self.config)

        queue = get_output_queue()

        # Video player frame
        #self.video_player = VideoPlayer(self.right_frame, self.frame_queue)
        self.video_player = VideoPlayer(self.right_frame, queue)
          
        self.video_player.update_video_frame()

    def stop_video(self):
        self.stop_event.set()
        if self.video_thread:
            self.video_thread.join()

    def read_video(self, queue):
        #cap = cv2.VideoCapture(video_source)

        while not self.stop_event.is_set():

            # Decode the JSON message
            message = queue.get()

            if ( message is None ):
                break

            data = json.loads(message)

            # Extract frame id
            frame_id = data['frame_id']
            
            # Extract and decode the image
            frame = decode_frame(data['image'])

            # ret, frame = cap.read()
            # if not ret:
            #     break

            if not self.frame_queue.full():
                self.frame_queue.put(frame)

        #cap.release()

def decode_frame(encoded_frame):
    frame_bytes = base64.b64decode(encoded_frame)
    frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
    frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
    return frame

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()