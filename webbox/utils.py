"""أدوات مساعدة - محسّنة للأسماء الطويلة"""
import os
import re
import hashlib
from urllib.parse import urlparse, unquote


# ═══════════════════════════════════════════════════════════════════════
# امتدادات الملفات
# ═══════════════════════════════════════════════════════════════════════
ASSET_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico',
    '.bmp', '.tiff', '.avif',
    '.css', '.scss', '.sass', '.less',
    '.js', '.mjs', '.jsx', '.ts', '.tsx', '.coffee',
    '.py', '.php', '.rb', '.go', '.rs', '.java', '.c', '.cpp',
    '.h', '.hpp', '.cs', '.swift', '.kt', '.lua', '.sh', '.bat',
    '.json', '.xml', '.yaml', '.yml', '.csv', '.sql', '.txt',
    '.md', '.map', '.wasm', '.manifest',
    '.woff', '.woff2', '.ttf', '.eot', '.otf',
    '.mp4', '.webm', '.mp3', '.wav', '.ogg', '.m4a', '.flac',
    '.avi', '.mov', '.mkv',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.zip', '.tar', '.gz', '.rar', '.7z', '.bz2',
    '.appcache', '.vtt', '.srt',
}


class C:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    MAGENTA = "\033[95m"
    WHITE = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


C.R = C.RED
C.G = C.GREEN
C.Y = C.YELLOW
C.B = C.BLUE
C.C = C.CYAN
C.M = C.MAGENTA
C.W = C.WHITE


SPA_INDICATORS = [
    '<div id="root"',
    '<div id="app"',
    '<div id="__next"',
    'window.__NUXT__',
    'window.__INITIAL_STATE__',
    'data-reactroot',
    'ng-version=',
    '_ngcontent',
]


def is_spa(html):
    if not html:
        return False
    sample = html[:5000].lower()
    for indicator in SPA_INDICATORS:
        if indicator.lower() in sample:
            return True
    return False


def is_asset(url):
    if url.startswith("data:"):
        return True
    parsed = urlparse(url)
    path = parsed.path.lower()
    for ext in ASSET_EXTENSIONS:
        if path.endswith(ext):
            return True
    last = path.rsplit("/", 1)[-1]
    if "." in last and not last.startswith("."):
        return True
    return False


def clean_url(url):
    if "#" in url:
        url = url.split("#")[0]
    return url


MAX_FILENAME_LENGTH = 100
MAX_PATH_LENGTH = 200


def _short_hash(text, length=16):
    return hashlib.sha256(text.encode()).hexdigest()[:length]


def _get_extension(url, path):
    ext = os.path.splitext(path)[1].lower()
    if ext and ext in ASSET_EXTENSIONS:
        return ext
    parsed = urlparse(url)
    ext = os.path.splitext(parsed.path)[1].lower()
    if ext and ext in ASSET_EXTENSIONS:
        return ext
    for part in parsed.query.split("&"):
        if "=" in part:
            val = part.split("=", 1)[1]
            ext2 = os.path.splitext(val)[1].lower()
            if ext2 and ext2 in ASSET_EXTENSIONS:
                return ext2
    return ".bin"


def _sanitize(name):
    name = unquote(name)
    name = re.sub(r'[<>:"|?*\\\x00-\x1f]', '_', name)
    name = re.sub(r'_+', '_', name)
    name = name.lstrip(".")
    return name


def _shorten_filename(filename, url, ext):
    if len(filename) <= MAX_FILENAME_LENGTH:
        return filename
    prefix = filename[:30].rstrip("._-")
    h = _short_hash(url, 16)
    return f"{prefix}_{h}{ext}"


def safe_path(url, output_dir):
    url = clean_url(url)
    parsed = urlparse(url)
    original_path = parsed.path or "/"
    path = original_path

    if path.endswith("/"):
        path += "index.html"
    elif "." not in os.path.basename(path):
        if parsed.query:
            found = False
            for part in parsed.query.split("&"):
                if "=" in part:
                    val = part.split("=", 1)[1]
                    if "." in val:
                        path += "/" + val
                        found = True
                        break
            if not found:
                path += "/index.html"
        else:
            path += "/index.html"

    ext = _get_extension(url, path)
    dir_part = os.path.dirname(path).strip("/")
    filename = os.path.basename(path) or "index"
    filename = _sanitize(filename)
    if not filename:
        filename = "file"
    filename = _shorten_filename(filename, url, ext)

    dir_parts = []
    for part in dir_part.split("/"):
        part = _sanitize(part)
        if not part:
            continue
        if len(part) > 50:
            part = _short_hash(part, 12)
        dir_parts.append(part)

    if parsed.query:
        qh = _short_hash(parsed.query, 8)
        name, e = os.path.splitext(filename)
        filename = f"{name}_{qh}{e}"

    final_path = "/".join(dir_parts + [filename])

    if len(final_path) > MAX_PATH_LENGTH:
        first_dir = dir_parts[0] if dir_parts else ""
        h = _short_hash(url, 20)
        filename = f"{h}{ext}"
        final_path = os.path.join(first_dir, filename) if first_dir else filename

    if len(os.path.basename(final_path)) > 255:
        h = _short_hash(url, 20)
        final_path = os.path.join(
            os.path.dirname(final_path),
            f"{h}{ext}"
        )

    full = os.path.normpath(os.path.join(output_dir, final_path))
    if not full.startswith(output_dir):
        full = os.path.join(
            output_dir, "misc",
            _short_hash(url, 32) + ext
        )

    return full


def get_extension(url):
    url = clean_url(url)
    path = urlparse(url).path
    ext = os.path.splitext(path)[1].lower()
    return ext or ".bin"


def should_skip(url):
    if not url:
        return True
    if url.startswith(("mailto:", "tel:", "javascript:", "#", "data:")):
        return True
    if not url.startswith(("http://", "https://")):
        return True
    return False
