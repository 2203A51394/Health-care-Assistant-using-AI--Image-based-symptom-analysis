import streamlit as st
import pandas as pd
from deep_translator import GoogleTranslator
from PIL import Image
import re

# Streamlit page config
st.set_page_config(page_title="AI Health Assistant", page_icon="🤖", layout="wide")

# Load dataset
df = pd.read_csv("dataset - Sheet1.csv")
df.fillna("", inplace=True)

# ✅ Auto-detect column names and rename
rename_map = {}
for col in df.columns:
    col_lower = col.strip().lower()
    if "disease" in col_lower or "illness" in col_lower or "symptom" in col_lower:
        rename_map[col] = "disease"
    elif "cure" in col_lower or "treatment" in col_lower or "medicine" in col_lower:
        rename_map[col] = "cure"
    elif "category" in col_lower or "type" in col_lower or "severity" in col_lower:
        rename_map[col] = "category"
df.rename(columns=rename_map, inplace=True)

# ✅ Validate essential columns
if "disease" not in df.columns or "cure" not in df.columns:
    st.error("❌ Your dataset must contain the following columns: 'disease' and 'cure'. Please check your CSV.")
    st.stop()

# Normalize data
df['disease'] = df['disease'].astype(str).str.strip().str.lower()
if 'category' not in df.columns:
    df['category'] = "neutral"

# Translation helper
def translate(text, src, dest):
    try:
        return GoogleTranslator(source=src, target=dest).translate(text)
    except:
        return text

# Language selector
lang_codes = {"English": "en", "Telugu": "te", "Hindi": "hi"}
language = st.selectbox("Choose your language:", list(lang_codes.keys()))
selected_lang_code = lang_codes[language]

# CSS Styling
st.markdown("""
<style>
.chat-bubble { padding:10px; margin:8px; border-radius:10px; max-width:70%; }
.user-bubble { background:#d1e7dd; margin-left:auto; }
.bot-bubble { color:white; }
</style>
""", unsafe_allow_html=True)

# Dummy image-based prediction
def predict_disease(image):
    return "fever"

# Disease Matcher
def get_advice(user_input):
    user_input = user_input.lower().strip()
    words = re.findall(r'\w+', user_input)
    disease_scores = []

    for _, row in df.iterrows():
        disease_text = row['disease']
        cure = row['cure']
        category = row['category']
        score = sum(1 for word in words if word in disease_text)
        if score > 0:
            disease_scores.append((score, cure, category))

    if disease_scores:
        disease_scores.sort(reverse=True, key=lambda x: x[0])
        cure_text, category = disease_scores[0][1], disease_scores[0][2]
        formatted = "<br>".join([f"• {c.strip()}" for c in cure_text.split('|')])
        return formatted, category

    return "❌ I don't have information about that. Please consult a doctor.", "neutral"

# Chat storage
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("🤖 AI Health Assistant")
st.write("Ask about your symptoms or upload an image 🩺")

user_input = st.text_input("Type your question:")
uploaded_file = st.file_uploader("Upload an image (optional):", type=["jpg", "jpeg", "png"])

if user_input or uploaded_file:
    combined_response = ""
    category = "neutral"

    if user_input:
        input_eng = translate(user_input, selected_lang_code, "en") if language != "English" else user_input
        text_res, category = get_advice(input_eng)
        if language != "English":
            text_res = translate(text_res, "en", selected_lang_code)
        st.session_state.messages.append({"role": "user", "text": user_input})
        combined_response += f"From your text: {text_res}"

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, caption="Uploaded Image", use_column_width=True)
        predicted = predict_disease(img)
        img_res, category = get_advice(predicted)
        if language != "English":
            img_res = translate(img_res, "en", selected_lang_code)
        combined_response += f"<br>From your image: {img_res}"

    st.session_state.messages.append({"role": "bot", "text": combined_response, "category": category})

# Color mapping
category_colors = {
    "fever": "#ff6b6b", "mild": "#ffb74d", "wellness": "#4caf50", "neutral": "#607d8b"
}

# Display chat UI
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"<div class='chat-bubble user-bubble'>🧑‍💻 {msg['text']}</div>", unsafe_allow_html=True)
    else:
        color = category_colors.get(msg["category"], "#607d8b")
        st.markdown(f"<div class='chat-bubble bot-bubble' style='background:{color};'>🤖 {msg['text']}</div>", unsafe_allow_html=True)
