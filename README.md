# Marketing Intelligence Agent

Open-source marketing intelligence tools for AI coding assistants. Spy on competitors' ads across Facebook and YouTube — powered by browser automation.

Each folder is a self-contained tool with its own README, install instructions, and source files.

## Tools

| Tool | Description | Status |
|------|-------------|--------|
| [facebook-ads-spy](./facebook-ads-spy/) | Scrape any advertiser's Facebook ads — images, videos, ad copy, transcripts | Ready |
| [youtube-ads-spy](./youtube-ads-spy/) | Find any brand's YouTube video ads — thumbnails, view counts, transcripts | Ready |

## How They Work

Both tools use **Patchright** (anti-detection browser automation) to scrape public ad transparency platforms:

- **Facebook Ads Spy** scrapes the [Meta Ad Library](https://www.facebook.com/ads/library/)
- **YouTube Ads Spy** scrapes the [Google Ads Transparency Center](https://adstransparency.google.com/)

No API keys or logins required for basic scraping. Optional API keys unlock video transcription.

## Quick Start

Pick a tool, follow its README:

```bash
# Facebook Ads
cd facebook-ads-spy && cat README.md

# YouTube Ads
cd youtube-ads-spy && cat README.md
```

## Works With

- **Claude Code** — install as a slash command (`/ads-spy`, `/youtube-ads-scraper`)
- **Gemini CLI** — run the Python script directly
- **Any AI CLI** — standalone Python scripts, no framework lock-in
- **Terminal** — works without any AI assistant
