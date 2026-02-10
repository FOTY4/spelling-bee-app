import streamlit as st
import streamlit.components.v1 as components
import pytesseract
from PIL import Image
from pillow_heif import register_heif_opener
from gtts import gTTS
import io
import random
import base64
import time
import requests

# Register the HEIC opener for iPhone photos
register_heif_opener()

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
    .definition-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #4CAF50;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

def play_audio(text):
    tts = gTTS(text=text, lang='en')
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    b64 = base64.b64encode(mp3_fp.getvalue()).decode()
    unique_id = f"audio_{int(time.time() * 1000)}"
    components.html(
        f"""<script>var audio = new Audio("data:audio/mp3;base64,{b64}");
        audio.play().catch(e => console.log(e));</script>""",
        height=0,
    )

def get_definition(word):
    """Fetches definition from Free Dictionary API."""
    try:
        response = requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}")
        if response.status_code == 200:
            data = response.json()
            # Extract the first definition found
            definition = data[0]['meanings'][0]['definitions'][0]['definition']
            return definition
        return "Definition not found for this word."
    except:
        return "Could not connect to dictionary service."

# --- SESSION STATE ---
if 'test_list' not in st.session_state:
    st.session_state.test_list = []
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'revealed' not in st.session_state:
    st.session_state.revealed = False
if 'show_def' not in st.session_state:
    st.session_state.show_def = False

# --- UI ---
st.title("🐝 AI Spelling Bee + Vocab")

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
        st.session_state.show_def = False
        st.rerun()

# 1. SCANNING SECTION
if not st.session_state.test_list:
    image_file = st.file_uploader("Upload word list photo", type=['png', 'jpg', 'jpeg', 'heic'])
    if image_file:
        img = Image.open(image_file).convert("RGB")
        st.image(img, width=300)
        if st.button("📝 Start Practice Session"):
            with st.spinner("Extracting words..."):
                text = pytesseract.image_to_string(img)
                extracted = [line.strip() for line in text.split('\n') if len(line.strip()) > 1]
                if extracted:
                    if randomize: random.shuffle(extracted)
                    st.session_state.test_list = extracted[:max_words]
                    st.rerun()
                else:
                    st.error("No text found. Check lighting/focus.")

# 2. TESTING SECTION
else:
    word = st.session_state.test_list[st.session_state.current_index]
    st.write(f"### Word {st.session_state.current_index + 1} of {len(st.session_state.test_list)}")
    
    col1, col2 = st.columns(2)
    with col1:
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

    with col2:
        if st.button("📖 DEFINITION"):
            st.session_state.show_def = True

    # Show Definition if requested
    if st.session_state.show_def:
        definition = get_definition(word)
        st.markdown(f"<div class='definition-box'><b>Definition:</b><br>{definition}</div>", unsafe_allow_html=True)

    st.divider()
    
    # Reveal Word logic
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
            st.session_state.show_def = False # Reset definition for next word
            st.rerun()
        else:
            st.balloons()
            st.success("Test Complete!")
            if st.button("Restart Session"):
                st.session_state.test_list = []
                st.rerun()
                
