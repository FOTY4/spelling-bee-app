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

# 1. iPhone Image Support
register_heif_opener()

st.set_page_config(page_title="AI Spelling Bee", layout="centered")

# --- CSS FOR MOBILE ---
st.markdown("""
    <style>
    div.stButton > button {
        height: 4em;
        font-size: 20px !important;
        font-weight: bold;
        border-radius: 15px;
        background-color: #f0f2f6;
    }
    h1 { text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- THE iOS AUDIO FIX ---
def play_audio(text):
    """Generates audio and forces it to play using a fresh JS injection."""
    tts = gTTS(text=text, lang='en')
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    b64 = base64.b64encode(mp3_fp.getvalue()).decode()
    
    # We use a unique key based on the current time to force the browser 
    # to treat this as a brand-new user-initiated event.
    unique_key = f"audio_{int(time.time() * 1000)}"
    
    components.html(
        f"""
        <div id="{unique_key}"></div>
        <script>
            var audio = new Audio("data:audio/mp3;base64,{b64}");
            audio.play().catch(function(error) {{
                console.log("iOS blocked autoplay. Ensuring user gesture is recognized.");
            }});
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
    st.header("Settings")
    max_words = st.number_input("Words per test", min_value=1, value=10)
    randomize = st.checkbox("Randomize List", value=True)
    if st.button("🗑️ Clear and Start New Scan"):
        st.session_state.test_list = []
        st.session_state.current_index = 0
        st.rerun()

# 1. SCANNING
if not st.session_state.test_list:
    st.write("### 📸 Scan your word list")
    image_file = st.file_uploader("Upload or Take Photo", type=['png', 'jpg', 'jpeg', 'heic'])

    if image_file:
        # The iPhone Fix: Convert to RGB to clear metadata
        img = Image.open(image_file).convert("RGB")
        st.image(img, width=300)
        
        if st.button("📝 Load Words"):
            with st.spinner("Reading words..."):
                text = pytesseract.image_to_string(img)
                extracted = [line.strip() for line in text.split('\n') if len(line.strip()) > 1]
                
                if extracted:
                    if randomize:
                        random.shuffle(extracted)
                    st.session_state.test_list = extracted[:max_words]
                    st.rerun()
                else:
                    st.error("No words found. Ensure the photo is clear and bright.")

# 2. TESTING
else:
    word = st.session_state.test_list[st.session_state.current_index]
    
    st.write(f"**Word {st.session_state.current_index + 1} of {len(st.session_state.test_list)}**")
    
    # Audio Button
    if st.button("🔊 READ ALOUD"):
        play_audio(word)
        
    st.divider()
    
    # Reveal Logic
    if st.button("👁️ SHOW SPELLING"):
        st.session_state.revealed = True
        st.rerun()

    if st.session_state.revealed:
        st.markdown(f"<h1>{word}</h1>", unsafe_allow_html=True)
    else:
        st.markdown("<h1 style='color: #ccc;'>????</h1>", unsafe_allow_html=True)

    st.divider()

    # Navigation
    if st.button("NEXT WORD ➡️"):
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
                
