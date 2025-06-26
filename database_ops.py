# database_ops.py
import sqlite3
import random
from datetime import date, timedelta
import streamlit as st
import bcrypt # Import bcrypt for password hashing

DATABASE_FILE = 'student.db'

def init_db():
    """Initializes the SQLite database with PHARMACY_INVENTORY, DIAGNOSTIC_DATA,
    and USERS tables. Populates them with sample data if tables are empty.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Create PHARMACY_INVENTORY table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PHARMACY_INVENTORY (
            DRUG_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            DRUG_NAME VARCHAR(50) NOT NULL,
            GENERIC_NAME VARCHAR(50),
            FORMULATION VARCHAR(20),
            DOSAGE VARCHAR(20),
            PACK_SIZE VARCHAR(20),
            PRICE_PER_PACK REAL,
            STOCK_QUANTITY INT,
            EXPIRY_DATE DATE,
            SUPPLIER VARCHAR(50)
        );
    """)

    # Create DIAGNOSTIC_DATA table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS DIAGNOSTIC_DATA (
            PATIENT_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            PATIENT_NAME VARCHAR(50) NOT NULL,
            DIAGNOSIS VARCHAR(100),
            DIAGNOSIS_DATE DATE,
            TEST_RESULTS VARCHAR(200),
            DRUG_ID_PRESCRIBED INTEGER,
            FOREIGN KEY (DRUG_ID_PRESCRIBED) REFERENCES PHARMACY_INVENTORY(DRUG_ID)
        );
    """)

    # Create USERS table for authentication
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS USERS (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            USERNAME TEXT UNIQUE NOT NULL,
            PASSWORD_HASH TEXT NOT NULL
        );
    """)
    conn.commit() # Commit table creation

    # --- Insert sample data into PHARMACY_INVENTORY if it's empty ---
    cursor.execute("SELECT COUNT(*) FROM PHARMACY_INVENTORY;")
    if cursor.fetchone()[0] == 0:
        print("Inserting sample data into PHARMACY_INVENTORY...")
        pharmacy_data_for_init = [
            ('Lipitor', 'Atorvastatin', 'Tablet', '20mg', '30 tabs', 12.50, 150, '2026-12-31', 'PharmaCorp'),
            ('Amoxil', 'Amoxicillin', 'Capsule', '250mg', '20 caps', 8.75, 200, '2025-11-15', 'MediSupply'),
            ('Zestril', 'Lisinopril', 'Tablet', '10mg', '90 tabs', 25.00, 80, '2027-01-20', 'PharmaCorp'),
            ('Ibuprofen', 'Ibuprofen', 'Tablet', '200mg', '100 tabs', 5.20, 300, '2025-09-01', 'GenericLabs'),
            ('Metformin', 'Metformin', 'Tablet', '500mg', '60 tabs', 15.00, 120, '2026-06-30', 'MediSupply'),
            ('Prozac', 'Fluoxetine', 'Capsule', '20mg', '30 caps', 45.00, 75, '2027-03-10', 'PharmaCorp'),
            ('Ventolin', 'Albuterol', 'Inhaler', '90mcg/puff', '1 inhaler', 60.00, 50, '2025-10-05', 'RespiraCare'),
            ('Nexium', 'Esomeprazole', 'Capsule', '40mg', '30 caps', 30.25, 90, '2026-08-22', 'GastricHealth'),
            ('Synthroid', 'Levothyroxine', 'Tablet', '75mcg', '90 tabs', 20.00, 110, '2027-04-18', 'ThyroCorp'),
            ('Plavix', 'Clopidogrel', 'Tablet', '75mg', '30 tabs', 55.00, 60, '2025-12-01', 'CardioMed')
        ]
        cursor.executemany("""
            INSERT INTO PHARMACY_INVENTORY (DRUG_NAME, GENERIC_NAME, FORMULATION, DOSAGE, PACK_SIZE, PRICE_PER_PACK, STOCK_QUANTITY, EXPIRY_DATE, SUPPLIER)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, pharmacy_data_for_init)
        conn.commit()
        print("PHARMACY_INVENTORY data inserted.")

    # --- Insert sample data into DIAGNOSTIC_DATA if it's empty ---
    cursor.execute("SELECT COUNT(*) FROM DIAGNOSTIC_DATA;")
    if cursor.fetchone()[0] == 0:
        print("Inserting sample data into DIAGNOSTIC_DATA...")
        
        drug_id_map = {}
        cursor.execute("SELECT DRUG_NAME, DRUG_ID FROM PHARMACY_INVENTORY;")
        for drug_name, drug_id in cursor.fetchall():
            drug_id_map[drug_name] = drug_id

        patient_names = ["Amit Sharma", "Priya Singh", "Rahul Kumar", "Anjali Patel", "Vikram Reddy",
                         "Deepa Gupta", "Rohan Mehta", "Shweta Joshi", "Arjun Desai", "Neha Verma",
                         "Suresh Rao", "Meena Sharma", "Karan Singh", "Divya Reddy", "Rajesh Kumar",
                         "Smita Patel", "Gaurav Gupta", "Pooja Mehta", "Sanjay Joshi", "Rina Verma"]
        diagnoses = ["Hypertension", "Type 2 Diabetes", "Asthma", "Allergy", "Bacterial Infection",
                     "Migraine", "Arthritis", "Depression", "Anxiety", "Common Cold", "Thyroid Imbalance", "Pneumonia"]
        test_results_options = [
            "Blood pressure elevated", "HbA1c high", "Spirometry normal", "Allergy panel positive for pollen",
            "Culture positive for strep", "MRI clear", "X-ray shows joint inflammation", "Mood assessment stable",
            "Panic attack reported", "Negative for flu", "Thyroid levels abnormal", "Chest X-ray shows consolidation"
        ]
        today = date.today()

        diagnostic_data_for_init = []
        for _ in range(200):
            patient_name = random.choice(patient_names)
            diagnosis = random.choice(diagnoses)
            diagnosis_date = today - timedelta(days=random.randint(1, 3 * 365))
            test_results = random.choice(test_results_options)
            
            available_drug_ids = list(drug_id_map.values())
            drug_id_prescribed = random.choice(available_drug_ids + [None]) if available_drug_ids else None

            diagnostic_data_for_init.append((patient_name, diagnosis, diagnosis_date.strftime('%Y-%m-%d'),
                                            test_results, drug_id_prescribed))

        insert_query_diagnostic = """
            INSERT INTO DIAGNOSTIC_DATA (PATIENT_NAME, DIAGNOSIS, DIAGNOSIS_DATE, TEST_RESULTS, DRUG_ID_PRESCRIBED)
            VALUES (?, ?, ?, ?, ?);
        """
        cursor.executemany(insert_query_diagnostic, diagnostic_data_for_init)
        conn.commit()
        print("DIAGNOSTIC_DATA data inserted.")

    conn.close()

def execute_sql_query(sql_query):
    """Executes an SQL query against the database.
    Returns (rows, columns) for SELECT queries, or (status_message, None) for UPDATE/INSERT/DELETE.
    Handles database errors and displays them in Streamlit.
    """
    conn = None
    rows = []
    columns = []
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cur = conn.cursor()
        cur.execute(sql_query)
        
        if sql_query.strip().upper().startswith("SELECT"):
            columns = [description[0] for description in cur.description] if cur.description else []
            rows = cur.fetchall()
            return rows, columns
        else:
            conn.commit()
            return "Operation successful: Database updated.", None
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        st.code(sql_query, language="sql")
        return None, None
    finally:
        if conn:
            conn.close()

def add_user(username, password):
    """Adds a new user to the USERS table with a hashed password.
    Returns True on success, False if username exists or error.
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute("INSERT INTO USERS (USERNAME, PASSWORD_HASH) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        st.error("Username already exists. Please choose a different username.")
        return False
    except sqlite3.Error as e:
        st.error(f"Database error during signup: {e}")
        return False
    finally:
        if conn:
            conn.close()

def verify_user(username, password):
    """Verifies user credentials.
    Returns True if username and password match, False otherwise.
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT PASSWORD_HASH FROM USERS WHERE USERNAME = ?", (username,))
        result = cursor.fetchone()
        if result:
            stored_password_hash = result[0]
            # Check the provided password against the stored hash
            if bcrypt.checkpw(password.encode('utf-8'), stored_password_hash.encode('utf-8')):
                return True
        return False
    except sqlite3.Error as e:
        st.error(f"Database error during login: {e}")
        return False
    finally:
        if conn:
            conn.close()