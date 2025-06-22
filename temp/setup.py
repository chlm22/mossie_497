#!/usr/bin/env python3
"""
Mossie setup script to initialize the database and create an admin user.
"""

import os
import sys
import getpass
import argparse
import subprocess
import psycopg2
from psycopg2 import sql

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Setup Mossie application')
    parser.add_argument('--db-name', default='mossie', help='PostgreSQL database name')
    parser.add_argument('--db-user', default='postgres', help='PostgreSQL username')
    parser.add_argument('--db-password', help='PostgreSQL password')
    parser.add_argument('--db-host', default='localhost', help='PostgreSQL host')
    parser.add_argument('--db-port', default='5432', help='PostgreSQL port')
    parser.add_argument('--admin-user', help='Admin username for Mossie')
    parser.add_argument('--admin-password', help='Admin password for Mossie')
    parser.add_argument('--no-create-db', action='store_true', help='Skip database creation')
    return parser.parse_args()


def create_database(args):
    """Create the PostgreSQL database."""
    print(f"Creating database '{args.db_name}'...")
    
    # Connect to default database to create new database
    conn_string = f"host={args.db_host} port={args.db_port} user={args.db_user}"
    if args.db_password:
        conn_string += f" password={args.db_password}"
    
    try:
        # Connect to postgres database to create the new database
        conn = psycopg2.connect(conn_string + " dbname=postgres")
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database already exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s;",
            (args.db_name,)
        )
        
        if cursor.fetchone():
            print(f"Database '{args.db_name}' already exists.")
        else:
            # Create the database
            cursor.execute(sql.SQL("CREATE DATABASE {};").format(
                sql.Identifier(args.db_name)
            ))
            print(f"Database '{args.db_name}' created successfully!")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating database: {e}")
        return False
        
    return True


def setup_database(args):
    """Initialize the database schema."""
    print("Setting up database schema...")
    
    env = os.environ.copy()
    env["DATABASE_URL"] = f"postgresql://{args.db_user}:{args.db_password or ''}@{args.db_host}:{args.db_port}/{args.db_name}"
    
    try:
        # Run the database initialization command
        result = subprocess.run(
            ["python", "app.py", "init-db-schema", "schema.sql"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env=env,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error initializing database: {e}")
        print(e.stdout)
        print(e.stderr)
        return False


def create_admin(args):
    """Create admin user."""
    print("Creating admin user...")
    
    env = os.environ.copy()
    env["DATABASE_URL"] = f"postgresql://{args.db_user}:{args.db_password or ''}@{args.db_host}:{args.db_port}/{args.db_name}"
    
    try:
        # Run the create-user command
        result = subprocess.run(
            ["python", "app.py", "create-user", args.admin_user, args.admin_password],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env=env,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating admin user: {e}")
        print(e.stdout)
        print(e.stderr)
        return False


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Prompt for missing credentials
    if not args.db_password:
        args.db_password = getpass.getpass("PostgreSQL password: ")
    
    if not args.admin_user:
        args.admin_user = input("Admin username: ")
    
    if not args.admin_password:
        args.admin_password = getpass.getpass("Admin password: ")
    
    # Create database if needed
    if not args.no_create_db and not create_database(args):
        print("Failed to create database. Exiting.")
        return 1
    
    # Setup database schema
    if not setup_database(args):
        print("Failed to initialize database schema. Exiting.")
        return 1
    
    # Create admin user
    if not create_admin(args):
        print("Failed to create admin user. Exiting.")
        return 1
    
    print("\nSetup completed successfully!")
    print(f"You can now run the application with: python app.py")
    print(f"Login with username: {args.admin_user}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
