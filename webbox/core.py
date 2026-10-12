#!/usr/bin/env python3
"""
webbox v3.0 - سحب المواقع بكل ملفاتها + دعم SPA
"""
import os
import re
import json
import time
import hashlib
import threading
import socketserver
import http.server
import webbrowser
from urllib.parse import urlparse, urljoin, urlencode
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .utils import (
    C, is_asset, is_spa, safe_path, get_extension,
    should_skip, clean_url
)


# ═══════════════════════════════════════════════════════════════════════════
# SPA Detection
# ═══════════════════════════════════════════════════════════════════════════
SPA_MARKERS = {
    "react": [r'<div id="root"', r'data-reactroot', r'__REACT_DEVTOOLS'],
    "vue": [r'<div id="app"', r'data-v-[a-f0-9]{8}', r'__VUE__', r'__NUXT__'],
    "angular": [r'ng-version=', r'_ngcontent', r'ng-app'],
    "svelte": [r'class="svelte-', r'__svelte'],
    "nextjs": [r'__NEXT_DATA__', r'<div id="__next"'],
}


def detect_spa(html: str) -> dict:
    """كشف نوع SPA"""
    if not html:
        return {"is_spa": False, "framework": None, "confidence": 0.0}

    sample = html[:10000]
    scores = {}

    for framework, patterns in SPA_MARKERS.items():
        matches = sum(
            1 for p in patterns
            if re.search(p, sample, re.IGNORECASE)
        )
        if matches > 0:
            scores[framework] = matches / len(patterns)

    if len(html) < 5000 and '<script' in html:
        scores["_small_html"] = 0.5

    if not scores:
        return {"is_spa": False, "framework": None, "confidence": 0.0}

    best = max(scores, key=scores.get)
    return {
        "is_spa": scores[best] > 0.3,
        "framework": best if not best.startswith("_") else "unknown",
        "confidence": scores[best],
    }


# ═══════════════════════════════════════════════════════════════════════════
# SPA Scripts Injection
# ═══════════════════════════════════════════════════════════════════════════
SPA_BEFORE = """
<script>
(function() {
    var originalPathname = window.location.pathname;
    var fileName = originalPathname.split('/').pop();
    if (fileName && fileName.indexOf('.html') !== -1) {
        var cleanPath = originalPathname.substring(0, originalPathname.lastIndexOf('/')) + '/';
        try { history.replaceState({}, '', cleanPath); } catch (e) {}
    }
    if (!document.querySelector('base')) {
        var base = document.createElement('base');
        base.href = './';
        document.head.insertBefore(base, document.head.firstChild);
    }
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations().then(function(regs) {
            regs.forEach(function(reg) { reg.unregister(); });
        });
    }
    window.__WEBBOX_SPA__ = true;
    console.log('[webbox] SPA fix (before) applied');
})();
</script>
"""


SPA_AFTER = """
<script>
(function() {
    var originalFetch = window.fetch;
    window.fetch = function(input, init) {
        var url = typeof input === 'string' ? input : input.url;
        return originalFetch.apply(this, arguments).catch(function(err) {
            var cacheKey = 'webbox_cache_' + btoa(url).substring(0, 50);
            var cached = localStorage.getItem(cacheKey);
            if (cached) {
                try {
                    var data = JSON.parse(cached);
                    console.log('[webbox] Served from cache:', url);
                    return new Response(JSON.stringify(data.body), {
                        status: data.status || 200,
                        headers: data.headers || { 'Content-Type': 'application/json' }
                    });
                } catch (e) {}
            }
            throw err;
        });
    };
    console.log('[webbox] API cache interception active');
})();
</script>
"""


SESSION_RESTORE_TEMPLATE = """
<script>
(function() {
    var session = {session_json};
    if (!session) return;
    if (session.cookies) {
        session.cookies.forEach(function(c) {
            try {
                document.cookie = c.name + '=' + c.value +
                    '; path=' + (c.path || '/') +
                    (c.domain ? '; domain=' + c.domain : '');
            } catch (e) {}
        });
    }
    if (session.storage) {
        try {
            if (session.storage.localStorage) {
                for (var k in session.storage.localStorage) {
                    localStorage.setItem(k, session.storage.localStorage[k]);
                }
            }
            if (session.storage.sessionStorage) {
                for (var k in session.storage.sessionStorage) {
                    sessionStorage.setItem(k, session.storage.sessionStorage[k]);
                }
            }
        } catch (e) {}
    }
    console.log('[webbox] Session restored');
})();
</script>
"""


def inject_spa_fix(html: str, spa_info: dict, session_data: dict = None) -> str:
    """حقن scripts الإصلاح"""
    if not spa_info.get("is_spa"):
        return html

    # BEFORE
    if "</head>" in html:
        html = html.replace("</head>", SPA_BEFORE + "</head>", 1)
    else:
        html = SPA_BEFORE + html

    # Session
    if session_data:
        session_script = SESSION_RESTORE_TEMPLATE.format(
            session_json=json.dumps(session_data, ensure_ascii=False)
        )
        if "<body" in html:
            html = re.sub(
                r'(<body[^>]*>)',
                r'\1' + session_script,
                html,
                count=1,
                flags=re.IGNORECASE
            )

    # AFTER
    if "</body>" in html:
        html = html.replace("</body>", SPA_AFTER + "</body>", 1)
    else:
        html += SPA_AFTER

    return html


# ═══════════════════════════════════════════════════════════════════════════
# API Cache
# ═══════════════════════════════════════════════════════════════════════════
class APICache:
    """حفظ API responses"""

    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.cache_dir = os.path.join(output_dir, "_webbox_api_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache = {}

    def _key(self, url):
        return hashlib.md5(url.encode()).hexdigest()

    def add(self, url, method, response_body, status, headers):
        key = self._key(f"{method}:{url}")
        self.cache[key] = {
            "url": url,
            "method": method,
            "status": status,
            "headers": dict(headers),
            "body": response_body,
        }

    def save(self):
        filepath = os.path.join(self.cache_dir, "responses.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
        return filepath


# ═══════════════════════════════════════════════════════════════════════════
# Session Manager
# ═══════════════════════════════════════════════════════════════════════════
class SessionManager:
    """حفظ الجلسة"""

    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.session_file = os.path.join(output_dir, "_webbox_session.json")
        self.data = {
            "cookies": [],
            "headers": {},
            "storage": {
                "localStorage": {},
                "sessionStorage": {},
            },
        }

    def add_cookies(self, cookies):
        for cookie in cookies:
            self.data["cookies"].append({
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain or "",
                "path": cookie.path or "/",
            })

    def add_headers(self, headers):
        important = ["authorization", "x-csrf-token", "content-type"]
        for k, v in headers.items():
            if k.lower() in important:
                self.data["headers"][k] = v

    def save(self):
        with open(self.session_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        return self.session_file

    def get_data(self):
        return self.data


# ═══════════════════════════════════════════════════════════════════════════
# Local Server
# ═══════════════════════════════════════════════════════════════════════════
class SPARequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handler مع SPA fallback"""

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        file_path = os.path.join(self.directory, path.lstrip('/'))

        if os.path.exists(file_path) and os.path.isfile(file_path):
            return super().do_GET()

        # SPA fallback
        index_file = os.path.join(self.directory, "index.html")
        if os.path.exists(index_file):
            self.path = "/index.html"
            return super().do_GET()

        return super().do_GET()

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()

    def log_message(self, format, *args):
        pass


def start_local_server(directory, port=8080, open_browser=True):
    """تشغيل السيرفر"""
    handler = lambda *args, **kwargs: SPARequestHandler(
        *args, directory=directory, **kwargs
    )

    try:
        httpd = socketserver.TCPServer(("", port), handler)
    except OSError as e:
        print(f"{C.R}❌ Port {port} busy: {e}{C.W}")
        return None

    url = f"http://localhost:{port}"
    print(f"\n{C.GREEN}🌐 Server: {url}{C.W}")
    print(f"{C.CYAN}📁 Serving: {directory}{C.W}")
    print(f"{C.YELLOW}⏹️  Ctrl+C to stop{C.W}\n")

    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}⏹️  Server stopped{C.W}")
    finally:
        httpd.server_close()


# ═══════════════════════════════════════════════════════════════════════════
# WebBox Main Class
# ═══════════════════════════════════════════════════════════════════════════
class WebBox:
    """أداة سحب المواقع"""

    def __init__(self, url, max_depth=3, max_pages=100,
                 delay=0.3, output=None, user_agent=None,
                 spa_mode=False, api_cache=False, save_session=False,
                 serve=False, serve_port=8080):
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        url = clean_url(url)

        self.start_url = url
        self.base_domain = urlparse(url).netloc
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay = delay
        self.is_spa_site = False
        self.spa_framework = None

        # SPA options
        self.spa_mode = spa_mode
        self.api_cache_enabled = api_cache
        self.save_session_enabled = save_session
        self.serve_after = serve
        self.serve_port = serve_port

        self.api_cache = None
        self.session_manager = None
        self.detected_spa = None

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
            total=3, backoff_factor=0.5,
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

        self.visited = set()
        self.downloaded = []
        self.failed = []
        self.assets = []

    # ═══════════════════════════════════════════════════════
    def log(self, msg, color=C.WHITE):
        print(f"{color}{msg}{C.WHITE}")

    def _is_same_domain(self, url):
        try:
            return urlparse(url).netloc == self.base_domain
        except Exception:
            return False

    # ═══════════════════════════════════════════════════════
    # Download asset
    # ═══════════════════════════════════════════════════════
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
            self.assets.append({"url": url, "path": path, "size": size})
            ext = get_extension(url)
            self.log(f"  {C.GREEN}✓{C.WHITE} [{size//1024}KB] "
                     f"{ext:<8} {url[:55]}")

            # حفظ API responses
            if self.api_cache and "json" in r.headers.get("Content-Type", "").lower():
                try:
                    self.api_cache.add(
                        url, "GET", r.text,
                        r.status_code, dict(r.headers)
                    )
                except Exception:
                    pass

            time.sleep(self.delay)

        except Exception as e:
            self.failed.append((url, str(e)[:50]))
            self.log(f"  {C.RED}✗{C.WHITE} {url[:55]} — {str(e)[:35]}")

    # ═══════════════════════════════════════════════════════
    # Extract assets from HTML
    # ═══════════════════════════════════════════════════════
    def _extract_assets(self, url, html):
        try:
            soup = BeautifulSoup(html, "html.parser")
        except Exception as e:
            self.log(f"{C.YELLOW}⚠ HTML parse failed: {e}{C.W}")
            return set()

        assets = set()

        # CSS + preload
        for link in soup.find_all("link", href=True):
            rel = " ".join(link.get("rel", [])).lower()
            if any(k in rel for k in ["stylesheet", "preload", "prefetch", "modulepreload"]):
                assets.add(urljoin(url, link["href"]))

        # Scripts
        for script in soup.find_all("script", src=True):
            assets.add(urljoin(url, script["src"]))

        # Images
        for img in soup.find_all("img"):
            for attr in ["src", "data-src", "data-original", "data-lazy"]:
                if img.get(attr):
                    assets.add(urljoin(url, img[attr]))
            if img.get("srcset"):
                for part in img["srcset"].split(","):
                    src = part.strip().split()[0]
                    if src:
                        assets.add(urljoin(url, src))

        # Sources (video/audio)
        for source in soup.find_all("source"):
            for attr in ["src", "srcset"]:
                if source.get(attr):
                    for part in source[attr].split(","):
                        src = part.strip().split()[0]
                        if src:
                            assets.add(urljoin(url, src))

        # Video/audio
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

        # Links to files
        for a in soup.find_all("a", href=True):
            full = urljoin(url, a["href"])
            if is_asset(full):
                assets.add(full)

        return assets

    # ═══════════════════════════════════════════════════════
    # Extract internal links
    # ═══════════════════════════════════════════════════════
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
            if is_asset(full):
                continue
            if (self._is_same_domain(full)
                    and full not in self.visited
                    and len(self.visited) < self.max_pages):
                links.append(full)
        return links

    # ═══════════════════════════════════════════════════════
    # Crawl
    # ═══════════════════════════════════════════════════════
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

            if "html" in content_type or "xml" in content_type:
                # ✅ كشف SPA
                spa_info = detect_spa(r.text)

                if spa_info["is_spa"] and not self.detected_spa:
                    self.detected_spa = spa_info
                    self.is_spa_site = True
                    self.spa_framework = spa_info["framework"]
                    self.log(f"{C.YELLOW}🔍 SPA detected: "
                             f"{spa_info['framework']} "
                             f"(confidence: {spa_info['confidence']:.2f}){C.W}")

                    if self.api_cache_enabled and not self.api_cache:
                        self.api_cache = APICache(self.output_dir)
                        self.log(f"{C.CYAN}📦 API cache enabled{C.W}")

                    if self.save_session_enabled and not self.session_manager:
                        self.session_manager = SessionManager(self.output_dir)
                        self.log(f"{C.CYAN}💾 Session save enabled{C.W}")

                # حقن SPA fix
                html = r.text
                if spa_info["is_spa"] and self.spa_mode:
                    session_data = None
                    if self.session_manager:
                        session_data = self.session_manager.get_data()

                    html = inject_spa_fix(html, spa_info, session_data=session_data)
                    self.log(f"{C.GREEN}💉 SPA fix injected{C.W}")

                # حفظ
                path = safe_path(url, self.output_dir)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8", errors="ignore") as f:
                    f.write(html)

                size = len(html)
                self.downloaded.append({
                    "url": url, "path": path, "size": size
                })
                indent = "  " * depth

                if self.is_spa_site and url == self.start_url:
                    self.log(f"{indent}{C.YELLOW}⚠ SPA (React/Vue) "
                             f"{size//1024}KB {url[:55]}{C.W}")
                else:
                    self.log(f"{indent}{C.GREEN}✓{C.WHITE} "
                             f"[HTML {size//1024}KB] {url[:60]}")

                # Assets
                assets = self._extract_assets(url, html)
                for asset_url in assets:
                    self._download_asset(asset_url)

                # Internal links
                if not self.is_spa_site:
                    links = self._extract_links(url, html, depth)
                    for next_url in links:
                        time.sleep(self.delay)
                        self._crawl(next_url, depth + 1)

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

    # ═══════════════════════════════════════════════════════
    # Run
    # ═══════════════════════════════════════════════════════
    def run(self):
        print(f"\n{C.CYAN}{'═'*62}{C.W}")
        print(f"{C.BOLD}{C.CYAN}  webbox v3.0 - سحب موقع كامل{C.W}")
        print(f"{C.CYAN}{'═'*62}{C.W}\n")
        print(f"  {C.BLUE}الهدف:{C.W}      {self.start_url}")
        print(f"  {C.BLUE}المجلد:{C.W}      {self.output_dir}")
        print(f"  {C.BLUE}العمق:{C.W}       {self.max_depth}")
        print(f"  {C.BLUE}الحد:{C.W}        {self.max_pages} صفحة")

        if self.spa_mode:
            print(f"  {C.YELLOW}SPA mode:{C.W}   ✅ مفعّل")
        if self.api_cache_enabled:
            print(f"  {C.YELLOW}API cache:{C.W}  ✅ مفعّل")
        if self.save_session_enabled:
            print(f"  {C.YELLOW}Session:{C.W}    ✅ مفعّل")
        if self.serve_after:
            print(f"  {C.YELLOW}Serve:{C.W}      ✅ port {self.serve_port}")
        print()

        os.makedirs(self.output_dir, exist_ok=True)
        start = time.time()
        self.log(f"{C.CYAN}[بدء السحب...]{C.W}\n")

        self._crawl(self.start_url, 0)
        elapsed = time.time() - start

        # حفظ الجلسة
        if self.session_manager:
            self.session_manager.add_cookies(self.session.cookies)
            self.session_manager.save()
            self.log(f"\n{C.GREEN}💾 Session saved{C.W}")

        # حفظ API cache
        if self.api_cache and self.api_cache.cache:
            self.api_cache.save()
            self.log(f"{C.GREEN}💾 API cache saved "
                     f"({len(self.api_cache.cache)} responses){C.W}")

        # تقرير
        report = {
            "target": self.start_url,
            "domain": self.base_domain,
            "date": datetime.now().isoformat(),
            "version": "3.0.0",
            "elapsed_seconds": round(elapsed, 2),
            "is_spa": self.is_spa_site,
            "spa_framework": self.spa_framework,
            "pages_downloaded": len(self.downloaded),
            "assets_downloaded": len(self.assets),
            "failed": len(self.failed),
            "pages": self.downloaded,
            "assets": self.assets,
            "failures": [
                {"url": u, "error": str(e)} for u, e in self.failed
            ],
        }

        report_path = os.path.join(self.output_dir, "_webbox_report.json")
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # نتائج
        print(f"\n{C.CYAN}{'═'*62}{C.W}")
        print(f"{C.BOLD}{C.GREEN}  ✅ انتهى{C.W}")
        print(f"{C.CYAN}{'═'*62}{C.W}")
        print(f"  {C.GREEN}صفحات:{C.W}   {len(self.downloaded)}")
        print(f"  {C.GREEN}ملفات:{C.W}   {len(self.assets)}")
        print(f"  {C.YELLOW}فشل:{C.W}     {len(self.failed)}")
        print(f"  {C.CYAN}الوقت:{C.W}   {elapsed:.1f}s")

        if self.is_spa_site:
            print(f"\n  {C.YELLOW}⚠ SPA detected ({self.spa_framework}){C.W}")
            if self.spa_mode:
                print(f"  {C.GREEN}✅ SPA fix applied{C.W}")
            else:
                print(f"  {C.YELLOW}💡 Use --spa-mode for better results{C.W}")

        print(f"  {C.BLUE}المجلد:{C.W}  {self.output_dir}")
        print(f"{C.CYAN}{'═'*62}{C.W}\n")

        # تشغيل السيرفر
        if self.serve_after:
            start_local_server(
                self.output_dir,
                port=self.serve_port,
                open_browser=True
            )

        return report
