import streamlit as st
from groq import Groq
import base64

st.set_page_config(page_title="MarktRadar OS Final", layout="wide")
st.title("⚡ MARKTRADAR – AUTOPILOT-VERSION")

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
    with st.spinner("Modell wird gesucht & Experten-Analyse läuft..."):
        try:
            client = Groq(api_key=GROQ_API_KEY)
            
            # --- DYNAMISCHE MODELL-SUCHE ---
            # Wir holen uns die Liste der verfügbaren Modelle
            all_models = client.models.list()
            model_ids = [m.id for m in all_models.data]
            
            # Suche nach einem Vision-Modell, falls Bilder da sind
            selected_model = "llama-3.3-70b-versatile" # Default
            if uploaded_files:
                # Suche nach Modellen, die 'vision' im Namen haben
                vision_models = [m for m in model_ids if "vision" in m]
                if vision_models:
                    selected_model = vision_models[0] # Nimm das erste gefundene Vision-Modell
            
            st.info(f"Verwendetes Modell: {selected_model}")

            # --- PROMPT & CONTENT ---
            prompt_text = (
                f"Du bist ein Gutachter für Resale-Ware. Schrott-Anteil: {defekt_prozent}%.\n"
                f"Analysiere die Daten extrem konservativ.\n"
                f"Erstelle eine Tabelle: [Artikel] | [Zustand] | [Flohmarkt-Preis (Min)] | [Sicherheits-Gebot].\n"
                f"Nenne das absolute Maximalgebot für den gesamten Posten und 3 Risiken."
            )
            
            # Die sicherste Struktur für die API
            message_content = [{"type": "text", "text": prompt_text}]
            
            if uploaded_files:
                for f in uploaded_files:
                    f.seek(0)
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                    message_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                    })

            # API-Aufruf mit dem dynamisch gewählten Modell
            response = client.chat.completions.create(
                model=selected_model,
                messages=[{"role": "user", "content": message_content}]
            )
            
            st.success("Analyse erfolgreich!")
            st.write(response.choices[0].message.content)
            
        except Exception as e:
            st.error(f"Fehler: {e}")
            st.info("Wenn das Problem weiterhin besteht, lade bitte keine Bilder hoch, um die Vision-Modelle zu umgehen.")
