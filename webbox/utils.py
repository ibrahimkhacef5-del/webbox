cat > webbox/utils.py << 'ENDOFFILE'
"""أدوات مساعدة"""
import os
import re
import hashlib
from urllib.parse import urlparse, unquote


# ═══════════════════════════════════════════════════════
# امتدادات الملفات المدعومة
# ═══════════════════════════════════════════════════════
ASSET_EXTENSIONS = {
    # صور
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.ico',
    '.bmp', '.tiff', '.avif',
    # أنماط
    '.css', '.scss', '.sass', '.less',
    # سكربتات
    '.js', '.mjs', '.jsx', '.ts', '.tsx', '.coffee',
    # لغات برمجة
    '.py', '.php', '.rb', '.go', '.rs', '.java', '.c', '.cpp',
    '.h', '.hpp', '.cs', '.swift', '.kt', '.lua', '.sh', '.bat',
    # بيانات
    '.json', '.xml', '.yaml', '.yml', '.csv', '.sql', '.txt',
    '.md', '.map', '.wasm', '.manifest',
    # خطوط
    '.woff', '.woff2', '.ttf', '.eot', '.otf',
    # وسائط
    '.mp4', '.webm', '.mp3', '.wav', '.ogg', '.m4a', '.flac',
    '.avi', '.mov', '.mkv',
    # مستندات
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    # أرشيف
    '.zip', '.tar', '.gz', '.rar', '.7z', '.bz2',
    # أخرى
    '.appcache', '.vtt', '.srt',
}


# ═══════════════════════════════════════════════════════
# ألوان الطرفية
# ═══════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════
# كشف SPA (React/Vue/Angular)
# ═══════════════════════════════════════════════════════
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


def is_spa(html: str) -> bool:
    """فحص إذا كانت الصفحة SPA"""
    if not html:
        return False
    sample = html[:5000].lower()
    for indicator in SPA_INDICATORS:
        if indicator.lower() in sample:
            return True
    return False


def is_asset(url: str) -> bool:
    """فحص إذا كان الرابط ملفاً"""
    if url.startswith("data:"):
        return True

    parsed = urlparse(url)
    path = parsed.path.lower()

    # فحص الامتداد
    for ext in ASSET_EXTENSIONS:
        if path.endswith(ext):
            return True

    # فحص إذا كان فيه نقطة في آخر جزء
    last = path.rsplit("/", 1)[-1]
    if "." in last and not last.startswith("."):
        return True

    return False


def clean_url(url: str) -> str:
    """تنظيف الرابط من fragment و query غير ضرورية"""
    # احذف fragment (#)
    if "#" in url:
        url = url.split("#")[0]
    return url


def safe_path(url: str, output_dir: str) -> str:
    """تحويل URL إلى مسار آمن محلي"""
    # احذف fragment أولاً
    url = clean_url(url)

    parsed = urlparse(url)
    path = parsed.path or "/"

    # إذا انتهى بـ / → index.html
    if path.endswith("/"):
        path += "index.html"

    # إذا ما فيه امتداد → نحاول من الـ query
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

    # معالجة query
    if parsed.query:
        h = hashlib.md5(parsed.query.encode()).hexdigest()[:8]
        name, ext = os.path.splitext(path)
        path = f"{name}_{h}{ext}"

    # تنظيف
    path = unquote(path)
    path = re.sub(r'[<>:"|?*]', '_', path)
    path = path.lstrip("/")

    # منع الخروج من المجلد
    full = os.path.normpath(os.path.join(output_dir, path))
    if not full.startswith(output_dir):
        full = os.path.join(
            output_dir, "misc",
            hashlib.md5(url.encode()).hexdigest() + ".bin"
        )
    return full


def get_extension(url: str) -> str:
    """استخراج الامتداد"""
    url = clean_url(url)
    path = urlparse(url).path
    ext = os.path.splitext(path)[1].lower()
    return ext or ".bin"


def should_skip(url: str) -> bool:
    """فحص إذا كان الرابط يجب تخطيه"""
    if not url:
        return True
    if url.startswith(("mailto:", "tel:", "javascript:", "#", "data:")):
        return True
    if not url.startswith(("http://", "https://")):
        return True
    return False
ENDOFFILE
