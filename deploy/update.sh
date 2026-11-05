#!/usr/bin/env bash
# Pull the latest code onto the server and restart. Run as root: sudo bash /opt/tracker/deploy/update.sh
set -euo pipefail
APP_DIR=/opt/tracker
sudo -u tracker git -C "$APP_DIR" pull --rebase
sudo -u tracker "$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"
systemctl restart tracker
systemctl --no-pager status tracker | head -5
