#!/usr/bin/env python3
"""
Audio FFT Relay — Hub for ESP32-S3-BOX-3 Chakra Audio Pipeline

Receives raw 16-bit PCM audio from ESP32, runs FFT + chakra detection,
broadcasts results via Server-Sent Events (SSE) so any number of VMs
can subscribe in real time.

Endpoints:
    POST /aws/audio       ← ESP32 sends raw PCM (application/octet-stream)
    POST /aws/chakra      ← ESP32 sends pre-computed {frequency, chakra_index}
    GET  /aws/audio/live  → SSE stream of chakra detections (for any subscriber)
    GET  /aws/audio/raw   → SSE stream of raw PCM base64 chunks (for own FFT)
    GET  /health          → {"status": "ok", "subscribers": N}

Deploy:
    pip install numpy boto3
    python3 audio_fft_relay.py --port 8765

The ESP32 sends to this via Cloudflare tunnel or direct IP.
Other VMs subscribe to /aws/audio/live for real-time chakra results.
"""

import argparse
import base64
import json
import math
import struct
import threading
import time
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO

import numpy as np

# ═══════════════════════════════════════════════════════════════════
#  Chakra table — must match chakra_component.h
# ═══════════════════════════════════════════════════════════════════
CHAKRA_TABLE = [
    {"name": "Root",         "hex": "#FF0000", "r": 0xFF, "g": 0x00, "b": 0x00,
     "freq_lo": 242.0, "freq_hi": 272.0},
    {"name": "Sacral",       "hex": "#FF7F00", "r": 0xFF, "g": 0x7F, "b": 0x00,
     "freq_lo": 272.0, "freq_hi": 305.0},
    {"name": "Solar Plexus", "hex": "#FFFF00", "r": 0xFF, "g": 0xFF, "b": 0x00,
     "freq_lo": 305.0, "freq_hi": 343.0},
    {"name": "Heart",        "hex": "#00CC00", "r": 0x00, "g": 0xCC, "b": 0x00,
     "freq_lo": 323.0, "freq_hi": 363.0},
    {"name": "Throat",       "hex": "#0000FF", "r": 0x00, "g": 0x00, "b": 0xFF,
     "freq_lo": 363.0, "freq_hi": 407.0},
    {"name": "Third Eye",    "hex": "#4B0082", "r": 0x4B, "g": 0x00, "b": 0x82,
     "freq_lo": 407.0, "freq_hi": 457.0},
    {"name": "Crown",        "hex": "#EE82EE", "r": 0xEE, "g": 0x82, "b": 0xEE,
     "freq_lo": 457.0, "freq_hi": 514.0},
]

NOTE_TO_CHAKRA = [0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 6, 6]

# ═══════════════════════════════════════════════════════════════════
#  FFT Analyser — Python port of chakra_component.h
# ═══════════════════════════════════════════════════════════════════
FFT_N = 512
SAMPLE_RATE = 16000
FREQ_RES = SAMPLE_RATE / FFT_N   # 31.25 Hz/bin
THRESHOLD_DB = -45.0


class ChakraFFTAnalyser:
    """Accumulates PCM int16 samples, runs FFT, detects chakra."""

    def __init__(self):
        self.accum = np.array([], dtype=np.int16)
        self.last_result = None

    def push_samples(self, pcm_bytes: bytes) -> list[dict]:
        """Push raw PCM bytes (int16 LE). Returns list of detection dicts."""
        samples = np.frombuffer(pcm_bytes, dtype=np.int16)
        self.accum = np.append(self.accum, samples)
        results = []

        while len(self.accum) >= FFT_N:
            frame = self.accum[:FFT_N].astype(np.float32) / 32768.0
            self.accum = self.accum[FFT_N:]

            # RMS + dB
            rms = np.sqrt(np.mean(frame ** 2))
            signal_db = 20.0 * np.log10(rms + 1e-9)
            if signal_db < THRESHOLD_DB:
                continue

            # Hann window + FFT
            window = 0.5 * (1.0 - np.cos(2.0 * np.pi * np.arange(FFT_N) / (FFT_N - 1)))
            windowed = frame * window
            spectrum = np.fft.rfft(windowed)
            mag = np.abs(spectrum)

            # Harmonic product spectrum (60–1000 Hz)
            k_lo, k_hi = 2, 32
            best_bin, best_score = k_lo, 0.0
            half = FFT_N // 2
            for k in range(k_lo, k_hi + 1):
                score = mag[k]
                if 2 * k <= half:
                    score += 0.50 * mag[2 * k]
                if 3 * k <= half:
                    score += 0.33 * mag[3 * k]
                if 4 * k <= half:
                    score += 0.25 * mag[4 * k]
                if score > best_score:
                    best_score = score
                    best_bin = k

            # Parabolic interpolation
            fine_bin = float(best_bin)
            if k_lo < best_bin < k_hi:
                y0, y1, y2 = mag[best_bin - 1], mag[best_bin], mag[best_bin + 1]
                denom = y0 - 2.0 * y1 + y2
                if abs(denom) > 1e-12:
                    fine_bin = best_bin + 0.5 * (y0 - y2) / denom
            peak_freq = fine_bin * FREQ_RES

            # Semitone-based chakra detection (432 Hz reference, octave-independent)
            chakra_idx = -1
            if peak_freq >= 60.0:
                midi_note = 69.0 + 12.0 * math.log2(peak_freq / 432.0)
                semitone = round(midi_note) % 12
                if semitone < 0:
                    semitone += 12
                chakra_idx = NOTE_TO_CHAKRA[semitone]

            if chakra_idx >= 0:
                result = {
                    "chakra_index": chakra_idx,
                    "chakra_name": CHAKRA_TABLE[chakra_idx]["name"],
                    "frequency": round(peak_freq, 1),
                    "signal_db": round(signal_db, 1),
                    "color": CHAKRA_TABLE[chakra_idx]["hex"],
                    "r": CHAKRA_TABLE[chakra_idx]["r"],
                    "g": CHAKRA_TABLE[chakra_idx]["g"],
                    "b": CHAKRA_TABLE[chakra_idx]["b"],
                    "timestamp": time.time(),
                }
                self.last_result = result
                results.append(result)

        return results


# ═══════════════════════════════════════════════════════════════════
#  SSE Broadcast Hub
# ═══════════════════════════════════════════════════════════════════
class SSEHub:
    """Thread-safe hub for Server-Sent Events subscribers."""

    def __init__(self):
        self._lock = threading.Lock()
        self._subscribers: dict[int, list[dict]] = {}
        self._next_id = 0

    def subscribe(self) -> int:
        with self._lock:
            sid = self._next_id
            self._next_id += 1
            self._subscribers[sid] = []
            return sid

    def unsubscribe(self, sid: int):
        with self._lock:
            self._subscribers.pop(sid, None)

    def broadcast(self, event: dict):
        with self._lock:
            for queue in self._subscribers.values():
                queue.append(event)
                if len(queue) > 100:
                    queue.pop(0)

    def poll(self, sid: int, timeout: float = 1.0) -> list[dict]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._lock:
                queue = self._subscribers.get(sid)
                if queue is None:
                    return []
                if queue:
                    events = list(queue)
                    queue.clear()
                    return events
            time.sleep(0.05)
        return []

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._subscribers)


# ═══════════════════════════════════════════════════════════════════
#  Global state
# ═══════════════════════════════════════════════════════════════════
analyser = ChakraFFTAnalyser()
sse_hub = SSEHub()
raw_hub = SSEHub()
bedrock_client = None
last_bedrock_call = 0.0
BEDROCK_RATE_LIMIT = 3.0   # seconds between Bedrock invocations

AGENT_ID = "FEFWNRBPIQ"
AGENT_ALIAS_ID = "TSTALIASID"


def invoke_bedrock_async(chakra_result: dict):
    """Fire-and-forget Bedrock ChakraMaster invocation."""
    global last_bedrock_call, bedrock_client
    now = time.time()
    if now - last_bedrock_call < BEDROCK_RATE_LIMIT:
        return
    last_bedrock_call = now

    if bedrock_client is None:
        try:
            import boto3
            bedrock_client = boto3.client(
                "bedrock-agent-runtime", region_name="eu-central-1"
            )
        except Exception as e:
            print(f"[bedrock] boto3 init failed: {e}")
            return

    def _invoke():
        try:
            prompt = (
                f"Frequency {chakra_result['frequency']} Hz detected → "
                f"{chakra_result['chakra_name']} chakra. "
                f"Immediately set the light to RGB({chakra_result['r']},{chakra_result['g']},{chakra_result['b']}). "
                f"Do not ask for confirmation."
            )
            bedrock_client.invoke_agent(
                agentId=AGENT_ID,
                agentAliasId=AGENT_ALIAS_ID,
                sessionId=f"audio-{int(time.time())}",
                inputText=prompt,
            )
            print(f"[bedrock] ✓ {chakra_result['chakra_name']} ({chakra_result['frequency']} Hz)")
        except Exception as e:
            print(f"[bedrock] ✗ {e}")

    threading.Thread(target=_invoke, daemon=True).start()


# ═══════════════════════════════════════════════════════════════════
#  HTTP Handler
# ═══════════════════════════════════════════════════════════════════
class RelayHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Quieter logging
        if "/health" not in (args[0] if args else ""):
            print(f"[relay] {fmt % args}")

    def do_GET(self):
        if self.path == "/health":
            self._json_response(200, {
                "status": "ok",
                "subscribers": sse_hub.count,
                "raw_subscribers": raw_hub.count,
            })

        elif self.path == "/aws/audio/live":
            self._handle_sse(sse_hub)

        elif self.path == "/aws/audio/raw":
            self._handle_sse(raw_hub)

        else:
            self._json_response(404, {"error": "not found"})

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        if self.path == "/aws/audio":
            self._handle_audio(body)

        elif self.path == "/aws/chakra":
            self._handle_chakra(body)

        else:
            self._json_response(404, {"error": "not found"})

    def _handle_audio(self, pcm_data: bytes):
        """Receive raw PCM, run FFT, broadcast results."""
        # Broadcast raw PCM as base64 for clients wanting own FFT
        if raw_hub.count > 0:
            raw_event = {
                "type": "pcm",
                "sample_rate": 16000,
                "bits": 16,
                "channels": 1,
                "samples": len(pcm_data) // 2,
                "data_b64": base64.b64encode(pcm_data).decode("ascii"),
            }
            raw_hub.broadcast(raw_event)

        # Run FFT + chakra detection
        detections = analyser.push_samples(pcm_data)

        for det in detections:
            sse_hub.broadcast(det)
            invoke_bedrock_async(det)
            print(f"[fft] {det['chakra_name']} @ {det['frequency']} Hz "
                  f"({det['signal_db']} dB) → {sse_hub.count} subscribers")

        self._json_response(200, {
            "ok": True,
            "detections": len(detections),
        })

    def _handle_chakra(self, body: bytes):
        """Legacy: receive pre-computed {frequency, chakra_index} from ESP32."""
        try:
            data = json.loads(body)
            freq = float(data.get("frequency", 0))
            cidx = int(data.get("chakra_index", -1))
            if 0 <= cidx <= 6:
                result = {
                    "chakra_index": cidx,
                    "chakra_name": CHAKRA_TABLE[cidx]["name"],
                    "frequency": freq,
                    "signal_db": 0.0,
                    "color": CHAKRA_TABLE[cidx]["hex"],
                    "r": CHAKRA_TABLE[cidx]["r"],
                    "g": CHAKRA_TABLE[cidx]["g"],
                    "b": CHAKRA_TABLE[cidx]["b"],
                    "timestamp": time.time(),
                }
                sse_hub.broadcast(result)
                invoke_bedrock_async(result)
            self._json_response(200, {"ok": True})
        except Exception as e:
            self._json_response(400, {"error": str(e)})

    def _handle_sse(self, hub: SSEHub):
        """Stream Server-Sent Events to subscriber."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        sid = hub.subscribe()
        print(f"[sse] +subscriber #{sid} (total: {hub.count})")
        try:
            while True:
                events = hub.poll(sid, timeout=1.0)
                for ev in events:
                    line = f"data: {json.dumps(ev)}\n\n"
                    self.wfile.write(line.encode())
                    self.wfile.flush()
                if not events:
                    # Keep-alive
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            hub.unsubscribe(sid)
            print(f"[sse] -subscriber #{sid} (total: {hub.count})")

    def _json_response(self, code: int, data: dict):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


class ThreadedHTTPServer(HTTPServer):
    """Handle each request in a new thread (needed for SSE)."""
    allow_reuse_address = True

    def process_request(self, request, client_address):
        t = threading.Thread(target=self._handle, args=(request, client_address))
        t.daemon = True
        t.start()

    def _handle(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)


def main():
    parser = argparse.ArgumentParser(description="Audio FFT Relay for ESP32 Chakra Pipeline")
    parser.add_argument("--port", type=int, default=8765, help="Listen port (default: 8765)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Bind address")
    parser.add_argument("--no-bedrock", action="store_true", help="Disable Bedrock invocation")
    args = parser.parse_args()

    if args.no_bedrock:
        global BEDROCK_RATE_LIMIT
        BEDROCK_RATE_LIMIT = float("inf")

    server = ThreadedHTTPServer((args.host, args.port), RelayHandler)
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  Audio FFT Relay — Chakra Pipeline Hub                       ║
║                                                              ║
║  POST /aws/audio       ← ESP32 raw PCM (int16 LE, 16kHz)    ║
║  POST /aws/chakra      ← ESP32 pre-computed frequency        ║
║  GET  /aws/audio/live  → SSE chakra detections (subscribe)   ║
║  GET  /aws/audio/raw   → SSE raw PCM base64 (own FFT)        ║
║  GET  /health          → status + subscriber count            ║
║                                                              ║
║  Listening on {args.host}:{args.port}                        ║
╚══════════════════════════════════════════════════════════════╝
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[relay] Shutting down")
        server.shutdown()


if __name__ == "__main__":
    main()
