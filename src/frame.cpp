// frame.cpp
#include "frame.hpp"
#include <filesystem>

// frame.cpp
Frame::Frame(size_t frameSize, const std::vector<float>& coeffs)
    : size(frameSize), windowCoeffs(coeffs) {}

std::vector<double> Frame::generateFrame(const std::vector<float>& input, size_t startIndex) {
    std::vector<double> frame(size);
    for (size_t i = 0; i < size; ++i) {
        frame[i] = static_cast<float>(input[startIndex + i]) * windowCoeffs[i];
    }
    return frame;
}