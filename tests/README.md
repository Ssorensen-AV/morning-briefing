# Cloud capability test (2026-11-07)

| Check | Result | Detail |
|---|---|---|
| Python + pip | PASS | Python 3.11.18 (`python3`); `pip install piper-tts` OK (1.8.0) but pip belongs to Python 3.13 (`/usr/local/bin/piper`, python3.13). Use the `piper` CLI or `python3.13 -m piper`, not `python3 -m piper` |
| ffmpeg | PASS | /usr/bin/ffmpeg already present |
| HF voice download | PASS | 4 voices (.onnx ~114-121 MB + .json), all HTTP 200 |
| Podcast sources | PASS | AI Daily Brief RSS 200, 8,354,265 B, newest "Companies Are Spending 5x More on AI Now" (description 4838 chars); Lex RSS 200, 2,091,849 B; Lex transcript 200, 438,424 B, ~39.7k words (raw text incl. nav/markup; page is likely a long transcript) |
| Voice samples | PASS | tests/voice-*.mp3 for lessac, ryan, ljspeech, cori (mono 64 kbps); ~3 s render each |
| Git push | see report | |
