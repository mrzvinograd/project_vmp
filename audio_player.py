import os
import json
import pygame
from tkinter import filedialog, messagebox, simpledialog
from mutagen.easyid3 import EasyID3
import tkinter as tk
from tkinter import ttk
import threading
import time

# Уменьшаем размер буфера
pygame.mixer.pre_init(44100, -16, 2, 512)
pygame.mixer.init()
pygame.init()

class Playlist:
    def __init__(self, name):
        self.name = name
        self.tracks = []

    def add_track(self, track):
        self.tracks.append(track)

    def remove_track(self, track):
        self.tracks.remove(track)

    def clear(self):
        self.tracks = []

class AudioPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Audio Player")
        self.root.geometry("800x600")

        self.root.configure(bg="#f0f0f0")
        self.playlists = {}
        self.current_playlist = None
        self.current_track = None
        self.paused = False
        self.repeat_playlist = False
        self.repeat_track = False

        self.create_widgets()
        self.load_playlists()

        self.timeline_thread = None
        self.stop_timeline_thread = False

    def create_widgets(self):
        button_frame = tk.Frame(self.root, bg="#f0f0f0")
        button_frame.pack(pady=10)

        self.play_button = tk.Button(button_frame, text="▶ Play", command=self.play_pause, bg="lightgreen", font=("Arial", 12, "bold"))
        self.play_button.grid(row=0, column=0, padx=5)

        self.stop_button = tk.Button(button_frame, text="⏹ Stop", command=self.stop, bg="indianred1", font=("Arial", 12, "bold"))
        self.stop_button.grid(row=0, column=1, padx=5)

        self.prev_track_button = tk.Button(button_frame, text="⏮ Previous", command=self.play_prev_track, bg="lightblue", font=("Arial", 12, "bold"))
        self.prev_track_button.grid(row=0, column=2, padx=5)

        self.next_track_button = tk.Button(button_frame, text="⏭ Next", command=self.play_next_track, bg="lightblue", font=("Arial", 12, "bold"))
        self.next_track_button.grid(row=0, column=3, padx=5)

        self.repeat_playlist_button = tk.Button(button_frame, text="🔁 Repeat Playlist", command=self.toggle_repeat_playlist, bg="lightgrey", font=("Arial", 12))
        self.repeat_playlist_button.grid(row=0, column=4, padx=5)

        self.repeat_track_button = tk.Button(button_frame, text="🔂 Repeat Track", command=self.toggle_repeat_track, bg="lightgrey", font=("Arial", 12))
        self.repeat_track_button.grid(row=0, column=5, padx=5)

        volume_frame = tk.LabelFrame(self.root, text="Volume", font=("Arial", 12), bg="#f0f0f0")
        volume_frame.pack(fill="x", padx=10, pady=(0,10))

        self.volume_slider = tk.Scale(volume_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.set_volume)
        self.volume_slider.set(10)
        self.volume_slider.pack(fill="x", padx=10, pady=10)

        timeline_frame = tk.LabelFrame(self.root, text="Timeline", font=("Arial", 12), bg="#f0f0f0")
        timeline_frame.pack(fill="x", padx=10, pady=(0,10))

        self.current_time_label = tk.Label(timeline_frame, text="00:00", font=("Arial", 12), bg="#f0f0f0")
        self.current_time_label.pack(side=tk.LEFT, padx=10)

        self.timeline_slider = tk.Scale(timeline_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.set_position)
        self.timeline_slider.pack(side=tk.LEFT, fill="x", expand=True, padx=10, pady=10)

        self.total_time_label = tk.Label(timeline_frame, text="00:00", font=("Arial", 12), bg="#f0f0f0")
        self.total_time_label.pack(side=tk.RIGHT, padx=10)

        playlist_button_frame = tk.Frame(self.root, bg="#f0f0f0")
        playlist_button_frame.pack(pady=5)

        self.add_button = tk.Button(playlist_button_frame, text="➕ Add to Playlist", command=self.add_to_playlist, bg="lightgrey", font=("Arial", 12))
        self.add_button.grid(row=0, column=0, padx=5)

        self.create_playlist_button = tk.Button(playlist_button_frame, text="📂 Create Playlist", command=self.create_playlist, bg="lightgrey", font=("Arial", 12))
        self.create_playlist_button.grid(row=0, column=1, padx=5)

        self.load_playlist_button = tk.Button(playlist_button_frame, text="📁 Load Playlist", command=self.load_playlist, bg="lightgrey", font=("Arial", 12))
        self.load_playlist_button.grid(row=0, column=2, padx=5)

        self.save_playlist_button = tk.Button(playlist_button_frame, text="💾 Save Playlist", command=self.save_playlist, bg="lightgrey", font=("Arial", 12))
        self.save_playlist_button.grid(row=0, column=3, padx=5)

        self.clear_playlist_button = tk.Button(playlist_button_frame, text="🗑 Clear Playlist", command=self.clear_playlist, bg="lightgrey", font=("Arial", 12))
        self.clear_playlist_button.grid(row=0, column=4, padx=5)

        self.remove_track_button = tk.Button(playlist_button_frame, text="❌ Remove Track", command=self.remove_track_from_playlist, bg="lightgrey", font=("Arial", 12))
        self.remove_track_button.grid(row=0, column=5, padx=5)

        search_frame = tk.Frame(self.root, bg="#f0f0f0")
        search_frame.pack(pady=5)

        self.search_entry = tk.Entry(search_frame, width=30, font=("Arial", 12))
        self.search_entry.grid(row=0, column=0, padx=5)

        self.search_button = tk.Button(search_frame, text="🔍 Search", command=self.search_tracks, bg="lightgrey", font=("Arial", 12))
        self.search_button.grid(row=0, column=1, padx=5)

        self.track_info_button = tk.Button(self.root, text="ℹ Track Info", command=self.display_track_info, bg="lightgrey", font=("Arial", 12))
        self.track_info_button.pack(pady=5)

        playlist_frame = tk.LabelFrame(self.root, text="Playlist", font=("Arial", 12), bg="#f0f0f0")
        playlist_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.playlist_listbox = tk.Listbox(playlist_frame, width=100, height=20, font=("Arial", 12))
        self.playlist_listbox.pack(fill="both", expand=True)

    def update_playlist(self):
        self.playlist_listbox.delete(0, tk.END)
        if self.current_playlist:
            for track in self.current_playlist.tracks:
                tags = self.get_track_tags(track)
                if tags:
                    self.playlist_listbox.insert(tk.END, f"{tags['title']} - {tags['artist']}")
                else:
                    self.playlist_listbox.insert(tk.END, os.path.basename(track))

    def get_track_tags(self, track_path):
        try:
            tags = EasyID3(track_path)
            return tags
        except Exception as e:
            print(f"Error reading tags: {e}")
            return None

    def play_pause(self):
        if self.current_track is not None:
            if self.paused:
                pygame.mixer.music.unpause()
                self.paused = False
                self.play_button.config(text="⏸ Pause")
            else:
                pygame.mixer.music.pause()
                self.paused = True
                self.play_button.config(text="▶ Play")
        else:
            if self.current_playlist and self.current_playlist.tracks:
                self.play_track(0)
                self.play_button.config(text="⏸ Pause")

    def stop(self):
        pygame.mixer.music.stop()
        self.current_track = None
        self.timeline_slider.set(0)
        self.current_time_label.config(text="00:00")
        self.total_time_label.config(text="00:00")
        self.play_button.config(text="▶ Play")
        self.stop_timeline_thread = True

    def set_volume(self, volume):
        pygame.mixer.music.set_volume(int(volume) / 100)

    def add_to_playlist(self):
        file_path = filedialog.askopenfilename(filetypes=[("MP3 files", "*.mp3")])
        if file_path:
            self.current_playlist.add_track(file_path)
            self.update_playlist()

    def create_playlist(self):
        name = simpledialog.askstring("Playlist Name", "Enter a name for the new playlist:")
        if name:
            if name in self.playlists:
                messagebox.showerror("Error", f"A playlist with the name '{name}' already exists.")
            else:
                self.playlists[name] = Playlist(name)
                self.current_playlist = self.playlists[name]
                self.update_playlist()

    def save_playlist(self):
        if not self.current_playlist:
            messagebox.showwarning("Warning", "Please select a playlist or create a new one.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "w") as f:
                json.dump({
                    "name": self.current_playlist.name,
                    "tracks": self.current_playlist.tracks
                }, f)

    def load_playlist(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, "r") as f:
                playlist_data = json.load(f)
                name = playlist_data["name"]
                tracks = playlist_data["tracks"]
                if name not in self.playlists:
                    self.playlists[name] = Playlist(name)
                self.playlists[name].tracks = tracks
                self.current_playlist = self.playlists[name]
                self.update_playlist()

    def remove_track_from_playlist(self):
        if not self.current_playlist:
            messagebox.showwarning("Warning", "Please select a playlist or create a new one.")
            return
        selected_index = self.playlist_listbox.curselection()
        if selected_index:
            track_index = selected_index[0]
            track = self.current_playlist.tracks[track_index]
            self.current_playlist.remove_track(track)
            self.update_playlist()

    def clear_playlist(self):
        if not self.current_playlist:
            messagebox.showwarning("Warning", "Please select a playlist or create a new one.")
            return
        self.current_playlist.clear()
        self.update_playlist()

    def search_tracks(self):
        query = self.search_entry.get().lower()
        search_result = []
        if self.current_playlist:
            for track in self.current_playlist.tracks:
                if query in os.path.basename(track).lower():
                    search_result.append(track)
                else:
                    tags = self.get_track_tags(track)
                    if tags:
                        if query in tags.get("title", "").lower() or query in tags.get("artist", "").lower() or query in tags.get("album", "").lower():
                            search_result.append(track)
            if search_result:
                self.current_playlist.tracks = search_result
                self.update_playlist()
            else:
                messagebox.showinfo("Search", "No tracks found matching the query.")

    def display_track_info(self):
        if self.current_track is not None:
            track = self.current_playlist.tracks[self.current_track]
            tags = self.get_track_tags(track)
            if tags:
                info_str = ""
                for key, value in tags.items():
                    info_str += f"{key}: {value[0]}\n"
                messagebox.showinfo("Track Info", info_str)
            else:
                messagebox.showinfo("Track Info", "No information available.")
        else:
            messagebox.showwarning("Warning", "No track is currently playing.")

    def load_playlists(self):
        if os.path.exists("playlists.json"):
            with open("playlists.json", "r") as f:
                playlists_data = json.load(f)
                for playlist_data in playlists_data:
                    name = playlist_data["name"]
                    tracks = playlist_data["tracks"]
                    playlist = Playlist(name)
                    playlist.tracks = tracks
                    self.playlists[name] = playlist

    def play_prev_track(self):
        if self.current_track is not None:
            prev_track_index = (self.current_track - 1) % len(self.current_playlist.tracks)
            self.play_track(prev_track_index)

    def play_next_track(self):
        if self.current_track is not None:
            next_track_index = (self.current_track + 1) % len(self.current_playlist.tracks)
            self.play_track(next_track_index)

    def play_track(self, index):
        track = self.current_playlist.tracks[index]
        try:
            pygame.mixer.music.load(track)
            pygame.mixer.music.play()
            self.current_track = index
            self.timeline_slider.set(0)
            self.play_button.config(text="⏸ Pause")
            self.start_timeline_update()
        except pygame.error:
            messagebox.showerror("Error", "Cannot play the selected track.")
        else:
            self.update_track_info()

    def toggle_repeat_playlist(self):
        self.repeat_playlist = not self.repeat_playlist

    def toggle_repeat_track(self):
        self.repeat_track = not self.repeat_track

    def set_position(self, position):
        if self.current_track is not None:
            track = self.current_playlist.tracks[self.current_track]
            length = pygame.mixer.Sound(track).get_length()
            new_pos = float(position) * length / 100
            pygame.mixer.music.set_pos(new_pos)
            self.update_timeline_slider(new_pos, length)

    def start_timeline_update(self):
        if self.timeline_thread is not None:
            self.stop_timeline_thread = True
            self.timeline_thread.join()
        self.stop_timeline_thread = False
        self.timeline_thread = threading.Thread(target=self.track_time_update)
        self.timeline_thread.start()

    def track_time_update(self):
        while not self.stop_timeline_thread:
            if self.current_track is not None and not self.paused:
                track = self.current_playlist.tracks[self.current_track]
                length = pygame.mixer.Sound(track).get_length()
                current_pos = pygame.mixer.music.get_pos() / 1000  # get_pos() returns milliseconds
                self.root.after(0, self.update_timeline_slider, current_pos, length)
            time.sleep(0.5)

# Лагает если использовать отображение в real time
#    def update_timeline_slider(self, current_pos, length):
#        self.timeline_slider.set(current_pos / length * 100)
#        self.current_time_label.config(text=self.format_time(current_pos))
#        self.total_time_label.config(text=self.format_time(length))

    def update_track_info(self):
        if self.current_track is not None:
            track = self.current_playlist.tracks[self.current_track]
            length = pygame.mixer.Sound(track).get_length()
            self.total_time_label.config(text=self.format_time(length))
            self.current_time_label.config(text="00:00")

    @staticmethod
    def format_time(seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02}:{seconds:02}"