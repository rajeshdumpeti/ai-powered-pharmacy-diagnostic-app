# pages/billing_invoice_page.py
import streamlit as st
from services.database_service import execute_sql_query
import sqlite3
import os
from fpdf import FPDF
from datetime import datetime
from io import BytesIO
import json

# --- Configuration ---
GST_RATE = 0.18
DATABASE_FILE = os.path.join("data", "pharmacy_db.db")
FONT_PATH = os.path.join(os.path.dirname(__file__), "..", "fonts", "DejaVuSans.ttf")

# --- Helper Functions ---
def format_currency(amount):
    """Formats a float as a currency string with Rupee symbol."""
    return f"₹{amount:,.2f}"

# --- Database Functions ---
def get_all_drugs():
    rows, _ = execute_sql_query("SELECT DRUG_ID, DRUG_NAME, PRICE_PER_PACK FROM PHARMACY_INVENTORY ORDER BY DRUG_NAME;")
    return rows or []

def get_next_invoice_id_and_prepare_db(customer_name, payment_method, invoice_items_json, subtotal, gst_amount, grand_total):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS INVOICES (
            invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_date TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            invoice_items_json TEXT NOT NULL,
            subtotal REAL NOT NULL,
            gst_amount REAL NOT NULL,
            grand_total REAL NOT NULL
        )
    """)
    invoice_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO INVOICES (invoice_date, customer_name, payment_method, invoice_items_json, subtotal, gst_amount, grand_total)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (invoice_date, customer_name, payment_method, invoice_items_json, subtotal, gst_amount, grand_total))
    conn.commit()
    invoice_id = cursor.lastrowid
    conn.close()
    return invoice_id

# --- PDF Generation Function ---
def create_invoice_pdf(invoice_id, customer_name, payment_method, items, subtotal, gst, grand_total):
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    pdf = FPDF()
    try:
        if not os.path.exists(FONT_PATH):
            st.error(f"Font file not found at: {FONT_PATH}. Please ensure DejaVuSans.ttf is in your 'fonts' folder.")
            return None
        pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
        pdf.set_font("DejaVu", size=12)
    except Exception as e:
        st.error(f"Error loading font for PDF: {e}. Falling back to default font (may not support all characters).")
        pdf.set_font("Arial", size=12)

    pdf.add_page()

    pdf.set_font("DejaVu", '', 16)
    pdf.cell(0, 10, "Pharmacy GST Invoice", ln=True, align="C")
    pdf.set_font("DejaVu", '', 10)
    pdf.cell(0, 7, f"Invoice ID: {invoice_id}  Date: {date_str}", ln=True, align="C")
    pdf.ln(8)

    pdf.set_font("DejaVu", '', 12)
    pdf.cell(0, 8, "Customer Details:", ln=True)
    pdf.set_font("DejaVu", '', 12)
    pdf.cell(0, 7, f"Name: {customer_name}", ln=True)
    pdf.cell(0, 7, f"Payment Method: {payment_method}", ln=True)
    pdf.ln(8)

    pdf.set_font("DejaVu", '', 12)
    pdf.cell(80, 10, "Drug Name", 1, 0, 'C')
    pdf.cell(30, 10, "Qty", 1, 0, 'C')
    pdf.cell(40, 10, "Price/Unit", 1, 0, 'C')
    pdf.cell(40, 10, "Total", 1, 1, 'C')

    pdf.set_font("DejaVu", '', 10)
    for item in items:
        item_total = item['quantity'] * item['price_per_pack']
        pdf.cell(80, 10, item['drug_name'], 1, 0, 'L')
        pdf.cell(30, 10, str(item['quantity']), 1, 0, 'C')
        pdf.cell(40, 10, format_currency(item['price_per_pack']), 1, 0, 'R')
        pdf.cell(40, 10, format_currency(item_total), 1, 1, 'R')
    pdf.ln(5)

    pdf.set_font("DejaVu", '', 12)
    pdf.cell(150, 7, "Subtotal:", 0, 0, 'R')
    pdf.cell(40, 7, format_currency(subtotal), 0, 1, 'R')
    pdf.cell(150, 7, f"GST ({int(GST_RATE*100)}%):", 0, 0, 'R')
    pdf.cell(40, 7, format_currency(gst), 0, 1, 'R')
    pdf.set_font("DejaVu", '', 14)
    pdf.cell(150, 10, "Grand Total:", 0, 0, 'R')
    pdf.cell(40, 10, format_currency(grand_total), 0, 1, 'R')
    pdf.ln(10)

    pdf.set_font("DejaVu", '', 10)
    pdf.cell(0, 5, "Thank you for your business!", ln=True, align="C")

    buffer = BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    buffer.write(pdf_bytes)
    buffer.seek(0)
    return buffer.getvalue()

# --- Streamlit Page Function ---
def show_billing_page():
    st.markdown("## 🧾 Pharmacy Billing & Checkout")
    st.markdown("Generate detailed invoices for drug sales, including GST and PDF download.")

    if 'current_invoice_items' not in st.session_state:
        st.session_state.current_invoice_items = []

    drug_options = get_all_drugs()
    drug_dict = {f"{name} ({format_currency(price_per_pack)})": {"drug_id": drug_id, "price_per_pack": price_per_pack, "drug_name": name}
                 for drug_id, name, price_per_pack in drug_options}

    if not drug_dict:
        st.warning("No drugs found in inventory. Please add drugs first to generate invoices.")
        return

    st.markdown("### Add Items to Invoice")
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_drug_display = st.selectbox("Select Drug", list(drug_dict.keys()), key="add_drug_select")
    with col2:
        quantity_to_add = st.number_input("Quantity", min_value=1, value=1, key="add_drug_qty")

    if st.button("➕ Add Item to Invoice", key="add_item_btn"):
        if selected_drug_display:
            selected_drug_info = drug_dict[selected_drug_display]
            item_to_add = {
                "drug_id": selected_drug_info["drug_id"],
                "drug_name": selected_drug_info["drug_name"],
                "quantity": quantity_to_add,
                "price_per_pack": selected_drug_info["price_per_pack"]
            }
            # Check if drug is already in the list, if so, update quantity
            found = False
            for item in st.session_state.current_invoice_items:
                if item["drug_id"] == item_to_add["drug_id"]:
                    item["quantity"] += item_to_add["quantity"]
                    found = True
                    break
            if not found:
                st.session_state.current_invoice_items.append(item_to_add)
            st.success(f"Added {quantity_to_add} x {selected_drug_info['drug_name']} to invoice.")
        else:
            st.warning("Please select a drug to add.")

    st.markdown("### Current Invoice Items")
    if st.session_state.current_invoice_items:
        items_df = []
        total_subtotal = 0
        for i, item in enumerate(st.session_state.current_invoice_items):
            item_line_total = item['quantity'] * item['price_per_pack']
            total_subtotal += item_line_total
            items_df.append({
                "Drug Name": item['drug_name'],
                "Quantity": item['quantity'],
                "Price/Unit": format_currency(item['price_per_pack']),
                "Line Total": format_currency(item_line_total)
            })
        st.dataframe(items_df, use_container_width=True, hide_index=True)

        # Remove item buttons (one per row)
        for i in range(len(st.session_state.current_invoice_items)):
            if st.button(f"🗑️ Remove {st.session_state.current_invoice_items[i]['drug_name']}", key=f"remove_item_{i}"):
                del st.session_state.current_invoice_items[i]
                st.rerun() # Rerun to update the displayed list immediately

        st.markdown(f"**Calculated Subtotal: {format_currency(total_subtotal)}**")
        calculated_gst = total_subtotal * GST_RATE
        st.markdown(f"**Calculated GST ({int(GST_RATE*100)}%): {format_currency(calculated_gst)}**")
        calculated_grand_total = total_subtotal + calculated_gst
        st.markdown(f"**Calculated Grand Total: {format_currency(calculated_grand_total)}**")

    else:
        st.info("No items added to the invoice yet.")

    st.markdown("---")
    st.markdown("### Finalize Invoice")

    with st.form("finalize_invoice_form"):
        customer_name_final = st.text_input("Customer Name for Invoice", value=st.session_state.get("invoice_patient_name", ""), key="final_customer_name")
        payment_method_final = st.radio("Payment Method", ["Cash", "Card", "UPI"], index=["Cash", "Card", "UPI"].index(st.session_state.get("invoice_payment_mode", "Cash")), key="final_payment_method")

        generate_invoice_button = st.form_submit_button("💰 Generate Final Invoice")

    if generate_invoice_button:
        if not st.session_state.current_invoice_items:
            st.warning("Please add items to the invoice before generating.")
        elif not customer_name_final:
            st.warning("Please enter customer name for the invoice.")
        else:
            final_subtotal = sum(item['quantity'] * item['price_per_pack'] for item in st.session_state.current_invoice_items)
            final_gst = final_subtotal * GST_RATE
            final_grand_total = final_subtotal + final_gst

            invoice_items_json_str = json.dumps(st.session_state.current_invoice_items)

            invoice_id = get_next_invoice_id_and_prepare_db(
                customer_name_final, payment_method_final, invoice_items_json_str,
                final_subtotal, final_gst, final_grand_total
            )

            if invoice_id is None:
                st.error("Could not generate invoice ID or save invoice to database.")
                # No rerun here, let user see error
                return

            pdf_data = create_invoice_pdf(
                invoice_id,
                customer_name_final,
                payment_method_final,
                st.session_state.current_invoice_items,
                final_subtotal,
                final_gst,
                final_grand_total
            )

            if pdf_data:
                st.success(f"✅ Invoice {invoice_id} generated successfully!")
                st.download_button(
                    label="📥 Download Invoice PDF",
                    data=pdf_data,
                    file_name=f"invoice_{invoice_id}.pdf",
                    mime="application/pdf"
                )

    # Optionally, provide a button to start a new invoice
            if st.button("Start New Invoice"):
                st.session_state.current_invoice_items = []
                st.session_state.invoice_patient_name = ""
                st.session_state.invoice_payment_mode = "Cash"
                st.rerun()
            else:
                st.error("Failed to generate PDF. Check font configuration or logs for details.")

    st.markdown("---")
    st.markdown("<p style='font-size: small; color: gray;'>Add multiple drugs using the 'Add Item' button, then finalize the invoice.</p>", unsafe_allow_html=True)