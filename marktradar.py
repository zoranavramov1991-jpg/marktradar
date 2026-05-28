import streamlit as st
from groq import Groq
import base64

st.set_page_config(page_title="MarktRadar OS Final", layout="wide")
st.title("⚡ MARKTRADAR – STABILE VERSION")

# API-Key laden
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("API-Key fehlt!")
    st.stop()

link = st.text_input("Auktions-Link:")
defekt_prozent = st.slider("Schrott-Regler (%):", 0, 100, 20)
uploaded_files = st.file_uploader("Artikelbilder hochladen:", accept_multiple_files=True)

if st.button("🚀 EXPERTEN-ANALYSE STARTEN"):
    with st.spinner("Sachverständige prüfen..."):
        try:
            client = Groq(api_key=GROQ_API_KEY)
            
            # --- NEUES MODELL ---
            # Wir versuchen es mit dem aktuellen 90B Vision Modell
            model_to_use = "llama-3.2-90b-vision-preview"
            
            prompt_text = (
                f"Du bist ein unerbittlicher Gutachter für Resale-Ware. Schrott-Anteil: {defekt_prozent}%.\n"
                f"Analysiere die Daten extrem konservativ.\n"
                f"Erstelle eine Tabelle: [Artikel] | [Zustand] | [Flohmarkt-Preis (Min)] | [Sicherheits-Gebot].\n"
                f"Nenne das absolute Maximalgebot für den gesamten Posten und 3 Risiken."
            )
            
            # Content aufbauen
            message_content = [{"type": "text", "text": prompt_text}]
            
            if uploaded_files:
                for f in uploaded_files:
                    f.seek(0)
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                    message_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                    })

            # API-Aufruf
            response = client.chat.completions.create(
                model=model_to_use,
                messages=[{"role": "user", "content": message_content}]
            )
            
            st.success("Analyse erfolgreich!")
            st.write(response.choices[0].message.content)
            
        except Exception as e:
            st.error(f"Fehler: {e}")
            st.info("Tipp: Wenn das Modell nicht gefunden wird, versuche die Analyse OHNE Bilder hochzuladen.")
