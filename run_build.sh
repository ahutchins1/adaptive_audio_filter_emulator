
#!/bin/bash
python python/samples.py
chmod +x run_build.sh
rm -r build
rm -r out
cmake -S . -B build -G "MinGW Makefiles"

# # Check if CMake configuration was successful
if [ $? -ne 0 ]; then
    echo "CMake configuration failed. Please check the errors above."
    exit 1
fi
echo "CMake configuration successful."

cmake --build build

# Check if compilation was successful
if [ $? -ne 0 ]; then
    echo "Compilation failed. Please check the errors above."
    exit 1
fi
echo "Project built successfully."

echo ""
echo -e "\e[1;33m Running the C++ backend executable... \e[0m"
echo ""

powershell -Command " \
  Start-Process -FilePath '$(pwd -W | sed 's|/|\\|g')\\build\\out\\AudioFilterSim.exe' \
    -WorkingDirectory '$(pwd -W | sed 's|/|\\|g')' \
    -NoNewWindow -Wait \
"
echo ""
echo -e "\e[1;33m Running the python GUI... \e[0m"
echo ""

python python/emulator_GUI.py