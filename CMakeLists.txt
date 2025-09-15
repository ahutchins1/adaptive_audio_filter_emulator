cmake_minimum_required(VERSION 3.12)
project(AudioFilterSim)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_EXE_LINKER_FLAGS "-static-libgcc -static-libstdc++ -static")

# Add include directory
include_directories(include)

# Add executable and source files
add_executable(AudioFilterSim
    src/main.cpp
    src/frame.cpp
    src/fileio.cpp
    src/audio_processing.cpp
)

# Optional: Set output directory for binaries
set_target_properties(AudioFilterSim PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/out
)
