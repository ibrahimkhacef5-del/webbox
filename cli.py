cat > ~/webbox/webbox/cli.py << 'PYEOF'
#!/usr/bin/env python3
"""webbox CLI"""
import sys
from webbox.core import WebBox


VERSION = "1.0.0"


HELP = """
\033[96mwebbox v{version}\033[0m - سحب موقع كامل

\033[1mالاستخدام:\033[0m
  webbox <url> [خيارات]

\033[1mالخيارات:\033[0m
  --depth N      عمق السحب (افتراضي: 3)
  --max N        أقصى عدد صفحات (افتراضي: 100)
  --output DIR   مجلد الحفظ
  --delay N      تأخير بين الطلبات بالثواني (افتراضي: 0.3)
  -v, --version  الإصدار
  -h, --help     هذه المساعدة

\033[1mأمثلة:\033[0m
  webbox https://example.com
  webbox https://example.com --depth 2 --max 50
  webbox https://example.com --output ./mysite

\033[93m⚠  استخدمها فقط على مواقع تملكها أو مصرح لك بسحبها\033[0m
""".format(version=VERSION)


def main():
    args = sys.argv[1:]

    if not args or "-h" in args or "--help" in args:
        print(HELP)
        sys.exit(0)

    if "-v" in args or "--version" in args:
        print(f"webbox v{VERSION}")
        sys.exit(0)

    url = args[0]
    depth = 3
    max_pages = 100
    delay = 0.3
    output = None

    i = 1
    while i < len(args):
        if args[i] == "--depth" and i + 1 < len(args):
            depth = int(args[i + 1]); i += 2
        elif args[i] == "--max" and i + 1 < len(args):
            max_pages = int(args[i + 1]); i += 2
        elif args[i] == "--delay" and i + 1 < len(args):
            delay = float(args[i + 1]); i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output = args[i + 1]; i += 2
        else:
            i += 1

    try:
        box = WebBox(url, max_depth=depth, max_pages=max_pages,
                     delay=delay, output=output)
        box.run()
    except KeyboardInterrupt:
        print("\n\033[93m⚠ تم الإيقاف\033[0m")
        sys.exit(130)


if __name__ == "__main__":
    main()
PYEOF
