import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq

st.set_page_config(page_title="MarktRadar OS")
st.title("MARKTRADAR – CLOUD MULTIPLIER OS")

# 1. Key aus den Secrets laden
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception as e:
    st.error("Fehler: API-Key fehlt in den Secrets!")
    st.stop()

# 2. Funktion zum Auslesen der Webseite
def extrahiere_webseiten_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Unnötigen HTML-Code entfernen
        for script in soup(["script", "style"]):
            script.extract()
        return soup.get_text()[:2000] # Sicherer Puffer für die Textlänge
    except Exception as e:
        return f"System-Fehler beim Laden: {e}"

# 3. Benutzeroberfläche & KI-Logik
link = st.text_input("Auktions-Link hinzufügen:")

if st.button("Cloud-KI Analyse starten"):
    if link:
        with st.spinner("Analyse läuft..."):
            
            # Text von der Webseite holen
            text = extrahiere_webseiten_text(link)
            
            try:
                client = Groq(api_key=GROQ_API_KEY)
                prompt = f"Analysiere diese Auktionsbeschreibung und nenne das Umsatzpotenzial: {text}"
                
                # Hier nutzen wir jetzt das aktuelle, unterstützte Llama 3.1 Modell!
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "user", "content": prompt}]
                )
                st.success(response.choices[0].message.content)
                
            except Exception as e:
                st.error(f"Groq-Fehler: {e}")
    else:
        st.warning("Bitte gib einen Link ein.")
