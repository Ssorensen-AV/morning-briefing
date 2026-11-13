# How to write the briefing

The listener is Scott, an operations manager with over 30 years in the audio-video industry. He's sharp and busy, he enjoys a bit of humor, and he likes things to feel premium. He listens on the move, so write for the ear, not the eye.

## Files to write

### `work/script.md`: what Cori reads aloud

Use exactly these `## ` sections, in this order, and leave out any section with nothing to cover:

| Section heading | Length | Content |
|---|---|---|
| `## Good Morning` | 60–90 words | The day and date, plus a one-line preview of each section. |
| `## TLDR AI` | the whole issue, usually 700–900 words | Every story in the TLDR AI issue (see below). |
| `## AI News` | 0–400 words | From the AI Daily Brief show notes, only what TLDR didn't already cover. |
| `## AI Deep Dive: <guest or topic>` | whatever AI time is left | From the Lex Fridman transcript. |
| `## Acquired: <episode title>` | 2,450–2,700 words (at least 15 minutes) | See below. |
| `## Packers Game Day` | 150–250 words | Only when sources.md has a Packers preview (see below). |
| `## Sign-off` | 40–60 words | Where we are in the Acquired catalog ("episode 12 of 217"), plus a light parting line. |

**The whole briefing must stay at or under 30 minutes, which is about 4,650 words.** Cori reads at about 160 words per minute.
- Acquired gets its 15 minutes first. Then the TLDR AI issue is read in full.
- **The AI sections together get about 1,900 words.** TLDR AI comes first, then AI News, then the Deep Dive gets what's left, usually 600–900 words.
- If there's no TLDR issue (it doesn't publish on weekends), AI News and the Deep Dive share the 1,900 words, with AI News up to about 700.
- If there's no new AI Daily Brief episode, or TLDR already covered everything in it, leave out AI News.
- If there's no Lex episode, leave out the Deep Dive. Don't pad the other sections.
- On a Packers preview day, take the Packers section's time out of the Deep Dive.

### `work/highlights.md`: the bullets for the email

Use the same `## ` headings as the script, but only for TLDR AI, AI News, AI Deep Dive, Acquired and Packers Game Day. Under each, write 3–5 short bullets (`- `), each one specific: a number, a name, or a takeaway.

## Sources and honesty

- **TLDR AI.** Read the full issue: every story, in the newsletter's order and under its section names ("In Headlines and Launches..."). Sponsor items are already removed, so skip any that remain. Rework each summary for the ear (numbers spoken, no symbols, no "minute read" tags) but keep all of its facts, and add nothing it doesn't say. Keep the story count in sources.md as a check: every story must appear.
- **AI News.** The AI Daily Brief publishes show notes only, so cover only what the notes say. You may add widely known background, framed as background ("for context, ..."). Never invent quotes, numbers or claims and attribute them to the host. Skip sponsor and ad lines entirely.
- **AI Deep Dive.** You have the full Lex Fridman transcript.
  - Cover the guest, the two or three most interesting ideas, one short, clearly attributed quote, and why it matters.
  - If the episode is from the archive, say so naturally, with something like "from the Lex archive, back in 2019".
  - Note anything that has aged well or badly, but only where it's well established.
- **Acquired, with a full transcript.** Tell it as a story: the company's origin, the founders and key people, the deal, the key numbers, what made it work or not, and the hosts' main takeaways and grades. Attribute opinions to Ben and David. There's room for depth here, so include the turning points, the near-misses and the best anecdotes from the episode.
- **Acquired, show notes only** (marked in sources.md). Say up front, in one sentence, that this early episode has no published transcript, so you're telling the story of the deal itself. Then tell the full story from well-established public facts, and don't put words in the hosts' mouths. To reach the 15-minute minimum, go wide rather than padding: the founders and early years, the products and the market at the time, the deal itself and the numbers, what happened afterward, how it looks with hindsight today, and two or three lessons an operator could take from it. It must still reach at least 2,450 words.

- **Packers Game Day** (only on days sources.md includes the preview). In this order:
  1. Who they're playing, home or away, and where.
  2. The odds: the spread and the over/under, said naturally ("the Packers are three-point favorites"). Skip the moneyline unless it adds something.
  3. Injuries of consequence only: starters, stars and anyone ruled Out or on Injured Reserve whose absence changes the game. Use the depth-chart flag, years in the league, and what you reliably know about the player. Skip depth players. Say each player's status plainly ("out", "on injured reserve", "questionable").
  4. Day, kickoff time in Pacific time, and the network or streaming service.
  5. Whether Scott can watch it on regular over-the-air TV in the San Francisco market, and on which station. Use the YES, NO or MAYBE verdict in sources.md. For MAYBE, run one or two web searches for that week's FOX or CBS coverage map (for example "506 sports week 11 2026 coverage map") or Bay Area listings to settle it. If you still can't confirm it, say it's regional and not confirmed, and that the 506sports.com map shows it. Never guess.
  - Only state facts that are in sources.md or that a search confirmed today. The Packers bullets in the email should carry the kickoff, the channel, and the San Francisco answer.

## Writing for the ear

- Write short sentences with one idea each, and use contractions. Aim for a warm, confident narrator, never a press release.
- **Numbers:** write them the way you'd say them, like "about four point two billion dollars" or "twenty nineteen". Never use bare symbols like %, $, &, or "/".
- Spell out acronyms the first time, unless they're everyday words like AI, CEO or iPhone.
- **Formatting:** the script has no bullets, tables, URLs, parentheses or markdown. It's paragraphs only, so each paragraph becomes a breath.
- **Transitions:** use signposts like "Here's the twist." or "Why does this matter?"
- **Humor:** one or two light, dry touches per section. Never forced, and never at the guests' expense.
- **Banned:** "delve", "in today's fast-paced world", "game-changer", and filler openings like "So, ...".

## Length check

After rendering, `work/audio.json` lists each chapter's minutes.

| If this happens | Do this |
|---|---|
| Acquired is under 15 minutes | Expand it and render again, as many times as it takes. Acquired must never be under 15 minutes, transcript or not. |
| The total is over 30 minutes | Trim the Deep Dive first, then AI News, then Acquired down toward 15 minutes. Never drop a TLDR story or take Acquired under 15. Render again. |
