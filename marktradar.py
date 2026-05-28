import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq

# 1. Konfiguration & Key
st.title("MARKTRADAR – CLOUD MULTIPLIER OS")
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

# 2. Funktion definieren
def extrahiere_webseiten_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()[:3000]
    except Exception as e:
        return f"Fehler: {e}"

# 3. Layout und Button (Hier passiert die Magie)
link = st.text_input("Auktions-Link hinzufügen:")

if st.button("Cloud-KI Analyse starten"):
    if link:
        st.write("Analyse läuft...")
        text = extrahiere_webseiten_text(link)
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": f"Analysiere diese Auktion: {text}"}]
        )
        st.success(response.choices[0].message.content)
    else:
        st.warning("Bitte gib einen Link ein.")
