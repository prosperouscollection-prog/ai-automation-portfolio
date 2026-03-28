#!/usr/bin/env python3
"""
iMessage Integration for Remote Control
Send iMessages to your Mac mini to control Claude chat via commands
"""

import sys
import subprocess
import json
import re
from datetime import datetime

class iMessageController:
    """Handle iMessage-based remote control"""
    
    @staticmethod
    def send_imessage(phone_number, message):
        """Send iMessage using macOS"""
        try:
            script = f'''
            tell application "Messages"
                set targetContact to "{phone_number}"
                set targetService to service 1
                send "{message}" to buddy targetContact of targetService
            end tell
            '''
            subprocess.run(['osascript', '-e', script], check=True, capture_output=True)
            print(f"✓ Sent: {message}")
            return True
        except Exception as e:
            print(f"✗ Failed to send iMessage: {e}")
            return False
    
    @staticmethod
    def get_imessages():
        """Get recent iMessages (Mac only)"""
        try:
            script = '''
            tell application "Messages"
                set recentMessages to {}
                repeat with msg in (get every message in (messages of first chat))
                    set msgData to {text: text of msg, sender: sender of msg, timestamp: time string of (date of msg)}
                    set end of recentMessages to msgData
                end repeat
                return recentMessages
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            print(f"Error reading iMessages: {e}")
            return None
    
    @staticmethod
    def process_command(command_text):
        """Process remote commands from iMessage"""
        commands = {
            'status': 'Check Claude server status',
            'chat': 'Send a message to Claude',
            'clear': 'Clear conversation history',
            'help': 'Show available commands',
        }
        
        # Parse command
        parts = command_text.lower().strip().split(maxsplit=1)
        cmd = parts[0] if parts else None
        args = parts[1] if len(parts) > 1 else None
        
        if cmd == 'help':
            return commands
        elif cmd == 'status':
            return {'command': 'status', 'action': 'Check server health'}
        elif cmd == 'chat' and args:
            return {'command': 'chat', 'message': args}
        elif cmd == 'clear':
            return {'command': 'clear', 'action': 'Clear conversation'}
        else:
            return {'error': f'Unknown command: {cmd}. Type "help" for options.'}
    
    @staticmethod
    def setup_imessage_listener():
        """Setup listener for incoming iMessages"""
        print("""
        iMessage Integration Setup
        ==========================
        
        To control Claude chat via iMessage:
        
        1. Send commands to your Mac mini's iMessage (from your phone)
        2. Available commands:
           - "@claude chat What is machine learning?"
           - "@claude status" (check server)
           - "@claude clear" (clear conversation)
        
        NOTE: This requires iMessage to be set up on your Mac mini
        and you need to keep Messages app running in the background.
        
        Alternative: Use web interface directly
        Access: http://<your-mac-ip>:5000 from your phone
        """)

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python imessage_controller.py <phone> <message>")
        print("Example: python imessage_controller.py '+1234567890' 'Test message'")
        iMessageController.setup_imessage_listener()
        sys.exit(0)
    
    phone = sys.argv[1]
    message = sys.argv[2] if len(sys.argv) > 2 else "Test"
    
    iMessageController.send_imessage(phone, message)

if __name__ == '__main__':
    main()
