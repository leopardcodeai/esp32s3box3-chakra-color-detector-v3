# esp32s3box3-chakra-color-detector-v3

ESPHome firmware project for the **ESP32-S3-BOX-3**. The device runs a Chakra Frequency Analyser that maps singing-bowl frequencies (via FFT) to the 7 chakras and integrates deeply with Home Assistant for media, lights, and timers.

---

## Key Files

| File | Purpose |
|------|---------|
| `esp32s3box3.yaml` | Main ESPHome config (~4 300 lines) — do not add user-facing values here |
| `device_config.yaml` | **All user-configurable settings** — edit this first |
| `chakra_component.h` | Self-contained C++ FFT analyser (1 024-pt Cooley-Tukey) |
| `secrets.yaml` | WiFi credentials — never commit real values |
| `secrets.example.yaml` | CI placeholder — checked in |
| `tools/pin_check.py` | GPIO conflict + strapping-pin validator |
| `Makefile` | All dev commands |

## Commands

```bash
make validate        # Fast YAML schema check (no device needed) — run after every change
make check           # yaml-check + secrets-check + pins + validate
make pins            # GPIO conflict + strapping pin check (wired into flash/ota)
make flash           # Compile + flash via USB-C  (runs pins first)
make ota             # Compile + flash via Wi-Fi   (runs pins first)
make logs            # Stream device logs

make feature NAME=x  # Create feat/x branch
make fix NAME=x      # Create fix/x branch
make pr              # Push branch + open draft PR
make merge           # Squash-merge current branch PR → main (auto-tags release)
```

**Validation command** (for CI / scripted checks):
```bash
esphome config esp32s3box3.yaml
```

## PR / Release Workflow

All new work goes through the PR workflow — never commit directly to main.

1. `make feature NAME=my-feature` → creates `feat/my-feature` branch
2. Make changes, commit with Conventional Commit prefix (`feat:`, `fix:`, `chore:`, `docs:`)
3. `make pr` → opens draft PR, triggers CI validation
4. Wait for CI green, then `make merge`
5. `release.yml` auto-tags: `feat:` → minor bump, `fix:` → patch bump, `feat!:` → major bump

## Customising the Device

**Edit `device_config.yaml` only** — never touch `esp32s3box3.yaml` for user settings.

```yaml
home_assistant_host: !secret home_assistant_host
external_media_player: music_assistant_airplay   # → media_player.<this>
chakra_light_entity: living_room                  # → light.<this>  (no 'light.' prefix)
ha_timer_entity: timer.home_assistant_timer       # full entity_id
default_brightness: "100"
display_bg_hex: 'ffffff'    # white theme; dark: '032341'
display_text_hex: '000000'  # dark text; dark theme: 'ffffff'
```

## Architecture Notes

- **Substitutions precedence**: `device_config.yaml` values are authoritative. The main file (`esp32s3box3.yaml`) only defines internal substitutions (`font_glyphs`).
- **Theme colors**: `id(display_bg)` drives all page fills. `id(black)` uses `${display_text_hex}` so switching theme recolors all text automatically.
- **HA Timer**: `ha_timer_status` and `ha_timer_remaining` text_sensors subscribe to `${ha_timer_entity}`. Touch buttons on `time_remaining_page` call `timer.start/pause/cancel`.
- **VA timers** (voice assistant timers) are separate from HA timer entities — both are shown on `time_remaining_page` (voice timer on top, HA timer below).
- **FFT**: `chakra_component.h` must stay self-contained — no external DSP libraries.
- **ESPHome lambdas**: use `id(component)->method()` syntax inside lambdas, not YAML action names.
- **YAML tags**: `!secret` and `!lambda` cause `yaml.safe_load` to fail. The yaml-check target uses `add_multi_constructor('', ...)` to handle this.

## GPIO — All Pins Are Taken

Every GPIO on the S3-BOX-3 is assigned. Run `make pins` before any flash. Strapping pins (GPIO0, GPIO3, GPIO45, GPIO46) require `ignore_strapping_warning: true` in config.

| GPIO | Signal | Notes |
|------|--------|-------|
| GPIO0 | Boot button | Strapping pin |
| GPIO3 | Touch INT (GT911) | Strapping pin |
| GPIO45 | I2S LRCK | Strapping pin |
| GPIO46 | Speaker enable | Strapping pin |
| GPIO47 | LCD Backlight | LEDC PWM |
| GPIO19/20 | USB D+/D− | Reserved — do not use |

## Secrets

`secrets.yaml` is gitignored. For local dev, copy `secrets.example.yaml` → `secrets.yaml` and fill in real values. CI uses `secrets.example.yaml` directly.

## CI

`.github/workflows/validate.yml` — runs `esphome config esp32s3box3.yaml` on every PR using the `ghcr.io/esphome/esphome:stable` container.
