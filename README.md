# esp32s3box3-chakra-color-detector-v3

**An experimental ESPHome firmware project** that turns an ESP32-S3-BOX-3 into a real-time FFT sound analyser — detecting singing-bowl frequencies and controlling colored lights for sound healing events.

---

## The Story

This started as an experiment. Can you take a €40 ESP32 dev board, point a microphone at a singing bowl, and have it figure out which chakra is resonating — then light up the room in real time?

The answer turned out to be yes.

Over many late nights of vibe-coding — iterating on a 1024-point Cooley-Tukey FFT running bare-metal on an ESP32-S3, talking to Home Assistant over Wi-Fi, pushing RGB colours to Philips Hue bulbs while bowls were still ringing — it all came together. The device was programmed, flashed, and tested entirely through USB-C and OTA Wi-Fi updates, never once connecting a hardware debugger.

The whole experience proved something: modern AI-assisted development makes embedded systems surprisingly accessible. From GPIO strapping pin warnings to I2S microphone DMA buffer tuning — every obstacle was solvable in hours or days, not weeks or months. External devices, sensors, lights, media players — all orchestrated from a single YAML config and a self-contained C++ header.

This repo is the result. A snapshot of an experiment. Use it, fork it, learn from it, improve it.

---

## What It Does

- Captures audio from the built-in ES7210 MEMS microphones at 16 kHz
- Runs a 1024-point FFT in real time on-device (15.6 Hz/bin resolution)
- Maps the dominant frequency band to one of 7 chakras
- Pushes the detected chakra name + RGB colour to Home Assistant
- Controls a configurable HA light entity — changing room colour as bowls play
- Shows live FFT bars, peak frequency, and signal level on the 2.4" IPS display

| # | Chakra | Frequency | Colour |
|---|--------|-----------|--------|
| 0 | Root | 32–64 Hz | #FF0000 |
| 1 | Sacral | 64–128 Hz | #FF7F00 |
| 2 | Solar Plexus | 128–256 Hz | #FFFF00 |
| 3 | Heart | 256–512 Hz | #00CC00 |
| 4 | Throat | 512–1024 Hz | #0000FF |
| 5 | Third Eye | 1024–2048 Hz | #4B0082 |
| 6 | Crown | 2048–4096 Hz | #EE82EE |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/alexanderbrunker-star/esp32s3box3-chakra-color-detector-v3
cd esp32s3box3-chakra-color-detector-v3

# 2. Set up secrets (copy example → fill in real values)
cp secrets.example.yaml secrets.yaml
# Edit secrets.yaml with your Wi-Fi credentials, HA host, and API encryption key

# 3. Configure your device
# Edit device_config.yaml — set your HA light entity, media player, etc.

# 4. Validate
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

ESP32-S3-BOX-3 with Sensor Dock:

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

## Vibe-Coding Stack

The entire project was built with AI-assisted development:

- **Code**: ESPHome YAML config + custom C++ FFT header
- **Firmware**: ESP-IDF via PlatformIO (ESPHome managed)
- **Flashing**: USB-C serial bridge + OTA Wi-Fi updates
- **Integration**: Home Assistant Native API + REST services
- **Targets**: ESP32-S3, Philips Hue, Spotify, external media players
- **Dev loop**: Edit YAML → `make validate` → `make flash` → observe → repeat

No hardware debuggers. No C toolchain setup. Just a laptop, a USB-C cable, and an idea.

---

## Home Assistant Entities

| Entity | Type | Description |
|--------|------|-------------|
| `text_sensor.chakra_active_name` | Text sensor | Active chakra name |
| `text_sensor.chakra_active_color` | Text sensor | Active colour hex |
| `switch.chakra_mode` | Switch | Enable/disable analyser |
| Configurable light | Light | Auto-coloured on chakra detection |

---

## Resources

- [ESPHome Documentation](https://esphome.io/)
- [Home Assistant ESPHome Integration](https://www.home-assistant.io/integrations/esphome/)
- [BigBobbas upstream config](https://github.com/BigBobbas/ESP32-S3-Box3-Custom-ESPHome)
- [Espressif ESP32-S3-BOX-3 Hardware](https://github.com/espressif/esp-box)
