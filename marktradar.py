import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
import base64

st.set_page_config(page_title="MarktRadar OS", layout="wide")
st.title("MARKTRADAR – CLOUD MULTIPLIER OS")

# 1. API-Key aus den Secrets laden
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception as e:
    st.error("Fehler: API-Key fehlt in den Secrets!")
    st.stop()

# 2. Funktion zum Auslesen des Webseiten-Textes
def extrahiere_webseiten_text(url):
    if not url:
        return "Kein Link angegeben."
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        return soup.get_text()[:2000]
    except Exception as e:
        return f"Fehler beim Web-Scraping: {e}"

# 3. Benutzeroberfläche
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📦 Umsatz-Potenzial per Cloud-KI berechnen")
    link = st.text_input("Auktions-Link hinzufügen:")
    defekt_prozent = st.slider("Wie viel Prozent der Ware ist schätzungsweise DEFEKT / SCHROTT? (%):", 0, 100, 10)
    gegenstaende = st.text_area("Welche Gegenstände kaufst du gerade? (Kurze Liste):", placeholder="Z.B.: Stapel Vinyl-Schallplatten, 1x Polaroid Kamera mit Tasche...")

with col2:
    st.markdown("### 📸 Bilder-Galerie (Für genaue KI-Foto-Analyse)")
    uploaded_files = st.file_uploader("Bilder hochladen:", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    if uploaded_files:
        st.success(f"{len(uploaded_files)} Bild(er) erfolgreich für die KI-Analyse geladen!")

# 4. Das Experten-Gremium starten
if st.button("Cloud-KI Analyse starten"):
    if link or gegenstaende or uploaded_files:
        with st.spinner("Das Experten-Gremium analysiert Text, Gebühren und Bilder..."):
            
            # Webseite auslesen
            web_text = extrahiere_webseiten_text(link)
            
            # Knallharter Experten-Prompt
            prompt = f"""
            Du bist ein Gremium aus 3 extrem erfahrenen, skeptischen Reseller-Experten. 
            Der User hält die bisherige Schätzung von 4.200 € für völlig unrealistisch hoch. 
            Deine Aufgabe ist es, den Deal KNALLHART zu hinterfragen und den echten MINDEST-Netto-Verdienst zu berechnen.

            User-Eingaben:
            - Liste der Gegenstände: {gegenstaende}
            - Erwarteter Schrott-Anteil: {defekt_prozent}%
            - Gefundener Auktions-Text: {web_text}

            Kosten-Regeln der Auktion (Zwingend beachten!):
            - Zum Zuschlagspreis kommen immer +20% Aufgeld hinzu.
            - Auf die Gesamtsumme kommen nochmals +19% Umsatzsteuer oben drauf!

            Bitte gib deine Analyse strukturiert in diesen 3 Experten-Berichten aus:

            ### 🕵️‍♂️ EXPERTE 1: Der pessimistische Reseller (Realistischer Marktwert)
            - Schätze den absolut niedrigsten Marktwert bei schnellem Weiterverkauf (eBay 'Verkaufte Artikel' / Kleinanzeigen). Keine Traumpreise!
            - Ziehe sofort {defekt_prozent}% des Wertes ab, da dieser Teil als Schrott deklariert ist.

            ### 📊 EXPERTE 2: Der scharfkalkulierende Finanzchef (Echte Netto-Gewinn-Kalkulation)
            - Erstelle eine Beispiel-Rechnung: Wenn der User die Auktion für z.B. 100 € oder 300 € ersteigert, wie hoch sind die echten Gesamtkosten inklusive der 20% Aufgeld und 19% USt?
            - Ziehe vom Wiederverkaufserlös ca. 10% Plattformgebühren (eBay etc.) und Versandpuffer ab.
            - Wie viel Euro reiner Netto-Gewinn bleibt am Ende MINDESTENS auf dem Bankkonto übrig?

            ### 👁️ EXPERTE 3: Der Bildprüfer (KI-Vision-Analyse)
            - Analysiere die beigefügten Fotos ganz genau auf den Zustand der Ware (Kratzer, sichtbare Schäden, Vollständigkeit, Originalverpackung). 
            - Wenn du Mängel siehst, korrigiere den Wert weiter nach unten! Falls keine Fotos hochgeladen wurden, nenne dem User die 3 wichtigsten optischen Schwachstellen, auf die er vor Ort achten muss.

            FAZIT: Klares Urteil abgeben: Lohnt sich dieser Deal bei einem geschätzten Einkaufspreis? JA oder NEIN?
            """

            # Inhalt für das Groq-Vision-Modell vorbereiten
            content_list = [{"type": "text", "text": prompt}]
            
            # Bilder in Base64 umwandeln und an die KI anhängen
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    bytes_data = uploaded_file.read()
                    base64_image = base64.b64encode(bytes_data).decode('utf-8')
                    content_list.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    })

            # Anfrage an Groq absenden
            try:
                client = Groq(api_key=GROQ_API_KEY)
                
                # Hier nutzen wir das finale, stabile Llama 3.2 Vision Modell
                response = client.chat.completions.create(
                    model="llama-3.2-11b-vision-instruct",
                    messages=[{"role": "user", "content": content_list}]
                )
                
                st.markdown("---")
                st.info("### 📋 Das Gutachten des Experten-Gremiums:")
                st.write(response.choices[0].message.content)
                
            except Exception as e:
                st.error(f"Fehler bei der Experten-Analyse: {e}")
    else:
        st.warning("Bitte fülle mindestens ein Feld aus oder lade ein Foto hoch!")
