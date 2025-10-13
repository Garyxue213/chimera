document.addEventListener('DOMContentLoaded', function() {
    let loginForm = document.getElementById('login');
    let taskForm = document.getElementById('task-form');
    let taskModal = document.getElementById('task-modal');
    let dashboard = document.getElementById('dashboard');
    let loginSection = document.getElementById('login-form');
    let usernameDisplay = document.getElementById('username-display');
    let newTaskBtn = document.getElementById('new-task-btn');
    let logoutBtn = document.getElementById('logout-btn');

    const apiUrl = 'http://localhost:5000/api';

    // Login Form Submission
    loginForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        let username = document.getElementById('username').value;
        let password = document.getElementById('password').value;

        let response = await fetch(`${apiUrl}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (response.ok) {
            let data = await response.json();
            loginSection.classList.add('hidden');
            dashboard.classList.remove('hidden');
            usernameDisplay.textContent = data.user.username;
            loadTasks();
        } else {
            alert('Login failed! Check your credentials.');
        }
    });

    // Logout
    logoutBtn.addEventListener('click', async function(event) {
        let response = await fetch(`${apiUrl}/auth/logout`, {
            method: 'POST'
        });

        if (response.ok) {
            loginSection.classList.remove('hidden');
            dashboard.classList.add('hidden');
            alert('Logged out successfully!');
        } else {
            alert('Logout failed! Try again.');
        }
    });

    // New Task Button
    newTaskBtn.addEventListener('click', function() {
        taskModal.classList.remove('hidden');
    });

    // Close Modal
    taskModal.querySelector('.close').addEventListener('click', function() {
        taskModal.classList.add('hidden');
    });

    // Task Form Submission
    taskForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        let title = document.getElementById('task-title').value;
        let description = document.getElementById('task-description').value;
        let priority = document.getElementById('task-priority').value;
        let assignedTo = document.getElementById('task-assignee').value;

        let response = await fetch(`${apiUrl}/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, description, priority, assigned_to: assignedTo || null })
        });

        if (response.ok) {
            alert('Task created successfully!');
            taskModal.classList.add('hidden');
            loadTasks();
        } else {
            alert('Failed to create task!');
        }
    });

    // Load Tasks
    async function loadTasks() {
        let response = await fetch(`${apiUrl}/tasks`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });

        if (response.ok) {
            let tasks = await response.json();
            renderTasks(tasks);
        } else {
            alert('Failed to load tasks!');
        }
    }

    // Render Tasks
    function renderTasks(tasks) {
        let tasksContainer = document.getElementById('tasks-container');
        tasksContainer.innerHTML = '';

        tasks.forEach(task => {
            let taskElement = document.createElement('div');
            taskElement.className = 'task-item';
            taskElement.innerHTML = `
                <div>
                    <strong>${task.title}</strong><br>
                    <span>${task.description || ''}</span>
                </div>
                <div>
                    <span>Priority: ${task.priority}</span><br>
                    <span>Status: ${task.status}</span>
                </div>
                <div>
                    <button class="btn secondary" onclick="deleteTask(${task.id})">Delete</button>
                </div>
            `;
            tasksContainer.appendChild(taskElement);
        });
    }

    // Delete Task
    window.deleteTask = async function(taskId) {
        let response = await fetch(`${apiUrl}/tasks/${taskId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            alert('Task deleted successfully!');
            loadTasks();
        } else {
            alert('Failed to delete task!');
        }
    }

    // Load users to assign tasks
    async function loadUsers() {
        let response = await fetch(`${apiUrl}/users`, { method: 'GET' });
        if (response.ok) {
            let users = await response.json();
            let assigneeSelect = document.getElementById('task-assignee');
            users.forEach(user => {
                let option = document.createElement('option');
                option.value = user.id;
                option.textContent = user.username;
                assigneeSelect.appendChild(option);
            });
        }
    }

    // Initial Load
    loadUsers();
});

