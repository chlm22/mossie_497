# ======== Pet Functions ========

def init_pet_tables():
    """Create pet tables if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_pets (
            user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
            pet_name VARCHAR(50) DEFAULT 'Mossie',
            engagement_points INTEGER DEFAULT 0,
            last_interaction TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS pet_accessories (
            accessory_id SERIAL PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            type VARCHAR(20) NOT NULL,
            description TEXT
        );
        
        CREATE TABLE IF NOT EXISTS user_pet_accessories (
            user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
            accessory_id INTEGER REFERENCES pet_accessories(accessory_id) ON DELETE CASCADE,
            is_active BOOLEAN DEFAULT FALSE,
            PRIMARY KEY (user_id, accessory_id)
        );
    ''')
    
    # Insert default accessories if they don't exist
    cursor.execute("SELECT COUNT(*) FROM pet_accessories")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO pet_accessories (name, type, description) VALUES
            ('Red Hat', 'hat', 'A stylish red hat for your pet'),
            ('Blue Glasses', 'glasses', 'Cool blue sunglasses'),
            ('Bow Tie', 'neck', 'A fancy bow tie'),
            ('Scarf', 'neck', 'A warm scarf for cold days'),
            ('Party Hat', 'hat', 'A colorful party hat for celebrations')
        ''')
    
    conn.commit()

def get_user_pet(user_id):
    """Get pet data for a user, create if doesn't exist."""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    cursor.execute("SELECT * FROM user_pets WHERE user_id = %s", (user_id,))
    pet = cursor.fetchone()
    
    if pet is None:
        # Create default pet for user
        cursor.execute(
            "INSERT INTO user_pets (user_id) VALUES (%s) RETURNING *",
            (user_id,)
        )
        conn.commit()
        pet = cursor.fetchone()
        
        # Give user default accessories
        cursor.execute("SELECT accessory_id FROM pet_accessories LIMIT 2")
        default_accessories = cursor.fetchall()
        
        for acc in default_accessories:
            cursor.execute(
                "INSERT INTO user_pet_accessories (user_id, accessory_id, is_active) VALUES (%s, %s, %s)",
                (user_id, acc[0], False)
            )
        conn.commit()
    
    return dict(pet)

def get_pet_accessories(user_id):
    """Get all accessories for a user's pet."""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    cursor.execute('''
        SELECT pa.accessory_id, pa.name, pa.type, pa.description, 
               COALESCE(upa.is_active, FALSE) as is_active
        FROM pet_accessories pa
        LEFT JOIN user_pet_accessories upa ON pa.accessory_id = upa.accessory_id AND upa.user_id = %s
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
        "SELECT is_active FROM user_pet_accessories WHERE user_id = %s AND accessory_id = %s",
        (user_id, accessory_id)
    )
    result = cursor.fetchone()
    
    if result is None:
        # User doesn't have this accessory yet, add it
        cursor.execute(
            "INSERT INTO user_pet_accessories (user_id, accessory_id, is_active) VALUES (%s, %s, TRUE)",
            (user_id, accessory_id)
        )
    else:
        # Toggle the active state
        cursor.execute(
            "UPDATE user_pet_accessories SET is_active = NOT is_active WHERE user_id = %s AND accessory_id = %s",
            (user_id, accessory_id)
        )
    
    conn.commit()
    return True

def update_pet_engagement(user_id, points=1):
    """Update pet engagement points for a user."""
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    # Get current pet data or create if doesn't exist
    pet = get_user_pet(user_id)
    
    # Update engagement points and last interaction time
    cursor.execute(
        """
        UPDATE user_pets 
        SET engagement_points = engagement_points + %s, last_interaction = CURRENT_TIMESTAMP 
        WHERE user_id = %s
        RETURNING *
        """,
        (points, user_id)
    )
    conn.commit()
    
    updated_pet = cursor.fetchone()
    return dict(updated_pet)
