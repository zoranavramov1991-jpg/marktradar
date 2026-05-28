import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
import base64

st.set_page_config(page_title="MarktRadar OS v4.0", layout="wide")
st.title("⚡ MARKTRADAR – EXPERTEN-PREIS-CHECKER PRO")
st.subheader("Echtzeit-Markt-Analyse & Konservative Kalkulation")

# 1. API-Key laden
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception as e:
    st.error("Fehler: API-Key fehlt in den Secrets!")
    st.stop()

# 2. Web-Scraping
def extrahiere_webseiten_text(url):
    if not url: return "Kein Link angegeben."
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]): script.extract()
        return soup.get_text()[:3000]
    except: return "Fehler beim Web-Scraping."

# 3. UI
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📊 Parameter")
    link = st.text_input("Auktions-Link:")
    defekt_prozent = st.slider("Schrott-Regler (% der Ware unbrauchbar):", 0, 100, 10)
    risiko_faktor = st.select_slider("Strenge-Faktor der KI:", options=["Normal", "Streng", "Absolut Unerbittlich"], value="Streng")
    gegenstaende = st.text_area("Zusätzliche Infos / Artikelliste:")

with col2:
    st.markdown("### 📸 Bild-Scan")
    uploaded_files = st.file_uploader("Artikelbilder hochladen:", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

# 4. Analyse
if st.button("🚀 EXPERTEN-CHECK STARTEN"):
    with st.spinner("Sachverständige prüfen Marktdaten und kalkulieren das Sicherheits-Gebot..."):
        web_text = extrahiere_webseiten_text(link)
        
        # PROMPT IST HIER JETZT KORREKT INNERHALB DER LOGIK
        prompt = f"""
        Du bist der Chef-Prüfer für Ankaufs-Risiken. Sei unerbittlich. Strenge-Modus: {risiko_faktor}.
        Wenn auf 'Absolut Unerbittlich' gestellt, streiche alle Artikel aus der Kalkulation, die nicht innerhalb von 14 Tagen garantiert verkauft werden.
        Wenn du Zweifel an einem Artikel hast, bewerte ihn mit 0 €.

        Input:
        - Schrott-Anteil: {defekt_prozent}%
        - Manuelle Infos: {gegenstaende}
        - Web-Daten: {web_text}

        Aufgabe:
        1. Die 'Brutal-Tabelle':
           - Spalten: [Artikel] | [Zustands-Risiko 1-10] | [Verkaufswahrscheinlichkeit] | [SICHERER ANKAUFS-WERT].
           - Berechne den 'SICHERER ANKAUFS-WERT' so: Marktpreis minus 70% Sicherheitsabschlag minus 10% Plattformgebühr.
        2. Liquiditäts-Check: Welche Artikel sind [LAGER-LEICHEN]?
        3. Dein finaler Sparring-Plan:
           - Nenne mir die absolute Obergrenze für das Gebot für den GESAMTEN POSTEN.
           - Formel: Summe aller 'SICHEREN ANKAUFS-WERTE' abzüglich 20% Puffer.
        4. Die 'Todes-Liste': Welche 3 Faktoren lassen diesen Deal scheitern?
        """

        client = Groq(api_key=GROQ_API_KEY)
        
        groq_models = client.models.list()
        all_model_ids = [m.id for m in groq_models.data]
        vision_keywords = ["vision", "scout", "maverick"]
        modelle_zum_testen = [m for m in all_model_ids if any(k in m.lower() for k in vision_keywords)] + \
                             [m for m in all_model_ids if not any(k in m.lower() for k in vision_keywords)]

        content_list = [{"type": "text", "text": prompt}]
        if uploaded_files:
            for f in uploaded_files:
                f.seek(0)
                base64_image = base64.b64encode(f.read()).decode('utf-8')
                content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}})

        for modell in modelle_zum_testen:
            try:
                is_vision_model = any(k in modell.lower() for k in vision_keywords)
                msg = [{"role": "user", "content": content_list}] if (is_vision_model and uploaded_files) else [{"role": "user", "content": prompt}]
                response = client.chat.completions.create(model=modell, messages=msg)
                
                st.success(f"✔️ Experten-Analyse durchgeführt mit {modell}")
                st.markdown("---")
                st.write(response.choices[0].message.content)
                break
            except: continue
