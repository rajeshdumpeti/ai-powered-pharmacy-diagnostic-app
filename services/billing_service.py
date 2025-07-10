import os
import sqlite3
from datetime import datetime
from fpdf import FPDF

INVOICE_DB = "data/invoice_records.db"
INVOICE_DIR = "data"

# Make sure directory exists
os.makedirs(INVOICE_DIR, exist_ok=True)

def init_invoice_db():
    """Creates the invoice database and table if not exists."""
    conn = sqlite3.connect(INVOICE_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            drug_name TEXT,
            quantity INTEGER,
            price_per_pack REAL,
            gst_amount REAL,
            total_amount REAL,
            payment_mode TEXT,
            timestamp TEXT
        );
    """)
    conn.commit()
    conn.close()


def generate_invoice(customer_name, drug_name, quantity, price_per_pack, payment_mode):
    """Calculates total with GST, stores record, and creates a PDF invoice."""

    # Calculate GST and total
    subtotal = quantity * price_per_pack
    gst_amount = round(subtotal * 0.18, 2)  # 18% GST
    total_amount = round(subtotal + gst_amount, 2)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save to DB
    conn = sqlite3.connect(INVOICE_DB)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO invoices (customer_name, drug_name, quantity, price_per_pack, gst_amount, total_amount, payment_mode, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (customer_name, drug_name, quantity, price_per_pack, gst_amount, total_amount, payment_mode, timestamp))
    invoice_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Generate PDF
    file_path = os.path.join(INVOICE_DIR, f"invoice_{invoice_id}.pdf")
    create_invoice_pdf(invoice_id, customer_name, drug_name, quantity, price_per_pack, gst_amount, total_amount, payment_mode, timestamp, file_path)

    return file_path, invoice_id


def create_invoice_pdf(invoice_id, customer_name, drug_name, quantity, price_per_pack, gst_amount, total_amount, payment_mode, timestamp, file_path):
    """Creates a simple GST invoice PDF."""
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Pharmacy Billing Invoice", ln=1, align='C')
    pdf.cell(200, 10, txt=f"Invoice ID: {invoice_id}", ln=2, align='R')
    pdf.cell(200, 10, txt=f"Date: {timestamp}", ln=3, align='R')
    pdf.ln(10)

    pdf.cell(100, 10, txt=f"Customer Name: {customer_name}", ln=True)
    pdf.cell(100, 10, txt=f"Payment Mode: {payment_mode}", ln=True)
    pdf.ln(10)

    # Table
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 10, txt="Drug", border=1)
    pdf.cell(30, 10, txt="Qty", border=1)
    pdf.cell(40, 10, txt="Price/Pack", border=1)
    pdf.cell(40, 10, txt="GST", border=1)
    pdf.cell(30, 10, txt="Total", border=1, ln=True)

    pdf.set_font("Arial", size=12)
    pdf.cell(50, 10, txt=drug_name, border=1)
    pdf.cell(30, 10, txt=str(quantity), border=1)
    pdf.cell(40, 10, txt=f"₹{price_per_pack}", border=1)
    pdf.cell(40, 10, txt=f"₹{gst_amount}", border=1)
    pdf.cell(30, 10, txt=f"₹{total_amount}", border=1, ln=True)

    pdf.output(file_path)
