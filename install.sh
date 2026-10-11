cat > ~/webbox/install.sh << 'SHEOF'
#!/data/data/com.termux/files/usr/bin/bash
set -e

GREEN="\033[92m"
CYAN="\033[96m"
YELLOW="\033[93m"
BOLD="\033[1m"
RESET="\033[0m"

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════╗"
echo "║      webbox installer v2.0           ║"
echo "╚══════════════════════════════════════╝"
echo -e "${RESET}"

# 1. المتطلبات
echo -e "${CYAN}[1/4] تثبيت المتطلبات...${RESET}"
pkg update -y > /dev/null 2>&1 || true
pkg install -y python git > /dev/null 2>&1

# 2. مكتبات Python
echo -e "${CYAN}[2/4] تثبيت مكتبات Python...${RESET}"
pip install --quiet --upgrade pip
pip install --quiet requests beautifulsoup4 urllib3

# 3. نسخ الملفات
echo -e "${CYAN}[3/4] نسخ الملفات...${RESET}"
INSTALL_DIR="$HOME/.local/share/webbox"
mkdir -p "$INSTALL_DIR"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp -r "$SCRIPT_DIR/webbox" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/" 2>/dev/null || true

# 4. الأمر
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
echo -e "${GREEN}${BOLD}✅ تم التثبيت!${RESET}"
echo ""
echo -e "${CYAN}جرّب:${RESET}"
echo -e "  ${BOLD}webbox https://example.com${RESET}"
echo ""
SHEOF

chmod +x ~/webbox/install.sh
