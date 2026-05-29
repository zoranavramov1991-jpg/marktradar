import streamlit as st
import os, re, base64, urllib.parse, json
from datetime import datetime
import requests
from openai import OpenAI

st.set_page_config(page_title="⚡ MarktRadar OS PRO", page_icon="⚡",
    layout="wide", initial_sidebar_state="collapsed")

# ── CUSTOM CSS DESIGN ────────────────────────────────────────
st.markdown("""
<style>
/* ── HINTERGRUND: Hell mit sanftem Gradient ── */
.stApp {
    background: linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #f0f9ff 100%);
}

/* ── 3D KARTEN-EFFEKT ── */
[data-testid="stVerticalBlock"] > div {
    transition: transform 0.2s ease;
}

/* ── TABS: Modern & 3D ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: rgba(255,255,255,0.7);
    border-radius: 16px;
    padding: 8px;
    flex-wrap: wrap;
    box-shadow:
        0 2px 8px rgba(0,0,0,0.08),
        0 1px 2px rgba(0,0,0,0.05),
        inset 0 1px 0 rgba(255,255,255,0.9);
    backdrop-filter: blur(10px);
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 10px;
    color: #666;
    font-size: 13px;
    font-weight: 600;
    padding: 7px 14px;
    border: none;
    transition: all 0.25s cubic-bezier(0.34,1.56,0.64,1);
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #6c47ff 0%, #9b6dff 100%) !important;
    color: #fff !important;
    font-weight: 700 !important;
    box-shadow:
        0 4px 15px rgba(108,71,255,0.4),
        0 2px 4px rgba(108,71,255,0.3),
        inset 0 1px 0 rgba(255,255,255,0.2) !important;
    transform: translateY(-1px) scale(1.02) !important;
}
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(108,71,255,0.1);
    color: #6c47ff;
    transform: translateY(-1px);
}
.stTabs [data-baseweb="tab-panel"] {
    background: rgba(255,255,255,0.6);
    border-radius: 16px;
    padding: 1.5rem;
    border: 0.5px solid rgba(255,255,255,0.9);
    margin-top: 10px;
    box-shadow:
        0 8px 32px rgba(31,38,135,0.1),
        0 2px 8px rgba(0,0,0,0.06),
        inset 0 1px 0 rgba(255,255,255,0.8);
    backdrop-filter: blur(12px);
}

/* ── BUTTONS: 3D Gold ── */
.stButton > button {
    background: linear-gradient(135deg, #f5a623 0%, #f7c948 50%, #e8850a 100%) !important;
    color: #fff !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.65rem 1.5rem !important;
    font-size: 14px !important;
    letter-spacing: 0.3px !important;
    box-shadow:
        0 6px 20px rgba(245,166,35,0.35),
        0 2px 6px rgba(245,166,35,0.25),
        inset 0 1px 0 rgba(255,255,255,0.3),
        inset 0 -2px 0 rgba(0,0,0,0.1) !important;
    transform: perspective(500px) translateZ(0);
    transition: all 0.2s cubic-bezier(0.34,1.56,0.64,1) !important;
}
.stButton > button:hover {
    transform: perspective(500px) translateZ(6px) translateY(-2px) !important;
    box-shadow:
        0 10px 28px rgba(245,166,35,0.45),
        0 4px 10px rgba(245,166,35,0.3),
        inset 0 1px 0 rgba(255,255,255,0.4) !important;
}
.stButton > button:active {
    transform: perspective(500px) translateZ(2px) translateY(0px) !important;
    box-shadow:
        0 3px 10px rgba(245,166,35,0.3),
        inset 0 2px 4px rgba(0,0,0,0.15) !important;
}

/* ── METRIKEN: 3D Cards ── */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.8) !important;
    border: 0.5px solid rgba(255,255,255,0.9) !important;
    border-radius: 16px !important;
    padding: 1.2rem !important;
    box-shadow:
        0 8px 24px rgba(31,38,135,0.08),
        0 2px 6px rgba(0,0,0,0.06),
        inset 0 1px 0 rgba(255,255,255,1) !important;
    backdrop-filter: blur(8px);
    transform: perspective(800px) translateZ(0);
    transition: transform 0.2s ease !important;
}
[data-testid="metric-container"]:hover {
    transform: perspective(800px) translateZ(8px) translateY(-2px) !important;
    box-shadow:
        0 16px 40px rgba(31,38,135,0.12),
        0 4px 12px rgba(0,0,0,0.08) !important;
}
[data-testid="metric-container"] label {
    color: #888 !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #6c47ff !important;
    font-size: 24px !important;
    font-weight: 800 !important;
}

/* ── INPUTS: Modern ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    background: rgba(255,255,255,0.9) !important;
    border: 1.5px solid rgba(108,71,255,0.15) !important;
    border-radius: 12px !important;
    color: #333 !important;
    font-size: 14px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
    transition: all 0.2s !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #6c47ff !important;
    box-shadow: 0 0 0 3px rgba(108,71,255,0.12), 0 2px 8px rgba(0,0,0,0.05) !important;
    transform: translateY(-1px) !important;
}

/* ── SELECTBOX ── */
.stSelectbox > div > div {
    background: rgba(255,255,255,0.9) !important;
    border: 1.5px solid rgba(108,71,255,0.15) !important;
    border-radius: 12px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
}

/* ── FILE UPLOADER: 3D ── */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.7) !important;
    border: 2px dashed rgba(108,71,255,0.3) !important;
    border-radius: 16px !important;
    padding: 1.5rem !important;
    box-shadow: 0 4px 16px rgba(108,71,255,0.08) !important;
    transition: all 0.2s !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #6c47ff !important;
    background: rgba(108,71,255,0.04) !important;
    transform: translateY(-2px) !important;
}

/* ── EXPANDER: 3D ── */
.streamlit-expanderHeader {
    background: rgba(255,255,255,0.8) !important;
    border-radius: 12px !important;
    border: 0.5px solid rgba(255,255,255,0.9) !important;
    color: #444 !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
    transition: all 0.2s !important;
}
.streamlit-expanderHeader:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.1) !important;
}

/* ── SUCCESS/INFO/WARNING: Modern ── */
.stAlert {
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06) !important;
}

/* ── STATUS CONTAINER ── */
[data-testid="stStatusContainer"] {
    background: rgba(255,255,255,0.7) !important;
    border: 0.5px solid rgba(255,255,255,0.9) !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.06) !important;
    backdrop-filter: blur(8px);
}

/* ── SLIDER ── */
.stSlider [data-baseweb="thumb"] {
    background: linear-gradient(135deg, #6c47ff, #9b6dff) !important;
    box-shadow: 0 2px 8px rgba(108,71,255,0.4) !important;
    border: 2px solid white !important;
}
.stSlider [data-baseweb="track"] > div:first-child {
    background: linear-gradient(90deg, #6c47ff, #f5a623) !important;
}

/* ── RADIO ── */
.stRadio label {
    background: rgba(255,255,255,0.8) !important;
    border: 1px solid rgba(108,71,255,0.15) !important;
    border-radius: 10px !important;
    padding: 6px 14px !important;
    cursor: pointer !important;
    transition: all 0.2s cubic-bezier(0.34,1.56,0.64,1) !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.05) !important;
}
.stRadio label:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 12px rgba(108,71,255,0.15) !important;
    border-color: #6c47ff !important;
}
.stRadio label:has(input:checked) {
    background: linear-gradient(135deg, rgba(108,71,255,0.1), rgba(155,109,255,0.1)) !important;
    border-color: #6c47ff !important;
    color: #6c47ff !important;
    box-shadow: 0 4px 14px rgba(108,71,255,0.2) !important;
    transform: translateY(-1px) !important;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: rgba(0,0,0,0.05); border-radius: 10px; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(#6c47ff, #f5a623);
    border-radius: 10px;
}

/* ── MOBILE ── */
@media (max-width: 768px) {
    .stTabs [data-baseweb="tab"] {
        font-size: 11px !important;
        padding: 5px 8px !important;
    }
}
</style>
""", unsafe_allow_html=True)

# ── SECRETS ─────────────────────────────────────────────────
def secret(k):
    try: return st.secrets[k]
    except: return os.environ.get(k,"")

OR_KEY = secret("OPENROUTER_API_KEY")

# ── SESSION STATE ────────────────────────────────────────────
for k,v in {
    "lager":[],"sim":[],"lot":[],"gwlog":[],"fotos":[],"fcnt":0,
    # Lern-System
    "feedback_log":[],       # Alle Korrekturen gespeichert
    "analyse_history":[],    # Alle Analysen gespeichert
    "mein_wissen":[],        # Persönliches Preis-Wissen
    "preis_korrekturen":{},  # Echte Verkaufspreise
}.items():
    if k not in st.session_state: st.session_state[k]=v

# ── KI ENGINE ────────────────────────────────────────────────
def komprimiere(b64):
    """Bild auf max 800KB komprimieren"""
    try:
        from PIL import Image
        import io as _io
        img = Image.open(_io.BytesIO(base64.b64decode(b64)))
        if img.mode not in ("RGB",): img = img.convert("RGB")
        img.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
        buf = _io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return b64

def ki(prompt, bilder=None):
    """
    KI-Funktion mit automatischem Modell-Fallback.
    Probiert Vision-Modelle nacheinander bis eines funktioniert.
    """
    if not OR_KEY:
        return "❌ Kein API-Key konfiguriert! Bitte OPENROUTER_API_KEY in Streamlit Secrets eintragen."

    client = OpenAI(api_key=OR_KEY, base_url="https://openrouter.ai/api/v1")
    hdrs = {"HTTP-Referer": "https://marktradar.streamlit.app", "X-Title": "MarktRadar"}

    # Modell-Reihenfolge für Vision (Fallback-Kette)
    vision_modelle = [
        "google/gemini-1.5-flash",          # Günstig, schnell, gut
        "google/gemini-1.5-pro",             # Besser aber teurer
        "qwen/qwen-vl-plus",                 # Alibaba Vision
        "meta-llama/llama-3.2-11b-vision-instruct:free",  # Kostenlos!
        "openai/gpt-4o",                     # OpenAI Vision
    ]
    text_modell = "openai/gpt-4o-mini"

    verweigerungen = ["tut mir leid","kann nicht helfen","cannot assist",
                      "can't help","i'm sorry","unable to"]

    try:
        if bilder and len(bilder) > 0:
            # Bilder komprimieren
            bilder_k = [komprimiere(b) for b in bilder[:4]]

            # Vision-Nachrichten aufbauen
            def mache_msgs(b64_liste):
                inhalt = []
                for b64 in b64_liste:
                    inhalt.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                    })
                inhalt.append({"type": "text", "text": prompt})
                return [{"role": "user", "content": inhalt}]

            # Modelle nacheinander versuchen
            letzter_fehler = ""
            for model in vision_modelle:
                try:
                    msgs = mache_msgs(bilder_k)
                    r = client.chat.completions.create(
                        model=model, messages=msgs,
                        max_tokens=2500, extra_headers=hdrs
                    )
                    antwort = r.choices[0].message.content

                    # Prüfe ob echte Analyse oder Verweigerung
                    # Echte Analyse enthält immer Preise (EUR oder €)
                    hat_preise = "eur" in antwort.lower() or "€" in antwort
                    ist_verweigerung = any(v in antwort.lower() for v in verweigerungen)
                    if hat_preise or (not ist_verweigerung and len(antwort) > 200):
                        return antwort  # ✅ Erfolg!

                except Exception as e:
                    letzter_fehler = str(e)
                    if "404" in str(e) or "not found" in str(e).lower():
                        continue  # Nächstes Modell probieren
                    if "429" in str(e) or "rate" in str(e).lower():
                        continue
                    continue

            # Alle Vision-Modelle fehlgeschlagen → Text-Analyse
            return ki(prompt)  # Rekursiv ohne Bilder

        else:
            # Nur Text
            msgs = [{"role": "user", "content": prompt}]
            r = client.chat.completions.create(
                model=text_modell, messages=msgs,
                max_tokens=2500, extra_headers=hdrs
            )
            return r.choices[0].message.content

    except Exception as e:
        return f"❌ Fehler: {str(e)}"

# ── URL LESEN ────────────────────────────────────────────────
def lies_url(url):
    try:
        h = {"User-Agent":"Mozilla/5.0","Accept-Language":"de-DE,de;q=0.9"}
        r = requests.get(url, headers=h, timeout=15)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup(["script","style","nav","footer","header"]): t.decompose()
        zeilen = [z.strip() for z in soup.get_text("\n").split("\n") if len(z.strip())>15]
        return "\n".join(zeilen[:150])[:5000]
    except Exception as e:
        return f"[URL-Fehler: {e}]"

# ── ANALYSE-PROMPT ────────────────────────────────────────────
def mache_prompt(defekt, beschreibung, url_text):
    """Einfacher, natürlicher Prompt der von allen KI-Modellen akzeptiert wird"""

    zustand = (
        "wie neu" if defekt <= 20 else
        "leicht gebraucht" if defekt <= 40 else
        "gebraucht" if defekt <= 60 else
        "stark beschädigt" if defekt <= 80 else
        "defekt"
    )

    extra = ""
    if beschreibung.strip():
        extra += f" Der Händler schreibt: {beschreibung}."
    if url_text.strip() and not url_text.startswith("[URL"):
        extra += f"\n\nInformationen von der Webseite:\n{url_text[:2000]}"

    # Gelerntes Wissen aus früheren Analysen
    lern_kontext = ""
    if st.session_state.get("mein_wissen"):
        lern_kontext += "\n\nMein persönliches Wissen aus Erfahrung:\n"
        for w in st.session_state.mein_wissen[-5:]:
            lern_kontext += f"- {w}\n"
    if st.session_state.get("preis_korrekturen"):
        lern_kontext += "\nEchte Verkaufspreise die ich erzielt habe:\n"
        for art, preis in list(st.session_state.preis_korrekturen.items())[-5:]:
            lern_kontext += f"- {art}: €{preis}\n"
    if st.session_state.get("feedback_log"):
        lern_kontext += "\nMeine Korrekturen aus früheren Analysen:\n"
        for fb in st.session_state.feedback_log[-5:]:
            lern_kontext += f"- {fb}\n"

    return (
        f"Ich bin ein Händler auf deutschen Flohmärkten und verkaufe auf "
        f"Kleinanzeigen, Vinted, Facebook und eBay.\n"
        f"Der Artikel ist im Zustand: {zustand} ({defekt}% Defekt).{extra}{lern_kontext}\n\n"
        f"Bitte analysiere den/die Artikel im Bild und beantworte auf Deutsch:\n\n"
        f"Für JEDEN sichtbaren Artikel:\n"
        f"**Artikel: [Name]**\n"
        f"- Was ist es genau? [Beschreibung, Marke, Material]\n"
        f"- Alter & Herstellung:\n"
        f"  • Herstellungsjahr: [genaues Jahr ODER z.B. 'ca. 1965' ODER '1960-1970']\n"
        f"  • Epoche: [z.B. Wilhelminisch / Jugendstil / Art Deco / Nachkrieg / DDR / 50er / 60er / 70er / 80er / 90er / Modern]\n"
        f"  • Herkunftsland: [z.B. Deutschland / DDR / Westdeutschland / Italien / unbekannt]\n"
        f"  • Antik?: [Ja (über 100 Jahre) / Vintage (20-100 Jahre) / Modern (unter 20 Jahre)]\n"
        f"  • Alters-Beweis: [Was zeigt das Alter? z.B. Stempel, Schriftart, Material, Design]\n"
        f"- Zustand: [Einschätzung]\n"
        f"- Verkäuflichkeit: 🟢 schnell (1-7 Tage) / 🟡 mittel (1-4 Wochen) / 🔴 langsam (Monate)\n"
        f"PREISE (jeweils NUR eine konkrete Zahl, keine Spannen!):\n"
        f"- eBay: €[eine Zahl] (realistischer Verkaufspreis)\n"
        f"- Kleinanzeigen: €[eine Zahl]\n"
        f"- Vinted: €[eine Zahl]\n"
        f"- Facebook: €[eine Zahl]\n"
        f"- Flohmarkt: €[eine Zahl]\n"
        f"- Maximaler Ankaufspreis: €[eine Zahl]\n"
        f"Wichtig: Nur konkrete Zahlen, keine Spannen wie €30-€100!\n\n"
        f"\n\nFür JEDEN Artikel auch diese Punkte:\n\n"

        f"🏆 BESTE VERKAUFS-STRATEGIE:\n"
        f"- Beste Plattform: [Welche und warum]\n"
        f"- Optimaler Preis: €[eine konkrete Zahl]\n"
        f"- Zweitbeste Option: [Plattform] für €[eine konkrete Zahl]\n"
        f"- Flohmarkt: [Ja €[konkrete Zahl] / Nein]\n"
        f"- Schnell-Tipp: [1 konkreter Tipp]\n\n"

        f"🎯 KONFIDENZ-SCORE:\n"
        f"- Identifikation: X% sicher ([Begründung])\n"
        f"- Preisschätzung: X% sicher ([Begründung])\n"
        f"- Gesamtsicherheit: X%\n\n"

        f"⚠️ FÄLSCHUNGS-CHECK:\n"
        f"- Risiko: [Niedrig / Mittel / Hoch]\n"
        f"- Red Flags: [konkrete Warnsignale oder 'keine']\n"
        f"- Echtheitsbeweis: [Was spricht für Echtheit]\n\n"

        f"✨ AUFBEREITUNG & MEHRWERT:\n"
        f"- Empfehlung: [Reinigen / Polieren / Reparieren / Nichts tun]\n"
        f"- Methode: [Wie genau aufbereiten?]\n"
        f"- Wertsteigerung: +€X möglich\n\n"

        f"👥 SAMMLER & ZIELGRUPPE:\n"
        f"- Hauptkäufer: [Wer kauft das?]\n"
        f"- Sammlergruppen: [Spezifische Gruppen]\n"
        f"- Wo finden: [Facebook-Gruppen, Foren, Plattformen]\n\n"

        f"📅 BESTER VERKAUFS-ZEITPUNKT:\n"
        f"- Beste Monate: [Welche Monate]\n"
        f"- Schlechteste Monate: [Welche meiden]\n"
        f"- Jetzt verkaufen?: [Ja / Warten bis: Monat]\n\n"

        f"📝 FERTIGE KLEINANZEIGE (kopierbereit):\n"
        f"Titel: [Max 60 Zeichen]\n"
        f"Beschreibung: [3-4 überzeugende Sätze]\n"
        f"Preis: €X\n\n"

        f"---\n\n"

        f"🔢 SERIENNUMMERN & CODES:\n"
        f"- Seriennummer/Modellnr.: [falls sichtbar oder 'nicht erkennbar']\n"
        f"- Herstellungsdatum laut Code: [Datum oder 'nicht bestimmbar']\n"
        f"- Bedeutung: [Was sagt die Nummer aus?]\n\n"

        f"🔬 MATERIAL-ANALYSE:\n"
        f"- Hauptmaterial: [genaue Materialangabe]\n"
        f"- Qualitätsstufe: [z.B. Silber 925 / Porzellan 1. Wahl / Vollholz Eiche]\n"
        f"- Materialwert: [Beeinflusst Preis um +/- €X]\n\n"

        f"📋 ZUSTAND-PROTOKOLL:\n"
        f"- Schäden einzeln: [jede Delle, Kratzer, Chip genau beschreiben]\n"
        f"- Preisminderung: -€X wegen [Schaden]\n"
        f"- Ohne Schäden wäre Wert: €X\n\n"

        f"🔍 STEMPEL-DECODER:\n"
        f"- Alle Stempel/Punzen: [jeden Stempel beschreiben]\n"
        f"- Bedeutung: [was bedeutet jeder Stempel?]\n"
        f"- Echtheitswert: [wie viel mehr wert durch Stempel?]\n\n"

        f"📊 VERGLEICHSVERKÄUFE:\n"
        f"- Ähnlicher Artikel 1: [Beschreibung] → verkauft für €X auf [Plattform]\n"
        f"- Ähnlicher Artikel 2: [Beschreibung] → verkauft für €X auf [Plattform]\n"
        f"- Trend: [Preise steigen/fallen/stabil]\n\n"

        f"💰 GEWINNPROGNOSE:\n"
        f"- Empfohlener Einkaufspreis: €X\n"
        f"- Aufbereitungskosten: €X\n"
        f"- Erwarteter Verkaufspreis: €[konkrete Zahl]\n"
        f"- Plattformgebühren: €[konkrete Zahl]\n"
        f"- Netto-Gewinn: €[konkrete Zahl]\n"
        f"- ROI: X%\n"
        f"- Lohnt sich?: [✅ JA / ⚠️ GRENZFALL / ❌ NEIN]\n\n"

        f"🌟 RARITÄTEN-CHECK:\n"
        f"Falls der Artikel selten oder besonders wertvoll ist:\n"
        f"- Seltenheit: [Sehr selten / Selten / Häufig / Massenware]\n"
        f"- Warum selten?: [Begründung — Auflage, Epoche, Hersteller]\n"
        f"- Höchstpreis je nach Sammler: bis zu €X möglich\n"
        f"- Spezial-Tipp: [An welchen Sammler/Händler/Auktionshaus wenden?]\n"
        f"- ⭐ ALERT: Falls Schätzwert über €200 → UNBEDINGT vor Verkauf von Experten bewerten lassen!\n\n"

        f"\n🗺️ BESTER FLOHMARKT IN BERLIN für diesen Artikel:\n"
        f"Berliner Flohmärkte zur Auswahl:\n"
        f"- Mauerpark (So): Vintage, Kleidung, Kuriositäten, Junge Käufer\n"
        f"- Boxhagener Platz (So): Antiquitäten, Porzellan, Bücher, Sammler\n"
        f"- RAW Flohmarkt (Sa+So): Vintage Mode, Vinyl, Streetwear\n"
        f"- Fehrbelliner Platz (Di+Fr): Antiquitäten, Silber, Porzellan, Schmuck\n"
        f"- Treptower Park (So): Elektronik, Werkzeug, DDR-Artikel\n"
        f"- Winterfeldtmarkt (Sa): Bio, Vintage, Kunst, gehobenes Publikum\n"
        f"- Ostbahnhof (Fr-So): Alles gemischt, günstig, viele Käufer\n"
        f"- Arkonaplatz (So): Antiquitäten, Raritäten, Bücher, Kunst\n"
        f"- Alexanderplatz (tägl.): Touristen, Souvenirs, Gemischt\n\n"
        f"Basierend auf dem Artikel:\n"
        f"🥇 BESTER MARKT: [Name] am [Tag]\n"
        f"- Warum: [Zielgruppe und Spezialisierung passen weil...]\n"
        f"- Erwarteter Preis dort: €X\n"
        f"- Beste Uhrzeit: [z.B. 'Vor 10 Uhr kommen']\n\n"
        f"🥈 ZWEITBESTER MARKT: [Name] am [Tag]\n"
        f"- Warum: [Begründung]\n"
        f"- Erwarteter Preis: €X\n\n"
        f"❌ NICHT GEEIGNET: [Markt] weil [Begründung]\n\n"

        f"\n📷 FOTO-ANLEITUNG (welche Fotos noch machen?):\n"
        f"- Pflicht-Fotos: [z.B. Stempel, Rückseite, Maßband, Details]\n"
        f"- Warum wichtig: [welches Foto steigert den Verkaufspreis?]\n"
        f"- Foto-Tipp: [Bestes Licht, Hintergrund, Winkel für diesen Artikel]\n\n"

        f"🏪 ANKAUFSSTELLEN BERLIN (wo sonst verkaufen?):\n"
        f"- Spezialhändler: [passende Händler für diesen Artikel in Berlin]\n"
        f"- Antiquariate/Trödler: [konkrete Empfehlung]\n"
        f"- Pfandhaus/Auktionshaus: [falls geeignet, welches?]\n"
        f"- Was würden die zahlen: ca. €X\n"
        f"- Online-Spezialisten: [z.B. Catawiki, Dorotheum, Auktionshaus]\n\n"

        f"---\n"
        f"GESAMT ALLER ARTIKEL:\n"
        f"- Gesamtwert: €X bis €X\n"
        f"- Max. Ankaufspreis gesamt: €X\n"
        f"- Wertvollster Artikel: [Name] (€X)\n"
        f"- Raritäten gefunden: [Namen oder 'keine']"
    )

# ── HEADER ───────────────────────────────────────────────────
st.markdown("""
<div style='background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);
padding:18px;border-radius:14px;margin-bottom:18px;text-align:center'>
<h1 style='color:#f5a623;margin:0;font-size:2em'>⚡ MarktRadar OS PRO</h1>
<p style='color:#a8b2d8;margin:5px 0 0'>
Kleinanzeigen · Vinted · Facebook · eBay · Flohmärkte · Auktionen
</p></div>""", unsafe_allow_html=True)

# ── TABS ─────────────────────────────────────────────────────
T = st.tabs([
    "🔍 Analyse",
    "💬 Anschreib-Bot",
    "📦 Lager",
    "📚 OCR Scanner",
    "🔧 Reparatur",
    "📈 Trends",
    "🎭 Verhandlung",
    "📸 Foto-Coach",
    "🗺️ Flohmärkte",
    "🔬 Marken-Scanner",
    "📅 Timing",
    "✨ Anzeigen-KI",
    "🤖 Reselling-Chat",
    "🔎 Konkurrenz",
    "📊 Business-Coach",
    "📦 Lager-KI",
    "📰 Markt-News",
    "✍️ Profi-Text",
])

with T[0]:
    st.header("🔍 Artikel-Analyse")
    st.markdown("Fotos + Links werden **vollständig** analysiert — jeder Artikel einzeln mit Preisen!")

    typ = st.radio("Was analysieren?",["📸 Foto","🔗 Link","📸 + 🔗 Beides"],
                   horizontal=True, key="a_typ")

    url_text = ""
    url_inp  = ""

    # ── FOTO-UPLOAD ──
    if "Foto" in typ:
        st.markdown("##### 📷 Fotos hochladen")

        hochgeladen = st.file_uploader(
            "Foto(s) auswählen (mehrere möglich)",
            type=["jpg","jpeg","png","webp"],
            accept_multiple_files=True,
            key=f"fu_{st.session_state.fcnt}"
        )

        # Automatisch in Session State laden sobald hochgeladen
        if hochgeladen:
            neue_bilder = []
            for f in hochgeladen:
                f.seek(0)
                b64 = base64.b64encode(f.read()).decode()
                if b64 not in st.session_state.fotos:
                    neue_bilder.append(b64)
            if neue_bilder:
                st.session_state.fotos.extend(neue_bilder)

        # Fotos anzeigen
        n = len(st.session_state.fotos)
        if n > 0:
            st.success(f"✅ {n} Foto(s) bereit für Analyse")
            cols = st.columns(min(n, 4))
            for i, b64 in enumerate(st.session_state.fotos):
                with cols[i % 4]:
                    st.image(base64.b64decode(b64), caption=f"Foto {i+1}", use_column_width=True)
            if st.button("🗑️ Alle Fotos löschen", use_container_width=True):
                st.session_state.fotos = []
                st.session_state.fcnt += 1
                st.rerun()

    # ── URL-EINGABE ──
    if "Link" in typ:
        url_inp = st.text_input("🔗 Link eingeben",
            placeholder="https://luedtke-auktion-online.de/... oder Kleinanzeigen/Vinted-Link",
            key="a_url")

    # ── OPTIONEN ──
    st.markdown("---")
    c1,c2 = st.columns([2,1])
    with c1:
        beschr = st.text_area("📝 Eigene Beschreibung (optional)",
            placeholder="z.B. 'Kaffeeservice 6-teilig, kleiner Chip am Rand'",
            height=70, key="a_beschr")
    with c2:
        defekt = st.slider("🔧 Defekt-Grad", 1, 100, 10, 5, key="a_defekt")
        if   defekt <= 20: st.success(f"🟢 {defekt}% Fast neu")
        elif defekt <= 50: st.warning(f"🟡 {defekt}% Gebraucht")
        elif defekt <= 80: st.error(f"🔴 {defekt}% Beschädigt")
        else:               st.error(f"⛔ {defekt}% Fast unbrauchbar")

    hat_fotos = len(st.session_state.fotos) > 0
    hat_url   = bool(url_inp.strip())
    hat_beschr = bool(beschr.strip())

    if st.button("🚀 VOLLANALYSE STARTEN", type="primary", use_container_width=True, key="a_start"):
        if not (hat_fotos or hat_url or hat_beschr):
            st.warning("⚠️ Bitte zuerst Foto speichern, Link eingeben oder Beschreibung schreiben!")
        else:
            # STUFE 1 — Daten sammeln
            with st.status("📡 Stufe 1: Daten sammeln...", expanded=True):
                if hat_url:
                    st.write(f"🌐 Lese: {url_inp}")
                    url_text = lies_url(url_inp)
                    if url_text.startswith("[URL"):
                        st.warning("⚠️ URL konnte nicht gelesen werden")
                    else:
                        st.success(f"✅ {len(url_text)} Zeichen ausgelesen")
                if hat_fotos:
                    st.success(f"✅ {len(st.session_state.fotos)} Foto(s) bereit")

            # STUFE 2 — KI-Analyse
            with st.status("🔬 Stufe 2: KI analysiert jeden Artikel...", expanded=True):
                prompt = mache_prompt(defekt, beschr, url_text)
                bilder = st.session_state.fotos if hat_fotos else None
                with st.spinner("🤖 KI arbeitet — bitte warten..."):
                    ergebnis = ki(prompt, bilder=bilder)
                st.markdown(ergebnis)
                st.session_state["ana_ergebnis"] = ergebnis

                # Suchbegriff extrahieren
                suchbegriff = "Vintage Artikel"
                for line in ergebnis.split("\n"):
                    if "ARTIKEL 1:" in line.upper() or line.strip().startswith("ARTIKEL 1"):
                        teile = line.split(":")
                        if len(teile)>1:
                            suchbegriff = teile[1].strip().strip("*[] ")[:40]
                        break

            # STUFE 3 — Links
            with st.status("🔗 Stufe 3: Such-Links für alle Plattformen...", expanded=True):
                ebay_url = f"https://www.ebay.de/sch/i.html?_nkw={urllib.parse.quote(suchbegriff)}&LH_Complete=1&LH_Sold=1"
                ka_url   = f"https://www.kleinanzeigen.de/s-{urllib.parse.quote(suchbegriff)}/k0"
                vi_url   = f"https://www.vinted.de/catalog?search_text={urllib.parse.quote(suchbegriff)}"
                fb_url   = f"https://www.facebook.com/marketplace/search/?query={urllib.parse.quote(suchbegriff)}"
                st.markdown(f"**Suche nach: {suchbegriff}**")
                c1,c2 = st.columns(2)
                with c1:
                    st.markdown(f"🛒 [eBay beendete Verkäufe →]({ebay_url})")
                    st.markdown(f"📱 [Kleinanzeigen →]({ka_url})")
                with c2:
                    st.markdown(f"👗 [Vinted →]({vi_url})")
                    st.markdown(f"👥 [Facebook →]({fb_url})")

            # STUFE 4 — Zusammenfassung
            # ── ANALYSE SPEICHERN ──
            if ergebnis and len(ergebnis) > 200:
                st.session_state.analyse_history.append({
                    "datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
                    "analyse": ergebnis[:300],
                    "defekt": defekt
                })

            with st.status("✅ Stufe 4: Zusammenfassung...", expanded=True):
                ana_text = st.session_state.get("ana_ergebnis","")
                # Nur zusammenfassen wenn echte Analyse vorhanden
                verweigerung = ["tut mir leid","kann nicht","cannot","sorry"]
                ist_echt = not any(v in ana_text.lower() for v in verweigerung) and len(ana_text) > 200
                if ist_echt:
                    fazit = ki(
                        "Erstelle eine kurze Zusammenfassung (max 5 Zeilen) aus dieser Analyse.\n"
                        "Nur echte Fakten aus der Analyse. Nichts erfinden. Auf Deutsch.\n"
                        "Format:\n"
                        "• Artikel: [echte Namen aus der Analyse]\n"
                        "• GRUEN (schnell): [echte Namen]\n"
                        "• GELB (mittel): [echte Namen]\n"
                        "• ROT (langsam): [echte Namen]\n"
                        "• Gesamtwert: [echte Schätzung]\n\n"
                        f"Analyse:\n{ana_text[:1000]}"
                    )
                    st.info(f"📊 {fazit}")
                else:
                    st.warning("⚠️ Keine vollständige Analyse vorhanden.")

# ════════════════════════════════════════════════════════════
# TAB 2 — ANSCHREIB-BOT
# ════════════════════════════════════════════════════════════

with T[1]:
    st.header("💬 Anschreib-Bot")
    c1,c2 = st.columns(2)
    with c1:
        ab_art  = st.text_input("Artikel", placeholder="z.B. Vintage Kamera", key="ab_art")
        ab_mp   = st.number_input("Mein Angebot (€)", min_value=1.0, value=20.0, key="ab_mp")
        ab_vk   = st.number_input("Verkäufer-Preis (€)", min_value=1.0, value=50.0, key="ab_vk")
    with c2:
        ab_stil = st.selectbox("Stil", ["Freundlich & charmant","Bestimmt & direkt",
            "Dringend (heute)","Paket-Deal","Letztes Angebot"], key="ab_stil")
        ab_pl   = st.selectbox("Plattform", ["Kleinanzeigen","eBay","Facebook","Vinted","Flohmarkt"], key="ab_pl")
    ab_kunde = st.text_area("📩 Nachricht des Kunden (optional):",
        placeholder="Fügen Sie die Nachricht des Kunden ein — KI antwortet darauf!",
        height=80, key="ab_kunde")
    if st.button("✍️ Nachricht generieren", type="primary", use_container_width=True, key="ab_btn"):
        if ab_art:
            with st.spinner("✍️ ..."):
                kunden_text = f"\nKunden-Nachricht: '{ab_kunde}'" if ab_kunde.strip() else ""
                r = ki(f"Schreibe eine Verhandlungs-Nachricht auf Deutsch.\n"
                       f"Stil: {ab_stil} | Plattform: {ab_pl}\n"
                       f"Artikel: {ab_art} | Angebot: EUR{ab_mp} | Verkäufer: EUR{ab_vk}{kunden_text}\n"
                       f"Max 5 Saetze, psychologisch optimiert, NUR die fertige Nachricht!")
                st.text_area("📩 Kopieren:", value=r, height=180, key="ab_r")

# ════════════════════════════════════════════════════════════
# TAB 3 — LAGER
# ════════════════════════════════════════════════════════════

with T[2]:
    st.header("📦 Lagerbestand")
    c1,c2 = st.columns(2)
    with c1:
        la  = st.text_input("Artikel", key="la")
        lek = st.number_input("EK (€)", min_value=0.0, value=10.0, key="lek")
        lvk = st.number_input("Ziel-VK (€)", min_value=0.0, value=45.0, key="lvk")
    with c2:
        lzu = st.selectbox("Zustand",["Sehr gut","Gut","Gebraucht","Beschädigt"],key="lzu")
        lpl = st.selectbox("Plattform",["Kleinanzeigen","eBay","Vinted","Facebook","Flohmarkt"],key="lpl")
        lta = st.number_input("Liegezeit (Tage)",min_value=0,value=0,key="lta")
    if st.button("📦 Hinzufügen",type="primary",use_container_width=True,key="la_btn"):
        if la:
            g = lvk - lek - (lvk*0.05)
            st.session_state.lager.append({"artikel":la,"ek":lek,"vk":lvk,"zustand":lzu,"plattform":lpl,"tage":lta,"gewinn":round(g,2)})
            st.success(f"✅ Gewinn: EUR{g:.2f}")
            st.rerun()
    if st.session_state.lager:
        g_ek = sum(i["ek"] for i in st.session_state.lager)
        g_g  = sum(i["gewinn"] for i in st.session_state.lager)
        c1,c2,c3 = st.columns(3)
        c1.metric("Artikel",len(st.session_state.lager))
        c2.metric("Kapital",f"€{g_ek:.2f}")
        c3.metric("Gewinn",f"€{g_g:.2f}")
        st.markdown("---")
        for it in st.session_state.lager:
            c1,c2,c3,c4 = st.columns([3,1,1,1])
            c1.markdown(f"**{it['artikel']}** ({it['zustand']}) — {it['plattform']}")
            c2.markdown(f"€{it['ek']:.0f}")
            c3.markdown(f"→ €{it['vk']:.0f}")
            c4.markdown(f"**+€{it['gewinn']:.0f}**")
            if it["tage"]>30: st.warning(f"⏰ {it['artikel']}: {it['tage']} Tage!")

# ════════════════════════════════════════════════════════════
# TAB 4 — OCR SCANNER
# ════════════════════════════════════════════════════════════

with T[3]:
    st.header("📚 OCR Medien-Scanner")
    ocr_b = st.file_uploader("📷 Stapel fotografieren",type=["jpg","jpeg","png"],key="ocr_b")
    ocr_t = st.selectbox("Typ",["Bücher","CDs/Vinyl","Video-Spiele","DVDs","Gemischt"],key="ocr_t")
    if st.button("🔍 Analysieren",type="primary",use_container_width=True,key="ocr_btn"):
        if ocr_b:
            with st.spinner("🤖 Scanne..."):
                b64 = base64.b64encode(ocr_b.read()).decode()
                r = ki(f"Experte fuer {ocr_t} in Deutschland. Scanne ALLE {ocr_t} im Foto.\n"
                       f"Fuer jeden: [Titel] | eBay: EUR X | Kleinanzeigen: EUR X | Vinted: EUR X | Flohmarkt: EUR X\n"
                       f"Am Ende: Top-3 wertvollste + Gesamtwert. Auf Deutsch.", bilder=[b64])
                st.markdown(r)

# ════════════════════════════════════════════════════════════
# TAB 5 — REPARATUR
# ════════════════════════════════════════════════════════════

with T[4]:
    st.header("🔧 Reparatur-Rechner")
    rep_fotos = st.file_uploader("📷 Fotos hochladen (mehrere möglich)",
        type=["jpg","jpeg","png"], accept_multiple_files=True, key="rep_fotos")
    if rep_fotos:
        cols = st.columns(min(len(rep_fotos),4))
        for i,f in enumerate(rep_fotos):
            with cols[i%4]: st.image(f, caption=f"Foto {i+1}", use_column_width=True)
    c1,c2 = st.columns(2)
    with c1:
        ra = st.text_input("Artikel",key="ra")
        rek2 = st.number_input("EK (€)",min_value=0.0,value=15.0,key="rek2")
        rm = st.number_input("Material (€)",min_value=0.0,value=25.0,key="rm")
        rs = st.number_input("Stunden",min_value=0.5,value=3.0,step=0.5,key="rs")
    with c2:
        rvk = st.number_input("Erwarteter VK (€)",min_value=0.0,value=120.0,key="rvk")
        rpl = st.selectbox("Plattform",["Kleinanzeigen","eBay","Vinted","Facebook","Flohmarkt"],key="rpl")
        rb  = st.text_area("Was reparieren?",height=70,key="rb")
    if st.button("🔧 Berechnen",type="primary",use_container_width=True,key="r_btn"):
        geb = rvk*(0.119 if "eBay" in rpl else 0.05 if "Vinted" in rpl else 0.02)
        gk  = rek2+rm+(rvk*0.02)+geb
        gw  = rvk-gk
        sl  = gw/rs if rs>0 else 0
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Kosten",f"€{gk:.2f}")
        c2.metric("Gewinn",f"€{gw:.2f}")
        c3.metric("Stundenlohn",f"€{sl:.2f}/h")
        c4.metric("ROI",f"{(gw/gk*100) if gk>0 else 0:.0f}%")
        if sl>=15: st.success(f"✅ LOHNT SICH!")
        elif sl>=8: st.warning(f"⚠️ Grenzfall")
        else: st.error(f"❌ Lohnt nicht")
        if rb:
            with st.spinner("💡 Tipps..."):
                st.markdown(ki(f"3 Reparatur-Tipps fuer '{ra}': {rb}. Kurz auf Deutsch."))

# ════════════════════════════════════════════════════════════
# TAB 6 — POST-DUELL
# ════════════════════════════════════════════════════════════

with T[5]:
    st.header("📈 Trends")
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("### 🔥 Hot-Trends 2025/26")
        for s,n,w,p in [
            ("🔥","Vintage Levi's 501","+187%","€45"),("🔥","Game Boy Color","+214%","€110"),
            ("🔥","90s Sportjacken","+92%","€55"),("🔥","Analoge Kameras","+165%","€75"),
            ("📈","Meissen Porzellan","+14%","€45"),("📈","LEGO Classic","+95%","€55"),
            ("📈","Vintage Adidas","+72%","€50"),("⚖️","Kaffeemaschinen","+8%","€25")]:
            st.markdown(f"{s} **{n}** — {p} ({w})")
    with c2:
        st.markdown("### 💡 Gold-Wörter")
        for g in ["🏠 Dachbodenfund","🏡 Haushaltsauflösung","⚰️ Nachlass",
                  "🔑 Kellerfund","🚚 Umzugskarton","🎁 Zu verschenken",
                  "📦 Konvolut Kiste","👵 Oma entrümpelt"]:
            st.markdown(f"- {g}")
    st.markdown("---")
    tf = st.text_input("🤖 Frage:",placeholder="Was ist gerade gefragt?",key="tf")
    if st.button("Fragen",key="t_btn"):
        if tf:
            with st.spinner("..."):
                st.markdown(ki(f"Reselling-Experte Deutschland. Kurz auf Deutsch: {tf}"))

# ════════════════════════════════════════════════════════════
# TAB 8 — VERHANDLUNG
# ════════════════════════════════════════════════════════════

with T[6]:
    st.header("🎭 Verhandlungs-Simulator")
    c1,c2 = st.columns(2)
    with c1:
        va  = st.text_input("Artikel",key="va")
        vvk = st.number_input("Verkäufer-Preis (€)",min_value=1.0,value=80.0,key="vvk")
        vz  = st.number_input("Ihr Ziel (€)",min_value=1.0,value=40.0,key="vz")
    with c2:
        vt  = st.selectbox("Verkäufer-Typ",["Sturköpfig","Freundlich","Gestresst","Unentschlossen","Profi"],key="vt")
        vpl = st.selectbox("Wo?",["Flohmarkt","Kleinanzeigen","Facebook"],key="vpl")
    if st.button("🎭 Start",type="primary",use_container_width=True,key="v_start"):
        if va:
            st.session_state.sim = []
            r = ki(f"Du bist Verkäufer ({vt}) auf {vpl}. Artikel: {va} fuer EUR{vvk}.\n"
                   f"Erste Reaktion wenn Kaeufer fragt ob Preis verhandelbar. 2-3 Saetze. Deutsch. In der Rolle!")
            st.session_state.sim.append({"r":"🏪","t":r})
            st.rerun()
    if st.session_state.sim:
        st.markdown("---")
        for m in st.session_state.sim:
            if m["r"]=="🏪": st.info(f"**{m['r']} Verkäufer:** {m['t']}")
            else: st.success(f"**{m['r']} Sie:** {m['t']}")
        kunden_msg = st.text_area("📩 Nachricht des Kunden (optional):",
            placeholder="Nachricht des Kunden einfügen — KI antwortet darauf",
            height=70, key="v_kunde")
        ai = st.text_input("Ihre Antwort:", key="v_inp")
        c1,c2 = st.columns(2)
        with c1:
            if st.button("📤 Senden",type="primary",use_container_width=True,key="v_send"):
                eingabe = kunden_msg.strip() if kunden_msg.strip() else ai
                if eingabe:
                    st.session_state.sim.append({"r":"🛒","t":eingabe})
                    verl = "\n".join([f"{m['r']}: {m['t']}" for m in st.session_state.sim])
                    r = ki(f"Verkäufer ({vt}) von {va} (EUR{vvk}). Verlauf:\n{verl}\nAntworte als Verkäufer (2-3 Sätze, Deutsch, in Rolle bleiben)!")
                    st.session_state.sim.append({"r":"🏪","t":r})
                    st.rerun()
        with c2:
            if st.button("🧠 Strategie",use_container_width=True,key="v_str"):
                verl = "\n".join([f"{m['r']}: {m['t']}" for m in st.session_state.sim])
                r = ki(f"Verhandlungsanalyse fuer {va}, Ziel EUR{vz}. Verlauf:\n{verl}\n1.Was gut? 2.Was besser? 3.Naechste Nachricht? Deutsch.")
                st.markdown(f"### 🧠\n{r}")

# ════════════════════════════════════════════════════════════
# TAB 9 — FOTO-COACH
# ════════════════════════════════════════════════════════════

with T[7]:
    st.header("📸 Foto-Coach")
    fc_b = st.file_uploader("Foto hochladen",type=["jpg","jpeg","png"],key="fc_b")
    fc_p = st.selectbox("Plattform",["Kleinanzeigen","Vinted","eBay","Facebook","Alle"],key="fc_p")
    if st.button("📸 Analysieren",type="primary",use_container_width=True,key="fc_btn"):
        if fc_b:
            with st.spinner("🔍 ..."):
                b64 = base64.b64encode(fc_b.read()).decode()
                c1,c2 = st.columns(2)
                with c1:
                    fc_b.seek(0); st.image(fc_b,caption="Ihr Foto",use_column_width=True)
                with c2:
                    r = ki(f"Produkt-Foto Experte fuer {fc_p}. Bewerte und verbessere dieses Foto. Auf Deutsch.\n"
                           f"Bewertung (1-10): Helligkeit, Hintergrund, Schaerfe, Winkel\n"
                           f"Probleme: [was ist schlecht?]\nVerbesserungen: 1. 2. 3.\n"
                           f"Perfektes Foto: Hintergrund, Licht, Winkel, Extras\nPreis-Potenzial: +X% durch besseres Foto", bilder=[b64])
                    st.markdown(r)

# ════════════════════════════════════════════════════════════
# TAB 10 — FLOHMÄRKTE BERLIN
# ════════════════════════════════════════════════════════════

with T[8]:
    st.header("🗺️ Berliner Flohmärkte Mo–So")
    maerkte = [
        ("Montag","Flohmarkt am Rathaus Steglitz","Schloßstraße 37, 12163","Mo–Sa 9–18h","+49 30 79706820","🏠 Haushalt, Bücher","⭐⭐⭐","Günstige Alltagsartikel","https://maps.google.com/?q=Rathaus+Steglitz+Berlin"),
        ("Montag","Trödelmarkt Berliner Straße","Berliner Str. 16, 10715","Mo–Fr 10–17h","+49 30 8537240","🛍️ Gemischt, Antiquitäten","⭐⭐⭐","Kleine Händler — gute Verhandlung","https://maps.google.com/?q=Berliner+Straße+16+Berlin"),
        ("Dienstag","Flohmarkt Fehrbelliner Platz","Fehrbelliner Pl., 10707","Di & Fr 8–15h","+49 30 28097272","🏺 Antiquitäten, Porzellan","⭐⭐⭐⭐","Top für Porzellan & Silber!","https://maps.google.com/?q=Fehrbelliner+Platz+Berlin"),
        ("Dienstag","Antikmarkt Charlottenburg","Kantstraße 17, 10623","Di–Sa 10–18h","+49 30 3138030","🏛️ Antiquitäten, Kunst","⭐⭐⭐⭐","Hochwertige Antiquitäten","https://maps.google.com/?q=Kantstraße+17+Berlin"),
        ("Mittwoch","Flohmarkt Alexanderplatz","Alexanderplatz, 10178","Täglich 10–19h","+49 30 24632425","🏙️ Gemischt, Vintage","⭐⭐⭐","Täglich offen — spontane Käufe","https://maps.google.com/?q=Alexanderplatz+Flohmarkt+Berlin"),
        ("Mittwoch","Trödelmarkt Spandau","Carl-Schurz-Str. 13, 13597","Mi & Sa 8–14h","+49 30 3545080","🔧 Werkzeug, Haushalt","⭐⭐⭐","Günstige Werkzeuge","https://maps.google.com/?q=Carl-Schurz-Straße+Spandau+Berlin"),
        ("Donnerstag","Trödelmarkt Schöneberg","Winterfeldtplatz, 10781","Do (klein) Sa 8–14h","+49 30 7262290","🌿 Vintage, Mode, Haushalt","⭐⭐⭐⭐","Donnerstags ruhiger & günstiger!","https://maps.google.com/?q=Winterfeldtplatz+Berlin"),
        ("Freitag","Flohmarkt Fehrbelliner Platz","Fehrbelliner Pl., 10707","Di & Fr 8–15h","+49 30 28097272","🏺 Antiquitäten, Porzellan","⭐⭐⭐⭐⭐","Freitags BESTE Auswahl!","https://maps.google.com/?q=Fehrbelliner+Platz+Berlin"),
        ("Freitag","Antik & Trödelmarkt Ostbahnhof","Erich-Steinfurth-Str. 1, 10243","Fr–So 9–16h","+49 30 2936028","🛍️ Großer Gemischtmarkt","⭐⭐⭐⭐","Freitags wenig Leute — beste Preise!","https://maps.google.com/?q=Flohmarkt+Ostbahnhof+Berlin"),
        ("Samstag","RAW Flohmarkt","Revaler Str. 99, 10245","Sa & So 10–18h","+49 30 29367840","🕶️ Vintage Mode, Vinyl","⭐⭐⭐⭐⭐","BESTE Vintage-Kleidung Berlin!","https://maps.google.com/?q=RAW+Gelände+Berlin"),
        ("Samstag","Winterfeldtmarkt","Winterfeldtplatz, 10781","Jeden Sa 8–14h","+49 30 7262290","🌿 Bio, Vintage, Kunst","⭐⭐⭐⭐⭐","Einer der besten Berliner Märkte!","https://maps.google.com/?q=Winterfeldtmarkt+Berlin"),
        ("Samstag","Antik & Trödelmarkt Ostbahnhof","Erich-Steinfurth-Str. 1, 10243","Fr–So 9–16h","+49 30 2936028","🛍️ Großer Gemischtmarkt","⭐⭐⭐⭐","Groß & günstig","https://maps.google.com/?q=Flohmarkt+Ostbahnhof+Berlin"),
        ("Sonntag","Mauerpark Flohmarkt","Bernauer Str. 63, 13355","Jeden So 9–18h","+49 30 40505380","🎭 Gemischt Vintage","⭐⭐⭐⭐⭐","MUSS! Vor 10 Uhr kommen!","https://maps.google.com/?q=Mauerpark+Flohmarkt+Berlin"),
        ("Sonntag","Flohmarkt Boxhagener Platz","Boxhagener Pl., 10245","Jeden So 10–18h","+49 30 29362596","🏺 Antiquitäten, Porzellan","⭐⭐⭐⭐⭐","Top für Porzellan & Antiquitäten!","https://maps.google.com/?q=Boxhagener+Platz+Flohmarkt+Berlin"),
        ("Sonntag","Treptower Flohmarkt","Treptower Park, 12435","Jeden So 8–16h","+49 30 5321555","🔧 Elektronik, DDR","⭐⭐⭐⭐","Gut für Elektronik & DDR!","https://maps.google.com/?q=Treptower+Park+Flohmarkt+Berlin"),
        ("Sonntag","RAW Flohmarkt","Revaler Str. 99, 10245","Sa & So 10–18h","+49 30 29367840","🕶️ Vintage Mode, Vinyl","⭐⭐⭐⭐⭐","Sonntags entspannter als Sa","https://maps.google.com/?q=RAW+Gelände+Berlin"),
        ("Sonntag","Arkonaplatz Flohmarkt","Arkonaplatz, 10435","Jeden So 10–16h","+49 30 7861003","🏛️ Antiquitäten, Raritäten","⭐⭐⭐⭐","Klein aber fein — echte Raritäten!","https://maps.google.com/?q=Arkonaplatz+Flohmarkt+Berlin"),
        ("Sonntag","Nowkoelln Flowmarkt","Maybachufer, 12047","2. & 4. So 11–18h","+49 30 62908811","🎨 Design, Vintage","⭐⭐⭐⭐","Kreativ & günstig","https://maps.google.com/?q=Maybachufer+Berlin"),
        ("Sonntag","Antik & Trödelmarkt Ostbahnhof","Erich-Steinfurth-Str. 1, 10243","Fr–So 9–16h","+49 30 2936028","🛍️ Großer Gemischtmarkt","⭐⭐⭐⭐","Sonntags am vollsten — früh!","https://maps.google.com/?q=Flohmarkt+Ostbahnhof+Berlin"),
    ]
    tage = ["Alle","Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]
    fw = st.radio("📅 Tag:",tage,horizontal=True,key="fw")
    st.markdown("---")
    gefiltert = maerkte if fw=="Alle" else [m for m in maerkte if m[0]==fw]
    if fw=="Alle":
        for tag in tage[1:]:
            tm = [m for m in maerkte if m[0]==tag]
            if tm:
                st.markdown(f"### 📅 {tag}")
                for m in tm:
                    with st.expander(f"{m[6]} **{m[1]}**"):
                        c1,c2 = st.columns([2,1])
                        with c1:
                            st.markdown(f"📍 {m[2]}\n\n🕐 {m[3]}\n\n📞 **{m[4]}**\n\n🏷️ {m[5]}\n\n💡 *{m[7]}*")
                        with c2:
                            st.markdown(m[6])
                            st.link_button("🗺️ Maps",m[8],use_container_width=True)
    else:
        for m in gefiltert:
            with st.expander(f"{m[6]} **{m[1]}**"):
                c1,c2 = st.columns([2,1])
                with c1:
                    st.markdown(f"📍 {m[2]}\n\n🕐 {m[3]}\n\n📞 **{m[4]}**\n\n🏷️ {m[5]}\n\n💡 *{m[7]}*")
                with c2:
                    st.markdown(m[6])
                    st.link_button("🗺️ Maps",m[8],use_container_width=True)
    st.markdown("---")
    st.markdown("### 🤖 KI-Flohmarkt-Assistent")
    fq = st.text_input("Frage stellen:", placeholder="z.B. Wo finde ich heute gute Antiquitäten?", key="fq")
    if st.button("🗺️ KI fragen", type="primary", use_container_width=True, key="f_btn"):
        if fq:
            with st.spinner("🤖 Analysiere..."):
                r = ki(f"""Berliner Flohmarkt-Experte mit aktuellen Informationen ({datetime.now().strftime('%B %Y')}).
Beantworte auf Deutsch konkret und aktuell: {fq}
Berücksichtige: Mauerpark(So), Boxhagener Platz(So), RAW(Sa+So),
Fehrbelliner Platz(Di+Fr), Treptower Park(So), Winterfeldtmarkt(Sa),
Ostbahnhof(Fr-So), Arkonaplatz(So)""")
                st.markdown(r)
    if st.button("📊 Aktuelle Marktlage Berlin", use_container_width=True, key="f_markt"):
        with st.spinner("🤖 Analysiere aktuelle Lage..."):
            r = ki(f"""Berliner Flohmarkt-Experte. Aktuelle Analyse {datetime.now().strftime('%B %Y')}.
Was ist gerade besonders auf Berliner Flohmärkten gefragt?
Welche Märkte sind gerade besonders gut?
Insider-Tipps für diese Woche. Auf Deutsch.""")
            st.markdown(r)

# ════════════════════════════════════════════════════════════
# TAB 11 — LOT
# ════════════════════════════════════════════════════════════

with T[9]:
    st.header("🔬 Marken-Scanner")
    st.markdown("Stempel/Punze/Logo fotografieren → KI identifiziert Marke!")
    ms_b = st.file_uploader("📷 Stempel/Logo fotografieren",type=["jpg","jpeg","png"],key="ms_b")
    ms_k = st.selectbox("Kategorie",["Porzellan & Keramik","Silber & Besteck","Uhren","Schmuck","Elektronik","Kleidung","Spielzeug","Unbekannt"],key="ms_k")
    if st.button("🔬 Identifizieren",type="primary",use_container_width=True,key="ms_btn"):
        if ms_b:
            with st.spinner("🔬 Scanne Marke..."):
                b64 = base64.b64encode(ms_b.read()).decode()
                c1,c2 = st.columns(2)
                with c1: ms_b.seek(0); st.image(ms_b,caption="Ihr Stempel",use_column_width=True)
                with c2:
                    r = ki(f"Marken-Experte fuer {ms_k}. Identifiziere diesen Stempel/Logo/Punze.\n"
                           f"Antworte immer auf Deutsch.\n"
                           f"Marke: [Name]\nHerkunft: [Land]\nJahr: [ca. Jahr]\nEchtheit: [Echt/Unsicher/Faelschung]\n"
                           f"Beweis: [was macht es echt?]\nSeltenheit: [hoch/mittel/niedrig]\nWert: EUR X bis EUR Y\n"
                           f"eBay-Suchbegriff: [Begriff]", bilder=[b64])
                    st.markdown(r)

# ════════════════════════════════════════════════════════════
# TAB 15 — BUNDLE
# ════════════════════════════════════════════════════════════

with T[10]:
    st.header("📅 Saisonaler Timing-Planer")
    ti_a = st.text_input("Artikel",placeholder="z.B. Winterjacke, Weihnachtsdeko, Gartenmöbel",key="ti_a")
    ti_m = st.selectbox("Monat",["Januar","Februar","März","April","Mai","Juni",
        "Juli","August","September","Oktober","November","Dezember"],index=datetime.now().month-1,key="ti_m")
    if st.button("📅 Besten Zeitpunkt finden",type="primary",use_container_width=True,key="ti_btn"):
        if ti_a:
            with st.spinner("🤖 ..."):
                r = ki(f"Markt-Timing Experte fuer deutschen Secondhand-Markt.\n"
                       f"Artikel: {ti_a} | Jetzt: {ti_m}\n"
                       f"Erstelle auf Deutsch:\n"
                       f"BESTE MONATE: [Monate + warum]\nSCHLECHTESTE MONATE: [Monate + warum]\n"
                       f"MONAT-TABELLE: alle 12 Monate mit Nachfrage und Preis-Potenzial\n"
                       f"JETZT IM {ti_m.upper()}: Lohnt sich? Wenn warten: bis wann? Erwarteter Mehrerlös: X%")
                st.markdown(r)

# ════════════════════════════════════════════════════════════
# TAB 18 — GEWINN-BUCH
# ════════════════════════════════════════════════════════════

with T[11]:
    st.header("✨ Anzeigen-Optimierer")
    c1,c2 = st.columns(2)
    with c1:
        ao_l = st.selectbox("Plattform",["Kleinanzeigen","Vinted","eBay","Facebook"],key="ao_l")
        ao_p = st.number_input("Preis (€)",min_value=0.0,value=45.0,key="ao_p")
    with c2:
        ao_k = st.selectbox("Kategorie",["Haushalt","Kleidung","Elektronik","Möbel","Spielzeug","Sonstiges"],key="ao_k")
        ao_t2 = st.number_input("Tage online ohne Verkauf",min_value=0,value=7,key="ao_t2")
    ao_ti = st.text_input("Aktueller Titel:",key="ao_ti")
    ao_tx = st.text_area("Aktuelle Beschreibung:",height=100,key="ao_tx")
    if st.button("✨ Optimieren",type="primary",use_container_width=True,key="ao_btn"):
        if ao_ti or ao_tx or ao_fotos:
            with st.spinner("✨ ..."):
                ao_bilder = []
                if ao_fotos:
                    for f in ao_fotos:
                        f.seek(0)
                        ao_bilder.append(base64.b64encode(f.read()).decode())
                r = ki(f"Verkaufsanzeigen-Experte fuer {ao_l}. Kategorie: {ao_k}. Preis: EUR{ao_p}. {ao_t2} Tage online.\n"
                       f"Titel: {ao_ti}\nBeschreibung: {ao_tx}\n"
                       f"Analysiere und verbessere. Auf Deutsch.\n"
                       f"1. Analyse (Note 1-10 + Schwaechen)\n"
                       f"2. NEUER TITEL (max 60 Zeichen, kopierfertig)\n"
                       f"3. NEUE BESCHREIBUNG (kopierfertig, alle Keywords)\n"
                       f"4. Preis-Empfehlung (jetzt EUR{ao_p} — besser: EUR?)\n"
                       f"5. Keywords fuer {ao_l}\n"
                       f"6. Tipps: Foto, Posting-Zeit, erwartete Verbesserung +X%",
                      bilder=ao_bilder if ao_bilder else None)
                st.markdown(r)

# ════════════════════════════════════════════════════════════
# TAB 20 — TAGESPLAN
# ════════════════════════════════════════════════════════════

with T[12]:
    st.header("🤖 KI-Reselling-Chat")
    st.markdown("Ihr persönlicher Reselling-Experte — stellen Sie jede Frage!")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    if prompt_chat := st.chat_input("Fragen Sie alles über Reselling, Preise, Flohmärkte..."):
        st.session_state.chat_history.append({"role":"user","content":prompt_chat})
        with st.chat_message("user"):
            st.markdown(prompt_chat)
        system = ("Du bist ein erfahrener deutscher Reselling-Experte und Flohmarkt-Profi. "
                  "Du kennst alle deutschen Plattformen: Kleinanzeigen, Vinted, Facebook, eBay. "
                  "Antworte immer auf Deutsch, konkret und praktisch.")
        verlauf = [{"role":"system","content":system}]
        for m in st.session_state.chat_history[-10:]:
            verlauf.append({"role":m["role"],"content":m["content"]})
        with st.chat_message("assistant"):
            with st.spinner("🤖 Denke nach..."):
                antwort = ki(system + " Frage: " + prompt_chat)
                st.markdown(antwort)
        st.session_state.chat_history.append({"role":"assistant","content":antwort})
    if st.button("🗑️ Chat löschen", key="chat_clear"):
        st.session_state.chat_history = []
        st.rerun()

# ════════════════════════════════════════════════════════════
# TAB 22 — KONKURRENZ-CHECKER
# ════════════════════════════════════════════════════════════

with T[13]:
    st.header("🔎 KI-Konkurrenz-Checker")
    st.markdown("Link einer anderen Anzeige eingeben → KI sagt wie Sie besser sein können!")
    kk_url  = st.text_input("🔗 Link der Konkurrenz-Anzeige:", placeholder="https://www.kleinanzeigen.de/...", key="kk_url")
    kk_art  = st.text_input("Ihr Artikel:", placeholder="z.B. Kinderwagen Peg Perego", key="kk_art")
    kk_preis = st.number_input("Ihr geplanter Preis (€):", min_value=0.0, value=80.0, key="kk_preis")
    if st.button("🔎 Konkurrenz analysieren", type="primary", use_container_width=True, key="kk_btn"):
        if kk_url:
            with st.spinner("🔍 Analysiere Konkurrenz..."):
                seite_text = lies_url(kk_url)
                r = ki(f"""Analysiere diese Konkurrenz-Anzeige für einen deutschen Reseller.
Konkurrenz-Anzeige Inhalt:
{seite_text[:2000]}
Mein Artikel: {kk_art} | Mein geplanter Preis: €{kk_preis}

Antworte auf Deutsch:
📊 KONKURRENZ-ANALYSE:
- Ihr Preis: €X
- Ihr Zustand: [Beschreibung]
- Ihre Stärken: [was machen sie gut?]
- Ihre Schwächen: [was machen sie schlecht?]

🥇 WIE SIE BESSER SEIN KÖNNEN:
- Optimaler Preis für Sie: €X (weil...)
- Besserer Titel: [Vorschlag]
- Bessere Beschreibung: [Tipp]
- Ihr Vorteil: [was können Sie besser anbieten?]

⚡ FAZIT: Lohnt es sich mit dieser Konkurrenz zu konkurrieren? [Ja/Nein + Warum]""")
                st.markdown(r)

# ════════════════════════════════════════════════════════════
# TAB 23 — BUSINESS-COACH
# ════════════════════════════════════════════════════════════

with T[14]:
    st.header("📊 KI-Business-Coach")
    st.markdown("KI analysiert Ihre Verkäufe und gibt konkrete Wachstums-Tipps!")
    if st.session_state.gwlog:
        ges_g = sum(i["g"] for i in st.session_state.gwlog)
        ges_e = sum(i["ek"] for i in st.session_state.gwlog)
        roi = (ges_g/ges_e*100) if ges_e > 0 else 0
        c1,c2,c3 = st.columns(3)
        c1.metric("Verkäufe", len(st.session_state.gwlog))
        c2.metric("Gewinn", f"€{ges_g:.2f}")
        c3.metric("ROI", f"{roi:.0f}%")
        if st.button("🤖 Business-Analyse starten", type="primary", use_container_width=True, key="bc_btn"):
            with st.spinner("📊 KI analysiert Ihr Business..."):
                log = "\n".join([f"{e['a']}: EK€{e['ek']} VK€{e['vk']} G€{e['g']} {e['pl']}" for e in st.session_state.gwlog])
                r = ki(f"""Du bist ein Business-Coach für deutsche Reseller und Flohmarkt-Händler.
Analysiere diese Verkaufshistorie und gib konkrete Wachstums-Tipps auf Deutsch.
Verkäufe:
{log}

📈 STÄRKEN: [Was läuft gut?]
⚠️ SCHWÄCHEN: [Was verbessern?]
🎯 TOP-3 EMPFEHLUNGEN: [Konkrete Maßnahmen]
💰 GEWINN-POTENTIAL: Mit diesen Änderungen könnten Sie €X mehr verdienen
📊 BESTE PLATTFORM: [Welche nutzen Sie zu wenig?]
🛒 BESTE KATEGORIE: [Welche Artikel bringen meisten ROI?]""")
                st.markdown(r)
    else:
        st.info("💡 Tragen Sie erst Verkäufe im Gewinn-Buch ein!")

# ════════════════════════════════════════════════════════════
# TAB 24 — LAGER-KI-OPTIMIERER
# ════════════════════════════════════════════════════════════

with T[15]:
    st.header("📦 KI-Lager-Optimierer")
    st.markdown("KI analysiert Ihr Lager und sagt was zuerst verkauft werden sollte!")
    if st.session_state.lager:
        if st.button("🤖 Lager analysieren", type="primary", use_container_width=True, key="lo_btn"):
            with st.spinner("📦 KI analysiert Lager..."):
                lager_text = "\n".join([f"{it['artikel']}: EK€{it['ek']} VK€{it['vk']} {it['tage']}Tage {it['plattform']}" for it in st.session_state.lager])
                r = ki(f"""Analysiere diesen Lagerbestand eines deutschen Resellers. Auf Deutsch.
Lager:
{lager_text}

🚨 SOFORT VERKAUFEN (liegt zu lang):
[Artikel die zu lange liegen + warum + Preis senken auf €X]

⚡ DIESE WOCHE VERKAUFEN:
[Welche Artikel priorisieren?]

📦 BUNDLE-EMPFEHLUNG:
[Welche Artikel zusammen verkaufen für mehr Gewinn?]

💡 PREIS-ANPASSUNGEN:
[Welche Preise senken/erhöhen?]

📊 LAGER-GESUNDHEIT: [Note 1-10 + Begründung]""")
                st.markdown(r)
    else:
        st.info("💡 Fügen Sie erst Artikel im Lager-Tab ein!")

# ════════════════════════════════════════════════════════════
# TAB 25 — MARKT-NEWS
# ════════════════════════════════════════════════════════════

with T[16]:
    st.header("📰 KI-Markt-News")
    st.markdown("Was ist gerade gefragt? KI analysiert aktuelle Trends!")
    mn_kat = st.selectbox("Kategorie:", ["Alles","Kleidung","Elektronik","Porzellan & Antiquitäten",
        "Spielzeug","Möbel","Bücher & Medien"], key="mn_kat")
    if st.button("📰 Aktuelle Trends abrufen", type="primary", use_container_width=True, key="mn_btn"):
        with st.spinner("📡 Analysiere Markt..."):
            r = ki(f"""Du bist Markt-Analyst für deutschen Secondhand-Markt.
Erstelle einen aktuellen Markt-Report für: {mn_kat}
Plattformen: Kleinanzeigen, Vinted, Facebook, eBay, Flohmärkte Berlin.
Datum: {datetime.now().strftime('%B %Y')}. Auf Deutsch.

🔥 TOP-5 MEISTGESUCHTE ARTIKEL GERADE:
[Liste mit Artikel, Durchschnittspreis, Nachfrage-Trend]

📈 STEIGENDE PREISE:
[Was wird gerade teurer und warum?]

📉 FALLENDE PREISE:
[Was ist übersättigt?]

💎 GEHEIMTIPP DES MONATS:
[Ein unterschätzter Artikel mit hohem Gewinnpotenzial]

🗓️ SAISONALER TIPP:
[Was jetzt im {datetime.now().strftime('%B')} besonders gut verkaufen?]""")
            st.markdown(r)

# ════════════════════════════════════════════════════════════
# TAB 26 — PROFI-TEXT GENERATOR
# ════════════════════════════════════════════════════════════

with T[17]:
    st.header("✍️ KI-Profi-Text Generator")
    st.markdown("Fotos hochladen + Details eingeben → KI schreibt Profi-Anzeige für alle Plattformen!")
    pt_fotos = st.file_uploader("📷 Artikel-Fotos (mehrere möglich)",
        type=["jpg","jpeg","png"], accept_multiple_files=True, key="pt_fotos")
    if pt_fotos:
        cols = st.columns(min(len(pt_fotos),4))
        for i,f in enumerate(pt_fotos):
            with cols[i%4]: st.image(f, caption=f"Foto {i+1}", use_column_width=True)
    c1,c2 = st.columns(2)
    with c1:
        pt_art   = st.text_input("Artikel:", placeholder="z.B. Peg Perego Kinderwagen", key="pt_art")
        pt_zust  = st.selectbox("Zustand:", ["Wie neu","Sehr gut","Gut","Gebraucht"], key="pt_zust")
        pt_preis = st.number_input("Preis (€):", min_value=0.0, value=120.0, key="pt_preis")
    with c2:
        pt_details = st.text_area("Details:", placeholder="z.B. Grau, mit Babyschale, Jahrgang 2022, kein Versand", height=100, key="pt_details")
    if st.button("✍️ Profi-Texte erstellen", type="primary", use_container_width=True, key="pt_btn"):
        if pt_art or pt_fotos:
            with st.spinner("✍️ Erstelle Profi-Texte..."):
                pt_bilder = []
                if pt_fotos:
                    for f in pt_fotos:
                        f.seek(0)
                        pt_bilder.append(base64.b64encode(f.read()).decode())
                r = ki(f"""Erstelle professionelle Verkaufstexte für alle Plattformen. Auf Deutsch.
Artikel: {pt_art} | Zustand: {pt_zust} | Preis: €{pt_preis}
Details: {pt_details}

📱 KLEINANZEIGEN-ANZEIGE:
Titel (max 60 Zeichen): [Titel]
Beschreibung: [3-4 Sätze, überzeugend]

👗 VINTED-BESCHREIBUNG:
[Kurz, emoji-freundlich, 2-3 Sätze]

👥 FACEBOOK MARKETPLACE:
[Freundlich, lokal, 2-3 Sätze]

🛒 EBAY-BESCHREIBUNG:
Titel (max 80 Zeichen): [Titel mit Keywords]
Beschreibung: [Vollständig mit allen Details]

🏷️ BESTE KEYWORDS für alle Plattformen:
[10 Suchbegriffe die Käufer nutzen]""")
                st.markdown(r)

# ════════════════════════════════════════════════════════════
# TAB 27 — EINKAUFS-PLANER
# ════════════════════════════════════════════════════════════


# ── FOOTER ──────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"<p style='text-align:center;color:#666'>⚡ MarktRadar OS PRO v6.0 · Zoran Berlin · {datetime.now().strftime('%d.%m.%Y')}</p>", unsafe_allow_html=True)
