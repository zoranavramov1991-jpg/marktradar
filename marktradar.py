import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
import base64

st.set_page_config(page_title="MarktRadar OS v5.0", layout="wide")
st.title("⚡ MARKTRADAR – ANALYTISCHER ANKAUFS-PRÜFER")

# API-Key laden
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("API-Key fehlt!")
    st.stop()

# ... (Web-Scraping Funktion bleibt gleich) ...
def extrahiere_webseiten_text(url):
    if not url: return "Kein Link."
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()[:3000]
    except: return "Scraping-Fehler."

# UI
col1, col2 = st.columns([1, 1])
with col1:
    link = st.text_input("Auktions-Link:")
    defekt_prozent = st.slider("Schrott-Regler (%):", 0, 100, 20)
    risiko_faktor = st.select_slider("Strenge-Faktor:", options=["Normal", "Streng", "Absolut Unerbittlich"], value="Absolut Unerbittlich")
    gegenstaende = st.text_area("Artikelliste:")
with col2:
    uploaded_files = st.file_uploader("Artikelbilder:", accept_multiple_files=True)

if st.button("🚀 ANALYSE STARTEN"):
    web_text = extrahiere_webseiten_text(link)
    
    # NEUER PROMPT: Fokus auf Mathematik statt Schätzung
    prompt = f"""
    Du bist ein Experte für Gebrauchtwaren-Ankauf. Deine Aufgabe ist die Risikominimierung.
    Strenge: {risiko_faktor}.

    Regeln für die Berechnung:
    1. Gehe bei jedem Artikel vom niedrigsten jemals erzielten Verkaufspreis aus (Flohmarkt-Niveau).
    2. Wenn ein Artikel eine unbekannte Marke oder unklarer Zustand ist -> Wert = 0.
    3. Abzug: Vom Flohmarkt-Wert ziehst du {defekt_prozent}% für das Ausfallrisiko ab.
    4. Ziel: Berechne den 'Sicheren Ankaufs-Maximalwert', bei dem ich bei jedem Teil eine Marge von mindestens 30% erziele.

    Erstelle die Tabelle:
    [Artikel] | [Zustand] | [Flohmarkt-Preis (Basis)] | [Mein Sicherheits-Gebot] | [Kanal-Empfehlung]

    Am Ende:
    - Summe aller Sicherheits-Gebote = Absolutes Maximalgebot für den gesamten Posten.
    - Liste die 3 'Todes-Faktoren' auf, die diesen Deal ruinieren könnten.
    """
    
    # ... (Rest der Logik wie bisher) ...
    client = Groq(api_key=GROQ_API_KEY)
    # ... (Modell-Auswahl und Request) ...
    # (Stelle sicher, dass der restliche Code hier korrekt eingefügt ist)
