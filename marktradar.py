import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq

# 1. Layout & Konfiguration
st.set_page_config(page_title="MarktRadar OS")
st.title("MARKTRADAR – CLOUD MULTIPLIER OS")

# 2. Sicherer Key-Zugriff
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("Fehler: API-Key fehlt in den Secrets!")
    st.stop()

# 3. Hilfsfunktion
def extrahiere_webseiten_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Skripte und Styles entfernen für sauberen Text
        for script in soup(["script", "style"]):
            script.extract()
        return soup.get_text()[:2000] # Begrenzung auf 2000 Zeichen
    except Exception as e:
        return f"Fehler: {e}"

# 4. UI & KI-Logik
link = st.text_input("Auktions-Link hinzufügen:")

if st.button("Cloud-KI Analyse starten"):
    if link:
        with st.spinner("Analyse läuft..."):
            text = extrahiere_webseiten_text(link)
            
            client = Groq(api_key=GROQ_API_KEY)
            
            prompt = f"Analysiere diese Auktionsbeschreibung und nenne das Umsatzpotenzial: {text}"
            
            response = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": prompt}]
            )
            
            st.success(response.choices[0].message.content)
    else:
        st.warning("Bitte gib einen Link ein.")
