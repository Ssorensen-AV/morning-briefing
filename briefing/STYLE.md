# How to write the briefing

The listener is Scott, an operations manager with over 30 years in the audio-video industry. He's sharp and busy, he enjoys a bit of humor, and he likes things to feel premium. He listens on the move, so write for the ear, not the eye.

## Files to write

### `work/script.md`: what Cori reads aloud

Use exactly these `## ` sections, in this order, and leave out any section with nothing to cover:

| Section heading | Length | Content |
|---|---|---|
| `## Good Morning` | 60–90 words | The day and date, plus a one-line preview of each section. |
| `## TLDR AI` | the whole issue, usually 700–900 words | Every story in the TLDR AI issue (see below). |
| `## AI News` | 0–250 words | From the AI Daily Brief show notes, only what TLDR didn't already cover. |
| `## AI Deep Dive: <guest or topic>` | whatever AI time is left | From the Lex Fridman transcript. |
| `## Acquired: <episode title>` | 3,200–3,350 words (at least 20 minutes) | See below. |
| `## Sign-off` | 40–60 words | Where we are in the Acquired catalog ("episode 12 of 217"), plus a light parting line. |

**The whole briefing must stay at or under 30 minutes, which is about 4,650 words.** Cori reads at about 160 words per minute.
- Acquired gets its 20 minutes first. Then the TLDR AI issue is read in full.
- **The AI sections together get about 1,250 words.** TLDR AI comes first, then AI News, then the Deep Dive gets what's left, usually 250–450 words: the guest, the one or two best ideas, and why it matters.
- If there's no TLDR issue (it doesn't publish on weekends), AI News and the Deep Dive share the 1,250 words, with AI News up to about 450.
- If there's no new AI Daily Brief episode, or TLDR already covered everything in it, leave out AI News.
- If there's no Lex episode, leave out the Deep Dive. Don't pad the other sections.

### `work/highlights.md`: the bullets for the email

Use the same `## ` headings as the script, but only for TLDR AI, AI News, AI Deep Dive and Acquired. Under each, write 3–5 short bullets (`- `), each one specific: a number, a name, or a takeaway.

## Sources and honesty

- **TLDR AI.** Read the full issue: every story, in the newsletter's order and under its section names ("In Headlines and Launches..."). Sponsor items are already removed, so skip any that remain. Rework each summary for the ear (numbers spoken, no symbols, no "minute read" tags) but keep all of its facts, and add nothing it doesn't say. Keep the story count in sources.md as a check: every story must appear.
- **AI News.** The AI Daily Brief publishes show notes only, so cover only what the notes say. You may add widely known background, framed as background ("for context, ..."). Never invent quotes, numbers or claims and attribute them to the host. Skip sponsor and ad lines entirely.
- **AI Deep Dive.** You have the full Lex Fridman transcript.
  - It's short now, so cover the guest, the one or two most interesting ideas, at most one short, clearly attributed quote, and why it matters.
  - If the episode is from the archive, say so naturally, with something like "from the Lex archive, back in 2019".
  - Note anything that has aged well or badly, but only where it's well established.
- **Acquired, with a full transcript.** Tell it as a story: the company's origin, the founders and key people, the deal, the key numbers, what made it work or not, and the hosts' main takeaways and grades. Attribute opinions to Ben and David. There's room for depth here, so include the turning points, the near-misses and the best anecdotes from the episode.
- **Acquired, show notes only** (marked in sources.md). Say up front, in one sentence, that this early episode has no published transcript, so you're telling the story of the deal itself. Then tell the full story from well-established public facts, and don't put words in the hosts' mouths. To reach the 20-minute minimum, go wide rather than padding: the founders and early years, the products and the market at the time, the deal itself and the numbers, what happened afterward, how it looks with hindsight today, and two or three lessons an operator could take from it. It must still reach at least 3,200 words.

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
| Acquired is under 20 minutes | Expand it and render again, as many times as it takes. Acquired must never be under 20 minutes, transcript or not. |
| The total is over 30 minutes | Trim the Deep Dive first, then AI News, then Acquired down toward 20 minutes. Never drop a TLDR story or take Acquired under 20. Render again. |
