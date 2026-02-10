import streamlit as st
import streamlit.components.v1 as components
import pytesseract
from PIL import Image
from pillow_heif import register_heif_opener # <--- New translator
from gtts import gTTS
import io
import random
import base64
import time

# Register the HEIC opener so Pillow can read iPhone photos
register_heif_opener()

# --- CONFIGURATION ---
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

st.set_page_config(page_title="🐝 AI Spelling Bee", layout="centered")

# --- CSS FOR UI ---
st.markdown("""
    <style>
    div.stButton > button {
        height: 3.5em;
        font-size: 18px !important;
        font-weight: bold;
        border-radius: 12px;
    }
    .timer-text {
        font-size: 20px;
        text-align: center;
        color: #FF4B4B;
    }
    </style>
""", unsafe_allow_html=True)

# --- THE BULLETPROOF AUDIO FIX ---
def play_audio(text):
    tts = gTTS(text=text, lang='en')
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    b64 = base64.b64encode(mp3_fp.getvalue()).decode()
    
    unique_id = f"audio_{int(time.time() * 1000)}"
    
    components.html(
        f"""
        <div id="{unique_id}_container"></div>
        <script>
            var audio = new Audio("data:audio/mp3;base64,{b64}");
            audio.play().catch(e => console.log("Playback failed:", e));
        </script>
        """,
        height=0,
    )

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
    st.header("⚙️ Practice Settings")
    auto_reveal = st.toggle("Auto-Reveal Word", value=True)
    reveal_delay = st.slider("Seconds to wait:", 1, 10, 3)
    
    st.divider()
    max_words = st.number_input("Words per test", min_value=1, value=10)
    randomize = st.checkbox("Randomize List", value=True)
    
    if st.button("🗑️ Start Over / New Scan"):
        st.session_state.test_list = []
        st.session_state.current_index = 0
        st.rerun()

# 1. SCANNING SECTION
if not st.session_state.test_list:
    image_file = st.file_uploader("Upload word list photo", type=['png', 'jpg', 'jpeg', 'heic'])

    if image_file:
        img = Image.open(image_file)
        # CONVERT TO RGB: This strips out iPhone metadata that confuses Tesseract
        img = img.convert("RGB")
        
        st.image(img, width=300)
        if st.button("📝 Start Practice Session"):
            with st.spinner("Extracting words..."):
                # We pass the cleaned RGB image to Tesseract
                text = pytesseract.image_to_string(img)
                extracted = [line.strip() for line in text.split('\n') if len(line.strip()) > 1]
                
                if extracted:
                    if randomize:
                        random.shuffle(extracted)
                    st.session_state.test_list = extracted[:max_words]
                    st.rerun()
                else:
                    st.error("No text found. Check lighting/focus.")

# 2. TESTING SECTION
else:
    word = st.session_state.test_list[st.session_state.current_index]
    st.write(f"### Word {st.session_state.current_index + 1} of {len(st.session_state.test_list)}")
    
    if st.button("🔊 READ WORD"):
        play_audio(word)
        
        if auto_reveal and not st.session_state.revealed:
            placeholder = st.empty()
            for i in range(reveal_delay, 0, -1):
                placeholder.markdown(f"<p class='timer-text'>Revealing in {i}...</p>", unsafe_allow_html=True)
                time.sleep(1)
            placeholder.empty()
            st.session_state.revealed = True
            st.rerun()
            
    st.divider()
    
    if not st.session_state.revealed:
        if st.button("👁️ SHOW SPELLING"):
            st.session_state.revealed = True
            st.rerun()

    if st.session_state.revealed:
        st.markdown(f"<h1 style='text-align: center; color: #4CAF50;'>{word}</h1>", unsafe_allow_html=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #ccc;'>????</h1>", unsafe_allow_html=True)

    st.divider()

    if st.button("NEXT WORD ➡️"):
        if st.session_state.current_index < len(st.session_state.test_list) - 1:
            st.session_state.current_index += 1
            st.session_state.revealed = False
            st.rerun()
        else:
            st.balloons()
            st.success("Test Complete!")
            if st.button("Restart Session"):
                st.session_state.test_list = []
                st.rerun()
                
