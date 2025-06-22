# ======== Mood Tracking Functions ========

def init_mood_tables():
    """Create mood tracking tables if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_moods (
            mood_id SERIAL PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            mood_value INTEGER NOT NULL CHECK (mood_value BETWEEN 1 AND 5),
            mood_note TEXT,
            recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_moods_user_id ON user_moods(user_id);
        CREATE INDEX IF NOT EXISTS idx_moods_recorded_at ON user_moods(recorded_at);
    ''')
    
    conn.commit()

def set_mood(user_id, mood_value, mood_note=None):
    """Record a mood entry for a user."""
    if not 1 <= mood_value <= 5:
        raise ValueError("Mood value must be between 1 and 5")
    
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Check if user already recorded a mood today
    today = datetime.datetime.now().date()
    cursor.execute(
        """
        SELECT * FROM user_moods 
        WHERE user_id = %s AND DATE(recorded_at) = %s
        """,
        (user_id, today)
    )
    
    existing_mood = cursor.fetchone()
    
    if existing_mood:
        # Update existing mood for today
        cursor.execute(
            """
            UPDATE user_moods 
            SET mood_value = %s, mood_note = %s, recorded_at = CURRENT_TIMESTAMP 
            WHERE mood_id = %s
            RETURNING *
            """,
            (mood_value, mood_note, existing_mood['mood_id'])
        )
    else:
        # Insert new mood
        cursor.execute(
            """
            INSERT INTO user_moods (user_id, mood_value, mood_note) 
            VALUES (%s, %s, %s)
            RETURNING *
            """,
            (user_id, mood_value, mood_note)
        )
    
    conn.commit()
    return dict(cursor.fetchone())

def get_weekly_moods(user_id):
    """Get mood entries for the past 7 days."""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Get moods for the last 7 days
    cursor.execute(
        """
        SELECT * FROM user_moods 
        WHERE user_id = %s AND recorded_at >= CURRENT_DATE - INTERVAL '7 days'
        ORDER BY recorded_at
        """,
        (user_id,)
    )
    
    moods = cursor.fetchall()
    return [dict(mood) for mood in moods]

def get_monthly_moods(user_id, year, month):
    """Get mood entries for a specific month."""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Validate month and year
    if not (1 <= month <= 12):
        raise ValueError("Month must be between 1 and 12")
    
    # Get start and end date for the month
    start_date = datetime.date(year, month, 1)
    if month == 12:
        end_date = datetime.date(year + 1, 1, 1)
    else:
        end_date = datetime.date(year, month + 1, 1)
    
    # Get moods for the specified month
    cursor.execute(
        """
        SELECT * FROM user_moods 
        WHERE user_id = %s AND recorded_at >= %s AND recorded_at < %s
        ORDER BY recorded_at
        """,
        (user_id, start_date, end_date)
    )
    
    moods = cursor.fetchall()
    return [dict(mood) for mood in moods]
