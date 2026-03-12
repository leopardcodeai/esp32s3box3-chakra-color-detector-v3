## Overview

You are working on an ESPHome firmware project for the ESP32-S3-BOX-3.
Project root: PROJECT_ROOT

## Project Context

- Main config: `esp32s3box3.yaml` (~4300 lines, ESP-IDF framework)
- Custom FFT header: `chakra_component.h` (1024-pt Cooley-Tukey, self-contained)
- Secrets: `secrets.yaml` (WiFi credentials — do NOT commit real values)
- Hardware: ESP32-S3-BOX-3, ES7210 mic, ES8311 DAC, 320×240 IPS display, capacitive touch

## Build Command

Validate only (no device needed):
```
cd PROJECT_ROOT && esphome config esp32s3box3.yaml 2>&1 | head -50
```

## Before Starting

Check @.agent/logs/LOG.md for previous work (last 5 entries).

## Task Flow

Tasks are listed in @.agent/tasks.json

1. Pick highest-priority task with `passes: false`
2. Read full spec in `notes` field of the task
3. Make minimal changes to `esp32s3box3.yaml` and/or `chakra_component.h`
4. Validate: run `esphome config esp32s3box3.yaml` — must complete without errors
5. If validation passes, set `passes: true` in `tasks.json`
6. Log entry → `.agent/logs/LOG.md` (date, task ID, what changed)
7. Commit using Conventional Commit format

## Rules

- **CRITICAL**: Only work on **ONE task per invocation**. After committing, output `<promise>TASK-{ID}:DONE</promise>` and **STOP immediately**.
- **CRITICAL**: When **ALL** tasks pass → output `<promise>COMPLETE</promise>` and nothing else.
- Never hardcode WiFi credentials or API keys.
- Never modify `secrets.yaml`.
- Keep `chakra_component.h` self-contained (no external DSP libraries).
- ESPHome quirks: use `id(component)->method()` in lambdas, not YAML action names.
- When stuck → `<promise>BLOCKED:description</promise>`
