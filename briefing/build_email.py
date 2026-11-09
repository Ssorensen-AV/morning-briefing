#!/usr/bin/env python3
"""Build the briefing email (work/email.html and work/email.txt).

  build_email.py AUDIO_URL

Reads work/highlights.md, work/audio.json and work/selection.json.
The HTML uses tables and inline styles so it renders the same in Gmail on phone and desktop.
"""
import datetime as dt
import html
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work")

INK, MUTED, RULE, ACCENT, PAPER, CARD = "#14181f", "#5b6472", "#e4e7ec", "#b8862f", "#f4f2ee", "#ffffff"
SERIF = "Georgia,'Times New Roman',serif"
SANS = "-apple-system,BlinkMacSystemFont,'Helvetica Neue',Helvetica,Arial,sans-serif"


def local_today():
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo("America/Los_Angeles")).date()
    except Exception:
        return dt.date.today()


def highlights():
    out, cur = {}, None
    path = os.path.join(WORK, "highlights.md")
    if not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8"):
        if line.startswith("## "):
            cur = line[3:].strip()
            out[cur] = []
        elif cur and re.match(r"\s*[-•*]\s+", line):
            out[cur].append(re.sub(r"^\s*[-•*]\s+", "", line).strip())
    return out


def source_links(sel):
    links = {}
    if sel.get("tldr"):
        links["tldr"] = [(f"TLDR AI: {sel['tldr']['title']}", sel["tldr"]["link"])]
    for i in sel.get("aidb") or []:
        links.setdefault("ai", []).append((f"The AI Daily Brief: {i['title']}", i["link"]))
    if sel.get("lex"):
        links["lex"] = [(f"Lex Fridman {sel['lex']['title']}", sel["lex"]["url"])]
    if sel.get("acquired") and sel["acquired"].get("page"):
        links["acquired"] = [(f"Acquired: {sel['acquired']['title']}", sel["acquired"]["page"])]
    return links


def links_for(title, links):
    t = title.lower()
    if "tldr" in t:
        return links.get("tldr", [])
    if "acquired" in t:
        return links.get("acquired", [])
    if "lex" in t or "deep dive" in t:
        return links.get("lex", [])
    if "ai" in t.split() or "news" in t or "daily brief" in t:
        return links.get("ai", [])
    return []


def build(url):
    audio = json.load(open(os.path.join(WORK, "audio.json")))
    sel = json.load(open(os.path.join(WORK, "selection.json")))
    hl, links = highlights(), source_links(sel)
    day = local_today()
    date_line = f"{day:%A, %B} {day.day}, {day.year}"
    e = html.escape

    chap_rows = "".join(
        f'<tr><td style="padding:6px 0;font:14px {SANS};color:{MUTED};width:56px">{c["start"]}</td>'
        f'<td style="padding:6px 0;font:15px {SANS};color:{INK}">{e(c["title"])}</td>'
        f'<td align="right" style="padding:6px 0;font:13px {SANS};color:{MUTED}">{c["minutes"]} min</td></tr>'
        for c in audio["chapters"])

    blocks = ""
    for c in audio["chapters"]:
        items = hl.get(c["title"])
        if not items:
            continue
        lis = "".join(f'<li style="margin:0 0 8px">{e(i)}</li>' for i in items)
        src = "".join(f'<a href="{e(u)}" style="color:{ACCENT};text-decoration:none">{e(n)} &rarr;</a><br>'
                      for n, u in links_for(c["title"], links))
        blocks += (
            f'<tr><td style="padding:28px 0 0">'
            f'<div style="font:600 11px {SANS};letter-spacing:.14em;text-transform:uppercase;color:{ACCENT}">'
            f'{c["start"]} &middot; {c["minutes"]} min</div>'
            f'<div style="font:22px/1.3 {SERIF};color:{INK};margin:6px 0 12px">{e(c["title"])}</div>'
            f'<ul style="margin:0;padding:0 0 0 18px;font:15px/1.55 {SANS};color:{INK}">{lis}</ul>'
            f'<div style="font:13px/1.7 {SANS};margin-top:10px">{src}</div></td></tr>')

    acq = sel.get("acquired")
    progress = (f"Acquired catalog: episode {acq['position']} of {acq['total']}" if acq else "")
    html_out = f"""<!doctype html><html><head><meta name="color-scheme" content="light dark"><meta name="supported-color-schemes" content="light dark"></head>
<body style="margin:0;padding:0;background-color:{PAPER}" bgcolor="{PAPER}">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{PAPER}" style="background-color:{PAPER}"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="{CARD}" style="max-width:600px;background-color:{CARD};border-radius:14px;overflow:hidden">
<tr><td bgcolor="{INK}" style="background-color:{INK};background-image:linear-gradient({INK},{INK});padding:32px 32px 28px;border-radius:14px 14px 0 0">
  <div style="font:600 11px {SANS};letter-spacing:.2em;text-transform:uppercase;color:{ACCENT}">Morning Briefing</div>
  <div style="font:30px/1.2 {SERIF};color:#ffffff;margin-top:8px">{e(date_line)}</div>
  <div style="font:14px {SANS};color:#aab2bf;margin-top:6px">{audio["minutes"]} minutes &middot; read by Cori</div>
  <table role="presentation" cellpadding="0" cellspacing="0" style="margin-top:22px"><tr>
    <td bgcolor="{ACCENT}" style="background-color:{ACCENT};border-radius:999px"><a href="{e(url)}" target="_blank"
      style="display:inline-block;padding:13px 26px;background-color:{ACCENT};border:1px solid {ACCENT};border-radius:999px;font:600 15px {SANS};color:{INK};text-decoration:none">&#9654;&nbsp; Listen now</a></td></tr></table>
</td></tr>
<tr><td style="padding:24px 32px 4px">
  <div style="font:600 11px {SANS};letter-spacing:.14em;text-transform:uppercase;color:{MUTED};margin-bottom:6px">In this briefing</div>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-top:1px solid {RULE}">{chap_rows}</table>
</td></tr>
<tr><td style="padding:0 32px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0">{blocks}</table></td></tr>
<tr><td style="padding:32px;font:12px/1.6 {SANS};color:{MUTED}">
  <div style="border-top:1px solid {RULE};padding-top:16px">{e(progress)}<br>
  The Listen button opens the audio in your browser; no sign-in needed.</div>
</td></tr></table></td></tr></table></body></html>"""

    txt = [f"MORNING BRIEFING: {date_line}", f"{audio['minutes']} minutes. Listen: {url}", ""]
    for c in audio["chapters"]:
        txt.append(f"{c['start']}  {c['title']} ({c['minutes']} min)")
        txt += [f"  - {i}" for i in hl.get(c["title"], [])]
        txt += [f"  {n}: {u}" for n, u in links_for(c["title"], links)]
    if progress:
        txt += ["", progress]

    open(os.path.join(WORK, "email.html"), "w").write(html_out)
    open(os.path.join(WORK, "email.txt"), "w").write("\n".join(txt) + "\n")
    print(f"Subject: Morning Briefing: {date_line}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    build(sys.argv[1])
