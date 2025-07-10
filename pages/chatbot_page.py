# pages/chatbot_page.py
import streamlit as st
from services.gemini_service import get_chatbot_response # Import from new path
from prompts import LLM_CHATBOT_INFO_PROMPT # Import from new path

def show_chatbot_page():
    st.header("AI Chatbot for Database Info")
    st.markdown("Ask general questions about the Pharmacy Inventory and Diagnostic Data tables and their structure. I won't perform live data lookups, but I can tell you what kind of information is stored in each field.")

    for message in st.session_state.chatbot_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask me about the database (e.g., 'What is in PHARMACY_INVENTORY?')"):
        st.session_state.chatbot_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                full_chat_history_for_llm = []
                for msg in st.session_state.chatbot_history:
                    full_chat_history_for_llm.append({
                        "role": "user" if msg["role"] == "user" else "model",
                        "content": msg["content"]
                    })

                ai_response = get_chatbot_response(
                    user_query=prompt,
                    chatbot_prompt_template=LLM_CHATBOT_INFO_PROMPT,
                    chat_history=full_chat_history_for_llm
                )
                
                st.markdown(ai_response)
        st.session_state.chatbot_history.append({"role": "assistant", "content": ai_response})

    st.markdown("---")