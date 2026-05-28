import streamlit as st
from groq import Groq
import base64

st.set_page_config(page_title="MarktRadar OS v6.1", layout="wide")
st.title("⚡ MARKTRADAR – STABILE ANALYSE")

# API-Key laden
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("API-Key fehlt!")
    st.stop()

link = st.text_input("Auktions-Link:")
defekt_prozent = st.slider("Schrott-Regler (%):", 0, 100, 20)
uploaded_files = st.file_uploader("Bilder:", accept_multiple_files=True)

if st.button("🚀 ANALYSE STARTEN"):
    with st.spinner("Analysiere..."):
        try:
            client = Groq(api_key=GROQ_API_KEY)
            
            # Aufbau der Content-Liste
            content_list = []
            
            # 1. Text-Prompt hinzufügen
            prompt_text = f"Analysiere diesen Posten (Schrott-Anteil {defekt_prozent}%). Erstelle eine Tabelle mit Flohmarkt-Preis, Sicherheits-Gebot und Kanal-Empfehlung. Sei extrem konservativ."
            content_list.append({"type": "text", "text": prompt_text})
            
            # 2. Bilder hinzufügen (korrektes Format für die API)
            if uploaded_files:
                for f in uploaded_files:
                    f.seek(0)
                    b64 = base64.b64encode(f.read()).decode('utf-8')
                    content_list.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                    })

            # API-Aufruf
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=[{"role": "user", "content": content_list}]
            )
            
            st.success("Analyse erfolgreich!")
            st.write(response.choices[0].message.content)
            
        except Exception as e:
            st.error(f"Fehler bei der Anfrage: {e}")
