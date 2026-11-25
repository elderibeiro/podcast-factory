# Cost table (free vs paid)

Figures below come from the [Gemini Developer API pricing](https://ai.google.dev/gemini-api/docs/pricing) page, checked on November 25, 2026. Prices change. Recheck that page before you budget a paid upgrade.

## Models this project uses

| Model ID | Role in this repo | Free tier (list price) | Paid tier, per 1M tokens (USD) |
| --- | --- | --- | --- |
| `gemini-3.5-flash-lite` | Default text | Free of charge | $0.30 input / $2.50 output |
| `gemini-3.8-flash` | Optional richer text | Free of charge | $0.75 input / $3.75 output through December 31, 2026; $1.50 / $7.50 starting January 1, 2027 |
| `gemini-3.8-flash-lite-tts` | Default speech | Free of charge | $0.50 text in / $6.00 audio out through December 31, 2026 (~$0.0015 per 10 seconds of audio). Starting January 1, 2027: $1.00 / $12.00 (~$0.003 per 10 seconds) |
| `gemini-3.8-flash-tts` | Higher-fidelity speech fallback | Free of charge | $0.50 text in / $9.00 audio out through December 31, 2026 (~$0.00225 per 10 seconds). Starting January 1, 2027: $1.00 / $18.00 (~$0.0045 per 10 seconds) |
| `gemini-3.1-flash-tts-preview` | Speech fallback | Free of charge | $1.00 text in / $20.00 audio out |
| `gemini-2.5-flash-preview-tts` | Older speech fallback | Free of charge | $0.50 text in / $10.00 audio out |
| `gemini-2.5-pro-preview-tts` | Not used | **Not available** on the free tier | $1.00 text in / $20.00 audio out |

Audio tokens are described by Google as 25 tokens per second of audio.

## What a weekly 5-minute episode usually costs

A typical Podcast Factory run makes a handful of short text requests (outline, script, newsletter, show notes, social posts, titles, fact-check) plus one speech pass over a ~5-minute script.

On the **free tier**, those calls are listed as free of charge, within whatever request-per-day limit AI Studio shows for your project. That is enough for most weekly neighborhood or shop shows, as long as you are not generating dozens of takes a day.

If you moved the same workload to **paid** pricing, the text side would usually be cents, not dollars. The speech side is the part to watch: at the late-2026 Flash-Lite TTS paid rate of about $0.0015 per 10 seconds, five minutes of audio is on the order of **five cents** per take, before retries. A higher-fidelity `gemini-3.8-flash-tts` take is a little more. Generate once, listen, then re-run only the sections you change.

Hosting the RSS feed (Spotify for Creators, a host's free plan, or a paid host) is separate from Gemini and is not included here.

## Other cost notes

- `--dry-run` costs nothing and needs no key. Use it while you edit prompts and configs.
- Free-tier content may be used to improve Google's products; paid-tier content is listed as not used that way. See [gemini-api-key.md](gemini-api-key.md).
- Do not start new work on deprecated `gemini-2.5-flash` or `gemini-2.5-pro` text IDs. Google is routing those to newer models.

This table is not a quote from Google, and it is not a promise that the free tier will stay unchanged.
