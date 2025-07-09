# pages/natural_language_query_page.py
import streamlit as st
from services.database_service import execute_sql_query # Import from new path
from services.gemini_service import generate_sql_query_from_prompt # Import from new path
from prompts import LLM_SQL_GENERATION_PROMPT # Import from new path

def show_natural_language_query_page():
    st.header("Natural Language Query (Advanced)")
    st.markdown("Type natural language questions or commands for direct SQL generation, including updates, inserts, and deletes.")

    user_typed_question = st.text_input(
        "Enter your query or command:",
        value=st.session_state.question_input_value,
        key="main_input_text"
    )

    st.subheader("Or choose from a suggestion:")

    suggested_prompts = [
        "Show all drugs with less than 50 packs in stock.",
        "List all drugs supplied by PharmaCorp.",
        "Which drugs are expiring before 2026-12-31?",
        "List patient names with a 'Diabetes Type 2' diagnosis.",
        "What drugs were prescribed for patients diagnosed with 'Asthma'?",
        "Show the diagnosis and prescribed drug for patient Amit Sharma.",
        "How many diagnoses were made in 2024?",
        "Sell 5 packs of Ibuprofen 200mg tablets.",
        "Restock 15 packs of Metformin 500mg tablets.",
        "What is the stock quantity for Lipitor 20mg tablets?",
        "Add a new drug: Ibuprofen, Ibuprofen, Tablet, 400mg, 50 tabs, 4.00 price, 200 stock, 2027-01-01 expiry, supplied by GenericMeds.",
        "Delete drug with DRUG_ID 1."
    ]

    def set_question_only(prompt_text):
        st.session_state.question_input_value = prompt_text
        st.rerun()

    cols_llm_suggestions = st.columns(3)

    for i, prompt_text in enumerate(suggested_prompts):
        with cols_llm_suggestions[i % 3]:
            if st.button(prompt_text, key=f"suggest_llm_{i}"):
                set_question_only(prompt_text)

    submit_button_clicked_llm = st.button("Generate SQL Query & Execute", key="manual_submit_llm")

    if submit_button_clicked_llm:
        current_question_llm = st.session_state.main_input_text
        
        if current_question_llm.strip() == "":
            st.warning("Please enter a query or command, or choose a suggestion.")
        else:
            with st.spinner("Generating SQL query..."):
                generated_sql_query = generate_sql_query_from_prompt(current_question_llm, LLM_SQL_GENERATION_PROMPT)

            if generated_sql_query and not generated_sql_query.startswith("Error:"):
                st.subheader("Generated SQL Query:")
                st.code(generated_sql_query, language="sql")

                st.subheader("Query Results/Status:")
                
                query_results_data, query_results_columns = execute_sql_query(generated_sql_query) 

                history_entry = {
                    "prompt": current_question_llm,
                    "sql": generated_sql_query,
                    "result": query_results_data if isinstance(query_results_data, str) else "Data Retrieved",
                    "status": "Success"
                }
                if query_results_data is not None and isinstance(query_results_data, list) and not query_results_data:
                    history_entry["result"] = "No results found"
                st.session_state.prompt_history.append(history_entry)

                if query_results_data is not None:
                    if isinstance(query_results_data, str): 
                        st.success(query_results_data)
                        if generated_sql_query.strip().upper().startswith(("UPDATE", "INSERT", "DELETE")):
                            st.info("The database has been modified. You can run a SELECT query to see the changes.")
                    else:
                        if query_results_data:
                            try:
                                if query_results_columns:
                                    df_data_llm = [dict(zip(query_results_columns, row)) for row in query_results_data]
                                    st.dataframe(df_data_llm)
                                else:
                                    st.write(query_results_data)
                            except Exception as e:
                                st.write(query_results_data)
                                st.warning(f"Could not display results as a table/dataframe: {e}")
                        else:
                            st.info("No results found for your query. Check the query and database content, or criteria.")
                else:
                    history_entry["status"] = "Error"
                    history_entry["result"] = "Database error occurred (see above)."
            elif generated_sql_query.startswith("Error:"):
                history_entry = {
                    "prompt": current_question_llm,
                    "sql": "N/A",
                    "result": generated_sql_query,
                    "status": "AI Generation Error"
                }
                st.session_state.prompt_history.append(history_entry)
                pass

    st.markdown("---")

    if st.button("Show Query History", key="show_history_btn"):
        if st.session_state.prompt_history:
            st.subheader("SQL Query History:")
            for i, entry in enumerate(reversed(st.session_state.prompt_history)):
                with st.expander(f"Prompt {len(st.session_state.prompt_history) - i}: {entry['prompt'][:50]}..."):
                    st.markdown(f"**Prompt:** {entry['prompt']}")
                    st.markdown(f"**Generated SQL:**")
                    st.code(entry['sql'], language="sql")
                    st.markdown(f"**Result/Status:** {entry['result']}")
                    st.markdown(f"**Overall Status:** `{entry['status']}`")
                    st.markdown("---")
        else:
            st.info("No SQL query history yet. Type a query or command and execute it!")
    st.markdown("---")