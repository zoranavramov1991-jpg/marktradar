import streamlit as st
from groq import Groq
import base64

# --- KONFIGURATION ---
st.set_page_config(page_title="MarktRadar OS Final", layout="wide")
st.title("⚡ MARKTRADAR – STABILE VERSION")

# 1. API-Key laden
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("API-Key fehlt!")
    st.stop()

# 2. UI-Elemente
link = st.text_input("Auktions-Link:")
defekt_prozent = st.slider("Schrott-Regler (%):", 0, 100, 20)
uploaded_files = st.file_uploader("Artikelbilder hochladen:", accept_multiple_files=True)

# 3. Logik
if st.button("🚀 EXPERTEN-ANALYSE STARTEN"):
    with st.spinner("Experten-Analyse läuft..."):
        try:
            client = Groq(api_key=GROQ_API_KEY)
            prompt_text = (
                f"Du bist ein unerbittlicher Gutachter für Resale-Ware. Schrott-Anteil: {defekt_prozent}%.\n"
                f"Erstelle eine Tabelle: [Artikel] | [Zustand] | [Flohmarkt-Preis (Min)] | [Sicherheits-Gebot].\n"
                f"Nenne das absolute Maximalgebot für den gesamten Posten und 3 Risiken."
            )
            
            # --- FALLUNTERSCHEIDUNG ---
            if uploaded_files:
                # VISION-PFAD (Bilder vorhanden)
                # Wir nutzen 'llama-3.2-11b-vision-instruct' (Aktueller Standard)
                model_name = "llama-3.2-11b-vision-instruct"
                
                content_list = [{"type": "text", "text": prompt_text}]
                for f in uploaded_files:
                    f.seek(0)
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                    content_list.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                    })
                messages = [{"role": "user", "content": content_list}]
            else:
                # TEXT-PFAD (Keine Bilder)
                # Wir nutzen 'llama-3.3-70b-versatile' (Der Fels in der Brandung)
                model_name = "llama-3.3-70b-versatile"
                messages = [{"role": "user", "content": prompt_text}]

            # API-Aufruf
            response = client.chat.completions.create(
                model=model_name,
                messages=messages
            )
            
            st.success(f"Analyse erfolgreich mit {model_name}!")
            st.write(response.choices[0].message.content)
            
        except Exception as e:
            st.error(f"Fehler: {e}")
            st.info("TIPP: Wenn hier 'model_decommissioned' steht, ist das Vision-Modell wieder veraltet. Lade in diesem Fall KEINE Bilder hoch, dann nutzt das Tool das stabile Text-Modell.")
