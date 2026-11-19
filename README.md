# Morning Briefing

A daily audio briefing, up to 30 minutes long, read by the Cori voice. It's built from:

- **AI:** the TLDR AI newsletter (read in full), The Neuron (daily newsletter, from Gmail), Last Week in AI (a weekly roundup when a new issue is out, plus occasional "From the archive" filler), and Lex Fridman (full transcripts; new episodes first, otherwise his back catalog).
- **Acquired:** the whole catalog in order, one episode a day, starting with Pixar (2015).
- **Packers:** a game-week preview with the storyline, odds, injuries, kickoff and San Francisco TV.

A claude.ai cloud routine runs every morning. It follows `ROUTINE.md` and sends the finished briefing by Gmail to the one recipient named in the routine's own settings. No email address is kept in this repository.

| File | What it does |
|---|---|
| `briefing/gather.py` | Picks today's episodes and fetches their text. `--commit` moves the bookmarks forward. |
| `briefing/newsletters.py` | The Neuron and Last Week in AI sections: `plan`, `build` (`--dry-run` prints the segments and changes nothing), and `commit`. |
| `briefing/STYLE.md` | How the briefing is written. Edit this to change the tone or length. |
| `briefing/speak.py` | Records the script with Piper (Cori voice) into one MP3, with a chapter per section. |
| `briefing/publish.py` | Puts the MP3 on the `audio` branch, keeping the newest 14, and prints its link. |
| `briefing/build_email.py` | Builds the HTML email. |
| `briefing/config.json` | Settings, below. |
| `state.json` | The bookmarks: what has already been covered, including the Last Week in AI issues and archive stories used. |
| `scripts/` | The text of every briefing. |

## Newsletter settings (`briefing/config.json`)

| Setting | Default | Meaning |
|---|---|---|
| `neuron_sender` | `theneuron@newsletter.theneurondaily.com` | The address The Neuron arrives from. Confirmed from the inbox. |
| `neuron_thin_words` | `400` | If today's Neuron has fewer words than this after cleaning (or none arrived), the day counts as thin and may get archive filler. |
| `neuron_retry_minutes` | `15` | How long the run keeps checking Gmail for today's Neuron, every 5 minutes, before skipping it. |
| `lwiai_feed` | `https://lastweekin.ai/feed` | The Last Week in AI Substack feed. |
| `lwiai_sender` | `lastweekinai@substack.com` | Its email address. Gmail is used when the feed has only a preview of a paid-gated issue, or when the feed is down. |
| `lwiai_new_days` | `21` | An unused issue up to this many days old still counts as new and becomes the Weekly Roundup. |
| `filler_days_per_week` | `2` | The most "From the archive" segments in any 7 days. Filler runs only on thin days with no new weekly issue. |
| `archive_window_days` | `[14, 90]` | Archive issues are picked from this age range when possible (older ones only if none are left). |
| `to` | `[]` | Only used if the routine names no recipient. Leave it empty: this repository is public. |

Gmail access comes from the routine's claude.ai Gmail connector, so there are no credentials here. Python can't read mail itself: `newsletters.py plan` lists the searches, the routine saves each message to `work/mail/`, and `build` cleans it.

### Trying it locally

```bash
python3 briefing/newsletters.py plan
# save today's Neuron to work/mail/neuron.txt ("Subject: ..." and "Date: ..." lines, a blank line, then the body)
python3 briefing/newsletters.py build --dry-run
```
