# pages/patient_summary_page.py
import streamlit as st
from services.database_service import execute_sql_query, fetch_all_patient_names_and_ids # Import from new path
from services.gemini_service import get_llm_analysis_from_data # Import from new path
from prompts import LLM_PATIENT_SUMMARY_PROMPT # Import from new path

def show_patient_summary_page():
    st.header("AI-Powered Patient History Summarizer")
    st.markdown("Get a concise, AI-generated summary of a patient's diagnostic and medication history.")

    patient_data = fetch_all_patient_names_and_ids()
    if patient_data:
        patient_names = [f"{name} (ID: {pid})" for pid, name in patient_data]
        patient_dict = {f"{name} (ID: {pid})": pid for pid, name in patient_data}

        selected_patient = st.selectbox("Search for a patient by name:", options=patient_names, index=0)

        if st.button("Generate Patient Summary", key="generate_patient_summary_btn"):
            if selected_patient:
                patient_id_summary = patient_dict[selected_patient]
                with st.spinner(f"Generating summary for {selected_patient}..."):
                    summary_query = f"""
                    SELECT
                        DD.PATIENT_NAME,
                        DD.DIAGNOSIS,
                        DD.DIAGNOSIS_DATE,
                        DD.TEST_RESULTS,
                        PI.DRUG_NAME,
                        PI.DOSAGE
                    FROM DIAGNOSTIC_DATA AS DD
                    LEFT JOIN PHARMACY_INVENTORY AS PI ON DD.DRUG_ID_PRESCRIBED = PI.DRUG_ID
                    WHERE DD.PATIENT_ID = {patient_id_summary}
                    ORDER BY DD.DIAGNOSIS_DATE ASC;
                    """
                    summary_data_raw, summary_cols = execute_sql_query(summary_query)

                    if summary_data_raw:
                        summary_data_df = [dict(zip(summary_cols, row)) for row in summary_data_raw]

                        llm_summary = get_llm_analysis_from_data(
                            summary_data_df,
                            LLM_PATIENT_SUMMARY_PROMPT,
                            original_request=f"Summarize the health history for {selected_patient}"
                        )
                        if llm_summary and not llm_summary.startswith("Error:"):
                            st.subheader(f"Summary for {selected_patient}:")
                            st.write(llm_summary)
                        else:
                            st.error(llm_summary)
                    else:
                        st.info(f"No diagnostic data found for {selected_patient}.")
            else:
                st.warning("Please select a patient.")
    else:
        st.warning("No patients found in the diagnostic data.")
    st.markdown("---")