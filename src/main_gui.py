import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import yaml
from threading import Thread
from PIL import Image, ImageTk

from config_manager import load_yaml_config
from config_manager import run_config

class VideoPlayer:
    def __init__(self, canvas):
        self.canvas = canvas
        self.video_source = None
        self.cap = None
        self.playing = False

    def load_video(self, source):
        self.video_source = source
        self.cap = cv2.VideoCapture(self.video_source)

    def play_video(self):
        if not self.cap:
            messagebox.showerror("Error", "No video loaded.")
            return

        self.playing = True
        self._play_video()

    def _play_video(self):
        if not self.playing:
            return

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = cv2.resize(frame, (self.canvas.winfo_width(), self.canvas.winfo_height()))
            img = ImageTk.PhotoImage(image=Image.fromarray(img))
            self.canvas.create_image(0, 0, anchor=tk.NW, image=img)
            self.canvas.image = img
            self.canvas.after(10, self._play_video)
        else:
            self.playing = False
            self.cap.release()

    def stop_video(self):
        self.playing = False
        if self.cap:
            self.cap.release()
            self.cap = None

class Application(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Video Player")
        self.geometry("900x680")

        self.create_top_menu()
        self.create_frames()

        self.video_players = [VideoPlayer(self.video_canvases[i]) for i in range(4)]

    def create_top_menu(self):
        top_frame = tk.Frame(self)
        top_frame.pack(side=tk.TOP, fill=tk.X)

        open_button = tk.Button(top_frame, text="Open", command=self.open_file)
        open_button.pack(side=tk.LEFT, padx=5, pady=5)

        play_button = tk.Button(top_frame, text="Play", command=self.play_videos)
        play_button.pack(side=tk.LEFT, padx=5, pady=5)

        stop_button = tk.Button(top_frame, text="Stop", command=self.stop_videos)
        stop_button.pack(side=tk.LEFT, padx=5, pady=5)

        events_button = tk.Button(top_frame, text="Events", command=self.show_events)
        events_button.pack(side=tk.LEFT, padx=5, pady=5)

    def create_frames(self):
        left_frame = tk.Frame(self, width=600, height=600)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.video_canvases = [tk.Canvas(left_frame, width=300, height=300, bg="black") for _ in range(4)]
        for i, canvas in enumerate(self.video_canvases):
            canvas.grid(row=i//2, column=i%2, padx=5, pady=5)

        right_frame = tk.Frame(self, width=200, height=600)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("YAML files", "*.yaml")])
        if not file_path:
            return

        config = load_yaml_config(file_path)

        run_config(config)

        # video_files = data.get('videos', [])
        # for i, video_file in enumerate(video_files):
        #     if i < 4:
        #         self.video_players[i].load_video(video_file)

    def play_videos(self):
        for player in self.video_players:
            Thread(target=player.play_video).start()

    def stop_videos(self):
        for player in self.video_players:
            player.stop_video()

    def show_events(self):
        messagebox.showinfo("Events", "No events available.")

if __name__ == "__main__":
    app = Application()
    app.mainloop()
