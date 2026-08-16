# GRAIL: Gesture-Controlled Robotic Hand with On-Device AI Inference

[![Video Simulation](https://img.shields.io/badge/Watch-Video_Simulation-red?logo=youtube)](https://drive.google.com/file/d/1D5U6A-xz78___bFntrZBHNr2fK748HhY/view?usp=sharing)
[![Platform](https://img.shields.io/badge/Platform-STM32H7-blue.svg)](https://www.st.com/en/microcontrollers-microprocessors/stm32h7-series.html)
[![AI](https://img.shields.io/badge/AI-TensorFlow_|_MediaPipe-orange.svg)]()

## Overview
**GRAIL** (Gesture-Controlled Robotic Hand with On-Device AI Inference) is a hardware-software integration project that controls a robotic hand using vision-based gesture recognition. By migrating the architecture from an ESP32 to an STM32H7 microcontroller, this project achieves **full on-device edge inference**, bypassing the need for cloud computing. 

A custom dense neural network trained on 21-point MediaPipe hand-landmark data is deployed directly onto the microcontroller via X-CUBE-AI, utilizing INT8 quantization to achieve high accuracy with a minimal memory footprint.

## Key Features
* **Edge AI Inference:** Full on-device neural network execution on the STM32H7.
* **High Accuracy & Efficiency:** Reaches **99.3% classification accuracy** while fitting entirely within **3 KB of RAM**.
* **Model Optimization:** Employs **INT8 quantization** via X-CUBE-AI to overcome low-level firmware and data-quantization constraints.
* **Computer Vision:** Utilizes **MediaPipe** for extracting 21-point hand-landmark data to feed into the neural network.

## Tech Stack
* **Languages:** Python, C (Embedded)
* **Hardware:** STM32H7 Microcontroller, Robotic Hand Assembly
* **PCB Design:** KiCad
* **Tools & Frameworks:** STM32CubeIDE, X-CUBE-AI, TensorFlow, MediaPipe

## System Architecture
1. **Data Collection & Processing:** A camera captures hand gestures, and Python scripts utilizing MediaPipe extract the 21 3D hand landmarks.
2. **Model Training:** A custom dense neural network is trained on these coordinates using TensorFlow to classify different gestures.
3. **Quantization & Deployment:** The trained model is quantized to INT8 and converted into optimized C code using STMicroelectronics' X-CUBE-AI.
4. **On-Device Inference:** The STM32H7 runs the AI model locally, processing incoming landmark data and mapping it to specific servo movements on the robotic hand.

## Contributors
* **Aniket Kumar Rai** 
* **Aditya Gautam**
* **Aditya Kumar**
* **Abhay Kumar**

## Demo
Check out the [Video Simulation](https://drive.google.com/file/d/1D5U6A-xz78___bFntrZBHNr2fK748HhY/view?usp=sharing) to see the robotic hand in action.
