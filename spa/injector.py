"""حقن scripts في HTML المحفوظ"""
import re
import os


SPA_BEFORE = """
<!-- webbox SPA fix: BEFORE React loads -->
<script>
(function() {
    // 1. منع file:// من كسر window.location
    var originalPathname = window.location.pathname;
    var fileName = originalPathname.split('/').pop();
    if (fileName && fileName.indexOf('.html') !== -1) {
        var cleanPath = originalPathname.substring(0, originalPathname.lastIndexOf('/')) + '/';
        try {
            history.replaceState({}, '', cleanPath);
        } catch (e) {
            console.warn('[webbox] Cannot fix pathname:', e);
        }
    }

    // 2. حقن <base href="/">
    if (!document.querySelector('base')) {
        var base = document.createElement('base');
        base.href = './';
        document.head.insertBefore(base, document.head.firstChild);
    }

    // 3. تعطيل Service Workers
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations().then(function(regs) {
            regs.forEach(function(reg) { reg.unregister(); });
        });
    }

    // 4. علامة للـ after script
    window.__WEBBOX_SPA__ = true;
    console.log('[webbox] SPA fix applied (before)');
})();
</script>
"""


SPA_AFTER = """
<!-- webbox SPA fix: AFTER React loads -->
<script>
(function() {
    // 1. اعتراض fetch واسترجاع من cache
    var originalFetch = window.fetch;
    window.fetch = function(input, init) {
        var url = typeof input === 'string' ? input : input.url;

        // حاول من cache أولاً
        return originalFetch.apply(this, arguments).catch(function(err) {
            console.warn('[webbox] Fetch failed, trying cache:', url);
            return fetchFromCache(url).then(function(cached) {
                if (cached) {
                    console.log('[webbox] Served from cache:', url);
                    return new Response(cached.body, {
                        status: cached.status || 200,
                        headers: cached.headers || { 'Content-Type': 'application/json' }
                    });
                }
                throw err;
            });
        });
    };

    // 2. اعتراض XHR
    var originalXHR = window.XMLHttpRequest.prototype.open;
    window.XMLHttpRequest.prototype.open = function(method, url) {
        this.__webbox_url = url;
        return originalXHR.apply(this, arguments);
    };

    // 3. استرجاع localStorage
    var savedStorage = window.__WEBBOX_STORAGE__;
    if (savedStorage) {
        try {
            for (var key in savedStorage.localStorage) {
                localStorage.setItem(key, savedStorage.localStorage[key]);
            }
            for (var key in savedStorage.sessionStorage) {
                sessionStorage.setItem(key, savedStorage.sessionStorage[key]);
            }
            console.log('[webbox] Storage restored');
        } catch (e) {
            console.warn('[webbox] Storage restore failed:', e);
        }
    }

    // 4. استرجاع من cache
    function fetchFromCache(url) {
        return new Promise(function(resolve) {
            if (typeof localStorage === 'undefined') return resolve(null);

            var cacheKey = 'webbox_cache_' + btoa(url).substring(0, 50);
            var cached = localStorage.getItem(cacheKey);

            if (cached) {
                try {
                    resolve(JSON.parse(cached));
                } catch (e) {
                    resolve(null);
                }
            } else {
                resolve(null);
            }
        });
    }

    console.log('[webbox] API cache interception active');
})();
</script>
"""


SESSION_RESTORE = """
<script>
// استرجاع الجلسة
(function() {
    var session = window.__WEBBOX_SESSION__;
    if (!session) return;

    // Cookies
    if (session.cookies) {
        session.cookies.forEach(function(c) {
            document.cookie = c.name + '=' + c.value +
                '; path=' + (c.path || '/') +
                '; domain=' + (c.domain || location.hostname);
        });
    }

    console.log('[webbox] Session restored');
})();
</script>
"""


def inject_spa_fix(html: str, spa_info: dict, session_data: dict = None,
                    api_cache: dict = None) -> str:
    """حقن كل scripts الإصلاح"""

    if not spa_info.get("is_spa"):
        return html

    # 1. حقن الـ BEFORE في <head>
    if "</head>" in html:
        html = html.replace("</head>", SPA_BEFORE + "</head>", 1)
    else:
        html = SPA_BEFORE + html

    # 2. حقن session data
    if session_data:
        import json
        session_script = f"""
<script>
window.__WEBBOX_SESSION__ = {json.dumps(session_data, ensure_ascii=False)};
"""
        if api_cache:
            session_script += f"""
window.__WEBBOX_STORAGE__ = {json.dumps(api_cache.get('storage', {}), ensure_ascii=False)};
"""
        session_script += "</script>"

        if "<body" in html:
            html = re.sub(
                r'(<body[^>]*>)',
                r'\1' + session_script,
                html,
                count=1,
                flags=re.IGNORECASE
            )

    # 3. حقن الـ AFTER قبل </body>
    if "</body>" in html:
        html = html.replace("</body>", SPA_AFTER + "</body>", 1)
    else:
        html += SPA_AFTER

    return html
