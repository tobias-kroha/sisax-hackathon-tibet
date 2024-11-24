import zipfile
import streamlit as st
import pandas as pd
from datetime import datetime
import logging
import io
import os
import base64
import aisisax.llm.openai_connector as aisax_openai
import json
from mimetypes import guess_type
from PIL import Image
import subprocess

__version__ = "0.5"

st.set_page_config(
    page_title="AI Manuscript Analysis",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Configure server to handle larger files
st._config.set_option('server.maxUploadSize', 200)  # Size in MB (1024 MB = 1 GB)

# Configure logging to capture output for display
class StreamlitHandler(logging.Handler):
    def __init__(self, placeholder):
        super().__init__()
        self.placeholder = placeholder
        self.logs = []

    def emit(self, record):
        log_entry = self.format(record)
        self.logs.append(log_entry)
        # Join all logs and update the placeholder
        log_text = '\n'.join(self.logs)
        self.placeholder.text_area("Processing Logs", log_text, height=200)

def convert_tiff_to_jpg(tiff_path):
    # Open and convert TIFF to JPG
    with Image.open(tiff_path) as img:
        jpg_path = os.path.splitext(tiff_path)[0] + '.jpg'
        img.convert('RGB').save(jpg_path, 'JPEG', quality=70)
    # Remove original TIFF file
    os.remove(tiff_path)
    return jpg_path

def process_images(uploaded_files, progress_bar, log_placeholder):
    # Set up logging
    logger = logging.getLogger('tibet_processor')
    logger.setLevel(logging.INFO)
    handler = StreamlitHandler(log_placeholder)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    df = pd.DataFrame()

    # Clear temp directory at start
    if not hasattr(st.session_state, 'temp_files'):
        st.session_state.temp_files = []
        
    # Create a directory for storing images if it doesn't exist
    images_dir = "static/images"
    os.makedirs(images_dir, exist_ok=True)

    all_files = []
    
    # Handle ZIP files and regular image files
    for uploaded_file in uploaded_files:
        try:
            if uploaded_file.type == 'application/zip':
                # Create a temporary file to save the ZIP content
                zip_path = os.path.join(images_dir, uploaded_file.name)
                with open(zip_path, 'wb') as f:
                    f.write(uploaded_file.read())
                
                # Extract ZIP contents
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # create a directory for the zip file in the images directory, name is the zip file name without extension
                    zip_dir = os.path.join(images_dir, os.path.splitext(uploaded_file.name)[0])
                    os.makedirs(zip_dir, exist_ok=True)

                    # Extract all files to the images directory
                    zip_ref.extractall(zip_dir)

                    logger.info(f"Extracted {len(zip_ref.namelist())} files from ZIP file {uploaded_file.name}")

                    # if zip contains tiff files, convert them to jpg
                    for name in zip_ref.namelist():
                        if name.lower().endswith(('.tif', '.tiff')):
                            tiff_path = os.path.join(zip_dir, name)
                            jpg_path = convert_tiff_to_jpg(tiff_path)
                            all_files.append(jpg_path)
                
                    # remove the last files from all_files (to skip the color calibration page)
                    all_files = all_files[:-1]

                # Remove the temporary ZIP file
                os.remove(zip_path)
            else:
                # Handle regular image files
                file_path = os.path.join(images_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.read())
                all_files.append(file_path)
                
        except Exception as e:
            logger.error(f"Error processing {uploaded_file.name}: {str(e)}")
            if 'result' in locals():
                logger.error(f"Raw result: {result}")

    logger.info(f"Processing {len(all_files)} files")
    
    # Process all files
    for i, file_path in enumerate(all_files):
        filename = os.path.basename(file_path)
        logger.info(f"Processing {filename} Size: {os.path.getsize(file_path) / 1024:.2f} KB with model {st.session_state.model}, temperature {st.session_state.temperature}")

        try:
            # Extract ppn and page number from filename
            filename_parts = file_path.split("/")

            logger.debug(f"Filename parts: {filename_parts}")
            ppn = filename_parts[-2] if len(filename_parts) > 1 else "unknown"
            page_number = filename_parts[-1] if len(filename_parts) > 0 else "unknown"
            # strip extension from page number and convert to int (if possible)
            try:
                page_number = int(os.path.splitext(page_number)[0])
            except ValueError:
                page_number = "unknown"

            result = aisax_openai.generate_multimodal_answer(
                st.session_state.ai_prompt,
                image_path=file_path, 
                temperature=st.session_state.temperature,
                api_key=st.session_state.openai_api_key,
                model=st.session_state.model
            )

            # Process the result and convert to JSON
            result = result.strip().split('\n')[1:-1]
            result = '\n'.join(result)
            result = json.loads(result)

            # Add additional metadata
            if ppn.isdigit():
                result["PPN"] = ppn
            result["Page number"] = page_number

            # Store the absolute path
            result["Image"] = file_path

            # Append the result to DataFrame
            df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)

        except Exception as e:
            logger.error(f"Error processing {filename}: {str(e)}")
            if 'result' in locals():
                logger.error(f"Raw result: {result}")

        progress_bar.progress((i + 1) / len(all_files))

    return df

def cleanup_temp_files():
    if hasattr(st.session_state, 'temp_files'):
        for temp_file in st.session_state.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                # Also remove the parent directory if empty
                parent_dir = os.path.dirname(temp_file)
                if not os.listdir(parent_dir):
                    os.rmdir(parent_dir)
            except Exception as e:
                print(f"Error removing temporary file {temp_file}: {e}")
        st.session_state.temp_files = []

def main():
    # Initialize session state variables
    if 'jpg_quality' not in st.session_state:
        st.session_state.jpg_quality = 70
    if 'ai_prompt' not in st.session_state:
        st.session_state.ai_prompt = """You are an expert for interpreting Tibetan manuscripts. 
Attached you will find an image of a Tibetan manuscript. Use your expertise to analyze the image and provide responses. The analysis should specifically account for the presence of Tibetan, Chinese, and Arabic numerals, as well as structural and illustrative elements. Consider the following charsets for enhanced accuracy:
Tibetan script (U+0F00–U+0FFF): Including Tibetan characters, numerals (e.g., ཀ, ཁ, ག, ༡, ༢, ༣), and annotations.
Chinese characters (U+4E00–U+9FFF): Traditional and simplified forms.
Arabic numerals (0–9): Standard decimal numbers.

Answer the following questions and respond as a pure JSON object the following format:

"Chinese character present" (Bool): Is there at least one Chinese character or number on the image
"Chinese page number" (Bool): Does the image contain at least one chinese character or number, that is vertical oriented and is on the right side of the image outside of the tibet?
"Arabic numeral present" (Bool): Does the image contain an Arabic numeral?
"Arabic numeral int" (Integer): If there is an Arabic numeral, which one?
"Illustration present" (Bool): Does the image contain an illustration? Round red stamps are not illustrations
"Illustration position" (String): If the image contains not an illustration return 'none', else return the postion of the illustrated area as 'left', 'right' or 'center'
"Illustration caption" (Bool): Does the image contain an illustration with a caption?
"Tibetian page number" (Bool): Does the image contain a page number in tibetian, that are vertical oriented and left aligned. If so return 'true', 'false' otherwise
"Frame present" (String): Analyze the image to detect vertical lines framing the text. The lines may be thin, uniform, and either red or black. Respond with one of the following: None if no lines are present, Red if red lines are detected, or Black if black lines are detected
"""
    if 'temperature' not in st.session_state:
        st.session_state.temperature = 0.5
    if 'openai_api_key' not in st.session_state:
        st.session_state.openai_api_key = None
    if 'model' not in st.session_state:
        st.session_state.model = "gpt-4o"  # Default model
    
    # Clean up any existing temporary files
    cleanup_temp_files()
    
    st.title("AI Manuscript Analysis")
    
    
    # Initialize session state variables
    if 'processing_started' not in st.session_state:
        st.session_state.processing_started = False
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    
    # Add configuration button and expander
    with st.expander("⚙️ Settings"):
        col1, col2, col3 = st.columns(3)  # Changed to 3 columns
        
        with col1:
            st.session_state.jpg_quality = st.slider(
                "JPG Compression Quality", 
                1, 100, 
                st.session_state.jpg_quality,
                help="Higher value = better quality but larger file size"
            )
        
        with col2:
            st.session_state.temperature = st.slider(
                "AI Temperature", 
                0.0, 1.0, 
                st.session_state.temperature,
                step=0.1,
                help="Higher values make the output more creative but less predictable"
            )
        
        with col3:
            st.session_state.model = st.selectbox(
                "AI Model",
                options=["gpt-4o", "chatgpt-4o-latest", "gpt-4o-mini"],
                index=0,  # Default to gpt-4o
                help="Select the AI model to use for analysis"
            )
        
        # API key input
        api_key = st.text_input(
            "OpenAI API Key (optional)", 
            type="password",
            help="Enter your OpenAI API key. If left empty, the default key will be used."
        )
        # Update session state based on input
        st.session_state.openai_api_key = api_key if api_key.strip() else None
        
        st.session_state.ai_prompt = st.text_area(
            "AI Analysis Prompt",
            st.session_state.ai_prompt,
            height=400,
            help="Customize the prompt sent to the AI for image analysis"
        )
    
    # File uploader (remove max_size parameter)
    uploaded_files = st.file_uploader(
        "Upload manuscript images", 
        accept_multiple_files=True, 
        type=['zip', 'jpg', 'jpeg', 'png']
    )

    if uploaded_files:
        st.write(f"Number of files uploaded: {len(uploaded_files)}")

        # Create placeholder for progress bar and logs
        progress_bar = st.progress(0)
        log_placeholder = st.empty()
        
       
        if st.button("Process Images", key="process_button"):
            st.session_state.processing_started = True  # Set flag to indicate processing has started
            with st.spinner("Processing images..."):
                # Process the uploaded files
                df = process_images(uploaded_files, progress_bar, log_placeholder)
            st.session_state.df = df  # Store DataFrame in session state
            st.session_state.processing_complete = True  # Set flag to indicate processing is complete
            st.success("Processing complete!")


         # Optionally, show processing status
        elif st.session_state.processing_started and not st.session_state.processing_complete:
            st.info("Processing images... Please wait.")
        
        # Show results after processing
        if st.session_state.get('processing_complete'):
            df = st.session_state.df
            
            # Create download buttons
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)
            
            st.download_button(
                label="Download Excel Results",
                data=excel_buffer,
                file_name="tibet_analysis.xlsx",
                mime="application/vnd.ms-excel"
            )
            
            # Display each row with its image using Streamlit components
            for _, row in df.iterrows():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    # Display the image using st.image
                    image_path = row['Image']
                    if os.path.exists(image_path):
                        st.image(image_path, width=750)
                    else:
                        st.error(f"Image not found: {image_path}")
                
                with col2:
                    # Display column labels
                    for col in df.columns:
                        if col != 'Image':                       
                            st.write(f"**{col}**")
                
                with col3:
                    # Display values, excluding the 'Image' column
                    for col in df.columns:
                        if col != 'Image':
                            if isinstance(row[col], bool):
                                st.write("✅ Yes" if row[col] else "❌ No")
                            else:
                                st.write(f"{row[col]}")
                
                st.divider()  # Add a separator between rows
            # Reset button
            if st.button("Process New Files", key="reset_button"):
                st.session_state.processing_started = False
                st.session_state.processing_complete = False
                st.session_state.df = None
                cleanup_temp_files()
                st.rerun()

    st.markdown("""---""")
    st.markdown(f"<p style='text-align: right; color: grey; font-size: 11px;'>Version v{__version__}</p>", unsafe_allow_html=True)
            

if __name__ == "__main__":
    main() 