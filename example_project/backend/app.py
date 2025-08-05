#!/usr/bin/env python3
"""
TaskFlow - Main Flask Application
A collaborative task management web application
"""

from flask import Flask, request, jsonify, session
from flask_cors import CORS
import sqlite3
import hashlib
import os
from datetime import datetime
import sys

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'
CORS(app)

DATABASE = 'backend/database.db'

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            assigned_to INTEGER,
            created_by INTEGER NOT NULL,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'todo',
            due_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assigned_to) REFERENCES users (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Insert sample data
    cursor.execute('''
        INSERT OR IGNORE INTO users (username, email, password_hash) VALUES 
        ('admin', 'admin@taskflow.com', ?),
        ('alice', 'alice@taskflow.com', ?),
        ('bob', 'bob@taskflow.com', ?)
    ''', (
        hashlib.sha256('admin123'.encode()).hexdigest(),
        hashlib.sha256('alice123'.encode()).hexdigest(), 
        hashlib.sha256('bob123'.encode()).hexdigest()
    ))
    
    cursor.execute('''
        INSERT OR IGNORE INTO tasks (title, description, created_by, assigned_to, priority, status) VALUES
        ('Fix login bug', 'Users cannot logout properly after session expires', 1, 2, 'high', 'todo'),
        ('Add input validation', 'Task creation needs proper input validation', 1, 3, 'high', 'in_progress'),
        ('Implement notifications', 'Add task assignment notifications', 1, NULL, 'medium', 'todo'),
        ('Create dashboard', 'Build team dashboard view', 1, 2, 'medium', 'todo'),
        ('Add dark mode', 'Implement dark mode UI theme', 1, NULL, 'low', 'todo')
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    conn = get_db()
    user = conn.execute(
        'SELECT * FROM users WHERE username = ?', (username,)
    ).fetchone()
    
    if user and user['password_hash'] == hashlib.sha256(password.encode()).hexdigest():
        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({
            'success': True,
            'user': {'id': user['id'], 'username': user['username'], 'email': user['email']}
        })
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """User logout endpoint - HAS A BUG!"""
    # BUG: Session not properly cleared, causes authentication issues
    session.pop('user_id', None)
    # Missing: session.pop('username', None)  # This line is missing!
    return jsonify({'success': True})

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db()
    tasks = conn.execute('''
        SELECT t.*, u.username as assigned_username, c.username as created_username
        FROM tasks t
        LEFT JOIN users u ON t.assigned_to = u.id
        LEFT JOIN users c ON t.created_by = c.id
        ORDER BY t.created_at DESC
    ''').fetchall()
    
    return jsonify([dict(task) for task in tasks])

@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create new task with proper input validation"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    
    # Input validation - check for required fields
    if not data or not data.get('title'):
        return jsonify({'error': 'Missing required field: title'}), 400
    
    title = data.get('title').strip()
    if len(title) == 0:
        return jsonify({'error': 'Title cannot be empty'}), 400
    
    if len(title) > 200:
        return jsonify({'error': 'Title too long (max 200 characters)'}), 400
    
    description = data.get('description', '').strip()
    if len(description) > 1000:
        return jsonify({'error': 'Description too long (max 1000 characters)'}), 400
    
    assigned_to = data.get('assigned_to')
    priority = data.get('priority', 'medium')
    
    # Validate priority
    if priority not in ['low', 'medium', 'high']:
        return jsonify({'error': 'Invalid priority. Must be: low, medium, or high'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tasks (title, description, created_by, assigned_to, priority)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, description, session['user_id'], assigned_to, priority))
    
    task_id = cursor.lastrowid
    conn.commit()
    
    return jsonify({'success': True, 'task_id': task_id}), 201

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update task"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    conn = get_db()
    
    # Update task
    conn.execute('''
        UPDATE tasks SET 
            title = COALESCE(?, title),
            description = COALESCE(?, description),
            assigned_to = COALESCE(?, assigned_to),
            priority = COALESCE(?, priority),
            status = COALESCE(?, status),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (
        data.get('title'), data.get('description'), data.get('assigned_to'),
        data.get('priority'), data.get('status'), task_id
    ))
    
    conn.commit()
    return jsonify({'success': True})

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete task - HAS UI UPDATE BUG!"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db()
    conn.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    
    # BUG: Should return task data for UI update, but doesn't
    return jsonify({'success': True})

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users for task assignment"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    conn = get_db()
    users = conn.execute('SELECT id, username, email FROM users').fetchall()
    return jsonify([dict(user) for user in users])

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'init-db':
        init_db()
    else:
        # Create database if it doesn't exist
        if not os.path.exists(DATABASE):
            init_db()
        app.run(debug=True, host='0.0.0.0', port=5000)
