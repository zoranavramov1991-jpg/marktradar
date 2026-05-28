import streamlit as st
import requests
from bs4 import BeautifulSoup
import json

# ----------------------------------------------------
# 🔑 DEIN KOSTENLOSER CLOUD-KI SCHLÜSSEL
# ----------------------------------------------------
GROQ_API_KEY = "HIER_DEINEN_GROQ_KEY_EINSETZEN"

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
        else:
            return f"Fehler beim Laden (Status: {response.status_code})"
    except Exception as e:
        return f"Fehler: {e}"

# Funktion für die Cloud-KI Abfrage (Groq API)
def groq_ki_abfrage(prompt):
    if GROQ_API_KEY == "HIER_DEINEN_GROQ_KEY_EINSETZEN":
        return "Fehler: Du hast deinen kostenlosen Groq API-Key noch nicht im Code eingetragen!"
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-70b-8192",  # Die riesige, ultraschnelle Llama3-Version in der Cloud
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }
    try:
        res = requests.post(url, headers=headers, json=data, timeout=30)
        if res.status_code == 200:
            return res.json()['choices'][0]['message']['content']
        else:
            return f"Fehler von der Cloud-KI (Status {res.status_code}): {res.text}"
    except Exception as e:
        return f"Verbindungsfehler zur Cloud-KI: {e}"

# Seiteneinstellungen
st.set_page_config(page_title="MarktRadar OS", page_icon="🛰️", layout="wide")

# SIDEBAR WERKZEUG-BOX
with st.sidebar:
    st.header("🧰 Kostenlose Reseller-Tools")
    st.write("Nutze diese Gratis-Tools parallel für maximale Profi-Ergebnisse:")
    st.markdown("---")
    st.markdown("🔍 **[Google Lens öffnen](https://lens.google.com/)**\n\n*Perfekt auf dem Handy für schnellen Live-Scan.*")
    st.markdown("🖼️ **[Photoroom Web-Version](https://www.photoroom.com/de/hintergrund-entfernen)**\n\n*Hintergrund kostenlos entfernen.*")
    st.markdown("🤖 **[Microsoft Copilot](https://copilot.microsoft.com/)**\n\n*Zweite Meinung einholen.*")
    st.markdown("🌐 **[DeepL Übersetzer](https://www.deepl.com/translator)**\n\n*Für ausländische Auktionstexte.*")
    st.markdown("---")
    st.caption("Modus: MOBILE CLOUD-APP (ONLINE)")

# Hauptbereich
st.title("🛰️ MARKTRADAR – CLOUD MULTIPLIER OS")
st.write("Dein eigenes Händlerbetriebssystem – optimiert für dein Smartphone.")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🛰️ Erlös- & Gewinn-Analyse", "🧮 ROI- & Gebührenrechner", "🚨 Risiko- & Betrügerprüfung"])

with tab1:
    st.subheader("📦 Umsatz-Potenzial per Cloud-KI berechnen")
    
    col_eingabe, col_bilder = st.columns([1, 1])
    
    with col_eingabe:
        auktions_url = st.text_input("🔗 Auktions-Link hinzufügen:", placeholder="https://luedtke-auktion-online.de/auktion/...")
        
        risiko_prozent = st.slider(
            "⚠️ Wie viel Prozent der Ware ist schätzungsweise DEFEKT / SCHROTT? (%):", 
            min_value=0, max_value=100, value=10
        )
        funktioniert_prozent = 100 - risiko_prozent
        
        produkt_text = st.text_area(
            "✍️ Welche Gegenstände kaufst du gerade? (Kurze Liste):",
            placeholder="Z.B.: Stapel Vinyl-Schallplatten, 1x Polaroid Kamera mit Tasche, Hi-Fi Verstärker...",
            height=120
        )
        
        start_analyse = st.button("🚀 Cloud-KI Analyse starten", type="primary")

    with col_bilder:
        st.markdown("**📸 Bilder-Galerie (Zur Ansicht auf dem Handy):**")
        uploaded_files = st.file_uploader("Bilder hochladen:", accept_multiple_files=True, type=['png', 'jpg', 'jpeg'])
        if uploaded_files:
            for uploaded_file in uploaded_files:
                st.image(uploaded_file, use_container_width=True)

    if start_analyse:
        if not produkt_text.strip():
            st.warning("Bitte gib kurz ein, welche Gegenstände berechnet werden sollen!")
        else:
            web_inhalt = ""
            if auktions_url.strip():
                with st.spinner("🌐 Lese Auktions-Webseite aus..."):
                    web_inhalt = extrahiere_webseiten_text(auktions_url)
            
            with st.spinner("⚡ Cloud-KI-Team berechnet die Ertrags-Prognose..."):
                
                # Wir packen die Logik der 3 Agenten in einen großen, mächtigen Cloud-Prompt
                haupt_prompt = f"""
                Du bist ein System aus 3 hochspezialisierten KI-Händler-Agenten (Flohmarkt-Experte, Kleinanzeigen-Stratege, Finanzchef).
                Kalkuliere folgendes Mischpaket knallhart und realistisch für den deutschen Reseller-Markt.
                
                Gegenstände im Paket: "{produkt_text}"
                Zusatzinfos von der Webseite: "{web_inhalt}"
                Eingestellte Defekt-Quote: {risiko_prozent}% (Das heißt, {funktioniert_prozent}% der Sachen funktionieren).
                
                Schritt 1 (Flohmarkt-Experte): Schätze für jeden Gegenstand den absolut niedrigsten Mindestpreis (Flohmarkt-Barpreis).
                Schritt 2 (Kleinanzeigen-Stratege): Schätze für jeden Gegenstand den maximalen Höchstpreis bei Kleinanzeigen (Kein eBay!).
                Schritt 3 (Finanzchef): Rechne die Summen zusammen und ziehe von BEIDEN Endergebnissen exakt {risiko_prozent}% ab.
                
                Gib das Ergebnis exakt in diesem Format aus, direkt auf Deutsch, ohne Smalltalk:
                
                ## 💰 1. PREIS-MATRIX DER EINZELTEILE
                [Liste der Gegenstände: Name | Flohmarkt-Mindestpreis | Kleinanzeigen-Höchstpreis]
                
                ## 📊 2. ERTRAGS-PROGNOSE (Inkl. {risiko_prozent}% Defekt-Abschlag)
                * **Sicherer Mindest-Erlös (Flohmarkt gesamt nach Abschlag):** [Wert] €
                * **Maximaler Höchst-Erlös (Kleinanzeigen gesamt nach Abschlag):** [Wert] €
                
                ## 🔨 3. GEBOTS-STRATEGIE FÜR DIE AUKTION
                * **Maximaler Einkaufspreis (Dein Limit):** [Berechne exakt 45% des Sicheren Mindest-Erlöses] €
                * **Händler-Fazit:** [Kurzer, deutlicher Rat für den Einkauf]
                """
                
                finales_ergebnis = groq_ki_abfrage(haupt_prompt)
                
                st.success("🤖 Analyse abgeschlossen!")
                st.markdown("---")
                st.markdown(finales_ergebnis)
                st.markdown("---")

# Übrige Tabs für später
with tab2:
    st.subheader("🧮 ROI- & Gebührenrechner")
with tab3:
    st.subheader("🚨 Risiko- & Betrügerprüfung")

st.caption("Systemstatus: ONLINE | Modus: Cloud-Multi-Agenten | Modell: Llama3-70B (Cloud)")