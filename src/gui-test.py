import os
import cv2
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import threading

class VideoPlayer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Video Directory Tree")
        self.geometry("800x600")

        self.tree = ttk.Treeview(self, show="tree")
        self.tree.pack(side=tk.LEFT, fill=tk.Y)

        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.LEFT, fill=tk.Y)

        self.load_button = ttk.Button(self, text="Load Directory", command=self.load_directory)
        self.load_button.pack(pady=10)

        self.video_label = ttk.Label(self)
        self.video_label.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.cap = None
        self.video_thread = None
        self.stop_event = threading.Event()

    def load_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.populate_tree(directory)

    def populate_tree(self, directory, parent=""):
        for dirpath, dirnames, filenames in os.walk(directory):
            for dirname in dirnames:
                node_id = self.tree.insert(parent, "end", text=dirname, open=True)
                self.populate_tree(os.path.join(dirpath, dirname), node_id)
            for filename in filenames:
                if filename.endswith(('.mp4', '.avi', '.mov', '.mkv')):
                    self.tree.insert(parent, "end", text=filename, tags=("video",))
            break
        self.tree.tag_bind("video", "<Double-1>", self.play_video)

    def play_video(self, event):
        item = self.tree.selection()[0]
        file_path = self.get_full_path(item)
        if file_path:
            if self.cap:
                self.stop_event.set()
                self.cap.release()
            self.stop_event.clear()
            self.cap = cv2.VideoCapture(file_path)
            self.video_thread = threading.Thread(target=self.stream_video)
            self.video_thread.start()

    def stream_video(self):
        while not self.stop_event.is_set() and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
                self.video_label.update()
            else:
                break

    def get_full_path(self, item):
        path = self.tree.item(item, "text")
        parent = self.tree.parent(item)
        while parent:
            path = os.path.join(self.tree.item(parent, "text"), path)
            parent = self.tree.parent(parent)
        return path

    def on_closing(self):
        if self.cap:
            self.stop_event.set()
            self.cap.release()
        self.destroy()

if __name__ == "__main__":
    app = VideoPlayer()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
