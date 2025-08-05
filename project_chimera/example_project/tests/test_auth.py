import unittest
import hashlib
import os
import tempfile
from backend.app import app, init_db, get_db

class TestAuth(unittest.TestCase):
    def setUp(self):
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

    def test_login_success(self):
        response = self.app.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json)

    def test_login_failure(self):
        response = self.app.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', response.json)

    def test_logout(self):
        with self.app.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'admin'
        response = self.app.post('/api/auth/logout')
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json)

    def test_logout_without_login(self):
        response = self.app.post('/api/auth/logout')
        self.assertEqual(response.status_code, 200)  # Should succeed even if not logged in
        self.assertIn('success', response.json)

class TestTasks(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        with app.app_context():
            init_db()

    def login_as_admin(self):
        self.app.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'admin123'
        })

    def test_get_tasks_unauthenticated(self):
        response = self.app.get('/api/tasks')
        self.assertEqual(response.status_code, 401)

    def test_create_task_authenticated(self):
        self.login_as_admin()
        response = self.app.post('/api/tasks', json={
            'title': 'New Task',
            'description': 'Test task',
            'priority': 'low'
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn('success', response.json)

    def test_create_task_unauthenticated(self):
        response = self.app.post('/api/tasks', json={
            'title': 'New Task',
            'description': 'Test task'
        })
        self.assertEqual(response.status_code, 401)

    def test_get_tasks_authenticated(self):
        self.login_as_admin()
        response = self.app.get('/api/tasks')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)

    def test_delete_task_authenticated(self):
        self.login_as_admin()
        response = self.app.delete('/api/tasks/1')  # Assuming task with ID 1 exists
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json)

if __name__ == '__main__':
    unittest.main()
