
import numpy as np
import scipy.io.wavfile as wav
from quant_tool import FixedPointValue

fs = 48000
i_file = "audio_files/unfiltered_samples.wav"
o_file = "audio_file.txt"

fs_d, data = wav.read(i_file)
if fs != fs_d:
    raise ValueError("Resample is needed")
if data.dtype == np.int16:
    data_float = data / 32768.0
elif data.dtype == np.float32 or data.dtype == np.float64:
    data_float = data
else:
    raise TypeError("Unsupported WAV data format.")

data_float = np.clip(data_float, -1.0, 1.0 - 2**-15)
# Convert to fixed-point using the FixedPointValue class
NB_total = 16
NB_float = 15
data_q15 = []
data_bin = []
for val in data_float:
    try:
        fixed_point = FixedPointValue(NB_total, NB_float, val)
        data_q15.append(fixed_point.to_quant_float())
        data_bin.append(fixed_point.to_binary())
        # Print the value in hex and binary for debugging
        # print(f"Value: {val}, Hex: {fixed_point.to_hex()}, Binary: {fixed_point.to_binary()}")
    except ValueError as e:
        print(f"Error: {e}")
        continue

np.savetxt(o_file, data_bin, fmt="%s")