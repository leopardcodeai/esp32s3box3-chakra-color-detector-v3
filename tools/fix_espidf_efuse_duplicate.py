"""
Remove duplicate esp_efuse_fields.c from ESP-IDF 5.5.x build cache.
ESP-IDF 5.5 added src/esp_efuse_fields.c but the chip-specific copy
(e.g. esp32s3/esp_efuse_fields.c) still exists, causing PlatformIO to
fail with "Multiple ways to build the same target".
Run before every compile via: make fix-espidf-efuse
"""
import os
import glob

build_root = os.path.join(os.path.dirname(__file__), "..", ".esphome", "build")
pattern = os.path.join(
    build_root, "**", "framework-espidf",
    "components", "efuse", "src", "esp_efuse_fields.c",
)
for path in glob.glob(pattern, recursive=True):
    os.remove(path)
    print(f"[fix-espidf-efuse] Removed duplicate: {path}")
