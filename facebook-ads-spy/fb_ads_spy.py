#!/usr/bin/env python3
"""
Facebook Ads Spy — CLI scraper for Meta Ad Library.
Outputs Obsidian-ready Markdown with downloaded images, videos, and transcripts.

Usage:
    python3 fb_ads_spy.py "Nike" [--max-ads 200] [--output-dir ~/obsidian-vault/facebook-ads]

Requirements:
    pip3 install requests patchright
    patchright install chromium
    brew install ffmpeg  (optional, for video transcription)

Set DEEPGRAM_API_KEY env var for video transcription (optional):
    export DEEPGRAM_API_KEY="your-key-here"
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import random
from datetime import date
from pathlib import Path
from urllib.parse import unquote

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

DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY", "")


# --- Utility functions ---

def delay(min_s=1.5, max_s=3):
    time.sleep(random.uniform(min_s, max_s))


def slugify(name: str) -> str:
    """Convert brand name to folder-safe slug: lowercase, hyphens, no special chars. Max 50 chars."""
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')[:50].strip('-')
    return slug


def escape_markdown(text: str) -> str:
    """Escape Markdown-significant characters in ad copy."""
    for ch in ['\\', '#', '*', '[', ']', '|', '`', '>', '!', '_', '{', '}']:
        text = text.replace(ch, f'\\{ch}')
    return text


def download_image(url: str, filepath: Path) -> bool:
    """Download an image from URL to filepath. Returns True on success."""
    try:
        resp = requests.get(url, timeout=15, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        })
        if resp.status_code == 200 and len(resp.content) > 100:
            filepath.write_bytes(resp.content)
            return True
    except Exception:
        pass
    return False


def download_video(url: str, filepath: Path) -> bool:
    """Download a video from URL to filepath. Uses streaming for large files. Returns True on success."""
    try:
        resp = requests.get(url, timeout=120, stream=True, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        })
        if resp.status_code == 200:
            size = 0
            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
                    size += len(chunk)
            if size > 1000:
                return True
            else:
                filepath.unlink(missing_ok=True)
    except Exception:
        filepath.unlink(missing_ok=True)
    return False


def find_ffmpeg() -> str:
    """Find ffmpeg binary path."""
    import shutil
    path = shutil.which("ffmpeg")
    if path:
        return path
    # Common locations
    for p in ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg", "/usr/bin/ffmpeg"]:
        if os.path.exists(p):
            return p
    return ""


def convert_mp4_to_mp3(mp4_path: Path, mp3_path: Path) -> bool:
    """Convert MP4 to MP3 using ffmpeg. Returns True on success."""
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        return False
    try:
        result = subprocess.run(
            [ffmpeg, "-i", str(mp4_path), "-vn", "-acodec", "libmp3lame",
             "-ab", "128k", "-ar", "44100", "-y", str(mp3_path)],
            capture_output=True, timeout=60
        )
        return result.returncode == 0 and mp3_path.exists() and mp3_path.stat().st_size > 100
    except Exception:
        return False


def transcribe_audio(mp3_path: Path) -> str:
    """Transcribe MP3 using Deepgram nova-3. Returns transcript text or empty string."""
    if not DEEPGRAM_API_KEY:
        return ""
    try:
        with open(mp3_path, 'rb') as f:
            audio_data = f.read()
        resp = requests.post(
            'https://api.deepgram.com/v1/listen',
            headers={'Authorization': f'Token {DEEPGRAM_API_KEY}', 'Content-Type': 'audio/mp3'},
            params={'model': 'nova-3', 'smart_format': 'true', 'language': 'en'},
            data=audio_data,
            timeout=120
        )
        resp.raise_for_status()
        result = resp.json()
        transcript = result['results']['channels'][0]['alternatives'][0]['transcript']
        return transcript.strip()
    except Exception as e:
        print(f"[ads-spy] Transcription failed: {e}")
        return ""


# --- Browser helper functions ---

def dismiss_popups(page):
    selectors = [
        'button[data-cookiebanner="accept_button"]',
        'button:has-text("Accept All")',
        'button:has-text("Accept all")',
        'button:has-text("Allow all cookies")',
        '[aria-label="Decline optional cookies"]',
        'button:has-text("Not Now")',
        'button:has-text("Not now")',
    ]
    for sel in selectors:
        try:
            el = page.query_selector(sel)
            if el and el.is_visible():
                el.click()
                delay(1, 2)
        except Exception:
            continue


def _click_advertiser_from_dropdown(page):
    skip_texts = [
        "search this exact phrase", "search this", "ad library report",
        "ad library api", "branded content", "ad category", "choose an",
        "all ads", "ad library", "system status", "subscribe", "faq",
        "about ads", "privacy", "terms", "cookies", "meta ©",
        "advertisers",
    ]

    # Strategy 1: Items with "follow" text
    try:
        follow_els = page.query_selector_all('span:has-text("follow"), span:has-text("Follow")')
        for el in follow_els:
            try:
                parent = el
                for _ in range(8):
                    parent = parent.evaluate_handle('el => el.parentElement').as_element()
                    if not parent:
                        break
                    role = parent.get_attribute('role') or ''
                    tag = parent.evaluate('el => el.tagName') or ''
                    if role in ('option', 'link', 'button', 'menuitem') or tag in ('A', 'LI'):
                        text = (parent.inner_text() or "").strip()
                        name = text.split('\n')[0].strip()
                        if name and len(name) > 1:
                            parent.click()
                            delay(4, 6)
                            return name
            except Exception:
                continue
    except Exception:
        pass

    # Strategy 2: Dropdown options
    for sel in [
        'ul[role="listbox"] li',
        '[role="listbox"] [role="option"]',
        '[role="option"]',
        'li[role="option"]',
    ]:
        try:
            items = page.query_selector_all(sel)
            for item in items:
                text = (item.inner_text() or "").strip()
                text_lower = text.lower()
                if any(skip in text_lower for skip in skip_texts):
                    continue
                if not text or len(text) < 2:
                    continue
                name = text.split('\n')[0].strip()
                item.click()
                delay(4, 6)
                return name
        except Exception:
            continue

    # Strategy 3: Links with view_all_page_id
    try:
        links = page.query_selector_all('a[href*="view_all_page_id"]')
        for link in links:
            if link.is_visible():
                text = (link.inner_text() or "").strip()
                name = text.split('\n')[0].strip()
                if name:
                    link.click()
                    delay(4, 6)
                    return name
    except Exception:
        pass

    return None


def extract_ads_from_page(page):
    return page.evaluate("""
    () => {
        const results = [];
        const allElements = document.querySelectorAll('*');
        const libraryIdElements = [];
        for (const el of allElements) {
            const directText = Array.from(el.childNodes)
                .filter(n => n.nodeType === 3)
                .map(n => n.textContent)
                .join('');
            if (directText.includes('Library ID:')) {
                libraryIdElements.push(el);
            }
        }

        const processedIds = new Set();

        for (const idEl of libraryIdElements) {
            try {
                const idText = idEl.innerText || '';
                const idMatch = idText.match(/Library ID:\\s*(\\d+)/);
                if (!idMatch) continue;
                const libraryId = idMatch[1];
                if (processedIds.has(libraryId)) continue;
                processedIds.add(libraryId);

                let card = idEl;
                for (let i = 0; i < 10; i++) {
                    if (!card.parentElement) break;
                    card = card.parentElement;
                    const rect = card.getBoundingClientRect();
                    if (rect.height > 300 && card.querySelector('img')) break;
                }

                const cardText = card.innerText || '';

                let advertiserName = '';
                const nameLinks = card.querySelectorAll('a[role="link"]');
                for (const link of nameLinks) {
                    const t = (link.innerText || '').trim();
                    if (t && t.length > 1 && t.length < 80 &&
                        !t.includes('See ad details') && !t.includes('Library') &&
                        !t.includes('Learn more') && !t.includes('Report')) {
                        advertiserName = t;
                        break;
                    }
                }

                const dateMatch = cardText.match(/Started running on\\s+([\\w\\s,]+\\d{4})/);
                const startDate = dateMatch ? dateMatch[1].trim() : '';

                let status = '';
                if (cardText.includes('Active')) status = 'Active';
                if (cardText.includes('Inactive')) status = 'Inactive';

                const platforms = [];
                const platformImgs = card.querySelectorAll('img[alt]');
                for (const img of platformImgs) {
                    const alt = (img.getAttribute('alt') || '').toLowerCase();
                    if (alt.includes('facebook') && !platforms.includes('Facebook')) platforms.push('Facebook');
                    if (alt.includes('instagram') && !platforms.includes('Instagram')) platforms.push('Instagram');
                    if (alt.includes('messenger') && !platforms.includes('Messenger')) platforms.push('Messenger');
                    if (alt.includes('audience') && !platforms.includes('Audience Network')) platforms.push('Audience Network');
                }

                let adCopy = '';
                const allDivs = card.querySelectorAll('div, span');
                for (const el of allDivs) {
                    const directChildren = el.childNodes;
                    let directText = '';
                    for (const child of directChildren) {
                        if (child.nodeType === 3) directText += child.textContent;
                        if (child.nodeType === 1 && ['BR', 'SPAN', 'A', 'B', 'I', 'EM', 'STRONG'].includes(child.tagName)) {
                            directText += child.textContent;
                        }
                    }
                    directText = directText.trim();
                    if (directText.length > 30 && directText.length < 3000 &&
                        !directText.includes('Library ID') &&
                        !directText.includes('Started running') &&
                        !directText.includes('Platforms') &&
                        !directText.includes('See ad details') &&
                        !directText.includes('multiple versions') &&
                        directText.length > adCopy.length) {
                        adCopy = directText;
                    }
                }

                let landingUrl = '';
                const allLinks = card.querySelectorAll('a[href]');
                for (const link of allLinks) {
                    const href = link.getAttribute('href') || '';
                    if (href.startsWith('https://l.facebook.com/l.php')) {
                        const uMatch = href.match(/[?&]u=([^&]+)/);
                        if (uMatch) {
                            landingUrl = decodeURIComponent(uMatch[1]);
                            break;
                        }
                    }
                    if (href && !href.includes('facebook.com') && !href.includes('fb.com') &&
                        !href.startsWith('#') && !href.startsWith('/') &&
                        (href.startsWith('http://') || href.startsWith('https://'))) {
                        landingUrl = href;
                        break;
                    }
                }

                let ctaText = '';
                const ctaCandidates = ['Install Now', 'Learn More', 'Shop Now', 'Sign Up',
                                       'Download', 'Book Now', 'Contact Us', 'Get Offer',
                                       'Apply Now', 'Subscribe', 'Watch More', 'Listen Now'];
                for (const cta of ctaCandidates) {
                    if (cardText.includes(cta)) { ctaText = cta; break; }
                }

                const images = [];
                const imgEls = card.querySelectorAll('img[src]');
                for (const img of imgEls) {
                    const src = img.getAttribute('src') || '';
                    const w = img.width || img.naturalWidth || 0;
                    const h = img.height || img.naturalHeight || 0;
                    if (src && w > 80 && h > 80 && !src.includes('emoji')) {
                        images.push(src);
                    }
                }

                const videos = [];
                const videoEls = card.querySelectorAll('video[src], video source[src]');
                for (const vid of videoEls) {
                    const src = vid.getAttribute('src') || '';
                    if (src) videos.push(src);
                }
                const posterEls = card.querySelectorAll('video[poster]');
                for (const vid of posterEls) {
                    const poster = vid.getAttribute('poster') || '';
                    if (poster) images.push(poster);
                }

                const adType = videos.length > 0 ? 'video' : (images.length > 0 ? 'image' : 'unknown');

                results.push({
                    library_id: libraryId,
                    advertiser_name: advertiserName,
                    status: status,
                    start_date: startDate,
                    ad_copy: adCopy,
                    landing_url: landingUrl,
                    cta: ctaText,
                    ad_type: adType,
                    image_urls: images.join(' | '),
                    video_urls: videos.join(' | '),
                    platforms: platforms.join(', '),
                });
            } catch(e) {}
        }
        return results;
    }
    """)


# --- Main scraping function ---

def scrape_ads(keyword: str, max_ads: int = 200):
    """
    Scrape Facebook Ad Library for an advertiser.
    Returns (ads_list, advertiser_name) tuple.
    """
    print(f"[ads-spy] Opening Facebook Ad Library...")

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome",
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--window-size=1400,900",
            ],
        )
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            locale="en-US",
        )
        page = context.new_page()
        ads_data = []
        advertiser_name = None

        try:
            # Navigate to Ad Library
            url = (
                f"https://www.facebook.com/ads/library/"
                f"?active_status=all&ad_type=all&country=ALL"
                f"&q={keyword.replace(' ', '%20')}"
            )
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            delay(5, 7)
            dismiss_popups(page)
            delay(2, 3)

            # Retype keyword to trigger autocomplete
            print(f"[ads-spy] Searching for '{keyword}'...")
            search_bar = None
            for sel in [
                'input[placeholder*="Search by keyword"]',
                'input[type="search"]',
                'input[aria-label*="Search"]',
            ]:
                try:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        search_bar = el
                        break
                except Exception:
                    continue

            if not search_bar:
                for sb in page.query_selector_all('[role="searchbox"]'):
                    try:
                        if sb.is_visible():
                            box = sb.bounding_box()
                            if box and box['width'] > 100:
                                search_bar = sb
                                break
                    except Exception:
                        continue

            if search_bar:
                search_bar.click()
                delay(0.5, 1)
                page.keyboard.press("Meta+a")
                page.keyboard.press("Backspace")
                delay(0.5, 1)
                for char in keyword:
                    page.keyboard.press(char)
                    time.sleep(random.uniform(0.1, 0.2))
                delay(3, 5)
                advertiser_name = _click_advertiser_from_dropdown(page)

            # If dropdown returned garbage (ad copy instead of name), discard it
            if advertiser_name and len(advertiser_name) > 80:
                print(f"[ads-spy] Dropdown returned text too long, ignoring...")
                advertiser_name = None

            if not advertiser_name:
                print("[ads-spy] No advertiser found in dropdown, using keyword search...")
                page.keyboard.press("Enter")
                delay(4, 6)
            else:
                print(f"[ads-spy] Found advertiser: {advertiser_name}")

            dismiss_popups(page)

            # Scroll to load ads
            print(f"[ads-spy] Loading ads (target: {max_ads})...")
            prev_height = 0
            stale_rounds = 0

            for attempt in range(40):
                body_text = page.inner_text('body')
                lib_ids = re.findall(r'Library ID:\s*\d+', body_text)
                current_count = len(lib_ids)

                if current_count >= max_ads:
                    break

                current_height = page.evaluate("document.body.scrollHeight")
                if current_height == prev_height:
                    stale_rounds += 1
                    if stale_rounds >= 5:
                        break
                else:
                    stale_rounds = 0
                prev_height = current_height

                print(f"[ads-spy] Loaded {current_count}/{max_ads} ads...")

                for sel in [
                    'button:has-text("See more")',
                    'div[role="button"]:has-text("See more")',
                ]:
                    try:
                        btn = page.query_selector(sel)
                        if btn and btn.is_visible():
                            btn.click()
                            delay(2, 3)
                            break
                    except Exception:
                        continue

                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                delay(2, 3)

            # Extract ads
            print("[ads-spy] Extracting ad data...")
            ads_data = extract_ads_from_page(page)

            if not ads_data:
                print("[ads-spy] No ads found on page.")
                return [], advertiser_name or keyword

            ads_data = ads_data[:max_ads]

            # Enrich ads missing landing URLs
            missing_urls = sum(1 for a in ads_data if not a.get('landing_url'))
            if missing_urls > 0:
                needs_url = [a for a in ads_data if not a.get('landing_url') and a.get('library_id')]
                to_enrich = needs_url[:min(missing_urls, 20)]
                print(f"[ads-spy] Enriching {len(to_enrich)} ads with landing URLs...")

                for i, ad in enumerate(to_enrich):
                    lid = ad['library_id']
                    detail_url = f"https://www.facebook.com/ads/library/?id={lid}"
                    print(f"[ads-spy] Enriching ad {i+1}/{len(to_enrich)}...")

                    detail_page = context.new_page()
                    try:
                        detail_page.goto(detail_url, wait_until="domcontentloaded", timeout=30000)
                        delay(3, 5)
                        dismiss_popups(detail_page)

                        links = detail_page.query_selector_all('a[href]')
                        for link in links:
                            try:
                                href = link.get_attribute('href') or ""
                                if 'l.facebook.com/l.php' in href:
                                    u_match = re.search(r'[?&]u=([^&]+)', href)
                                    if u_match:
                                        ad['landing_url'] = unquote(u_match.group(1))
                                        break
                                elif (href.startswith('http') and 'facebook.com' not in href and
                                      'fb.com' not in href and not href.startswith('#')):
                                    ad['landing_url'] = href
                                    break
                            except Exception:
                                continue

                        if not ad.get('image_urls'):
                            imgs = []
                            for img in detail_page.query_selector_all('img[src]'):
                                try:
                                    src = img.get_attribute('src') or ""
                                    w = img.evaluate('el => el.naturalWidth || el.width') or 0
                                    if src and w > 80:
                                        imgs.append(src)
                                except Exception:
                                    continue
                            if imgs:
                                ad['image_urls'] = ' | '.join(imgs)

                    except Exception:
                        pass
                    finally:
                        detail_page.close()

            print(f"[ads-spy] Extracted {len(ads_data)} ads.")
            return ads_data, advertiser_name or keyword

        except Exception as e:
            print(f"[ads-spy] Error: {e}")
            return ads_data, advertiser_name or keyword
        finally:
            browser.close()


# --- Markdown generation ---

def generate_markdown(ads: list, brand_name: str, brand_slug: str, output_dir: Path) -> str:
    """
    Download images/videos, transcribe video audio, and generate Obsidian Markdown.
    Returns the Markdown content string.
    """
    images_dir = output_dir / brand_slug / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    videos_dir = output_dir / brand_slug / "videos"
    videos_dir.mkdir(parents=True, exist_ok=True)
    audio_dir = output_dir / brand_slug / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()
    total_video_ads = sum(1 for a in ads if a.get('ad_type') == 'video')
    total_image_ads = sum(1 for a in ads if a.get('ad_type') == 'image')
    lines = [
        f"# {brand_name} — Facebook Ads\n",
        f"> Scraped on {today} | {len(ads)} ads found ({total_image_ads} image, {total_video_ads} video)\n",
    ]

    for i, ad in enumerate(ads, 1):
        ad_type = ad.get('ad_type', 'unknown')
        lines.append(f"## Ad {i} ({ad_type})")

        lib_id = ad.get('library_id', '')
        if lib_id:
            lines.append(f"**Library ID:** {lib_id}")

        start_date = ad.get('start_date', '')
        if start_date:
            lines.append(f"**Start Date:** {start_date}")

        landing_url = ad.get('landing_url', '')
        if landing_url:
            lines.append(f"**Landing URL:** {landing_url}")

        ad_copy = ad.get('ad_copy', '')
        if ad_copy:
            lines.append(f"**Ad Copy:** {escape_markdown(ad_copy)}")

        lines.append("")  # blank line before media

        # Download videos + extract audio + transcribe
        video_urls = ad.get('video_urls', '')
        if video_urls:
            urls = [u.strip() for u in video_urls.split(' | ') if u.strip()]
            for j, vid_url in enumerate(urls, 1):
                vid_filename = f"ad-{i}-{j}.mp4"
                mp3_filename = f"ad-{i}-{j}.mp3"
                vid_filepath = videos_dir / vid_filename
                mp3_filepath = audio_dir / mp3_filename

                print(f"[ads-spy] Downloading video {vid_filename}...")
                if download_video(vid_url, vid_filepath):
                    lines.append(f"![[videos/{vid_filename}]]")

                    # Convert to MP3
                    print(f"[ads-spy] Extracting audio → {mp3_filename}...")
                    if convert_mp4_to_mp3(vid_filepath, mp3_filepath):
                        lines.append(f"Audio: ![[audio/{mp3_filename}]]")

                        # Transcribe with Deepgram
                        if DEEPGRAM_API_KEY:
                            print(f"[ads-spy] Transcribing {mp3_filename}...")
                            transcript = transcribe_audio(mp3_filepath)
                            if transcript:
                                lines.append("")
                                lines.append(f"**Transcript:**")
                                lines.append(f"> {transcript}")
                            else:
                                lines.append("*Transcription failed or no speech detected*")
                        else:
                            lines.append("*Set DEEPGRAM_API_KEY to enable transcription*")
                    else:
                        lines.append("*Audio extraction failed (install ffmpeg)*")
                else:
                    lines.append(f"[Video unavailable — CDN link expired or blocked]")

        # Download images
        image_urls = ad.get('image_urls', '')
        if image_urls:
            urls = [u.strip() for u in image_urls.split(' | ') if u.strip()]
            for j, img_url in enumerate(urls, 1):
                filename = f"ad-{i}-{j}.jpg"
                filepath = images_dir / filename
                if download_image(img_url, filepath):
                    lines.append(f"![Ad Image](images/{filename})")
                else:
                    lines.append("[Image unavailable]")
        elif not video_urls:
            lines.append("*No media*")

        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# --- CLI ---

def parse_args():
    parser = argparse.ArgumentParser(description="Scrape Facebook Ad Library for an advertiser")
    parser.add_argument("advertiser", help="Advertiser name to search for")
    parser.add_argument("--max-ads", type=int, default=200, help="Maximum ads to scrape (default: 200)")
    parser.add_argument("--output-dir", default=os.path.expanduser("~/obsidian-vault/facebook-ads"),
                        help="Output directory (default: ~/obsidian-vault/facebook-ads)")
    return parser.parse_args()


def main():
    args = parse_args()
    print(f"[ads-spy] Scraping Facebook ads for: {args.advertiser}")
    print(f"[ads-spy] Max ads: {args.max_ads}")
    print(f"[ads-spy] Output: {args.output_dir}")

    ads_data = []
    brand_name = args.advertiser

    try:
        ads_data, brand_name = scrape_ads(args.advertiser, args.max_ads)
    except KeyboardInterrupt:
        print("\n[ads-spy] Interrupted! Saving partial results...")
    except Exception as e:
        print(f"[ads-spy] Scraping failed: {e}")
    finally:
        if not ads_data:
            print("[ads-spy] No ads found.")
            sys.exit(1)

        # Generate output even on partial failure
        brand_slug = slugify(brand_name)
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"[ads-spy] Downloading media, extracting audio, transcribing...")
        markdown = generate_markdown(ads_data, brand_name, brand_slug, output_dir)

        md_path = output_dir / brand_slug / f"{brand_slug}.md"
        md_path.write_text(markdown, encoding="utf-8")

        images_path = output_dir / brand_slug / "images"
        total_images = sum(
            1 for f in images_path.iterdir()
            if f.is_file()
        ) if images_path.exists() else 0

        videos_path = output_dir / brand_slug / "videos"
        total_videos = sum(
            1 for f in videos_path.iterdir()
            if f.is_file()
        ) if videos_path.exists() else 0

        audio_path = output_dir / brand_slug / "audio"
        total_audio = sum(
            1 for f in audio_path.iterdir()
            if f.is_file()
        ) if audio_path.exists() else 0

        print(f"[ads-spy] Done! Saved {len(ads_data)} ads ({total_images} images, {total_videos} videos, {total_audio} transcripts)")
        print(f"[ads-spy] Output: {md_path}")


if __name__ == "__main__":
    main()
