#pragma once
#include <vector>
#include <string>
#include <complex>
#include <cstdint>

std::vector<float> readBinData(const std::string& filename);
std::vector<float> readHexData(const std::string& filename);

// Saves a 2D vector of doubles to a .txt file with a metadata header
void writeFrames(const std::vector<std::vector<double>>& frames, const std::string& filename);

// Saves a 2D vector of complex doubles to a .txt file with a metadata header
void writeFFT(const std::vector<std::vector<std::complex<double>>>& fftFrames);

// Saves a 1D vector of a signal in doubles to a .txt file without metadata header
void WriteSignal(const std::vector<double> &signal);

std::vector<std::vector<double>> readFrames(const std::string& filename);

void testReadWrite();
