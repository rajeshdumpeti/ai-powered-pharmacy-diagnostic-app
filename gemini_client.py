# gemini_client.py
import os
import re
import time
import google.generativeai as genai
import streamlit as st # For displaying Streamlit warnings/errors

from dotenv import load_dotenv

load_dotenv() # Load environment variables here as well, needed for API key setup

def configure_gemini():
    """Configures the Google Gemini API key."""
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
        return True
    else:
        st.error("Error: GOOGLE_API_KEY not found in environment variables. Please check your .env file.")
        return False

def get_gemini_response(question, prompt, max_retries=3, initial_delay=5):
    """
    Loads the Gemini model and provides an SQL query response to a given question
    with retry logic for API quota issues.
    """
    if not configure_gemini(): # Ensure API key is configured before making calls
        return "Error: Gemini API not configured."

    model = genai.GenerativeModel('models/gemini-2.0-flash') # Using flash model as per your code
    for attempt in range(max_retries):
        try:
            response = model.generate_content([prompt[0], question])
            cleaned_response = response.text.strip()
            # This regex correctly extracts content from various code block formats (```sql, ```, ```python)
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
                    time.sleep(delay)
                else:
                    st.error("Max retries reached for API call. Please try again later or check your Google API quotas.")
                    return "Error: API quota exceeded."
            else:
                st.error(f"An unexpected API error occurred: {e}")
                return "Error: An API error occurred."
    return "Error: Failed to get response after multiple retries."