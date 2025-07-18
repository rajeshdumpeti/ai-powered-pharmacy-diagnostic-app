# services/gemini_service.py
import os
import re
import time
import google.generativeai as genai
import streamlit as st

from dotenv import load_dotenv

load_dotenv()

def configure_gemini():
    """Configures the Google Gemini API key."""
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
        return True
    else:
        st.error("Error: GOOGLE_API_KEY not found in environment variables. Please check your .env file.")
        return False

def generate_sql_query_from_prompt(question, prompt_template, max_retries=3, initial_delay=5):
    """
    Generates an SQL query from a natural language question using the Gemini model.
    """
    if not configure_gemini():
        return "Error: Gemini API not configured."

    model = genai.GenerativeModel('models/gemini-2.0-flash')
    for attempt in range(max_retries):
        try:
            response = model.generate_content([prompt_template[0], question])
            cleaned_response = response.text.strip()
            # This regex extracts content from various code block formats (```sql, ```, ```python)
            cleaned_response = re.sub(r'```(?:\w+)?\s*(.*?)\s*```', r'\1', cleaned_response, flags=re.DOTALL)
            cleaned_response = cleaned_response.strip()
            return cleaned_response
        except genai.types.BlockedPromptException as e:
            st.error(f"The request was blocked: {e.safety_ratings}. Please refine your query.")
            return "Error: Query blocked due to safety concerns."
        except Exception as e:
            if "ResourceExhausted" in str(e):
                st.warning(f"API quota exceeded (attempt {attempt + 1}/{max_retries}). Please wait a moment.")
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)
                else:
                    st.error("Max retries reached for API call. Please try again later or check your Google API quotas.")
                    return "Error: API quota exceeded."
            else:
                st.error(f"An unexpected API error occurred: {e}")
                return "Error: An API error occurred."
    return "Error: Failed to get response after multiple retries."

def get_llm_analysis_from_data(data_to_analyze, analysis_prompt_template, original_request="", max_retries=3, initial_delay=5):
    """
    Takes structured data (e.g., list of dicts from SQL query results) and an analysis prompt,
    then uses Gemini to generate a human-readable analysis or summary.
    """
    if not configure_gemini():
        return "Error: Gemini API not configured."

    model = genai.GenerativeModel('models/gemini-2.0-flash')
    
    # Format data for LLM
    formatted_data = []
    if isinstance(data_to_analyze, list) and all(isinstance(d, dict) for d in data_to_analyze):
        # Convert list of dicts to a more readable string format
        for item in data_to_analyze:
            formatted_data.append(", ".join([f"{k}: {v}" for k, v in item.items()]))
        formatted_data_str = "\n".join(formatted_data)
    else: # Fallback for non-dict data (e.g., simple list of tuples)
        formatted_data_str = str(data_to_analyze)

    # Construct the final prompt for the LLM
    if "original_request" in analysis_prompt_template: # For generic report prompt
        full_prompt = analysis_prompt_template.format(original_request=original_request, raw_data=formatted_data_str)
    else: # For patient summary or inventory insights
        full_prompt = analysis_prompt_template.format(patient_data=formatted_data_str, inventory_data=formatted_data_str)


    for attempt in range(max_retries):
        try:
            response = model.generate_content([full_prompt])
            cleaned_response = response.text.strip()
            return cleaned_response
        except genai.types.BlockedPromptException as e:
            st.error(f"The analysis request was blocked: {e.safety_ratings}. Please refine your input.")
            return "Error: Analysis blocked due to safety concerns."
        except Exception as e:
            if "ResourceExhausted" in str(e):
                st.warning(f"API quota exceeded (attempt {attempt + 1}/{max_retries}). Please wait a moment.")
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)
                else:
                    st.error("Max retries reached for analysis API call. Please try again later or check your Google API quotas.")
                    return "Error: API quota exceeded for analysis."
            else:
                st.error(f"An unexpected API error occurred during analysis: {e}")
                return "Error: An API error occurred during analysis."
    return "Error: Failed to get analysis after multiple retries."


def get_chatbot_response(user_query, chatbot_prompt_template, chat_history, max_retries=3, initial_delay=5):
    """
    Gets a conversational response from Gemini based on a user query and provided chat history.
    """
    if not configure_gemini():
        return "Error: Gemini API not configured."

    model = genai.GenerativeModel('models/gemini-2.0-flash')
    
    # Construct conversation history including the system prompt
    convo = model.start_chat(history=[])

    # Add the system prompt as an initial "user" instruction
    convo.history.append({"role": "user", "parts": [chatbot_prompt_template]})
    convo.history.append({"role": "model", "parts": ["Understood. I am ready to answer your questions about the database schema."]})

    # Add previous chat history for context
    for msg in chat_history:
        role = "user" if msg["role"] == "user" else "model"
        convo.history.append({"role": role, "parts": [msg["content"]]})


    for attempt in range(max_retries):
        try:
            response = convo.send_message(user_query)
            cleaned_response = response.text.strip()
            return cleaned_response
        except genai.types.BlockedPromptException as e:
            st.error(f"The chatbot request was blocked: {e.safety_ratings}. Please try a different phrasing.")
            return "I'm sorry, I cannot respond to that query due to safety guidelines. Please ask something different about the database structure."
        except Exception as e:
            if "ResourceExhausted" in str(e):
                st.warning(f"Chatbot API quota exceeded (attempt {attempt + 1}/{max_retries}). Please wait a moment.")
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)
                else:
                    st.error("Max retries reached for chatbot API call. Please try again later.")
                    return "I'm experiencing high traffic. Please try asking again in a few moments."
            else:
                st.error(f"An unexpected API error occurred with the chatbot: {e}")
                return "I'm sorry, an error occurred while processing your request. Please try again."
    return "I'm having trouble connecting. Please try again later."


def analyze_medical_image(image_data_base64, prompt, max_retries=3, initial_delay=5):
    """
    Analyzes a medical image using Gemini's vision capabilities.
    image_data_base64: Base64 encoded string of the image.
    prompt: Text prompt for the LLM to guide the analysis.
    """
    if not configure_gemini():
        return "Error: Gemini API not configured."

    model = genai.GenerativeModel('models/gemini-2.0-flash') # Gemini 2.0 Flash supports vision
    
    # Construct the content for the model
    contents = [
        {"role": "user", "parts": [
            {"text": prompt},
            {"inline_data": {
                "mime_type": "image/jpeg", # Assuming JPEG for now, could be dynamic based on uploaded_file.type
                "data": image_data_base64
            }}
        ]}
    ]

    for attempt in range(max_retries):
        try:
            response = model.generate_content(contents)
            cleaned_response = response.text.strip()
            return cleaned_response
        except genai.types.BlockedPromptException as e:
            st.error(f"Image analysis request blocked: {e.safety_ratings}. Please ensure the image content is appropriate.")
            return "Error: Image analysis blocked due to safety concerns. Please try a different image or refine your request."
        except Exception as e:
            if "ResourceExhausted" in str(e):
                st.warning(f"Image analysis API quota exceeded (attempt {attempt + 1}/{max_retries}). Please wait a moment.")
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)
                else:
                    st.error("Max retries reached for image analysis API call. Please try again later.")
                    return "Error: Image analysis API quota exceeded."
            else:
                st.error(f"An unexpected API error occurred during image analysis: {e}")
                return "Error: An API error occurred during image analysis."
    return "Error: Failed to get image analysis after multiple retries."