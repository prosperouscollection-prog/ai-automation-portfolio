# Cloudflare Tunnel — Backup Remote Access

## What this does

Gives you a backup way to reach your Mac mini.

## Steps

1. `brew install cloudflared`
2. `cloudflared tunnel login`
3. `cloudflared tunnel create genesis-ai-tunnel`
4. Create `~/.cloudflared/config.yml`
5. Point `ssh.genesisai.systems` to your Mac mini
6. Install the Cloudflare service
7. SSH using the backup hostname

## Cost

Free
