import unittest
import json
import os
import tempfile
from urllib.parse import urljoin
from backend.app import app, init_db, get_db

# Task test class for Flask application
class TestTasks(unittest.TestCase):
    def setUp(self):
        """Set up test client and initialize database."""
        # Create a temporary database for testing
        self.test_db_fd, self.test_db_path = tempfile.mkstemp()
        app.config['DATABASE'] = self.test_db_path
        app.config['TESTING'] = True
        
        # Patch the DATABASE constant in the app module
        import backend.app as backend_app
        self.original_database = backend_app.DATABASE
        backend_app.DATABASE = self.test_db_path
        
        self.app = app.test_client()
        with app.app_context():
            init_db()
    
    def tearDown(self):
        """Clean up test database."""
        import backend.app as backend_app
        backend_app.DATABASE = self.original_database
        os.close(self.test_db_fd)
        os.unlink(self.test_db_path)

    def login(self, username, password):
        """Helper method to authenticate a user."""
        return self.app.post('/api/auth/login', json={
            'username': username,
            'password': password
        })

    def test_get_tasks_unauthenticated(self):
        """Test fetching tasks without authentication."""
        response = self.app.get('/api/tasks')
        self.assertEqual(response.status_code, 401)

    def test_get_tasks_authenticated(self):
        """Test fetching tasks with authentication."""
        self.login('admin', 'admin123')
        response = self.app.get('/api/tasks')
        self.assertEqual(response.status_code, 200)

    def test_create_task_valid(self):
        """Test creating a new task with valid data."""
        self.login('admin', 'admin123')
        response = self.app.post('/api/tasks', json={
            'title': 'Test Task',
            'description': 'Test description',
            'priority': 'high'
        })
        self.assertEqual(response.status_code, 201)

    def test_create_task_no_title(self):
        """Test creating a task without providing a title."""
        self.login('admin', 'admin123')
        response = self.app.post('/api/tasks', json={
            'description': 'Test task without title'
        })
        self.assertEqual(response.status_code, 400)

    def test_update_task(self):
        """Test updating an existing task."""
        self.login('admin', 'admin123')
        create_response = self.app.post('/api/tasks', json={
            'title': 'Update Task',
            'description': 'Task for update test',
            'priority': 'medium'
        })
        task_id = create_response.get_json()['task_id']
        response = self.app.put(f'/api/tasks/{task_id}', json={
            'status': 'completed'
        })
        self.assertEqual(response.status_code, 200)

    def test_delete_task(self):
        """Test deleting a task."""
        self.login('admin', 'admin123')
        create_response = self.app.post('/api/tasks', json={
            'title': 'Delete Task',
            'description': 'Task to be deleted'
        })
        task_id = create_response.get_json()['task_id']
        response = self.app.delete(f'/api/tasks/{task_id}')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()

