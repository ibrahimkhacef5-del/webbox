"""حفظ واسترجاع الجلسة"""
import json
import os


class SessionManager:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.session_file = os.path.join(output_dir, ".webbox_session.json")
        self.data = {
            "cookies": [],
            "headers": {},
            "storage": {
                "localStorage": {},
                "sessionStorage": {},
            },
        }

    def add_cookies(self, cookies):
        """إضافة cookies من requests"""
        for cookie in cookies:
            self.data["cookies"].append({
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path,
            })

    def add_headers(self, headers):
        """إضافة headers مهمة"""
        important = [
            "authorization", "x-csrf-token", "x-requested-with",
            "content-type", "accept", "user-agent"
        ]
        for k, v in headers.items():
            if k.lower() in important:
                self.data["headers"][k] = v

    def save(self):
        with open(self.session_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        return self.session_file

    def get_session_script_data(self):
        """بيانات لـ JavaScript"""
        return {
            "cookies": self.data["cookies"],
            "headers": self.data["headers"],
            "storage": self.data["storage"],
        }
