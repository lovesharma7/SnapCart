document.addEventListener('DOMContentLoaded', () => {
    // Show/hide forms
    document.getElementById('show-register').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('login-form').style.display = 'none';
        document.getElementById('register-form').style.display = 'block';
    });
    
    document.getElementById('show-login').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('register-form').style.display = 'none';
        document.getElementById('login-form').style.display = 'block';
    });
    
    // Login
    document.getElementById('login-btn').addEventListener('click', login);
    document.getElementById('login-password').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') login();
    });
    
    // Register
    document.getElementById('register-btn').addEventListener('click', register);
});

// Login function
async function login() {
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;
    const messageDiv = document.getElementById('login-message');
    
    if (!username || !password) {
        showMessage(messageDiv, 'Please fill in all fields', 'error');
        return;
    }
    
    try {
        const response = await fetch('http://127.0.0.1:5000/api/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(messageDiv, 'Login successful! Redirecting...', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 1000);
        } else {
            showMessage(messageDiv, data.message || 'Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showMessage(messageDiv, 'An error occurred', 'error');
    }
}

// Register function
async function register() {
    const username = document.getElementById('register-username').value.trim();
    const email = document.getElementById('register-email').value.trim();
    const password = document.getElementById('register-password').value;
    const messageDiv = document.getElementById('register-message');
    
    if (!username || !email || !password) {
        showMessage(messageDiv, 'Please fill in all fields', 'error');
        return;
    }
    
    try {
        const response = await fetch('http://127.0.0.1:5000/api/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showMessage(messageDiv, 'Registration successful! Please login.', 'success');
            setTimeout(() => {
                document.getElementById('show-login').click();
            }, 1500);
        } else {
            showMessage(messageDiv, data.error || 'Registration failed', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showMessage(messageDiv, 'An error occurred', 'error');
    }
}

// Show message helper
function showMessage(element, message, type) {
    element.textContent = message;
    element.className = `message ${type}`;
    element.style.display = 'block';
}
