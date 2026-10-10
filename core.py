cat > ~/webbox/webbox/core.py << 'PYEOF'
#!/usr/bin/env python3
"""
webbox - سحب موقع كامل وحفظه محلياً
"""
import os
import sys
import re
import json
import time
import hashlib
from urllib.parse import urlparse, urljoin, unquote
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


R = "\033[91m"; G = "\033[92m"; Y = "\033[93m"
B = "\033[94m"; C = "\033[96m"; W = "\033[0m"
BOLD = "\033[1m"

class WebBox:
    def __init__(self, url, max_depth=3, max_pages=100, delay=0.3, output=None):
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        self.start_url = url
        self.base_domain = urlparse(url).netloc
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay = delay

        safe_name = re.sub(r'[^\w\-.]', '_', self.base_domain)
        if output:
            self.output_dir = os.path.abspath(output)
        else:
            self.output_dir = os.path.join(
                os.path.expanduser("~"), "downloads", safe_name
            )

        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5,
                        status_forcelist=[500, 502, 503, 504])
        self.session.mount("http://", HTTPAdapter(max_retries=retries))
        self.session.mount("https://", HTTPAdapter(max_retries=retries))
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36"
        })

        self.visited = set()
        self.downloaded = []
        self.failed = []
        self.assets = []

    def log(self, msg, color=W):
        print(f"{color}{msg}{W}")

    def _safe_path(self, url):
        parsed = urlparse(url)
        path = parsed.path or "/"
        if path.endswith("/"):
            path += "index.html"
        elif "." not in os.path.basename(path):
            path += "/index.html"

        if parsed.query:
            h = hashlib.md5(parsed.query.encode()).hexdigest()[:8]
            name, ext = os.path.splitext(path)
            path = f"{name}_{h}{ext or '.html'}"

        path = unquote(path)
        path = re.sub(r'[<>:"|?*]', '_', path)
        path = path.lstrip("/")

        full = os.path.normpath(os.path.join(self.output_dir, path))
        if not full.startswith(self.output_dir):
            full = os.path.join(self.output_dir, "misc",
                                hashlib.md5(url.encode()).hexdigest() + ".bin")
        return full

    def _is_same_domain(self, url):
        try:
            return urlparse(url).netloc == self.base_domain
        except:
            return False

    def _download_asset(self, url):
        if url in self.visited:
            return
        self.visited.add(url)
        try:
            r = self.session.get(url, timeout=15, stream=True)
            if r.status_code != 200:
                self.failed.append((url, r.status_code))
                return
            path = self._safe_path(url)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            size = os.path.getsize(path)
            self.assets.append({"url": url, "path": path, "size": size})
            self.log(f"  {G}✓{W} [{size//1024}KB] {url[:70]}")
            time.sleep(self.delay)
        except Exception as e:
            self.failed.append((url, str(e)[:50]))
            self.log(f"  {R}✗{W} {url[:70]} — {str(e)[:40]}")

    def _process_html(self, url, html, depth):
        soup = BeautifulSoup(html, "lxml")
        assets_to_get = set()

        for link in soup.find_all("link", rel="stylesheet"):
            href = link.get("href")
            if href:
                assets_to_get.add(urljoin(url, href))

        for script in soup.find_all("script", src=True):
            assets_to_get.add(urljoin(url, script["src"]))

        for img in soup.find_all("img", src=True):
            assets_to_get.add(urljoin(url, img["src"]))

        for source in soup.find_all("source", srcset=True):
            for part in source["srcset"].split(","):
                src = part.strip().split()[0]
                if src:
                    assets_to_get.add(urljoin(url, src))

        for asset_url in assets_to_get:
            if asset_url.startswith(("http://", "https://")):
                self._download_asset(asset_url)

        next_pages = []
        if depth < self.max_depth:
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith(("mailto:", "tel:", "javascript:", "#")):
                    continue
                full = urljoin(url, href)
                if (self._is_same_domain(full)
                        and full not in self.visited
                        and len(self.visited) < self.max_pages):
                    next_pages.append(full)

        return next_pages

    def _crawl(self, url, depth):
        if url in self.visited or len(self.visited) >= self.max_pages:
            return
        self.visited.add(url)
        try:
            r = self.session.get(url, timeout=15)
            if r.status_code != 200:
                self.failed.append((url, r.status_code))
                self.log(f"{R}✗{W} [{r.status_code}] {url[:70]}")
                return

            content_type = r.headers.get("Content-Type", "")
            if "html" not in content_type.lower():
                self.log(f"{Y}⊘{W} تخطي: {url[:60]}")
                return

            path = self._safe_path(url)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", errors="ignore") as f:
                f.write(r.text)

            size = len(r.text)
            self.downloaded.append({"url": url, "path": path, "size": size})
            indent = "  " * depth
            self.log(f"{indent}{G}✓{W} [{size//1024}KB] {url[:70]}")

            next_pages = self._process_html(url, r.text, depth)
            for next_url in next_pages:
                time.sleep(self.delay)
                self._crawl(next_url, depth + 1)

        except Exception as e:
            self.failed.append((url, str(e)[:50]))
            self.log(f"{R}✗{W} {url[:70]} — {str(e)[:40]}")

    def run(self):
        print(f"\n{C}{'='*60}{W}")
        print(f"{BOLD}{C}webbox - سحب موقع كامل{W}")
        print(f"{C}{'='*60}{W}\n")
        print(f"{B}الهدف:{W}      {self.start_url}")
        print(f"{B}المجلد:{W}      {self.output_dir}")
        print(f"{B}العمق:{W}       {self.max_depth}")
        print(f"{B}الحد:{W}        {self.max_pages} صفحة\n")

        os.makedirs(self.output_dir, exist_ok=True)
        start = time.time()
        self.log(f"{C}[بدء السحب...]{W}\n")
        self._crawl(self.start_url, 0)
        elapsed = time.time() - start

        report = {
            "target": self.start_url,
            "domain": self.base_domain,
            "date": datetime.now().isoformat(),
            "elapsed_seconds": round(elapsed, 2),
            "pages_downloaded": len(self.downloaded),
            "assets_downloaded": len(self.assets),
            "failed": len(self.failed),
            "pages": self.downloaded,
            "assets": self.assets,
            "failures": [{"url": u, "error": str(e)} for u, e in self.failed],
        }

        report_path = os.path.join(self.output_dir, "_webbox_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n{C}{'='*60}{W}")
        print(f"{BOLD}{G}✅ انتهى{W}")
        print(f"{C}{'='*60}{W}")
        print(f"{G}صفحات:{W}   {len(self.downloaded)}")
        print(f"{G}أصول:{W}    {len(self.assets)}")
        print(f"{Y}فشل:{W}     {len(self.failed)}")
        print(f"{C}الوقت:{W}   {elapsed:.1f}s")
        print(f"{B}المجلد:{W}  {self.output_dir}")
        print(f"{C}{'='*60}{W}\n")

        return report
PYEOF
