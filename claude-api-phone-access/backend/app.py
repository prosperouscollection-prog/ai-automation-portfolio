#!/usr/bin/env python3
"""
Claude API Backend Server
Runs on Mac mini, accessible from phone over local network or ngrok tunnel
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import anthropic
import os
import json
from datetime import datetime
import logging
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get absolute paths
BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
BACKEND_DIR = Path(__file__).parent

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path='')
CORS(app)

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))

# Conversation history storage
conversations = {}
HISTORY_FILE = Path('conversation_history.json')

def load_history():
    """Load conversation history from file"""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_history():
    """Save conversation history to file"""
    with open(HISTORY_FILE, 'w') as f:
        json.dump(conversations, f, indent=2)

def get_claude_response(user_message, conversation_id='default'):
    """Get response from Claude API"""
    try:
        # Initialize conversation if needed
        if conversation_id not in conversations:
            conversations[conversation_id] = []
        
        # Add user message to history
        conversations[conversation_id].append({
            "role": "user",
            "content": user_message
        })
        
        # Call Claude API
        response = client.messages.create(
            model="claude-opus-4-1-20250805",  # Latest model available
            max_tokens=2048,
            messages=conversations[conversation_id]
        )
        
        assistant_message = response.content[0].text
        
        # Add assistant response to history
        conversations[conversation_id].append({
            "role": "assistant",
            "content": assistant_message
        })
        
        # Save history
        save_history()
        
        return assistant_message, None
    
    except Exception as e:
        logger.error(f"Error calling Claude API: {str(e)}")
        return None, str(e)

@app.route('/')
def index():
    """Serve the main page"""
    return send_from_directory(str(FRONTEND_DIR), 'index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint"""
    data = request.json
    user_message = data.get('message', '')
    conversation_id = data.get('conversation_id', 'default')
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    response, error = get_claude_response(user_message, conversation_id)
    
    if error:
        return jsonify({'error': error}), 500
    
    return jsonify({
        'response': response,
        'conversation_id': conversation_id,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/conversations', methods=['GET'])
def get_conversations():
    """Get all conversation IDs"""
    return jsonify(list(conversations.keys()))

@app.route('/api/conversation/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get specific conversation history"""
    if conversation_id not in conversations:
        return jsonify({'error': 'Conversation not found'}), 404
    
    return jsonify(conversations[conversation_id])

@app.route('/api/conversation/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Delete a conversation"""
    if conversation_id in conversations:
        del conversations[conversation_id]
        save_history()
        return jsonify({'status': 'deleted'})
    return jsonify({'error': 'Conversation not found'}), 404

@app.route('/api/clear', methods=['POST'])
def clear_all():
    """Clear all conversations"""
    global conversations
    conversations = {}
    save_history()
    return jsonify({'status': 'cleared'})

@app.route('/api/status', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().isoformat(),
        'conversations': len(conversations)
    })

@app.route('/api/import', methods=['POST'])
def import_conversations():
    """Import conversations from JSON data"""
    try:
        data = request.json
        import_data = data.get('conversations', {})
        merge_mode = data.get('merge', 'append')  # append, replace, or merge
        
        if not import_data:
            return jsonify({'error': 'No conversations provided'}), 400
        
        imported_count = 0
        for conv_id, messages in import_data.items():
            if not isinstance(messages, list):
                continue
            
            if merge_mode == 'replace' or conv_id not in conversations:
                conversations[conv_id] = messages
                imported_count += 1
            elif merge_mode == 'merge':
                conversations[conv_id].extend(messages)
                imported_count += 1
            # 'append' mode: skip if exists
        
        save_history()
        return jsonify({
            'status': 'imported',
            'conversations_imported': imported_count,
            'total_conversations': len(conversations)
        })
    
    except Exception as e:
        logger.error(f"Error importing conversations: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export', methods=['GET'])
def export_conversations():
    """Export all conversations as JSON"""
    try:
        return jsonify(conversations)
    except Exception as e:
        logger.error(f"Error exporting conversations: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/<path:path>')
def catch_all(path):
    """Serve static files and fallback to index.html"""
    file_path = FRONTEND_DIR / path
    if file_path.exists() and file_path.is_file():
        return send_from_directory(str(FRONTEND_DIR), path)
    # Fallback to index.html for SPA routing
    return send_from_directory(str(FRONTEND_DIR), 'index.html')

if __name__ == '__main__':
    # Load existing history
    conversations = load_history()
    
    # Run on 0.0.0.0 to be accessible from phone
    # Port 5000 by default
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Claude API server on port {port}")
    logger.info("Access from phone at: http://<your-mac-ip>:5000")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
