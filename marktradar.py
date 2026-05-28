import streamlit as st
import requests
from bs4 import BeautifulSoup
import json

# Der Key wird jetzt automatisch aus deinem Streamlit-Secrets-Tresor geholt!
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("Fehler: Du hast deinen Groq API-Key noch nicht im Bereich 'Secrets' in den App-Einstellungen hinterlegt!")
    st.stop()

# Funktion für den Webseiten-Text
def extrahiere_webseiten_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            sauberer_text = '\n'.join(chunk for chunk in chunks if chunk)
            return sauberer_text[:3000]
    except Exception as e:
        return f"Fehler beim Laden: {e}"

# Dein restlicher Code (Layout, Button, etc.) folgt hier...
# (Den Rest deiner Datei kannst du so lassen, wie er ist!)
