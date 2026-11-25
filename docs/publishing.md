# How to publish via RSS

Podcast Factory stops at a reviewed script, a written edition, and optional WAV audio. Publishing still needs a human: you host an RSS feed, then submit that feed to each directory. The steps below are the usual path as of late 2026. Always follow the platform's current help page if it disagrees with this summary.

## 1. Host the audio and an RSS feed

You need a stable URL for each episode file and an RSS 2.0 feed with podcast extensions (title, description, artwork, audio enclosure, and a public contact email that you are willing to publish).

Common options for a small organization:

- **Spotify for Creators** can host the show and give you an RSS feed after the first episode is published. See [Finding and enabling your RSS feed](https://support.spotify.com/us/creators/article/finding-and-enabling-your-rss-feed/).
- A dedicated host (many have a free or low-cost plan) will give you a feed and a post form for each episode.
- Self-hosting is possible but you must serve byte-range requests, keep the feed valid, and not take the files down later.

Export or convert the WAV from this tool to the format your host asks for (often 44.1 kHz stereo or mono MP3). Keep a copy of the reviewed script and the audio.

Before you enable a public RSS feed, remember that **the email in the feed becomes public**. Use an organizational inbox, not a personal one.

## 2. Spotify for Creators

1. Sign in at [creators.spotify.com](https://creators.spotify.com).
2. If Spotify is your host, publish the first episode there. The show is listed on Spotify from that feed.
3. To use the same feed on other apps, open **Settings → Availability**, wait until **RSS Distribution** appears (after the first episode), and enable the feed. Spotify does not automatically register you at Apple or Amazon; you submit the feed yourself.

Details: [Finding and enabling your RSS feed](https://support.spotify.com/us/creators/article/finding-and-enabling-your-rss-feed/).

## 3. Apple Podcasts Connect

1. Sign in to [Apple Podcasts Connect](https://podcastsconnect.apple.com).
2. Click **Add** and choose **New Show**, then **Add a show with an RSS feed**.
3. Paste the feed URL, review the show details, set content rights and a contact, choose countries, and publish.
4. Apple validates the feed. Fix any warnings before the show can go live. Review can take time.

Details: [Submit a new show](https://podcasters.apple.com/support/897-submit-a-show).

## 4. Amazon Music and Audible

1. Open [podcasters.amazon.com](https://podcasters.amazon.com) and choose **Add or claim your podcast**.
2. Sign in with an Amazon account, paste the RSS URL, accept the terms, and confirm ownership with the email address in the feed.
3. A new show can take up to about a week to appear in Amazon Music and Audible. Later episodes usually follow sooner.

## 5. YouTube podcasts

1. In [YouTube Studio](https://studio.youtube.com), click **Create → New podcast**.
2. You can upload video episodes, turn a playlist into a podcast, or **Submit RSS feed** so YouTube pulls episodes (including for YouTube Music).
3. Follow YouTube's verification and content rules. An audio-only RSS import may still be shown with cover art; check the current Studio flow.

Overview: [Start your podcast on YouTube](https://www.youtube.com/creators/create/podcasts/).

## After you are listed

- Post new episodes to the host first. Directories pull from the feed; you should not upload a second, different copy to each app unless a platform requires it (some YouTube setups do).
- Keep titles, show notes, and artwork consistent with what you already reviewed.
- Add the [AI disclosure](ai-disclosure.md) to show notes if the episode used generated script or voice.
- Use [release-checklist.md](release-checklist.md) every week so a volunteer can ship without skipping the human review.
