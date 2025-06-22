"""Mossie model (database) API."""

import sqlite3
import flask
import os
import hashlib
import uuid
import secrets
import datetime
import temp


def get_db():
    """Open a new database connection."""
    if "sqlite_db" not in flask.g:
        flask.g.sqlite_db = sqlite3.connect(
            flask.current_app.config["DATABASE_FILENAME"],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        # Enable foreign keys
        flask.g.sqlite_db.execute("PRAGMA foreign_keys = ON")
        # Configure SQLite to return rows as dictionaries
        flask.g.sqlite_db.row_factory = sqlite3.Row

    return flask.g.sqlite_db


def close_db(e=None):
    """Close the database connection at the end of a request."""
    db = flask.g.pop("sqlite_db", None)

    if db is not None:
        db.close()


def init_db():
    """Create database tables if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create users table with UUID, username, salted password, and timestamp fields
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            reset_token TEXT,
            reset_token_expires TIMESTAMP
        )
    ''')
    
    # Create index on username
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
    
    conn.commit()
    
    # Initialize feature-specific tables
    init_user_settings_table()
    init_journal_tables()
    init_pet_tables()
    init_mood_tables()
    
def init_db_from_schema(schema_file):
    """Initialize database from a schema file."""
    conn = get_db()
    cursor = conn.cursor()
    
    with open(schema_file, 'r') as f:
        sql_schema = f.read()
        
    cursor.execute(sql_schema)
    conn.commit()


def init_app(app):
    """Register database functions with the Flask app."""
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
        init_user_settings_table()
        init_journal_tables()
        init_pet_tables()
        init_mood_tables()


def create_user(username, password):
    """Create a new user with salted password hash."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if username already exists
    cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
    if cursor.fetchone() is not None:
        return False
    
    # Generate a new UUID for user_id
    user_id = str(uuid.uuid4())
    
    # Generate a random salt
    salt = str(uuid.uuid4())
    
    # Create salted and hashed password
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    
    # Insert new user
    cursor.execute(
        "INSERT INTO users (user_id, username, password_hash, password_salt) VALUES (?, ?, ?, ?)",
        (user_id, username, password_hash, salt)
    )
    conn.commit()
    
    return True


def verify_user(username, password):
    """Verify username and password."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get user record
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if user is None:
        return None
    
    # Check password
    salt = user['password_salt']
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    
    if password_hash != user['password_hash']:
        return None
    
    # Update last login time
    update_cursor = conn.cursor()
    update_cursor.execute(
        "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE user_id = ?",
        (user['user_id'],)
    )
    conn.commit()
    
    return dict(user)  # Convert to regular dict for returning


def generate_reset_token(username):
    """Generate a password reset token for the specified user."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if user is None:
        return None
    
    # Generate token and expiration time (1 hour from now)
    token = secrets.token_hex(32)
    expires = datetime.datetime.now() + datetime.timedelta(hours=1)
    
    # Save token to database
    cursor.execute(
        "UPDATE users SET reset_token = ?, reset_token_expires = ? WHERE user_id = ?",
        (token, expires, user['user_id'])
    )
    conn.commit()
    
    return token


def verify_reset_token(token):
    """Verify a password reset token and return the user if valid."""
    if not token:
        return None
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get user with matching token that hasn't expired
    cursor.execute(
        "SELECT * FROM users WHERE reset_token = ? AND reset_token_expires > ?",
        (token, datetime.datetime.now())
    )
    user = cursor.fetchone()
    
    if user is None:
        return None
    
    return dict(user)


def reset_password(user_id, new_password):
    """Reset a user's password and clear the reset token."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Generate a new salt
    salt = str(uuid.uuid4())
    
    # Create new salted and hashed password
    password_hash = hashlib.sha256((new_password + salt).encode()).hexdigest()
    
    # Update password and clear reset token
    cursor.execute(
        "UPDATE users SET password_hash = ?, password_salt = ?, reset_token = NULL, reset_token_expires = NULL WHERE user_id = ?",
        (password_hash, salt, user_id)
    )
    conn.commit()
    
    return True
# ======== User Settings Functions ========

def init_user_settings_table():
    """Create the user settings table if it doesn't exist."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id TEXT PRIMARY KEY,
            dark_mode INTEGER DEFAULT 0,
            high_contrast INTEGER DEFAULT 0,
            font_size TEXT DEFAULT 'medium',
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()

def get_user_settings(user_id):
    """Get settings for a specific user."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if user has settings, if not create default settings
    cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    settings = cursor.fetchone()
    
    if settings is None:
        # Create default settings for user
        cursor.execute(
            "INSERT INTO user_settings (user_id) VALUES (?)",
            (user_id,)
        )
        conn.commit()
        
        # Get the newly created settings
        cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
        settings = cursor.fetchone()
    
    return dict(settings)

def update_user_settings(user_id, dark_mode=None, high_contrast=None, font_size=None):
    """Update user settings."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get current settings
    current_settings = get_user_settings(user_id)
    
    # Update only the provided fields
    if dark_mode is None:
        dark_mode = current_settings['dark_mode']
    if high_contrast is None:
        high_contrast = current_settings['high_contrast']
    if font_size is None:
        font_size = current_settings['font_size']
    
    # Update the settings
    cursor.execute(
        """
        UPDATE user_settings 
        SET dark_mode = ?, high_contrast = ?, font_size = ?, last_updated = CURRENT_TIMESTAMP 
        WHERE user_id = ?
        """,
        (dark_mode, high_contrast, font_size, user_id)
    )
    conn.commit()
    
    # Get updated settings
    cursor.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
    return dict(cursor.fetchone())
# ======== Journal Functions ========

def init_journal_tables():
    """Create journal tables if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS journal_entries (
            entry_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_journal_user_id ON journal_entries(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_journal_created_at ON journal_entries(created_at)')
    
    conn.commit()

def get_journal_entries(user_id):
    """Get all journal entries for a user, ordered by most recent first."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM journal_entries WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    
    entries = cursor.fetchall()
    return [dict(entry) for entry in entries]

def get_journal_entry(user_id, entry_id):
    """Get a specific journal entry."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM journal_entries WHERE user_id = ? AND entry_id = ?",
        (user_id, entry_id)
    )
    
    entry = cursor.fetchone()
    if entry is None:
        return None
    
    return dict(entry)

def create_journal_entry(user_id, title, content):
    """Create a new journal entry."""
    conn = get_db()
    cursor = conn.cursor()
    
    entry_id = str(uuid.uuid4())
    
    cursor.execute(
        "INSERT INTO journal_entries (entry_id, user_id, title, content) VALUES (?, ?, ?, ?)",
        (entry_id, user_id, title, content)
    )
    conn.commit()
    
    return entry_id

def update_journal_entry(entry_id, title, content):
    """Update an existing journal entry."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        UPDATE journal_entries 
        SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE entry_id = ?
        """,
        (title, content, entry_id)
    )
    conn.commit()
    
    return True

def delete_journal_entry(user_id, entry_id):
    """Delete a journal entry."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "DELETE FROM journal_entries WHERE user_id = ? AND entry_id = ?",
        (user_id, entry_id)
    )
    conn.commit()
    
    # Check if any rows were affected
    return cursor.rowcount > 0
# ======== Pet Functions ========

def init_pet_tables():
    """Create pet tables if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Create user_pets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_pets (
            user_id TEXT PRIMARY KEY,
            pet_name TEXT DEFAULT 'Mossie',
            engagement_points INTEGER DEFAULT 0,
            last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    ''')
    
    # Create pet_accessories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pet_accessories (
            accessory_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            description TEXT
        )
    ''')
    
    # Create user_pet_accessories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_pet_accessories (
            user_id TEXT,
            accessory_id INTEGER,
            is_active INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, accessory_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (accessory_id) REFERENCES pet_accessories(accessory_id) ON DELETE CASCADE
        )
    ''')
    
    # Insert default accessories if they don't exist
    cursor.execute("SELECT COUNT(*) FROM pet_accessories")
    if cursor.fetchone()[0] == 0:
        accessories = [
            ('Red Hat', 'hat', 'A stylish red hat for your pet'),
            ('Blue Glasses', 'glasses', 'Cool blue sunglasses'),
            ('Bow Tie', 'neck', 'A fancy bow tie'),
            ('Scarf', 'neck', 'A warm scarf for cold days'),
            ('Party Hat', 'hat', 'A colorful party hat for celebrations')
        ]
        
        for acc in accessories:
            cursor.execute(
                "INSERT INTO pet_accessories (name, type, description) VALUES (?, ?, ?)",
                acc
            )
    
    conn.commit()

def get_user_pet(user_id):
    """Get pet data for a user, create if doesn't exist."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM user_pets WHERE user_id = ?", (user_id,))
    pet = cursor.fetchone()
    
    if pet is None:
        # Create default pet for user
        cursor.execute(
            "INSERT INTO user_pets (user_id) VALUES (?)",
            (user_id,)
        )
        conn.commit()
        
        # Get the newly created pet
        cursor.execute("SELECT * FROM user_pets WHERE user_id = ?", (user_id,))
        pet = cursor.fetchone()
        
        # Give user default accessories
        cursor.execute("SELECT accessory_id FROM pet_accessories LIMIT 2")
        default_accessories = cursor.fetchall()
        
        for acc in default_accessories:
            cursor.execute(
                "INSERT INTO user_pet_accessories (user_id, accessory_id, is_active) VALUES (?, ?, ?)",
                (user_id, acc[0], 0)
            )
        conn.commit()
    
    return dict(pet)

def get_pet_accessories(user_id):
    """Get all accessories for a user's pet."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT pa.accessory_id, pa.name, pa.type, pa.description, 
               COALESCE(upa.is_active, 0) as is_active
        FROM pet_accessories pa
        LEFT JOIN user_pet_accessories upa ON pa.accessory_id = upa.accessory_id AND upa.user_id = ?
        ORDER BY pa.type, pa.name
    ''', (user_id,))
    
    accessories = cursor.fetchall()
    return [dict(acc) for acc in accessories]

def toggle_pet_accessory(user_id, accessory_id):
    """Toggle an accessory for a user's pet."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if user has this accessory
    cursor.execute(
        "SELECT is_active FROM user_pet_accessories WHERE user_id = ? AND accessory_id = ?",
        (user_id, accessory_id)
    )
    result = cursor.fetchone()
    
    if result is None:
        # User doesn't have this accessory yet, add it
        cursor.execute(
            "INSERT INTO user_pet_accessories (user_id, accessory_id, is_active) VALUES (?, ?, 1)",
            (user_id, accessory_id)
        )
    else:
        # Toggle the active state (SQLite doesn't have a NOT operator for booleans)
        new_state = 1 if result[0] == 0 else 0
        cursor.execute(
            "UPDATE user_pet_accessories SET is_active = ? WHERE user_id = ? AND accessory_id = ?",
            (new_state, user_id, accessory_id)
        )
    
    conn.commit()
    return True

def update_pet_engagement(user_id, points=1):
    """Update pet engagement points for a user."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get current pet data or create if doesn't exist
    pet = get_user_pet(user_id)
    
    # Update engagement points and last interaction time
    cursor.execute(
        """
        UPDATE user_pets 
        SET engagement_points = engagement_points + ?, last_interaction = CURRENT_TIMESTAMP 
        WHERE user_id = ?
        """,
        (points, user_id)
    )
    conn.commit()
    
    # Get updated pet data
    cursor.execute("SELECT * FROM user_pets WHERE user_id = ?", (user_id,))
    updated_pet = cursor.fetchone()
    return dict(updated_pet)
# ======== Mood Tracking Functions ========

def init_mood_tables():
    """Create mood tracking tables if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_moods (
            mood_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            mood_value INTEGER NOT NULL CHECK (mood_value BETWEEN 1 AND 5),
            mood_note TEXT,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_moods_user_id ON user_moods(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_moods_recorded_at ON user_moods(recorded_at)')
    
    conn.commit()

def set_mood(user_id, mood_value, mood_note=None):
    """Record a mood entry for a user."""
    if not 1 <= mood_value <= 5:
        raise ValueError("Mood value must be between 1 and 5")
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if user already recorded a mood today
    today = datetime.datetime.now().date().isoformat()
    cursor.execute(
        """
        SELECT * FROM user_moods 
        WHERE user_id = ? AND DATE(recorded_at) = ?
        """,
        (user_id, today)
    )
    
    existing_mood = cursor.fetchone()
    
    if existing_mood:
        # Update existing mood for today
        cursor.execute(
            """
            UPDATE user_moods 
            SET mood_value = ?, mood_note = ?, recorded_at = CURRENT_TIMESTAMP 
            WHERE mood_id = ?
            """,
            (mood_value, mood_note, existing_mood['mood_id'])
        )
        conn.commit()
        
        # Get updated mood
        cursor.execute("SELECT * FROM user_moods WHERE mood_id = ?", (existing_mood['mood_id'],))
    else:
        # Insert new mood
        cursor.execute(
            """
            INSERT INTO user_moods (user_id, mood_value, mood_note) 
            VALUES (?, ?, ?)
            """,
            (user_id, mood_value, mood_note)
        )
        conn.commit()
        
        # Get the newly created mood
        cursor.execute("SELECT * FROM user_moods WHERE user_id = ? ORDER BY recorded_at DESC LIMIT 1", (user_id,))
    
    return dict(cursor.fetchone())

def get_weekly_moods(user_id):
    """Get mood entries for the past 7 days."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Calculate date 7 days ago
    seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()
    
    # Get moods for the last 7 days
    cursor.execute(
        """
        SELECT * FROM user_moods 
        WHERE user_id = ? AND recorded_at >= ?
        ORDER BY recorded_at
        """,
        (user_id, seven_days_ago)
    )
    
    moods = cursor.fetchall()
    return [dict(mood) for mood in moods]

def get_monthly_moods(user_id, year, month):
    """Get mood entries for a specific month."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Validate month and year
    if not (1 <= month <= 12):
        raise ValueError("Month must be between 1 and 12")
    
    # Get start and end date for the month
    start_date = datetime.date(year, month, 1).isoformat()
    if month == 12:
        end_date = datetime.date(year + 1, 1, 1).isoformat()
    else:
        end_date = datetime.date(year, month + 1, 1).isoformat()
    
    # Get moods for the specified month
    cursor.execute(
        """
        SELECT * FROM user_moods 
        WHERE user_id = ? AND recorded_at >= ? AND recorded_at < ?
        ORDER BY recorded_at
        """,
        (user_id, start_date, end_date)
    )
    
    moods = cursor.fetchall()
    return [dict(mood) for mood in moods]
