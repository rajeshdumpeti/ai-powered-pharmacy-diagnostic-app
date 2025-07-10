from datetime import datetime

def generate_invoice(patient_name, items, payment_mode, gst_rate=0.18):
    """
    Generates a GST-compliant invoice.

    Args:
        patient_name (str): Name of the patient/customer.
        items (list of dict): List of items with keys: name, quantity, price_per_unit.
        payment_mode (str): Payment method - 'Cash', 'Card', or 'UPI'.
        gst_rate (float): GST rate to apply. Default is 18%.

    Returns:
        dict: Invoice details including GST breakdown and total.
    """
    invoice = {
        "invoice_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "patient_name": patient_name,
        "items": [],
        "payment_mode": payment_mode,
        "subtotal": 0,
        "gst_amount": 0,
        "total_amount": 0,
    }

    for item in items:
        item_total = item["quantity"] * item["price_per_unit"]
        invoice["items"].append({
            "name": item["name"],
            "quantity": item["quantity"],
            "price_per_unit": item["price_per_unit"],
            "total": item_total
        })
        invoice["subtotal"] += item_total

    invoice["gst_amount"] = round(invoice["subtotal"] * gst_rate, 2)
    invoice["total_amount"] = round(invoice["subtotal"] + invoice["gst_amount"], 2)

    return invoice
