-- Mossie PostgreSQL Schema

-- Drop tables if they exist
DROP TABLE IF EXISTS users;

-- Create users table
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    password_salt VARCHAR(36) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Create index on username for faster lookups
CREATE INDEX idx_users_username ON users(username);

-- Initial admin user can be created using the application's registration feature
