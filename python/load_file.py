import numpy as np
from typing import Tuple, Dict
    
def load_samples(filepath):
    samples = []
    with open(filepath, "r") as f:
        for line in f:
            bin_str = line.strip()
            if len(bin_str) != 16:
                continue  
            val = int(bin_str, 2)
            if val & 0x8000:  # if sign bit is set
                val -= 1 << 16
            samples.append(val / 32768.0)
    return np.array(samples, dtype=np.float32)

def load_windowed_frames(filepath):
    with open(filepath, 'r') as f:
        header = dict(item.split('=') for item in f.readline().strip().split(','))
        frame_size = int(header['frameSize'])
        num_frames = int(header['numFrames'])
        data = np.loadtxt(f, delimiter=',', dtype=np.float64)
    return data.reshape((num_frames, frame_size))

def load_fft_results(filepath):
    with open(filepath) as f:
        header = dict(p.split('=') for p in f.readline().strip().split(','))
        frame_size = int(header['frameSize'])
        # num_frames = int(header['numFrames'])
        data = np.loadtxt(f, delimiter=',', dtype=np.float64)
    return (data[:, ::2] + 1j * data[:, 1::2]).reshape(-1, frame_size)

def load_signal(filepath):
    with open(filepath) as f:
        data = np.loadtxt(f, delimiter=' ', dtype=np.float64)
    return data