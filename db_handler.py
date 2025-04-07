import sqlite3
import os
from datetime import datetime

class DatabaseHandler:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chat.db')
        self._init_db()

    def _init_db(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS conversations
                     (id TEXT PRIMARY KEY, 
                      user_id TEXT,
                      last_context TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      conversation_id TEXT,
                      user_message TEXT,
                      bot_response TEXT,
                      sentiment TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY(conversation_id) REFERENCES conversations(id))''')
        conn.commit()
        conn.close()

    def save_message(self, conversation_id, user_message, bot_response, sentiment=None):
        """Save a message exchange to the database."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Ensure conversation exists
        c.execute('INSERT OR IGNORE INTO conversations (id) VALUES (?)', (conversation_id,))
        
        # Save message
        c.execute('''INSERT INTO messages 
                     (conversation_id, user_message, bot_response, sentiment)
                     VALUES (?, ?, ?, ?)''',
                  (conversation_id, user_message, bot_response, sentiment))
        conn.commit()
        conn.close()

    def get_conversation_history(self, conversation_id, limit=5):
        """Retrieve recent conversation history."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''SELECT user_message, bot_response 
                     FROM messages 
                     WHERE conversation_id = ?
                     ORDER BY created_at DESC
                     LIMIT ?''', (conversation_id, limit))
        messages = c.fetchall()
        conn.close()
        return [{"user": msg[0], "bot": msg[1]} for msg in reversed(messages)]

    def get_all_conversations(self):
        """Retrieve all conversations for admin view."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''SELECT c.id, c.created_at, 
                     (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) as msg_count
                     FROM conversations c
                     ORDER BY c.created_at DESC''')
        conversations = c.fetchall()
        conn.close()
        return [{"id": conv[0], "created_at": conv[1], "message_count": conv[2]} for conv in conversations]

    def delete_conversation(self, conversation_id):
        """Delete a conversation and all its messages."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('DELETE FROM messages WHERE conversation_id = ?', (conversation_id,))
        c.execute('DELETE FROM conversations WHERE id = ?', (conversation_id,))
        conn.commit()
        conn.close()