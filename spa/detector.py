"""كشف المواقع SPA"""
import re


SPA_MARKERS = {
    "react": [
        r'<div id="root"',
        r'<div id="app"',
        r'data-reactroot',
        r'_reactRootContainer',
        r'__REACT_DEVTOOLS',
    ],
    "vue": [
        r'<div id="app"',
        r'data-v-[a-f0-9]{8}',
        r'__VUE__',
        r'__NUXT__',
    ],
    "angular": [
        r'ng-version=',
        r'_ngcontent',
        r'ng-app',
        r'<app-root',
    ],
    "svelte": [
        r'class="svelte-',
        r'__svelte',
        r'svelte-[a-z0-9]+',
    ],
    "nextjs": [
        r'__NEXT_DATA__',
        r'<div id="__next"',
    ],
    "nuxt": [
        r'__NUXT__',
    ],
}


def detect_spa(html: str) -> dict:
    """
    كشف نوع SPA
    يعيد: {"is_spa": bool, "framework": str, "confidence": float}
    """
    if not html:
        return {"is_spa": False, "framework": None, "confidence": 0.0}

    sample = html[:10000]
    scores = {}

    for framework, patterns in SPA_MARKERS.items():
        matches = 0
        for pattern in patterns:
            if re.search(pattern, sample, re.IGNORECASE):
                matches += 1
        if matches > 0:
            scores[framework] = matches / len(patterns)

    # علامات إضافية
    # SPA عادة HTML قصير + JS كبير
    if len(html) < 5000 and '<script' in html:
        scores["_small_html"] = 1

    # div فارغ في body
    if re.search(r'<body[^>]*>\s*<div[^>]*>\s*</div>', sample):
        scores["_empty_body"] = 1

    if not scores:
        return {"is_spa": False, "framework": None, "confidence": 0.0}

    best = max(scores, key=scores.get)
    confidence = scores[best]

    return {
        "is_spa": confidence > 0.3,
        "framework": best if not best.startswith("_") else "unknown",
        "confidence": confidence,
    }
