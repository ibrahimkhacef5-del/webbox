cat > ~/webbox/install.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
#
# webbox installer for Termux
#

set -e

GREEN="\033[92m"
RED="\033[91m"
YELLOW="\033[93m"
CYAN="\033[96m"
BOLD="\033[1m"
RESET="\033[0m"

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════╗"
echo "║      webbox installer v1.0           ║"
echo "╚══════════════════════════════════════╝"
echo -e "${RESET}"

# التحقق من Termux
if [ ! -d "/data/data/com.termux" ]; then
    echo -e "${YELLOW}⚠ لست في Termux — التثبيت سيستمر لكن قد يحتاج تعديل${RESET}"
fi

# تثبيت المتطلبات
echo -e "${CYAN}[1/4] تثبيت المتطلبات...${RESET}"
pkg update -y > /dev/null 2>&1 || true
pkg install -y python git > /dev/null 2>&1

# تثبيت مكتبات Python
echo -e "${CYAN}[2/4] تثبيت مكتبات Python...${RESET}"
pip install --quiet --upgrade pip
pip install --quiet requests beautifulsoup4 lxml urllib3

# نسخ الملفات
echo -e "${CYAN}[3/4] نسخ الملفات...${RESET}"
INSTALL_DIR="$HOME/.local/share/webbox"
mkdir -p "$INSTALL_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -r "$SCRIPT_DIR/webbox" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/" 2>/dev/null || true

# إنشاء الأمر
echo -e "${CYAN}[4/4] إنشاء الأمر webbox...${RESET}"
BIN_DIR="$PREFIX/bin"
if [ ! -d "$BIN_DIR" ]; then
    BIN_DIR="$HOME/.local/bin"
    mkdir -p "$BIN_DIR"
fi

cat > "$BIN_DIR/webbox" << WRAPPER
#!/data/data/com.termux/files/usr/bin/bash
export PYTHONPATH="$INSTALL_DIR:\$PYTHONPATH"
exec python "$INSTALL_DIR/webbox/cli.py" "\$@"
WRAPPER

chmod +x "$BIN_DIR/webbox"

echo ""
echo -e "${GREEN}${BOLD}✅ تم التثبيت بنجاح!${RESET}"
echo ""
echo -e "${CYAN}جرّب:${RESET}"
echo -e "  ${BOLD}webbox https://example.com${RESET}"
echo -e "  ${BOLD}webbox --help${RESET}"
echo ""
EOF

chmod +x ~/webbox/install.sh
