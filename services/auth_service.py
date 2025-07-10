import sqlite3
import bcrypt
import random
import time
import os

DATABASE_FILE = os.path.join('data', 'pharmacy_db.db')

# In-memory OTP store (for demo purposes only)
otp_store = {}

def generate_otp(length=6):
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])

def store_otp(username, otp):
    """Stores OTP temporarily for a user (in-memory store)."""
    otp_store[username] = {
        "otp": otp,
        "timestamp": time.time()
    }

def hash_password(password):
    """Hashes a password using bcrypt."""
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def verify_password(password, hashed_password):
    """Verifies a password against a hashed password."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def verify_otp(username, entered_otp, expiry_seconds=300):
    """Verifies OTP with expiry check (default: 5 minutes)."""
    data = otp_store.get(username)
    if not data:
        return False

    if time.time() - data["timestamp"] > expiry_seconds:
        del otp_store[username]
        return False

    if data["otp"] == entered_otp:
        del otp_store[username]
        return True

    return False

def add_user(username, password, role='Pharmacist'):
    """Adds a new user to the database with a specific role."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Check if username already exists
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            return False  # Username already exists

        hashed_password = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, hashed_password, role)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error during add_user: {e}")
        return False
    finally:
        if conn:
            conn.close()

def verify_user(username, password):
    """Verifies user credentials and stores role if valid."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT password, role FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        if result:
            hashed_password, role = result
            if verify_password(password, hashed_password):
                import streamlit as st
                st.session_state.user_role = role  # Store role in session
                return True
        return False
    except sqlite3.Error as e:
        print(f"Database error during verify_user: {e}")
        return False
    finally:
        if conn:
            conn.close()
            
def get_user_role(username):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE username = ?", (username,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Error fetching user role: {e}")
        return None
    finally:
        conn.close()