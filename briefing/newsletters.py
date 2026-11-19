#!/usr/bin/env python3
"""The AI newsletter segments: The Neuron (daily), Last Week in AI (weekly roundup) and archive filler.

  newsletters.py plan              decide today's issues; write work/newsletters_plan.json
                                   (the Gmail messages the routine must fetch, and where to save them)
  newsletters.py build [--dry-run] clean the saved text into segments and add them to work/sources.md;
                                   --dry-run only prints the segments and changes nothing
  newsletters.py commit            after a successful run, record the issues and archive stories used

The routine fetches mail itself (Python has no Gmail access): for each entry in the plan's "fetch"
list it runs the Gmail search, takes the newest match, and saves the message to the given file as
"Subject: ...", "Date: ...", a blank line, then the plain-text body.
Python standard library only. Settings live in briefing/config.json (see README.md).
"""
import datetime as dt
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gather import NS, STATE, WORK, ET, get, load_state, local_now, strip_html, wrap  # noqa: E402

CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
PLAN = os.path.join(WORK, "newsletters_plan.json")
SEL = os.path.join(WORK, "newsletters.json")
MAIL = os.path.join(WORK, "mail")
USED_FILE = os.path.join(WORK, "archive_used.json")   # written by the writer: the archive stories it used

DEFAULTS = {
    "neuron_sender": "theneuron@newsletter.theneurondaily.com",
    "neuron_thin_words": 400,          # below this, today's Neuron counts as thin
    "neuron_retry_minutes": 15,
    "lwiai_feed": "https://lastweekin.ai/feed",
    "lwiai_sender": "lastweekinai@substack.com",
    "lwiai_new_days": 21,              # an unused issue this recent is still "new"
    "filler_days_per_week": 2,         # most archive segments in any 7 days
    "archive_window_days": [14, 90],   # prefer archive issues this many days old
}

PROMPT = """You're writing the AI news segment of Scott's morning brief. Scott is an operations manager who follows the AI industry and uses AI tools in his own projects, including home automation and workflow automation. From the newsletter text below, pick the 4–6 most important items. For each one, write the headline in plain words and 1–2 sentences on what happened and why it matters. Put model releases, major company moves (OpenAI, Anthropic, Google, Nvidia, etc.) and practical new tools first. Skip sponsored content, promos and filler. Don't invent anything that isn't in the text. Keep the whole segment under about 250 words so it reads well aloud."""
MODE_NOTES = {
    "daily": "",
    "weekly_roundup": "For this weekly_roundup, allow up to 8 items and about 400 words.",
    "archive": 'For this archive segment, use 2–3 items, and open with "From the archive, {date}:".',
}
HEADINGS = {"daily": "The Neuron", "weekly_roundup": "Weekly Roundup: Last Week in AI",
            "archive": "From the Archive"}


def config():
    cfg = dict(DEFAULTS)
    if os.path.exists(CONFIG):
        with open(CONFIG) as f:
            cfg.update({k: v for k, v in json.load(f).items() if v not in (None, "")})
    return cfg


def log(msg):
    print(f"[newsletters] {msg}", file=sys.stderr)


def nl_state(state):
    return state.setdefault("newsletters", {"used": [], "archive_days": [], "archive_stories": []})


def say_date(d):
    return f"{d:%B} {d.day}, {d.year}"


# ---------------------------------------------------------------- cleaning

SPONSOR = re.compile(r"(?i)^\W*(from our partners?|together with|presented by|brought to you by|in partnership with|"
                     r"sponsored( by)?|sponsor(ed)? content|a word from our sponsors?|partners?\s*$)\b")
CTA = re.compile(r"(?i)(advertise (to|with|in front)|click here|request it here|read more\W*$|get the report|rsvp|"
                 r"save your spot|\bsign up (here|for|now|today)\b|\bsubscribe (here|now|today|to (the|our))\b|"
                 r"\bunsubscribe\b|update your (email )?preferences|share the neuron|\brefer (a friend|your)|"
                 r"\breferral\b|view (this|in) (email|browser)|your browser does not support|login or subscribe|"
                 r"forward(ed)? (this|to a friend)|^caption:|^view image:|^download the report|\bfree for \d+ days\b)")
FOOTER = re.compile(r"(?i)^(that['’]s all for now|a cat['’]s commentary|what'?d you think|p\.?s\.?\b|©|"
                    r"the neuron$|don't fall behind on ai|you are receiving|you're receiving)")
DROP_SECTIONS = re.compile(r"(?i)(upcoming event|the neuron irl|new from the neuron: ai explained|"
                           r"new episodes air)")


def is_heading(line):
    s = line.strip()
    return s.startswith("#") or (s.startswith("**") and s.endswith("**") and len(s) < 160)


def plain(line):
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", line)                 # images
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)                # links -> text
    s = re.sub(r"https?://\S+", "", s)                             # bare and tracking URLs
    s = re.sub(r"^#+\s*", "", re.sub(r"[*_`]+", "", s)).strip(" -•|")
    return " ".join(s.split())


def clean_newsletter(text):
    """Turn newsletter plain text (markdown-ish) into readable text without ads, promos or footers."""
    out, skip = [], None          # skip: None, "sponsor-head" (until the sponsor's heading), "section"
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if FOOTER.search(plain(line)):
            break
        if SPONSOR.search(plain(line)) and len(plain(line)) < 60:
            skip = "sponsor-head"
            continue
        if is_heading(line):
            if skip == "sponsor-head":
                skip = "section"          # the sponsor's own heading: drop it and its body
                continue
            skip = "section" if DROP_SECTIONS.search(plain(line)) or "(sponsor)" in line.lower() else None
            if skip:
                continue
        elif skip:
            continue
        p = plain(line)
        if not p or CTA.search(p) or re.fullmatch(r"[\W\d_]+", p):
            continue
        out.append(("## " if is_heading(line) else "") + p)
    return "\n".join(out)


def clean_lwiai(text):
    """Last Week in AI: drop each story's list of source headlines ("Sources:" ... "Source"), then clean."""
    out, in_sources = [], False
    for line in text.splitlines():
        s = line.strip()
        if re.fullmatch(r"(?i)sources?:", s):
            in_sources = True
            continue
        if in_sources:
            if len(s.split()) < 25:
                continue
            in_sources = False
            s = re.sub(r"^Source\s+", "", s)
        out.append(s)
    return clean_newsletter("\n".join(out))


def read_mail(path):
    """A saved message: header lines (Subject:, Date:), a blank line, then the body."""
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    head, _, body = raw.partition("\n\n")
    meta = dict(re.findall(r"(?m)^(Subject|Date):\s*(.*)$", head))
    return {"subject": meta.get("Subject", ""), "date": meta.get("Date", ""), "body": body.strip()}


# ---------------------------------------------------------------- Last Week in AI

def lwiai_posts(feed_url):
    """All posts in the Substack feed, newest first, with their feed text and whether it is complete."""
    root = ET.fromstring(get(feed_url))
    posts = []
    for it in root.iter("item"):
        title = html.unescape((it.findtext("title") or "").strip())
        body = it.findtext("content:encoded", namespaces=NS) or it.findtext("description") or ""
        text = strip_html(body)
        try:
            from email.utils import parsedate_to_datetime
            when = parsedate_to_datetime(it.findtext("pubDate"))
        except Exception:
            continue
        m = re.search(r"#\s*(\d+)", title)
        posts.append({
            "title": title, "url": (it.findtext("link") or "").strip(), "date": when.date().isoformat(),
            "number": m.group(1) if m else None,
            "kind": "podcast" if re.match(r"(?i)lwiai podcast", title) else "newsletter",
            "text": text, "words": len(text.split()),
            "complete": len(text.split()) >= 300 and not re.search(r"(?i)(read more|continue reading)\s*$", text.strip()),
        })
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def used_urls(ns):
    return {u["url"] for u in ns["used"]}


def pick_weekly(posts, ns, cfg, today):
    """The newest newsletter issue that is recent and not used yet."""
    used = used_urls(ns)
    for p in posts:
        if p["kind"] != "newsletter":
            continue
        age = (today - dt.date.fromisoformat(p["date"])).days
        if age > cfg["lwiai_new_days"]:
            return None
        if p["url"] not in used:
            return p
    return None


def pick_archive(posts, ns, cfg, today, exclude):
    """An older, unused post with complete feed text, preferring the archive window."""
    lo, hi = cfg["archive_window_days"]
    used = used_urls(ns) | {exclude}
    ok = [p for p in posts if p["complete"] and p["url"] not in used
          and (today - dt.date.fromisoformat(p["date"])).days >= lo]
    inside = [p for p in ok if (today - dt.date.fromisoformat(p["date"])).days <= hi]
    return (inside or ok or [None])[0]


def filler_allowed(ns, cfg, today):
    week = [d for d in ns["archive_days"] if 0 <= (today - dt.date.fromisoformat(d)).days < 7]
    return len(week) < cfg["filler_days_per_week"]


# ---------------------------------------------------------------- commands

def plan():
    cfg, today = config(), local_now().date()
    ns = nl_state(load_state())
    os.makedirs(MAIL, exist_ok=True)
    out = {"date": today.isoformat(), "fetch": [], "weekly": None, "archive": None, "log": []}
    after = f"{today:%Y/%m/%d}"
    out["fetch"].append({"name": "neuron", "query": f"from:{cfg['neuron_sender']} after:{after}",
                         "file": os.path.relpath(os.path.join(MAIL, "neuron.txt"), os.path.dirname(WORK)),
                         "retry_minutes": cfg["neuron_retry_minutes"],
                         "note": "Today's issue only. If nothing matches, wait about 5 minutes and search again, "
                                 "until retry_minutes have passed; then skip it."})
    try:
        posts = lwiai_posts(cfg["lwiai_feed"])
    except Exception as e:
        posts = []
        out["log"].append(f"Last Week in AI feed failed ({type(e).__name__}: {e}); using Gmail only")
    weekly = pick_weekly(posts, ns, cfg, today)
    if weekly:
        out["weekly"] = {k: weekly[k] for k in ("title", "url", "date", "number", "complete")}
        if not weekly["complete"]:
            q = f'from:{cfg["lwiai_sender"]} subject:"#{weekly["number"]}"' if weekly["number"] \
                else f'from:{cfg["lwiai_sender"]} newer_than:21d'
            out["fetch"].append({"name": "lwiai_weekly", "query": q,
                                 "file": os.path.relpath(os.path.join(MAIL, "lwiai_weekly.txt"), os.path.dirname(WORK)),
                                 "retry_minutes": 0,
                                 "note": "The feed has only a preview of this issue; the email has the full text."})
    elif not posts:
        # Feed is down: a recent issue email that hasn't been used yet can still be the weekly roundup.
        out["fetch"].append({"name": "lwiai_weekly", "query": f'from:{cfg["lwiai_sender"]} newer_than:{cfg["lwiai_new_days"]}d "in AI #"',
                             "file": os.path.relpath(os.path.join(MAIL, "lwiai_weekly.txt"), os.path.dirname(WORK)),
                             "retry_minutes": 0, "note": "Feed fallback: the newest issue email, if any."})
    arch = pick_archive(posts, ns, cfg, today, weekly["url"] if weekly else None)
    if arch:
        out["archive"] = {k: arch[k] for k in ("title", "url", "date", "kind")}
        with open(os.path.join(MAIL, "lwiai_archive.txt"), "w", encoding="utf-8") as f:
            f.write(f"Subject: {arch['title']}\nDate: {arch['date']}\n\n{arch['text']}\n")
    if weekly and weekly["complete"]:
        with open(os.path.join(MAIL, "lwiai_weekly.txt"), "w", encoding="utf-8") as f:
            f.write(f"Subject: {weekly['title']}\nDate: {weekly['date']}\n\n{weekly['text']}\n")
    with open(PLAN, "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps(out, indent=2))


def segment(mode, source, date, text, extra=""):
    note = MODE_NOTES[mode].format(date=date)
    return (f"## SOURCE: {source} ({mode}) -> script section `## {HEADINGS[mode]}`\n\n"
            f"{PROMPT}\n{note}\n{extra}\n\nSource: {source}, {date} Mode: {mode}\n\n{wrap(text)}\n")


def build(dry_run=False):
    cfg, today = config(), local_now().date()
    ns = nl_state(load_state())
    with open(PLAN) as f:
        p = json.load(f)
    logs, segs, sel = list(p.get("log", [])), [], {"neuron": None, "lwiai_weekly": None, "lwiai_archive": None}
    base = os.path.dirname(WORK)

    mail = read_mail(os.path.join(MAIL, "neuron.txt"))
    neuron_words = 0
    if mail and mail["body"]:
        text = clean_newsletter(mail["body"])
        neuron_words = len(text.split())
        date = say_date(today)
        segs.append(segment("daily", "The Neuron", date, text,
                            "TLDR AI is read earlier in the brief: if a story was already covered there, "
                            "give it one short line or pick the next item."))
        sel["neuron"] = {"subject": mail["subject"], "date": today.isoformat(), "words": neuron_words,
                         "link": "https://www.theneurondaily.com/"}
    else:
        logs.append("The Neuron: no issue from today in Gmail; section skipped")
    thin = neuron_words < cfg["neuron_thin_words"]

    weekly_mail = read_mail(os.path.join(MAIL, "lwiai_weekly.txt"))
    if weekly_mail and len(strip_html(weekly_mail["body"]).split()) >= 300:
        info = p.get("weekly") or {"title": weekly_mail["subject"], "url": None, "date": weekly_mail["date"][:10]}
        try:
            d = say_date(dt.date.fromisoformat(info["date"][:10]))
        except ValueError:
            d = info["date"]
        segs.append(segment("weekly_roundup", "Last Week in AI", d, clean_lwiai(strip_html(weekly_mail["body"]))))
        sel["lwiai_weekly"] = {"title": info["title"], "url": info["url"] or f"subject:{weekly_mail['subject']}",
                               "date": info["date"][:10], "link": info["url"] or "https://lastweekin.ai/"}
    elif p.get("weekly"):
        logs.append(f"Last Week in AI: new issue {p['weekly']['title']!r} has no full text yet (feed preview only, "
                    "no email found); it stays unused for a later day")

    arch = p.get("archive")
    if thin and not sel["lwiai_weekly"] and arch and filler_allowed(ns, cfg, today):
        amail = read_mail(os.path.join(MAIL, "lwiai_archive.txt"))
        d = say_date(dt.date.fromisoformat(arch["date"]))
        avoid = ns.get("archive_stories", [])[-60:]
        extra = ("This is archive content: say clearly it's from the " + d + " issue, not today's news. "
                 "Pick only stories that still matter today; skip anything clearly out of date. "
                 "After writing, save the headlines you used as a JSON list of strings to work/archive_used.json.")
        if avoid:
            extra += " Don't repeat any of these stories used in earlier archive segments: " + "; ".join(avoid)
        segs.append(segment("archive", "Last Week in AI", d, clean_lwiai(amail["body"]), extra))
        sel["lwiai_archive"] = {"title": arch["title"], "url": arch["url"], "date": arch["date"], "link": arch["url"]}
    elif thin and not sel["lwiai_weekly"]:
        logs.append("Archive filler: skipped (" + ("no unused older issue" if not arch else
                    "already used the configured filler days this week") + ")")

    for line in logs:
        log(line)
    if dry_run:
        print("\n\n".join(segs) if segs else "(no newsletter segments today)")
        print("\n--- selection ---\n" + json.dumps(sel, indent=2))
        return
    sel["log"] = logs
    with open(SEL, "w") as f:
        json.dump(sel, f, indent=2)
    if segs:
        with open(os.path.join(WORK, "sources.md"), "a", encoding="utf-8") as f:
            f.write("\n\n" + "\n\n".join(segs))
    print(json.dumps(sel, indent=2))


def commit():
    if not os.path.exists(SEL):
        print("No newsletter selection to record.")
        return
    with open(SEL) as f:
        sel = json.load(f)
    state = load_state()
    ns = nl_state(state)
    today = local_now().date().isoformat()
    for key, mode in (("lwiai_weekly", "weekly_roundup"), ("lwiai_archive", "archive")):
        item = sel.get(key)
        if item and item["url"] not in used_urls(ns):
            ns["used"].append({"url": item["url"], "title": item["title"], "date": item["date"],
                               "mode": mode, "used_on": today})
    if sel.get("lwiai_archive"):
        ns["archive_days"].append(today)
        stories = []
        if os.path.exists(USED_FILE):
            try:
                with open(USED_FILE) as f:
                    stories = [s for s in json.load(f) if isinstance(s, str)]
            except ValueError:
                pass
        for u in ns["used"]:
            if u["url"] == sel["lwiai_archive"]["url"]:
                u["stories"] = stories
        ns["archive_stories"] = (ns.get("archive_stories", []) + stories)[-200:]
    ns["archive_days"] = ns["archive_days"][-30:]
    with open(STATE, "w") as f:
        json.dump(state, f, indent=2)
    print("Newsletter bookmarks moved forward.")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "plan":
        plan()
    elif cmd == "build":
        build(dry_run="--dry-run" in sys.argv)
    elif cmd == "commit":
        commit()
    else:
        sys.exit(__doc__)
