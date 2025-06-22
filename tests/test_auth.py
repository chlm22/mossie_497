"""Test cases for Mossie login interface authentication system."""

import pytest
import psycopg2
import uuid
import hashlib
import time
from datetime import datetime, timedelta


class TestRegistration:
    def test_successful_registration(self, client, test_user):
        """Test Case 1: User Registration Test."""
        # Submit registration form
        response = client.post('/register', data=test_user, follow_redirects=True)
        
        # Check redirect to login page
        assert b'Account created successfully!' in response.data or b'Please log in' in response.data
        
        # Verify user in database
        conn = psycopg2.connect('dbname=mossie_test host=localhost')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (test_user['username'],))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        assert user is not None
        assert len(user) >= 4  # At least user_id, username, password_hash, password_salt
        assert user[1] == test_user['username']  # username is at index 1
        # Verify UUID format
        try:
            uuid_obj = uuid.UUID(str(user[0]))
            assert isinstance(uuid_obj, uuid.UUID)
        except ValueError:
            pytest.fail("user_id is not a valid UUID")
    
    def test_duplicate_username_registration(self, client, test_user):
        """Test Case 2: Duplicate Username Registration Test."""
        # First registration should succeed
        response = client.post('/register', data=test_user, follow_redirects=True)
        assert b'Account created successfully!' in response.data or b'Please log in' in response.data
        
        # Second registration with same username should fail
        response = client.post('/register', data=test_user)
        assert b'Username already exists' in response.data
        
        # Verify only one user was created
        conn = psycopg2.connect('dbname=mossie_test host=localhost')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = %s", (test_user['username'],))
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        assert count == 1


class TestLogin:
    def test_successful_login(self, client, test_user):
        """Test Case 3: Successful Login Test."""
        # Register the user first
        client.post('/register', data=test_user, follow_redirects=True)
        
        # Clear the session
        client.get('/logout')
        
        # Try to log in
        response = client.post('/login', data=test_user, follow_redirects=True)
        
        # Check if login was successful
        assert b'Welcome' in response.data or b'Dashboard' in response.data or test_user['username'].encode() in response.data
        
        # Verify session is set
        with client.session_transaction() as session:
            assert 'user_id' in session
            assert 'username' in session
            assert session['username'] == test_user['username']
    
    def test_failed_login(self, client, test_user):
        """Test Case 4: Failed Login Test."""
        # Register the user first
        client.post('/register', data=test_user, follow_redirects=True)
        
        # Test nonexistent user
        response = client.post('/login', data={
            'username': 'nonexistent_user',
            'password': test_user['password']
        })
        assert b'Invalid username or password' in response.data
        
        # Test wrong password
        response = client.post('/login', data={
            'username': test_user['username'],
            'password': 'WrongPassword123!'
        })
        assert b'Invalid username or password' in response.data


class TestLastLogin:
    def test_last_login_timestamp(self, client, test_user):
        """Test Case 5: Last Login Timestamp Test."""
        # Register the user
        client.post('/register', data=test_user, follow_redirects=True)
        
        # Check initial login timestamp
        conn = psycopg2.connect('dbname=mossie_test host=localhost')
        cursor = conn.cursor()
        cursor.execute("SELECT last_login FROM users WHERE username = %s", (test_user['username'],))
        initial_timestamp = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        # Wait a moment to ensure timestamp will be different
        time.sleep(1)
        
        # Log in again
        client.post('/login', data=test_user)
        
        # Check updated login timestamp
        conn = psycopg2.connect('dbname=mossie_test host=localhost')
        cursor = conn.cursor()
        cursor.execute("SELECT last_login FROM users WHERE username = %s", (test_user['username'],))
        updated_timestamp = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        # Verify timestamp was updated
        if initial_timestamp is None:
            assert updated_timestamp is not None
        else:
            assert updated_timestamp > initial_timestamp


class TestPasswordReset:
    def test_password_reset_request(self, client, test_user):
        """Test Case 6: Password Reset Request Test."""
        # Register the user
        client.post('/register', data=test_user, follow_redirects=True)
        
        # Request password reset
        response = client.post('/reset-request', data={'username': test_user['username']}, follow_redirects=True)
        assert b'Password reset link' in response.data
        
        # Check database for reset token
        conn = psycopg2.connect('dbname=mossie_test host=localhost')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT reset_token, reset_token_expires FROM users WHERE username = %s", 
            (test_user['username'],)
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        reset_token, expiry = result
        assert reset_token is not None
        assert expiry is not None
        
        # Verify expiry is in the future (1 hour)
        now = datetime.now()
        assert expiry > now
        time_diff = expiry - now
        assert time_diff < timedelta(hours=1, minutes=5)  # Allow for processing time
    
    def test_password_reset_with_valid_token(self, client, test_user):
        """Test Case 7: Password Reset with Valid Token Test."""
        # Register the user
        client.post('/register', data=test_user, follow_redirects=True)
        
        # Request password reset
        client.post('/reset-request', data={'username': test_user['username']})
        
        # Get token from database
        conn = psycopg2.connect('dbname=mossie_test host=localhost')
        cursor = conn.cursor()
        cursor.execute("SELECT reset_token FROM users WHERE username = %s", (test_user['username'],))
        token = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        # Reset password using token
        new_password = 'NewPassword456!'
        response = client.post(
            f'/reset-password/{token}',
            data={'password': new_password, 'confirm_password': new_password},
            follow_redirects=True
        )
        
        # Check if redirected to login
        assert b'login' in response.data.lower() or b'sign in' in response.data.lower()
        
        # Try logging in with new password
        response = client.post('/login', data={
            'username': test_user['username'],
            'password': new_password
        }, follow_redirects=True)
        assert b'Dashboard' in response.data or test_user['username'].encode() in response.data
        
        # Check that token is cleared
        conn = psycopg2.connect('dbname=mossie_test host=localhost')
        cursor = conn.cursor()
        cursor.execute("SELECT reset_token FROM users WHERE username = %s", (test_user['username'],))
        token_after = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        assert token_after is None
    
    def test_password_reset_with_expired_token(self, client, test_user):
        """Test Case 8: Password Reset with Expired Token Test."""
        # Register the user
        client.post('/register', data=test_user, follow_redirects=True)
        
        # Request password reset
        client.post('/reset-request', data={'username': test_user['username']})
        
        # Get token from database
        conn = psycopg2.connect('dbname=mossie_test host=localhost')
        cursor = conn.cursor()
        cursor.execute("SELECT reset_token FROM users WHERE username = %s", (test_user['username'],))
        token = cursor.fetchone()[0]
        
        # Set expiry to past time
        past_time = datetime.now() - timedelta(hours=1)
        cursor.execute(
            "UPDATE users SET reset_token_expires = %s WHERE username = %s",
            (past_time, test_user['username'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        # Try resetting with expired token
        new_password = 'NewPassword456!'
        response = client.post(
            f'/reset-password/{token}',
            data={'password': new_password, 'confirm_password': new_password},
            follow_redirects=True
        )
        
        # Should be redirected to reset request with error
        assert b'reset' in response.data.lower() and (b'invalid' in response.data.lower() or b'expired' in response.data.lower())


class TestSessionProtection:
    def test_session_protection(self, client, test_user):
        """Test Case 9: Session Protection Test."""
        # Attempt to access protected route without login
        response = client.get('/dashboard', follow_redirects=True)
        assert b'login' in response.data.lower() or b'sign in' in response.data.lower()
        
        # Register and login
        client.post('/register', data=test_user, follow_redirects=True)
        client.post('/login', data=test_user)
        
        # Access protected route after login
        response = client.get('/dashboard')
        assert response.status_code == 200
        assert b'Dashboard' in response.data or test_user['username'].encode() in response.data
        
        # Logout
        client.get('/logout')
        
        # Try to access protected route after logout
        response = client.get('/dashboard', follow_redirects=True)
        assert b'login' in response.data.lower() or b'sign in' in response.data.lower()


class TestSQLInjectionProtection:
    def test_sql_injection_protection(self, client):
        """Test Case 10: SQL Injection Protection Test."""
        # Define SQL injection attempts
        sql_injections = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "admin'--",
            "' UNION SELECT username, password FROM users--"
        ]
        
        for injection in sql_injections:
            # Try SQL injection in login
            response = client.post('/login', data={
                'username': injection,
                'password': 'anything'
            })
            assert b'Invalid username or password' in response.data
            
            # Try SQL injection in registration
            response = client.post('/register', data={
                'username': injection,
                'password': 'SecurePassword123!'
            })
            
            # Check if tables still exist (no drop table succeeded)
            conn = psycopg2.connect('dbname=mossie_test host=localhost')
            cursor = conn.cursor()
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')")
            table_exists = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            
            assert table_exists is True
