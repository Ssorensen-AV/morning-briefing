#!/usr/bin/env python3
"""Turn work/script.md into one MP3 with a chapter per section, read by the Cori voice.

  speak.py OUT.mp3

script.md: each section starts with a "## Title" line, and the spoken text follows it.
Any "# ..." line is ignored. Needs the `piper` command and ffmpeg.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work")
VOICE = "en_GB-cori-high"
VOICE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/cori/high/"
VOICE_DIR = os.path.expanduser("~/.cache/piper-voices")
RATE = 22050          # Cori's native sample rate
BITRATE = "48k"       # mono speech: about 6 MB for 20 minutes


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        sys.exit(f"Command failed: {' '.join(cmd[:3])}...\n{r.stderr[-2000:]}")
    return r.stdout


def voice_model():
    os.makedirs(VOICE_DIR, exist_ok=True)
    model = os.path.join(VOICE_DIR, VOICE + ".onnx")
    for name in (VOICE + ".onnx", VOICE + ".onnx.json"):
        path = os.path.join(VOICE_DIR, name)
        if not os.path.exists(path) or os.path.getsize(path) < 1000:
            urllib.request.urlretrieve(VOICE_URL + name, path)
    return model


def piper_cmd():
    exe = shutil.which("piper")
    if exe:
        return [exe]
    for py in ("python3.13", "python3.12", "python3"):
        if shutil.which(py) and subprocess.run([py, "-c", "import piper"], capture_output=True).returncode == 0:
            return [py, "-m", "piper"]
    sys.exit("Piper is not installed (pip install piper-tts).")


def sections(path):
    title, buf, out = None, [], []
    for line in open(path, encoding="utf-8"):
        if line.startswith("## "):
            if title is not None:
                out.append((title, "\n".join(buf).strip()))
            title, buf = line[3:].strip(), []
        elif line.startswith("# ") and title is None:
            continue
        else:
            buf.append(line.rstrip("\n"))
    if title is not None:
        out.append((title, "\n".join(buf).strip()))
    return [(t, s) for t, s in out if s]


def speakable(text):
    """Strip markdown and smooth punctuation that TTS stumbles over."""
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)         # links -> their text
    t = re.sub(r"[*_`#>]+", "", t)
    t = t.replace("—", ", ").replace("–", " to ").replace("…", "...")
    t = re.sub(r"(?m)^\s*[-•]\s+", "", t)
    t = re.sub(r"\n{2,}", "\n", t)
    return t.strip()


def duration(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "default=nw=1:nk=1", path]).strip())


def main(out_mp3):
    secs = sections(os.path.join(WORK, "script.md"))
    if not secs:
        sys.exit("work/script.md has no '## ' sections.")
    model, piper = voice_model(), piper_cmd()
    tmp = tempfile.mkdtemp()
    fmt = ["-ar", str(RATE), "-ac", "1", "-c:a", "pcm_s16le"]

    # A soft two-note chime between sections, and short silences around it.
    chime = os.path.join(tmp, "chime.wav")
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
         "sine=f=659.25:d=0.22,afade=t=out:st=0.05:d=0.17", "-f", "lavfi", "-i",
         "sine=f=987.77:d=0.45,afade=t=out:st=0.08:d=0.37", "-filter_complex",
         "[0][1]concat=n=2:v=0:a=1,volume=0.18", *fmt, chime])
    gap = os.path.join(tmp, "gap.wav")
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"anullsrc=r={RATE}:cl=mono",
         "-t", "0.7", *fmt, gap])

    parts, chapters, t = [], [], 0.0
    for n, (title, text) in enumerate(secs):
        wav = os.path.join(tmp, f"s{n}.wav")
        raw = os.path.join(tmp, f"r{n}.wav")
        said = speakable(text)
        r = subprocess.run(piper + ["-m", model, "-f", raw, "--sentence-silence", "0.3"],
                           input=said, text=True, capture_output=True)
        if r.returncode or not os.path.exists(raw):          # older/newer CLI without that flag
            r = subprocess.run(piper + ["-m", model, "-f", raw], input=said, text=True, capture_output=True)
        if r.returncode or not os.path.exists(raw):
            sys.exit(f"Piper failed on section '{title}':\n{r.stderr[-2000:]}")
        run(["ffmpeg", "-y", "-v", "error", "-i", raw, *fmt, wav])
        lead = [chime, gap] if n else []
        start = t
        for p in lead + [wav, gap]:
            parts.append(p)
            t += duration(p)
        chapters.append({"title": title, "start": start, "end": t})

    listing = os.path.join(tmp, "list.txt")
    with open(listing, "w") as f:
        f.writelines(f"file '{p}'\n" for p in parts)
    meta = os.path.join(tmp, "meta.txt")
    with open(meta, "w") as f:
        f.write(";FFMETADATA1\ntitle=Morning Briefing\nartist=Morning Briefing\n")
        for c in chapters:
            f.write(f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={int(c['start']*1000)}\n"
                    f"END={int(c['end']*1000)}\ntitle={c['title']}\n")

    os.makedirs(os.path.dirname(os.path.abspath(out_mp3)), exist_ok=True)
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", listing,
         "-i", meta, "-map", "0:a", "-map_metadata", "1", "-map_chapters", "1",
         "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-ar", str(RATE), "-ac", "1",
         "-c:a", "libmp3lame", "-b:a", BITRATE, "-id3v2_version", "3", out_mp3])
    shutil.rmtree(tmp, ignore_errors=True)

    summary = {"file": out_mp3, "minutes": round(t / 60, 1),
               "chapters": [{"title": c["title"], "start": f"{int(c['start']//60)}:{int(c['start']%60):02d}",
                             "minutes": round((c["end"] - c["start"]) / 60, 1)} for c in chapters]}
    with open(os.path.join(WORK, "audio.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
