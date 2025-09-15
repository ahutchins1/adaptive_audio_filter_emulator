import matplotlib.pyplot as plt
import numpy as np
import load_file
import scipy.io.wavfile as wav
from quant_tool import FixedPointValue
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib
matplotlib.use('TkAgg')

def to_wav(data_double, output_wav, fs=48000):
    """
    Convert double values from a text file to a .wav file
    
    Parameters:
    data_double: vector array with double values
    output_wav: path to output .wav file
    fs: sampling rate (default: 48000 Hz)
    """

    NB_total = 16
    NB_float = 15
    data_int16 = []
    
    for val in data_double:
        try:
            # Create fixed-point representation
            fixed_point = FixedPointValue(NB_total, NB_float, val)
            
            # Convert back to 16-bit integer
            # The to_quant_float() gives us the quantized float value
            quant_float = fixed_point.to_quant_float()
            
            # Convert back to 16-bit integer (PCM format)
            int_value = int(quant_float * 32768)
            int_value = np.clip(int_value, -32768, 32767)
            data_int16.append(int_value)
            
        except ValueError as e:
            print(f"Error processing value {val}: {e}")
            # Use 0 as fallback value
            data_int16.append(0)
            continue
    
    # Convert to numpy array with int16 dtype
    audio_data = np.array(data_int16, dtype=np.int16)
    
    # Write to WAV file
    wav.write(output_wav, fs, audio_data)
    print(f"Successfully created {output_wav} with {len(audio_data)} samples")

# Set global matplotlib font sizes to 14
import matplotlib as mpl
mpl.rcParams['font.size'] = 14           # Default font size
mpl.rcParams['axes.titlesize'] = 14      # Title font size
mpl.rcParams['axes.labelsize'] = 14      # Axis label font size
mpl.rcParams['xtick.labelsize'] = 14     # X-axis tick label size
mpl.rcParams['ytick.labelsize'] = 14     # Y-axis tick label size
mpl.rcParams['legend.fontsize'] = 14     # Legend font size

# Try to import pygame for audio playback
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Pygame not installed. Audio playback will be disabled.")

class EmulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Emulator Signal Viewer")
        self.root.geometry("1400x900")

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.style = ttk.Style()
        self.style.configure('TLabel', font=('Arial', 14))
        self.style.configure('TButton', font=('Arial', 14))
        self.style.configure('TLabelframe.Label', font=('Arial', 14, 'bold'))
        self.style.configure('TNotebook.Tab', font=('Arial', 14))  # This fixes tab names
        
        self.samples_file           = "audio_file.txt"
        self.windowed_frames_file   = "out/output_frames.txt"
        self.fft_results_file       = "out/output_fft.txt"
        self.psd_est_noise_file     = "out/output_psd_est_noise.txt"
        self.psd_signal_file        = "out/output_psd_signal.txt"
        self.recon_signal_file      = "out/output_recon_signal.txt"
        
        self.audio_file1 = "audio_files/unfiltered_samples.wav"
        self.audio_file2 = "audio_files/filtered_samples.wav"
        
        self.Fs = 48000  # Fixed sampling frequency
        self.Ns = 256
        self.Nfft = 256
        
        self.samples = None
        self.windowed_frames = None
        self.fft_res = None
        self.psd_est_noise = None
        self.psd_signal = None
        self.recon_signal = None
        
        self.current_audio = None
        self.audio_playing = False
        
        self.status_var = tk.StringVar(value="Loading data...")
        
        if PYGAME_AVAILABLE:
            pygame.mixer.init()
        
        self.load_all_data()
        
        self.setup_gui()
        
    def load_all_data(self):
        """Load all required data files"""
        try:
            self.samples = load_file.load_samples(self.samples_file)
            self.windowed_frames = load_file.load_windowed_frames(self.windowed_frames_file)
            self.fft_res = load_file.load_fft_results(self.fft_results_file)
            self.psd_est_noise = load_file.load_windowed_frames(self.psd_est_noise_file)
            self.psd_signal = load_file.load_windowed_frames(self.psd_signal_file)
            self.recon_signal = load_file.load_signal(self.recon_signal_file)
            to_wav(self.recon_signal, self.audio_file2)
            self.status_var.set("All data loaded successfully!")
            print("All data loaded successfully!")
        except Exception as e:
            error_msg = f"Failed to load data files: {str(e)}"
            self.status_var.set(error_msg)
            messagebox.showerror("Error", error_msg)
            self.root.destroy()

    def on_closing(self):
        """Properly close the application"""
        try:
            # Stop any playing audio
            if PYGAME_AVAILABLE and pygame.mixer.get_init():
                pygame.mixer.music.stop()
                pygame.mixer.quit()
        except:
            pass
        
        plt.close('all')
        
        self.root.destroy()
        self.root.quit()
    
    def setup_gui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        self.tab3 = ttk.Frame(self.notebook) 
        
        self.notebook.add(self.tab1, text="Signal Comparison")
        self.notebook.add(self.tab2, text="Frame Analysis")
        self.notebook.add(self.tab3, text="Audio Player")
        
        self.setup_tab1()
        self.setup_tab2()
        self.setup_tab3()
        
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, font=('Arial', 14))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_tab1(self):
        """Setup Signal Comparison tab"""
        control_frame = ttk.Frame(self.tab1)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(control_frame, text=f"Sampling Frequency: {self.Fs} Hz (Fixed)", font=('Arial', 14)).pack(side=tk.LEFT, padx=5)
        
        self.fig1 = plt.Figure(figsize=(12, 8))
        self.ax1 = self.fig1.add_subplot(111)
        self.canvas1 = FigureCanvasTkAgg(self.fig1, self.tab1)
        self.canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        toolbar_frame = ttk.Frame(self.tab1)
        toolbar_frame.pack(fill=tk.X)
        toolbar1 = NavigationToolbar2Tk(self.canvas1, toolbar_frame)
        toolbar1.update()

        self.update_tab1()
    
    def setup_tab2(self):
        control_frame = ttk.Frame(self.tab2)
        control_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(control_frame, text="Frame:", font=('Arial', 14)).pack(side=tk.LEFT, padx=5)
        self.frame_var = tk.IntVar(value=0)
        max_frame = self.windowed_frames.shape[0] - 1 if self.windowed_frames is not None else 0
        self.frame_slider = ttk.Scale(control_frame, from_=0, to=max_frame, 
                                     variable=self.frame_var, orient=tk.HORIZONTAL,
                                     length=300, command=self.update_tab2)
        self.frame_slider.pack(side=tk.LEFT, padx=5)

        self.frame_label = ttk.Label(control_frame, text="0", font=('Arial', 14, 'bold'))
        self.frame_label.pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text=f"Sampling Frequency: {self.Fs} Hz", font=('Arial', 14)).pack(side=tk.LEFT, padx=5)

        self.fig2, (self.ax2_top, self.ax2_bottom) = plt.subplots(2, 1, figsize=(12, 10))
        self.canvas2 = FigureCanvasTkAgg(self.fig2, self.tab2)
        self.canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        toolbar_frame = ttk.Frame(self.tab2)
        toolbar_frame.pack(fill=tk.X)
        toolbar2 = NavigationToolbar2Tk(self.canvas2, toolbar_frame)
        toolbar2.update()

        self.update_tab2()
    
    def setup_tab3(self):
        """Setup Audio Player tab"""
        if not PYGAME_AVAILABLE:
            error_frame = ttk.Frame(self.tab3)
            error_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            error_label = ttk.Label(error_frame, 
                                  text="Audio playback requires pygame library.\n"
                                       "Install it with: pip install pygame",
                                  font=('Arial', 14),
                                  justify=tk.CENTER)
            error_label.pack(expand=True)
            return

        audio_frame = ttk.Frame(self.tab3, padding=20)
        audio_frame.pack(fill=tk.BOTH, expand=True)

        file_frame = ttk.LabelFrame(audio_frame, text="Audio Files", padding=10)
        file_frame.pack(fill=tk.X, pady=10)

        ttk.Button(file_frame, text="Play Unfiltered Samples File", 
                  command=lambda: self.play_audio(self.audio_file1)).pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(file_frame, text="Play Denoised Samples File", 
                  command=lambda: self.play_audio(self.audio_file2)).pack(side=tk.LEFT, padx=5, pady=5)
        
        control_frame = ttk.LabelFrame(audio_frame, text="Playback Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=10)
        
        self.play_button = ttk.Button(control_frame, text="▶ Play", command=self.toggle_playback)
        self.play_button.pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Button(control_frame, text="■ Stop", command=self.stop_audio).pack(side=tk.LEFT, padx=5, pady=5)

        volume_frame = ttk.Frame(control_frame)
        volume_frame.pack(side=tk.LEFT, padx=20, pady=5)
        
        ttk.Label(volume_frame, text="Volume:", font=('Arial', 14)).pack(side=tk.LEFT)
        self.volume_var = tk.DoubleVar(value=0.7)  # Default volume 70%
        volume_scale = ttk.Scale(volume_frame, from_=0.0, to=1.0, 
                                variable=self.volume_var, orient=tk.HORIZONTAL,
                                length=100, command=self.set_volume)
        volume_scale.pack(side=tk.LEFT, padx=5)

        status_frame = ttk.LabelFrame(audio_frame, text="Playback Status", padding=10)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.audio_status_var = tk.StringVar(value="Ready to play audio")
        ttk.Label(status_frame, textvariable=self.audio_status_var, font=('Arial', 14)).pack(pady=5)

        self.current_file_var = tk.StringVar(value="No file loaded")
        ttk.Label(status_frame, textvariable=self.current_file_var, font=('Arial', 14)).pack(pady=5)
    
    def play_audio(self, filename):
        try:
            self.stop_audio()

            pygame.mixer.music.load(filename)
            self.current_audio = filename
            self.current_file_var.set(f"Current file: {filename}")

            self.set_volume()

            pygame.mixer.music.play()
            self.audio_playing = True
            self.play_button.config(text="⏸ Pause")
            self.audio_status_var.set("Playing...")
            self.status_var.set(f"Playing audio: {filename}")
            
        except Exception as e:
            error_msg = f"Failed to play audio: {str(e)}"
            self.audio_status_var.set(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def toggle_playback(self):
        if self.current_audio is None:
            self.audio_status_var.set("No audio file loaded")
            return
        
        if self.audio_playing:
            pygame.mixer.music.pause()
            self.audio_playing = False
            self.play_button.config(text="▶ Play")
            self.audio_status_var.set("Paused")
        else:
            pygame.mixer.music.unpause()
            self.audio_playing = True
            self.play_button.config(text="⏸ Pause")
            self.audio_status_var.set("Playing...")
    
    def stop_audio(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
        self.audio_playing = False
        self.play_button.config(text="▶ Play")
        self.audio_status_var.set("Stopped")
        self.status_var.set("Audio playback stopped")
    
    def set_volume(self, *args):
        if PYGAME_AVAILABLE:
            pygame.mixer.music.set_volume(self.volume_var.get())
    
    def update_tab1(self):
        if self.samples is None or self.recon_signal is None:
            self.status_var.set("Error: Required data not loaded for Tab 1")
            return
        
        try:
            time_axis = np.arange(len(self.samples)) / self.Fs
            
            self.ax1.clear()

            self.ax1.plot(time_axis, self.samples, 'b-', linewidth=1.5, label='Original Signal', alpha=0.7)

            self.ax1.plot(time_axis, self.recon_signal, 'r-', linewidth=1.5, label='Reconstructed Signal', alpha=0.7)
            
            self.ax1.set_xlabel('Time [s]', fontsize=14)
            self.ax1.set_ylabel('Amplitude', fontsize=14)
            self.ax1.set_title('Signal Comparison: Original vs Reconstructed', fontsize=14)
            self.ax1.legend(fontsize=14)
            self.ax1.grid(True)
            
            self.fig1.tight_layout()
            self.canvas1.draw()
            
            self.status_var.set("Signal comparison updated")
            
        except Exception as e:
            error_msg = f"Failed to update signal comparison: {str(e)}"
            self.status_var.set(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def update_tab2(self, *args):
        if (self.windowed_frames is None or self.psd_est_noise is None or 
            self.psd_signal is None):
            self.status_var.set("Error: Required data not loaded for Tab 2")
            return
        
        try:
            current_frame = int(self.frame_var.get())
            self.frame_label.config(text=str(current_frame))
            xt = np.arange(self.Ns) / self.Fs
            xfft = np.linspace(0.0, 1.0 / (2.0 * xt[1]), self.Nfft // 2)

            self.ax2_top.clear()
            self.ax2_bottom.clear()
            self.ax2_top.plot(xt, self.windowed_frames[current_frame], 
                             'b-', linewidth=2, label=f'Windowed Frame {current_frame}')
            self.ax2_top.set_xlabel('Time [s]', fontsize=14)
            self.ax2_top.set_ylabel('Amplitude', fontsize=14)
            self.ax2_top.set_title(f'Windowed Frame {current_frame} (Time Domain)', fontsize=14)
            self.ax2_top.legend(fontsize=14)
            self.ax2_top.grid(True)

            self.ax2_bottom.plot(xfft, self.psd_est_noise[current_frame][:self.Nfft//2], 
                                'r-', linewidth=2, label='PSD Estimated Noise', alpha=0.7)
            self.ax2_bottom.plot(xfft, self.psd_signal[current_frame][:self.Nfft//2], 
                                'g-', linewidth=2, label='PSD Signal', alpha=0.7)
            self.ax2_bottom.set_xlabel('Frequency [Hz]', fontsize=14)
            self.ax2_bottom.set_ylabel('Power Spectral Density', fontsize=14)
            self.ax2_bottom.set_title(f'PSD Comparison - Frame {current_frame}', fontsize=14)
            self.ax2_bottom.legend(fontsize=14)
            self.ax2_bottom.grid(True)
            
            self.fig2.tight_layout()
            self.canvas2.draw()
            
            self.status_var.set(f"Displaying frame {current_frame}")
            
        except IndexError:
            self.status_var.set("Frame index out of range")
        except Exception as e:
            error_msg = f"Failed to update frame analysis: {str(e)}"
            self.status_var.set(error_msg)
            messagebox.showerror("Error", error_msg)

def main():
    root = tk.Tk()
    app = EmulatorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()


