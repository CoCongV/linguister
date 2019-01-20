import vlc
from playsound import playsound

def play(file):
    # file_type = file.split('.')[-1]
    # song = AudioSegment.from_file('file', file_type)
    # playback.play(song)
    # player = vlc.MediaPlayer(file)
    # r = player.play()
    playsound(file)
