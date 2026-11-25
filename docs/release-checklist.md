# Release checklist

Walk through this list before every episode. It is written for a volunteer who may only ship a show once a week.

## Before you generate

- [ ] The `podcast.yaml` file still matches the show you are publishing (name, sections, cadence, platforms).
- [ ] The episode brief has dates, hours, and sources, and nothing you would not be willing to say in public.
- [ ] The brief has **no** personal emails, home addresses, or family details.
- [ ] You have not padded the brief with rumors or numbers you could not check.

Optional: `podcast-factory generate --dry-run --brief path/to/brief.md` and read the rendered prompts.

## After a live generate (or after you write the script yourself)

- [ ] Read the outline and the script out loud. Cut anything the brief does not support.
- [ ] Read `drafts/fact-check.md` and apply the cuts. If the verdict is "Do not publish yet," stop.
- [ ] Confirm names, times, prices, and addresses of public places against the original source.
- [ ] Crime and safety items stay calm, practical, and free of speculation.
- [ ] The welcome and sign-off follow your host-name rule.
- [ ] The newsletter (if you use one) matches the audio and lists sources.
- [ ] Show notes and social posts do not invent a "now live on…" platform you have not posted to, and they do not invent contact details.

## Audio

- [ ] Listen to the full file once, with headphones if you can.
- [ ] Pronunciations, numbers, and dates sound right. Re-generate a section if they do not.
- [ ] Loudness is consistent. Export to the format your host requires (often MP3).
- [ ] The file name and episode title match the show notes.

## Publish

- [ ] Upload audio (and artwork, if needed) to your host so the RSS feed updates.
- [ ] Paste the reviewed description, title, and AI disclosure into the host.
- [ ] Confirm the new item appears in the feed.
- [ ] After the first episode, submit or update the feed at Spotify for Creators, Apple Podcasts Connect, Amazon Music for Podcasters, and YouTube, as described in [publishing.md](publishing.md).
- [ ] Publish the written edition where you said you would (blog, PDF, bulletin, or newsletter).
- [ ] Only then paste the social posts, with a real link.

## After it is out

- [ ] Click the episode on at least one app and listen to the first 15 seconds.
- [ ] Keep the brief, script, newsletter, and audio together for your records.
- [ ] Note anything to change in `podcast.yaml` or the prompts next week.
