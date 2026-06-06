# Contributing to ESP32-S3-BOX-3 Chakra V3

We welcome contributions to optimize the on-device FFT analyzer, improve the user interface on the LCD, or expand integrations with Home Assistant.

## How to Contribute

1. **Check Issues**: Scan active issues for duplicates before starting.
2. **Fork and Branch**: Fork the repo and create your branch: `feat/improve-fft` or `fix/i2s-timing`.
3. **Develop**:
   - Write clean, performance-optimized C++ for `chakra_component.h`. Keep memory constraints (PSRAM/SRAM limits) in mind.
   - Refactor or enhance YAML templates safely in `esp32s3box3.yaml`.
   - Test config changes using `make validate` (runs ESPHome validator).
4. **Commit**: Use Conventional Commits formatting (e.g. `feat: optimize Cooley-Tukey butterfly loop`, `fix: correct I2S audio pin configuration`).
5. **PR**: Open a pull request against the `main` branch.

## Development Setup

```bash
# Validate your configuration
make validate

# Flash to device via serial USB-C
make flash

# Monitor serial logs
make logs
```
