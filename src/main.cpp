#include <cstdint>
#include <iostream>
#include <pocketfft_hdronly.h>
#include <filesystem>
#include "../include/frame.hpp"
#include "../include/fileio.hpp"
#include "../include/audio_processing.hpp"
using namespace std;
using namespace pocketfft;
namespace fs = std::filesystem;
// #define FREQ_DEBUG
#define OVERLAPADD


int main() {
    fs::create_directory("out");
    auto samples = readBinData("audio_file.txt");         // Insert path to input signal file

    #ifdef OVERLAPADD
    auto coeffs = readHexData("include/coeffs_hex.mem"); // Insert path to Hanning window coeffs file
    const size_t frame_size = coeffs.size(); // N
    const size_t hop = frame_size / 2;       // 50% overlap
    const size_t fft_size = (frame_size / 2) + 1;
    #else          
    std::vector<float> coeffs(256);
    for (auto& val : coeffs){val = 1.0f;}
    const size_t frame_size = coeffs.size(); // N
    const size_t hop = frame_size;           // 0% overlap
    const size_t fft_size = (frame_size / 2) + 1;
    #endif

    size_t frame_counter = 0;
    Frame frame(frame_size, coeffs);
    std::vector<double> windowed_frame(frame_size);
    std::vector<std::vector<double>> frames;                      // To store the full windowed frames vector

    std::vector<std::complex<double>> res(fft_size);              // To store FFT results for a single frame
    std::vector<std::vector<std::complex<double>>> results_fft;   // To store the full FFT results vector

    size_t d = 64;                                                // Estimation window
    NoiseEstimator noise_est(fft_size, d);                        // Generates the noise estimator
    std::vector<double> psd(fft_size);                            // To store the PSD (whole signal) results for a single frame
    std::vector<std::vector<double>> psd_signal_frames;           // To store the full signal PSD results vector
    std::vector<double> psd_noise(fft_size);                      // To store the PSD results of the noise for a single frame
    std::vector<std::vector<double>> psd_noise_frames;            // To store the full Noise PSD results vector

    WienerFilter filter(frame_size);                              // Generates the Wiener filter
    std::vector<std::complex<double>> filtered_frame(fft_size);  // To store the filtered signal for a single frame

    std::vector<double> recon_frame(frame_size);                  // To store reconstructed single frame after IFFT
    std::vector<double> recon_signal(samples.size());             // To store the reconstructed signal

    std::vector<double> delayed_samples(hop);                     // To store the second half of the past frame 

    // testReadWrite();
    // std::vector<std::vector<double>> true_noise_psd = readFrames("true_noise_psd.txt");

    // for (const auto& element : samples) {std::cout << element << " ";} std::cout << std::endl; //print sample vector   
    while ((frame_counter * hop + frame_size) < samples.size()) {
        size_t startIndex = frame_counter * hop;

        // 1. Generate windowed frame
        windowed_frame = frame.generateFrame(samples, startIndex);   // Generate a single frame of samples, with 50% overlapping and Hann windowing
        frames.push_back(windowed_frame);

        // 2. Apply FFT
        // Set up shape
        shape_t shape = {frame_size}; 

        // Set up strides. Input is real, output is complex
        stride_t stride_x = {sizeof(double)}; 
        stride_t stride_X = {sizeof(std::complex<double>)};  

        shape_t axes{0}; // Single axis for 1D FFT

        // Compute the R2C DFT (no scaling)
        r2c(shape, stride_x, stride_X, axes, FORWARD, windowed_frame.data(), res.data(), 1.0);
        
        //--------------------------------

        // Analyze the frequency spectrum
        #ifdef FREQ_DEBUG
        // Compute frequency bins and magnitudes
        std::vector<double> freqs(res.size());
        std::vector<double> mags(res.size());
        std::vector<double> esd(res.size());
        const double f_bin = 48000 / frame_size; 
        res[0] *= 0.001;
        res[1] *= 0.001;
        for (size_t k = 0; k < res.size(); ++k) {
            freqs[k] = k * f_bin;             
            mags[k] = std::abs(res[k]) * 2.0/frame_size;  
            esd[k] = mags[k] * mags[k];
        }
        mags[0] /= 2.0;                       
        if (frame_size % 2 == 0) {
            mags.back() /= 2.0;            
        }

        // Find peak frequency
        auto peak_it = std::max_element(mags.begin(), mags.end());
        size_t peak_bin = std::distance(mags.begin(), peak_it);
        double peak_freq = freqs[peak_bin];

        // Print results
        // std::cout << "Peak frequency: " << peak_freq << "\n";
        // std::cout << "Bin number: " << peak_bin << "\n";
        // std::cout << "FFT bin size: " << f_bin << " Hz/bin\n";
        // std::cout << "Magnitude at peak: " << *peak_it << "\n";
        #endif

        // Scale the results for posterior processing
        double scale = 1.0 / frame_size;
        for (size_t k = 1; k < frame_size/2; ++k) {
            res[k] *= scale;
        }
        res[0] *= 1.0 * scale;
        res[fft_size - 1] *= 1.0 * scale;

        // Store the scaled FFT results of the current frame along with the others 
        results_fft.push_back(res);

        // Calculate the PSD from the current frame
        for (size_t k = 0; k < res.size(); ++k) { 
            psd[k] = std::norm(res[k]);
        }
        psd_signal_frames.push_back(psd);

        // 3. Estimate the noise PSD
        // Update the information of the noise estimator with the PSD of the current frame

        noise_est.update(psd);
        psd_noise = noise_est.getNoiseEstimate();
    
        psd_noise_frames.push_back(psd_noise);
        
        // 4. Apply filter
        // filtered_frame = filter.apply(res, psd, true_noise_psd[frame_counter]);
        filtered_frame = filter.apply(res, psd, psd_noise);

        // 5. Apply IFFT
        // Compute the C2R DFT (no scaling)
        c2r(shape, stride_X, stride_x, axes, BACKWARD, filtered_frame.data(), recon_frame.data(), 1.0);
        //--------------------------------

        // 6. Compute Overlap-add
        #ifdef OVERLAPADD
        if (frame_counter == 0){
            // Copies the first half of the first frame
            // std::copy(recon_frame.begin(), recon_frame.begin() + hop, recon_signal.begin());
            for (size_t i = 0; i < hop; i++){
                recon_signal[i] = recon_frame[i];
            }
        }
        else{
            // Add the first half of the current frame with the last half of the last frame
            for (size_t i = 0; i < hop; i++){
                recon_signal[(frame_counter * hop) + i] = recon_frame[i] + delayed_samples[i];
            }
        }
        #else
        for (size_t i = 0; i < frame_size; i++){
            recon_signal[(frame_counter * frame_size) + i] = recon_frame[i];
        }
        #endif
        //---------------------------------
        
        // Store the second half of the current frame
        // std::copy(recon_frame.begin() + hop, recon_frame.end(), delayed_samples.begin());
        for (size_t i = 0; i < hop; i++){
            delayed_samples[i] = recon_frame[i + hop];
        }

        // Increment counter
        frame_counter++;
    }
    std::cout << "--- Frame counter status: " << ++frame_counter << std::endl;

    // Generate a file with all the windowed frames
    writeFrames(frames, "out/output_frames.txt");

    // Generate a file with all the FFT results
    writeFFT(results_fft);

    // Generate a file with all the signal PSD results in frames
    writeFrames(psd_signal_frames, "out/output_psd_signal.txt");

    // Generate a file with all the Noise PSD results in frames
    writeFrames(psd_noise_frames, "out/output_psd_est_noise.txt");

    // Generate a file with the reconstructed signal
    WriteSignal(recon_signal);

    std::cout << "--- Generated output files" << std::endl;
    std::cout << "\n--- C++ Processing Finished --- \n" << std::endl;
    return 0;
}