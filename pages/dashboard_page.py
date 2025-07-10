# pages/dashboard_page.py
import streamlit as st

def show_dashboard_page():
    role = st.session_state.get("user_role", "Guest") 
    st.markdown("<h1 style='text-align: center; color: #4166d5;'>Rajesh's AI-APP</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center; color: #008080;'>Welcome to Your AI-Powered Assistant!</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>This application helps you efficiently manage pharmacy inventory and patient diagnostic data using the power of AI.</p>", unsafe_allow_html=True)
    st.markdown("---")

    st.subheader("What you can do with this app:")
    if role == "Pharmacist":
        st.markdown("""
        * **💊 Quick Drug Search:** Instantly find drug details by name.
        * **➕ Add New Drug:** Easily add new drugs to inventory.
        * **📊 Inventory Insights:** Receive AI-driven recommendations for stock management (low stock, expiring drugs).
        * **💬 Natural Language Query (Advanced):** Directly ask questions or issue commands (e.g., "sell 5 packs of Lipitor") in plain English to interact with the database.
        * **🤖 AI Chatbot:** Ask general questions about the database structure and what kind of data is stored.
        """)
    elif role == "Doctor":
        st.markdown("""
        * **🧑‍⚕️ Patient History Summarizer:** Get AI-generated summaries of patient health journeys.
        * **✍️ Custom Data Report:** Describe the report you need in natural language, and AI will generate it for you.
        * **💬 Natural Language Query (Advanced):** Directly ask questions or issue commands (e.g., "add a diagnostic record for John Doe") in plain English to interact with the database.
        * **🤖 AI Chatbot:** Ask general questions about the database structure and what kind of data is stored.
        * **🖼️ Medical Image Analysis:** Upload medical images and get AI-powered descriptions and insights.
        """)
    elif role == "Admin":
        st.markdown("""
        * **💊 Quick Drug Search:** Instantly find drug details by name.
        * **➕ Add Records:** Easily add new drugs to inventory or new diagnostic patient records.
        * **🗑️ Delete Records:** Remove specific records by ID.
        * **🧑‍⚕️ Patient History Summarizer:** Get AI-generated summaries of patient health journeys.
        * **📊 Inventory Insights:** Receive AI-driven recommendations for stock management (low stock, expiring drugs).
        * **✍️ Custom Data Report:** Describe the report you need in natural language, and AI will generate it for you.
        * **💬 Natural Language Query (Advanced):** Directly ask questions or issue commands (e.g., "sell 5 packs of Lipitor") in plain English to interact with the database.
        * **🤖 AI Chatbot:** Ask general questions about the database structure and what kind of data is stored.
        * **🖼️ Medical Image Analysis:** Upload medical images and get AI-powered descriptions and insights.
        """)
    else:
        st.markdown("""
        * **💊 You should be either pharmacist, doctor or Admin to use this app
        """)
    # st.markdown("---")

    # st.subheader("Quick Shortcuts:")
    # col1, col2, col3 = st.columns(3)        
    # print("Role:", role)  # Display the user's role
    # with col1:
    #     if st.button("Quick Drug Search", key="dashboard_shortcut_search"):
    #         st.session_state.current_page = "quick_drug_search"
    #         st.rerun()
    #     if st.button("Add New Drug", key="dashboard_shortcut_add_drug"):
    #         st.session_state.current_page = "add_drug"
    #         st.rerun()

    # with col2:
    #     if st.button("Add Diagnostic Record", key="dashboard_shortcut_add_diag"):
    #         st.session_state.current_page = "add_diagnostic_record"
    #         st.rerun()
    #     if st.button("Natural Language Query", key="dashboard_shortcut_nlq"):
    #         st.session_state.current_page = "natural_language_query"
    #         st.rerun()

    # with col3:
    #     if st.button("Inventory Insights", key="dashboard_shortcut_inventory"):
    #         st.session_state.current_page = "inventory_insights"
    #         st.rerun()
    #     if st.button("Patient Summary", key="dashboard_shortcut_patient"):
    #         st.session_state.current_page = "patient_summary"
    #         st.rerun()

    # st.markdown("---")
    st.info("Use the navigation menu on the left to access all features.")