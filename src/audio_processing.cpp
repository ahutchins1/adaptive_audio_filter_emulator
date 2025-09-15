#include "audio_processing.hpp"
#include <iostream>
#include <iomanip>

//Minimum Statistics Noise Estimator
NoiseEstimator::NoiseEstimator(size_t num_bins_param, size_t d_param)
: num_bins(num_bins_param), d(d_param), psd_smoothed(num_bins_param, 0.0), 
psd_history_buffer (num_bins_param,std::vector<double>(d_param, 1.0)),
psd_noise_est(num_bins_param, 1e-10), bias_comp(num_bins_param, 1.2), idx(0){}

void NoiseEstimator::update(const std::vector<double>& current_power_spectrum){
    double alpha = 0.8; // α - smoothing factor
    for (size_t i = 0; i < num_bins; i++){
        // Smoothe the PSD in the current bin
        // P_noise_smoothed[i] = α * P_noise_smoothed[i] + (1-α) * P_min[i] -> Leaky Integrator
        psd_smoothed[i] = (alpha * psd_smoothed[i]) + ((1 - alpha) * current_power_spectrum[i]);

        // Copy the smoothed psd up to the current frame into the buffer
        psd_history_buffer[i][idx] = psd_smoothed[i]; 

        // Find the minimum power value in the bin across the d frames
        auto min_psd = *std::min_element(psd_history_buffer[i].begin(), psd_history_buffer[i].end());

        // Apply the bias compensation factor
        psd_noise_est[i] = bias_comp[i] * min_psd;
        // psd_noise_est[i] = 0.0003;
    }
    idx = (idx + 1) % d; // Increment the frame index within the d limit of frames in history
}

const std::vector<double>& NoiseEstimator::getNoiseEstimate() const{
    return psd_noise_est;
}


// Decision-Directed approach on Wiener filter
WienerFilter::WienerFilter(size_t frame_size_param)
                :frame_size(frame_size_param), p_xi(frame_size_param,0.0),
                p_wiener_gain(frame_size_param,0.0), p_SNR(frame_size_param,1e-10){}

std::vector<std::complex<double>> WienerFilter::apply(
    const std::vector<std::complex<double>>& current_frame,     // Current frame's spectrum
    const std::vector<double>& psd,                             // PSD of the unfiltered signal (voice + noise)
    const std::vector<double>& psd_noise_est                    // PSD of the estimated noise in the frame   
){
    // X(k,n) = S(k,n) + W(k,n)
    // |X(k, n)|² : PSD of the unfiltered signal.
    // |Ŵ(k, n)|² : PSD of the estimated noise signal.
    // |Ŝ(k, n)|² : PSD of the estimated clean voice signal.

    double alpha_w = 0.35;   // Smoothing factor for Decision-Directed approach
    double alpha_snr = 0.15; // Smoothing factor for SNR
    size_t fft_size = (frame_size / 2) + 1;
    std::vector<std::complex<double>> filtered_signal_fft(fft_size);
    for (size_t k = 0; k < fft_size; k++){
        double SNR = (alpha_snr * p_SNR[k]) + ((1 - alpha_snr) * (psd[k] / (psd_noise_est[k])));

        double term1 = alpha_w * p_xi[k];                                     
        double term2 = (1 - alpha_w) * std::max((SNR - 1),1e-10);  // Decision-Directed "voice detection"
        
        // Current a priori SNR using Decision-Directed approach
        // ξ(k, n) = α_dd * (ξ(k, n-1)) + (1 - α_dd) * max((|X(k, n)|² / |Ŵ(k, n)|²) - 1, 0 )
        double xi = term1 + (term2);

        // Ŝ(k, n) = ξ(k, n) / (1 + ξ(k, n)) * X(k,n)
        double wiener_gain = std::isnan(xi) ? 0.0 : xi / (1.0 + xi);
        filtered_signal_fft[k] = current_frame[k] * wiener_gain;

        // Store the values of the variables for the next call
        p_xi[k] = xi;
        p_SNR[k] = SNR;
    }
    return filtered_signal_fft;
}