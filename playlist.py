class Playlist:
    def __init__(self, name):
        self.name = name
        self.tracks = []

    def add_track(self, track):
        self.tracks.append(track)

    def remove_track(self, track):
        if track in self.tracks:
            self.tracks.remove(track)

    def clear(self):
        self.tracks = []