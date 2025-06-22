# Mossie Login System

A login system for the Mossie mental health application, featuring secure user authentication with PostgreSQL.

## Features

- User authentication with salted passwords
- PostgreSQL database integration
- UUID-based user identification 
- Login timestamp tracking
- Modern, responsive UI
- CLI tools for database management

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)

## Setup Instructions

### 1. Install PostgreSQL

If you don't have PostgreSQL installed, follow the installation instructions for your operating system:
- macOS: `brew install postgresql`
- Linux: `sudo apt-get install postgresql`
- Windows: Download from the [official PostgreSQL website](https://www.postgresql.org/download/windows/)

### 2. Create the Database

```bash
# Log in to PostgreSQL as postgres user
psql -U postgres

# Create the database
CREATE DATABASE mossie;

# Exit PostgreSQL
\q
```

### 3. Install Python Dependencies

```bash
cd /Users/calebchoi/Desktop/mossie_497/temp
pip install -r requirements.txt
```

### 4. Initialize the Database

Option 1: Using the schema file
```bash
python app.py init-db-schema schema.sql
```

Option 2: Using the built-in initialization
```bash
python app.py init-db
```

### 5. Create a User

```bash
python app.py create-user username yourpassword
```

### 6. Run the Application

```bash
python app.py
```

The application will be available at http://127.0.0.1:5000

## Environment Variables

You can customize the application settings using the following environment variables:

- `SECRET_KEY`: Flask secret key for session encryption (default: 'dev_key_only_for_development')
- `DATABASE_URL`: PostgreSQL connection string (default: 'postgresql://postgres:postgres@localhost:5432/mossie')

## Database Schema

The users table contains the following fields:
- `user_id`: UUID primary key
- `username`: Unique username (VARCHAR)
- `password_hash`: SHA-256 hash of password with salt (VARCHAR) 
- `password_salt`: Unique salt for password hashing (VARCHAR)
- `created_at`: Account creation timestamp
- `last_login`: Last login timestamp
