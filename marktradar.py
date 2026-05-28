import streamlit as st
from groq import Groq
import base64

# --- SEITEN-KONFIGURATION ---
st.set_page_config(page_title="MarktRadar OS Stabil", layout="wide")
st.title("⚡ MARKTRADAR – STABIL-VERSION")

# --- 1. FUNKTIONEN (Logik vom UI getrennt) ---
def analysiere_daten(api_key, prompt, uploaded_files):
    client = Groq(api_key=api_key)
    
    # Text-Inhalt
    content = [{"type": "text", "text": prompt}]
    
    # Bild-Inhalt sicher hinzufügen
    if uploaded_files:
        for f in uploaded_files:
            f.seek(0)
            b64_image = base64.b64encode(f.read()).decode('utf-8')
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}
            })
            
    # Wir nutzen ein universelles Modell, das Text und (wenn verfügbar) Bilder verarbeitet
    # 'llama-3.3-70b-versatile' ist sehr stabil für Analyse
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": content}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Fehler bei der Anfrage: {e}"

# --- 2. UI-ELEMENTE ---
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.error("API-Key fehlt in den Secrets!")
    st.stop()

link = st.text_input("Auktions-Link:")
defekt_prozent = st.slider("Schrott-Regler (%):", 0, 100, 20)
uploaded_files = st.file_uploader("Artikelbilder:", accept_multiple_files=True)

# --- 3. DIE BEREINIGTE ANALYSE-LOGIK ---
# Erst hier unten, in einer kontrollierten Umgebung, wird der Button abgefragt
if st.button("🚀 EXPERTEN-ANALYSE STARTEN"):
    if not link and not uploaded_files:
        st.warning("Bitte gib einen Link ein oder lade ein Bild hoch.")
    else:
        with st.spinner("Experten-Gutachten wird erstellt..."):
            prompt = f"""
            Du bist ein Gutachter für Resale. Analysiere den Posten (Schrott: {defekt_prozent}%).
            Erstelle eine Tabelle mit: [Artikel] | [Zustand] | [Flohmarkt-Preis] | [Sicherheits-Gebot].
            Nenne das Maximalgebot für den Gesamtposten und die 3 größten Risiken.
            """
            
            ergebnis = analysiere_daten(GROQ_API_KEY, prompt, uploaded_files)
            st.markdown("---")
            st.write(ergebnis)
