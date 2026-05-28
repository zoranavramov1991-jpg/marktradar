import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
import base64

st.set_page_config(page_title="MarktRadar OS v6.0", layout="wide")
st.title("⚡ MARKTRADAR – DIREKT-ANALYSE")

# 1. API-Key laden
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("API-Key fehlt!")
    st.stop()

# 2. UI
link = st.text_input("Auktions-Link:")
defekt_prozent = st.slider("Schrott-Regler (%):", 0, 100, 20)
uploaded_files = st.file_uploader("Bilder:", accept_multiple_files=True)

# 3. Analyse starten
if st.button("🚀 ANALYSE JETZT STARTEN"):
    with st.spinner("Verbinde zu Groq..."):
        try:
            client = Groq(api_key=GROQ_API_KEY)
            
            # Prompt direkt hier definieren
            prompt = f"Analysiere diesen Artikel-Posten (Schrott-Anteil {defekt_prozent}%). Erstelle eine Tabelle mit Flohmarkt-Preis, Sicherheits-Gebot und Kanal-Empfehlung. Sei extrem konservativ."
            
            # Message-Payload vorbereiten
            messages = [{"role": "user", "content": prompt}]
            
            # Falls Bilder da sind, anfügen
            if uploaded_files:
                for f in uploaded_files:
                    f.seek(0)
                    b64 = base64.b64encode(f.read()).decode('utf-8')
                    messages.append({"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]})

            # DIREKT auf ein stabiles Modell schießen (ohne Suche)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=messages
            )
            
            st.success("Analyse erfolgreich!")
            st.write(response.choices[0].message.content)
            
        except Exception as e:
            st.error(f"Fehler: {str(e)}")
