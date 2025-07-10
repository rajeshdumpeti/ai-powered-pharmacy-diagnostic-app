import streamlit as st
from datetime import datetime

def show_billing_page():
    st.markdown("## 🧾 Billing & GST Invoice Generator")

    with st.form("invoice_form"):
        patient_name = st.text_input("Patient Name")
        payment_mode = st.selectbox("Payment Mode", ["Cash", "Card", "UPI"])

        st.markdown("### Add Items")
        item_name = st.text_input("Item Name")
        quantity = st.number_input("Quantity", min_value=1, step=1)
        price_per_unit = st.number_input("Price per Unit (₹)", min_value=0.0, format="%.2f")

        add_item = st.form_submit_button("Add Item")
        if add_item and item_name and quantity > 0 and price_per_unit > 0:
            if "invoice_items" not in st.session_state:
                st.session_state.invoice_items = []
            st.session_state.invoice_items.append({
                "name": item_name,
                "quantity": quantity,
                "price_per_unit": price_per_unit
            })
            st.rerun()

    if "invoice_items" in st.session_state and st.session_state.invoice_items:
        st.markdown("### 🧾 Items in Invoice")
        for item in st.session_state.invoice_items:
            st.write(f"- {item['name']} ({item['quantity']} x ₹{item['price_per_unit']})")

        subtotal = sum(item["quantity"] * item["price_per_unit"] for item in st.session_state.invoice_items)
        gst_amount = round(subtotal * 0.18, 2)
        total_amount = round(subtotal + gst_amount, 2)

        st.markdown("---")
        st.write(f"**Subtotal:** ₹{subtotal:.2f}")
        st.write(f"**GST (18%):** ₹{gst_amount:.2f}")
        st.write(f"**Total Amount:** ₹{total_amount:.2f}")
        st.write(f"**Payment Mode:** `{payment_mode}`")
        st.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if st.button("✅ Generate Invoice"):
            st.success("Invoice generated successfully!")

        if st.button("🗑️ Clear Invoice"):
            del st.session_state.invoice_items
            st.rerun()
