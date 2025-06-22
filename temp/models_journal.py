# ======== Journal Functions ========

def init_journal_tables():
    """Create journal tables if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS journal_entries (
            entry_id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_journal_user_id ON journal_entries(user_id);
        CREATE INDEX IF NOT EXISTS idx_journal_created_at ON journal_entries(created_at);
    ''')
    
    conn.commit()

def get_journal_entries(user_id):
    """Get all journal entries for a user, ordered by most recent first."""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    cursor.execute(
        "SELECT * FROM journal_entries WHERE user_id = %s ORDER BY created_at DESC",
        (user_id,)
    )
    
    entries = cursor.fetchall()
    return [dict(entry) for entry in entries]

def get_journal_entry(user_id, entry_id):
    """Get a specific journal entry."""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    cursor.execute(
        "SELECT * FROM journal_entries WHERE user_id = %s AND entry_id = %s",
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
        "INSERT INTO journal_entries (entry_id, user_id, title, content) VALUES (%s, %s, %s, %s)",
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
        SET title = %s, content = %s, updated_at = CURRENT_TIMESTAMP 
        WHERE entry_id = %s
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
        "DELETE FROM journal_entries WHERE user_id = %s AND entry_id = %s",
        (user_id, entry_id)
    )
    conn.commit()
    
    # Check if any rows were affected
    return cursor.rowcount > 0
