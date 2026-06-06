# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-06

### Added
- **Real-Time FFT Analyzer**: Cooley-Tukey 1024-point C++ FFT component (`chakra_component.h`) executing bare-metal on ESP32-S3.
- **Microphone Streaming**: Audio capture via twin ES7210 MEMS microphones utilizing DMA buffers over I2S at 16 kHz.
- **Home Assistant API Integration**: Real-time push of detected chakra name and matching RGB color value to HA.
- **Interactive LCD GUI**: Real-time visual spectrum bars, peak frequency, and level meters rendered on the 2.4″ IPS display.
- **Robust Build Management**: `Makefile` interface for automated esphome compile, validation, flashing, and logs.
- **CI Config Validate**: GitHub Action workflow validating ESPHome configuration files.
