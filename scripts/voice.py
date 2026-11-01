"""Add a VOICEVOX narration to every queued reel that has narration.json with "voiced": false.

Runs in GitHub Actions with the VOICEVOX ENGINE as a service container (http://localhost:50021).
For each segment: synthesize, speed it up (max 1.6x) if it would overrun its scene, place it at the
scene start, then mix over the reel's existing BGM (BGM lowered so the voice is clear).
"""
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
ENGINE = "http://localhost:50021"


def synth(text, speaker, speed):
    q = requests.post(f"{ENGINE}/audio_query", params={"text": text, "speaker": speaker}, timeout=60)
    q.raise_for_status()
    query = q.json()
    query["speedScale"] = speed
    query["prePhonemeLength"] = 0.05
    query["postPhonemeLength"] = 0.05
    query["volumeScale"] = 1.15
    r = requests.post(f"{ENGINE}/synthesis", params={"speaker": speaker}, json=query, timeout=120)
    r.raise_for_status()
    return r.content


def wav_seconds(data, tmp):
    p = Path(tmp) / "probe.wav"
    p.write_bytes(data)
    with wave.open(str(p)) as w:
        return w.getnframes() / w.getframerate()


def voice_reel(folder):
    meta_path = folder / "narration.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("voiced"):
        return False
    reel = folder / "reel.mp4"
    speaker = meta.get("speaker", 8)
    with tempfile.TemporaryDirectory() as tmp:
        inputs, filters = [], []
        for i, seg in enumerate(meta["segments"]):
            speed = 1.15
            data = synth(seg["text"], speaker, speed)
            length = wav_seconds(data, tmp)
            room = seg["dur"] - 0.25
            if length > room:
                speed = min(1.6, speed * length / room)
                data = synth(seg["text"], speaker, speed)
            clip = Path(tmp) / f"v{i}.wav"
            clip.write_bytes(data)
            inputs += ["-i", str(clip)]
            delay = int((seg["start"] + 0.1) * 1000)
            filters.append(f"[{i + 1}:a]aresample=48000,adelay={delay}|{delay},apad[v{i}]")
            print(f"  seg {i}: {seg['text']} (speed {speed:.2f})")
        n = len(meta["segments"])
        voices = "".join(f"[v{i}]" for i in range(n))
        fc = ";".join(filters) + f";{voices}amix=inputs={n}:normalize=0[vo];" \
             "[0:a]volume=0.35[bgm];[bgm][vo]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]"
        out = Path(tmp) / "out.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(reel), *inputs, "-filter_complex", fc,
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
                        "-movflags", "+faststart", str(out)], check=True)
        reel.write_bytes(out.read_bytes())
    meta["voiced"] = True
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def main():
    done = 0
    for meta in sorted((ROOT / "queue").glob("*/narration.json")):
        print(f"voicing {meta.parent.name}")
        if voice_reel(meta.parent):
            done += 1
    print(f"voiced {done} reel(s)")


if __name__ == "__main__":
    sys.exit(main())
