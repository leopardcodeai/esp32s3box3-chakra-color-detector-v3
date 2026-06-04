# ESP32-S3-BOX-3 Chakra V3

> **Real-time FFT sound analyser** for the ESP32-S3-BOX-3 — detects singing-bowl frequencies, maps them to the 7 chakras, and controls smart lights via Home Assistant. Built with vibe-coding workflows by [LeopardCode.AI](https://leopardcode.ai).

[![ESPHome](https://img.shields.io/badge/ESPHome-2026.4-blue)](https://esphome.io)
[![ESP32](https://img.shields.io/badge/Target-ESP32--S3--BOX--3-orange)](https://github.com/espressif/esp-box)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## The Story

This started as an experiment. Can you take a €40 ESP32 dev board, point a microphone at a singing bowl, and have it figure out which chakra is resonating — then light up the room in real time?

The answer turned out to be **yes**.

Over many late nights of vibe-coding — iterating on a 1024-point Cooley-Tukey FFT running bare-metal on an ESP32-S3, talking to Home Assistant over Wi-Fi, pushing RGB colours to Philips Hue bulbs while bowls were still ringing — it all came together. The device was programmed, flashed, and tested entirely through USB-C and OTA Wi-Fi updates, never once connecting a hardware debugger.

The whole experience proved something: **modern AI-assisted development makes embedded systems surprisingly accessible.** From GPIO strapping pin warnings to I2S microphone DMA buffer tuning — every obstacle was solvable in hours or days, not weeks or months. External devices, sensors, lights, media players — all orchestrated from a single YAML config and a self-contained C++ header.

This repo is the result. A snapshot of an experiment. Use it, fork it, learn from it, improve it.

---

## What It Does

- Captures audio from the built-in **ES7210 MEMS microphones** at 16 kHz
- Runs a **1024-point FFT** in real time on-device (15.6 Hz/bin resolution)
- Maps the dominant frequency band to one of **7 chakras**
- Pushes the detected chakra name + RGB colour to **Home Assistant**
- Controls a configurable HA light entity — changing room colour as bowls play
- Shows live FFT bars, peak frequency, and signal level on the **2.4" IPS display**

### Chakra Frequency Map

| # | Chakra | Frequency Range | Colour |
|:-:|--------|:---------------:|--------|
| 0 | Root | 32–64 Hz | `#FF0000` |
| 1 | Sacral | 64–128 Hz | `#FF7F00` |
| 2 | Solar Plexus | 128–256 Hz | `#FFFF00` |
| 3 | Heart | 256–512 Hz | `#00CC00` |
| 4 | Throat | 512–1024 Hz | `#0000FF` |
| 5 | Third Eye | 1024–2048 Hz | `#4B0082` |
| 6 | Crown | 2048–4096 Hz | `#EE82EE` |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/leopardcodeai/esp32s3box3-chakra-color-detector-v3.git
cd esp32s3box3-chakra-color-detector-v3

# 2. Set up secrets (copy example → fill in real values)
cp secrets.example.yaml secrets.yaml
# Edit secrets.yaml with your Wi-Fi credentials, HA host, and API encryption key

# 3. Configure your device
# Edit device_config.yaml — set your HA light entity, media player, etc.

# 4. Validate configuration
make validate

# 5. Flash via USB-C
make flash

# 6. Or OTA (once on Wi-Fi)
make ota

# 7. Watch logs
make logs
```

---

## Hardware

**ESP32-S3-BOX-3** with Sensor Dock — an inexpensive but powerful edge-AI platform.

| Component | Detail |
|-----------|--------|
| MCU | ESP32-S3-WROOM-1 — dual-core LX7 @ 240 MHz |
| Flash | 16 MB Quad Flash |
| PSRAM | 16 MB Octal PSRAM |
| Display | 2.4″ IPS 320×240 SPI TFT with capacitive touch |
| Microphones | ES7210 — 2× digital MEMS via I2S |
| Speaker | ES8311 DAC + onboard amplifier |
| Wireless | Wi-Fi 4 + Bluetooth 5.0 LE |

---

## Key Files

| File | Purpose |
|------|---------|
| `esp32s3box3.yaml` | Main ESPHome configuration (~4300 lines) |
| `device_config.yaml` | All user-configurable settings — edit this first |
| `chakra_component.h` | Self-contained C++ FFT analyser (1024-pt Cooley-Tukey) |
| `secrets.yaml` | Wi-Fi credentials + API key — never commit |
| `secrets.example.yaml` | Safe placeholder for CI — committed |

---

## Home Assistant Entities

| Entity | Type | Description |
|--------|------|-------------|
| `text_sensor.chakra_active_name` | Text sensor | Active chakra name |
| `text_sensor.chakra_active_color` | Text sensor | Active colour hex |
| `switch.chakra_mode` | Switch | Enable/disable analyser |
| Configurable light | Light | Auto-coloured on chakra detection |

---

## Vibe-Coding Stack

The entire project was built with AI-assisted development — no hardware debuggers, no C toolchain setup, just a laptop and a USB-C cable.

- **Code**: ESPHome YAML config + custom C++ FFT header
- **Firmware**: ESP-IDF via PlatformIO (ESPHome managed)
- **Flashing**: USB-C serial bridge + OTA Wi-Fi updates
- **Integration**: Home Assistant Native API + REST services
- **Targets**: ESP32-S3, Philips Hue, Spotify, external media players
- **Dev loop**: Edit YAML → `make validate` → `make flash` → observe → repeat

---

## Resources

- [ESPHome Documentation](https://esphome.io/)
- [Home Assistant ESPHome Integration](https://www.home-assistant.io/integrations/esphome/)
- [BigBobbas upstream ESP32-S3-BOX-3 config](https://github.com/BigBobbas/ESP32-S3-Box3-Custom-ESPHome)
- [Espressif ESP32-S3-BOX-3 Hardware](https://github.com/espressif/esp-box)
- [LeopardCode.AI — AI Engineering & Consulting](https://leopardcode.ai)

---

<p align="center">
  <sub>Built with vibe-coding workflows by <a href="https://leopardcode.ai">LeopardCode.AI</a></sub><br>
  <sub>Dr. Alexander Brunker — AI Engineering &amp; Consulting</sub>
</p>
