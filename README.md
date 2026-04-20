# ESP32-S3-BOX-3 Custom ESPHome — Chakra Analyser Edition

ESPHome firmware for the **Espressif ESP32-S3-BOX-3** with Sensor Dock, built on top of the [BigBobbas custom config](https://github.com/BigBobbas/ESP32-S3-Box3-Custom-ESPHome). Extends the original with a **Chakra Frequency Analyser** page that listens to the built-in MEMS microphones, detects dominant singing-bowl frequencies via FFT, maps them to the 7 chakras, and in the current `esp32s3box3_v4.yaml` flow drives Hue lights directly through the local Hue Bridge.

## Current v4 Light-Control Pipeline

`esp32s3box3_v4.yaml` is the current direct-light-control configuration. In this mode the light path does **not** depend on the Home Assistant light API.

```
Mic -> FFT -> chakra_index -> chakra_send_to_ha
                              |
                              +-> RGB from ChakraAnalyser::get_info()
                              |
                              +-> RGB -> HSV conversion
                              |
                              +-> light_set_color
                              |
                              +-> light_send_to_all
                              |
                              +-> HTTP PUT http://<bridge>/api/<key>/lights/<id>/state
                              |
                              +-> Hue lights 5,6,8,9,18,20,21
```

Notes:

- The current lighting path is `Chakra -> ESPHome -> Hue Bridge -> Hue lights`.
- `chakra_update_ha_sensor` still posts a sensor update to Home Assistant if the host is reachable, but that sensor post is **not** the light-control path.
- `light_control_mode: hue` must be active in `device_config.yaml`.
- `hue_light_entity` must resolve to a comma-separated list of numeric Hue light IDs.

### v3.1 — Raw Audio Streaming + Multi-VM Pipeline

The device streams **raw PCM audio** (16 kHz, 16-bit, mono) to a central relay VM. The relay runs its own FFT + chakra detection (identical algorithm to the on-device C++ version) and broadcasts results via **Server-Sent Events (SSE)**. Any number of VMs can subscribe — each running a lightweight listener that controls its local HA light in real time.

```
ESP32 Mic → Raw PCM
                 │
    ┌────────────┴────────────┐
    │ ☁ OFF                   │ ☁ ON
    ▼                         ▼
 ESP32 FFT → HA          ESP32 → Relay → FFT → SSE broadcast
 (local, instant)                   │        │
                                    │    ┌───┴──────────┐
                                    │    │ VM-1 (HA #1) │ ← chakra_listener.py
                                    │    │ VM-2 (HA #2) │ ← chakra_listener.py
                                    │    │ VM-N (HA #N) │ ← ...
                                    │    └──────────────┘
                                    ▼
                              AWS Bedrock
                              (parallel)
```

---

## Audio Streaming Pipeline (☁ ON mode)

When the cloud icon is active, the ESP32 streams raw audio to the relay hub:

```
┌─────────────────────────────────────────────────────────────┐
│                    ESP32-S3-BOX-3                            │
│                                                             │
│  ┌─────────┐    ┌────────────────────────────────────┐     │
│  │ ES7210  │───▶│ aws_audio_streamer.h               │     │
│  │ MEMS Mic│    │ Double-buffered PCM → HTTP POST    │     │
│  │ 16kHz   │    │ 4096 samples/chunk (~256 ms)       │     │
│  └─────────┘    │ FreeRTOS background task (core 0)  │     │
│       ▲         └────────────────┬───────────────────┘     │
│       │ (parallel)               │ POST /aws/audio         │
│  ┌────┴─────────┐                │ Content-Type:           │
│  │ Voice Assist │                │  application/octet-     │
│  │ (wake word   │                │  stream (raw int16 LE)  │
│  │  always on)  │                │                         │
│  └──────────────┘                │                         │
└──────────────────────────────────┼─────────────────────────┘
                                   │
                                   ▼
                      ┌────────────────────────┐
                      │  Cloudflare Tunnel     │
                      │  (trycloudflare.com)   │
                      └────────────┬───────────┘
                                   │
                                   ▼
                      ┌────────────────────────────────────┐
                      │  Audio FFT Relay (port 8765)       │
                      │  audio_fft_relay.py                │
                      │                                    │
                      │  POST /aws/audio    ← raw PCM in   │
                      │  POST /aws/chakra   ← legacy JSON  │
                      │  GET  /aws/audio/live → SSE chakra │
                      │  GET  /aws/audio/raw  → SSE PCM    │
                      │  GET  /health         → status     │
                      │                                    │
                      │  numpy FFT (512-pt Hann + HPS)     │
                      │  Identical to on-device algorithm   │
                      └──────┬─────────────┬───────────────┘
                             │             │
                    ┌────────▼──┐    ┌─────▼───────────────┐
                    │ Bedrock   │    │  SSE Broadcast      │
                    │ (boto3)   │    │                     │
                    │ ChakraMas │    │  VM-1: listener.py  │
                    │ ter agent │    │  VM-2: listener.py  │
                    │ → Lambda  │    │  VM-N: ...          │
                    │ → CW met. │    │                     │
                    └───────────┘    │  Each subscribes to │
                                    │  /aws/audio/live    │
                                    │  → HA light.turn_on │
                                    └─────────────────────┘
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/aws/audio` | Raw PCM (int16 LE, 16 kHz) from ESP32 |
| `POST` | `/aws/chakra` | Legacy JSON `{frequency, chakra_index}` |
| `GET` | `/aws/audio/live` | SSE stream — chakra detections (JSON) |
| `GET` | `/aws/audio/raw` | SSE stream — raw PCM as base64 (for own FFT) |
| `GET` | `/health` | Status + subscriber count |

### SSE Event Format (`/aws/audio/live`)

```json
{
  "chakra_index": 3,
  "chakra_name": "Heart",
  "frequency": 343.2,
  "signal_db": -22.5,
  "color": "#00CC00",
  "r": 0, "g": 204, "b": 0,
  "timestamp": 1741783200.5
}
```

### CloudWatch Metrics

The Lambda emits custom metrics under namespace **`ChakraAnalyser`**, dimensioned by chakra name:

| Metric | Description |
|--------|-------------|
| `ChakraActivation` | Count of detections per chakra |
| `FrequencyDetected` | Detected frequency in Hz |
| `ColorR` / `ColorG` / `ColorB` | RGB values sent to the light |

View live in AWS Console → CloudWatch → Metrics → ChakraAnalyser.

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
| `esp32s3box3.yaml` | Legacy main ESPHome configuration |
| `esp32s3box3_v4.yaml` | Current direct Hue Bridge configuration with pipeline diagnostics |
| `device_config.yaml` | **All user-configurable settings** — edit this first |
| `chakra_component.h` | Self-contained C++ FFT analyser (512-pt Cooley-Tukey) |
| `hue_http_helpers.h` | Shared ESP-IDF HTTP helper that captures Hue response bodies without post-`perform()` read errors |
| `aws_audio_streamer.h` | Double-buffered PCM streamer — FreeRTOS background HTTP POST |
| `vm_scripts/audio_fft_relay.py` | **Relay hub** — receives PCM, runs FFT, SSE broadcast + Bedrock |
| `vm_scripts/chakra_listener.py` | **HA listener** — subscribes to SSE, controls local HA light |
| `secrets.yaml` | Wi-Fi credentials — **never commit real values** |
| `secrets.example.yaml` | CI placeholder — checked in |
| `tools/pin_check.py` | GPIO conflict + strapping-pin validator |
| `tools/substitution_check.py` | Guard against self-referential substitutions such as `foo: ${foo}` |
| `tools/hue_bridge_test.py` | Inspect and validate configured Hue light targets from the host |
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

4. The active chakra name + hex colour are published locally as `text_sensor` entities (`chakra_active_name`, `chakra_active_color`).
5. In `light_control_mode: hue`, `chakra_send_to_ha` converts the chakra RGB colour to Hue HSV and calls the Hue Bridge directly for each configured light ID.
6. In `light_control_mode: HA API`, the fallback path still uses `light.turn_on` on the configured Home Assistant entity.

### Sensitivity tuning

The Chakra page has **+/−** touch buttons to adjust the detection threshold live. The default is `0.10` (10 % of peak bin energy). Increase it if background noise triggers false positives; decrease it for quieter bowls.

---

## VM Deployment

### Relay Hub (central VM)

```bash
pip install numpy boto3
python3 vm_scripts/audio_fft_relay.py --port 8765
# Optional: --no-bedrock to disable AWS agent invocation
```

### Listener (any VM with Home Assistant)

```bash
pip install requests sseclient-py
python3 vm_scripts/chakra_listener.py \
  --relay-url http://<RELAY_IP>:8765 \
  --ha-token YOUR_LONG_LIVED_TOKEN \
  --light light.living_room
```

Or via environment variables:

```bash
export RELAY_URL=http://192.168.64.9:8765
export HA_TOKEN=your_token_here
export LIGHT_ENTITY=light.living_room
python3 vm_scripts/chakra_listener.py
```

Both scripts include systemd unit examples in their file headers.

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
  light_control_mode: hue
  hue_light_entity: "5,6,8,9,18,20,21"
```

### 3. Compile

```bash
make validate
make check
make flash
make ota
```

## Pipeline Test Procedure

Use this procedure to isolate failures in the exact order they can occur.

### 1. Static config guards

```bash
make subst-check CONFIG=esp32s3box3_v4.yaml
make validate CONFIG=esp32s3box3_v4.yaml
```

Expected result:

- no self-referential substitutions
- valid ESPHome config

### 2. Host -> Hue Bridge target check

```bash
make hue-bridge-test
```

Expected result:

- all configured light IDs exist
- all are `reachable=true`
- all expose color control (`has_gamut=True`)

Optional write/readback test from the host:

```bash
make hue-write-test
```

Notes:

- A `write-test` can warn about a hue readback mismatch even when the write succeeded. Many Hue lamps remap requested hue values to their own reachable gamut.
- The important pass criteria are: HTTP `200`, `reachable=True`, `colormode=hs`, brightness near target, saturation near target.

### 3. Device -> Hue Bridge direct payload test

After flashing `esp32s3box3_v4.yaml`, use these diagnostic buttons on the device:

- `Test Hue Connection`
- `Inspect Hue Targets`
- `Run Hue Pipeline Self-Test`
- `Test Hue Payload Sweep`

Expected logs:

- `hue_config: Configured Hue targets: 5,6,8,9,18,20,21`
- `test_hue: Target light: 5`
- `hue_inspect: Light <id> status 200: ...`
- `hue_test: PASS light <id> -> ...`
- `hue_response: Light <id>: [{"success":...}]`

If you see `Hue target IDs are unresolved: ${hue_light_entity}`, the build is invalid and must not be deployed.

### 3a. Full regression run

This combines the host bridge verification with the on-device self-test button:

```bash
make hue-full-test
```

This is the fastest reusable regression check after any YAML, substitution, or Hue transport change.

### 4. Chakra -> Hue end-to-end test

Use the device button `Test Chakra Hue Pipeline`.

What it does:

- injects chakra indices `0..6`
- runs the same `chakra_send_to_ha` script used by live FFT detections
- verifies state via `light_get_state`

Expected logs:

- `pipeline_test: Chakra pipeline step <n> -> <name>`
- `chakra_send: Condition check: light_control_mode == 'hue' ? TRUE`
- `light_color: Setting color - H:... S:... B:...`
- `hue_send: Light <id> - URL: http://<bridge>/api/<key>/lights/<id>/state`

### 5. Live microphone / FFT verification

Finally enable `Chakra Mode`, produce a known tone, and verify:

- `chakra_send` appears only when a new chakra is detected
- `hue_send` follows immediately after `chakra_send`
- the room lights change

If step 2 passes but step 3 fails, the issue is inside the ESPHome Hue transport path.
If step 3 passes but step 5 fails, the issue is in the FFT/chakra trigger path.

## Known Failure Signatures

- `Hue target IDs are unresolved: ${hue_light_entity}`
  The firmware still contains an unresolved substitution. Run `make subst-check CONFIG=esp32s3box3_v4.yaml` and reflash.
- `light_control_mode` is not `hue`
  The device is on the wrong branch of the pipeline and will not use the direct Hue Bridge transport.
- Host tests pass, but `Test Hue Connection` fails on-device
  The problem is inside the ESP-side HTTP path, Wi-Fi path, or embedded request formatting.
- `Test Hue Connection` and `Run Hue Pipeline Self-Test` pass, but live Chakra mode does not change lights
  The issue is no longer the Hue bridge. Focus on FFT detection, debounce, `chakra_index`, and whether `chakra_send_to_ha` is firing.
- `write-test` warns that `hue` readback differs from the requested hue
  This is normal for some lamps and does not automatically indicate a failure as long as the bridge accepted the request and the light entered `hs` mode.

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

- ESPHome 2026.3.0
- Framework: `esp-idf` (ESP-IDF 5.5.3)
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
