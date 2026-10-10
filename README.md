cat > ~/webbox/README.md << 'EOF'
# webbox 📦

أداة سحب المواقع — تحفظ الموقع كاملاً (HTML + CSS + JS + صور) في مجلد محلي.

## ✨ المميزات

- سحب صفحات HTML مع تتبع الروابط الداخلية
- سحب الأصول: CSS، JS، الصور
- حفظ في مجلد باسم الموقع
- تقرير JSON كامل بكل التفاصيل
- تتبع الفشل مع الأخطاء
- Retry تلقائي عند فشل الشبكة
- تشتغل في Termux مباشرة

## 📦 التثبيت

### Termux

```bash
pkg install python git -y
git clone https://github.com/USERNAME/webbox.git
cd webbox
bash install.sh
