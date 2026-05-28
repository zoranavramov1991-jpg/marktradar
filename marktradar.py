import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq

st.set_page_config(page_title="MarktRadar OS")
st.title("MARKTRADAR – CLOUD MULTIPLIER OS")

# 1. Key prüfen
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception as e:
    st.error("Fehler: API-Key fehlt in den Secrets!")
    st.stop()

# 2. Text extrahieren
def extrahiere_webseiten_text(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        return soup.get_text()[:1500] 
    except Exception as e:
        return f"System-Fehler: {e}"

# 3. Layout & Abfrage
link = st.text_input("Auktions-Link hinzufügen:")

if st.button("Cloud-KI Analyse starten"):
    if link:
        with st.spinner("Analyse läuft..."):
            
            # Schritt A: Text holen
            text = extrahiere_webseiten_text(link)
            st.info(f"Vorschau des geladenen Textes: {text[:100]}...") # Zeigt uns, ob die Seite blockiert!
            
            # Schritt B: Groq zwingen, den wahren Fehler zu verraten
            try:
                client = Groq(api_key=GROQ_API_KEY)
                prompt = f"Analysiere diese Auktion kurz und knapp: {text}"
                
                response = client.chat.completions.create(
                    model="llama3-8b-8192",
                    messages=[{"role": "user", "content": prompt}]
                )
                st.success(response.choices[0].message.content)
                
            except Exception as e:
                # Hier decken wir den wahren Fehler auf!
                st.error(f"Der wahre Groq-Fehler lautet: {e}")
    else:
        st.warning("Bitte gib einen Link ein.")
