import streamlit as st
from groq import Groq
import base64

# --- SEITEN-KONFIGURATION ---
st.set_page_config(page_title="MarktRadar OS Unbreakable", layout="wide")
st.title("⚡ MARKTRADAR – UNBREAKABLE VERSION")

# 1. API-Key laden
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("API-Key fehlt!")
    st.stop()

# 2. UI
link = st.text_input("Auktions-Link:")
defekt_prozent = st.slider("Schrott-Regler (%):", 0, 100, 20)
uploaded_files = st.file_uploader("Artikelbilder hochladen:", accept_multiple_files=True)

# 3. Logik mit SELBSTHEILUNG
if st.button("🚀 EXPERTEN-ANALYSE STARTEN"):
    with st.spinner("Analyse läuft..."):
        try:
            client = Groq(api_key=GROQ_API_KEY)
            prompt_text = (
                f"Du bist ein unerbittlicher Gutachter für Resale-Ware. Schrott-Anteil: {defekt_prozent}%.\n"
                f"Erstelle eine Tabelle: [Artikel] | [Zustand] | [Flohmarkt-Preis (Min)] | [Sicherheits-Gebot].\n"
                f"Nenne das absolute Maximalgebot für den gesamten Posten und 3 Risiken."
            )
            
            # Modelle definieren
            vision_model = "llama-3.2-11b-vision-instruct"
            text_model = "llama-3.3-70b-versatile"
            
            messages = []
            final_model = text_model # Default
            
            # Bilder-Logik
            if uploaded_files:
                content_list = [{"type": "text", "text": prompt_text}]
                for f in uploaded_files:
                    f.seek(0)
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                    content_list.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                    })
                messages = [{"role": "user", "content": content_list}]
                final_model = vision_model
            else:
                messages = [{"role": "user", "content": prompt_text}]
                final_model = text_model

            # VERSUCH 1: Vision-Modell (falls Bilder da sind)
            try:
                response = client.chat.completions.create(model=final_model, messages=messages)
                st.success("Analyse erfolgreich!")
                st.write(response.choices[0].message.content)
            
            # FALLBACK: Falls Vision scheitert, nutze Text-Modell
            except Exception as e:
                st.warning("Vision-Modell nicht verfügbar. Wechsle auf reinen Text-Modus...")
                response = client.chat.completions.create(
                    model=text_model, 
                    messages=[{"role": "user", "content": prompt_text}]
                )
                st.write("*(Hinweis: Analyse erfolgte ohne Bild-Support, da Vision-Modell nicht aktiv)*")
                st.write(response.choices[0].message.content)

        except Exception as e:
            st.error(f"Kritischer Fehler: {e}")
