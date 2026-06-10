# Deployment Guide

How this project is hosted in production, and how to operate / troubleshoot it.

## Architecture at a glance

```
                                                  Oracle Cloud VM (Ubuntu 22.04)
                                                  Public IP: 80.225.244.24
 Browser ──HTTPS──▶ Vercel (static frontend)      ┌─────────────────────────────────────┐
   │                crypto-trading-analysis        │  nginx :443 (TLS, Let's Encrypt cert) │
   │                .vercel.app                     │        │ reverse_proxy + ws upgrade   │
   │                                                │        ▼                              │
   └──────WSS────▶ crypto-trading-analysis ────────▶│  uvicorn :8000 (FastAPI bot)          │
                   .duckdns.org  (DNS → 80.225.244.24)│        (systemd: crypto-bot.service)  │
                                                  └─────────────────────────────────────┘
```

- **Frontend**: static React/Vite app on **Vercel**, auto-deployed from `main`.
- **Domain**: free **DuckDNS** subdomain `crypto-trading-analysis.duckdns.org` → points to the Oracle VM's public IP.
- **Backend**: FastAPI bot (uvicorn) on an **Oracle Cloud** VM, fronted by **nginx** which terminates TLS and proxies the WebSocket.

The dashboard talks to the backend **only over the WebSocket** (`/ws`). There are no REST `/api` calls from the frontend.

---

## 1. Frontend — Vercel

- **URL**: https://crypto-trading-analysis.vercel.app
- **Deploys** automatically on every push to `main` (the project root's `frontend/` is the Vercel build).
- The WebSocket URL is chosen at runtime in [`frontend/src/App.jsx`](frontend/src/App.jsx):

  ```js
  const isLocal = window.location.hostname === "localhost" || "127.0.0.1";
  const WS_URL = isLocal
    ? "ws://localhost:8000/ws"                              // local dev
    : "wss://crypto-trading-analysis.duckdns.org/ws";       // production
  ```

  > ⚠️ This URL is **baked into the build**. Changing it requires a redeploy (push to `main`).
  > It **must** be `wss://` (secure) because the Vercel page is HTTPS — browsers block insecure
  > `ws://` from an HTTPS page (mixed content), and reject self-signed / IP-only certs.

- `frontend/.env.production` mirrors the same URL (`VITE_WS_URL`) for consistency, though `App.jsx`
  currently hardcodes the value.

---

## 2. Domain — DuckDNS

- **Dashboard**: https://www.duckdns.org (sign in with Google)
- **Subdomain**: `crypto-trading-analysis.duckdns.org`
- **Points to**: `80.225.244.24` (the Oracle VM public IP)
- If the VM's public IP ever changes, update it on the DuckDNS dashboard (set "current ip" → "update ip"),
  **or** from the VM via the DuckDNS API:

  ```bash
  curl "https://www.duckdns.org/update?domains=crypto-trading-analysis&token=YOUR_TOKEN&ip="
  ```
  (Token is on your DuckDNS dashboard — keep it private; do not commit it.)

---

## 3. Backend host — Oracle Cloud VM

| Property | Value |
|---|---|
| Instance | `instance-20260526-1645` |
| OS | Canonical Ubuntu 22.04 |
| Region | `ap-mumbai-1` (India West) |
| Public IP | `80.225.244.24` |
| Login user | `ubuntu` |
| SSH key | the Oracle key pair downloaded at instance creation (`ssh-key-2026-05-26 ... .key`) |

**SSH in:**
```bash
ssh -i /path/to/ssh-key-2026-05-26.key ubuntu@80.225.244.24
```

**Project location on the VM:** `/home/ubuntu/crypto-trading-bot` (a git clone of this repo, branch `main`).
Secrets (Binance/Claude keys) live in `backend/.env` on the VM — **not** in git.

### Firewall — TWO layers (both must allow a port)

Oracle blocks ports in two independent places. To expose a port externally, open it in **both**:

1. **OCI Security List** (cloud console):
   Networking → Virtual Cloud Networks → your VCN → Security Lists → *Default Security List* →
   Security rules → **Add Ingress Rules** (Source `0.0.0.0/0`, TCP, destination port).
2. **VM iptables** (on the host):
   ```bash
   sudo iptables -I INPUT 1 -p tcp --dport <PORT> -j ACCEPT
   sudo netfilter-persistent save
   ```

**Currently open ingress:** `22` (SSH), `80` (HTTP — for cert issuance/renewal), `443` (HTTPS/WSS), `8000` (direct API, optional).

---

## 4. nginx reverse proxy + TLS

nginx terminates TLS on `:443` and proxies to the bot on `localhost:8000`, including the WebSocket upgrade.

- **Config**: `/etc/nginx/sites-available/trading-bot` (symlinked into `sites-enabled/`)
- The `location /` block has the WebSocket upgrade headers (`Upgrade`, `Connection "upgrade"`,
  `proxy_http_version 1.1`) — required for `/ws` to work.

```bash
sudo nginx -t            # test config
sudo systemctl reload nginx
```

### TLS certificate — Let's Encrypt (certbot)

- Issued with the nginx plugin:
  ```bash
  sudo certbot --nginx -d crypto-trading-analysis.duckdns.org
  ```
- Cert lives in `/etc/letsencrypt/live/crypto-trading-analysis.duckdns.org/`.
- **Auto-renewal** is handled by certbot's systemd timer (renews ~30 days before the 90-day expiry).
  Verify with:
  ```bash
  sudo certbot renew --dry-run
  systemctl list-timers | grep certbot
  ```
- Renewal uses the HTTP-01 challenge on **port 80**, which is why port 80 must stay open.

---

## 5. The bot as a service — systemd

The bot runs as a managed service so it survives reboots and crashes.

- **Unit**: `/etc/systemd/system/crypto-bot.service`
  ```ini
  [Unit]
  Description=Crypto Trading Bot (FastAPI/uvicorn)
  After=network-online.target
  Wants=network-online.target

  [Service]
  Type=simple
  User=ubuntu
  WorkingDirectory=/home/ubuntu/crypto-trading-bot/backend
  ExecStart=/home/ubuntu/crypto-trading-bot/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
  Restart=always
  RestartSec=5

  [Install]
  WantedBy=multi-user.target
  ```

**Common commands:**
```bash
sudo systemctl status crypto-bot      # is it running?
sudo systemctl restart crypto-bot     # restart (e.g. after a code update)
sudo systemctl stop crypto-bot
sudo journalctl -u crypto-bot -f      # live logs
```

---

## 6. Updating production

### Frontend (UI changes)
Push to `main` → Vercel rebuilds and deploys automatically.

### Backend (bot/API changes)
```bash
ssh -i /path/to/key ubuntu@80.225.244.24
cd /home/ubuntu/crypto-trading-bot
git pull
# if Python deps changed:
#   source backend/venv/bin/activate && pip install -r backend/requirements.txt
sudo systemctl restart crypto-bot
```

---

## 7. Troubleshooting "Reconnecting…"

The dashboard header shows "Reconnecting…" when the browser can't hold the WebSocket open. Check in order:

1. **Is the bot up?** `sudo systemctl status crypto-bot` and `sudo journalctl -u crypto-bot -n 50`.
2. **Is the WSS endpoint reachable + cert valid?**
   ```bash
   curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
        -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
        https://crypto-trading-analysis.duckdns.org/ws
   # expect: HTTP/1.1 101 Switching Protocols
   ```
3. **Cert expired?** `sudo certbot certificates`. Renew: `sudo certbot renew`.
4. **DNS drifted?** `nslookup crypto-trading-analysis.duckdns.org` should return the VM's current public IP.
   If the IP changed, update DuckDNS (see §2).
5. **Mixed content / wrong URL?** The frontend must use `wss://…duckdns.org/ws` — never `ws://` or a raw IP
   (browsers reject both from an HTTPS page).
6. **Firewall?** Confirm ports 80/443 are open in *both* the OCI Security List and VM iptables (see §3).
