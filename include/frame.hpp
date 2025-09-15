// frame.hpp
#pragma once
#include <vector>
#include <cstdint>

class Frame {
public:
    Frame(size_t frameSize, const std::vector<float>& coeffs);
    std::vector<double> generateFrame(const std::vector<float>& input, size_t startIndex);

private:
    size_t size;
    std::vector<float> windowCoeffs;
};
