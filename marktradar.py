import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
import base64

st.set_page_config(page_title="MarktRadar OS v2.0", layout="wide")
st.title("⚡ MARKTRADAR – EXTREM-EXPERTEN MULTIPLIER OS")
st.subheader("99% präzise Einzelteil-Inventur & KI-Bewertung")

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
        return soup.get_text()[:2000]
    except: return "Fehler beim Web-Scraping."

# 3. UI
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📊 Parameter")
    link = st.text_input("Auktions-Link:")
    defekt_prozent = st.slider("Schrott-Regler (% der Ware unbrauchbar):", 0, 100, 10)
    gegenstaende = st.text_area("Zusätzliche Infos / Artikelliste:")

with col2:
    st.markdown("### 📸 Bild-Scan")
    uploaded_files = st.file_uploader("Artikelbilder hochladen:", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

# 4. Analyse
if st.button("🔥 EXPERTEN-ANALYSE STARTEN"):
    with st.spinner("Sachverständige analysieren Bilder und Daten..."):
        web_text = extrahiere_webseiten_text(link)
        
        prompt = f"""
        Du bist ein unbarmherziges Experten-Gremium. Analysiere die Bilder und Infos extrem präzise.
        
        Input:
        - Schrott-Anteil: {defekt_prozent}%
        - Manuelle Infos: {gegenstaende}
        - Auktions-Text: {web_text}

        Aufgabe:
        1. Inventur: Liste alle Artikel auf dem Bild/Text einzeln auf mit geschätztem Marktwert (Flohmarkt vs. Online).
        2. Risiko: Berücksichtige den Schrott-Anteil von {defekt_prozent}%.
        3. Empfehlung: Lohnt sich der Erwerb basierend auf dem Warenwert?
        """

        client = Groq(api_key=GROQ_API_KEY)
        
        # Modellwahl: Bevorzuge Vision-Modelle
        groq_models = client.models.list()
        all_model_ids = [m.id for m in groq_models.data]
        vision_keywords = ["vision", "scout", "maverick"]
        modelle_zum_testen = [m for m in all_model_ids if any(k in m.lower() for k in vision_keywords)] + \
                             [m for m in all_model_ids if not any(k in m.lower() for k in vision_keywords)]

        # Bild-Daten verarbeiten
        content_list = [{"type": "text", "text": prompt}]
        if uploaded_files:
            for f in uploaded_files:
                base64_image = base64.b64encode(f.read()).decode('utf-8')
                content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}})

        for modell in modelle_zum_testen:
            try:
                msg = [{"role": "user", "content": content_list}] if any(k in modell.lower() for k in vision_keywords) else [{"role": "user", "content": prompt}]
                response = client.chat.completions.create(model=modell, messages=msg)
                st.success(f"✔️ Analyse via {modell}")
                st.write(response.choices[0].message.content)
                break
            except: continue
