import streamlit as st
import pytesseract
from PIL import Image
from gtts import gTTS
import io
import random
import base64
import time

# --- CONFIGURATION ---
# If on Windows, ensure this path is correct:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.set_page_config(page_title="AI Spelling Bee", layout="centered")

# --- CUSTOM CSS & AUTOPLAY SCRIPT ---
def play_audio(text):
    """Generates audio and injects HTML to autoplay it with a unique ID."""
    tts = gTTS(text=text, lang='en')
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    b64 = base64.b64encode(mp3_fp.getvalue()).decode()
    
    # We add a unique 'timestamp' so the browser always sees this as a new element
    unique_id = str(time.time()).replace('.', '')
    
    md = f"""
        <audio autoplay="true" id="{unique_id}">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """
    st.markdown(md, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'all_extracted_words' not in st.session_state:
    st.session_state.all_extracted_words = []
if 'test_list' not in st.session_state:
    st.session_state.test_list = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'revealed' not in st.session_state:
    st.session_state.revealed = False

# --- OCR LOGIC ---
def extract_text(image):
    text = pytesseract.image_to_string(image)
    lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 1]
    return lines

# --- UI ---
st.title("🐝 AI Spelling Bee Pro")

with st.sidebar:
    st.header("Test Settings")
    max_words = st.number_input("Max words per test", min_value=1, value=10)
    randomize = st.checkbox("Randomize word order", value=True)
    
    if st.button("♻️ Restart / New Test"):
        if st.session_state.all_extracted_words:
            words = st.session_state.all_extracted_words.copy()
            if randomize:
                random.shuffle(words)
            st.session_state.test_list = words[:max_words]
            st.session_state.current_index = 0
            st.session_state.revealed = False
            st.rerun()

# 1. UPLOAD
image_file = st.file_uploader("Upload spelling list photo", type=['png', 'jpg', 'jpeg'])

if image_file and not st.session_state.test_list:
    img = Image.open(image_file)
    st.image(img, width=250)
    if st.button("📝 Load Words from Photo"):
        extracted = extract_text(img)
        if extracted:
            st.session_state.all_extracted_words = extracted
            words_to_use = extracted.copy()
            if randomize:
                random.shuffle(words_to_use)
            st.session_state.test_list = words_to_use[:max_words]
            st.rerun()

# 2. TESTING
if st.session_state.test_list:
    current_word = st.session_state.test_list[st.session_state.current_index]
    
    st.write(f"### Word {st.session_state.current_index + 1} of {len(st.session_state.test_list)}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔊 Read Word"):
            play_audio(current_word)
            
    with col2:
        if st.button("👁️ Reveal Word"):
            st.session_state.revealed = True

    # Display Result
    st.markdown("---")
    if st.session_state.revealed:
        st.markdown(f"<h1 style='text-align: center; color: #4CAF50;'>{current_word}</h1>", unsafe_allow_html=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #888;'>????</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # NAVIGATION
    if st.button("Next Word ➡️"):
        if st.session_state.current_index < len(st.session_state.test_list) - 1:
            st.session_state.current_index += 1
            st.session_state.revealed = False
            st.rerun()
        else:
            st.balloons()
            st.success("Test Complete!")
            if st.button("Start Over"):
                st.session_state.test_list = []
                st.rerun()
