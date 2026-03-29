# Remote Access — Tailscale
# Free SSH From Work or Phone to Mac Mini

## What This Does

Lets you SSH into your Mac mini from anywhere.  
Free forever. No router setup needed.  
Works on laptop, phone, anywhere with internet.

## Step 1: Install on Mac Mini

1. Go to tailscale.com/download
2. Download for macOS
3. Install and open
4. Sign in with info@genesisai.systems
5. Note your Tailscale IP

## Step 2: Turn On SSH

System Settings → General → Sharing  
Turn on Remote Login  
Allow all users

## Step 3: Install on Personal Laptop

1. Go to tailscale.com/download
2. Sign in with the same account
3. Confirm it connects

## Step 4: SSH From Work

`ssh genesisai@[your-tailscale-ip]`

## Step 5: Install on Phone

1. Download Termius
2. Add a new host
3. Hostname: your Tailscale IP
4. Username: genesisai
5. Port: 22

## Monthly Cost

$0 for up to 100 devices
