#!/usr/bin/env python3
"""webbox v3.0 - CLI"""
import sys
import os
from webbox.core import WebBox


VERSION = "3.0.0"


HELP = """
\033[96m╔══════════════════════════════════════════════════════════╗
║           webbox v{version} - سحب المواقع                  ║
╚══════════════════════════════════════════════════════════╝\033[0m

\033[1mالاستخدام:\033[0m
  webbox <url> [خيارات]

\033[1mخيارات السحب:\033[0m
  --depth N          عمق السحب (افتراضي: 3)
  --max N            أقصى عدد صفحات (افتراضي: 100)
  --delay N          تأخير بين الطلبات بالثواني (افتراضي: 0.3)
  --output DIR       مجلد الحفظ
  --ua STRING        User-Agent مخصص

\033[1mخيارات SPA (للمواقع الحديثة):\033[0m
  --spa-mode         تفعيل معالجة SPA (React/Vue/Angular)
  --api-cache        حفظ API responses
  --save-session     حفظ cookies + localStorage
  --serve            تشغيل local server بعد السحب
  --port N           port السيرفر (افتراضي: 8080)

\033[1mخيارات مساعدة:\033[0m
  -v, --version      الإصدار
  -h, --help         هذه المساعدة

\033[1mأمثلة أساسية:\033[0m
  \033[93mwebbox https://example.com\033[0m
  \033[93mwebbox https://example.com --depth 2 --max 50\033[0m
  \033[93mwebbox https://example.com --output ./mysite\033[0m

\033[1mأمثلة SPA:\033[0m
  \033[93mwebbox https://shop2game.com --spa-mode\033[0m
  \033[93mwebbox https://shop2game.com --spa-mode --api-cache\033[0m
  \033[93mwebbox https://react.dev --spa-mode --serve\033[0m
  \033[93mwebbox https://vuejs.org --spa-mode --save-session --port 3000\033[0m

\033[1mمجلد الحفظ:\033[0m
  \033[96m/storage/emulated/0/webbox/<domain>/\033[0m

\033[93m⚠  استخدمها فقط على مواقع تملكها أو مصرح لك بسحبها\033[0m
""".format(version=VERSION)


def main():
    args = sys.argv[1:]

    # ═══════════════════════════════════════════════════════
    # Help
    # ═══════════════════════════════════════════════════════
    if not args or "-h" in args or "--help" in args:
        print(HELP)
        sys.exit(0)

    # ═══════════════════════════════════════════════════════
    # Version
    # ═══════════════════════════════════════════════════════
    if "-v" in args or "--version" in args:
        print(f"webbox v{VERSION}")
        sys.exit(0)

    # ═══════════════════════════════════════════════════════
    # URL
    # ═══════════════════════════════════════════════════════
    url = args[0]

    # ═══════════════════════════════════════════════════════
    # Defaults
    # ═══════════════════════════════════════════════════════
    depth = 3
    max_pages = 100
    delay = 0.3
    output = None
    user_agent = None

    # SPA options
    spa_mode = False
    api_cache = False
    save_session = False
    serve = False
    serve_port = 8080

    # ═══════════════════════════════════════════════════════
    # Parse arguments
    # ═══════════════════════════════════════════════════════
    i = 1
    while i < len(args):
        arg = args[i]

        # Basic options
        if arg == "--depth" and i + 1 < len(args):
            try:
                depth = int(args[i + 1])
            except ValueError:
                print(f"\033[91m❌ قيمة غير صالحة لـ --depth: {args[i+1]}\033[0m")
                sys.exit(1)
            i += 2

        elif arg == "--max" and i + 1 < len(args):
            try:
                max_pages = int(args[i + 1])
            except ValueError:
                print(f"\033[91m❌ قيمة غير صالحة لـ --max: {args[i+1]}\033[0m")
                sys.exit(1)
            i += 2

        elif arg == "--delay" and i + 1 < len(args):
            try:
                delay = float(args[i + 1])
            except ValueError:
                print(f"\033[91m❌ قيمة غير صالحة لـ --delay: {args[i+1]}\033[0m")
                sys.exit(1)
            i += 2

        elif arg == "--output" and i + 1 < len(args):
            output = args[i + 1]
            i += 2

        elif arg == "--ua" and i + 1 < len(args):
            user_agent = args[i + 1]
            i += 2

        # SPA options
        elif arg == "--spa-mode":
            spa_mode = True
            i += 1

        elif arg == "--api-cache":
            api_cache = True
            i += 1

        elif arg == "--save-session":
            save_session = True
            i += 1

        elif arg == "--serve":
            serve = True
            i += 1

        elif arg == "--port" and i + 1 < len(args):
            try:
                serve_port = int(args[i + 1])
            except ValueError:
                print(f"\033[91m❌ قيمة غير صالحة لـ --port: {args[i+1]}\033[0m")
                sys.exit(1)
            i += 2

        else:
            # Unknown argument - show warning
            if arg.startswith("--"):
                print(f"\033[93m⚠ خيار غير معروف: {arg}\033[0m")
            i += 1

    # ═══════════════════════════════════════════════════════
    # Validation
    # ═══════════════════════════════════════════════════════
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    if depth < 0:
        print(f"\033[91m❌ --depth يجب أن يكون >= 0\033[0m")
        sys.exit(1)

    if max_pages < 1:
        print(f"\033[91m❌ --max يجب أن يكون >= 1\033[0m")
        sys.exit(1)

    if delay < 0:
        print(f"\033[91m❌ --delay يجب أن يكون >= 0\033[0m")
        sys.exit(1)

    if serve_port < 1024 or serve_port > 65535:
        print(f"\033[91m❌ --port يجب أن يكون بين 1024 و 65535\033[0m")
        sys.exit(1)

    # ═══════════════════════════════════════════════════════
    # Run
    # ═══════════════════════════════════════════════════════
    try:
        box = WebBox(
            url,
            max_depth=depth,
            max_pages=max_pages,
            delay=delay,
            output=output,
            user_agent=user_agent,
            spa_mode=spa_mode,
            api_cache=api_cache,
            save_session=save_session,
            serve=serve,
            serve_port=serve_port,
        )
        box.run()

    except KeyboardInterrupt:
        print(f"\n\033[93m⚠ تم الإيقاف\033[0m")
        sys.exit(130)

    except Exception as e:
        print(f"\n\033[91m❌ خطأ: {e}\033[0m")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
