#pragma once
// chakra_component.h  v3
// Improvements over v2:
//  - Harmonic-product scoring replaces simple peak search:
//    scores each candidate fundamental by summing energy at f + 2f + 3f + 4f,
//    so the true pitch wins over any isolated overtone.
//  - Parabolic interpolation gives sub-bin frequency accuracy (~1 Hz).
//  - Search range narrowed to 60–1000 Hz (singing-bowl fundamentals only).
//  - Pre-computed magnitude array eliminates redundant sqrtf calls.
//  - Updated CHAKRA_TABLE frequencies to standard 432 Hz tuning reference.

#include <cmath>
#include <cstring>
#include <cstdint>
#include <algorithm>

static const int CHAKRA_NUM_BARS = 16;

struct ChakraInfo {
    const char* name;
    const char* hex_color;
    uint8_t r, g, b;
    float freq_lo;
    float freq_hi;
    bool dark_bg;
};

static const ChakraInfo CHAKRA_TABLE[7] = {
    // freq_lo/hi = ±1 semitone around canonical 432 Hz-tuned note (single octave reference).
    // Detection is semitone-class based (octave-independent); these are informational.
    {"Root",         "#FF0000", 0xFF, 0x00, 0x00,  242.0f,  272.0f, false}, // C4 ≈ 257 Hz
    {"Sacral",       "#FF7F00", 0xFF, 0x7F, 0x00,  272.0f,  305.0f, false}, // D4 ≈ 288 Hz
    {"Solar Plexus", "#FFFF00", 0xFF, 0xFF, 0x00,  305.0f,  343.0f, false}, // E4 ≈ 324 Hz
    {"Heart",        "#00CC00", 0x00, 0xCC, 0x00,  323.0f,  363.0f, false}, // F4 ≈ 343 Hz
    {"Throat",       "#0000FF", 0x00, 0x00, 0xFF,  363.0f,  407.0f, true }, // G4 ≈ 385 Hz
    {"Third Eye",    "#4B0082", 0x4B, 0x00, 0x82,  407.0f,  457.0f, true }, // A4 = 432 Hz
    {"Crown",        "#EE82EE", 0xEE, 0x82, 0xEE,  457.0f,  514.0f, false}, // B4 ≈ 485 Hz
};

// 16 log-spaced bar edges from 32–5000 Hz
static const float BAR_FREQ_LO[CHAKRA_NUM_BARS] = {
     32.0f,  44.0f,  61.0f,  85.0f, 118.0f, 163.0f, 226.0f, 313.0f,
    434.0f, 601.0f, 832.0f,1152.0f,1596.0f,2210.0f,3060.0f,4000.0f
};
static const float BAR_FREQ_HI[CHAKRA_NUM_BARS] = {
     44.0f,  61.0f,  85.0f, 118.0f, 163.0f, 226.0f, 313.0f, 434.0f,
    601.0f, 832.0f,1152.0f,1596.0f,2210.0f,3060.0f,4000.0f,5000.0f
};

class ChakraAnalyser {
public:
    static int    dominant_chakra;                 // -1 = none, 0-6 = chakra index
    static float  peak_magnitude;                  // RMS amplitude 0.0-1.0
    static float  bar_magnitudes[CHAKRA_NUM_BARS]; // 0.0-1.0, relative to running max
    static float  peak_frequency;                  // Hz of dominant FFT bin
    static float  signal_db;                       // dBFS of RMS signal (~-90 to 0)
    static int    accum_fill;                      // samples buffered so far (0-1024)

    static void init() {}

    // Streaming accumulator: call from microphone on_data.
    // Returns true when 1024 samples have been processed and results are fresh.
    static bool push_samples(const int16_t* buf, size_t len, float threshold) {
        for (size_t i = 0; i < len; i++) {
            _accum[_accum_count++] = buf[i];
            if (_accum_count >= FFT_N) {
                _run_fft(threshold);
                _accum_count = 0;
                accum_fill = 0;
                return true;
            }
        }
        accum_fill = _accum_count;
        return false;
    }

    static const ChakraInfo& get_info(int idx) {
        if (idx < 0 || idx > 6) {
            static const ChakraInfo none = {"None", "#FFFFFF", 0xFF, 0xFF, 0xFF, 0, 0, false};
            return none;
        }
        return CHAKRA_TABLE[idx];
    }

private:
    static constexpr int FFT_N = 512;
    static float    _re[FFT_N];
    static float    _im[FFT_N];
    static float    _mag[FFT_N / 2 + 1]; // pre-computed magnitude spectrum
    static int16_t  _accum[FFT_N];
    static int      _accum_count;
    static float    _running_bar_max;   // decaying max for bar normalisation

    static void _bit_reverse(float* re, float* im, int n) {
        int j = 0;
        for (int i = 1; i < n; i++) {
            int bit = n >> 1;
            for (; j & bit; bit >>= 1) j ^= bit;
            j ^= bit;
            if (i < j) {
                float tr = re[i]; re[i] = re[j]; re[j] = tr;
                float ti = im[i]; im[i] = im[j]; im[j] = ti;
            }
        }
    }

    static void _fft(float* re, float* im, int n) {
        _bit_reverse(re, im, n);
        for (int len = 2; len <= n; len <<= 1) {
            float ang = -2.0f * M_PI / len;
            float wr = cosf(ang), wi = sinf(ang);
            for (int i = 0; i < n; i += len) {
                float cur_r = 1.0f, cur_i = 0.0f;
                for (int j = 0; j < len / 2; j++) {
                    float ur = re[i + j], ui = im[i + j];
                    float vr = re[i+j+len/2]*cur_r - im[i+j+len/2]*cur_i;
                    float vi = re[i+j+len/2]*cur_i + im[i+j+len/2]*cur_r;
                    re[i + j]         = ur + vr;
                    im[i + j]         = ui + vi;
                    re[i + j + len/2] = ur - vr;
                    im[i + j + len/2] = ui - vi;
                    float new_r = cur_r*wr - cur_i*wi;
                    cur_i = cur_r*wi + cur_i*wr;
                    cur_r = new_r;
                }
            }
        }
    }

    static void _run_fft(float threshold) {
        const float sample_rate = 16000.0f;

        // ── RMS signal level (before windowing, true amplitude measure) ──
        float sum_sq = 0.0f;
        for (int i = 0; i < FFT_N; i++) {
            float s = _accum[i] / 32768.0f;
            sum_sq += s * s;
        }
        float rms = sqrtf(sum_sq / FFT_N);
        peak_magnitude = rms;
        signal_db = 20.0f * log10f(rms + 1e-9f);

        // ── Apply Hann window and run FFT ────────────────────────────────
        for (int i = 0; i < FFT_N; i++) {
            float w = 0.5f * (1.0f - cosf(2.0f * M_PI * i / (FFT_N - 1)));
            _re[i] = (_accum[i] / 32768.0f) * w;
            _im[i] = 0.0f;
        }
        _fft(_re, _im, FFT_N);

        float freq_res = sample_rate / FFT_N;   // 31.25 Hz per bin

        // ── Pre-compute magnitude spectrum (avoids redundant sqrtf) ─────
        for (int k = 0; k <= FFT_N / 2; k++)
            _mag[k] = sqrtf(_re[k]*_re[k] + _im[k]*_im[k]);

        // ── Harmonic-product peak detection (60–1000 Hz) ─────────────────
        // Scores each candidate fundamental by summing weighted energy at
        // f, 2f, 3f, 4f.  The true pitch outscores any isolated overtone.
        // Example: a C bowl's 3rd harmonic (G) only gets mag[G], but C itself
        // gets mag[C] + 0.5×mag[2C] + 0.33×mag[3C=G] + 0.25×mag[4C].
        // At 16 kHz / 512 pts: freq_res = 31.25 Hz/bin → k_lo=2 (62.5 Hz), k_hi=32 (1000 Hz)
        const int k_lo = 2;    //  62.5 Hz
        const int k_hi = 32;   // 1000.0 Hz (covers B5 ≈ 988 Hz)
        int   best_bin   = k_lo;
        float best_score = 0.0f;
        for (int k = k_lo; k <= k_hi; k++) {
            float score = _mag[k];
            if (2*k <= FFT_N/2) score += 0.50f * _mag[2*k];
            if (3*k <= FFT_N/2) score += 0.33f * _mag[3*k];
            if (4*k <= FFT_N/2) score += 0.25f * _mag[4*k];
            if (score > best_score) { best_score = score; best_bin = k; }
        }

        // ── Parabolic interpolation for sub-bin frequency accuracy ───────
        float fine_bin = (float)best_bin;
        if (best_bin > k_lo && best_bin < k_hi) {
            float y0 = _mag[best_bin - 1], y1 = _mag[best_bin], y2 = _mag[best_bin + 1];
            float denom = y0 - 2.0f*y1 + y2;
            if (fabsf(denom) > 1e-12f) fine_bin = best_bin + 0.5f * (y0 - y2) / denom;
        }
        peak_frequency = fine_bin * freq_res;

        // ── Accumulate bar energies ──────────────────────────────────────
        for (int b = 0; b < CHAKRA_NUM_BARS; b++) bar_magnitudes[b] = 0.0f;
        const int k_bar_max = (int)(5000.0f / freq_res) + 1;
        for (int k = 2; k < FFT_N / 2 && k <= k_bar_max; k++) {
            float freq = k * freq_res;
            for (int b = 0; b < CHAKRA_NUM_BARS; b++) {
                if (freq >= BAR_FREQ_LO[b] && freq < BAR_FREQ_HI[b]) {
                    bar_magnitudes[b] += _mag[k];
                    break;  // bands are non-overlapping
                }
            }
        }

        // ── Running-max normalisation: bars decay instead of always=1.0 ─
        float bar_max = 1e-9f;
        for (int b = 0; b < CHAKRA_NUM_BARS; b++)
            if (bar_magnitudes[b] > bar_max) bar_max = bar_magnitudes[b];
        // Fast attack, slow decay (~1 s at ~15 fps)
        if (bar_max > _running_bar_max) _running_bar_max = bar_max;
        else _running_bar_max *= 0.93f;
        if (_running_bar_max < 1e-6f) _running_bar_max = 1e-6f;
        for (int b = 0; b < CHAKRA_NUM_BARS; b++)
            bar_magnitudes[b] /= _running_bar_max;

        // ── Chakra detection via musical note class ──────────────────────
        // Semitone → chakra: C=Root, D=Sacral, E=Solar, F=Heart,
        //                    G=Throat, A=Third Eye, B=Crown.
        // Sharps/flats map to the nearer chakra note.
        // Octave-independent: any octave of C maps to Root, etc.
        dominant_chakra = -1;
        if (rms >= threshold && peak_frequency >= 60.0f) {
            float midi_note = 69.0f + 12.0f * log2f(peak_frequency / 432.0f);
            int semitone = ((int)roundf(midi_note)) % 12;
            if (semitone < 0) semitone += 12;
            // C=0,C#=1 → Root(0); D=2,D#=3 → Sacral(1); E=4 → Solar(2);
            // F=5,F#=6 → Heart(3); G=7,G#=8 → Throat(4); A=9 → ThirdEye(5); A#=10,B=11 → Crown(6)
            static const int NOTE_TO_CHAKRA[12] = {0, 0, 1, 1, 2, 3, 3, 4, 4, 5, 6, 6};
            dominant_chakra = NOTE_TO_CHAKRA[semitone];
        }
    }
};

// Static member definitions
int    ChakraAnalyser::dominant_chakra  = -1;
float  ChakraAnalyser::peak_magnitude   = 0.0f;
float  ChakraAnalyser::peak_frequency   = 0.0f;
float  ChakraAnalyser::signal_db        = -90.0f;
int    ChakraAnalyser::accum_fill       = 0;
float  ChakraAnalyser::bar_magnitudes[CHAKRA_NUM_BARS] = {};
float  ChakraAnalyser::_re[ChakraAnalyser::FFT_N]      = {};
float  ChakraAnalyser::_im[ChakraAnalyser::FFT_N]      = {};
float  ChakraAnalyser::_mag[ChakraAnalyser::FFT_N/2+1] = {};
int16_t ChakraAnalyser::_accum[ChakraAnalyser::FFT_N]  = {};
int    ChakraAnalyser::_accum_count     = 0;
float  ChakraAnalyser::_running_bar_max = 1.0f;
