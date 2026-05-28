import streamlit as st
from groq import Groq
import base64

st.set_page_config(page_title="MarktRadar OS Fix", layout="wide")
st.title("⚡ MARKTRADAR – FINALE STABILISIERUNG")

# 1. API-Key
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("API-Key fehlt!")
    st.stop()

# 2. UI
col1, col2 = st.columns(2)
with col1:
    model_input = st.text_input("Modell (für Text: llama-3.3-70b-versatile):", value="llama-3.3-70b-versatile")
with col2:
    defekt_prozent = st.slider("Schrott-Regler (%):", 0, 100, 20)

uploaded_files = st.file_uploader("Artikelbilder hochladen:", accept_multiple_files=True)

# 3. Logik
if st.button("🚀 ANALYSE STARTEN"):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        prompt_text = f"Analysiere diesen Posten (Schrott: {defekt_prozent}%). Tabelle: [Artikel]|[Zustand]|[Preis]|[Gebot]. Nenne Maximalgebot und 3 Risiken."

        # ABSOLUTE TRENNUNG DER LOGIK
        if uploaded_files:
            # PFAD A: BILDER VORHANDEN (Erwartet Listen-Struktur)
            st.info("Sende Bilder an die API...")
            content = [{"type": "text", "text": prompt_text}]
            for f in uploaded_files:
                f.seek(0)
                b64 = base64.b64encode(f.read()).decode('utf-8')
                content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
            
            messages = [{"role": "user", "content": content}]
        else:
            # PFAD B: KEINE BILDER (Erwartet REINEN STRING - der Fehler-Killer!)
            st.info("Sende nur Text an die API...")
            messages = [{"role": "user", "content": prompt_text}]

        # Aufruf
        response = client.chat.completions.create(
            model=model_input,
            messages=messages
        )
        st.write(response.choices[0].message.content)

    except Exception as e:
        st.error(f"Fehler: {e}")
