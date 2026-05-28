import streamlit as st
from groq import Groq
import base64

# --- SEITE ---
st.set_page_config(page_title="MarktRadar", layout="wide")
st.title("⚡ MARKTRADAR")

# --- INPUTS ---
link = st.text_input("Auktions-Link:")
defekt_prozent = st.slider("Schrott-Regler (%):", 0, 100, 20)
uploaded_files = st.file_uploader("Artikelbilder:", accept_multiple_files=True)

# --- LOGIK ---
if st.button("🚀 ANALYSE STARTEN"):
    try:
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
        prompt = (
            f"Du bist Gutachter für Resale-Ware. Schrott-Anteil: {defekt_prozent}%.\n"
            f"Link: {link}.\n"
            f"Erstelle eine Tabelle mit Spalten: Artikel, Zustand, Preis, Gebot.\n"
            f"Nenne das Maximalgebot und 3 Risiken."
        )

        # Nachricht erstellen
        if uploaded_files:
            # Bild-Modus (Vision)
            model = "llama-3.2-11b-vision-instruct"
            content = [{"type": "text", "text": prompt}]
            for f in uploaded_files:
                f.seek(0)
                b64 = base64.b64encode(f.read()).decode('utf-8')
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })
        else:
            # Text-Modus
            model = "llama-3.3-70b-versatile"
            content = prompt

        # API Aufruf
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": content}]
        )
        
        st.write(response.choices[0].message.content)

    except Exception as e:
        st.error(f"Fehler: {e}")
