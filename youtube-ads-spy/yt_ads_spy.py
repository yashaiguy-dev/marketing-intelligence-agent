#!/usr/bin/env python3
"""
YouTube Ads Spy — CLI scraper for Google Ads Transparency Center.
Finds YouTube video ads for a domain/advertiser, extracts metadata + transcripts.
Outputs Obsidian-ready Markdown.

Usage:
    python3 yt_ads_spy.py "nike.com" [--max-videos 20] [--output-dir ~/obsidian-vault/youtube-ads]

Requirements:
    pip3 install requests patchright
    patchright install chromium

Set RAPIDAPI_KEY env var for video transcription (optional):
    export RAPIDAPI_KEY="your-key-here"
"""

import argparse
import html
import os
import re
import sys
import time
import random
from datetime import date
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests not found. Run: pip3 install requests")
    sys.exit(1)

try:
    from patchright.sync_api import sync_playwright
except ImportError:
    print("Error: patchright not found. Run: pip3 install patchright && patchright install chromium")
    sys.exit(1)


# --- Config ---

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "")
RAPIDAPI_HOST = "youtube-transcript3.p.rapidapi.com"


# --- Utility functions ---

def delay(min_s=1.5, max_s=3.5):
    time.sleep(random.uniform(min_s, max_s))


def slugify(name: str) -> str:
    """Convert domain/brand name to folder-safe slug. Max 50 chars."""
    slug = name.lower().strip()
    slug = re.sub(r'https?://', '', slug)
    slug = slug.rstrip('/')
    slug = re.sub(r'[^a-z0-9\s.-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    slug = re.sub(r'[.-]+', '-', slug)
    slug = slug.strip('-')[:50].strip('-')
    return slug


def escape_markdown(text: str) -> str:
    """Escape Markdown-significant characters."""
    for ch in ['\\', '#', '*', '[', ']', '|', '`', '>', '!', '_', '{', '}']:
        text = text.replace(ch, f'\\{ch}')
    return text


# --- YouTube helper functions ---

def is_real_youtube_url(url):
    if not url:
        return False
    return ("youtube.com/watch" in url or
            "youtu.be/" in url or
            "youtube.com/embed/" in url) and "googlesyndication" not in url


def find_youtube_in_frames(page):
    """Search all page frames for a YouTube video ID."""
    for sel in [
        'a[href*="youtube.com/watch"]',
        'a[href*="youtu.be/"]',
        'a:has-text("Watch on YouTube")',
    ]:
        try:
            el = page.query_selector(sel)
            if el:
                href = el.get_attribute("href") or ""
                if is_real_youtube_url(href):
                    return href
        except Exception:
            continue

    try:
        for iframe in page.query_selector_all('iframe'):
            src = iframe.get_attribute("src") or ""
            if "youtube.com/embed/" in src:
                vid_id = src.split("/embed/")[-1].split("?")[0]
                if vid_id and len(vid_id) == 11:
                    return f"https://www.youtube.com/watch?v={vid_id}"
    except Exception:
        pass

    try:
        for frame in page.frames:
            frame_url = frame.url or ""
            if frame_url == page.url:
                continue

            if "youtube.com/embed/" in frame_url:
                vid_id = frame_url.split("/embed/")[-1].split("?")[0]
                if vid_id and len(vid_id) >= 10:
                    return f"https://www.youtube.com/watch?v={vid_id}"

            for sel in [
                'a[href*="youtube.com/watch"]',
                'a[href*="youtu.be/"]',
                'iframe[src*="youtube.com/embed"]',
            ]:
                try:
                    el = frame.query_selector(sel)
                    if el:
                        href = el.get_attribute("href") or el.get_attribute("src") or ""
                        if is_real_youtube_url(href):
                            if "/embed/" in href:
                                vid_id = href.split("/embed/")[-1].split("?")[0]
                                return f"https://www.youtube.com/watch?v={vid_id}"
                            return href
                except Exception:
                    continue

            try:
                frame_html = frame.content()
                for pattern in [
                    r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
                    r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
                    r'youtu\.be/([a-zA-Z0-9_-]{11})',
                ]:
                    matches = re.findall(pattern, frame_html)
                    if matches:
                        return f"https://www.youtube.com/watch?v={matches[0]}"
            except Exception:
                pass
    except Exception:
        pass

    return None


def fetch_transcript(video_id):
    if not RAPIDAPI_KEY:
        return ""
    try:
        resp = requests.get(
            f"https://{RAPIDAPI_HOST}/api/transcript",
            params={"videoId": video_id},
            headers={
                "x-rapidapi-host": RAPIDAPI_HOST,
                "x-rapidapi-key": RAPIDAPI_KEY,
            },
            timeout=15,
        )
        data = resp.json()
        if data.get("success") and data.get("transcript"):
            return " ".join(
                html.unescape(seg.get("text", ""))
                for seg in data["transcript"]
            ).strip()
        return ""
    except Exception:
        return ""


def get_youtube_details(context, youtube_url):
    if "youtu.be/" in youtube_url:
        video_id = youtube_url.split("youtu.be/")[-1].split("?")[0]
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
    if not youtube_url.startswith("http"):
        youtube_url = "https://" + youtube_url

    yt_page = context.new_page()
    try:
        yt_page.goto(youtube_url, wait_until="domcontentloaded", timeout=30000)
        delay(3, 5)

        title = ""
        for sel in ['meta[property="og:title"]', 'meta[name="title"]']:
            el = yt_page.query_selector(sel)
            if el:
                title = (el.get_attribute("content") or "").strip()
                if title:
                    break
        if not title:
            title = yt_page.title().replace(" - YouTube", "").strip()

        views = ""
        for sel in [
            'meta[itemprop="interactionCount"]',
            'ytd-video-view-count-renderer .view-count',
            '#info-container ytd-video-view-count-renderer span',
            'span:has-text("views")',
        ]:
            try:
                el = yt_page.query_selector(sel)
                if el:
                    views = (el.get_attribute("content") or el.inner_text() or "").strip()
                    if views:
                        break
            except Exception:
                continue

        upload_date = ""
        for sel in [
            'meta[itemprop="uploadDate"]',
            'meta[itemprop="datePublished"]',
            'meta[property="og:video:release_date"]',
        ]:
            try:
                el = yt_page.query_selector(sel)
                if el:
                    upload_date = (el.get_attribute("content") or "").strip()
                    if upload_date:
                        break
            except Exception:
                continue

        if not upload_date:
            for sel in [
                '#info-strings yt-formatted-string',
                'span:has-text("ago")',
            ]:
                try:
                    el = yt_page.query_selector(sel)
                    if el:
                        upload_date = el.inner_text().strip()
                        if upload_date:
                            break
                except Exception:
                    continue

        video_id = youtube_url.split("v=")[-1].split("&")[0] if "v=" in youtube_url else ""
        transcript = fetch_transcript(video_id) if video_id else ""

        return {
            "youtube_url": youtube_url,
            "title": title,
            "views": views,
            "upload_date": upload_date,
            "transcript": transcript,
        }
    except Exception:
        return {
            "youtube_url": youtube_url,
            "title": "ERROR",
            "views": "ERROR",
            "upload_date": "ERROR",
            "transcript": "",
        }
    finally:
        yt_page.close()


def collect_ad_urls(page, max_needed):
    prev_count = 0
    stale_rounds = 0
    target = max_needed * 3

    for attempt in range(30):
        ads = page.query_selector_all('creative-preview')
        current_count = len(ads)
        if current_count >= target:
            break
        if current_count == prev_count:
            stale_rounds += 1
            if stale_rounds >= 3:
                break
        else:
            stale_rounds = 0
        prev_count = current_count
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        delay(1.5, 2.5)

    ads = page.query_selector_all('creative-preview')
    ad_urls = []
    for ad in ads:
        try:
            link = ad.query_selector('a[href*="creative"]')
            if link:
                href = link.get_attribute("href") or ""
                if href:
                    if href.startswith("/"):
                        href = "https://adstransparency.google.com" + href
                    ad_urls.append(href)
                    continue
        except Exception:
            pass
        ad_urls.append(None)

    return ad_urls


# --- Main scraping function ---

def scrape_ads(domain: str, max_videos: int = 20):
    """
    Scrape Google Ads Transparency for YouTube video ads.
    Returns (results_list, advertiser_name) tuple.
    """
    print(f"[yt-ads-spy] Opening Google Ads Transparency...")

    results = []
    seen_video_ids = set()
    is_direct_url = "adstransparency.google.com/advertiser/" in domain

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--window-size=1366,900",
            ],
        )
        context = browser.new_context(
            viewport={"width": 1366, "height": 900},
            locale="en-US",
        )
        page = context.new_page()

        try:
            # Step 1: Navigate
            if is_direct_url:
                print("[yt-ads-spy] Loading advertiser page...")
                page.goto(domain, wait_until="networkidle", timeout=60000)
                delay(3, 5)
            else:
                clean_domain = domain.replace("https://", "").replace("http://", "").rstrip("/")
                print(f"[yt-ads-spy] Searching for '{clean_domain}'...")
                page.goto("https://adstransparency.google.com/?region=anywhere",
                          wait_until="networkidle", timeout=60000)
                delay(5, 7)

                # Search
                page.mouse.click(683, 400)
                delay(1, 2)

                search_input = None
                for sel in [
                    'input[placeholder*="Find the ads"]',
                    'input[type="search"]',
                    'input[aria-label*="search" i]',
                    'input[placeholder*="search" i]',
                    'input[type="text"]',
                    '[role="searchbox"]',
                    '[role="combobox"]',
                    'input',
                ]:
                    try:
                        el = page.query_selector(sel)
                        if el and el.is_visible():
                            search_input = el
                            break
                    except Exception:
                        continue

                if not search_input:
                    print("[yt-ads-spy] Cannot find search box!")
                    return results, domain

                search_input.click()
                delay(0.5, 1)
                search_input.fill(clean_domain)
                delay(2, 3)

                for sel in [
                    '[role="listbox"] [role="option"]',
                    '[class*="suggestion"]',
                    'a[href*="advertiser"]',
                ]:
                    try:
                        el = page.query_selector(sel)
                        if el and el.is_visible():
                            el.click()
                            delay(3, 5)
                            break
                    except Exception:
                        continue

            # Dismiss popups
            for _ in range(3):
                try:
                    for btn in page.query_selector_all('[aria-label="Close"]'):
                        if btn.is_visible():
                            btn.click()
                            delay(1, 2)
                            break
                except Exception:
                    pass

            page.mouse.click(683, 450)
            delay(1, 2)

            # See all ads
            print("[yt-ads-spy] Loading all ads...")
            for sel in [
                'a:has-text("See all ads")',
                'button:has-text("See all ads")',
                'text="See all ads"',
            ]:
                try:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        el.click()
                        delay(3, 5)
                        break
                except Exception:
                    continue

            # Dismiss popup again
            try:
                for btn in page.query_selector_all('[aria-label="Close"]'):
                    if btn.is_visible():
                        btn.click()
                        delay(1, 2)
                        break
            except Exception:
                pass

            # Format → Video
            print("[yt-ads-spy] Filtering by Video format...")
            format_clicked = False
            for sel in [
                '[aria-label="Ad format filter"]',
                'button:has-text("All formats")',
                'text="All formats"',
                'button:has-text("Format")',
            ]:
                try:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        el.click()
                        format_clicked = True
                        delay(1, 2)
                        break
                except Exception:
                    continue

            if not format_clicked:
                try:
                    for btn in page.query_selector_all('[aria-label="Close"]'):
                        if btn.is_visible():
                            btn.click()
                            delay(1, 2)
                            break
                except Exception:
                    pass
                page.mouse.click(683, 300)
                delay(1, 2)
                for sel in ['[aria-label="Ad format filter"]', 'button:has-text("All formats")']:
                    try:
                        el = page.query_selector(sel)
                        if el and el.is_visible():
                            el.click()
                            delay(1, 2)
                            break
                    except Exception:
                        continue

            delay(1, 1.5)
            for sel in [
                'text="Video"',
                '[role="option"]:has-text("Video")',
                '[role="menuitem"]:has-text("Video")',
                'li:has-text("Video")',
            ]:
                try:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        el.click()
                        delay(3, 5)
                        break
                except Exception:
                    continue

            # Force video filter via URL if needed
            if "format=VIDEO" not in page.url:
                current = page.url
                new_url = current + ("&" if "?" in current else "?") + "format=VIDEO"
                page.goto(new_url, wait_until="networkidle", timeout=60000)
                delay(3, 5)

            # Collect ad URLs
            print("[yt-ads-spy] Collecting ad URLs...")
            ad_urls = collect_ad_urls(page, max_videos)
            total_ads = len(ad_urls)
            print(f"[yt-ads-spy] Found {total_ads} video ads. Processing...")

            if not ad_urls:
                print("[yt-ads-spy] No video ads found!")
                return results, domain

            # Process each ad
            consecutive_dupes = 0

            for i, ad_url in enumerate(ad_urls):
                if len(results) >= max_videos:
                    break
                if consecutive_dupes >= 10:
                    break

                print(f"[yt-ads-spy] Checking ad {i+1}/{total_ads} (found {len(results)}/{max_videos})...")

                try:
                    if ad_url:
                        page.goto(ad_url, wait_until="domcontentloaded", timeout=60000)
                    else:
                        continue

                    delay(2, 4)

                    # Dismiss popup
                    try:
                        for btn in page.query_selector_all('[aria-label="Close"]'):
                            if btn.is_visible():
                                btn.click()
                                delay(0.5, 1)
                                break
                    except Exception:
                        pass

                    # Find YouTube video
                    youtube_url = None
                    for slide in range(6):
                        youtube_url = find_youtube_in_frames(page)
                        if youtube_url:
                            vid_id = youtube_url.split("v=")[-1].split("&")[0] if "v=" in youtube_url else ""
                            if vid_id and vid_id in seen_video_ids:
                                youtube_url = None
                            else:
                                if vid_id:
                                    seen_video_ids.add(vid_id)
                                break

                        try:
                            next_btn = page.query_selector('[aria-label="Next variation"]')
                            if next_btn and next_btn.get_attribute("aria-disabled") != "true":
                                next_btn.click()
                                delay(1.5, 2.5)
                            else:
                                break
                        except Exception:
                            break

                    if youtube_url:
                        print(f"[yt-ads-spy] Found video! Getting details...")
                        info = get_youtube_details(context, youtube_url)
                        info["ad_index"] = len(results) + 1
                        info["advertiser"] = domain
                        info["total_ads_on_page"] = total_ads
                        info["ads_checked"] = i + 1
                        results.append(info)
                        consecutive_dupes = 0
                        print(f"[yt-ads-spy] Video {len(results)}: {info['title'][:60]}...")
                    else:
                        consecutive_dupes += 1

                except Exception:
                    consecutive_dupes += 1

            print(f"[yt-ads-spy] Extracted {len(results)} YouTube videos.")
            return results, domain

        except Exception as e:
            print(f"[yt-ads-spy] Error: {e}")
            return results, domain
        finally:
            browser.close()


# --- Markdown generation ---

def generate_markdown(videos: list, advertiser: str, brand_slug: str) -> str:
    """Generate Obsidian Markdown for all YouTube video ads."""
    today = date.today().isoformat()
    lines = [
        f"# {advertiser} — YouTube Ads\n",
        f"> Scraped on {today} | {len(videos)} videos found\n",
    ]

    for i, video in enumerate(videos, 1):
        title = video.get('title', 'Unknown')
        url = video.get('youtube_url', '')
        views = video.get('views', '')
        upload_date = video.get('upload_date', '')
        transcript = video.get('transcript', '')

        # Extract video ID for thumbnail
        vid_id = ""
        if "v=" in url:
            vid_id = url.split("v=")[-1].split("&")[0]

        lines.append(f"## Video {i}: {escape_markdown(title)}")
        lines.append(f"**URL:** {url}")

        if views:
            # Format view count
            try:
                view_num = int(views)
                if view_num >= 1_000_000:
                    views_fmt = f"{view_num/1_000_000:.1f}M"
                elif view_num >= 1_000:
                    views_fmt = f"{view_num/1_000:.1f}K"
                else:
                    views_fmt = str(view_num)
                lines.append(f"**Views:** {views_fmt} ({view_num:,})")
            except (ValueError, TypeError):
                lines.append(f"**Views:** {views}")

        if upload_date:
            lines.append(f"**Upload Date:** {upload_date}")

        lines.append("")

        # YouTube thumbnail (these don't expire)
        if vid_id:
            lines.append(f"![Thumbnail](https://img.youtube.com/vi/{vid_id}/maxresdefault.jpg)")
            lines.append("")

        if transcript:
            lines.append("<details>")
            lines.append("<summary>Transcript</summary>")
            lines.append("")
            lines.append(escape_markdown(transcript))
            lines.append("")
            lines.append("</details>")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# --- CLI ---

def parse_args():
    parser = argparse.ArgumentParser(description="Scrape Google Ads Transparency for YouTube video ads")
    parser.add_argument("domain", help="Advertiser domain (e.g. nike.com) or direct Ads Transparency URL")
    parser.add_argument("--max-videos", type=int, default=20, help="Maximum videos to find (default: 20)")
    parser.add_argument("--output-dir", default=os.path.expanduser("~/obsidian-vault/youtube-ads"),
                        help="Output directory (default: ~/obsidian-vault/youtube-ads)")
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"[yt-ads-spy] Scraping YouTube ads for: {args.domain}")
    print(f"[yt-ads-spy] Max videos: {args.max_videos}")
    print(f"[yt-ads-spy] Output: {args.output_dir}")

    results = []
    advertiser = args.domain

    try:
        results, advertiser = scrape_ads(args.domain, args.max_videos)
    except KeyboardInterrupt:
        print("\n[yt-ads-spy] Interrupted! Saving partial results...")
    except Exception as e:
        print(f"[yt-ads-spy] Scraping failed: {e}")
    finally:
        if not results:
            print("[yt-ads-spy] No videos found.")
            sys.exit(1)

        brand_slug = slugify(advertiser)
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        brand_dir = output_dir / brand_slug
        brand_dir.mkdir(parents=True, exist_ok=True)

        print(f"[yt-ads-spy] Generating Markdown...")
        markdown = generate_markdown(results, advertiser, brand_slug)

        md_path = brand_dir / f"{brand_slug}.md"
        md_path.write_text(markdown, encoding="utf-8")

        print(f"[yt-ads-spy] Done! Saved {len(results)} videos")
        print(f"[yt-ads-spy] Output: {md_path}")


if __name__ == "__main__":
    main()
