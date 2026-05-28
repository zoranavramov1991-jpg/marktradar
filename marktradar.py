import streamlit as st
from groq import Groq
import base64

st.set_page_config(page_title="MarktRadar OS v6.2", layout="wide")
st.title("⚡ MARKTRADAR – EXPERTEN-ANALYSE PRO")

# 1. API-Key laden
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("API-Key fehlt in den Secrets!")
    st.stop()

# 2. UI Elemente
link = st.text_input("Auktions-Link:")
defekt_prozent = st.slider("Schrott-Regler (% der Ware unbrauchbar):", 0, 100, 20)
uploaded_files = st.file_uploader("Artikelbilder hochladen:", accept_multiple_files=True)

# 3. Analyse Logik
if st.button("🚀 EXPERTEN-ANALYSE STARTEN"):
    with st.spinner("Sachverständige prüfen Marktdaten..."):
        try:
            client = Groq(api_key=GROQ_API_KEY)
            
            # --- DER PROMPT (Optimiert für Experten-Strenge) ---
            expert_prompt = (
                f"Du bist ein unerbittlicher Gutachter für Resale-Ware. Deine Aufgabe: Schütze mich vor Verlusten.\n"
                f"Schrott-Anteil des Postens: {defekt_prozent}%.\n"
                f"Analysiere die Bilder und den Kontext extrem konservativ.\n\n"
                f"AUFGABE:\n"
                f"1. Erstelle eine Tabelle: [Artikel] | [Zustand] | [Flohmarkt-Preis (Minimum)] | [Sicherheits-Gebot].\n"
                f"2. Berechne den 'SICHEREN ANKAUFS-WERT': Marktpreis minus 70% Risiko-Abschlag.\n"
                f"3. Nenne das absolute Maximalgebot für den gesamten Posten.\n"
                f"4. Nenne die 3 größten Risiken, warum dieser Deal scheitern könnte."
            )
            
            # --- KORREKTES FORMAT FÜR MULTIMODALE ANFRAGEN ---
            # Wir bauen den content IMMER als Liste auf, um den 'must be string' Fehler zu vermeiden
            message_content = [{"type": "text", "text": expert_prompt}]
            
            if uploaded_files:
                for f in uploaded_files:
                    f.seek(0)
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                    message_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                    })

            # API-Aufruf mit dem korrekten Format
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": message_content}]
            )
            
            st.success("Analyse erfolgreich abgeschlossen.")
            st.markdown("---")
            st.write(response.choices[0].message.content)
            
        except Exception as e:
            st.error(f"Ein technischer Fehler ist aufgetreten: {e}")
            st.info("Tipp: Überprüfe, ob deine Bilder korrekt geladen wurden.")
