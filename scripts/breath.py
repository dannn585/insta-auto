"""Find and remove breaths (inhale / exhale noises) from a voice recording.

Idea: vowels have a pitch (periodic), breaths do not. A sound that stays pitch-less for a long time
next to a pause is a breath. Short pitch-less parts (consonants like "s", "sh", "k", devoiced "su")
are kept, so words are not cut.

  python scripts/breath.py drafts/voice/1111.m4a            -> prints the breaths it found
  python scripts/breath.py in.m4a out.wav                    -> writes a copy with the breaths muted
reel_v3.py calls clean() automatically (spec "breath": false to turn it off).
"""
import subprocess
import sys
import wave

import numpy as np

SR = 16000          # analysis rate
HOP = 0.01          # 10 ms frames
WIN = 0.04          # 40 ms window for pitch
LEAD_KEEP = 0.12    # pitch-less sound kept right before a vowel (consonant at word start)
TAIL_KEEP = 0.16    # kept right after the last vowel (devoiced endings: "です", "ます")
MIN_BREATH = 0.12   # shorter pitch-less blips are left alone


def load(path, sr=SR):
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(pcm, np.int16).astype(np.float64) / 32768


def frames(x):
    hop, win = int(HOP * SR), int(WIN * SR)
    n = max(0, (len(x) - win) // hop + 1)
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    return x[idx]


def analyse(x):
    F = frames(x)
    rms = np.sqrt(np.mean(F ** 2, axis=1)) + 1e-9
    db = 20 * np.log10(rms)
    ref = np.percentile(db, 95)                      # loud speech level of this file
    # normalized autocorrelation in the voice pitch range (70-400 Hz)
    Fz = F - F.mean(axis=1, keepdims=True)
    Fz *= np.hanning(F.shape[1])[None, :]
    spec = np.fft.rfft(Fz, 2 * F.shape[1], axis=1)
    ac = np.fft.irfft(np.abs(spec) ** 2, axis=1)[:, :F.shape[1]]
    ac /= ac[:, :1] + 1e-12
    lo, hi = int(SR / 400), int(SR / 70)
    pitch = ac[:, lo:hi].max(axis=1)
    rel = db - ref
    sound = rel > -42                                # anything audible over the room noise
    voiced = sound & (pitch > 0.4) & (rel > -38)
    return rel, sound, voiced


def runs(mask):
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            out.append((i, j))
            i = j
        else:
            i += 1
    return out


def find(path):
    """Return [(start, end), ...] seconds that are breaths."""
    x = load(path)
    rel, sound, voiced = analyse(x)
    # bridge tiny gaps so one breath is one island
    s = sound.copy()
    for a, b in runs(~sound):
        if b - a <= 4 and a > 0:
            s[a:b] = True
    breaths = []
    for a, b in runs(s):
        v = np.flatnonzero(voiced[a:b])
        # ignore 1-2 stray "voiced" frames inside a breath
        if len(v) < 4:
            cand = [(a, b)]
        else:
            first, last = a + v[0], a + v[-1] + 1
            cand = [(a, first - int(LEAD_KEEP / HOP)), (last + int(TAIL_KEEP / HOP), b)]
            # long pitch-less stretch between two words (breath taken mid-phrase)
            for c, d in runs(~voiced[first:last]):
                if (d - c) * HOP > 0.35:
                    cand.append((first + c + int(TAIL_KEEP / HOP), first + d - int(LEAD_KEEP / HOP)))
        for c, d in cand:
            if (d - c) * HOP >= MIN_BREATH:
                breaths.append((round(c * HOP + WIN / 2, 3), round(d * HOP + WIN / 2, 3)))
    return breaths


def clean(path, out_wav, fade=0.02):
    """Write out_wav (48 kHz mono) with every breath muted (short fades, so no clicks)."""
    sr = 48000
    x = load(path, sr)
    g = np.ones(len(x))
    for a, b in find(path):
        i, j = int(a * sr), int(b * sr)
        f = int(fade * sr)
        g[i:j] = 0
        g[max(0, i - f):i] = np.minimum(g[max(0, i - f):i], np.linspace(1, 0, i - max(0, i - f)))
        g[j:j + f] = np.minimum(g[j:j + f], np.linspace(0, 1, len(g[j:j + f])))
    y = (np.clip(x * g, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(y.tobytes())
    return out_wav


if __name__ == "__main__":
    if len(sys.argv) > 2:
        clean(sys.argv[1], sys.argv[2])
        print(sys.argv[2])
    else:
        for a, b in find(sys.argv[1]):
            print(f"{a:7.2f}-{b:7.2f} ({b - a:.2f}s)")
