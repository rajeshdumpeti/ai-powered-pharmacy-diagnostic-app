# pages/image_analysis_page.py
import streamlit as st
from PIL import Image
import io
import base64

# Import the new image analysis function from gemini_client
from services.gemini_service import analyze_medical_image # Import from new path

def show_image_analysis_page():
    """
    Displays the UI for medical image analysis.
    Allows users to upload an image and get an AI-generated analysis.
    """
    st.markdown("<h2 style='text-align: center; color: #008080;'>Medical Image Analysis</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #2F4F4F;'>An application that helps users in recognizing medical images and provides insights.</p>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("<h4>Please upload the medical images for analysis</h4>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Drag and drop file here",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=False,
        key="image_uploader"
    )

    # State to hold the image data and analysis result
    if 'uploaded_image_data' not in st.session_state:
        st.session_state.uploaded_image_data = None
    if 'image_analysis_result' not in st.session_state:
        st.session_state.image_analysis_result = ""
    if 'uploaded_file_name' not in st.session_state:
        st.session_state.uploaded_file_name = ""
    if 'uploaded_file_size' not in st.session_state:
        st.session_state.uploaded_file_size = ""

    # Process uploaded file
    if uploaded_file is not None:
        # Read image as bytes
        bytes_data = uploaded_file.getvalue()
        
        # Display uploaded file info as in the screenshot
        st.markdown(f"""
            <div style="display: flex; align-items: center; gap: 10px; margin-top: 20px; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                <span style="font-size: 24px;">📄</span>
                <span>{uploaded_file.name}</span>
                <span style="color: #666;">{round(len(bytes_data) / 1024, 2)} KB</span>
                <span style="margin-left: auto; cursor: pointer;" onclick="window.parent.document.querySelector('[data-testid=\"image_uploader-clear-button\"]').click();">❌</span>
            </div>
            """, unsafe_allow_html=True)

        # Store in session state
        st.session_state.uploaded_image_data = bytes_data
        st.session_state.uploaded_file_name = uploaded_file.name
        st.session_state.uploaded_file_size = f"{round(len(bytes_data) / 1024, 2)} KB"

        # Optionally display the image
        st.image(uploaded_file, caption='Uploaded Medical Image', use_column_width=True)
    else:
        # Clear previous image data if no file is currently uploaded
        st.session_state.uploaded_image_data = None
        st.session_state.uploaded_file_name = ""
        st.session_state.uploaded_file_size = ""
        st.session_state.image_analysis_result = ""


    # Button to trigger analysis
    if st.button("Generate Image Analysis", key="generate_image_analysis_btn"):
        if st.session_state.uploaded_image_data:
            with st.spinner("Analyzing image... This may take a moment."):
                # Convert image bytes to base64
                base64_image = base64.b64encode(st.session_state.uploaded_image_data).decode('utf-8')

                # Define the prompt for Gemini Vision model
                analysis_prompt = """
                Analyze this medical image. Describe what you observe in detail.
                Identify any visible anatomical structures, anomalies, or potential findings.
                Based on your observations, provide a concise and informative analysis.
                DO NOT make a diagnosis or offer medical advice. Focus solely on describing the image content.
                """
                
                # Call the Gemini Vision API
                analysis_result = analyze_medical_image(base64_image, analysis_prompt)
                
                st.session_state.image_analysis_result = analysis_result
                st.rerun() # Rerun to display result

        else:
            st.warning("Please upload a medical image first to generate an analysis.")

    # Display analysis result
    if st.session_state.image_analysis_result:
        st.subheader("AI Image Analysis:")
        st.markdown(st.session_state.image_analysis_result)

    st.markdown("---")
    st.info("Disclaimer: This AI analysis is for informational purposes only and does not constitute medical advice or diagnosis. Always consult with a qualified healthcare professional for any medical concerns.")