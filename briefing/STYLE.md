# How to write the briefing

The listener is Scott, an operations manager with over 30 years in the audio-video industry. He's sharp and busy, he enjoys a bit of humor, and he likes things to feel premium. He listens on the move, so write for the ear, not the eye.

## Files to write

### `work/script.md`: what Cori reads aloud

Use exactly these `## ` sections, in this order, and leave out any section with nothing to cover:

| Section heading | Length | Content |
|---|---|---|
| `## Good Morning` | 70–110 words | The day and date, plus a one-line preview of each section. |
| `## AI News` | 350–600 words | From the AI Daily Brief show notes (see below). |
| `## AI Deep Dive: <guest or topic>` | the rest of the AI time | From the Lex Fridman transcript. |
| `## Acquired: <episode title>` | about 1,500 words (about 10 minutes) | See below. |
| `## Sign-off` | 40–70 words | Where we are in the Acquired catalog ("episode 12 of 217"), plus a light parting line. |

**AI News and AI Deep Dive together should total about 1,500 words (about 10 minutes).**
- If there's no new AI Daily Brief episode, leave out AI News and give the full 1,500 words to the Deep Dive.
- If there's no Lex episode, AI News may run up to about 700 words. Don't pad it.

### `work/highlights.md`: the bullets for the email

Use the same `## ` headings as the script, but only for AI News, AI Deep Dive and Acquired. Under each, write 3–5 short bullets (`- `), each one specific: a number, a name, or a takeaway.

## Sources and honesty

- **AI News.** The AI Daily Brief publishes show notes only, so cover only what the notes say. You may add widely known background, framed as background ("for context, ..."). Never invent quotes, numbers or claims and attribute them to the host. Skip sponsor and ad lines entirely.
- **AI Deep Dive.** You have the full Lex Fridman transcript.
  - Cover the guest, the three or four most interesting ideas, one or two memorable quotes (short and clearly attributed), and why it matters.
  - If the episode is from the archive, say so naturally, with something like "from the Lex archive, back in 2019".
  - Note anything that has aged well or badly, but only where it's well established.
- **Acquired, with a full transcript.** Tell it as a story: the company's origin, the deal, the key numbers, what made it work or not, and the hosts' main takeaways and grades. Attribute opinions to Ben and David.
- **Acquired, show notes only** (marked in sources.md). Say up front, in one sentence, that this early episode has no published transcript, so you're telling the story of the deal itself. Then tell it from well-established public facts, and don't put words in the hosts' mouths. Keep it to about 1,200–1,500 words.

## Writing for the ear

- Write short sentences with one idea each, and use contractions. Aim for a warm, confident narrator, never a press release.
- **Numbers:** write them the way you'd say them, like "about four point two billion dollars" or "twenty nineteen". Never use bare symbols like %, $, &, or "/".
- Spell out acronyms the first time, unless they're everyday words like AI, CEO or iPhone.
- **Formatting:** the script has no bullets, tables, URLs, parentheses or markdown. It's paragraphs only, so each paragraph becomes a breath.
- **Transitions:** use signposts like "Here's the twist." or "Why does this matter?"
- **Humor:** one or two light, dry touches per section. Never forced, and never at the guests' expense.
- **Banned:** "delve", "in today's fast-paced world", "game-changer", and filler openings like "So, ...".

## Length check

Cori reads at about 150 words per minute. After rendering, `work/audio.json` lists each chapter's minutes.

| If this happens | Do this |
|---|---|
| The two AI sections total under 8 or over 12 minutes | Revise the script once and render again. |
| Acquired is under 8 or over 12 minutes | Revise the script once and render again. |
| It's show-notes-only with thin material | A short Acquired section (down to about 6 minutes) is fine. |
