# Daily World Cup Cinematic Video Pipeline (Free Stack)

Fully automated, runs daily via GitHub Actions (free 2,000 min/month for
public repos), produces a subtitle-free cinematic Short every day and a
long-form weekly recap on Sundays, and auto-publishes to your YouTube channel.

## Stack (all free)
- **GitHub Actions** — scheduler + compute
- **Gemini API (free tier)** — daily "on this day" topic + shot list
- **archive.org** — public-domain footage search (best-effort; often empty)
- **Pillow + FFmpeg** — generated cinematic stills, Ken Burns zoom, color
  grading, crossfades, slow-motion — guarantees output even with no footage
- **YouTube Data API v3 (free quota: 10,000 units/day, ~6 uploads)** — publish

## One-time setup

### 1. Repo secrets
In GitHub repo → Settings → Secrets and variables → Actions, add:
- `GEMINI_API_KEY` — from https://aistudio.google.com/apikey (free)
- `YT_CLIENT_ID`, `YT_CLIENT_SECRET` — from Google Cloud Console, OAuth
  client (Desktop app type), with YouTube Data API v3 enabled
- `YT_REFRESH_TOKEN` — generate once locally:
  ```python
  from google_auth_oauthlib.flow import InstalledAppFlow
  flow = InstalledAppFlow.from_client_secrets_file(
      "client_secret.json",
      scopes=["https://www.googleapis.com/auth/youtube.upload"],
  )
  creds = flow.run_local_server(port=0)
  print(creds.refresh_token)
  ```

### 2. Royalty-free music
Download one ambient/cinematic track from YouTube Audio Library (free, no
attribution required for most tracks) and commit it as `assets/music.mp3`.
This is reused every day — no need to fetch new music.

### 3. Adjust schedule
Edit the cron line in `.github/workflows/daily.yml` (default: 06:00 UTC).

## Important notes / limitations
- **archive.org clips are rare** for World Cup content — most days the
  pipeline will fall back to AI-generated cinematic stills with Ken Burns
  motion. This keeps it 100% copyright-safe and never blocks the daily run.
- **No subtitles/text overlays** are added, per your requirement.
- **"Most viral on the internet"** is intentionally NOT implemented —
  scraping/reposting viral World Cup clips (real match footage) will trigger
  FIFA/broadcaster copyright claims and likely get your channel struck or
  terminated. This pipeline instead generates original cinematic content
  daily, which is sustainable long-term.
- Test with `workflow_dispatch` (manual run button in the Actions tab)
  before relying on the schedule.

## To improve quality later (still free-ish)
- Swap Pillow stills for actual AI-generated images (e.g. a free tier of
  an image-gen API) for richer scenes.
- Add a second CC footage source (Wikimedia Commons video search).
- Vary music tracks (rotate 3-5 CC0 tracks from assets/).
