# Daily run instructions (for the cloud routine)

You are producing today's Morning Briefing. Work from the repository root. These rules apply to the whole run:

- **Never send email.** Only create a Gmail draft, with the Gmail connector's `create_draft`.
- **Use no other connectors.**
- **Don't edit the code** in `briefing/` unless a step fails because of it. If you do, say so in the final reply.

## Steps

1. **Set up.** Run `git pull -q`, then `pip install -q piper-tts`. Pip may install piper under Python 3.13, so always use the `piper` command, never `python3 -m piper`.

2. **Gather.** Run `DAY=$(TZ=America/Los_Angeles date +%F)`, then `python3 briefing/gather.py`. This writes `work/sources.md` and `work/selection.json`, and any problems appear in that file's `errors` list.

3. **Read.** Read all of `work/sources.md`. It's long (the transcripts can run to 40,000 words), so read it in chunks until you've seen the end.

4. **Write.** Follow `briefing/STYLE.md` exactly. Write `work/script.md` and `work/highlights.md`.

5. **Record.** Run `python3 briefing/speak.py work/briefing.mp3`. Then check `work/audio.json` against the length check in STYLE.md, revising and re-rendering as that check says.

6. **Publish the audio.** Run `URL=$(python3 briefing/publish.py work/briefing.mp3 $DAY)`.

7. **Build the email.** Run `python3 briefing/build_email.py "$URL"`, which prints the subject line.

8. **Create the Gmail draft** with `create_draft`:
   - **subject:** the printed subject line
   - **htmlBody:** the exact contents of `work/email.html`
   - **body:** the exact contents of `work/email.txt`
   - **to:** the `to` list in `briefing/config.json`, if it isn't empty
   - Do not send it.

9. **Save progress.** Only do this after the draft exists:
   1. Run `python3 briefing/gather.py --commit`.
   2. Save the script as `scripts/$DAY.md`.
   3. `git add state.json scripts`, then commit "Briefing $DAY".
   4. `git pull --rebase -q origin main`, then `git push origin HEAD:main`.

## If something fails

- **A single source fails in step 2:** carry on with the others, and mention it in the Good Morning section in one light sentence.
- **Any later step fails and you can't fix it:**
  1. Still create a Gmail draft with the subject "Morning Briefing: problem on $DAY", stating the failed step and the error in plain English.
  2. Don't run step 9, so tomorrow retries the same episodes.

## Final reply

Keep it to a few lines: the episodes covered, the total minutes, the audio link, and whether the draft was created.
