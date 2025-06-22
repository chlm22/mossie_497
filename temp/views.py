"""Mossie views/routes."""

import flask
from flask import redirect, render_template, request, session, url_for, flash
import temp
from temp import models
from functools import wraps


@temp.app.route('/')
def index():
    """Redirect to login page."""
    return redirect(url_for('login'))


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


@temp.app.route('/login', methods=['GET', 'POST'])
def login():
    """User login view."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Verify credentials
        user = models.verify_user(username, password)
        
        if user:
            # Store user information in session
            session.clear()
            session['user_id'] = str(user['user_id'])
            session['username'] = user['username']
            
            # Check if a next parameter exists
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard')
                
            return redirect(next_page)
        
        # Authentication failed
        return render_template('login.html', error="Invalid username or password")
    
    # GET request - show the login form
    return render_template('login.html')


@temp.app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard view."""
    return render_template('dashboard.html', username=session['username'])


@temp.app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration view."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Create new user
        success = models.create_user(username, password)
        
        if success:
            return redirect(url_for('login'))
        else:
            return render_template('register.html', error="Username already exists")
    
    # GET request - show the registration form
    return render_template('register.html')


@temp.app.route('/logout')
def logout():
    """User logout."""
    # Clear the session
    session.clear()
    return redirect(url_for('login'))


@temp.app.route('/reset-request', methods=['GET', 'POST'])
def reset_request():
    """Password reset request view."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form['username']
        
        # Generate reset token
        token = models.generate_reset_token(username)
        
        if token:
            # In a real application, send an email with the reset token
            reset_link = url_for('reset_password', token=token, _external=True)
            
            # For demonstration purposes, just display the link
            success_message = f"Password reset link has been generated. In a real application, this would be emailed to the user."
            
            # Log the reset link for demo purposes
            print(f"Reset link for {username}: {reset_link}")
            
            return render_template('reset_request.html', success=success_message, reset_link=reset_link)
        
        # User not found
        return render_template('reset_request.html', error="No account found with that username")
    
    # GET request - show the reset request form
    return render_template('reset_request.html')


@temp.app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Password reset view."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    # Verify token
    user = models.verify_reset_token(token)
    
    if user is None:
        return redirect(url_for('reset_request', error="Invalid or expired token"))
    
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validate passwords match
        if password != confirm_password:
            return render_template('reset_password.html', error="Passwords do not match", token=token)
        
        # Reset password
        if models.reset_password(user['user_id'], password):
            return redirect(url_for('login', success="Your password has been reset!"))
        else:
            return render_template('reset_password.html', error="Password reset failed", token=token)
    
    # GET request - show the password reset form
    return render_template('reset_password.html', token=token)
