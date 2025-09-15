#pragma once
#include <cstdint>
#include <vector>
#include <complex>
#include <algorithm>
#include <iostream>

class NoiseEstimator{
    private:
        size_t num_bins;
        size_t d;

        std::vector<double> psd_smoothed;
        std::vector<std::vector<double>> psd_history_buffer;  
        std::vector<double> psd_noise_est;
        std::vector<double> bias_comp;                
        size_t idx;                                 
    public:  
        NoiseEstimator(size_t num_bins_param, size_t d_param);
        void update(const std::vector<double>& current_power_spectrum);
        const std::vector<double>& getNoiseEstimate() const;
};

class WienerFilter{
    private: 
        size_t frame_size;
        std::vector<double> p_xi;
        std::vector<double> p_wiener_gain;
        std::vector<double> p_SNR;
    public:
        WienerFilter(size_t frame_size_param);
        std::vector<std::complex<double>> apply(const std::vector<std::complex<double>>& current_frame,
        const std::vector<double>& psd, const std::vector<double>& psd_noise_est);
};

