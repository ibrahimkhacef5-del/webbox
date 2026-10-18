cat > ~/webbox/webbox/utils.py << 'UTILSEOF'
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


# ═══════════════════════════════════════════════════════════════════════
# الألوان
# ═══════════════════════════════════════════════════════════════════════
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


# اختصارات للتوافق
C.R = C.RED
C.G = C.GREEN
C.Y = C.YELLOW
C.B = C.BLUE
C.C = C.CYAN
C.M = C.MAGENTA
C.W = C.WHITE


# ═══════════════════════════════════════════════════════════════════════
# SPA Detection
# ═══════════════════════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════════════════════
# فحص الأصول
# ═══════════════════════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════════════════════
# 🔥 الأهم: safe_path — تحويل آمن لأي URL
# ═══════════════════════════════════════════════════════════════════════
MAX_FILENAME_LENGTH = 100   # الحد الأقصى لطول اسم الملف
MAX_PATH_LENGTH = 200       # الحد الأقصى لطول المسار الكامل


def _short_hash(text, length=16):
    """هاش قصير من نص"""
    return hashlib.sha256(text.encode()).hexdigest()[:length]


def _get_extension(url, path):
    """استخراج الامتداد"""
    # من الـ path
    ext = os.path.splitext(path)[1].lower()
    if ext and ext in ASSET_EXTENSIONS:
        return ext

    # من الـ URL
    parsed = urlparse(url)
    ext = os.path.splitext(parsed.path)[1].lower()
    if ext and ext in ASSET_EXTENSIONS:
        return ext

    # من query
    for part in parsed.query.split("&"):
        if "=" in part:
            val = part.split("=", 1)[1]
            ext2 = os.path.splitext(val)[1].lower()
            if ext2 and ext2 in ASSET_EXTENSIONS:
                return ext2

    # افتراضي
    return ".bin"


def _sanitize(name):
    """تنظيف اسم ملف"""
    name = unquote(name)
    # إزالة الأحرف غير المسموحة
    name = re.sub(r'[<>:"|?*\\\x00-\x1f]', '_', name)
    # إزالة المسافات المتعددة
    name = re.sub(r'_+', '_', name)
    # إزالة النقاط في البداية
    name = name.lstrip(".")
    return name


def _shorten_filename(filename, url, ext):
    """
    إذا اسم الملف طويل جداً:
    - احتفظ بأول 30 حرف
    - أضف هاش من URL الكامل
    - أضف الامتداد
    """
    if len(filename) <= MAX_FILENAME_LENGTH:
        return filename

    # خذ أول 30 حرف
    prefix = filename[:30].rstrip("._-")
    # هاش من URL
    h = _short_hash(url, 16)
    # ركّب
    return f"{prefix}_{h}{ext}"


def safe_path(url, output_dir):
    """
    تحويل URL إلى مسار آمن محلي

    - يحذف الأحرف غير المسموحة
    - يختصر الأسماء الطويلة
    - يمنع الخروج من output_dir
    """
    url = clean_url(url)
    parsed = urlparse(url)
    original_path = parsed.path or "/"

    # ═══ 1. تحضير المسار الأولي ═══
    path = original_path

    # إذا ينتهي بـ / → index.html
    if path.endswith("/"):
        path += "index.html"
    elif "." not in os.path.basename(path):
        # ما فيه امتداد
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

    # ═══ 2. استخراج الامتداد ═══
    ext = _get_extension(url, path)

    # ═══ 3. تقسيم المسار (dirname + filename) ═══
    dir_part = os.path.dirname(path).strip("/")
    filename = os.path.basename(path) or "index"

    # ═══ 4. تنظيف الاسم ═══
    filename = _sanitize(filename)
    if not filename:
        filename = "file"

    # ═══ 5. اختصار الاسم إذا طويل ═══
    filename = _shorten_filename(filename, url, ext)

    # ═══ 6. تنظيف مجلدات المسار ═══
    dir_parts = []
    for part in dir_part.split("/"):
        part = _sanitize(part)
        if not part:
            continue
        # إذا الجزء طويل جداً، اختصره
        if len(part) > 50:
            part = _short_hash(part, 12)
        dir_parts.append(part)

    # ═══ 7. إعادة تركيب المسار ═══
    # إضافة query كـ hash صغير
    if parsed.query:
        qh = _short_hash(parsed.query, 8)
        name, e = os.path.splitext(filename)
        filename = f"{name}_{qh}{e}"

    final_path = "/".join(dir_parts + [filename])

    # ═══ 8. فحص الطول النهائي ═══
    if len(final_path) > MAX_PATH_LENGTH:
        # احتفظ بأول مجلد فقط + هاش
        first_dir = dir_parts[0] if dir_parts else ""
        h = _short_hash(url, 20)
        filename = f"{h}{ext}"
        final_path = os.path.join(first_dir, filename) if first_dir else filename

    # ═══ 9. فحص الطول المطلق (نظام الملفات) ═══
    # معظم أنظمة الملفات تحد من اسم الملف بـ 255
    if len(os.path.basename(final_path)) > 255:
        h = _short_hash(url, 20)
        final_path = os.path.join(
            os.path.dirname(final_path),
            f"{h}{ext}"
        )

    # ═══ 10. منع الخروج من output_dir ═══
    full = os.path.normpath(os.path.join(output_dir, final_path))
    if not full.startswith(output_dir):
        full = os.path.join(
            output_dir, "misc",
            _short_hash(url, 32) + ext
        )

    return full


# ═══════════════════════════════════════════════════════════════════════
# دوال مساعدة
# ═══════════════════════════════════════════════════════════════════════
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
UTILSEOF

echo "✅ utils.py محدّث"
