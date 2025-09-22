-- Fix production database schema by adding missing email verification columns
-- This script can be run directly in production to add the missing columns

-- Add is_verified column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'is_verified') THEN
        ALTER TABLE users ADD COLUMN is_verified BOOLEAN NOT NULL DEFAULT false;
        RAISE NOTICE 'Added is_verified column';
    ELSE
        RAISE NOTICE 'is_verified column already exists';
    END IF;
END $$;

-- Add verification_token column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'verification_token') THEN
        ALTER TABLE users ADD COLUMN verification_token VARCHAR(255);
        RAISE NOTICE 'Added verification_token column';
    ELSE
        RAISE NOTICE 'verification_token column already exists';
    END IF;
END $$;

-- Add verification_token_expires column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'verification_token_expires') THEN
        ALTER TABLE users ADD COLUMN verification_token_expires TIMESTAMP;
        RAISE NOTICE 'Added verification_token_expires column';
    ELSE
        RAISE NOTICE 'verification_token_expires column already exists';
    END IF;
END $$;

-- Add password_reset_token column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'password_reset_token') THEN
        ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(255);
        RAISE NOTICE 'Added password_reset_token column';
    ELSE
        RAISE NOTICE 'password_reset_token column already exists';
    END IF;
END $$;

-- Add password_reset_expires column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'password_reset_expires') THEN
        ALTER TABLE users ADD COLUMN password_reset_expires TIMESTAMP;
        RAISE NOTICE 'Added password_reset_expires column';
    ELSE
        RAISE NOTICE 'password_reset_expires column already exists';
    END IF;
END $$;

-- Add created_at column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'created_at') THEN
        ALTER TABLE users ADD COLUMN created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;
        RAISE NOTICE 'Added created_at column';
    ELSE
        RAISE NOTICE 'created_at column already exists';
    END IF;
END $$;

-- Show final table structure
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position;
