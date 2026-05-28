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
        st.success(f"{len(uploaded_files)} Bild(er) erfolgreich geladen!")

# 4. Das Experten-Gremium starten
if st.button("Cloud-KI Analyse starten"):
    if link or gegenstaende or uploaded_files:
        with st.spinner("Das Experten-Gremium analysiert die Artikel und kalkuliert die 3 Varianten..."):
            
            # Webseite auslesen
            web_text = extrahiere_webseiten_text(link)
            
            # Exakt angepasster Experten-Prompt nach User-Vorgabe
            prompt = f"""
            Du bist ein Gremium aus 3 extrem erfahrenen, skeptischen Reseller-Experten. 
            Deine Aufgabe ist es, die hochgeladenen Bilder und Artikellisten KNALLHART zu analysieren. 
            Ignoriere allgemeinen Webseiten-Spam und konzentriere dich zu 100% nur auf die tatsächlichen Gegenstände/Artikel!

            User-Eingaben:
            - Liste der Gegenstände: {gegenstaende}
            - Erwarteter Schrott-Anteil: {defekt_prozent}%
            - Gefundener Auktions-Text: {web_text}

            Kosten-Regeln der Auktion (Zwingend vom Gewinn abziehen!):
            - Zum Zuschlagspreis kommen immer +20% Aufgeld hinzu.
            - Auf die Gesamtsumme kommen nochmals +19% Umsatzsteuer oben drauf!

            Bitte berechne den echten Netto-Gewinn (nach Abzug aller Gebühren, Steuern und des {defekt_prozent}% Schrott-Anteils) in genau diesen 3 Schritten/Varianten:

            ### 🏃‍♂️ SCHRITT 1: Schnellverkauf (z.B. Flohmarkt / Sofort-Ankaufportale)
            - Sehr niedrige Preise, extrem schneller Warenumschlag (Geld sofort auf der Hand).
            - Wie hoch ist hier der geschätzte Mindest-Reingewinn?

            ### ⚖️ SCHRITT 2: Normalverkauf (z.B. eBay Kleinanzeigen / Standard-Onlinepreise)
            - Realistische Marktpreise bei mittlerer Wartezeit (ca. 1-4 Wochen).
            - Ziehe ca. 10% Plattformgebühren/Puffer ab. Wie hoch ist hier der Reingewinn?

            ### 🐢 SCHRITT 3: Langsamverkauf (z.B. Spezialisierte Sammlerbörsen / eBay Festpreis)
            - Absoluter Spitzenpreis für Liebhaber und Sammler, kann aber Monate dauern.
            - Wie hoch ist das maximale Gewinn-Potenzial?

            ---
            ### 🏁 PROFIT-ENDZIFFER
            Gib hier ganz am Ende eine unmissverständliche, klare Reingewinn-Spanne von Schritt 1 bis Schritt 3 als finale Zahl an (z.B. "PROFIT-ENDZIFFER: 150 € - 650 € Netto-Gewinn").
            Beende mit einem klaren Urteil: Lohnt sich dieser Deal bei einem normalen Einkaufspreis? JA oder NEIN?
            """

            client = Groq(api_key=GROQ_API_KEY)

            # VERSUCH 1: Analyse mit dem brandneuen Llama 4 Scout Vision-Modell
            try:
                content_list = [{"type": "text", "text": prompt}]
                
                if uploaded_files:
                    for uploaded_file in uploaded_files:
                        bytes_data = uploaded_file.read()
                        base64_image = base64.b64encode(bytes_data).decode('utf-8')
                        content_list.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        })
                
                # Nutzung des offiziell unterstützten Llama 4 Multimodal-Modells
                response = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=[{"role": "user", "content": content_list}]
                )
                
                st.markdown("---")
                st.info("### 📋 Das Gutachten des Experten-Gremiums (Inklusive visuellem Bild-Scan):")
                st.write(response.choices[0].message.content)

            # FALLBACK: Falls die Bilder-API unerwartet hakt, springt sofort die Text-KI ein
            except Exception as vision_error:
                st.warning("⚠️ Bild-Modell temporär überlastet. Starte automatischen Text-Sicherheitsmodus...")
                
                try:
                    response = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    st.markdown("---")
                    st.info("### 📋 Das Gutachten des Experten-Gremiums (Text- & Datenanalyse):")
                    st.write(response.choices[0].message.content)
                    
                except Exception as fallback_error:
                    st.error(f"Kritischer Systemfehler: {fallback_error}")
    else:
        st.warning("Bitte füge einen Link, Text oder Bilder hinzu!")
