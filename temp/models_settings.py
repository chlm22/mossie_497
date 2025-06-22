# ======== User Settings Functions ========

def init_user_settings_table():
    """Create the user settings table if it doesn't exist."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
            dark_mode BOOLEAN DEFAULT FALSE,
            high_contrast BOOLEAN DEFAULT FALSE,
            font_size VARCHAR(20) DEFAULT 'medium',
            last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    conn.commit()

def get_user_settings(user_id):
    """Get settings for a specific user."""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Check if user has settings, if not create default settings
    cursor.execute("SELECT * FROM user_settings WHERE user_id = %s", (user_id,))
    settings = cursor.fetchone()
    
    if settings is None:
        # Create default settings for user
        cursor.execute(
            "INSERT INTO user_settings (user_id) VALUES (%s) RETURNING *",
            (user_id,)
        )
        conn.commit()
        settings = cursor.fetchone()
    
    return dict(settings)

def update_user_settings(user_id, dark_mode=None, high_contrast=None, font_size=None):
    """Update user settings."""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
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
        SET dark_mode = %s, high_contrast = %s, font_size = %s, last_updated = CURRENT_TIMESTAMP 
        WHERE user_id = %s
        RETURNING *
        """,
        (dark_mode, high_contrast, font_size, user_id)
    )
    conn.commit()
    
    return dict(cursor.fetchone())
