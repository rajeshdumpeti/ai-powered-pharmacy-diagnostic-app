import sqlite3
import bcrypt
import os

DATABASE_FILE = os.path.join('data', 'pharmacy_db.db')

def hash_password(password):
    """Hashes a password using bcrypt."""
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def verify_password(password, hashed_password):
    """Verifies a password against a hashed password."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def add_user(username, password):
    """Adds a new user to the database."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Check if username already exists
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return False # Username already exists

        hashed_password = hash_password(password)
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error during add_user: {e}")
        return False
    finally:
        if conn:
            conn.close()

def verify_user(username, password):
    """Verifies user credentials."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        if result:
            hashed_password = result[0]
            return verify_password(password, hashed_password)
        return False
    except sqlite3.Error as e:
        print(f"Database error during verify_user: {e}")
        return False
    finally:
        if conn:
            conn.close()