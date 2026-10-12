"""حفظ API responses"""
import os
import json
import hashlib


class APICache:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.cache_dir = os.path.join(output_dir, "api-cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache = {}

    def _key(self, url):
        return hashlib.md5(url.encode()).hexdigest()

    def add(self, url, method, response_body, status, headers):
        """إضافة رد"""
        key = self._key(f"{method}:{url}")
        self.cache[key] = {
            "url": url,
            "method": method,
            "status": status,
            "headers": dict(headers),
            "body": response_body,
        }

    def save(self):
        """حفظ كل الردود"""
        filepath = os.path.join(self.cache_dir, "responses.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

        # إضافة ملف للاسترجاع السريع
        index_file = os.path.join(self.cache_dir, "index.json")
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(
                {k: v["url"] for k, v in self.cache.items()},
                f,
                ensure_ascii=False,
                indent=2
            )

        return filepath
