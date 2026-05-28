import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
import base64

st.set_page_config(page_title="MarktRadar OS v2.0", layout="wide")
st.title("⚡ MARKTRADAR – EXTREM-EXPERTEN MULTIPLIER OS")
st.subheader("99% präzise Einzelteil-Inventur & Plattform-Kalkulation")

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

# 3. Benutzeroberfläche (Optimiert für maximale Präzision)
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📊 Deal-Parameter & Kalkulation")
    link = st.text_input("Auktions-Link hinzufügen:")
    einkaufspreis = st.number_input("Dein geplanter Einkaufspreis / Maximalgebot (€):", min_value=0.0, value=100.0, step=10.0)
    defekt_prozent = st.slider("Schrott-Regler (% der Ware unbrauchbar):", 0, 100, 10)
    gegenstaende = st.text_area("Artikelliste (Falls bekannt, hier Details eintragen):", placeholder="Z.B.: 25x Amiga LPs, 1x Technics Plattenspieler...")

with col2:
    st.markdown("### 📸 Visueller Bild-Scan (Hochpräzise)")
    uploaded_files = st.file_uploader("Bilder der Artikel hochladen:", type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    if uploaded_files:
        st.success(f"🤖 {len(uploaded_files)} Bild(er) für 99%-Detail-Scan bereitgestellt!")

# 4. Das Experten-Gremium starten
if st.button("🔥 KNALLHARTE EXPERTEN-ANALYSE STARTEN"):
    if link or gegenstaende or uploaded_files:
        with st.spinner("Sachverständige scannen jedes Detail und berechnen die Plattform-Preise..."):
            
            web_text = extrahiere_webseiten_text(link)
            
            # Der ultimative Präzisions-Prompt
            prompt = f"""
            Du bist ein unbarmherziges, hochpräzises Gremium aus 3 Reseller-Experten (1x vereidigter Sachverständiger für Gebrauchtwaren, 1x Plattform-Stratege, 1x Chef-Finanzprüfer).
            Deine Aufgabe ist eine 99% genaue Einzelteil-Analyse der hochgeladenen Bilder und Artikellisten. Ignoriere jeden Werbe-Text der Webseite, fokussiere dich NUR auf die physischen Artikel.

            User-Eingaben & Kennzahlen:
            - Geplanter Einkaufspreis: {einkaufspreis} €
            - Schrott-Anteil (Wertlos): {defekt_prozent}%
            - Manuelle Artikelliste: {gegenstaende}
            - Gefundener Auktions-Text: {web_text}

            Kosten-Struktur der Auktion (Zwingend mathematisch korrekt berechnen!):
            - Echte Gesamtkosten = Einkaufspreis + 20% Aufgeld, und auf diese Zwischensumme nochmals +19% USt.

            Bitte liefere dein Gutachten exakt in dieser Struktur:

            ### 📋 1. Stück-für-Stück Inventur & Zustand (Aus Bildern & Text extrahiert)
            List oder tabelliere JEDEN einzelnen erkannten Gegenstand separat auf:
            - **Gegenstand:** [Genaue Bezeichnung]
            - **Visueller Zustand:** [Gebrauchsspuren, Kratzer, Vollständigkeit laut Foto]
            - **Flohmarkt-Preis:** [Sofort-Cash-Wert bei schnellem Abverkauf]
            - **Kleinanzeigen-Preis:** [Realistischer lokaler Festpreis]
            - **Spezial-Plattform (eBay/Discogs/Zoxs):** [Maximaler Online-Wert für Sammler]
            - **Empfohlene Route:** [Wo bringt dieses Teil am meisten Sinn?]

            ### 📉 2. Risiko- & Schrott-Abzug
            - Ziehe sofort {defekt_prozent}% vom Gesamtwert ab (Sicherheitsabschlag für defekte Ware).
            - Welche versteckten Risiken (z.B. tiefe Kratzer auf Platten, fehlende Kabel bei Technik) sind auf den Bildern zu vermuten?

            ### 📊 3. Finanz-Matrix (Wo bleibt am meisten hängen?)
            Berechne den echten Netto-Gewinn (Ertrag abzüglich deiner echten Gesamtkosten und abzüglich 10% Online-Gebührenpuffer):
            - **Szenario A (Reiner Flohmarkt-Abverkauf):** Wie viel Reingewinn bleibt am Ende auf dem Konto?
            - **Szenario B (Strategischer Online-Mix - Kleinanzeigen & eBay):** Wie viel Reingewinn bleibt am Ende auf dem Konto?

            ### 🏁 PROFIT-ENDZIFFER
            Gib hier die finale, bereinigte Netto-Gewinnspanne an:
            "PROFIT-ENDZIFFER: [Gewinn Szenario A] € bis [Gewinn Szenario B] € Netto-Reingewinn"

            Abschlussurteil: Lohnt sich dieser Deal bei einem Einkauf von {einkaufspreis} €? (Klares JA oder NEIN mit 1-Satz-Begründung).
            """

            client = Groq(api_key=GROQ_API_KEY)
            
            # Bilddaten aufbereiten
            content_list = [{"type": "text", "text": prompt}]
            if uploaded_files:
                for uploaded_file in uploaded_files:
                    bytes_data = uploaded_file.read()
                    base64_image = base64.b64encode(bytes_data).decode('utf-8')
                    content_list.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    })

            # Krisensichere Schleife: Testet verschiedene Groq-Modelle durch
            erfolgreich = False
            modelle_zum_testen = [
                "llama-3.2-90b-vision-preview",
                "llama-3.2-11b-vision-preview",
                "llama-3.1-8b-instant"  # Sicherer Text-Fallback falls Groq-Vision komplett down ist
            ]

            for modell in modelle_zum_testen:
                try:
                    # Falls es das Text-Modell ist, übergeben wir nur den Text-Prompt
                    messages_content = content_list if "vision" in modell else [{"role": "user", "content": prompt}]
                    
                    response = client.chat.completions.create(
                        model=modell,
                        messages=[{"role": "user", "content": messages_content}]
                    )
                    
                    st.markdown("---")
                    st.success(f"✔️ Analyse erfolgreich durchgeführt mit Modell: {modell}")
                    st.info("### 🕵️‍♂️ Das detaillierte Sachverständigen-Gutachten:")
                    st.write(response.choices[0].message.content)
                    erfolgreich = True
                    break # Schleife abbrechen, da wir ein Ergebnis haben!
                except Exception as e:
                    continue # Falls das Modell einen Fehler wirft, teste das nächste

            if not erfolgreich:
