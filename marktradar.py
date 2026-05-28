import streamlit as st
from groq import Groq
import base64

# --- SEITEN-KONFIGURATION ---
st.set_page_config(page_title="MarktRadar OS Stabil", layout="wide")
st.title("⚡ MARKTRADAR – EXPERTEN-ANALYSE")

# API-Key laden
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("API-Key fehlt in den Secrets!")
    st.stop()

# UI-Elemente
link = st.text_input("Auktions-Link:")
defekt_prozent = st.slider("Schrott-Regler (%):", 0, 100, 20)
uploaded_files = st.file_uploader("Artikelbilder hochladen:", accept_multiple_files=True)

# Analyse
if st.button("🚀 ANALYSE STARTEN"):
    with st.spinner("Sachverständige prüfen..."):
        try:
            client = Groq(api_key=GROQ_API_KEY)
            
            # --- DER PROMPT ---
            prompt_text = (
                f"Du bist ein unerbittlicher Gutachter für Resale-Ware. Schrott-Anteil: {defekt_prozent}%.\n"
                f"Analysiere die Bilder und den Kontext extrem konservativ.\n"
                f"Erstelle eine Tabelle: [Artikel] | [Zustand] | [Flohmarkt-Preis (Min)] | [Sicherheits-Gebot].\n"
                f"Nenne das absolute Maximalgebot für den gesamten Posten und 3 Gründe für ein Scheitern."
            )
            
            # --- DIE KONSTRUKTION DER MESSAGES ---
            # WICHTIG: Wir bauen die Nachricht explizit so auf, wie die API sie will
            messages = [{"role": "user", "content": [{"type": "text", "text": prompt_text}]}]
            
            # Bilder als Anhänge zur Content-Liste hinzufügen
            if uploaded_files:
                for f in uploaded_files:
                    f.seek(0)
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                    messages[0]["content"].append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                    })
            
            # API-Aufruf
            response = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview", # Spezielles Vision-Modell
                messages=messages
            )
            
            st.success("Analyse abgeschlossen.")
            st.write(response.choices[0].message.content)
            
        except Exception as e:
            st.error(f"Ein technischer Fehler ist aufgetreten: {e}")
            st.info("Hinweis: Wenn dies weiterhin auftritt, versuche es bitte OHNE Bilder hochzuladen.")
