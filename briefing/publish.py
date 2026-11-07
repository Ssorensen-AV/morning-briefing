#!/usr/bin/env python3
"""Put today's MP3 on the repo's `audio` branch and print its listening link.

  publish.py work/briefing.mp3 2026-11-08

The `audio` branch is rebuilt each day with only the newest KEEP files and no history,
so the repository stays small. GitHub Pages serves that branch, so the link plays in
any browser or phone. If the force-push is refused, the file goes into audio/ on main.
"""
import os
import shutil
import subprocess
import sys
import tempfile

REPO = "Ssorensen-AV/morning-briefing"
PAGES = "https://ssorensen-av.github.io/morning-briefing"
KEEP = 14


def git(*args, cwd=None, ok=False):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode and not ok:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r


def archive_page(files):
    """A small dark player page listing the briefings on the audio branch."""
    import datetime as dt
    rows = ""
    for x in reversed(files):
        d = dt.date.fromisoformat(x[:-4])
        rows += (f'<li><div class="d">{d:%A, %B} {d.day}, {d.year}</div>'
                 f'<audio controls preload="none" src="{x}"></audio></li>\n')
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Morning Briefing</title>
<style>
body{{margin:0;background:#14181f;color:#fff;font:16px -apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif}}
main{{max-width:600px;margin:0 auto;padding:40px 16px}}
.k{{font-weight:600;font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:#b8862f}}
h1{{font:30px/1.2 Georgia,serif;margin:8px 0 28px}}
ul{{list-style:none;margin:0;padding:0}} li{{padding:16px 0;border-top:1px solid #2a313d}}
.d{{font:18px Georgia,serif;margin-bottom:10px}} audio{{width:100%}}
</style></head><body><main><div class="k">Morning Briefing</div><h1>Recent briefings</h1>
<ul>
{rows}</ul></main></body></html>
"""


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
        with open(os.path.join(tmp, "index.html"), "w") as f:
            f.write(archive_page(files))
        open(os.path.join(tmp, ".nojekyll"), "w").close()
        git("add", "-A", cwd=tmp)
        git("commit", "-qm", f"Briefing audio {day}", cwd=tmp)
        git("push", "-f", "origin", "audio-new:audio", cwd=tmp)
        return f"{PAGES}/{day}.mp3"
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
