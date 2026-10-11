cat > ~/webbox/uninstall.sh << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
echo "🗑️  إزالة webbox..."
rm -f "$PREFIX/bin/webbox" "$HOME/.local/bin/webbox"
rm -rf "$HOME/.local/share/webbox"
echo "✅ تم"
EOF
chmod +x ~/webbox/uninstall.sh
