#!/bin/bash
# ─────────────────────────────────────────────
# AdBot – Systemd 24/7 Service Setup Script
# Run once on your VPS: bash setup_service.sh
# ─────────────────────────────────────────────

set -e

BOT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$BOT_DIR/venv/bin/python3"
MAIN_PY="$BOT_DIR/main.py"
SERVICE_FILE="/etc/systemd/system/adbot.service"

echo ""
echo "════════════════════════════════════════"
echo "  🤖 AdBot — Systemd Service Setup"
echo "════════════════════════════════════════"
echo ""

# Make sure running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root: sudo bash setup_service.sh"
    exit 1
fi

# Stop existing tmux/screen sessions if any
pkill -f "python3 main.py" 2>/dev/null && echo "⏹  Stopped existing bot process" || true

# Write the systemd service file
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=AdBot Telegram Bot (24/7)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=$BOT_DIR
ExecStart=$VENV_PYTHON $MAIN_PY
Restart=always
RestartSec=5
StartLimitIntervalSec=60
StartLimitBurst=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service file written to $SERVICE_FILE"

# Reload systemd, enable + start
systemctl daemon-reload
systemctl enable adbot
systemctl restart adbot

sleep 2

echo ""
echo "════════════════════════════════════════"
systemctl status adbot --no-pager -l
echo "════════════════════════════════════════"
echo ""
echo "✅ Done! Your bot now runs 24/7."
echo ""
echo "📋 Useful commands:"
echo "  View live logs    → journalctl -u adbot -f"
echo "  Restart after update → git pull && systemctl restart adbot"
echo "  Stop bot          → systemctl stop adbot"
echo "  Bot status        → systemctl status adbot"
echo ""
