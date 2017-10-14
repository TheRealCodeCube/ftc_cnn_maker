# ftc_cnn_maker
Utilities for creating convolutional neural networks (CNNs) for use with FTC robots.

# Required Packages (For debian-based linuxes)
Currently, this only works on Linux. You will need to install several packages to make it 
work. If you use a non-debian derivative of linux, the package names will be different.
- `android-tools-adb` (provides `adb` command)
- `caffe-cpu` or `caffe-cuda` (provides `caffe` command, requires non-free repositories)
- `imagemagick` (used for resizing input images to the correct size)
- `python3` (because the entire utility is written in Python-3)
- `python3-lmdb` (LMDB is the easiest database system to get working with caffe)
- `python3-matplotlib` (used for decoding of training data)
- `python3-numpy` (used for transposition of training data)
- `python3-tk` (gui library used to create the interface)

one-shot command:

    $ sudo apt-get install -y android-tools-adb caffe-cpu imagemagick python3 python3-lmdb python3-matplotlib python3-numpy python3-tk

# Usage
press buttons, they do things. (TODO: make this actually explain how to use it.)
