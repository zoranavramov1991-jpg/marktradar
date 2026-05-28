import streamlit as st
from groq import Groq
import base64

# --- SEITEN-KONFIGURATION ---
st.set_page_config(page_title="MarktRadar OS Ultimate", layout="wide")
st.title("⚡ MARKTRADAR – ULTIMATE CONTROL")

# 1. API-Key laden
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("API-Key fehlt in den Secrets!")
    st.stop()

# 2. UI-EINSTELLUNGEN
col1, col2 = st.columns(2)
with col1:
    # Hier kannst du das Modell ändern, wenn es nicht mehr existiert!
    model_input = st.text_input("Modell-Name (z.B. llama-3.3-70b-versatile):", value="llama-3.3-70b-versatile")
with col2:
    defekt_prozent = st.slider("Schrott-Regler (%):", 0, 100, 20)

link = st.text_input("Auktions-Link:")
uploaded_files = st.file_uploader("Artikelbilder hochladen:", accept_multiple_files=True)

# 3. ANALYSE-LOGIK
if st.button("🚀 ANALYSE STARTEN"):
    if not GROQ_API_KEY:
        st.error("API-Key nicht gefunden.")
    else:
        with st.spinner("Experten-Analyse läuft..."):
            try:
                client = Groq(api_key=GROQ_API_KEY)
                
                prompt_text = (
                    f"Du bist ein unerbittlicher Gutachter für Resale-Ware. Schrott-Anteil: {defekt_prozent}%.\n"
                    f"Analysiere den Posten basierend auf dem Link: {link}.\n"
                    f"Erstelle eine Tabelle: [Artikel] | [Zustand] | [Flohmarkt-Preis (Min)] | [Sicherheits-Gebot].\n"
                    f"Nenne das absolute Maximalgebot für den gesamten Posten und 3 Risiken."
                )

                # Vorbereitung der Nachricht
                if uploaded_files:
                    # Multimodal-Modus
                    messages = [{"role": "user", "content": [{"type": "text", "text": prompt_text}]}]
                    for f in uploaded_files:
                        f.seek(0)
                        b64 = base64.b64encode(f.read()).decode('utf-8')
                        messages[0]["content"].append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                        })
                else:
                    # Text-Modus (einfacher String)
                    messages = [{"role": "user", "content": prompt_text}]

                # API-Aufruf
                response = client.chat.completions.create(
                    model=model_input,
                    messages=messages
                )
                
                st.success("Erfolg!")
                st.write(response.choices[0].message.content)

            except Exception as e:
                st.error(f"Fehler: {e}")
                st.info("Tipp: Wenn 'model_not_found' erscheint, ändere den Namen im Feld oben (z.B. auf 'llama-3.3-70b-versatile').")
