# Morning Briefing

A daily audio briefing, about 20 minutes long, read by the Cori voice. It's built from:

- **AI:** The AI Daily Brief (show notes), plus Lex Fridman (full transcripts). New Lex episodes come first; otherwise it works through his back catalog.
- **Acquired:** the whole catalog in order, one episode a day, starting with Pixar (2015).

A claude.ai cloud routine runs every morning. It follows `ROUTINE.md`, and the finished briefing lands in Gmail **Drafts**. Nothing is sent automatically.

| File | What it does |
|---|---|
| `briefing/gather.py` | Picks today's episodes and fetches their text. `--commit` moves the bookmarks forward. |
| `briefing/STYLE.md` | How the briefing is written. Edit this to change the tone or length. |
| `briefing/speak.py` | Records the script with Piper (Cori voice) into one MP3, with a chapter per section. |
| `briefing/publish.py` | Puts the MP3 on the `audio` branch, keeping the newest 14, and prints its link. |
| `briefing/build_email.py` | Builds the HTML email. |
| `briefing/config.json` | Optional draft recipients. |
| `state.json` | The bookmarks: what has already been covered. |
| `scripts/` | The text of every briefing. |
