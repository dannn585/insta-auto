"""Original, royalty-free background music for reels (synthesized with numpy, no samples).

Unlike beat.py (one loop), each preset is a small arrangement so it does not get boring:
  intro (keys + hats) -> groove (drums + bass + keys) -> lift (arpeggio melody added)
  -> short break every 8 bars (kick drops out, a riser leads back in) ... -> fade out.
Different presets = different tempo, chords, sound, so consecutive reels do not sound the same.

Usage: python scripts/bgm.py out.wav seconds [preset] [seed]
presets: chill, pop, bright, warm, lofi, drive, soft
"""
import sys
import wave

import numpy as np

SR = 48000

# chord = list of MIDI notes (root first). One chord per bar.
PRESETS = {
    # lo-fi, relaxed (Fmaj7 Em7 Dm7 Cmaj7)
    "chill":  dict(bpm=88,  swing=.18, chords=[[53, 57, 60, 64], [52, 55, 59, 62], [50, 53, 57, 60], [48, 52, 55, 59]],
                   scale=[0, 2, 4, 7, 9], key=60, kick=(0, 2.5), snare=(1, 3), keys="ep", lead="bell"),
    # bright pop (C G Am F)
    "pop":    dict(bpm=112, swing=0,   chords=[[48, 52, 55, 60], [43, 47, 50, 55], [45, 48, 52, 57], [41, 45, 48, 53]],
                   scale=[0, 2, 4, 7, 9], key=72, kick=(0, 1, 2, 3), snare=(1, 3), keys="pluck", lead="pluck"),
    # upbeat (D A Bm G)
    "bright": dict(bpm=120, swing=0,   chords=[[50, 54, 57, 62], [45, 49, 52, 57], [47, 50, 54, 59], [43, 47, 50, 55]],
                   scale=[0, 2, 4, 7, 9], key=74, kick=(0, 1.5, 2, 3.5), snare=(1, 3), keys="pluck", lead="bell"),
    # warm, a little emotional (Am F C G)
    "warm":   dict(bpm=100, swing=.1,  chords=[[45, 48, 52, 57], [41, 45, 48, 53], [48, 52, 55, 60], [43, 47, 50, 55]],
                   scale=[0, 3, 5, 7, 10], key=69, kick=(0, 2, 2.75), snare=(1, 3), keys="ep", lead="pluck"),
    # dusty lo-fi (Ebmaj7 Dm7 Cm7 Bbmaj7)
    "lofi":   dict(bpm=82,  swing=.22, chords=[[51, 55, 58, 62], [50, 53, 57, 60], [48, 51, 55, 58], [46, 50, 53, 57]],
                   scale=[0, 2, 3, 7, 10], key=63, kick=(0, 2.5, 3.25), snare=(1, 3), keys="ep", lead="bell"),
    # driving (Em C G D)
    "drive":  dict(bpm=124, swing=0,   chords=[[52, 55, 59, 64], [48, 52, 55, 60], [43, 47, 50, 55], [50, 54, 57, 62]],
                   scale=[0, 3, 5, 7, 10], key=76, kick=(0, 1, 2, 3), snare=(1, 3), keys="pluck", lead="pluck"),
    # soft, curious (Gmaj7 F#m7 Em7 Dmaj7... in D)
    "soft":   dict(bpm=96,  swing=.12, chords=[[43, 47, 50, 54], [42, 45, 49, 52], [40, 43, 47, 50], [50, 54, 57, 61]],
                   scale=[0, 2, 4, 7, 9], key=74, kick=(0, 2.5), snare=(1, 3), keys="ep", lead="bell"),
}


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def shelf(x, fc, kind="low", order=2):
    """Gentle Butterworth-shaped low/high-pass done in the frequency domain (no scipy needed)."""
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    r = (f / fc) ** (2 * order)
    g = 1 / np.sqrt(1 + r) if kind == "low" else np.sqrt(r / (1 + r))
    return np.fft.irfft(X * g, n)


def adsr(n, a, d, s, r_len, sustain_level):
    e = np.full(n, sustain_level, dtype=float)
    na, nd, nr = int(a * SR), int(d * SR), int(r_len * SR)
    na = max(1, min(na, n))
    e[:na] = np.linspace(0, 1, na)
    nd = max(0, min(nd, n - na))
    e[na:na + nd] = np.linspace(1, sustain_level, nd) if nd else e[na:na + nd]
    nr = min(nr, n)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def tone(m, dur, kind, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    if kind == "ep":      # soft electric-piano-ish: sine + bell partial, slow decay
        det = 1 + rng.uniform(-.0015, .0015)
        w = np.sin(2 * np.pi * f * det * t) + .25 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 6) \
            + .12 * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-t * 9)
        return w * adsr(n, .01, .4, .45, .12, .45) * np.exp(-t * .6)
    if kind == "pluck":   # short pluck: a few harmonics that die fast
        w = sum((1 / k) * np.sin(2 * np.pi * k * f * t) * np.exp(-t * (5 + 4 * k)) for k in range(1, 6))
        return w * adsr(n, .003, .05, 1, .03, 1)
    if kind == "bell":    # glassy bell for the lead
        w = np.sin(2 * np.pi * f * t) * np.exp(-t * 3) + .4 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t * 7) \
            + .2 * np.sin(2 * np.pi * 5.4 * f * t) * np.exp(-t * 12)
        return w * adsr(n, .004, .05, 1, .05, 1)
    if kind == "bass":    # round bass: sine + a bit of 2nd harmonic
        w = np.sin(2 * np.pi * f * t) + .3 * np.sin(2 * np.pi * 2 * f * t) + .08 * np.sin(2 * np.pi * 3 * f * t)
        return w * adsr(n, .006, .08, .8, .06, .8)
    raise ValueError(kind)


def put(buf, x, start, gain=1.0, pan=0.0):
    s = int(start * SR)
    if s >= buf.shape[0] or s < 0:
        return
    x = x[: buf.shape[0] - s]
    buf[s:s + len(x), 0] += gain * x * (1 - max(pan, 0))
    buf[s:s + len(x), 1] += gain * x * (1 + min(pan, 0))


def drums(rng):
    kl = int(.4 * SR)
    t = np.arange(kl) / SR
    kick = np.sin(2 * np.pi * (48 * t + 110 / 28 * (1 - np.exp(-t * 28)))) * np.exp(-t * 8)
    kick += .3 * np.sin(2 * np.pi * 48 * t) * np.exp(-t * 4) * (t < .3)
    sl = int(.25 * SR)
    t = np.arange(sl) / SR
    noise = rng.standard_normal(sl)
    snare = shelf(noise, 1800, "high") * np.exp(-t * 18) * .8 + np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25) * .5
    hl = int(.07 * SR)
    t = np.arange(hl) / SR
    hat = shelf(rng.standard_normal(hl), 7000, "high", 3) * np.exp(-t * 60)
    ol = int(.22 * SR)
    t = np.arange(ol) / SR
    ohat = shelf(rng.standard_normal(ol), 6500, "high", 3) * np.exp(-t * 14)
    return kick, snare, hat, ohat


def motif(rng, scale, length=8):
    """A short melodic idea (scale degrees, None = rest) that is repeated with small changes."""
    deg = [int(rng.integers(0, 5)) for _ in range(length)]
    rhythm = rng.random(length) < .7
    rhythm[0] = True
    return [d if r else None for d, r in zip(deg, rhythm)]


def render(seconds, preset="chill", seed=1):
    P = PRESETS[preset]
    rng = np.random.default_rng(seed)
    n = int(SR * (seconds + .5))
    drum = np.zeros((n, 2))
    keys = np.zeros((n, 2))
    bass = np.zeros((n, 2))
    lead = np.zeros((n, 2))
    fx = np.zeros((n, 2))
    beat = 60 / P["bpm"]
    bar = beat * 4
    kick, snare, hat, ohat = drums(rng)
    chords = P["chords"]
    # vary the chord order a little per seed (rotate) so same preset != same song
    rot = int(rng.integers(0, 4))
    chords = chords[rot:] + chords[:rot]
    mot = motif(rng, P["scale"])
    mot2 = motif(rng, P["scale"])
    bars = int(np.ceil(seconds / bar)) + 1

    def sw(pos8):   # swing on the off-8ths
        return pos8 * beat / 2 + (P["swing"] * beat / 2 if pos8 % 2 else 0)

    for b in range(bars):
        t0 = b * bar
        if t0 > seconds + .5:
            break
        ch = chords[b % 4]
        sec = b % 8                       # position in an 8-bar section
        intro = b < 2
        brk = sec == 7                    # last bar of every 8: a breath
        lift = (b // 4) % 2 == 1 and not intro   # every other 4-bar block gets the melody
        # keys: chord stabs (pluck) or held chord (ep)
        if P["keys"] == "ep":
            for i, m in enumerate(ch):
                put(keys, tone(m, bar * .98, "ep", rng), t0 + i * .012, .2, (i - 1.5) * .25)
            if not intro:
                for i, m in enumerate(ch[1:]):   # a light re-hit on beat 3
                    put(keys, tone(m + 12, beat * 1.5, "pluck", rng), t0 + 2 * beat + .01, .05, .3 - .3 * i)
        else:
            pattern = [0, 1.5, 3] if not brk else [0]
            for p in pattern:
                for i, m in enumerate(ch):
                    put(keys, tone(m + 12, beat * .9, "pluck", rng), t0 + p * beat + i * .006, .13, (i - 1.5) * .3)
        # bass
        if not intro:
            root = ch[0] - 12
            steps = [0, 3, 4, 6] if not brk else [0]
            for k in steps:
                m = root + (12 if k == 6 and rng.random() < .5 else 0)
                put(bass, tone(m, beat * .45, "bass", rng), t0 + sw(k), .3)
        # drums
        hats_on = True
        if not intro:
            for k in P["kick"]:
                if brk and k >= 2:
                    continue
                put(drum, kick, t0 + k * beat, .55)
            for k in P["snare"]:
                if brk and k >= 2:
                    continue
                put(drum, snare, t0 + k * beat, .32, .05)
        if hats_on:
            for k in range(8):
                g = .13 if k % 2 else .08
                if intro and k % 2 == 0:
                    continue
                put(drum, hat, t0 + sw(k) + rng.uniform(-.004, .004), g * rng.uniform(.8, 1.1), .35)
            if not intro and b % 2 == 1:
                put(drum, ohat, t0 + sw(7), .07, .35)
        # fill + riser at the end of each 8 bars
        if brk:
            for k in range(4):
                put(drum, snare, t0 + 2 * beat + k * beat / 2, .12 + .05 * k, -.1)
            rl = int(bar / 2 * SR)
            t = np.arange(rl) / SR
            riser = shelf(rng.standard_normal(rl), 3000, "high") * (t / t[-1]) ** 2
            put(fx, riser, t0 + bar / 2, .06)
        # crash-ish swell on the first beat after a break
        if sec == 0 and b > 0:
            cl = int(1.2 * SR)
            t = np.arange(cl) / SR
            put(fx, shelf(rng.standard_normal(cl), 5000, "high") * np.exp(-t * 3), t0, .05)
        # melody (arpeggio from the motif, follows the chord root)
        if lift and not brk:
            m_use = mot if (b // 8) % 2 == 0 else mot2
            for k, d in enumerate(m_use):
                if d is None:
                    continue
                m = P["key"] + P["scale"][d]
                # keep the melody inside the chord's harmony: snap to the nearest chord tone half the time
                if rng.random() < .5:
                    m = min((c + 24 for c in ch), key=lambda c: abs(c - m))
                put(lead, tone(m, beat * .9, P["lead"], rng), t0 + sw(k), .12, .25 if k % 2 else -.25)

    lead = lead + .35 * np.roll(lead[:, ::-1], int(beat * .75 * SR), axis=0)   # ping-pong delay
    keys = np.stack([shelf(keys[:, 0], 5500), shelf(keys[:, 1], 5500)], axis=1)
    mix = drum + keys + bass + lead + fx
    # gentle "tape" glue
    mix = np.tanh(mix * 1.2) / 1.2
    n_out = int(SR * seconds)
    mix = mix[:n_out]
    fi, fo = int(.25 * SR), int(min(1.2, seconds / 4) * SR)
    mix[:fi] *= np.linspace(0, 1, fi)[:, None]
    mix[-fo:] *= np.linspace(1, 0, fo)[:, None]
    mix = mix / (np.max(np.abs(mix)) + 1e-9) * .7
    return mix


def write(path, mix):
    data = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


if __name__ == "__main__":
    out, secs = sys.argv[1], float(sys.argv[2])
    preset = sys.argv[3] if len(sys.argv) > 3 else "chill"
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    write(out, render(secs, preset, seed))
    print(out)
