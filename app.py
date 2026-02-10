import streamlit as st
import pytesseract
from PIL import Image
from pillow_heif import register_heif_opener
from gtts import gTTS
import io
import random

# 1. iPhone Image Support (HEIC)
register_heif_opener()

st.set_page_config(page_title="AI Spelling Bee", layout="centered")

# --- SESSION STATE ---
if 'test_list' not in st.session_state:
    st.session_state.test_list = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'revealed' not in st.session_state:
    st.session_state.revealed = False

# --- UI ---
st.title("🐝 AI Spelling Bee")

with st.sidebar:
    st.header("Settings")
    max_words = st.number_input("Words per test", min_value=1, value=10)
    randomize = st.checkbox("Randomize List", value=True)
    if st.button("🗑️ New Scan / Clear"):
        st.session_state.test_list = []
        st.session_state.current_index = 0
        st.rerun()

# 1. SCANNING SECTION
if not st.session_state.test_list:
    st.write("### 📸 1. Scan your word list")
    image_file = st.file_uploader("Upload or Take Photo", type=['png', 'jpg', 'jpeg', 'heic'])

    if image_file:
        # iPhone Fix: Convert to RGB to clear metadata
        img = Image.open(image_file).convert("RGB")
        st.image(img, width=300)
        
        # Using type="primary" makes the button a solid, readable color
        if st.button("📝 Load Words", type="primary", use_container_width=True):
            with st.spinner("Reading words..."):
                text = pytesseract.image_to_string(img)
                extracted = [line.strip() for line in text.split('\n') if len(line.strip()) > 1]
                
                if extracted:
                    if randomize:
                        random.shuffle(extracted)
                    st.session_state.test_list = extracted[:max_words]
                    st.rerun()
                else:
                    st.error("No words found. Try a closer photo.")

# 2. TESTING SECTION
else:
    word = st.session_state.test_list[st.session_state.current_index]
    
    st.write(f"**Word {st.session_state.current_index + 1} of {len(st.session_state.test_list)}**")
    
    # RELIABLE AUDIO: Standard Streamlit audio player
    # This is the only method iOS doesn't block
    tts = gTTS(text=word, lang='en')
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    
    st.write("### 🔊 Listen:")
    st.audio(mp3_fp, format="audio/mp3")
        
    st.divider()
    
    # REVEAL SECTION
    if not st.session_state.revealed:
        if st.button("👁️ SHOW SPELLING", type="primary", use_container_width=True):
            st.session_state.revealed = True
            st.rerun()
    else:
        # Show the word in large text
        st.markdown(f"<h1 style='text-align: center; color: #4CAF50;'>{word}</h1>", unsafe_allow_html=True)

    st.divider()

    # NAVIGATION
    if st.button("NEXT WORD ➡️", use_container_width=True):
        if st.session_state.current_index < len(st.session_state.test_list) - 1:
            st.session_state.current_index += 1
            st.session_state.revealed = False
            st.rerun()
        else:
            st.balloons()
            st.success("Test Complete!")
            if st.button("Start New Test"):
                st.session_state.test_list = []
                st.rerun()
                
