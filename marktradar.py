import streamlit as st
import requests
from bs4 import BeautifulSoup

st.title("MARKTRADAR – CLOUD MULTIPLIER OS")

# Sicherer Key-Zugriff
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("Fehler: API-Key fehlt in den Secrets!")
    st.stop()

# Deine Analyse-Funktion
def extrahiere_webseiten_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        return text[:3000]
    except Exception as e:
        return f"Fehler: {e}"

# UI-Elemente
link = st.text_input("Auktions-Link hinzufügen:")
if st.button("Cloud-KI Analyse starten"):
    if link:
        st.write("Analyse läuft...")
        text = extrahiere_webseiten_text(link)
        st.write("Text extrahiert, KI-Analyse startet nun...")
        # Hier würde jetzt dein API-Aufruf an Groq folgen
    else:
        st.warning("Bitte gib einen Link ein.")
