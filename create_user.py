#!/usr/bin/env python3
"""
Create a user for Mossie application.
"""
import os
import sys
import uuid
import hashlib
import psycopg2

def create_user(username, password):
    """Create a new user with the given username and password."""
    # Generate UUID for user_id
    user_id = str(uuid.uuid4())
    
    # Generate salt
    salt = str(uuid.uuid4())
    
    # Hash the password with the salt
    password_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    
    # Connect to the database
    try:
        conn = psycopg2.connect(
            dbname="mossie",
            host="localhost",
            user="postgres"  # Default PostgreSQL user
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Insert the user
        cursor.execute(
            "INSERT INTO users (user_id, username, password_hash, password_salt) "
            "VALUES (%s, %s, %s, %s)",
            (user_id, username, password_hash, salt)
        )
        
        print(f"User {username} created successfully!")
        
    except Exception as e:
        print(f"Error creating user: {e}")
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()
    
    return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_user.py <username> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    if create_user(username, password):
        sys.exit(0)
    else:
        sys.exit(1)
