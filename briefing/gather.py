#!/usr/bin/env python3
"""Pick today's episodes and save their text for the writer.

  gather.py            choose episodes, write work/sources.md and work/selection.json
  gather.py --commit   after a successful run, move the bookmarks in state.json forward

Python standard library only.
"""
import datetime as dt
import html
import json
import os
import re
import sys
import textwrap
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "state.json")
WORK = os.path.join(ROOT, "work")

AIDB_RSS = "https://anchor.fm/s/f7cac464/podcast/rss"
LEX_RSS = "https://lexfridman.com/feed/podcast/"
ACQ_RSS = "https://feeds.transistor.fm/acquired"
ACQ_SITEMAP = "https://www.acquired.fm/sitemap.xml"
TLDR_RSS = "https://tldr.tech/api/rss/ai"
ESPN = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh) morning-briefing/1.0"}

LEX_NEW_DAYS = 14   # a Lex episode this recent jumps ahead of the back catalog
AIDB_MAX = 2        # at most this many AI Daily Brief episodes per briefing

NS = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd",
      "content": "http://purl.org/rss/1.0/modules/content/"}


# ---------------------------------------------------------------- helpers

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        return r.read().decode("utf-8", "replace")


def strip_html(s):
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s or "")
    s = re.sub(r"(?i)<br\s*/?>|</p>|</li>|</h\d>", "\n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    lines = [" ".join(l.split()) for l in s.splitlines()]
    return "\n".join(l for l in lines if l)


def wrap(text, width=180):
    out = []
    for para in text.split("\n"):
        out.append(textwrap.fill(para, width) if para.strip() else "")
    return "\n".join(out)


def slugify(s):
    s = html.unescape(s).lower().replace("&", "and")
    s = re.sub(r"[’'\".]", "", s)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def parse_feed(xml_text):
    root = ET.fromstring(xml_text)
    items = []
    for it in root.iter("item"):
        try:
            when = parsedate_to_datetime(it.findtext("pubDate"))
        except Exception:
            continue
        desc = it.findtext("content:encoded", namespaces=NS) or it.findtext("description") or ""
        items.append({
            "guid": (it.findtext("guid") or it.findtext("link") or it.findtext("title")).strip(),
            "title": html.unescape((it.findtext("title") or "").strip()),
            "link": (it.findtext("link") or "").strip(),
            "date": when,
            "duration": it.findtext("itunes:duration", namespaces=NS) or "",
            "raw": ET.tostring(it, encoding="unicode"),
            "notes_html": desc,
        })
    items.sort(key=lambda i: i["date"])          # oldest first
    return items


def local_now():
    """The listener's local time (Pacific)."""
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo("America/Los_Angeles"))
    except Exception:
        return dt.datetime.now(dt.timezone(dt.timedelta(hours=-8)))


def load_state():
    if os.path.exists(STATE):
        with open(STATE) as f:
            return json.load(f)
    return {"version": 1, "aidb_last": None, "tldr_last": None, "lex_done": [], "acquired_done": [], "history": []}


# ---------------------------------------------------------------- transcript extractors

class _Lex(HTMLParser):
    """lexfridman.com transcript pages: <h2> chapters, then ts-segment blocks of ts-name + ts-text."""
    def __init__(self):
        super().__init__()
        self.out, self.mode, self.buf, self.name = [], None, [], ""

    def handle_starttag(self, tag, attrs):
        cls = dict(attrs).get("class", "") or ""
        if tag == "h2":
            self.mode, self.buf = "h2", []
        elif "ts-name" in cls:
            self.mode, self.buf = "name", []
        elif "ts-text" in cls:
            self.mode, self.buf = "text", []

    def handle_endtag(self, tag):
        if tag in ("h2", "span") and self.mode:
            t = " ".join("".join(self.buf).split())
            if self.mode == "h2" and t:
                self.out.append(f"\n[Chapter: {t}]")
            elif self.mode == "name":
                self.name = t
            elif self.mode == "text" and t:
                self.out.append(f"{self.name}: {t}")
            self.mode = None

    def handle_data(self, d):
        if self.mode:
            self.buf.append(d)


def lex_transcript(url):
    p = _Lex()
    p.feed(get(url))
    # keep only chapter headings that are followed by spoken lines (drops page furniture)
    lines = [l for n, l in enumerate(p.out)
             if not l.startswith("\n[Chapter:")
             or (n + 1 < len(p.out) and not p.out[n + 1].startswith("\n[Chapter:"))]
    return "\n".join(lines).strip()


class _Acq(HTMLParser):
    """acquired.fm episode pages: <article id="transcript"> holding <p> paragraphs."""
    def __init__(self):
        super().__init__()
        self.depth, self.inp, self.out, self.buf = 0, False, [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.depth == 0 and tag == "article" and a.get("id") == "transcript":
            self.depth = 1
        elif self.depth and tag == "article":
            self.depth += 1
        if self.depth and tag == "p":
            self.inp, self.buf = True, []

    def handle_endtag(self, tag):
        if self.depth and tag == "p" and self.inp:
            t = " ".join("".join(self.buf).split())
            if t:
                self.out.append(t)
            self.inp = False
        if self.depth and tag == "article":
            self.depth -= 1

    def handle_data(self, d):
        if self.inp:
            self.buf.append(d)


def acq_transcript(url):
    p = _Acq()
    p.feed(get(url))
    return "\n".join(p.out).strip()


# ---------------------------------------------------------------- choosing episodes

def choose_aidb(state):
    items = parse_feed(get(AIDB_RSS))
    last = dt.datetime.fromisoformat(state["aidb_last"]) if state.get("aidb_last") else None
    new = [i for i in items if last is None or i["date"] > last]
    if last is None:
        new = new[-1:]
    return new[-AIDB_MAX:]


def lex_items():
    out = []
    for i in parse_feed(get(LEX_RSS)):
        m = re.search(r"https?://lexfridman\.com/[a-z0-9-]+-transcript", i["raw"])
        if m:
            i["transcript_url"] = m.group(0)
            out.append(i)
    return out


def choose_lex(state):
    done = set(state.get("lex_done", []))
    todo = [i for i in lex_items() if i["transcript_url"] not in done]
    if not todo:
        return None
    now = dt.datetime.now(dt.timezone.utc)
    newest = todo[-1]
    if (now - newest["date"]).days <= LEX_NEW_DAYS:
        newest["kind"] = "new"
        return newest
    todo[0]["kind"] = "archive"
    return todo[0]


def acq_slugs():
    return re.findall(r"<loc>https://www\.acquired\.fm/episodes/([^<]+)</loc>", get(ACQ_SITEMAP))


def acq_page_for(item, slugs):
    m = re.search(r"acquired\.fm/episodes/([^/?#\s]+)", item["link"])
    if m:
        return "https://www.acquired.fm/episodes/" + m.group(1)
    s = slugify(re.sub(r"(?i)^(acquired )?(episode|ep\.?)\s*\d+\s*[:\-–]\s*", "", item["title"]))
    if not s:
        return None
    exact = [x for x in slugs if x == s]
    numbered = [x for x in slugs if re.fullmatch(r"(acquired-)?(episode|ep)-\d+-" + re.escape(s), x)]
    prefix = [x for x in slugs if re.fullmatch(r"(acquired-)?(episode|ep)-\d+-" + re.escape(s) + r"-.+", x)]
    loose = [x for x in slugs if s in x]
    for group in (exact, numbered, prefix, loose):
        if group:
            return "https://www.acquired.fm/episodes/" + min(group, key=len)
    # Fallback: best word overlap with the title's main part (before "with ..." / parentheses)
    core = re.sub(r"(?i)^special:\s*", "", item["title"])
    core = re.split(r"\s*\(|\s+with\s+|\s+live\s+", core)[0]
    want = set(slugify(core).split("-")) - {"the", "and", "a", "of", "acquired", "episode", "ep"}
    if not want:
        return None
    best, score = None, 0.0
    for x in slugs:
        have = set(x.split("-"))
        hit = len(want & have) / len(want)
        if hit > score or (hit == score and best and len(x) < len(best)):
            best, score = x, hit
    return "https://www.acquired.fm/episodes/" + best if score >= 0.6 else None


def tldr_issue(url):
    """A TLDR AI issue page: sections of articles, each a title and a short summary. Sponsors dropped."""
    page = get(url)
    out = []
    for sec in re.findall(r"(?s)<section>(.*?)</section>", page):
        arts = re.findall(r'(?s)<article.*?<h3>(.*?)</h3>.*?<div class="newsletter-html">(.*?)</div>\s*</article>', sec)
        arts = [(strip_html(t), strip_html(b)) for t, b in arts]
        arts = [(t, b) for t, b in arts if "(sponsor)" not in t.lower()]
        if not arts:
            continue
        h = re.search(r'<h3 class="[^"]*font-bold[^"]*">(.*?)</h3>', sec)
        out.append((strip_html(h.group(1)) if h else "", arts))
    return out


def get_json(url):
    return json.loads(get(url))


# Free over-the-air stations in the San Francisco Bay Area, by network.
SF_STATIONS = {"FOX": "KTVU FOX 2", "CBS": "KPIX CBS 5", "NBC": "KNTV NBC 11", "ABC": "KGO ABC 7"}


def packers_delivery_day(game_local):
    """The briefing day that carries the Packers preview: Friday for a Saturday to Monday game,
    otherwise the day before (Thursday game -> Wednesday)."""
    wd = game_local.weekday()                      # Monday 0 ... Sunday 6
    if wd in (5, 6, 0):
        back = (wd - 4) % 7                        # back to Friday
    else:
        back = 1
    return game_local.date() - dt.timedelta(days=back)


def networks(comp):
    out = []
    for b in comp.get("broadcasts") or []:
        out += b.get("names") or [((b.get("media") or {}).get("shortName"))]
    return [n for n in out if n]


def sf_tv(game, comp, game_utc):
    """Best judgment on whether the game is on free over-the-air TV in the San Francisco market."""
    nets = [n.upper() for n in networks(comp)]
    on_air = [n for n in nets if n in SF_STATIONS]
    if not nets:
        return {"verdict": "unknown", "why": "No network has been announced yet."}
    if not on_air:
        return {"verdict": "no", "why": f"It's on {', '.join(networks(comp))}, which is streaming or cable only "
                "in the Bay Area; local over-the-air simulcasts happen only in the two teams' home markets."}
    net = on_air[0]
    station = SF_STATIONS[net]
    if net in ("NBC", "ABC") or game_utc.astimezone(dt.timezone(dt.timedelta(hours=-5))).weekday() != 6:
        return {"verdict": "yes", "station": station,
                "why": f"{net} carries it nationally, so it's on {station}."}
    # A Sunday afternoon FOX or CBS game: regional unless it's the network's only game in that window.
    day = game_utc.astimezone(dt.timezone(dt.timedelta(hours=-5))).strftime("%Y%m%d")
    board = get_json(f"{ESPN}/scoreboard?dates={day}").get("events", [])
    same_window, niners = [], None
    for e in board:
        c = e["competitions"][0]
        when = dt.datetime.fromisoformat(e["date"].replace("Z", "+00:00"))
        if abs((when - game_utc).total_seconds()) <= 3600 and net in [n.upper() for n in networks(c)]:
            same_window.append(e["shortName"])
        if any(t["team"]["abbreviation"] == "SF" for t in c["competitors"]):
            niners = (e["shortName"], [n.upper() for n in networks(c)], when)
    clash = niners and net in niners[1] and abs((niners[2] - game_utc).total_seconds()) <= 3600 \
        and niners[0] != game["shortName"]
    if clash:
        return {"verdict": "no", "station": station,
                "why": f"The 49ers ({niners[0]}) are on {net} in the same window, so {station} will carry them."}
    if len(same_window) <= 1:
        return {"verdict": "yes", "station": station,
                "why": f"It's {net}'s only game in that window, so it goes out nationally on {station}."}
    note = f"{net} has {len(same_window)} games in that window ({', '.join(same_window)}), so it's regional"
    if niners:
        note += f"; the 49ers play {niners[0]} on {'/'.join(niners[1]) or 'TBD'} that day"
    return {"verdict": "maybe", "station": station,
            "why": note + f". Whether {station} picks the Packers depends on {net}'s coverage map."}


def gather_packers(sel, md, force=False):
    """Packers preview: only on the briefing day before game week's game (see packers_delivery_day)."""
    sel["packers"] = None
    today = local_now()
    events = get_json(f"{ESPN}/teams/gb/schedule").get("events", [])
    upcoming = []
    for e in events:
        when = dt.datetime.fromisoformat(e["date"].replace("Z", "+00:00"))
        if e["competitions"][0]["status"]["type"].get("state") == "pre" and when > today:
            upcoming.append((when, e))
    if not upcoming:
        return
    when, game = min(upcoming, key=lambda x: x[0])
    local = when.astimezone(today.tzinfo)
    due = packers_delivery_day(local)
    if not force and today.date() != due:
        return
    comp = game["competitions"][0]
    summary = get_json(f"{ESPN}/summary?event={game['id']}")
    home = next(t for t in comp["competitors"] if t["homeAway"] == "home")
    away = next(t for t in comp["competitors"] if t["homeAway"] == "away")
    gb_home = home["team"]["abbreviation"] == "GB"
    opp = (away if gb_home else home)["team"]
    odds = None
    for p in summary.get("pickcenter") or []:
        odds = {"source": (p.get("provider") or {}).get("name"), "spread": p.get("details"),
                "over_under": p.get("overUnder"),
                "gb_moneyline": ((p.get("homeTeamOdds") if gb_home else p.get("awayTeamOdds")) or {}).get("moneyLine"),
                "opp_moneyline": ((p.get("awayTeamOdds") if gb_home else p.get("homeTeamOdds")) or {}).get("moneyLine")}
        break
    detail = {}
    for t in summary.get("injuries") or []:
        if t["team"]["abbreviation"] == "GB":
            for i in t.get("injuries") or []:
                a = i.get("athlete") or {}
                what = (i.get("details") or {}).get("type") or (i.get("type") or {}).get("description")
                if what and what.lower() not in (i.get("status") or "").lower():
                    detail[a.get("displayName")] = what
    starters = set()
    try:
        for unit in get_json(f"{ESPN}/teams/gb/depthcharts").get("depthchart", []):
            for pos in unit.get("positions", {}).values():
                if pos.get("athletes"):
                    starters.add(pos["athletes"][0]["displayName"])
    except Exception:
        pass
    hurt = []
    for g in get_json(f"{ESPN}/teams/gb/roster").get("athletes", []):
        for a in g.get("items", []):
            for i in a.get("injuries") or []:
                hurt.append({"name": a["displayName"], "pos": (a.get("position") or {}).get("abbreviation"),
                             "status": i.get("status"), "since": (i.get("date") or "")[:10],
                             "injury": detail.get(a["displayName"]),
                             "years": (a.get("experience") or {}).get("years"),
                             "depth_chart_starter": a["displayName"] in starters})
                break
    tv = sf_tv(game, comp, when)
    time_known = game.get("timeValid", True)
    link = next((l["href"] for l in game.get("links", []) if "gamecast" in (l.get("rel") or [])), None) \
        or f"https://www.espn.com/nfl/game/_/gameId/{game['id']}"
    sel["packers"] = {"game": game["name"], "short": game["shortName"], "link": link,
                      "kickoff_pt": local.isoformat() if time_known else None, "networks": networks(comp),
                      "sf_tv": tv}
    md.append("## SOURCE: Green Bay Packers game preview (ESPN data, fetched this morning)\n")
    md.append(f"- Game: {game['name']} ({'home at ' if gb_home else 'away at '}"
              f"{(summary.get('gameInfo') or {}).get('venue', {}).get('fullName', 'venue TBD')})")
    md.append(f"- Opponent: {opp.get('displayName')}")
    md.append(f"- Kickoff: {local:%A, %B %-d at %-I:%M %p} Pacific" if time_known
              else f"- Kickoff: {local:%A, %B %-d}, time not set yet (the league flexes late-season times)")
    md.append(f"- TV/streaming: {', '.join(networks(comp)) or 'not announced yet'}")
    md.append(f"- On free TV in the San Francisco market: {tv['verdict'].upper()}. {tv['why']}")
    if odds:
        md.append(f"- Odds ({odds['source']}): spread {odds['spread']}, over/under {odds['over_under']}, "
                  f"moneyline Packers {odds['gb_moneyline']}, {opp.get('shortDisplayName')} {odds['opp_moneyline']}")
    else:
        md.append("- Odds: not posted yet")
    for t in comp["competitors"]:
        rec = (t.get("record") or [{}])[0].get("displayValue") if t.get("record") else None
        if rec:
            md.append(f"- Record: {t['team']['displayName']} {rec}")
    md.append("- Packers injuries (status, injury if known, date listed, years in the league, "
              "whether ESPN's depth chart lists him as a starter):")
    for h in sorted(hurt, key=lambda h: (h["status"] != "Out", h["status"] != "Injured Reserve", h["name"])):
        md.append(f"  - {h['name']}, {h['pos']}: {h['status']}" + (f", {h['injury']}" if h["injury"] else "")
                  + f", since {h['since']}, {h['years']} yrs" + (", starter" if h["depth_chart_starter"] else ""))
    keys = ("packers", "green bay", (opp.get("name") or "").lower(), (opp.get("location") or "").lower())
    news = [n.get("headline") for n in (summary.get("news") or {}).get("articles", [])
            if n.get("headline") and any(k and k in n["headline"].lower() for k in keys)][:5]
    if news:
        md.append("- Recent ESPN headlines for context: " + " | ".join(news))
    md.append("")


def acq_items():
    return [i for i in parse_feed(get(ACQ_RSS)) if not i["title"].lower().startswith("trailer")]


# ---------------------------------------------------------------- main

def gather_aidb(state, sel, md):
    """AI Daily Brief: show notes only (it publishes no transcripts)."""
    aidb = choose_aidb(state)
    sel["aidb"] = [{"guid": i["guid"], "title": i["title"], "date": i["date"].isoformat(),
                    "link": i["link"]} for i in aidb]
    md.append("## SOURCE: The AI Daily Brief (show notes only; there is no transcript)\n")
    if not aidb:
        md.append("No new episode since the last briefing.\n")
    for i in aidb:
        md.append(f"### {i['title']}  ({i['date']:%a %b %-d})\n")
        md.append(wrap(strip_html(i["notes_html"])) + "\n")


def gather_tldr(state, sel, md):
    """TLDR AI newsletter: the newest issue not yet covered (weekdays only, so weekends have none)."""
    items = [i for i in parse_feed(get(TLDR_RSS)) if re.search(r"/ai/\d{4}-\d{2}-\d{2}$", i["link"])]
    last = state.get("tldr_last")
    new = [i for i in items if last is None or i["link"].rsplit("/", 1)[1] > last]
    md.append("## SOURCE: TLDR AI newsletter (the full issue; sponsor items already removed)\n")
    sel["tldr"] = None
    if not new:
        md.append("No new issue since the last briefing.\n")
        return
    i = new[-1]
    day = i["link"].rsplit("/", 1)[1]
    sections = tldr_issue(i["link"])
    if not sections:
        raise ValueError(f"no stories found on {i['link']}")
    n = sum(len(a) for _, a in sections)
    words = sum(len(t.split()) + len(b.split()) for _, a in sections for t, b in a)
    sel["tldr"] = {"date": day, "title": i["title"], "link": i["link"], "stories": n, "words": words}
    md.append(f"### TLDR AI, {dt.date.fromisoformat(day):%A, %B %-d}: {i['title']}  ({n} stories)\n")
    for head, arts in sections:
        md.append(f"#### {head or 'Stories'}\n")
        for t, b in arts:
            md.append(f"- **{t}**: {b}")
        md.append("")


def gather_lex(state, sel, md):
    """Lex Fridman: the newest episode if it is recent, otherwise the next one from the back catalog."""
    lex = choose_lex(state)
    md.append("## SOURCE: Lex Fridman Podcast (full transcript)\n")
    sel["lex"] = None
    if not lex:
        md.append("Nothing left to cover today.\n")
        return
    text = lex_transcript(lex["transcript_url"])
    sel["lex"] = {"url": lex["transcript_url"], "title": lex["title"], "kind": lex["kind"],
                  "date": lex["date"].isoformat(), "words": len(text.split())}
    label = "NEW episode" if lex["kind"] == "new" else "From the archive"
    md.append(f"### {lex['title']}  ({label}, released {lex['date']:%B %-d, %Y})\n")
    md.append(wrap(text) + "\n")


def gather_acquired(state, sel, md):
    """Acquired: the next episode in order, starting from the very first."""
    items = acq_items()
    done = set(state.get("acquired_done", []))
    todo = [(n, i) for n, i in enumerate(items, 1) if i["guid"] not in done]
    md.append("## SOURCE: Acquired (oldest-first through the whole catalog)\n")
    sel["acquired"] = None
    if not todo:
        md.append("The whole catalog has been covered and there is no new episode.\n")
        return
    n, acq = todo[0]
    page = acq_page_for(acq, acq_slugs())
    text = acq_transcript(page) if page else ""
    has_t = len(text.split()) > 1500
    if not has_t:
        text = strip_html(acq["notes_html"])
    sel["acquired"] = {"guid": acq["guid"], "title": acq["title"], "page": page,
                       "date": acq["date"].isoformat(), "transcript": has_t,
                       "position": n, "total": len(items), "words": len(text.split())}
    kind = "full transcript" if has_t else "SHOW NOTES ONLY (no transcript published)"
    md.append(f"### {acq['title']}  (episode {n} of {len(items)}, "
              f"released {acq['date']:%B %-d, %Y}; {kind})\n")
    md.append(wrap(text) + "\n")


def gather():
    state = load_state()
    os.makedirs(WORK, exist_ok=True)
    sel, md, errors = {}, [], []
    md.append(f"# Source material for the briefing ({local_now():%A, %B %-d, %Y})\n")
    force_gb = os.environ.get("PACKERS_FORCE") == "1"
    for name, step in (("tldr", gather_tldr), ("aidb", gather_aidb), ("lex", gather_lex),
                       ("acquired", gather_acquired),
                       ("packers", lambda st, se, m: gather_packers(se, m, force_gb))):
        try:
            step(state, sel, md)
        except Exception as e:                      # one site being down should not sink the briefing
            sel[name] = [] if name == "aidb" else None
            errors.append(f"{name}: {type(e).__name__}: {e}")
            md.append(f"(This source could not be fetched today: {e})\n")
    sel["errors"] = errors
    with open(os.path.join(WORK, "sources.md"), "w") as f:
        f.write("\n".join(md))
    with open(os.path.join(WORK, "selection.json"), "w") as f:
        json.dump(sel, f, indent=2)
    print(json.dumps(sel, indent=2))


def commit():
    with open(os.path.join(WORK, "selection.json")) as f:
        sel = json.load(f)
    state = load_state()
    if sel.get("aidb"):
        state["aidb_last"] = max(i["date"] for i in sel["aidb"])
    if sel.get("tldr"):
        state["tldr_last"] = sel["tldr"]["date"]
    if sel.get("lex"):
        state["lex_done"].append(sel["lex"]["url"])
    if sel.get("acquired"):
        state["acquired_done"].append(sel["acquired"]["guid"])
    state["history"].append({
        "date": local_now().date().isoformat(),
        "tldr": (sel.get("tldr") or {}).get("date"),
        "aidb": [i["title"] for i in sel.get("aidb") or []],
        "lex": (sel.get("lex") or {}).get("title"),
        "acquired": (sel.get("acquired") or {}).get("title"),
    })
    with open(STATE, "w") as f:
        json.dump(state, f, indent=2)
    print("Bookmarks moved forward.")


if __name__ == "__main__":
    commit() if "--commit" in sys.argv else gather()
