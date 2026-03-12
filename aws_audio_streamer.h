// ═══════════════════════════════════════════════════════════════════════════
//  AWS Audio Streamer — streams raw PCM from ESP32 mic to relay via HTTP
//
//  Double-buffered: on_data fills write_buf; FreeRTOS task POSTs send_buf.
//  4096 samples per chunk ≈ 256 ms at 16 kHz / 16-bit mono.
// ═══════════════════════════════════════════════════════════════════════════
#pragma once

#include <cstring>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "esp_http_client.h"
#include "esp_crt_bundle.h"
#include "esp_log.h"

static const char* AWS_AUDIO_TAG = "aws_audio";

class AwsAudioStreamer {
 public:
    static constexpr size_t CHUNK_SAMPLES = 4096;   // ~256 ms at 16 kHz

    // Call once from on_boot
    static void init(const char* url) {
        strncpy(_url, url, sizeof(_url) - 1);
        _write_buf = _buf_a;
        _send_buf  = _buf_b;
        _write_pos = 0;
        _send_ready = false;
        _enabled    = false;
        _mutex = xSemaphoreCreateMutex();
        xTaskCreatePinnedToCore(_send_task, "aws_pcm", 8192,
                                nullptr, 3, &_task_handle, 0);
        ESP_LOGI(AWS_AUDIO_TAG, "Streamer ready → %s", _url);
    }

    static void set_enabled(bool en) {
        _enabled = en;
        if (!en && _mutex) {
            if (xSemaphoreTake(_mutex, pdMS_TO_TICKS(50)) == pdTRUE) {
                _write_pos = 0;
                xSemaphoreGive(_mutex);
            }
        }
        ESP_LOGI(AWS_AUDIO_TAG, "Streaming %s", en ? "ON" : "OFF");
    }

    static bool is_enabled() { return _enabled; }

    // Called from on_data lambda — copies into write buffer, swaps when full
    static void push_samples(const int16_t* samples, size_t count) {
        if (!_enabled || !_mutex) return;

        const int16_t* src = samples;
        size_t remaining = count;

        while (remaining > 0) {
            size_t space   = CHUNK_SAMPLES - _write_pos;
            size_t to_copy = (remaining < space) ? remaining : space;
            memcpy(&_write_buf[_write_pos], src, to_copy * sizeof(int16_t));
            _write_pos += to_copy;
            src        += to_copy;
            remaining  -= to_copy;

            if (_write_pos >= CHUNK_SAMPLES) {
                if (xSemaphoreTake(_mutex, 0) == pdTRUE) {
                    if (!_send_ready) {
                        int16_t* tmp = _write_buf;
                        _write_buf   = _send_buf;
                        _send_buf    = tmp;
                        _send_ready  = true;
                        xSemaphoreGive(_mutex);
                        xTaskNotifyGive(_task_handle);
                    } else {
                        // Previous chunk still in flight — drop this one
                        xSemaphoreGive(_mutex);
                    }
                }
                _write_pos = 0;
            }
        }
    }

 private:
    static int16_t  _buf_a[CHUNK_SAMPLES];
    static int16_t  _buf_b[CHUNK_SAMPLES];
    static int16_t* _write_buf;
    static int16_t* _send_buf;
    static size_t   _write_pos;
    static bool     _send_ready;
    static bool     _enabled;
    static char     _url[256];
    static SemaphoreHandle_t _mutex;
    static TaskHandle_t      _task_handle;

    static void _send_task(void* /*param*/) {
        while (true) {
            ulTaskNotifyTake(pdTRUE, portMAX_DELAY);

            int16_t* data = nullptr;
            if (xSemaphoreTake(_mutex, pdMS_TO_TICKS(200)) == pdTRUE) {
                if (_send_ready) {
                    data = _send_buf;
                    _send_ready = false;
                }
                xSemaphoreGive(_mutex);
            }
            if (!data) continue;

            esp_http_client_config_t cfg = {};
            cfg.url        = _url;
            cfg.method     = HTTP_METHOD_POST;
            cfg.timeout_ms = 5000;
            cfg.crt_bundle_attach = esp_crt_bundle_attach;
            cfg.skip_cert_common_name_check = true;

            esp_http_client_handle_t client = esp_http_client_init(&cfg);
            if (!client) { ESP_LOGW(AWS_AUDIO_TAG, "client init failed"); continue; }

            esp_http_client_set_header(client, "Content-Type",  "application/octet-stream");
            esp_http_client_set_header(client, "X-Sample-Rate", "16000");
            esp_http_client_set_header(client, "X-Bits",        "16");
            esp_http_client_set_header(client, "X-Channels",    "1");

            esp_http_client_set_post_field(
                client, reinterpret_cast<const char*>(data),
                CHUNK_SAMPLES * sizeof(int16_t));

            esp_err_t err = esp_http_client_perform(client);
            if (err != ESP_OK) {
                ESP_LOGW(AWS_AUDIO_TAG, "POST failed: %s", esp_err_to_name(err));
            }
            esp_http_client_cleanup(client);
        }
    }
};

// ── static storage ──────────────────────────────────────────────────────────
int16_t  AwsAudioStreamer::_buf_a[AwsAudioStreamer::CHUNK_SAMPLES] = {};
int16_t  AwsAudioStreamer::_buf_b[AwsAudioStreamer::CHUNK_SAMPLES] = {};
int16_t* AwsAudioStreamer::_write_buf  = nullptr;
int16_t* AwsAudioStreamer::_send_buf   = nullptr;
size_t   AwsAudioStreamer::_write_pos  = 0;
bool     AwsAudioStreamer::_send_ready = false;
bool     AwsAudioStreamer::_enabled    = false;
char     AwsAudioStreamer::_url[256]   = {};
SemaphoreHandle_t AwsAudioStreamer::_mutex       = nullptr;
TaskHandle_t      AwsAudioStreamer::_task_handle  = nullptr;
