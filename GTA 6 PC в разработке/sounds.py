from ursina import *
import os
import math
import wave
import struct
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SND_DIR = os.path.join(BASE_DIR, 'sounds')

class SoundGenerator:
    def __init__(self):
        if not os.path.exists(SND_DIR):
            os.makedirs(SND_DIR)
        self.sounds = {}
        self.build_all()

    def make_wav(self, filename, duration, freq_start, freq_end, noise_mix=0.0, vol=0.4):
        path = os.path.join(SND_DIR, filename)
        if not os.path.exists(path):
            rate = 22050
            n_samples = int(rate * duration)
            with wave.open(path, 'w') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(rate)
                frames = bytearray()
                for i in range(n_samples):
                    t = i / n_samples
                    freq = freq_start + (freq_end - freq_start) * t
                    tone = math.sin(2.0 * math.pi * freq * (i / rate))
                    noise = random.uniform(-1.0, 1.0)
                    env = (1.0 - t) ** 1.5
                    sample = ((1.0 - noise_mix) * tone + noise_mix * noise) * env * vol
                    val = int(max(-32767, min(32767, sample * 32767)))
                    frames += struct.pack('<h', val)
                wf.writeframes(frames)
        self.sounds[filename] = Audio(f'sounds/{filename}', autoplay=False, loop=False)

    def build_all(self):
        self.make_wav('pistol.wav', 0.16, 520, 110, noise_mix=0.55, vol=0.45)
        self.make_wav('smg.wav', 0.11, 680, 180, noise_mix=0.65, vol=0.4)
        self.make_wav('shotgun.wav', 0.32, 240, 45, noise_mix=0.85, vol=0.6)
        self.make_wav('rpg.wav', 0.45, 180, 380, noise_mix=0.75, vol=0.5)
        self.make_wav('boom.wav', 0.65, 140, 28, noise_mix=0.92, vol=0.7)
        self.make_wav('buy.wav', 0.25, 520, 880, noise_mix=0.0, vol=0.4)
        self.make_wav('siren.wav', 0.45, 650, 850, noise_mix=0.0, vol=0.18)

    def play(self, name):
        snd = self.sounds.get(name)
        if snd:
            snd.play()
