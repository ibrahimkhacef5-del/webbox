cd ~/webbox-fixed/temp

cat > README.md << 'READMEEOF'
<!-- ═══════════════════════════════════════════════════════════════ -->
<!--                          webbox v2.0                            -->
<!--              أداة سحب المواقع الأكثر شمولاً                     -->
<!-- ═══════════════════════════════════════════════════════════════ -->

<div align="center">

<!-- الشعار الكبير -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=12,20,24,30&height=200&section=header&text=webbox&fontSize=80&fontAlignY=35&animation=twinkling&fontColor=ffffff&desc=Site%20Downloader%20•%20Termux%20Ready%20•%20v2.0&descAlignY=55&descSize=18" width="100%"/>

<!-- الشارات الرئيسية -->
<p>
  <a href="https://github.com/ibrahimkhacef5-del/webbox/actions/workflows/test.yml">
    <img src="https://github.com/ibrahimkhacef5-del/webbox/actions/workflows/test.yml/badge.svg" alt="Tests"/>
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge&logo=opensourceinitiative&logoColor=white" alt="License"/>
  </a>
  <a href="https://termux.com/">
    <img src="https://img.shields.io/badge/Termux-Ready-000000?style=for-the-badge&logo=android&logoColor=white" alt="Termux"/>
  </a>
  <a href="https://github.com/ibrahimkhacef5-del/webbox/stargazers">
    <img src="https://img.shields.io/github/stars/ibrahimkhacef5-del/webbox?style=for-the-badge&color=ffd700&logo=github" alt="Stars"/>
  </a>
  <a href="https://github.com/ibrahimkhacef5-del/webbox/network/members">
    <img src="https://img.shields.io/github/forks/ibrahimkhacef5-del/webbox?style=for-the-badge&color=6366f1&logo=git" alt="Forks"/>
  </a>
  <a href="https://github.com/ibrahimkhacef5-del/webbox/issues">
    <img src="https://img.shields.io/github/issues/ibrahimkhacef5-del/webbox?style=for-the-badge&color=ef4444&logo=github" alt="Issues"/>
  </a>
  <a href="https://github.com/ibrahimkhacef5-del/webbox">
    <img src="https://img.shields.io/github/last-commit/ibrahimkhacef5-del/webbox?style=for-the-badge&color=10b981" alt="Last Commit"/>
  </a>
</p>

<!-- وصف مختصر -->
<h3>🎯 أداة سحب المواقع الأكثر شمولاً</h3>
<p><i>حمّل أي موقع كاملاً — HTML، CSS، JS، صور، فيديو، وأي ملف فيه نقطة</i></p>

<!-- شارات إضافية -->
<p>
  <img src="https://img.shields.io/badge/Platform-Termux%20%7C%20Linux%20%7C%20macOS-blueviolet?style=flat-square"/>
  <img src="https://img.shields.io/badge/Status-Active-success?style=flat-square"/>
  <img src="https://img.shields.io/badge/Maintained-Yes-brightgreen?style=flat-square"/>
  <img src="https://img.shields.io/badge/Made%20with-❤️-red?style=flat-square"/>
</p>

</div>

---

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--                          المحتويات                              -->
<!-- ═══════════════════════════════════════════════════════════════ -->

<details>
<summary><b>📋 جدول المحتويات</b></summary>

- [✨ المميزات](#-المميزات)
- [🎬 نظرة سريعة](#-نظرة-سريعة)
- [📦 التثبيت](#-التثبيت)
- [🚀 الاستخدام](#-الاستخدام)
- [📁 أين تُحفظ الملفات؟](#-أين-تُحفظ-الملفات)
- [🎯 أنواع الملفات المدعومة](#-أنواع-الملفات-المدعومة)
- [⚙️ الخيارات المتقدمة](#️-الخيارات-المتقدمة)
- [📊 مقارنة الإصدارات](#-مقارنة-الإصدارات)
- [🛠️ التقنيات المستخدمة](#️-التقنيات-المستخدمة)
- [❓ الأسئلة الشائعة](#-الأسئلة-الشائعة)
- [🐛 الإبلاغ عن مشكلة](#-الإبلاغ-عن-مشكلة)
- [🤝 المساهمة](#-المساهمة)
- [📄 الرخصة](#-الرخصة)

</details>

---

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--                          المميزات                               -->
<!-- ═══════════════════════════════════════════════════════════════ -->

## ✨ المميزات

<div align="center">

| 🌐 **سحب شامل** | 📦 **أي ملف** | 🔗 **تتبع الروابط** |
|:---:|:---:|:---:|
| HTML، CSS، JS، صور، خطوط | `.py` `.php` `.json` `.pdf` `.svg` `.mp4` | يسحب الصفحات الداخلية تلقائياً |

| 📁 **حفظ ذكي** | 📊 **تقرير JSON** | 🔄 **إعادة محاولة** |
|:---:|:---:|:---:|
| بنية مجلدات منظمة | كل التفاصيل محفوظة | تلقائياً عند فشل الشبكة |

| 📱 **Termux-ready** | ⚡ **سريعة** | 💾 **حفظ في ذاكرة الهاتف** |
|:---:|:---:|:---:|
| تشتغل مباشرة على أندرويد | سطر واحد للتشغيل | `/storage/emulated/0/webbox/` |

</div>

---

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--                          نظرة سريعة                             -->
<!-- ═══════════════════════════════════════════════════════════════ -->

## 🎬 نظرة سريعة

<div align="center">

<!-- محاكاة Terminal -->
<img src="https://raw.githubusercontent.com/ibrahimkhacef5-del/webbox/main/.github/preview.png" alt="webbox Terminal" width="700"/>

</div>

**مثال حقيقي:**

```bash
$ webbox https://example.com --depth 2 --max 20

════════════════════════════════════════════════════════════════
webbox v2.0 - سحب موقع كامل
════════════════════════════════════════════════════════════════

الهدف:      https://example.com
المجلد:     /storage/emulated/0/webbox/example.com
العمق:      2
الحد:       20 صفحة

[بدء السحب...]

✓ [HTML 1KB] https://example.com
  ✓ [2KB] .css https://example.com/style.css
  ✓ [5KB] .js https://example.com/script.js
  ✓ [12KB] .png https://example.com/logo.png
  ✓ [8KB] .woff2 https://example.com/font.woff2
  ✓ [45KB] .svg https://example.com/icon.svg
✓ [HTML 3KB] https://example.com/about
  ✓ [3KB] .png https://example.com/team.png

════════════════════════════════════════════════════════════════
✅ انتهى
════════════════════════════════════════════════════════════════
صفحات:   2
ملفات:   7
فشل:     0
الوقت:   12.4s
════════════════════════════════════════════════════════════════
