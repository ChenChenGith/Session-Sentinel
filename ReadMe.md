This is a python tool for capturing images automatically by periodic check whether the pixels in the designate have been changed.
20250924 News! Now this tool can perform speech recognition using Alibaba Cloud's real-time speech recognition model.

The exe program can be found in the releas page: [Releases · ChenChenGith/Video_PPT_capture](https://github.com/ChenChenGith/Video_PPT_capture/releases)

Requirment:

- Python>=3.8
- pillow>=10.4.0
- screeninfo>=0.8.1
- dashscope>=1.24.5
- pyaudio>=0.2.14

# Usage:

![alt text](asset/help_image.png)

[使用说明](./asset/help_md.md)

# Update

 Added a new position to fill in a custom real-time speech recognition model

## 20260106

The voice recognition feature has been added.

Optimizations have been made to the interface and storage paths.

## 20250924

The voice recognition feature has been added.

Optimizations have been made to the interface and storage paths.

## 20250122

Support multi-screen with any layout.

Remove Numpy to reduce the exe size (from 35M to 12M, have not release).

Modify the initial location of the float window, to let user note it.

Add a checkbox to allow user to chose whether display float window.

Add a button for opening the image save path.

# TODO:

- [X] Test on multiple displays
- [X] Allow users to config whether display float window

# Compile:

The exe program is compiled by ``pyinstaller``. To reduce the exe size, it is better to create a new environment and install necessary package.

Then use the following command to generate exe program:

```
pyinstaller -Fw -i asset/ycy.ico --add-data "asset;asset" screen_capture.py
```
