from flask import Flask, jsonify
import sqlite3
import os

app = Flask(__name__)

db_path = os.getenv("DB_PATH", "/app/data/tickets.db")
api_key = os.getenv("API_KEY", "chimera-api-key-12345")

# Initialize the database
def init_db():
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Create table
def init_db():
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Create table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'open'
            )
        ''')
        conn.commit()

@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Ticket Manager Running'}), 200

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8080)
