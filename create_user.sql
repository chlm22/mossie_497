-- Create a test user for Mossie
-- Username: admin
-- Password: password123 (with salt '550e8400-e29b-41d4-a716-446655440000')
-- Password hash is SHA-256 of 'password123550e8400-e29b-41d4-a716-446655440000'

INSERT INTO users (user_id, username, password_hash, password_salt, created_at)
VALUES (
    '123e4567-e89b-12d3-a456-426614174000', -- user_id (UUID)
    'admin', -- username
    '607701e119dc3aa16ad0593b8ede507103a33ec67d7700456fb1a1c5963dec87', -- password_hash (SHA-256)
    '550e8400-e29b-41d4-a716-446655440000', -- password_salt
    CURRENT_TIMESTAMP -- created_at
);
