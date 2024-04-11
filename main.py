import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import pygame
import os
import json
from audio_player import AudioPlayer
from playlist import Playlist

def main():
    pygame.init()
    root = tk.Tk()
    app = AudioPlayer(root)
    root.mainloop()
    pygame.quit()

if __name__ == "__main__":
    main()