#!/usr/bin/env bash
# One-time server setup for Ubuntu. Run as root:
#   sudo DOMAIN=tracker.example.com EMAIL=you@example.com bash setup.sh
# Safe to re-run; finished steps are skipped.
set -euo pipefail

: "${DOMAIN:?Set DOMAIN, e.g. DOMAIN=tracker.example.com}"
: "${EMAIL:?Set EMAIL for certificate expiry notices}"
REPO_URL="${REPO_URL:-git@github.com:aakshirwany/tracker.git}"
APP_DIR=/opt/tracker
APP_USER=tracker
APP_HOME=/var/lib/tracker

echo "==> Installing packages"
apt-get update
apt-get install -y python3 python3-venv git nginx certbot python3-certbot-nginx apache2-utils ufw

echo "==> Creating user '$APP_USER'"
id "$APP_USER" &>/dev/null || useradd --system --create-home --home-dir "$APP_HOME" --shell /usr/sbin/nologin "$APP_USER"

echo "==> GitHub deploy key"
KEY="$APP_HOME/.ssh/id_ed25519"
if [[ ! -f "$KEY" ]]; then
    sudo -u "$APP_USER" mkdir -p -m 700 "$APP_HOME/.ssh"
    sudo -u "$APP_USER" ssh-keygen -t ed25519 -N "" -C "tracker@$DOMAIN" -f "$KEY"
    ssh-keyscan github.com | sudo -u "$APP_USER" tee -a "$APP_HOME/.ssh/known_hosts" >/dev/null
    echo
    echo "Add this key on GitHub: repo -> Settings -> Deploy keys -> Add deploy key,"
    echo "and tick 'Allow write access' (needed for the Push button):"
    echo
    cat "$KEY.pub"
    echo
    read -rp "Press Enter once the key is added... "
fi

echo "==> Cloning repo to $APP_DIR"
if [[ ! -d "$APP_DIR/.git" ]]; then
    install -d -o "$APP_USER" -g "$APP_USER" "$APP_DIR"
    sudo -u "$APP_USER" git clone "$REPO_URL" "$APP_DIR"
fi
sudo -u "$APP_USER" git -C "$APP_DIR" config user.name "Tracker server"
sudo -u "$APP_USER" git -C "$APP_DIR" config user.email "tracker@$DOMAIN"

echo "==> Python environment"
[[ -d "$APP_DIR/venv" ]] || sudo -u "$APP_USER" python3 -m venv "$APP_DIR/venv"
sudo -u "$APP_USER" "$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"

echo "==> systemd service"
cp "$APP_DIR/deploy/tracker.service" /etc/systemd/system/tracker.service
systemctl daemon-reload
systemctl enable --now tracker
systemctl restart tracker

echo "==> Login for the web page"
if [[ ! -f /etc/nginx/tracker.htpasswd ]]; then
    read -rp "Username for the tracker login: " WEB_USER
    htpasswd -c /etc/nginx/tracker.htpasswd "$WEB_USER"
    chown root:www-data /etc/nginx/tracker.htpasswd
    chmod 640 /etc/nginx/tracker.htpasswd
fi

echo "==> nginx"
if [[ ! -f /etc/nginx/sites-available/tracker ]]; then
    sed "s/__DOMAIN__/$DOMAIN/" "$APP_DIR/deploy/nginx-tracker.conf" > /etc/nginx/sites-available/tracker
fi
ln -sf /etc/nginx/sites-available/tracker /etc/nginx/sites-enabled/tracker
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo "==> Firewall"
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "==> HTTPS certificate"
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL" --redirect

echo
echo "Done: https://$DOMAIN"
