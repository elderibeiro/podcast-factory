# How to get a free Gemini API key

Podcast Factory's default text and speech models are on the Gemini Developer API free tier, as listed on [Google's pricing page](https://ai.google.dev/gemini-api/docs/pricing) (checked November 25, 2026). You do not need a paid Google Cloud account to try the CLI.

## Create a key

1. Open [Google AI Studio](https://aistudio.google.com/) and sign in with a Google account.
2. Open the [API keys](https://aistudio.google.com/apikey) page and create a key in a project you control.
3. Copy the key into a local `.env` file in this repo (see `.env.example`). Never commit `.env`, paste a key into a prompt template, or put it in a newsletter.

```bash
cp .env.example .env
# then edit .env and set GEMINI_API_KEY=...
```

The CLI also accepts `GOOGLE_API_KEY`. A real environment variable wins over `.env`.

## What the free tier covers

As of November 25, 2026, the official pricing table marks these defaults as **Free of charge** on the free tier:

| Use | Default model ID | Why it is the default |
| --- | --- | --- |
| Text (outline, script, newsletter) | `gemini-3.5-flash-lite` | Free-tier row, and a lower paid price if you later upgrade |
| Speech | `gemini-3.8-flash-lite-tts` | Free-tier row, built for high-volume or short-form narration |

You can switch the text model to `gemini-3.8-flash` in `podcast.yaml` if you want the current Flash tier. Do **not** start a new project on `gemini-2.5-flash` or `gemini-2.5-pro`; Google has deprecated those IDs for new work and will route them to newer models.

## Limits and privacy

- Rate limits (requests per minute and per day) are **per project**, not per key, and are shown in AI Studio. Google says they are not guaranteed and can vary.
- On the free tier, Google states that content may be used to improve its products. If that is not acceptable for your parish, shop, or newsroom, use a paid tier (where the pricing page says content is not used that way) or stay on `--dry-run` and paste the prompts into a tool your organization has already approved.
- Keep source notes free of personal emails, home addresses, and unpublished personal data. The model will see whatever you put in the brief.

A walkthrough of costs, including a sample 5-minute weekly episode, is in [costs.md](costs.md).
