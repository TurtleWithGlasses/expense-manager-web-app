"""
Script to update avatar_url column from VARCHAR(500) to TEXT
Run this after deployment to fix avatar storage
"""
from sqlalchemy import create_engine, text
from app.core.config import settings

def update_avatar_column():
    """Update avatar_url column to TEXT type for PostgreSQL and SQLite"""
    try:
        engine = create_engine(settings.DATABASE_URL)

        with engine.connect() as conn:
            # Check if we're using PostgreSQL or SQLite
            dialect_name = engine.dialect.name

            if dialect_name == 'postgresql':
                # PostgreSQL syntax
                print("Detected PostgreSQL database")
                conn.execute(text("""
                    ALTER TABLE users
                    ALTER COLUMN avatar_url TYPE TEXT;
                """))
                conn.commit()
                print("[OK] Successfully updated avatar_url column to TEXT (PostgreSQL)")

            elif dialect_name == 'sqlite':
                # SQLite requires table recreation
                print("Detected SQLite database")

                # Check if users_new already exists and drop it
                try:
                    conn.execute(text("DROP TABLE IF EXISTS users_new"))
                    conn.commit()
                except:
                    pass

                # Create new table with TEXT column
                conn.execute(text("""
                    CREATE TABLE users_new (
                        id INTEGER PRIMARY KEY,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        hashed_password VARCHAR(255) NOT NULL,
                        full_name VARCHAR(255),
                        avatar_url TEXT,
                        is_verified BOOLEAN DEFAULT 0,
                        verification_token VARCHAR(255),
                        verification_token_expires DATETIME,
                        password_reset_token VARCHAR(255),
                        password_reset_expires DATETIME,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                conn.commit()

                # Copy data
                conn.execute(text("""
                    INSERT INTO users_new
                    SELECT * FROM users;
                """))
                conn.commit()

                # Drop old table
                conn.execute(text("DROP TABLE users;"))
                conn.commit()

                # Rename new table
                conn.execute(text("ALTER TABLE users_new RENAME TO users;"))
                conn.commit()

                # Recreate indexes
                conn.execute(text("CREATE UNIQUE INDEX ix_users_email ON users (email);"))
                conn.execute(text("CREATE INDEX ix_users_id ON users (id);"))
                conn.commit()

                print("[OK] Successfully updated avatar_url column to TEXT (SQLite)")

            else:
                print(f"Unsupported database type: {dialect_name}")
                return False

        return True

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    success = update_avatar_column()
    sys.exit(0 if success else 1)
