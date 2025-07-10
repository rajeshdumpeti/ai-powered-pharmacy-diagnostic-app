
import streamlit as st

def apply_custom_styles():
    """Applies custom CSS styles for the Streamlit app."""
    st.markdown("""
        <style>
        /* Target the specific 'Generate SQL Query & Execute' button by its key */
        button[data-testid="stButton-manual_submit_llm"] {
            background-color: #4CAF50; /* A pleasant shade of green */
            color: white; /* White text for good contrast */
            padding: 12px 24px; /* Slightly more padding for a larger touch area */
            border-radius: 8px; /* More rounded corners */
            border: none; /* Remove default border */
            font-size: 18px; /* Slightly larger font */
            font-weight: bold; /* Make text bold */
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); /* Subtle shadow for depth */
            transition: background-color 0.3s ease, box-shadow 0.3s ease, transform 0.2s ease; /* Smooth transitions */
        }

        button[data-testid="stButton-manual_submit_llm"]:hover {
            background-color: #45a049; /* Darker green on hover */
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3); /* Enhanced shadow on hover */
            transform: translateY(-2px); /* Slight lift effect */
        }

        button[data-testid="stButton-manual_submit_llm"]:active {
            background-color: #3e8e41; /* Even darker green when clicked */
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); /* Smaller shadow when active */
            transform: translateY(0); /* Return to original position */
        }
        </style>
    """, unsafe_allow_html=True)