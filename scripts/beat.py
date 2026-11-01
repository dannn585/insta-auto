"""Generate an original, royalty-free background beat (no samples) as a WAV file.

Usage: python scripts/beat.py out.wav seconds
"""
import sys
import wave

import numpy as np

SR = 48000
BPM = 112


def env(n, attack, decay):
    t = np.arange(n) / SR
    return np.minimum(t / attack, 1.0) * np.exp(-t / decay)


def main(path, seconds):
    n = int(SR * seconds)
    mix = np.zeros(n)
    beat = 60 / BPM
    rng = np.random.default_rng(7)

    kick_len = int(.35 * SR)
    tk = np.arange(kick_len) / SR
    kick = np.sin(2 * np.pi * (50 + 90 * np.exp(-tk * 30)) * tk) * np.exp(-tk * 9)
    hat_len = int(.06 * SR)
    hat = rng.standard_normal(hat_len) * env(hat_len, .001, .015)
    hat = np.diff(hat, prepend=0)  # crude high-pass

    # chord loop: Am - F - C - G (one bar each)
    chords = [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [196.0, 261.63, 329.63], [196.0, 246.94, 293.66]]
    bar = beat * 4
    i = 0
    tpos = 0.0
    while tpos < seconds:
        s = int(tpos * SR)
        # kick on 1 and 3, plus pickup
        for k in (0, 2, 2.75):
            ks = s + int(k * beat * SR)
            if ks < n:
                seg = kick[: n - ks]
                mix[ks:ks + len(seg)] += .9 * seg
        for h in range(8):
            hs = s + int((h + .5) * beat / 2 * SR)
            if hs < n:
                seg = hat[: n - hs]
                mix[hs:hs + len(seg)] += .18 * seg
        L = min(int(bar * SR), n - s)
        t = np.arange(L) / SR
        pad = sum(np.sin(2 * np.pi * f * t) + .3 * np.sin(2 * np.pi * 2 * f * t) for f in chords[i % 4])
        pluck_env = np.exp(-(t % (beat / 2)) * 7)  # rhythmic pluck on 8ths
        mix[s:s + L] += .07 * pad * (0.35 + 0.65 * pluck_env)
        i += 1
        tpos += bar

    fade = int(.6 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix[:int(.02 * SR)] *= np.linspace(0, 1, int(.02 * SR))
    mix = mix / np.max(np.abs(mix)) * .5  # keep it as background level
    data = (np.stack([mix, mix], axis=1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]))
