# services/database_service.py
import sqlite3
import os

DATABASE_FILE = os.path.join('data', 'pharmacy_db.db')

def init_db():
    """Initializes the SQLite database, creates tables, and inserts sample data if they don't exist."""
    os.makedirs('data', exist_ok=True) # Ensure data directory exists
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Create users table
     # Create users table with role support
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        );
    """)

    # Create PHARMACY_INVENTORY table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS PHARMACY_INVENTORY (
            DRUG_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            DRUG_NAME VARCHAR(255) NOT NULL,
            GENERIC_NAME VARCHAR(255),
            FORMULATION VARCHAR(100),
            DOSAGE VARCHAR(100),
            PACK_SIZE VARCHAR(100),
            PRICE_PER_PACK REAL,
            STOCK_QUANTITY INT,
            EXPIRY_DATE DATE,
            SUPPLIER VARCHAR(255)
        );
    """)

    # Create DIAGNOSTIC_DATA table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS DIAGNOSTIC_DATA (
            PATIENT_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            PATIENT_NAME VARCHAR(255) NOT NULL,
            DIAGNOSIS VARCHAR(255),
            DIAGNOSIS_DATE DATE,
            TEST_RESULTS TEXT,
            DRUG_ID_PRESCRIBED INTEGER,
            FOREIGN KEY (DRUG_ID_PRESCRIBED) REFERENCES PHARMACY_INVENTORY(DRUG_ID)
        );
    """)

    # Insert sample data into PHARMACY_INVENTORY if table is empty
    cursor.execute("SELECT COUNT(*) FROM PHARMACY_INVENTORY;")
    if cursor.fetchone()[0] == 0:
        sample_drugs = [
            ('Lipitor', 'Atorvastatin', 'Tablet', '20mg', '30 tabs', 15.75, 120, '2025-12-31', 'PharmaCorp'),
            ('Amoxil', 'Amoxicillin', 'Capsule', '250mg', '20 caps', 8.20, 200, '2026-06-15', 'MediSupply'),
            ('Ventolin', 'Salbutamol', 'Inhaler', '100mcg/puff', '1 inhaler', 25.00, 80, '2025-10-01', 'RespiraLabs'),
            ('Metformin', 'Metformin', 'Tablet', '500mg', '60 tabs', 5.50, 50, '2026-03-20', 'GenericMeds'),
            ('Zoloft', 'Sertraline', 'Tablet', '50mg', '30 tabs', 30.00, 30, '2025-09-01', 'NeuroPharma'),
            ('Ibuprofen', 'Ibuprofen', 'Tablet', '200mg', '50 tabs', 3.00, 150, '2027-01-01', 'GenericMeds')
        ]
        cursor.executemany("""
            INSERT INTO PHARMACY_INVENTORY (DRUG_NAME, GENERIC_NAME, FORMULATION, DOSAGE, PACK_SIZE, PRICE_PER_PACK, STOCK_QUANTITY, EXPIRY_DATE, SUPPLIER)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, sample_drugs)
        conn.commit()

    # Insert sample data into DIAGNOSTIC_DATA if table is empty
    cursor.execute("SELECT COUNT(*) FROM DIAGNOSTIC_DATA;")
    if cursor.fetchone()[0] == 0:
        sample_diagnoses = [
            ('Alice Smith', 'Hypertension', '2023-01-10', 'BP consistently high', 1), # Lipitor
            ('Bob Johnson', 'Asthma', '2023-03-22', 'Wheezing, shortness of breath', 3), # Ventolin
            ('Charlie Brown', 'Diabetes Type 2', '2023-05-01', 'High blood sugar levels', 4), # Metformin
            ('Diana Prince', 'Anxiety Disorder', '2023-07-15', 'Persistent worry, panic attacks', 5), # Zoloft
            ('Eve Adams', 'Common Cold', '2024-01-05', 'Runny nose, sore throat', 6), # Ibuprofen
            ('Frank White', 'Hypertension', '2024-02-20', 'Follow-up, BP stable', 1), # Lipitor
            ('Grace Lee', 'Diabetes Type 2', '2024-03-10', 'HbA1c elevated', 4), # Metformin
            ('Henry King', 'Migraine', '2024-04-01', 'Severe headache, light sensitivity', None) # No drug prescribed
        ]
        cursor.executemany("""
            INSERT INTO DIAGNOSTIC_DATA (PATIENT_NAME, DIAGNOSIS, DIAGNOSIS_DATE, TEST_RESULTS, DRUG_ID_PRESCRIBED)
            VALUES (?, ?, ?, ?, ?);
        """, sample_diagnoses)
        conn.commit()

    conn.close()

def execute_sql_query(query):
    """Executes a given SQL query and returns results or status."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # For DML statements (INSERT, UPDATE, DELETE)
        if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
            cursor.execute(query)
            conn.commit()
            return f"Query executed successfully. Rows affected: {cursor.rowcount}", None
        # For DDL statements (CREATE, DROP, ALTER) - though LLM should not generate these
        elif query.strip().upper().startswith(("CREATE", "DROP", "ALTER")):
            cursor.execute(query)
            conn.commit()
            return "DDL query executed successfully.", None
        # For SELECT statements
        else:
            cursor.execute(query)
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return rows, columns
    except sqlite3.Error as e:
        return f"Database Error: {e}", None
    except Exception as e:
        return f"An unexpected error occurred: {e}", None
    finally:
        if conn:
            conn.close()

def get_all_drugs_for_select():
    """Fetches all drug IDs and names for select boxes."""
    query = "SELECT DRUG_ID, DRUG_NAME FROM PHARMACY_INVENTORY ORDER BY DRUG_NAME ASC;"
    return execute_sql_query(query)

def fetch_all_drug_names():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT DRUG_NAME FROM PHARMACY_INVENTORY ORDER BY DRUG_NAME ASC")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]