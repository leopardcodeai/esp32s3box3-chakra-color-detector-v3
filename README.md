# ESP32-S3-BOX-3 Custom ESPHome — Chakra Analyser Edition

ESPHome firmware for the **Espressif ESP32-S3-BOX-3** with Sensor Dock, built on top of the [BigBobbas custom config](https://github.com/BigBobbas/ESP32-S3-Box3-Custom-ESPHome). Extends the original with a **Chakra Frequency Analyser** page that listens to the built-in MEMS microphones, detects dominant singing-bowl frequencies via FFT, maps them to the 7 chakras, and pushes the result to Home Assistant.

### v3 — AWS Bedrock Integration

The device now supports an **AWS Bedrock multi-agent pipeline** for intelligent chakra-to-light mapping. When the cloud icon (☁) in the header bar is active (green), detected frequencies are sent to AWS Bedrock's **ChakraMaster** supervisor agent, which orchestrates sub-agents (AcousticAnalyzer + SpiritualGuide) to analyse the frequency and set the HA light via Lambda. When the cloud icon is off (white), the local ESP32 pipeline controls the light directly.

```
ESP32 Mic → FFT → Frequency
                      │
         ┌────────────┴────────────┐
         │ ☁ OFF                   │ ☁ ON
         ▼                         ▼
    ESP32 → HA               ESP32 → Relay → AWS Bedrock
    (direct, instant)        ChakraMaster → Lambda → HA
```

---

## Hardware

### ESP32-S3-BOX-3 Specifications

| Component | Detail |
|-----------|--------|
| Board | ESP32-S3-BOX-3 + Sensor Dock |
| MCU | ESP32-S3-WROOM-1 — dual-core LX7 @ up to 240 MHz |
| Flash | 16 MB Quad Flash |
| PSRAM | 16 MB Octal PSRAM |
| Display | 2.4″ IPS 320 × 240 SPI TFT (ILI9342C) with capacitive touch |
| Touch | GT911 capacitive controller |
| Mic ADC | ES7210 — 2× digital MEMS microphones via I2S |
| Audio DAC | ES8311 — onboard speaker amplifier |
| IMU | 3-axis gyroscope + 3-axis accelerometer |
| Wireless | Wi-Fi 4 (2.4 GHz) + Bluetooth 5.0 LE |
| USB | 1× USB-C — power + UART download/debug |
| Connector | High-density PCIe connector for accessories |

### GPIO Pin Assignment

> ⚠️ **Pre-deploy mandatory check**: run `make pins` before every flash to detect conflicts.

| GPIO | Signal | Component | Notes |
|------|--------|-----------|-------|
| GPIO0 | Boot button | Physical button | Strapping pin — `ignore_strapping_warning` required |
| GPIO2 | I2S MCLK | ES7210 + ES8311 | Master clock |
| GPIO3 | Touch INT | GT911 | Strapping pin — `ignore_strapping_warning` required |
| GPIO4 | Display DC | ILI9342C (SPI) | Data/Command select |
| GPIO5 | Display CS | ILI9342C (SPI) | Chip select |
| GPIO6 | SPI MOSI | ILI9342C (SPI) | Display data |
| GPIO7 | SPI CLK | ILI9342C (SPI) | Display clock |
| GPIO8 | I2C-A SDA | ES7210, ES8311, GT911 | Bus A — 100 kHz |
| GPIO10 | Battery voltage ADC | ADC sensor (Dock) | `platform: adc`, diagnostic entity |
| GPIO15 | I2S DOUT | ES8311 (speaker out) | |
| GPIO16 | I2S DIN | ES7210 (mic in) | |
| GPIO17 | I2S BCLK | ES7210 + ES8311 | Bit clock |
| GPIO18 | I2C-A SCL | ES7210, ES8311, GT911 | Bus A — 100 kHz |
| GPIO21 | Radar presence | LD2410 sensor (Dock) | |
| GPIO40 | I2C-B SCL | Sensor Dock bus | Bus B — 50 kHz |
| GPIO41 | I2C-B SDA | Sensor Dock bus | Bus B — 50 kHz |
| GPIO45 | I2S LRCK | ES7210 + ES8311 | Strapping pin — `ignore_strapping_warning` required |
| GPIO46 | Speaker enable | PA enable | Strapping pin — `ignore_strapping_warning` required |
| GPIO47 | LCD Backlight | LEDC PWM output | Monochromatic light `led` |
| GPIO48 | Display RST | ILI9342C (SPI) | Inverted logic |

### Accessories

| Accessory | Description |
|-----------|-------------|
| **ESP32-S3-BOX-3-DOCK** | Stand with 2× Pmod™ headers (16 GPIOs), USB-A host port, USB-C 5 V power |
| **ESP32-S3-BOX-3-SENSOR** | Temp/Hum sensor, IR emitter/receiver, LD2410 radar, 18650 battery slot, MicroSD slot |
| **ESP32-S3-BOX-3-BRACKET** | Mounting adapter with 2× Pmod™ headers for wall/device mounting |
| **ESP32-S3-BOX-3-BREAD** | Breadboard adapter — exposes 16 GPIOs on 2.54 mm pitch headers |

### Strapping Pins (ESP32-S3)

The ESP32-S3 has four strapping pins that affect boot behavior. All are used by the S3-BOX-3 hardware and require `ignore_strapping_warning: true` in ESPHome:

| GPIO | Strapping function | Usage in this config |
|------|-------------------|---------------------|
| GPIO0 | Boot mode (BOOT button) | Physical button (INPUT_PULLUP, inverted) |
| GPIO3 | JTAG control | GT911 touch interrupt |
| GPIO45 | ROM message output | I2S LRCK |
| GPIO46 | ROM message enable | Speaker PA enable |

---

## Files

| File | Purpose |
|------|---------|
| `esp32s3box3.yaml` | Main ESPHome configuration (~4 400 lines) |
| `device_config.yaml` | **All user-configurable settings** — edit this first |
| `chakra_component.h` | Self-contained C++ FFT analyser (1 024-pt Cooley-Tukey) |
| `secrets.yaml` | Wi-Fi credentials — **never commit real values** |
| `secrets.example.yaml` | CI placeholder — checked in |
| `tools/pin_check.py` | GPIO conflict + strapping-pin validator |
| `Makefile` | All dev commands |

---

## Chakra Analyser Feature

A dedicated **Chakra** page (reachable from the Settings nav) replaces the Voice Assist pipeline with a continuous FFT frequency analyser.

### How it works

1. Toggle the **Chakra Mode** switch on the Chakra page.
2. The mic starts capturing audio; a 1 024-point FFT runs on every buffer (~16 kHz sample rate → 15.6 Hz/bin resolution).
3. The dominant bin is mapped to one of 7 chakras:

| # | Chakra | Frequency band | Colour |
|---|--------|---------------|--------|
| 0 | Root | 32 – 64 Hz | 🔴 `#FF0000` |
| 1 | Sacral | 64 – 128 Hz | 🟠 `#FF7F00` |
| 2 | Solar Plexus | 128 – 256 Hz | 🟡 `#FFFF00` |
| 3 | Heart | 256 – 512 Hz | 🟢 `#00CC00` |
| 4 | Throat | 512 – 1 024 Hz | 🔵 `#0000FF` |
| 5 | Third Eye | 1 024 – 2 048 Hz | 🟣 `#4B0082` |
| 6 | Crown | 2 048 – 4 096 Hz | 🟤 `#EE82EE` |

4. The active chakra name + hex colour are pushed to HA as `text_sensor` entities (`chakra_active_name`, `chakra_active_color`).
5. The `chakra_send_to_ha` script calls `light.turn_on` on your configured HA light entity with the matching RGB values.

### Sensitivity tuning

The Chakra page has **+/−** touch buttons to adjust the detection threshold live. The default is `0.10` (10 % of peak bin energy). Increase it if background noise triggers false positives; decrease it for quieter bowls.

---

## Setup

### 1. Fill in secrets

Edit `secrets.yaml`:

```yaml
wifi_ssid: "YourNetworkName"
wifi_password: "YourPassword"
```

### 2. Set your HA light entity

In `device_config.yaml`, update the substitutions:

```yaml
substitutions:
  chakra_light_entity: "your_chakra_light"   # without the "light." prefix
  aws_relay_url: "https://your-tunnel.trycloudflare.com"  # optional: for AWS mode
```

### 3. Compile

```bash
make validate   # quick schema check
make flash      # compile + flash via USB-C (first time)
make ota        # compile + flash via Wi-Fi (subsequent)
```

---

## Home Assistant entities

After adoption the device exposes:

| Entity | Type | Description |
|--------|------|-------------|
| `text_sensor.chakra_active_name` | Text sensor | Active chakra name (e.g. `Heart`) |
| `text_sensor.chakra_active_color` | Text sensor | Active colour hex (e.g. `#00CC00`) |
| `switch.chakra_mode` | Switch | Enable / disable analyser mode |
| `light.box3_color` *(via script)* | Light | Set automatically when a chakra is detected |

---

## Build environment

- ESPHome 2026.2.0
- Framework: `esp-idf` (ESP-IDF 5.5.2)
- PlatformIO build — all remote assets (fonts, images, sounds) fetched from GitHub raw URLs at compile time; no local clone of the upstream repo required.

---

## Resources

- [BigBobbas upstream repo](https://github.com/BigBobbas/ESP32-S3-Box3-Custom-ESPHome)
- [ESPHome Documentation](https://esphome.io/)
- [Home Assistant ESPHome Integration](https://www.home-assistant.io/integrations/esphome/)
- [Espressif ESP32-S3-BOX-3 Hardware Overview](https://github.com/espressif/esp-box/blob/master/docs/hardware_overview/esp32_s3_box_3/hardware_overview_for_box_3.md)
- [Espressif ESP-BOX GitHub (firmware, schematics, CAD)](https://github.com/espressif/esp-box)
- [ESP32-S3-BOX-3 Schematic & PCB source](https://github.com/espressif/esp-box/tree/master/hardware/PCB_ESP32-S3-BOX-3_V1.0)
- [ESP32-S3 Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf)
- [GT911 Touch Controller Datasheet](https://www.goodix.com/en/product/touch)
- [ES7210 4-ch ADC Datasheet](http://www.everest-semi.com/pdf/ES7210%20PB.pdf)
- [ES8311 Audio Codec Datasheet](http://www.everest-semi.com/pdf/ES8311%20PB.pdf)
