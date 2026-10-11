cat > webbox/core.py << 'ENDOFFILE'
#!/usr/bin/env python3
"""webbox - سحب المواقع بكل ملفاتها"""
import os
import re
import json
import time
from urllib.parse import urlparse, urljoin
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .utils import (
    C, is_asset, is_spa, safe_path, get_extension,
    should_skip, clean_url
)


class WebBox:
    """أداة سحب المواقع"""

    def __init__(self, url, max_depth=3, max_pages=100,
                 delay=0.3, output=None, user_agent=None):
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        # نظّف الرابط
        url = clean_url(url)

        self.start_url = url
        self.base_domain = urlparse(url).netloc
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay = delay
        self.is_spa_site = False

        # مجلد الحفظ
        safe_name = re.sub(r'[^\w\-.]', '_', self.base_domain)
        if output:
            self.output_dir = os.path.abspath(output)
        else:
            self.output_dir = os.path.join(
                "/storage/emulated/0/webbox", safe_name
            )

        # الجلسة
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504]
        )
        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.headers.update({
            "User-Agent": user_agent or (
                "Mozilla/5.0 (Linux; Android 10) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Mobile Safari/537.36"
            ),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        })

        # التتبع
        self.visited = set()
        self.downloaded = []
        self.failed = []
        self.assets = []

    # ═══════════════════════════════════════════════════
    # طباعة
    # ═══════════════════════════════════════════════════
    def log(self, msg, color=C.WHITE):
        print(f"{color}{msg}{C.WHITE}")

    # ═══════════════════════════════════════════════════
    # فحص النطاق
    # ═══════════════════════════════════════════════════
    def _is_same_domain(self, url):
        try:
            return urlparse(url).netloc == self.base_domain
        except Exception:
            return False

    # ═══════════════════════════════════════════════════
    # سحب ملف
    # ═══════════════════════════════════════════════════
    def _download_asset(self, url):
        url = clean_url(url)

        if url in self.visited:
            return
        self.visited.add(url)

        try:
            if url.startswith("data:"):
                return

            r = self.session.get(url, timeout=20, stream=True)
            if r.status_code != 200:
                self.failed.append((url, r.status_code))
                return

            path = safe_path(url, self.output_dir)
            os.makedirs(os.path.dirname(path), exist_ok=True)

            with open(path, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk:
                        f.write(chunk)

            size = os.path.getsize(path)
            self.assets.append({
                "url": url, "path": path, "size": size
            })

            ext = get_extension(url)
            self.log(f"  {C.GREEN}✓{C.WHITE} [{size//1024}KB] "
                     f"{ext:<8} {url[:55]}")

            time.sleep(self.delay)

        except Exception as e:
            self.failed.append((url, str(e)[:50]))
            self.log(f"  {C.RED}✗{C.WHITE} {url[:55]} — {str(e)[:35]}")

    # ═══════════════════════════════════════════════════
    # استخراج الأصول من HTML
    # ═══════════════════════════════════════════════════
    def _extract_assets(self, url, html):
        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception as e:
            self.log(f"{C.YELLOW}⚠ فشل تحليل HTML: {e}{C.WHITE}")
            return set()

        assets = set()

        # CSS + preload
        for link in soup.find_all("link", href=True):
            rel = " ".join(link.get("rel", [])).lower()
            if any(k in rel for k in ["stylesheet", "preload", "prefetch"]):
                assets.add(urljoin(url, link["href"]))

        # JS
        for script in soup.find_all("script", src=True):
            assets.add(urljoin(url, script["src"]))

        # صور
        for img in soup.find_all("img"):
            for attr in ["src", "data-src", "data-original",
                         "data-lazy", "data-srcset"]:
                if img.get(attr):
                    assets.add(urljoin(url, img[attr]))
            if img.get("srcset"):
                for part in img["srcset"].split(","):
                    src = part.strip().split()[0]
                    if src:
                        assets.add(urljoin(url, src))

        # source
        for source in soup.find_all("source"):
            for attr in ["src", "srcset"]:
                if source.get(attr):
                    for part in source[attr].split(","):
                        src = part.strip().split()[0]
                        if src:
                            assets.add(urljoin(url, src))

        # فيديو/صوت
        for media in soup.find_all(["video", "audio"]):
            if media.get("src"):
                assets.add(urljoin(url, media["src"]))
            if media.get("poster"):
                assets.add(urljoin(url, media["poster"]))

        # iframe
        for iframe in soup.find_all("iframe", src=True):
            src = iframe["src"]
            if not src.startswith(("about:", "javascript:")):
                assets.add(urljoin(url, src))

        # embed/object
        for tag in soup.find_all(["embed", "object"]):
            for attr in ["src", "data"]:
                if tag.get(attr):
                    assets.add(urljoin(url, tag[attr]))

        # روابط ملفات
        for a in soup.find_all("a", href=True):
            full = urljoin(url, a["href"])
            if is_asset(full):
                assets.add(full)

        return assets

    # ═══════════════════════════════════════════════════
    # استخراج الروابط الداخلية
    # ═══════════════════════════════════════════════════
    def _extract_links(self, url, html, depth):
        if depth >= self.max_depth:
            return []

        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception:
            return []

        links = []

        for a in soup.find_all("a", href=True):
            href = a["href"]
            if should_skip(href):
                continue

            full = clean_url(urljoin(url, href))

            # تخطي الملفات
            if is_asset(full):
                continue

            if (self._is_same_domain(full)
                    and full not in self.visited
                    and len(self.visited) < self.max_pages):
                links.append(full)

        return links

    # ═══════════════════════════════════════════════════
    # سحب صفحة
    # ═══════════════════════════════════════════════════
    def _crawl(self, url, depth):
        url = clean_url(url)

        if url in self.visited or len(self.visited) >= self.max_pages:
            return
        self.visited.add(url)

        try:
            r = self.session.get(url, timeout=20)
            if r.status_code != 200:
                self.failed.append((url, r.status_code))
                self.log(f"{C.RED}✗{C.WHITE} [{r.status_code}] {url[:65]}")
                return

            content_type = r.headers.get("Content-Type", "").lower()

            # HTML / XML
            if "html" in content_type or "xml" in content_type:
                path = safe_path(url, self.output_dir)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8", errors="ignore") as f:
                    f.write(r.text)

                size = len(r.text)
                self.downloaded.append({
                    "url": url, "path": path, "size": size
                })
                indent = "  " * depth

                # فحص SPA
                if is_spa(r.text):
                    self.is_spa_site = True
                    self.log(f"{indent}{C.YELLOW}⚠ SPA (React/Vue) "
                             f"{size//1024}KB {url[:55]}{C.WHITE}")
                else:
                    self.log(f"{indent}{C.GREEN}✓{C.WHITE} "
                             f"[HTML {size//1024}KB] {url[:60]}")

                # سحب الأصول
                assets = self._extract_assets(url, r.text)
                for asset_url in assets:
                    self._download_asset(asset_url)

                # سحب الصفحات الداخلية
                if not is_spa(r.text):
                    links = self._extract_links(url, r.text, depth)
                    for next_url in links:
                        time.sleep(self.delay)
                        self._crawl(next_url, depth + 1)

            # ملف عادي
            else:
                path = safe_path(url, self.output_dir)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as f:
                    f.write(r.content)

                size = len(r.content)
                ext = get_extension(url)
                self.assets.append({
                    "url": url, "path": path, "size": size
                })
                self.log(f"  {C.GREEN}✓{C.WHITE} [{size//1024}KB] "
                         f"{ext:<8} {url[:55]}")

        except Exception as e:
            self.failed.append((url, str(e)[:50]))
            self.log(f"{C.RED}✗{C.WHITE} {url[:65]} — {str(e)[:35]}")

    # ═══════════════════════════════════════════════════
    # التشغيل
    # ═══════════════════════════════════════════════════
    def run(self):
        print(f"\n{C.CYAN}{'═'*62}{C.WHITE}")
        print(f"{C.BOLD}{C.CYAN}  webbox v2.1 - سحب موقع كامل{C.WHITE}")
        print(f"{C.CYAN}{'═'*62}{C.WHITE}\n")
        print(f"  {C.BLUE}الهدف:{C.WHITE}      {self.start_url}")
        print(f"  {C.BLUE}المجلد:{C.WHITE}      {self.output_dir}")
        print(f"  {C.BLUE}العمق:{C.WHITE}       {self.max_depth}")
        print(f"  {C.BLUE}الحد:{C.WHITE}        {self.max_pages} صفحة\n")

        os.makedirs(self.output_dir, exist_ok=True)
        start = time.time()
        self.log(f"{C.CYAN}[بدء السحب...]{C.WHITE}\n")

        self._crawl(self.start_url, 0)
        elapsed = time.time() - start

        # تقرير
        report = {
            "target": self.start_url,
            "domain": self.base_domain,
            "date": datetime.now().isoformat(),
            "version": "2.1.0",
            "elapsed_seconds": round(elapsed, 2),
            "is_spa": self.is_spa_site,
            "pages_downloaded": len(self.downloaded),
            "assets_downloaded": len(self.assets),
            "failed": len(self.failed),
            "pages": self.downloaded,
            "assets": self.assets,
            "failures": [
                {"url": u, "error": str(e)} for u, e in self.failed
            ],
        }

        report_path = os.path.join(
            self.output_dir, "_webbox_report.json"
        )
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # النتيجة
        print(f"\n{C.CYAN}{'═'*62}{C.WHITE}")
        print(f"{C.BOLD}{C.GREEN}  ✅ انتهى{C.WHITE}")
        print(f"{C.CYAN}{'═'*62}{C.WHITE}")
        print(f"  {C.GREEN}صفحات:{C.WHITE}   {len(self.downloaded)}")
        print(f"  {C.GREEN}ملفات:{C.WHITE}   {len(self.assets)}")
        print(f"  {C.YELLOW}فشل:{C.WHITE}     {len(self.failed)}")
        print(f"  {C.CYAN}الوقت:{C.WHITE}   {elapsed:.1f}s")

        if self.is_spa_site:
            print(f"\n  {C.YELLOW}⚠ ملاحظة: الموقع SPA "
                  f"(React/Vue){C.WHITE}")
            print(f"  {C.YELLOW}  المحتوى يُبنى بـ JavaScript "
                  f"— webbox تسحب HTML فقط{C.WHITE}")

        print(f"  {C.BLUE}المجلد:{C.WHITE}  {self.output_dir}")
        print(f"{C.CYAN}{'═'*62}{C.WHITE}\n")

        return report
ENDOFFILE
