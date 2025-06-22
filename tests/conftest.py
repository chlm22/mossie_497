"""Test configuration for Mossie login system."""

import os
import sys
import pytest
import psycopg2
import uuid
import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import application modules
from temp import models
import run_flask


@pytest.fixture
def app():
    """Create and configure Flask app for testing."""
    app = run_flask.app
    app.config['TESTING'] = True
    app.config['DATABASE_URL'] = 'dbname=mossie_test host=localhost'
    app.config['SECRET_KEY'] = 'test_key'
    
    # Create test context
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """Create test client."""
    with app.test_client() as client:
        with app.app_context():
            setup_test_db()
        yield client
        with app.app_context():
            teardown_test_db()


@pytest.fixture
def test_user():
    """Create test user credentials."""
    return {
        'username': f'testuser_{uuid.uuid4().hex[:8]}',
        'password': 'TestPassword123!'
    }


def setup_test_db():
    """Set up test database tables."""
    conn = psycopg2.connect('dbname=mossie_test host=localhost')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id UUID PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(128) NOT NULL,
            password_salt VARCHAR(36) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP WITH TIME ZONE,
            reset_token VARCHAR(128),
            reset_token_expires TIMESTAMP WITH TIME ZONE
        );
        
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()


def teardown_test_db():
    """Clean up test database after tests."""
    conn = psycopg2.connect('dbname=mossie_test host=localhost')
    cursor = conn.cursor()
    
    # Drop tables
    cursor.execute('''
        DROP TABLE IF EXISTS users;
    ''')
    
    conn.commit()
    cursor.close()
    conn.close()
