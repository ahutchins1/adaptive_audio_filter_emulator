#include "fileio.hpp"
#include <fstream>
#include <stdexcept>
#include <iomanip>
#include <sstream>

#include <vector>
#include <string>
#include <iostream>

std::vector<float> readBinData(const std::string& filename) {
    std::vector<float> samples;
    std::ifstream file(filename);
    
    if (!file.is_open()) {
        throw std::runtime_error("Could not open file: " + filename);
    }
    
    std::string line;
    while (std::getline(file, line)) {
        uint16_t raw_value = 0;
        for (char c : line) {
            raw_value = (raw_value << 1) | (c == '1' ? 1 : 0);
        }

        int16_t fixed_value;
        if (raw_value & 0x8000) { 
            fixed_value = static_cast<int16_t>(raw_value | 0xFFFF0000); 
        } else {
            fixed_value = static_cast<int16_t>(raw_value);
        }
        
        float float_value = static_cast<float>(fixed_value) / 32768.0f;
        samples.push_back(float_value);
    }
    
    return samples;
}

std::vector<float> readHexData(const std::string& filename) { 
    std::ifstream file(filename);
    std::vector<float> data;
    std::string line;
    while (std::getline(file, line)) {
        unsigned int hex;
        std::stringstream ss(line);
        ss >> std::hex >> hex;
        int16_t val = static_cast<int16_t>(hex & 0xFFFF);
        float fval = static_cast<float>(val) / 32768.0f;
        data.push_back(fval);
    }
    return data;
}

void writeFrames(const std::vector<std::vector<double>>& frames, const std::string& filename) {
    if (frames.empty()) return;

    std::ofstream file(filename);
    if (!file) {
        throw std::runtime_error("Could not open file for writing: " + filename);
    }

    const size_t frameSize = frames[0].size();
    const size_t numFrames = frames.size();

    file << "frameSize=" << frameSize 
         << ",numFrames=" << numFrames 
         << ",type=double\n";

    file << std::fixed << std::setprecision(15); 
    for (const auto& frame : frames) {
        if (frame.size() != frameSize) {
            throw std::runtime_error("Inconsistent frame size in writeFrames");
        }
        for (size_t i = 0; i < frame.size(); ++i) {
            file << frame[i];
            if (i < frame.size() - 1) file << ",";
        }
        file << "\n";
    }
}

void writeFFT(const std::vector<std::vector<std::complex<double>>>& fftFrames) {
    const std::string& filename = "out/output_fft.txt";
    if (fftFrames.empty()) return;

    std::ofstream file(filename, std::ios::binary);
    if (!file) {
        throw std::runtime_error("Could not open file for writing: " + filename);
    }

    const size_t frameSize = fftFrames[0].size();
    const size_t numFrames = fftFrames.size();

    std::string header = "frameSize=" + std::to_string(frameSize)
                       + ",numFrames=" + std::to_string(numFrames)
                       + ",type=complex<double>\n";
    file.write(header.c_str(), header.size());

    for (const auto& frame : fftFrames) {
        if (frame.size() != frameSize) {
            throw std::runtime_error("Inconsistent frame size in writeFFT");
        }
        for (size_t i = 0; i < frame.size(); ++i) {
            file << frame[i].real() << "," << frame[i].imag();
            if (i < frame.size() - 1) file << ",";
        }
        file << "\n";
    }

    file.close();
}

void WriteSignal(const std::vector<double> &signal){
    if (signal.empty()) return;
    const std::string& filename = "out/output_recon_signal.txt"; 
    std::ofstream file(filename);

    for (size_t i = 0; i < signal.size(); ++i) {
        file << signal[i];
        if (i != signal.size() - 1) { 
            file << " ";         
        }
    }
    file.close();
}

std::vector<std::vector<double>> readFrames(const std::string& filename) {
    std::ifstream file(filename);
    if (!file) {
        throw std::runtime_error("Could not open file for reading: " + filename);
    }

    std::string header;
    std::getline(file, header);
    
    size_t frameSize = 0;
    size_t numFrames = 0;
    std::string type;
    
    std::istringstream headerStream(header);
    std::string token;
    
    while (std::getline(headerStream, token, ',')) {
        size_t equalsPos = token.find('=');
        if (equalsPos != std::string::npos) {
            std::string key = token.substr(0, equalsPos);
            std::string value = token.substr(equalsPos + 1);
            
            if (key == "frameSize") {
                frameSize = std::stoul(value);
            } else if (key == "numFrames") {
                numFrames = std::stoul(value);
            } else if (key == "type") {
                type = value;
            }
        }
    }

    if (frameSize == 0 || numFrames == 0) {
        throw std::runtime_error("Invalid header in file: " + filename);
    }
    if (type != "double") {
        throw std::runtime_error("Unsupported data type in file: " + type);
    }

    std::vector<std::vector<double>> frames;
    frames.reserve(numFrames);
    
    std::string line;
    size_t framesRead = 0;
    
    while (std::getline(file, line) && framesRead < numFrames) {
        if (line.empty()) continue;
        
        std::vector<double> frame;
        frame.reserve(frameSize);
        
        std::istringstream lineStream(line);
        std::string valueStr;
        
        while (std::getline(lineStream, valueStr, ',')) {
            try {
                frame.push_back(std::stod(valueStr));
            } catch (const std::exception& e) {
                throw std::runtime_error("Failed to parse double value: " + valueStr);
            }
        }
        
        if (frame.size() != frameSize) {
            throw std::runtime_error("Frame size mismatch in file. Expected: " + 
                                   std::to_string(frameSize) + ", Got: " + 
                                   std::to_string(frame.size()));
        }
        
        frames.push_back(std::move(frame));
        framesRead++;
    }
    
    if (framesRead != numFrames) {
        throw std::runtime_error("Number of frames mismatch. Expected: " + 
                               std::to_string(numFrames) + ", Read: " + 
                               std::to_string(framesRead));
    }
    
    return frames;
}

void testReadWrite() {
    std::vector<std::vector<double>> testFrames = {
        {1.0, 2.0, 3.0, 4.0},
        {5.5, 6.6, 7.7, 8.8},
        {0.123456789012345, -1.23456789012345, 9.87654321098765, 0.0}
    };
    
    const std::string filename = "test_frames.txt";
    
    try {
        writeFrames(testFrames, filename);
        std::cout << "Successfully wrote " << testFrames.size() << " frames to " << filename << std::endl;

        auto readFramesz = readFrames(filename);
        std::cout << "Successfully read " << readFramesz.size() << " frames from " << filename << std::endl;
  
        if (testFrames.size() != readFramesz.size()) {
            std::cout << "Frame count mismatch!" << std::endl;
            return;
        }
        
        for (size_t i = 0; i < testFrames.size(); ++i) {
            if (testFrames[i].size() != readFramesz[i].size()) {
                std::cout << "Frame size mismatch at index " << i << std::endl;
                return;
            }
            
            for (size_t j = 0; j < testFrames[i].size(); ++j) {
                if (std::abs(testFrames[i][j] - readFramesz[i][j]) > 1e-15) {
                    std::cout << "Data mismatch at frame " << i << ", element " << j << std::endl;
                    return;
                }
            }
        }
        
        std::cout << "Data integrity verified successfully!" << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
    }
}