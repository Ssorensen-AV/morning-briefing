#!/usr/bin/env python3
"""Put today's MP3 on the repo's `audio` branch and print its listening link.

  publish.py work/briefing.mp3 2026-11-08

The `audio` branch is rebuilt each day with only the newest KEEP files and no history,
so the repository stays small. If the force-push is refused, the file goes into
audio/ on main instead.
"""
import os
import shutil
import subprocess
import sys
import tempfile

REPO = "Ssorensen-AV/morning-briefing"
KEEP = 14


def git(*args, cwd=None, ok=False):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode and not ok:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r


def via_audio_branch(mp3, day):
    tmp = tempfile.mkdtemp()
    try:
        git("fetch", "origin", "audio", ok=True)
        git("worktree", "add", "--detach", tmp, "HEAD")
        git("checkout", "--orphan", "audio-new", cwd=tmp)
        git("rm", "-rfq", ".", cwd=tmp, ok=True)
        if git("rev-parse", "-q", "--verify", "origin/audio", ok=True).returncode == 0:
            git("checkout", "origin/audio", "--", ".", cwd=tmp, ok=True)
        shutil.copy(mp3, os.path.join(tmp, f"{day}.mp3"))
        files = sorted(f for f in os.listdir(tmp) if f.endswith(".mp3"))
        for old in files[:-KEEP]:
            os.remove(os.path.join(tmp, old))
        files = files[-KEEP:]
        with open(os.path.join(tmp, "README.md"), "w") as f:
            f.write("# Morning Briefing audio\n\nThe newest briefings. Older ones drop off automatically.\n\n")
            f.writelines(f"- [{x[:-4]}]({x})\n" for x in reversed(files))
        git("add", "-A", cwd=tmp)
        git("commit", "-qm", f"Briefing audio {day}", cwd=tmp)
        git("push", "-f", "origin", "audio-new:audio", cwd=tmp)
        return f"https://github.com/{REPO}/raw/audio/{day}.mp3"
    finally:
        git("worktree", "remove", "--force", tmp, ok=True)
        git("branch", "-D", "audio-new", ok=True)
        shutil.rmtree(tmp, ignore_errors=True)


def via_main(mp3, day):
    os.makedirs("audio", exist_ok=True)
    shutil.copy(mp3, f"audio/{day}.mp3")
    files = sorted(f for f in os.listdir("audio") if f.endswith(".mp3"))
    for old in files[:-KEEP]:
        git("rm", "-q", f"audio/{old}", ok=True)
    git("add", "audio")
    git("commit", "-qm", f"Briefing audio {day}")
    git("push", "origin", "HEAD:main")
    return f"https://github.com/{REPO}/raw/main/audio/{day}.mp3"


if __name__ == "__main__":
    mp3, day = sys.argv[1], sys.argv[2]
    try:
        url = via_audio_branch(mp3, day)
    except RuntimeError as e:
        print(f"audio branch failed ({e}); using main instead", file=sys.stderr)
        url = via_main(mp3, day)
    print(url)
