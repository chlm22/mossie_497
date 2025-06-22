#!/usr/bin/env python3
"""
Run script for Mossie Flask application
"""
import os
import sys
import uuid
import hashlib
import secrets
import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session

# Create Flask app
app = Flask(__name__, template_folder='temp/templates', static_folder='temp/static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_testing')

# Database configuration
db_url = os.environ.get('DATABASE_URL', 'dbname=mossie host=localhost')

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # For the direct SQL version, we simulate login with PostgreSQL
        try:
            import psycopg2
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, password_hash, password_salt FROM users WHERE username = %s",
                (username,)
            )
            user = cursor.fetchone()
            
            if user:
                user_id, password_hash, password_salt = user
                hashed = hashlib.sha256((password + password_salt).encode('utf-8')).hexdigest()
                
                if hashed == password_hash:
                    # Update last login timestamp
                    cursor.execute(
                        "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = %s",
                        (user_id,)
                    )
                    conn.commit()
                    
                    session.clear()
                    session['user_id'] = user_id
                    session['username'] = username
                    
                    next_url = request.args.get('next')
                    if next_url and next_url.startswith('/'):
                        return redirect(next_url)
                    return redirect(url_for('dashboard'))
                else:
                    error = 'Invalid username or password'
            else:
                error = 'Invalid username or password'
                
            cursor.close()
            conn.close()
        except Exception as e:
            error = f"Database error: {str(e)}"
    
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            import psycopg2
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            # Check if username exists
            cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                error = 'Username already exists'
            else:
                # Create new user
                user_id = str(uuid.uuid4())
                salt = str(uuid.uuid4())
                password_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
                
                cursor.execute(
                    "INSERT INTO users (user_id, username, password_hash, password_salt) "
                    "VALUES (%s, %s, %s, %s)",
                    (user_id, username, password_hash, salt)
                )
                conn.commit()
                flash('Account created successfully! Please log in.')
                return redirect(url_for('login'))
                
            cursor.close()
            conn.close()
        except Exception as e:
            error = f"Database error: {str(e)}"
    
    return render_template('register.html', error=error)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('login'))

@app.route('/reset_request', methods=['GET', 'POST'])
def reset_request():
    if request.method == 'POST':
        username = request.form['username']
        
        try:
            import psycopg2
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            if user:
                # Generate reset token
                token = secrets.token_hex(16)
                # Token expires in 1 hour
                expiry = datetime.datetime.now() + datetime.timedelta(hours=1)
                
                # Store token in database
                cursor.execute(
                    "UPDATE users SET reset_token = %s, reset_token_expiry = %s WHERE user_id = %s",
                    (token, expiry, user[0])
                )
                conn.commit()
                
                # In a real app, send email with reset link
                reset_link = url_for('reset_password', token=token, _external=True)
                print(f"Password reset link for {username}: {reset_link}")
                
                flash('Password reset instructions sent. Check console for the reset link.')
                return redirect(url_for('login'))
            else:
                flash('No account found with that username')
                
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f"Error: {str(e)}")
    
    return render_template('reset_request.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        password = request.form['password']
        
        try:
            import psycopg2
            conn = psycopg2.connect(db_url)
            cursor = conn.cursor()
            
            # Check if token is valid and not expired
            cursor.execute(
                "SELECT user_id FROM users WHERE reset_token = %s AND reset_token_expiry > %s",
                (token, datetime.datetime.now())
            )
            user = cursor.fetchone()
            
            if user:
                # Update password
                salt = str(uuid.uuid4())
                password_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
                
                cursor.execute(
                    "UPDATE users SET password_hash = %s, password_salt = %s, reset_token = NULL, reset_token_expiry = NULL WHERE user_id = %s",
                    (password_hash, salt, user[0])
                )
                conn.commit()
                
                flash('Password has been reset. You can now log in with your new password.')
                return redirect(url_for('login'))
            else:
                flash('Invalid or expired token')
                return redirect(url_for('reset_request'))
                
            cursor.close()
            conn.close()
        except Exception as e:
            flash(f"Error: {str(e)}")
    
    # Check if token is valid before showing the form
    try:
        import psycopg2
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT 1 FROM users WHERE reset_token = %s AND reset_token_expiry > %s",
            (token, datetime.datetime.now())
        )
        if not cursor.fetchone():
            flash('Invalid or expired token')
            return redirect(url_for('reset_request'))
            
        cursor.close()
        conn.close()
    except Exception as e:
        flash(f"Database error: {str(e)}")
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
