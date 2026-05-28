import streamlit as st
from groq import Groq

# 1. Layout
st.set_page_config(page_title="MarktRadar Basis", layout="centered")
st.title("⚡ MARKTRADAR (Basis-Modus)")

# 2. Eingaben
link = st.text_input("Auktions-Link:")
defekt_prozent = st.slider("Schrott-Regler (%):", 0, 100, 20)

# 3. Logik
if st.button("🚀 ANALYSE STARTEN"):
    try:
        # Initialisierung
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        
        prompt = (
            f"Du bist ein Gutachter für Resale-Ware. Schrott-Anteil: {defekt_prozent}%.\n"
            f"Analysiere den Link: {link}.\n"
            f"Erstelle eine Tabelle: Artikel | Zustand | Flohmarkt-Preis | Sicherheits-Gebot.\n"
            f"Nenne das Maximalgebot und 3 Risiken."
        )

        # API-Aufruf (Text-Modus)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        
        st.write(response.choices[0].message.content)
        
    except Exception as e:
        st.error(f"Fehler: {e}")
