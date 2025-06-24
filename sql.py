import sqlite3
import random
from datetime import date, timedelta

# Connect to the SQLite database.
connection = sqlite3.connect("student.db")
cursor = connection.cursor()

# --- OPTIONAL: Drop all existing tables for a clean start ---
cursor.execute("DROP TABLE IF EXISTS PHARMACY_INVENTORY")
cursor.execute("DROP TABLE IF EXISTS DIAGNOSTIC_DATA") # New table to drop
cursor.execute("DROP TABLE IF EXISTS STUDENT") # In case it was still there

# --- Create the PHARMACY_INVENTORY table ---
table_info_pharmacy = """
CREATE TABLE IF NOT EXISTS PHARMACY_INVENTORY(
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
)
"""
cursor.execute(table_info_pharmacy)

# --- Generate 100 Pharmacy Records ---
pharmacy_data = []
common_drugs = [
    ("Atorvastatin", "Lipitor", "Tablet", "20mg"), ("Metformin", "Glucophage", "Tablet", "500mg"),
    ("Lisinopril", "Prinivil", "Tablet", "10mg"), ("Levothyroxine", "Synthroid", "Tablet", "75mcg"),
    ("Amlodipine", "Norvasc", "Tablet", "5mg"), ("Metoprolol", "Lopressor", "Tablet", "50mg"),
    ("Albuterol", "Ventolin", "Inhaler", "90mcg/puff"), ("Losartan", "Cozaar", "Tablet", "25mg"),
    ("Omeprazole", "Prilosec", "Capsule", "20mg"), ("Gabapentin", "Neurontin", "Capsule", "300mg"),
    ("Sertraline", "Zoloft", "Tablet", "50mg"), ("Hydrochlorothiazide", "Microzide", "Tablet", "25mg"),
    ("Rosuvastatin", "Crestor", "Tablet", "10mg"), ("Amoxicillin", "Amoxil", "Capsule", "250mg"),
    ("Ibuprofen", "Advil", "Tablet", "200mg"), ("Acetaminophen", "Tylenol", "Tablet", "500mg"),
    ("Prednisone", "Deltasone", "Tablet", "10mg"), ("Ciprofloxacin", "Cipro", "Tablet", "250mg"),
    ("Azithromycin", "Zithromax", "Tablet", "250mg"), ("Doxycycline", "Vibramycin", "Capsule", "100mg"),
    ("Naproxen", "Aleve", "Tablet", "220mg"), ("Tramadol", "Ultram", "Tablet", "50mg"),
    ("Pantoprazole", "Protonix", "Tablet", "40mg"), ("Furosemide", "Lasix", "Tablet", "20mg"),
    ("Warfarin", "Coumadin", "Tablet", "5mg"), ("Citalopram", "Celexa", "Tablet", "20mg"),
    ("Alprazolam", "Xanax", "Tablet", "0.5mg"), ("Clonazepam", "Klonopin", "Tablet", "1mg"),
    ("Montelukast", "Singulair", "Tablet", "10mg"), ("Fluoxetine", "Prozac", "Capsule", "20mg"),
    ("Meloxicam", "Mobic", "Tablet", "15mg"), ("Aspirin", "Bayer", "Tablet", "81mg"),
    ("Clopidogrel", "Plavix", "Tablet", "75mg"), ("Duloxetine", "Cymbalta", "Capsule", "30mg"),
    ("Escitalopram", "Lexapro", "Tablet", "10mg"), ("Tamsulosin", "Flomax", "Capsule", "0.4mg"),
    ("Trazodone", "Desyrel", "Tablet", "50mg"), ("Simvastatin", "Zocor", "Tablet", "20mg"),
    ("Gabapentin", "Neurontin", "Oral Solution", "250mg/5ml"), ("Amoxicillin", "Amoxil", "Suspension", "125mg/5ml"),
    ("Loratadine", "Claritin", "Tablet", "10mg"), ("Famotidine", "Pepcid", "Tablet", "20mg"),
    ("Ondansetron", "Zofran", "Tablet", "4mg"), ("Prednisolone", "Orapred", "Oral Solution", "15mg/5ml"),
    ("Ranitidine", "Zantac", "Tablet", "150mg"), ("Sertraline", "Zoloft", "Oral Solution", "20mg/ml"),
    ("Folic Acid", "Folic Acid", "Tablet", "1mg"), ("Vitamin D3", "Cholecalciferol", "Capsule", "1000IU"),
    ("Calcium Carbonate", "Tums", "Chewable Tablet", "500mg"), ("Magnesium Oxide", "Mag-Ox", "Tablet", "400mg"),
    ("Potassium Chloride", "K-Dur", "Tablet", "20mEq")
]
pack_sizes = ["30 tabs", "60 tabs", "90 tabs", "100 ml", "200 ml", "1 vial", "50 cap", "150 cap"]
suppliers = ["PharmaCorp", "MediSupply", "GlobalDrugs", "ApexPharma", "HealthBridge"]
today = date.today()

for i in range(1, 101):
    drug_info = random.choice(common_drugs)
    drug_name, generic_name_default, formulation, dosage = drug_info
    generic_name = None if random.random() < 0.2 else (drug_name if random.random() < 0.4 else generic_name_default)
    pack_size = random.choice(pack_sizes)
    price_per_pack = round(random.uniform(5.00, 200.00), 2)
    stock_quantity = random.randint(10, 500)
    expiry_date = today + timedelta(days=random.randint(30, 3 * 365))
    supplier = random.choice(suppliers)
    pharmacy_data.append((drug_name, generic_name, formulation, dosage, pack_size,
                          price_per_pack, stock_quantity, expiry_date.strftime('%Y-%m-%d'), supplier))

insert_query_pharmacy = """
INSERT INTO PHARMACY_INVENTORY (
    DRUG_NAME, GENERIC_NAME, FORMULATION, DOSAGE, PACK_SIZE,
    PRICE_PER_PACK, STOCK_QUANTITY, EXPIRY_DATE, SUPPLIER
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
cursor.executemany(insert_query_pharmacy, pharmacy_data)
connection.commit()

# --- Retrieve DRUG_IDs for linking to Diagnostic Data ---
cursor.execute("SELECT DRUG_ID FROM PHARMACY_INVENTORY")
existing_drug_ids = [row[0] for row in cursor.fetchall()]
# Add a None option for cases where no drug was prescribed or it's unknown
if not existing_drug_ids:
    existing_drug_ids = [1] # Fallback if no drugs were inserted
existing_drug_ids.append(None) # Option for no drug prescribed

# --- Create the DIAGNOSTIC_DATA table ---
table_info_diagnostic = """
CREATE TABLE IF NOT EXISTS DIAGNOSTIC_DATA(
    PATIENT_ID INTEGER PRIMARY KEY AUTOINCREMENT,
    PATIENT_NAME VARCHAR(50) NOT NULL,
    DIAGNOSIS VARCHAR(100),
    DIAGNOSIS_DATE DATE,
    TEST_RESULTS VARCHAR(200), -- Simple string for test results summary
    DRUG_ID_PRESCRIBED INTEGER, -- Foreign key to PHARMACY_INVENTORY
    FOREIGN KEY (DRUG_ID_PRESCRIBED) REFERENCES PHARMACY_INVENTORY(DRUG_ID)
)
"""
cursor.execute(table_info_diagnostic)

# --- Generate 200 Diagnostic Records ---
diagnostic_data = []
patient_names = ["Amit Sharma", "Priya Singh", "Rahul Kumar", "Anjali Patel", "Vikram Reddy",
                 "Deepa Gupta", "Rohan Mehta", "Shweta Joshi", "Arjun Desai", "Neha Verma"]
diagnoses = ["Hypertension", "Type 2 Diabetes", "Asthma", "Allergy", "Bacterial Infection",
             "Migraine", "Arthritis", "Depression", "Anxiety", "Common Cold"]
test_results_options = [
    "Blood pressure elevated", "HbA1c high", "Spirometry normal", "Allergy panel positive for pollen",
    "Culture positive for strep", "MRI clear", "X-ray shows joint inflammation", "Mood assessment stable",
    "Panic attack reported", "Negative for flu"
]

for i in range(1, 201): # Generate 200 records
    patient_name = random.choice(patient_names)
    diagnosis = random.choice(diagnoses)
    diagnosis_date = today - timedelta(days=random.randint(1, 3 * 365)) # Up to 3 years ago
    test_results = random.choice(test_results_options)
    drug_id_prescribed = random.choice(existing_drug_ids) # Link to an existing drug or None

    diagnostic_data.append((patient_name, diagnosis, diagnosis_date.strftime('%Y-%m-%d'),
                            test_results, drug_id_prescribed))

insert_query_diagnostic = """
INSERT INTO DIAGNOSTIC_DATA (
    PATIENT_NAME, DIAGNOSIS, DIAGNOSIS_DATE, TEST_RESULTS, DRUG_ID_PRESCRIBED
) VALUES (?, ?, ?, ?, ?)
"""
cursor.executemany(insert_query_diagnostic, diagnostic_data)
connection.commit()

print('Pharmacy records:')
data_pharmacy = cursor.execute('''SELECT * FROM PHARMACY_INVENTORY''')
for row in data_pharmacy:
    print(row)

print('\nDiagnostic records:')
data_diagnostic = cursor.execute('''SELECT * FROM DIAGNOSTIC_DATA''')
for row in data_diagnostic:
    print(row)

connection.close()

print("\nDatabase 'student.db' updated with PHARMACY_INVENTORY and DIAGNOSTIC_DATA tables.")