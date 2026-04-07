---
name: ads-spy
description: Scrape Facebook Ad Library for an advertiser's ads — images, videos, ad copy, landing URLs, transcripts. Use when the user asks to spy on ads, scrape Facebook ads, or find ads for a brand.
---

# Ads Spy

When the user asks to scrape Facebook ads, spy on ads, or get ads for an advertiser, follow these steps:

## 1. Parse the request

Extract from the user's message:
- **Advertiser name** (required) — the brand/company to search for
- **Max ads** (optional) — if the user specifies a number, use it; otherwise default to 200

## 2. Run the scraper

Execute this command:

```bash
python3 ~/.qwen/skills/ads-spy/fb_ads_spy.py "<advertiser_name>" --max-ads <N>
```

Replace `<advertiser_name>` with the parsed name (keep original casing).
Replace `<N>` with the max ads count (default 200 if not specified).

**Important:** This launches a visible Chromium browser window. It takes 2-5 minutes depending on the number of ads. Do NOT set a short timeout — use at least 600000ms (10 minutes).

## 3. Report results

After the script finishes, tell the user:
- How many ads were found
- Where the Markdown file was saved
- Remind them they can open the folder as an Obsidian vault

Example: "Found 47 ads for DenSureFit. Saved to `~/obsidian-vault/facebook-ads/densurefit/densurefit.md` with 52 images. You can open `~/obsidian-vault/facebook-ads/` as an Obsidian vault to browse them."
