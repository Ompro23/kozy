import sqlite3
import os
import json
from datetime import datetime

class DatabaseHandler:
    """Database handler for managing conversations and messages"""
    
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
                      stress_level INTEGER DEFAULT 0,
                      anxiety_level INTEGER DEFAULT 0,
                      happiness_level INTEGER DEFAULT 5,
                      last_topic TEXT,
                      last_concern TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      conversation_id TEXT,
                      user_message TEXT,
                      bot_response TEXT,
                      sentiment TEXT,
                      detected_emotion TEXT,
                      topics TEXT,
                      concerns TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY(conversation_id) REFERENCES conversations(id))''')
        conn.commit()
        conn.close()

    def save_message(self, conversation_id, user_message, bot_response, sentiment=None, 
                     emotion=None, topics=None, concerns=None):
        """Save a message exchange to the database."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Ensure conversation exists
        c.execute('INSERT OR IGNORE INTO conversations (id) VALUES (?)', (conversation_id,))
        
        # Save message with context
        c.execute('''INSERT INTO messages 
                     (conversation_id, user_message, bot_response, sentiment,
                      detected_emotion, topics, concerns)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (conversation_id, user_message, bot_response, sentiment,
                   emotion, json.dumps(topics) if topics else None,
                   json.dumps(concerns) if concerns else None))
        
        # Update conversation state
        if topics or concerns:
            c.execute('''UPDATE conversations 
                         SET last_topic = ?, last_concern = ?
                         WHERE id = ?''',
                      (json.dumps(topics) if topics else None,
                       json.dumps(concerns) if concerns else None,
                       conversation_id))
        
        conn.commit()
        conn.close()

    def get_conversation_history(self, conversation_id, limit=5):
        """Retrieve recent conversation history."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''SELECT user_message, bot_response, sentiment, topics, concerns
                     FROM messages 
                     WHERE conversation_id = ?
                     ORDER BY created_at DESC
                     LIMIT ?''', (conversation_id, limit))
        messages = c.fetchall()
        conn.close()
        return [{
            "user": msg[0],
            "bot": msg[1],
            "sentiment": msg[2],
            "topics": json.loads(msg[3]) if msg[3] else None,
            "concerns": json.loads(msg[4]) if msg[4] else None
        } for msg in reversed(messages)]

    def get_all_conversations(self):
        """Get list of all conversations with message counts."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT c.id, c.created_at,
                   COUNT(m.id) as message_count
            FROM conversations c
            LEFT JOIN messages m ON c.id = m.conversation_id
            GROUP BY c.id
            ORDER BY c.created_at DESC
        ''')
        conversations = [
            {
                'id': row[0],
                'created_at': row[1],
                'message_count': row[2]
            }
            for row in c.fetchall()
        ]
        conn.close()
        return conversations

    def get_conversation_details(self, conversation_id):
        """Get details of a specific conversation."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT user_message, bot_response, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
        ''', (conversation_id,))
        messages = c.fetchall()
        conn.close()
        return [
            {
                'user': msg[0],
                'bot': msg[1],
                'timestamp': msg[2]
            }
            for msg in messages
        ]

    def delete_conversation(self, conversation_id):
        """Delete a conversation and all its messages."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('DELETE FROM messages WHERE conversation_id = ?', (conversation_id,))
        c.execute('DELETE FROM conversations WHERE id = ?', (conversation_id,))
        conn.commit()
        conn.close()

    def get_total_messages(self):
        """Get total number of messages in the system."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM messages')
        count = c.fetchone()[0]
        conn.close()
        return count

    def get_active_today(self):
        """Get number of conversations active today."""
        today = datetime.now().date().isoformat()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT COUNT(DISTINCT conversation_id)
            FROM messages
            WHERE DATE(created_at) = ?
        ''', (today,))
        count = c.fetchone()[0]
        conn.close()
        return count