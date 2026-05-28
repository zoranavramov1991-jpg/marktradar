import streamlit as st
from groq import Groq
import base64

# --- KONFIGURATION ---
st.set_page_config(page_title="MarktRadar OS", layout="wide")
st.title("⚡ MARKTRADAR")

# 1. API-Key laden
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("API-Key fehlt in den Secrets!")
    st.stop()

# 2. UI-ELEMENTE
col1, col2 = st.columns([1, 1])
with col1:
    link = st.text_input("Auktions-Link:")
with col2:
    defekt_prozent = st.slider("Schrott-Regler (%):", 0, 100, 20)

uploaded_files = st.file_uploader("Artikelbilder hochladen:", accept_multiple_files=True)

# 3. ANALYSE-LOGIK
if st.button("🚀 ANALYSE STARTEN"):
    if not GROQ_API_KEY:
        st.error("API-Key fehlt.")
    else:
        with st.spinner("Analyse läuft..."):
            try:
                client = Groq(api_key=GROQ_API_KEY)
                prompt = (
                    f"Du bist Gutachter für Resale-Ware. Schrott-Anteil: {defekt_prozent}%.\n"
                    f"Link: {link}.\n"
                    f"Erstelle eine Tabelle: [Artikel] | [Zustand] | [Flohmarkt-Preis] | [Sicherheits-Gebot].\n"
                    f"Nenne das absolute Maximalgebot und 3 Risiken."
                )

                # --- DER TRICK GEGEN DEN FEHLER ---
                if uploaded_files:
                    # BILD-MODUS: Erfordert zwingend eine Liste von Objekten
                    model = "llama-3.2-11b-vision-instruct"
                    content = [{"type": "text", "text": prompt}]
                    
                    for f in uploaded_files:
                        f.seek(0)
                        b64 = base64.b64encode(f.read()).decode('utf-8')
                        content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                        })
                    
                    messages = [{"role": "user", "content": content}]
                else:
                    # TEXT-MODUS: Erfordert zwingend einen EINFACHEN STRING
                    model = "llama-3.3-70b-versatile"
                    messages = [{"role": "user", "content": prompt}]

                # API-Aufruf
                response = client.chat.completions.create(
                    model=model,
                    messages=messages
                )
                
                st.success("Analyse erfolgreich!")
                st.write(response.choices[0].message.content)

            except Exception as e:
                st.error(f"Fehler: {e}")
                st.info("Hinweis: Falls hier 'model_not_found' steht, unterstützt dein Key das Vision-Modell nicht. Bitte versuche die Analyse ohne Bilder.")
