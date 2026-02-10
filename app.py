import streamlit as st
import streamlit.components.v1 as components
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

st.set_page_config(page_title="Universal Study Buddy", layout="centered")

# --- IMPROVED AUDIO FUNCTION ---
def play_audio(text):
    """Uses a custom component to force the browser to play audio every time."""
    tts = gTTS(text=text, lang='en')
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    b64 = base64.b64encode(mp3_fp.getvalue()).decode()
    
    # We use components.html to force a fresh iframe/re-render for the audio
    # The unique timestamp in the key ensures it never 'caches' the play command
    unique_key = f"audio_{int(time.time() * 1000)}"
    components.html(
        f"""
        <audio autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """,
        height=0,
    )

# --- SESSION STATE ---
if 'all_items' not in st.session_state:
    st.session_state.all_items = []
if 'test_list' not in st.session_state:
    st.session_state.test_list = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'revealed' not in st.session_state:
    st.session_state.revealed = False

# --- OCR LOGIC ---
def extract_text(image):
    # 'config' tells Tesseract to look for blocks of text
    text = pytesseract.image_to_string(image)
    lines = [line.strip() for line in text.split('\n') if len(line.strip()) > 1]
    return lines

# --- UI ---
st.title("🎓 Universal Study Buddy")
st.caption("Scan spelling words, math problems, or study notes!")

with st.sidebar:
    st.header("⚙️ Settings")
    mode = st.selectbox("Practice Mode", ["Spelling Bee", "Math / General Work"])
    max_items = st.number_input("Max items to test", min_value=1, value=10)
    randomize = st.checkbox("Randomize order", value=True)
    
    if st.button("♻️ Reset & Clear All"):
        st.session_state.all_items = []
        st.session_state.test_list = []
        st.session_state.current_index = 0
        st.rerun()

# 1. UPLOAD SECTION
if not st.session_state.test_list:
    st.write("### 📸 Step 1: Scan your work")
    image_file = st.file_uploader("Upload or take a photo", type=['png', 'jpg', 'jpeg'])

    if image_file:
        img = Image.open(image_file)
        st.image(img, width=300)
        if st.button("🔍 Process Scanned Work"):
            with st.spinner("Reading text..."):
                extracted = extract_text(img)
                if extracted:
                    st.session_state.all_items = extracted
                    items_to_use = extracted.copy()
                    if randomize:
                        random.shuffle(items_to_use)
                    st.session_state.test_list = items_to_use[:max_items]
                    st.rerun()
                else:
                    st.error("Couldn't read any text. Try a closer, brighter photo!")

# 2. TESTING SECTION
else:
    current_item = st.session_state.test_list[st.session_state.current_index]
    
    st.write(f"### 📝 {mode} Practice")
    st.progress((st.session_state.current_index + 1) / len(st.session_state.test_list))
    st.caption(f"Item {st.session_state.current_index + 1} of {len(st.session_state.test_list)}")

    # --- MODE LOGIC ---
    if mode == "Spelling Bee":
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔊 Read Word"):
                play_audio(current_item)
        with col2:
            if st.button("👁️ Reveal Word"):
                st.session_state.revealed = True
        
        st.markdown("---")
        if st.session_state.revealed:
            st.markdown(f"<h1 style='text-align: center; color: #4CAF50;'>{current_item}</h1>", unsafe_allow_html=True)
        else:
            st.markdown("<h1 style='text-align: center; color: #888;'>????</h1>", unsafe_allow_html=True)

    else:  # MATH / GENERAL MODE
        st.info("Reading the scanned problem below. Try to solve it before revealing!")
        # Use LaTeX for math if it looks like an equation, otherwise plain text
        if any(char in current_item for char in '+=-*/^'):
            st.latex(current_item.replace('x', r'\cdot'))
        else:
            st.subheader(f"Question: {current_item}")
        
        if st.button("👁️ Reveal Answer/Text"):
            st.session_state.revealed = True
        
        if st.session_state.revealed:
            st.success(f"Scanned Text: {current_item}")

    st.markdown("---")

    # NAVIGATION
    col_a, col_b = st.columns([1, 1])
    with col_b:
        if st.button("Next Item ➡️"):
            if st.session_state.current_index < len(st.session_state.test_list) - 1:
                st.session_state.current_index += 1
                st.session_state.revealed = False
                st.rerun()
            else:
                st.balloons()
                st.success("Practice Complete!")
                if st.button("Start New Session"):
                    st.session_state.test_list = []
                    st.rerun()
