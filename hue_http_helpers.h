#pragma once

#include <string>
#include <cstring>

#include "esp_err.h"
#include "esp_http_client.h"

namespace hue_http {

struct Response {
  esp_err_t err{ESP_FAIL};
  int status{-1};
  std::string body;
};

inline Response request(const char *url, esp_http_client_method_t method,
                        const char *payload = nullptr, int timeout_ms = 5000) {
  Response response;
  if (url == nullptr) {
    response.err = ESP_ERR_INVALID_ARG;
    return response;
  }

  esp_http_client_config_t cfg = {};
  cfg.url = url;
  cfg.method = method;
  cfg.timeout_ms = timeout_ms;
  cfg.buffer_size = 2048;
  cfg.buffer_size_tx = 512;

  esp_http_client_handle_t client = esp_http_client_init(&cfg);
  if (client == nullptr) {
    response.err = ESP_FAIL;
    return response;
  }

  const int write_len = payload == nullptr ? 0 : static_cast<int>(std::strlen(payload));
  if (payload != nullptr) {
    esp_http_client_set_header(client, "Content-Type", "application/json");
  }

  response.err = esp_http_client_open(client, write_len);
  if (response.err == ESP_OK && payload != nullptr && write_len > 0) {
    const int written = esp_http_client_write(client, payload, write_len);
    if (written < write_len) {
      response.err = ESP_FAIL;
    }
  }

  if (response.err == ESP_OK) {
    const int headers_ret = esp_http_client_fetch_headers(client);
    response.status = esp_http_client_get_status_code(client);

    if (headers_ret < 0 && response.status <= 0) {
      response.err = ESP_FAIL;
    } else {
      char buffer[256];
      int read_len = 0;
      while ((read_len = esp_http_client_read(client, buffer, sizeof(buffer))) > 0) {
        response.body.append(buffer, read_len);
      }
      if (read_len < 0) {
        response.err = ESP_FAIL;
      }
    }
  }

  esp_http_client_close(client);
  esp_http_client_cleanup(client);
  return response;
}

inline Response request(const char *url, esp_http_client_method_t method,
                        const std::string &payload, int timeout_ms = 5000) {
  return request(url, method, payload.c_str(), timeout_ms);
}

inline bool is_success_status(int status) { return status >= 200 && status < 300; }

inline bool body_contains_error(const std::string &body) {
  return body.find("\"error\"") != std::string::npos;
}

}  // namespace hue_http
