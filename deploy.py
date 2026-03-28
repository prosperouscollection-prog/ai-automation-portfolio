#!/usr/bin/env python3
"""
Claude API Phone Access - Deployment Agent
Automates setup, configuration, and deployment of the Claude API backend
"""

import os
import sys
import subprocess
import json
import platform
from pathlib import Path
from getpass import getpass
import time

class DeploymentAgent:
    """Handles automated deployment of Claude API phone access"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent / "claude-api-phone-access"
        self.backend_dir = self.base_dir / "backend"
        self.venv_dir = self.backend_dir / "venv"
        self.env_file = self.base_dir / ".env"
        self.os_type = platform.system()
        
    def print_header(self, text):
        """Print formatted header"""
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}\n")
    
    def print_step(self, num, text):
        """Print step indicator"""
        print(f"\n📌 Step {num}: {text}")
        print("-" * 50)
    
    def run_cmd(self, cmd, description="", check=True):
        """Run shell command and return result"""
        try:
            if description:
                print(f"  ⏳ {description}...")
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True,
                check=check
            )
            if result.returncode == 0 and description:
                print(f"  ✅ {description}")
            return result
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Error: {e.stderr or e.stdout}")
            return None
    
    def check_python(self):
        """Check if Python 3.8+ is installed"""
        self.print_step(1, "Checking Python Installation")
        
        result = self.run_cmd("python3 --version", "", check=False)
        if result.returncode != 0:
            print("❌ Python 3 not found!")
            print("Install Python 3.8+ from python.org")
            return False
        
        # Parse version
        version_str = result.stdout.strip()
        print(f"  Found: {version_str}")
        
        # Check if 3.8+
        version_parts = version_str.split()[-1].split('.')
        if int(version_parts[0]) >= 3 and int(version_parts[1]) >= 8:
            print("  ✅ Python version OK")
            return True
        else:
            print("❌ Need Python 3.8 or higher")
            return False
    
    def setup_venv(self):
        """Create and activate virtual environment"""
        self.print_step(2, "Setting Up Virtual Environment")
        
        if self.venv_dir.exists():
            print(f"  ℹ️  Virtual environment already exists")
            return True
        
        print(f"  Creating venv at: {self.venv_dir}")
        result = self.run_cmd(
            f"cd {self.backend_dir} && python3 -m venv venv",
            "Creating virtual environment",
            check=False
        )
        
        return result.returncode == 0
    
    def install_dependencies(self):
        """Install required Python packages"""
        self.print_step(3, "Installing Dependencies")
        
        if self.os_type == "Darwin":
            activate_cmd = f"source {self.venv_dir}/bin/activate"
        else:
            activate_cmd = f"source {self.venv_dir}/bin/activate"
        
        requirements_file = self.backend_dir / "requirements.txt"
        cmd = f"cd {self.backend_dir} && {activate_cmd} && pip install -r requirements.txt"
        
        result = self.run_cmd(cmd, "Installing packages", check=False)
        
        if result.returncode == 0:
            print("  ✅ Dependencies installed")
            return True
        else:
            print(f"  ⚠️  Install output: {result.stderr}")
            return False
    
    def setup_api_key(self):
        """Securely setup API key"""
        self.print_step(4, "Configuring Claude API Key")
        
        print("  You need a Claude API key to continue.")
        print("  Get one at: https://console.anthropic.com/account/keys")
        print("\n  Make sure you have:")
        print("    • An active Claude API account")
        print("    • $25 in API credit balance")
        print("    • Or a billing method on file")
        
        while True:
            api_key = getpass("\n  Enter your Claude API key (won't be shown): ").strip()
            
            if not api_key:
                print("  ❌ API key cannot be empty")
                continue
            
            if not api_key.startswith("sk-ant-"):
                print("  ⚠️  Warning: API key should start with 'sk-ant-'")
                confirm = input("  Continue anyway? (y/n): ").lower()
                if confirm != 'y':
                    continue
            
            # Verify key by testing it
            print("\n  🔍 Verifying API key...")
            verify_cmd = f"""cd {self.backend_dir} && {('source venv/bin/activate' if self.os_type == 'Darwin' else 'source venv/bin/activate')} && python3 << 'EOF'
import anthropic
import sys
try:
    client = anthropic.Anthropic(api_key='{api_key}')
    msg = client.messages.create(model='claude-3-5-sonnet-20241022', max_tokens=10, messages=[{{'role': 'user', 'content': 'hi'}}])
    print('✅')
except Exception as e:
    print('❌')
    sys.exit(1)
EOF"""
            
            verify_result = self.run_cmd(verify_cmd, "", check=False)
            
            if verify_result and verify_result.returncode == 0:
                print("  ✅ API key verified successfully!")
                break
            else:
                print("  ❌ API key verification failed")
                print("  Check that:")
                print("    • The key is correct")
                print("    • You have API credit")
                print("    • Your account is active")
                retry = input("\n  Try again? (y/n): ").lower()
                if retry != 'y':
                    return False
        
        return api_key
    
    def save_env_file(self, api_key):
        """Save API key to .env file"""
        print("\n  💾 Saving configuration...")
        
        env_content = f"""# Claude API Configuration
CLAUDE_API_KEY={api_key}

# Server Configuration
PORT=5000
DEBUG=False

# Optional: For remote access via ngrok
NGROK_AUTH_TOKEN=your_ngrok_token_here
"""
        
        try:
            self.env_file.write_text(env_content)
            # Restrict permissions
            os.chmod(self.env_file, 0o600)
            print("  ✅ .env file saved (permissions: 600)")
            return True
        except Exception as e:
            print(f"  ❌ Error saving .env: {e}")
            return False
    
    def check_mac_settings(self):
        """Guide user to set Mac to never sleep"""
        if self.os_type != "Darwin":
            return True
        
        self.print_step(5, "Configure Mac Mini (Never Sleep)")
        
        print("""
  Your Mac mini needs to stay on 24/7 for the server to work.
  
  Follow these steps:
  
  1. Click Apple menu → System Settings
  2. Go to Energy Saver (or Battery for laptops)
  3. Set "Turn display off after" to "Never"
  4. Set "Put computer to sleep after" to "Never"
  5. Check "Prevent computer from sleeping when plugged in"
  
  Note: You can still manually sleep the Mac if needed.
        """)
        
        confirm = input("  Have you configured these settings? (y/n): ").lower()
        return confirm == 'y'
    
    def get_mac_ip(self):
        """Get Mac's local IP address"""
        if self.os_type != "Darwin":
            return self.run_cmd("hostname -I", "", check=False).stdout.strip()
        
        # For Mac
        result = self.run_cmd(
            "ifconfig | grep 'inet ' | grep -v 127.0.0.1",
            "",
            check=False
        )
        
        if result and result.stdout:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                parts = line.split()
                if len(parts) > 1:
                    ip = parts[1]
                    if ip.startswith('192.') or ip.startswith('10.'):
                        return ip
        
        return None
    
    def show_access_info(self):
        """Show how to access from phone"""
        self.print_step(6, "Phone Access Information")
        
        mac_ip = self.get_mac_ip()
        
        print("""
  🎉 Your Claude API phone access is ready!
  
  LOCAL NETWORK ACCESS (Same WiFi):
  ─────────────────────────────────────
  """)
        
        if mac_ip:
            print(f"  URL: http://{mac_ip}:5000")
            print(f"  \n  Copy this link to your phone and bookmark it!")
        else:
            print(f"  URL: http://<your-mac-ip>:5000")
            print(f"  \n  Find your Mac IP:")
            print(f"    In Terminal: ifconfig | grep 'inet '")
            print(f"    Look for: 192.168.x.x or 10.0.x.x")
        
        print("""
  REMOTE ACCESS (Anywhere):
  ──────────────────────────
  Use ngrok for free tunnel:
  
  1. Install ngrok: brew install ngrok
  2. Get free account at ngrok.com
  3. In new terminal: ngrok http 5000
  4. Copy the URL (looks like: https://xxxx-xx-xxx.ngrok.io)
  5. Use that URL on your phone
  
  FIRST TIME TEST:
  ─────────────────
  1. Open the URL on your phone
  2. Type: "Hello, who are you?"
  3. Send
  4. Claude should respond!
  
  COST TRACKING:
  ───────────────
  Monitor your $25 credit at:
  https://console.anthropic.com/account/usage
  
  Each response costs ~$0.01-0.10
  You'll get hundreds of conversations!
        """)
    
    def offer_start_server(self):
        """Offer to start the server now"""
        self.print_step(7, "Start Server")
        
        start = input("\n  Start the server now? (y/n): ").lower()
        
        if start == 'y':
            print("\n  🚀 Starting server...")
            print("  Server running on http://0.0.0.0:5000")
            print("  Press Ctrl+C to stop\n")
            
            # Start server
            if self.os_type == "Darwin":
                activate_cmd = f"source {self.venv_dir}/bin/activate"
            else:
                activate_cmd = f"source {self.venv_dir}/bin/activate"
            
            cmd = f"cd {self.backend_dir} && {activate_cmd} && python app.py"
            os.system(cmd)
    
    def deploy(self):
        """Run full deployment"""
        self.print_header("Claude API Phone Access - Deployment")
        
        print("This script will:")
        print("  • Check Python installation")
        print("  • Create virtual environment")
        print("  • Install dependencies")
        print("  • Configure your API key")
        print("  • Guide Mac setup")
        print("  • Start the server")
        
        confirm = input("\nContinue? (y/n): ").lower()
        if confirm != 'y':
            print("Cancelled.")
            return False
        
        # Step 1: Check Python
        if not self.check_python():
            return False
        
        # Step 2: Setup venv
        if not self.setup_venv():
            print("❌ Failed to setup virtual environment")
            return False
        
        # Step 3: Install dependencies
        if not self.install_dependencies():
            print("⚠️  Some dependencies may have failed to install")
            # Don't exit, try to continue
        
        # Step 4: Setup API key
        api_key = self.setup_api_key()
        if not api_key:
            print("❌ API key setup cancelled")
            return False
        
        # Step 4b: Save env
        if not self.save_env_file(api_key):
            print("❌ Failed to save .env file")
            return False
        
        # Step 5: Check Mac settings
        if self.os_type == "Darwin":
            if not self.check_mac_settings():
                print("⚠️  Your Mac might go to sleep - make sure to configure it!")
        
        # Step 6: Show access info
        self.show_access_info()
        
        # Step 7: Offer to start
        self.offer_start_server()
        
        return True

def main():
    """Main entry point"""
    agent = DeploymentAgent()
    
    # Check if in right directory
    if not agent.base_dir.exists():
        print("❌ Error: claude-api-phone-access folder not found!")
        print(f"   Expected at: {agent.base_dir}")
        sys.exit(1)
    
    try:
        success = agent.deploy()
        if success:
            print("\n✅ Deployment complete!")
        else:
            print("\n❌ Deployment failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
