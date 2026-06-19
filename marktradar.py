"""
MarktRadar OS PRO — ULTIMATE EDITION v8.0
=========================================
• 9 Vision-Modelle mit Fallback-Kette
• Ensemble-KI: 3 Experten gleichzeitig + Richter-KI
• Google + Tavily + You.com Echtzeit-Suche
• Preis-Ensemble: 3 KIs bewerten Preise gleichzeitig
• Lern-System: KI lernt aus Ihren Korrekturen
• 18 Tabs alle mit Ensemble-KI
"""
import streamlit as st
import os, base64, urllib.parse, concurrent.futures, time, json
from datetime import datetime
import requests
from openai import OpenAI
import openai as _oai

# ── DAUERHAFTES SPEICHERN ─────────────────────────────────────
# Lern-Daten überleben jetzt App-Neustarts (vorher nur RAM = nach Neustart weg)
_SPEICHER_DATEI = "marktradar_lerndaten.json"
_LERN_KEYS = ["mein_wissen","preis_korrekturen","verkauf_log","ki_korrekturen",
              "kategorie_wissen","beste_zeiten","markt_notizen"]

def lade_lerndaten():
    """Lädt gespeicherte Lern-Daten von der Festplatte (falls vorhanden)."""
    try:
        if os.path.exists(_SPEICHER_DATEI):
            with open(_SPEICHER_DATEI, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def speichere_lerndaten():
    """Speichert alle Lern-Daten dauerhaft auf die Festplatte."""
    try:
        daten = {k: st.session_state.get(k) for k in _LERN_KEYS}
        with open(_SPEICHER_DATEI, "w", encoding="utf-8") as f:
            json.dump(daten, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False

st.set_page_config(page_title="⚡ MarktRadar OS PRO", page_icon="⚡",
    layout="wide", initial_sidebar_state="collapsed")

# ── CSS ───────────────────────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Inter:wght@400;500;600;700;800&display=swap');

/* === LUXUS-HINTERGRUND === */
.stApp{
  background:
    radial-gradient(ellipse 1200px 800px at 15% 0%, rgba(245,200,80,0.10) 0%, transparent 50%),
    radial-gradient(ellipse 900px 700px at 90% 100%, rgba(108,71,255,0.07) 0%, transparent 50%),
    linear-gradient(165deg, #fdfbf5 0%, #fbf8ef 40%, #f8f3e7 100%);
  font-family:'Inter',-apple-system,sans-serif;
}
.stApp::before{
  content:'';position:fixed;inset:0;pointer-events:none;
  background-image:radial-gradient(circle at 1px 1px, rgba(180,140,40,0.06) 1px, transparent 0);
  background-size:24px 24px;z-index:0;
}
.main .block-container{position:relative;z-index:1}
h1,h2,h3{font-family:'Playfair Display','Inter',serif!important;letter-spacing:-0.02em}

/* === EDLE TABS === */
.stTabs [data-baseweb="tab-list"]{
  gap:4px;
  background:linear-gradient(135deg, rgba(28,25,23,0.96) 0%, rgba(45,40,35,0.96) 100%);
  border-radius:18px;padding:10px;flex-wrap:wrap;
  box-shadow:0 10px 40px rgba(28,25,23,0.25), inset 0 1px 0 rgba(245,200,80,0.15);
  border:1px solid rgba(245,200,80,0.2);
}
.stTabs [data-baseweb="tab"]{
  background:transparent;border-radius:11px;color:#c9bfa9;
  font-size:13px;font-weight:600;padding:9px 16px;border:none;
  transition:all 0.35s cubic-bezier(0.4,0,0.2,1);letter-spacing:0.02em;
}
.stTabs [data-baseweb="tab"]:hover{color:#f5d48a;background:rgba(245,200,80,0.08);transform:translateY(-1px)}
.stTabs [aria-selected="true"]{
  background:linear-gradient(135deg,#f5d48a 0%,#e8a93a 50%,#c8862a 100%)!important;
  color:#1a1612!important;font-weight:700!important;
  box-shadow:0 6px 20px rgba(232,169,58,0.45), inset 0 1px 0 rgba(255,235,180,0.6)!important;
  transform:translateY(-2px) scale(1.04)!important;text-shadow:0 1px 0 rgba(255,235,180,0.4)!important;
}
.stTabs [data-baseweb="tab-panel"]{
  background:linear-gradient(180deg, rgba(255,253,247,0.85) 0%, rgba(252,248,238,0.85) 100%);
  border-radius:20px;padding:1.75rem;
  border:1px solid rgba(200,160,80,0.2);margin-top:14px;
  box-shadow:0 20px 60px rgba(60,45,20,0.08), 0 1px 0 rgba(255,255,255,0.9) inset;
  backdrop-filter:blur(20px);
  animation:fadeUp 0.5s cubic-bezier(0.16,1,0.3,1);
}
@keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}

/* === GOLD-BUTTONS MIT GLANZ === */
.stButton>button{
  background:linear-gradient(135deg,#f5d48a 0%,#e8a93a 45%,#c8862a 100%)!important;
  color:#1a1612!important;font-weight:700!important;border:none!important;
  border-radius:14px!important;padding:0.75rem 1.75rem!important;letter-spacing:0.02em!important;
  box-shadow:0 8px 24px rgba(200,134,42,0.35), inset 0 1px 0 rgba(255,240,200,0.7), inset 0 -1px 0 rgba(120,80,20,0.2)!important;
  transition:all 0.3s cubic-bezier(0.4,0,0.2,1)!important;
  position:relative!important;overflow:hidden!important;
  text-shadow:0 1px 0 rgba(255,235,180,0.5)!important;
}
.stButton>button::before{
  content:'';position:absolute;top:0;left:-100%;width:100%;height:100%;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,0.5),transparent);
  transition:left 0.6s ease;
}
.stButton>button:hover{
  transform:translateY(-3px) scale(1.02)!important;
  box-shadow:0 14px 36px rgba(200,134,42,0.5), inset 0 1px 0 rgba(255,240,200,0.8)!important;
}
.stButton>button:hover::before{left:100%}
.stButton>button:active{transform:translateY(-1px) scale(1.01)!important}

/* === METRIK-KARTEN (PREIS-BOX) === */
[data-testid="metric-container"]{
  background:linear-gradient(180deg, #ffffff 0%, #fdfaf2 100%)!important;
  border-radius:18px!important;padding:1.4rem!important;
  border:1px solid rgba(200,160,80,0.25)!important;
  box-shadow:0 12px 32px rgba(60,45,20,0.08), 0 1px 0 rgba(255,255,255,0.9) inset!important;
  transition:all 0.3s ease!important;
}
[data-testid="metric-container"]:hover{
  transform:translateY(-4px)!important;
  box-shadow:0 20px 48px rgba(200,134,42,0.18)!important;
  border-color:rgba(232,169,58,0.5)!important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"]{
  background:linear-gradient(135deg,#c8862a 0%,#e8a93a 100%)!important;
  -webkit-background-clip:text!important;-webkit-text-fill-color:transparent!important;
  background-clip:text!important;font-size:28px!important;font-weight:800!important;
  font-family:'Playfair Display',serif!important;
}

/* === INPUTS EDEL === */
.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stNumberInput>div>div>input{
  background:rgba(255,253,247,0.95)!important;
  border:1.5px solid rgba(200,160,80,0.25)!important;
  border-radius:12px!important;font-family:'Inter',sans-serif!important;
  transition:all 0.25s ease!important;color:#2a2520!important;
}
.stTextInput>div>div>input:focus,.stTextArea>div>div>textarea:focus,.stNumberInput>div>div>input:focus{
  border-color:#e8a93a!important;
  box-shadow:0 0 0 4px rgba(232,169,58,0.15)!important;
}
.stSelectbox>div>div{
  background:rgba(255,253,247,0.95)!important;
  border:1.5px solid rgba(200,160,80,0.25)!important;border-radius:12px!important;
}
[data-testid="stFileUploader"]{
  background:linear-gradient(135deg, rgba(255,253,247,0.9) 0%, rgba(252,245,225,0.9) 100%)!important;
  border:2px dashed rgba(200,134,42,0.4)!important;border-radius:18px!important;
  transition:all 0.3s ease!important;
}
[data-testid="stFileUploader"]:hover{
  border-color:#e8a93a!important;
  box-shadow:0 8px 24px rgba(232,169,58,0.15)!important;
  transform:scale(1.005)!important;
}

/* === SLIDER GOLD === */
.stSlider [data-baseweb="thumb"]{
  background:linear-gradient(135deg,#f5d48a,#e8a93a)!important;
  border:3px solid white!important;
  box-shadow:0 4px 12px rgba(200,134,42,0.4)!important;
}
.stSlider [data-baseweb="track"]>div:first-child{
  background:linear-gradient(90deg,#c8862a,#e8a93a,#f5d48a)!important;
}

/* === RADIO PILLS === */
.stRadio label{
  background:rgba(255,253,247,0.95)!important;
  border:1.5px solid rgba(200,160,80,0.2)!important;
  border-radius:12px!important;padding:8px 16px!important;
  cursor:pointer!important;transition:all 0.25s ease!important;
  font-weight:500!important;
}
.stRadio label:hover{
  border-color:rgba(232,169,58,0.5)!important;
  transform:translateY(-1px)!important;
  box-shadow:0 4px 12px rgba(200,134,42,0.1)!important;
}
.stRadio label:has(input:checked){
  background:linear-gradient(135deg, rgba(245,212,138,0.2), rgba(232,169,58,0.15))!important;
  border-color:#e8a93a!important;color:#7a5520!important;font-weight:700!important;
  box-shadow:0 4px 16px rgba(232,169,58,0.2)!important;
}

/* === ALERTS EDEL === */
.stAlert{
  border-radius:14px!important;border:none!important;
  box-shadow:0 6px 20px rgba(60,45,20,0.08)!important;
  backdrop-filter:blur(8px)!important;
}

/* === EXPANDER === */
.streamlit-expanderHeader,[data-testid="stExpander"] summary{
  background:linear-gradient(135deg, rgba(255,253,247,0.95), rgba(252,245,225,0.95))!important;
  border-radius:12px!important;border:1px solid rgba(200,160,80,0.2)!important;
  transition:all 0.25s ease!important;font-weight:600!important;
}
.streamlit-expanderHeader:hover,[data-testid="stExpander"] summary:hover{
  border-color:rgba(232,169,58,0.5)!important;
  box-shadow:0 4px 16px rgba(200,134,42,0.1)!important;
}

/* === PROGRESS BAR GOLD === */
.stProgress > div > div > div{
  background:linear-gradient(90deg,#c8862a,#e8a93a,#f5d48a)!important;
}

/* === SCROLLBAR GOLD === */
::-webkit-scrollbar{width:8px;height:8px}
::-webkit-scrollbar-track{background:rgba(252,248,238,0.5)}
::-webkit-scrollbar-thumb{
  background:linear-gradient(180deg,#e8a93a,#c8862a);
  border-radius:10px;border:1px solid rgba(255,255,255,0.3);
}
::-webkit-scrollbar-thumb:hover{background:linear-gradient(180deg,#f5d48a,#e8a93a)}

/* === SUBTILER PULS FÜR PRIMÄR-BUTTON === */
@keyframes goldPulse{
  0%,100%{box-shadow:0 8px 24px rgba(200,134,42,0.35), inset 0 1px 0 rgba(255,240,200,0.7)}
  50%{box-shadow:0 8px 32px rgba(232,169,58,0.55), inset 0 1px 0 rgba(255,240,200,0.9)}
}
.stButton>button[kind="primary"]{animation:goldPulse 2.8s ease-in-out infinite}

/* === SCHWEBENDE GOLD-PARTIKEL IM HINTERGRUND === */
@keyframes float1{0%,100%{transform:translate(0,0)}50%{transform:translate(40px,-30px)}}
@keyframes float2{0%,100%{transform:translate(0,0)}50%{transform:translate(-30px,40px)}}
@keyframes float3{0%,100%{transform:translate(0,0)}50%{transform:translate(25px,25px)}}
.stApp::after{
  content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background-image:
    radial-gradient(circle 3px at 12% 18%, rgba(232,169,58,0.45), transparent),
    radial-gradient(circle 2px at 88% 25%, rgba(245,212,138,0.6), transparent),
    radial-gradient(circle 2px at 25% 75%, rgba(232,169,58,0.4), transparent),
    radial-gradient(circle 3px at 75% 88%, rgba(245,212,138,0.5), transparent),
    radial-gradient(circle 2px at 50% 50%, rgba(232,169,58,0.3), transparent),
    radial-gradient(circle 2px at 95% 60%, rgba(245,212,138,0.4), transparent);
  animation:float1 18s ease-in-out infinite;
}

/* === ERFOLGS-/WARN-/INFO-ALERTS MIT EDLEM AKZENT === */
.stAlert[data-baseweb="notification"]{position:relative;overflow:hidden}
.stAlert[data-baseweb="notification"]::before{
  content:'';position:absolute;left:0;top:0;bottom:0;width:4px;
  background:linear-gradient(180deg,#f5d48a,#e8a93a,#c8862a);
}
div[data-testid="stAlertContentSuccess"]{
  background:linear-gradient(135deg,rgba(232,245,210,0.9) 0%,rgba(252,248,238,0.95) 100%)!important;
  border-left:4px solid #8aa84a!important;
}
div[data-testid="stAlertContentWarning"]{
  background:linear-gradient(135deg,rgba(252,238,210,0.9) 0%,rgba(255,253,247,0.95) 100%)!important;
  border-left:4px solid #e8a93a!important;
}
div[data-testid="stAlertContentInfo"]{
  background:linear-gradient(135deg,rgba(252,248,238,0.9) 0%,rgba(255,253,247,0.95) 100%)!important;
  border-left:4px solid #c8862a!important;
}
div[data-testid="stAlertContentError"]{
  background:linear-gradient(135deg,rgba(252,225,215,0.9) 0%,rgba(255,253,247,0.95) 100%)!important;
  border-left:4px solid #c84a2a!important;
}

/* === KAPITÄLCHEN BEI TAB-LABELS === */
.stTabs [data-baseweb="tab"]{text-transform:none;letter-spacing:0.03em}

/* === EDLE HORIZONTAL-TRENNER === */
hr{
  border:none!important;height:1px!important;
  background:linear-gradient(90deg,transparent,#e8a93a,transparent)!important;
  margin:1.5rem 0!important;
}

/* === CHECKBOX/TOGGLE GOLD === */
.stCheckbox label > div:first-child > div:first-child{
  border-color:rgba(200,160,80,0.4)!important;
}
.stCheckbox label > div:first-child[data-checked="true"]{
  background:linear-gradient(135deg,#f5d48a,#e8a93a)!important;
  border-color:#c8862a!important;
}

/* === EDLER RAHMEN UM CODE-BLÖCKE === */
code,.stCode{
  background:rgba(28,22,18,0.04)!important;
  border:1px solid rgba(200,160,80,0.2)!important;
  border-radius:8px!important;color:#7a5520!important;
}

/* === KAFFEE-WARMES SELECTION === */
::selection{background:rgba(245,212,138,0.5);color:#1a1612}

/* === STARKE LINKS === */
a{color:#c8862a!important;font-weight:600!important;text-decoration:none!important;
  background:linear-gradient(90deg,#c8862a,#e8a93a) bottom/0 1.5px no-repeat!important;
  transition:background-size 0.3s ease!important;padding-bottom:2px!important;}
a:hover{background-size:100% 1.5px!important;color:#e8a93a!important}

/* === MOBILE === */
@media(max-width:768px){
  .stTabs [data-baseweb="tab"]{font-size:11px!important;padding:6px 10px!important}
  h1{font-size:1.6em!important}
}
</style>""", unsafe_allow_html=True)

# ── SECRETS ──────────────────────────────────────────────────
def secret(k):
    try: return st.secrets[k]
    except: return os.environ.get(k,"")

OR_KEY     = secret("OPENROUTER_API_KEY")
TAVILY_KEY = secret("TAVILY_API_KEY")
YOU_KEY    = secret("YOU_API_KEY")
GOOGLE_KEY = secret("GOOGLE_API_KEY")
GOOGLE_CSE = secret("GOOGLE_CSE_ID")

# ── SESSION STATE ─────────────────────────────────────────────
# Wird bei JEDEM Rerun geprüft — falls ein Key fehlt (z.B. nach Cloud-Neustart),
# wird er wiederhergestellt statt mit AttributeError abzustürzen.
_SESSION_DEFAULTS = {
    "lager":[],"sim":[],"gwlog":[],"fotos":[],"fcnt":0,
    "feedback_log":[],"analyse_history":[],"mein_wissen":[],
    "preis_korrekturen":{},"chat_history":[],"vorabinfo":"",
    # Erweitertes Lern-System
    "verkauf_log":[],        # Echte Verkäufe mit Preis+Plattform
    "kategorie_wissen":{},   # Wissen pro Kategorie
    "beste_zeiten":{},       # Beste Verkaufszeiten
    "markt_notizen":{},      # Notizen zu Märkten
    "ki_korrekturen":[],     # Wo KI falsch lag
}
for k,v in _SESSION_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = (v.copy() if isinstance(v,(list,dict)) else v)

# Gespeicherte Lern-Daten von der Festplatte holen (nur einmal pro Session)
if not st.session_state.get("_lerndaten_geladen"):
    _gespeichert = lade_lerndaten()
    for _k, _v in _gespeichert.items():
        if _k in _LERN_KEYS and _v:
            st.session_state[_k] = _v
    st.session_state["_lerndaten_geladen"] = True

# ══════════════════════════════════════════════════════════════
# KI ENGINE — ULTIMATE
# ══════════════════════════════════════════════════════════════

# Vision-Fallback-Kette (6 Modelle, alle mit Guthaben zuverlässig)
VISION_KETTE = [
    "google/gemini-2.5-flash",
    "google/gemini-2.5-flash-lite",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "google/gemma-3-27b-it",
    "qwen/qwen-2.5-vl-72b-instruct",
]

# Ensemble-Modelle (3 beste gleichzeitig)
ENSEMBLE_VISION = [
    ("google/gemini-2.5-flash",      "🥇 Gemini 2.5 Flash"),
    ("google/gemini-2.5-flash-lite", "🥈 Gemini 2.5 Flash-Lite"),
    ("openai/gpt-4o",                "🥉 GPT-4o"),
]
ENSEMBLE_TEXT = [
    ("google/gemini-2.5-flash",      "🥇 Gemini 2.5"),
    ("google/gemini-2.5-flash-lite", "🥈 Gemini 2.5 Lite"),
    ("openai/gpt-4o-mini",           "🥉 GPT-4o-mini"),
]

def _client():
    return OpenAI(api_key=OR_KEY, base_url="https://openrouter.ai/api/v1")

def _hdrs():
    return {"HTTP-Referer":"https://marktradar.streamlit.app","X-Title":"MarktRadar"}

def baue_lern_kontext():
    """Gibt den kompletten Lern-Kontext für KI-Prompts zurück"""
    lern = ""
    if st.session_state.mein_wissen:
        lern += "\n\nMein persönliches Wissen (aus Erfahrung):\n"
        lern += "\n".join([f"- {w}" for w in st.session_state.mein_wissen[-10:]])
    if st.session_state.preis_korrekturen:
        lern += "\n\nEchte Verkaufspreise die ich erzielt habe:\n"
        lern += "\n".join([f"- {k}: €{v}" for k,v in list(st.session_state.preis_korrekturen.items())[-10:]])
    if st.session_state.verkauf_log:
        lern += "\n\nMeine letzten Verkäufe:\n"
        for v in st.session_state.verkauf_log[-5:]:
            lern += f"- {v['artikel']} für €{v['vk']} auf {v['plattform']} ({v['tage']} Tage)\n"
    if st.session_state.ki_korrekturen:
        lern += "\n\nWo ich die KI korrigiert habe:\n"
        lern += "\n".join([f"- {k}" for k in st.session_state.ki_korrekturen[-5:]])
    return lern


def komprimiere(b64, max_px=1024, q=80):
    """Robuste Bildkomprimierung — auch für große Handy-Fotos (Samsung etc.)"""
    try:
        from PIL import Image, ImageOps
        import io as _io
        roh = base64.b64decode(b64)
        img = Image.open(_io.BytesIO(roh))
        # EXIF-Rotation korrigieren (Handy-Fotos sind oft gedreht)
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass
        if img.mode != "RGB":
            img = img.convert("RGB")
        # Auf max_px verkleinern
        img.thumbnail((max_px, max_px), Image.Resampling.LANCZOS)
        buf = _io.BytesIO()
        img.save(buf, format="JPEG", quality=q, optimize=True)
        ergebnis = base64.b64encode(buf.getvalue()).decode()
        return ergebnis
    except Exception:
        # Wenn Komprimierung fehlschlägt: versuche wenigstens kleiner zu machen
        try:
            from PIL import Image
            import io as _io
            img = Image.open(_io.BytesIO(base64.b64decode(b64)))
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.thumbnail((800, 800))
            buf = _io.BytesIO()
            img.save(buf, format="JPEG", quality=70)
            return base64.b64encode(buf.getvalue()).decode()
        except Exception:
            return b64

def ki(prompt, bilder=None):
    """Einzelne KI mit Fallback-Kette + Cache (spart Kosten beim Testen)"""
    if not OR_KEY: return "❌ Kein API-Key!"
    # Cache: identische Anfragen wiederverwenden (gilt nur in dieser Session)
    import hashlib as _hl
    _bilder_sig = ""
    if bilder:
        try: _bilder_sig = "".join([(b[:60] if isinstance(b,str) else "") for b in bilder[:3]])
        except: pass
    _cache_key = _hl.md5((prompt[:500] + _bilder_sig).encode()).hexdigest()
    if "_ki_cache" not in st.session_state:
        st.session_state["_ki_cache"] = {}
    _cached = st.session_state["_ki_cache"].get(_cache_key)
    if _cached:
        return _cached
    c = _client()
    verweigerungen = ["tut mir leid","kann nicht helfen","cannot assist","i'm sorry"]
    try:
        if bilder:
            bilder_k = [komprimiere(b) for b in bilder[:4]]
            letzter_fehler = ""
            for model in VISION_KETTE:
                for versuch in range(2):
                    try:
                        inhalt = [{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b}"}} for b in bilder_k]
                        inhalt.append({"type":"text","text":prompt})
                        r = c.chat.completions.create(model=model,
                            messages=[{"role":"user","content":inhalt}],
                            max_tokens=1800, temperature=0.2, extra_headers=_hdrs())
                        a = r.choices[0].message.content
                        if a and len(a) > 80 and not any(v in a.lower() for v in verweigerungen):
                            st.session_state["_ki_cache"][_cache_key] = a
                            return a
                        break
                    except Exception as e:
                        letzter_fehler = str(e)[:120]
                        if "429" in str(e) and versuch == 0:
                            time.sleep(2)
                            continue
                        break
            return "❌ Vision-Analyse fehlgeschlagen. Letzter Fehler: " + letzter_fehler + " (Tipp: API-Key prüfen oder kleineres Foto)"
        else:
            r = c.chat.completions.create(model="openai/gpt-4o-mini",
                messages=[{"role":"user","content":prompt}],
                max_tokens=1500, temperature=0.2, extra_headers=_hdrs())
            _antwort = r.choices[0].message.content
            if _antwort:
                st.session_state["_ki_cache"][_cache_key] = _antwort
            return _antwort
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

def ensemble_ki(prompt, bilder=None, zeige_status=False, max_tokens=1200):
    """
    ULTIMATE ENSEMBLE:
    3 Top-Modelle arbeiten GLEICHZEITIG.
    Richter-KI (GPT-4o) fasst zu EINER perfekten Antwort zusammen.
    """
    if not OR_KEY: return ki(prompt, bilder=bilder)

    modelle = ENSEMBLE_VISION if bilder else ENSEMBLE_TEXT

    def ein_experte(info):
        model_id, name = info
        try:
            c2 = _oai.OpenAI(api_key=OR_KEY, base_url="https://openrouter.ai/api/v1")
            if bilder:
                bk = [komprimiere(b) for b in bilder[:3]]
                inhalt = [{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b}"}} for b in bk]
                inhalt.append({"type":"text","text":prompt})
                msgs = [{"role":"user","content":inhalt}]
            else:
                msgs = [{"role":"user","content":prompt}]
            r = c2.chat.completions.create(model=model_id, messages=msgs,
                max_tokens=max_tokens, temperature=0.2, extra_headers=_hdrs())
            a = r.choices[0].message.content
            if a and len(a) > 30: return (name, a)
        except: pass
        return (name, None)

    # Alle 3 gleichzeitig!
    antworten = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(ein_experte, m): m for m in modelle}
        for f in concurrent.futures.as_completed(futures):
            name, a = f.result()
            if a: antworten[name] = a

    if not antworten: return ki(prompt, bilder=bilder)
    if len(antworten) == 1: return list(antworten.values())[0]

    # Richter-KI fasst zusammen
    experten_text = "\n\n".join([f"[{n}]:\n{a[:700]}" for n,a in antworten.items()])
    return ki(
        f"Du bist Chef-Experte. {len(antworten)} Experten haben analysiert.\n"
        f"Erstelle EINE perfekte, vollständige finale Antwort auf Deutsch.\n"
        f"Nimm das Beste + Präziseste aus jeder Antwort.\n"
        f"Bei Preis-Unterschieden: nimm den Durchschnitt.\n"
        f"Experten-Analysen:\n{experten_text}\n\nFINALE ANTWORT:"
    )

# ── WEB-SUCHE ─────────────────────────────────────────────────
def hole_anzeigen(suchbegriff, max_treffer=4):
    """Sucht strukturierte Anzeigen-Treffer (Titel + URL + Snippet + Preis).
    Gibt eine Liste von Dicts zurück, jeder mit: titel, url, preis, snippet, quelle.
    Nutzt Tavily und DuckDuckGo, da beide URLs liefern (anders als Google CSE-Snippets)."""
    if not suchbegriff:
        return []
    treffer = []
    seen_urls = set()

    def _preis_aus(text):
        if not text: return None
        m = _re_ha.search(r"(\d{1,4}(?:[.,]\d{1,2})?)\s*(?:€|EUR|Euro)", text)
        if not m: return None
        try:
            p = float(m.group(1).replace(",","."))
            if 1 <= p <= 5000: return round(p)
        except: pass
        return None

    import re as _re_ha
    query = suchbegriff + " gebraucht Preis Deutschland"

    # Tavily liefert {title, url, content}
    try:
        if TAVILY_KEY:
            r = requests.post("https://api.tavily.com/search",
                json={"api_key":TAVILY_KEY,"query":query,"search_depth":"basic",
                      "max_results":8,"include_answer":False}, timeout=12)
            data = r.json()
            for res in (data.get("results") or [])[:8]:
                url = res.get("url","")
                if not url or url in seen_urls: continue
                titel = (res.get("title") or "")[:90]
                snippet = (res.get("content") or "")[:180]
                preis = _preis_aus(snippet) or _preis_aus(titel)
                # Quelle aus URL ableiten
                quelle = "Web"
                for q_name, q_dom in [("Kleinanzeigen","kleinanzeigen.de"),("eBay","ebay.de"),
                                       ("Vinted","vinted.de"),("Markt.de","markt.de"),
                                       ("Hood","hood.de"),("mobile.de","mobile.de"),
                                       ("Catawiki","catawiki"),("Etsy","etsy.com")]:
                    if q_dom in url.lower(): quelle = q_name; break
                treffer.append({"titel":titel,"url":url,"preis":preis,"snippet":snippet,"quelle":quelle})
                seen_urls.add(url)
    except Exception: pass

    # DuckDuckGo als Backup/Ergänzung (kein Key nötig)
    if len(treffer) < max_treffer:
        try:
            from ddgs import DDGS
            with DDGS() as d:
                res = list(d.text(query, region="de-de", max_results=8))
            for r in res[:8]:
                url = r.get("href") or r.get("url","")
                if not url or url in seen_urls: continue
                titel = (r.get("title") or "")[:90]
                snippet = (r.get("body") or "")[:180]
                preis = _preis_aus(snippet) or _preis_aus(titel)
                quelle = "Web"
                for q_name, q_dom in [("Kleinanzeigen","kleinanzeigen.de"),("eBay","ebay.de"),
                                       ("Vinted","vinted.de"),("Markt.de","markt.de"),
                                       ("Hood","hood.de"),("mobile.de","mobile.de")]:
                    if q_dom in url.lower(): quelle = q_name; break
                treffer.append({"titel":titel,"url":url,"preis":preis,"snippet":snippet,"quelle":quelle})
                seen_urls.add(url)
        except Exception: pass

    # Treffer MIT Preis nach vorne sortieren — die sind nützlicher
    treffer.sort(key=lambda t: (0 if t["preis"] else 1, -(t["preis"] or 0)))
    return treffer[:max_treffer]

def extrahiere_preise(text):
    """Zieht echte Euro-Preise aus Web-Text und gibt eine Auswertung zurück.
    Filtert Unsinn (zu billig/teuer) raus und liefert Spanne + Median."""
    if not text:
        return None
    import re as _re_p, statistics as _stat_p
    # Findet: 49€, € 49, 49 EUR, 49,90 €, 1.299 € usw.
    roh = _re_p.findall(r"(?:€\s*)?(\d{1,3}(?:[.\s]\d{3})*(?:,\d{1,2})?)\s*(?:€|EUR|Euro)|(?:€|EUR)\s*(\d{1,3}(?:[.\s]\d{3})*(?:,\d{1,2})?)", text)
    preise = []
    for a, b in roh:
        s = (a or b).replace(" ","").replace(".","").replace(",",".")
        try:
            p = float(s)
            # Plausibel für Secondhand: 1€ bis 5000€
            if 1 <= p <= 5000:
                preise.append(p)
        except Exception:
            continue
    if len(preise) < 2:
        return None
    preise.sort()
    # Extreme Ausreißer kappen (oberste/unterste 10%)
    n = len(preise)
    if n >= 6:
        schnitt = max(1, n // 10)
        preise = preise[schnitt:n-schnitt]
    median = round(_stat_p.median(preise))
    return {
        "median": median,
        "min": round(min(preise)),
        "max": round(max(preise)),
        "anzahl": len(preise),
    }

def google_suche(query):
    if not GOOGLE_KEY or not GOOGLE_CSE: return None
    try:
        r = requests.get("https://www.googleapis.com/customsearch/v1",
            params={"key":GOOGLE_KEY,"cx":GOOGLE_CSE,"q":query,"num":5,"hl":"de","gl":"de"},
            timeout=10)
        data = r.json()
        if data.get("items"):
            teile = ["🔍 GOOGLE:"]
            for item in data["items"][:6]:
                teile.append("• " + item.get("title","") + ": " + item.get("snippet","")[:300])
            return "\n".join(teile)
    except: pass
    return None

def tavily_suche(query):
    if not TAVILY_KEY: return None
    try:
        # Deutsch erzwingen durch deutsche Suchanfrage
        query_de = query + " Deutschland deutsch Preis gebraucht"
        # KEINE include_domains mehr — Tavily durchsucht das GANZE Web nach Preisen
        # (eBay, Kleinanzeigen, Vinted, Etsy, Catawiki, Auktionshäuser, Foren, Shops ...)
        r = requests.post("https://api.tavily.com/search",
            json={"api_key":TAVILY_KEY,"query":query_de,"search_depth":"advanced",
                  "max_results":12,"include_answer":True},
            timeout=15)
        data = r.json()
        teile = []
        if data.get("answer"):
            antwort = str(data["answer"])
            # Nur verwenden wenn auf Deutsch oder relevant
            if any(w in antwort.lower() for w in ["euro","€","preis","kaufen","verkauf","deutschland"]):
                teile.append(antwort)
        if data.get("results"):
            for res in data["results"][:10]:
                titel = res.get("title","")
                inhalt = res.get("content","")[:300]
                # Alles mitnehmen was nach Preis/Deutschland aussieht (egal welche Seite)
                url = res.get("url","")
                if "€" in inhalt or "eur" in inhalt.lower() or "preis" in inhalt.lower() or ".de" in url:
                    teile.append("• " + titel + ": " + inhalt)
        return "\n".join(teile) if teile else None
    except: pass
    return None

def you_suche(query):
    if not YOU_KEY: return None
    try:
        r = requests.get("https://api.ydc-index.io/search",
            headers={"X-API-Key":YOU_KEY},
            params={"query":query,"num_web_results":5}, timeout=15)
        data = r.json()
        if data.get("hits"):
            teile = ["🔍 YOU.COM:"]
            for hit in data["hits"][:3]:
                s = hit.get("snippets",[])
                if s: teile.append("• " + hit.get("title","") + ": " + str(s[0])[:150])
            return "\n".join(teile) if len(teile)>1 else None
    except: pass
    return None

def ddg_suche(query):
    """DuckDuckGo — braucht KEINEN Schlüssel. Wird auf Servern oft gedrosselt,
    daher nur als Bonus-Quelle. Schadet nie, kostet nichts."""
    try:
        from ddgs import DDGS
        teile = ["🔍 DUCKDUCKGO:"]
        with DDGS() as d:
            res = list(d.text(query + " Preis Euro Deutschland", region="de-de", max_results=6))
        for r in res[:5]:
            titel = str(r.get("title",""))
            body = str(r.get("body",""))[:250]
            teile.append("• " + titel + ": " + body)
        return "\n".join(teile) if len(teile) > 1 else None
    except Exception:
        return None

def multi_suche(query):
    """Google + Tavily + You.com gleichzeitig"""
    ergebnisse = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        fg = ex.submit(google_suche, query)
        ft = ex.submit(tavily_suche, query)
        fy = ex.submit(you_suche, query)
        if fg.result(): ergebnisse["Google"] = fg.result()
        if ft.result(): ergebnisse["Tavily"] = ft.result()
        if fy.result(): ergebnisse["You.com"] = fy.result()
    if not ergebnisse: return None
    return "\n\n".join([v for v in ergebnisse.values()])

def preis_ensemble(artikel, zustand, web_daten):
    """3 KIs bewerten Preise gleichzeitig → Konsens"""
    if not web_daten: return None
    prompt = (
        f"Preisexperte Secondhand Deutschland.\n"
        f"Artikel: {artikel} | Zustand: {zustand}\n"
        f"Web-Daten:\n{web_daten[:1000]}\n\n"
        f"Bewerte: eBay €X | Kleinanzeigen €X | Flohmarkt €X | Empfehlung €X | Trend ↑↓→"
    )
    modelle_p = [
        ("google/gemini-2.5-flash", "G2.5"),
        ("google/gemini-2.5-flash",       "G25"),
        ("openai/gpt-4o-mini",            "GPT"),
    ]
    def p_experte(info):
        mid, name = info
        try:
            c2 = _oai.OpenAI(api_key=OR_KEY, base_url="https://openrouter.ai/api/v1")
            r = c2.chat.completions.create(model=mid,
                messages=[{"role":"user","content":prompt}],
                max_tokens=200, extra_headers=_hdrs())
            a = r.choices[0].message.content
            if a and "€" in a: return (name, a)
        except: pass
        return (name, None)

    pw = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        futures = {ex.submit(p_experte, m): m for m in modelle_p}
        for f in concurrent.futures.as_completed(futures):
            n, a = f.result()
            if a: pw[n] = a

    if not pw: return None
    if len(pw) == 1: return list(pw.values())[0]
    pt = "\n".join([f"[{n}]: {a}" for n,a in pw.items()])
    return ki(
        f"3 Preisexperten haben Preise geschätzt:\n{pt}\n\n"
        f"Erstelle finalen Preis-Konsens. NUR konkrete Einzelzahlen — KEINE Spannen wie €45-55!\n"
        f"Format (genau so):\n"
        f"eBay: €X | Kleinanzeigen: €X | Vinted: €X | Facebook: €X | Flohmarkt: €X | Empfehlung: €X | Trend: ↑/↓/→\n"
        f"Begründung: [1 Satz warum dieser Preis realistisch ist]"
    )

# ── URL LESEN ─────────────────────────────────────────────────
_BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

def lies_url(url):
    """Lädt Text von URL — versucht 2× mit echtem Browser-Header."""
    letzter_fehler = ""
    for versuch in range(2):
        try:
            r = requests.get(url, headers=_BROWSER_HEADERS, timeout=20, allow_redirects=True)
            if r.status_code == 200 and r.text:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(r.text, "html.parser")
                for t in soup(["script","style","nav","footer","header"]): t.decompose()
                zeilen = [z.strip() for z in soup.get_text("\n").split("\n") if len(z.strip())>15]
                return "\n".join(zeilen[:150])[:5000]
            else:
                letzter_fehler = f"HTTP {r.status_code}"
        except requests.exceptions.Timeout:
            letzter_fehler = "Timeout"
        except Exception as e:
            letzter_fehler = str(e)[:80]
        if versuch == 0:
            time.sleep(1)
    return f"[URL-Fehler: {letzter_fehler}]"

# ── BILDER VON URL LADEN ─────────────────────────────────────
def lade_bilder_von_url(url):
    """
    Lädt ALLE Bilder von einer Webseite (z.B. Lüdtke Auktion).
    Funktioniert auch mit verschwommenen/schlechten Bildern!
    Gibt Liste von Base64-codierten Bildern zurück.
    """
    bilder_b64 = []
    try:
        r = requests.get(url, headers=_BROWSER_HEADERS, timeout=20, allow_redirects=True)
        if r.status_code != 200:
            return bilder_b64
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")

        # Finde alle Bild-URLs
        bild_urls = []

        # 1. Standard img Tags
        for img in soup.find_all("img"):
            src = img.get("src","") or img.get("data-src","") or img.get("data-lazy","")
            if src and len(src) > 5:
                if not src.startswith("http"):
                    base = "/".join(url.split("/")[:3])
                    src = base + ("" if src.startswith("/") else "/") + src
                # Ausschließen: Icons, Logos, Buttons
                if any(x in src.lower() for x in ["logo","icon","wait","banner","button"]): continue
                bild_urls.append(src)

        # 2. Links auf Bilder (wie bei Lüdtke: href auf bild.php)
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if any(x in href.lower() for x in ["bild.php","bild=",".jpg",".jpeg",".png",".webp"]):
                if not href.startswith("http"):
                    base = "/".join(url.split("/")[:3])
                    href = base + ("" if href.startswith("/") else "/") + href
                if href not in bild_urls:
                    bild_urls.append(href)

        # 3. Meta og:image
        for meta in soup.find_all("meta", property="og:image"):
            c = meta.get("content","")
            if c and c not in bild_urls: bild_urls.append(c)

        # Lade max. 8 Bilder (genug für gute Analyse)
        bild_urls = list(dict.fromkeys(bild_urls))[:8]

        for bild_url in bild_urls:
            try:
                br = requests.get(bild_url, headers=_BROWSER_HEADERS, timeout=10)
                if br.status_code == 200 and len(br.content) > 1000:
                    b64 = base64.b64encode(br.content).decode()
                    bilder_b64.append(b64)
            except: continue

    except Exception as e:
        pass

    return bilder_b64


# ── HEADER ────────────────────────────────────────────────────
st.markdown("""
<style>
@keyframes shimmer{
  0%{background-position:-200% center}
  100%{background-position:200% center}
}
@keyframes crown{
  0%,100%{transform:translateY(0) rotate(-2deg)}
  50%{transform:translateY(-4px) rotate(2deg)}
}
.luxus-header{
  background:linear-gradient(135deg, #1a1612 0%, #2a2218 50%, #1a1612 100%);
  padding:32px 28px;border-radius:24px;margin-bottom:24px;text-align:center;
  border:1px solid rgba(232,169,58,0.3);position:relative;overflow:hidden;
  box-shadow:0 24px 60px rgba(28,22,18,0.25), inset 0 1px 0 rgba(245,212,138,0.15);
}
.luxus-header::before{
  content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,transparent,#f5d48a,#e8a93a,#f5d48a,transparent);
}
.luxus-header::after{
  content:'';position:absolute;inset:0;pointer-events:none;
  background:radial-gradient(ellipse 400px 200px at 50% 0%, rgba(232,169,58,0.18) 0%, transparent 70%);
}
.luxus-crown{font-size:2.6em;display:inline-block;animation:crown 4s ease-in-out infinite;filter:drop-shadow(0 4px 12px rgba(232,169,58,0.5))}
.luxus-title{
  font-family:'Playfair Display',serif;
  background:linear-gradient(90deg,#c8862a 0%,#f5d48a 25%,#fff4d6 50%,#f5d48a 75%,#c8862a 100%);
  background-size:200% auto;
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  margin:6px 0 0;font-size:2.4em;font-weight:900;letter-spacing:-0.02em;
  animation:shimmer 6s linear infinite;
}
.luxus-sub{
  color:#a89878;margin:14px 0 0;font-size:11px;letter-spacing:4px;font-weight:600;
  text-transform:uppercase;
}
.luxus-sep{display:inline-block;margin:0 10px;color:#e8a93a}
</style>
<div class='luxus-header'>
  <div class='luxus-crown'>👑</div>
  <h1 class='luxus-title'>MarktRadar OS PRO</h1>
  <p class='luxus-sub'>
    Kleinanzeigen <span class='luxus-sep'>◆</span>
    Vinted <span class='luxus-sep'>◆</span>
    Facebook <span class='luxus-sep'>◆</span>
    eBay <span class='luxus-sep'>◆</span>
    Flohmärkte
  </p>
</div>""", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────
T = st.tabs([
    "🔍 Analyse","💬 Anschreib","📦 Lager","📚 OCR",
    "🔧 Reparatur","📈 Trends","🎭 Verhandlung","📸 Foto-Coach",
    "🗺️ Flohmärkte","🔬 Marken","📅 Timing","✨ Anzeigen-KI",
    "🤖 Chat","🔎 Konkurrenz","📊 Business","📦 Lager-KI",
    "📰 Markt-News","✍️ Profi-Text",
])

# ════════════════════════════════════════════════════════════
# TAB 1 — ANALYSE (ULTIMATE)
# ════════════════════════════════════════════════════════════
with T[0]:
    st.header("🔍 Artikel-Analyse — Ultimate Edition")
    st.markdown("**9 Vision-KIs · 3 Experten gleichzeitig · Google+Tavily+You.com · Richter-KI**")

    # ── SUCH-SCHLÜSSEL TESTEN ──
    with st.expander("🔧 Such-Schlüssel testen (falls 'keine Web-Daten')"):
        st.caption("Prüft jeden Schlüssel einzeln. So siehst du, welcher funktioniert.")
        if st.button("▶️ Jetzt alle 3 Suchmaschinen testen", key="test_keys"):
            # Google
            if not GOOGLE_KEY or not GOOGLE_CSE:
                st.error("🔴 Google: kein Schlüssel/CSE in Streamlit eingetragen")
            else:
                g = google_suche("Stereoanlage gebraucht Preis")
                if g: st.success("🟢 Google funktioniert!")
                else: st.error("🔴 Google antwortet nicht — Tageslimit (100/Tag) erreicht oder Schlüssel ungültig")
            # Tavily
            if not TAVILY_KEY:
                st.error("🔴 Tavily: kein Schlüssel in Streamlit eingetragen")
            else:
                t = tavily_suche("Stereoanlage gebraucht Preis")
                if t: st.success("🟢 Tavily funktioniert!")
                else: st.error("🔴 Tavily antwortet nicht — Monatslimit erreicht oder Schlüssel ungültig")
            # You.com
            if not YOU_KEY:
                st.error("🔴 You.com: kein Schlüssel in Streamlit eingetragen")
            else:
                y = you_suche("Stereoanlage gebraucht Preis")
                if y: st.success("🟢 You.com funktioniert!")
                else: st.error("🔴 You.com antwortet nicht — Limit erreicht oder Schlüssel ungültig")
            # DuckDuckGo (kein Schlüssel nötig)
            dd = ddg_suche("Stereoanlage gebraucht")
            if dd: st.success("🟢 DuckDuckGo funktioniert! (braucht keinen Schlüssel)")
            else: st.error("🔴 DuckDuckGo antwortet nicht — wird auf Servern oft geblockt (normal)")
            st.info("Tipp: Es reicht, wenn EINE Suchmaschine grün ist. Roter Google-Schlüssel = meist nur Tageslimit, morgen wieder ok.")

    # ── MODUS-WAHL ──
    modus = st.radio("⚡ Analyse-Modus:",
        ["🚀 Ultimate (3 Experten + Richter)", "⚡ Schnell (1 KI — schneller)"],
        horizontal=True, key="a_modus")

    typ = st.radio("Was analysieren?",["📸 Foto","🔗 Link","📸 + 🔗 Beides"],horizontal=True,key="a_typ")
    url_text = ""
    url_inp  = ""

    if "Foto" in typ:
        st.markdown("##### 📷 Fotos hochladen")
        st.caption("📱 Foto auswählen → 'Foto hinzufügen' → wiederholen für mehr")
        neu_foto = st.file_uploader("Foto auswählen",type=["jpg","jpeg","png","webp"],
            accept_multiple_files=False, key=f"fu_{st.session_state.fcnt}")
        c1,c2 = st.columns(2)
        with c1:
            if st.button("➕ Foto hinzufügen",type="primary",use_container_width=True,key="foto_add"):
                if neu_foto:
                    try:
                        if len(st.session_state.fotos) >= 8:
                            st.warning("⚠️ Maximal 8 Fotos pro Analyse — das reicht der KI völlig. Erst analysieren oder löschen.")
                        else:
                            neu_foto.seek(0)
                            roh_bytes = neu_foto.read()
                            roh_b64 = base64.b64encode(roh_bytes).decode()
                            del roh_bytes  # Roh-Foto sofort aus dem Speicher (S23-Fotos sind riesig)
                            # SOFORT komprimieren (große Handy-Fotos verkleinern!)
                            b64 = komprimiere(roh_b64)
                            del roh_b64
                            if b64 not in st.session_state.fotos:
                                st.session_state.fotos.append(b64)
                            st.session_state.fcnt += 1
                            st.rerun()
                    except Exception as e:
                        st.error(f"⚠️ Foto konnte nicht verarbeitet werden — bitte erneut versuchen. ({str(e)[:60]})")
                else: st.warning("Zuerst Foto auswählen!")
        with c2:
            if st.button("🗑️ Alle löschen",use_container_width=True,key="foto_clear"):
                st.session_state.fotos=[]; st.session_state.fcnt+=1; st.rerun()
        n = len(st.session_state.fotos)
        if n > 0:
            st.success(f"✅ {n} Foto(s) bereit!")
            cols = st.columns(min(n,3))
            for i,b64 in enumerate(st.session_state.fotos):
                with cols[i%3]: st.image(base64.b64decode(b64),caption=f"Foto {i+1}",use_column_width=True)
        else:
            st.info("📷 Foto auswählen → 'Foto hinzufügen' drücken!")

    if "Link" in typ:
        url_inp = st.text_input("🔗 Link",placeholder="https://luedtke-auktion-online.de/...",key="a_url")

    st.markdown("---")
    col1,col2 = st.columns([2,1])
    with col1:
        beschr = st.text_area("📝 Beschreibung (optional)",height=70,key="a_beschr")
    with col2:
        st.markdown("**🔍 Gebrauchsspuren**")
        gebrauch = st.slider("",1,100,15,5,key="a_gebrauch")
        if   gebrauch<=20: st.success(f"🟢 {gebrauch}% Kaum Spuren")
        elif gebrauch<=50: st.warning(f"🟡 {gebrauch}% Gebraucht")
        elif gebrauch<=80: st.error(f"🔴 {gebrauch}% Stark gebraucht")
        else:               st.error(f"⛔ {gebrauch}% Sehr stark")
        st.markdown("**🔧 Defekt?**")
        defekt_ja = st.radio("",["❓ Weiß nicht","✅ Nein","❌ Ja — defekt"],key="a_defekt_radio")

    hat_fotos = len(st.session_state.fotos) > 0
    hat_url   = bool(url_inp.strip())

    # ── VERLAUF anzeigen ──
    if st.session_state.analyse_history:
        with st.expander(f"🔄 Letzte Analysen ({len(st.session_state.analyse_history)})"):
            for i, h in enumerate(reversed(st.session_state.analyse_history[-10:])):
                st.markdown(f"**{h['datum']}** — {h['artikel']} | Zustand: {h['zustand']} | {h['ergebnis'][:80]}...")
            if st.button("🗑️ Verlauf löschen", key="verlauf_clear"):
                st.session_state.analyse_history = []; st.rerun()

    if st.button("🚀 ULTIMATE ANALYSE STARTEN",type="primary",use_container_width=True,key="a_start"):
        if not (hat_fotos or hat_url or beschr.strip()):
            st.warning("⚠️ Bitte Foto hochladen, Link eingeben oder beschreiben!")
        else:
            if   gebrauch<=20: g_beschr=f"Kaum Gebrauchsspuren ({gebrauch}%)"
            elif gebrauch<=50: g_beschr=f"Sichtbare Gebrauchsspuren ({gebrauch}%)"
            elif gebrauch<=80: g_beschr=f"Starke Gebrauchsspuren ({gebrauch}%)"
            else:               g_beschr=f"Sehr starke Gebrauchsspuren ({gebrauch}%)"
            if "Nein" in defekt_ja: d_beschr="Kein Defekt"
            elif "Ja"  in defekt_ja: d_beschr="DEFEKT!"
            else:                    d_beschr="Defekt unbekannt"

            schnell_modus = "Schnell" in modus

            # ── STUFE 1: Daten + Vorab-KI ──
            with st.status("📡 Stufe 1: Daten sammeln + KI-Vorab-Scan...",expanded=True):
                # Auto-Kategorie
                if hat_fotos and not schnell_modus:
                    st.write("🏷️ Auto-Kategorie erkennen...")
                    auto_kat = ki(
                        "Was für ein Artikel ist das? Antworte NUR mit einer Kategorie: "
                        "Kleidung / Elektronik / Porzellan & Keramik / Antiquität / Spielzeug / "
                        "Möbel / Bücher & Medien / Schmuck / Werkzeug / Sonstiges",
                        bilder=st.session_state.fotos[:1]
                    )
                    st.info(f"🏷️ Erkannte Kategorie: **{auto_kat.strip()}**")
                    st.session_state["auto_kat"] = auto_kat.strip()

                if hat_url:
                    url_text = lies_url(url_inp)
                    if url_text.startswith("[URL"):
                        _fehler_grund = url_text.replace("[URL-Fehler:","").replace("]","").strip()
                        st.warning(
                            f"⚠️ Webseite konnte nicht geladen werden ({_fehler_grund}). "
                            "Die Analyse läuft trotzdem mit den Fotos weiter."
                        )
                    else:
                        st.success(f"✅ {len(url_text)} Zeichen ausgelesen")
                        url_ki = ki("Secondhand-Experte. Extrahiere: Artikel, Preis, Zustand. Kurz Deutsch: " + url_text[:2000])
                        st.info("📄 "+url_ki)
                        artikel_name = url_ki.split("\n")[0][:40]
                        g = google_suche(artikel_name+" Wert Preis")
                        if g: url_text += "\nGOOGLE:\n" + g[:300]

                    # ── BILDER VON WEBSEITE LADEN ──
                    st.write("🖼️ Lade alle Bilder von der Webseite...")
                    url_bilder = lade_bilder_von_url(url_inp)
                    if url_bilder:
                        st.success(f"✅ {len(url_bilder)} Bilder von der Webseite geladen!")
                        # Bilder anzeigen
                        cols = st.columns(min(len(url_bilder), 4))
                        for i, b64 in enumerate(url_bilder):
                            try:
                                with cols[i%4]:
                                    st.image(base64.b64decode(b64), caption=f"Bild {i+1}", use_column_width=True)
                            except: pass
                        # Zu Analyse-Fotos hinzufügen
                        for b64 in url_bilder:
                            if b64 not in st.session_state.fotos:
                                st.session_state.fotos.append(b64)
                        st.success(f"✅ Alle {len(url_bilder)} Bilder für KI-Analyse bereit!")
                        hat_fotos = True  # Jetzt haben wir Fotos!
                    else:
                        st.info("ℹ️ Keine Bilder auf der Seite gefunden")
                if hat_fotos:
                    st.success(f"✅ {len(st.session_state.fotos)} Foto(s) bereit")
                    if not schnell_modus:
                        st.write("🔭 4 Vision-KIs scannen gleichzeitig vor...")
                        scan_modelle = [
                            ("google/gemini-2.5-flash","Gemini 2.5"),
                            ("google/gemini-2.5-flash-lite","Gemini 2.5 Lite"),
                            ("openai/gpt-4o","GPT-4o"),
                            ("openai/gpt-4o-mini","GPT-4o mini"),
                        ]
                        # Stufe 1 = nur grobe Vorab-Erkennung → kleinere Bilder reichen (spart Kosten)
                        bilder_vorab = [komprimiere(b, max_px=640, q=75) for b in st.session_state.fotos[:2]]
                        def vorab_scan(info):
                            mid, name = info
                            try:
                                c2 = _oai.OpenAI(api_key=OR_KEY,base_url="https://openrouter.ai/api/v1")
                                bk = bilder_vorab
                                inhalt=[{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b}"}} for b in bk]
                                inhalt.append({"type":"text","text":"Was siehst du? Artikel, Marke, Besonderheiten. Kurz Deutsch."})
                                r = c2.chat.completions.create(model=mid,
                                    messages=[{"role":"user","content":inhalt}],
                                    max_tokens=300, extra_headers=_hdrs())
                                a = r.choices[0].message.content
                                if a and len(a)>20: return (name,a)
                            except: pass
                            return (name,None)
                        vorab = {}
                        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
                            fs={ex.submit(vorab_scan,m):m for m in scan_modelle}
                            for f in concurrent.futures.as_completed(fs):
                                n,a=f.result()
                                if a: vorab[n]=a; st.write(f"✅ {n} bereit!")
                        if vorab:
                            st.session_state.vorabinfo="\n\n".join([f"[{n}]: {a}" for n,a in vorab.items()])
                            st.success(f"✅ {len(vorab)} KIs haben Fotos vorgelesen!")

            # ── STUFE 2: ANALYSE ──
            vorab_k = ("\n\nVORAB:\n" + st.session_state.vorabinfo) if st.session_state.get("vorabinfo","") else ""
            kat_k = ("\nErkannte Kategorie: " + st.session_state.get("auto_kat","")) if st.session_state.get("auto_kat") else ""
            lern=""
            if st.session_state.mein_wissen:
                lern += "\n\nMein Wissen:\n" + "\n".join([f"- {w}" for w in st.session_state.mein_wissen[-10:]])
            if st.session_state.preis_korrekturen:
                lern += "\n\nEchte Preise:\n" + "\n".join([f"- {k}: \u20ac{v}" for k,v in list(st.session_state.preis_korrekturen.items())[-5:]])
            extra=""
            if beschr.strip(): extra+=f" Händler: {beschr}."
            if url_text and not url_text.startswith("[URL"): extra += "\n\nWebseite:\n" + url_text[:1500]
            prompt = (
                "Ich bin Händler (Kleinanzeigen,Vinted,Facebook,eBay,Flohmärkte)." + kat_k + "\n"
                "Vom Händler angegeben — Gebrauchsspuren: " + g_beschr + "\n"
                "Vom Händler angegeben — Defekt: " + d_beschr + extra + vorab_k + lern + "\n\n"
                "Analysiere JEDEN sichtbaren Artikel im Bild. Auf Deutsch. Sei absoluter Profi-Experte!\n\n"

                "Für JEDEN Artikel:\n"
                "**Artikel: [Name]**\n\n"

                "📋 ARTIKEL-IDENTIFIKATION:\n"
                "- Was genau? [Marke, Modell, Material, Herstellungsland]\n"
                "- Alter: [Herstellungsjahr / Epoche / Herkunft / Antik?]\n"
                "- Seriennummer/Stempel: [falls sichtbar]\n\n"

                "🔍 ZUSTAND-ANALYSE (JEDES DETAIL!):\n"
                "Schaue das Bild EXTREM GENAU an — auch verschwommene Bereiche!\n"
                "- Gesamtzustand: [Wie neu / Sehr gut / Gut / Gebraucht / Stark gebraucht / Beschädigt]\n"
                "- Gebrauchsspuren-Grad: X% (0=neu, 100=sehr stark)\n\n"
                "JEDE sichtbare Gebrauchsspur einzeln:\n"
                "  • Kratzer: [Wo genau? Tiefe? Größe? Anzahl?]\n"
                "  • Dellen/Beulen: [Wo genau? Größe?]\n"
                "  • Chips/Absplitterungen: [Wo genau? Größe?]\n"
                "  • Verfärbungen/Flecken: [Wo? Farbe? Größe?]\n"
                "  • Risse/Brüche: [Wo? Länge?]\n"
                "  • Rost/Oxidation: [Wo? Ausmaß?]\n"
                "  • Abnutzung: [Wo? Art der Abnutzung?]\n"
                "  • Fehlende Teile: [Was fehlt?]\n"
                "  • Sonstiges: [Alles was auffällt]\n"
                "  → Falls NICHTS sichtbar: 'Keine erkennbaren Mängel'\n\n"

                "DEFEKT-ANALYSE:\n"
                "- Defekt-Status: [Funktionsfähig / Teildefekt / Voll defekt / Unklar]\n"
                "- Sichtbare Defekte: [Was ist kaputt oder fehlt?]\n"
                "- Preisminderung durch Mängel: -€X (wegen [Grund])\n"
                "- Ohne Mängel wäre Wert: €X\n\n"

                "- Verkäuflichkeit: 🟢schnell (1-7T) / 🟡mittel (1-4W) / 🔴langsam (Monate)\n\n"

                "💰 PREISE (NUR eine konkrete Zahl — keine Spannen!):\n"
                "Im aktuellen Zustand (" + g_beschr + "):\n"
                "WICHTIG: ALLE 5 Preise PFLICHT — KEINE darf fehlen!\n"
                "- eBay: €X\n"
                "- Kleinanzeigen: €X\n"
                "- Vinted: €X\n"
                "- Facebook: €X\n"
                "- Flohmarkt: €X\n"
                "- Max. Ankaufspreis jetzt: €X\n\n"
                "Nach Aufbereitung (gereinigt/repariert/wie neu):\n"
                "WICHTIG: ALLE 3 Preise PFLICHT:\n"
                "- eBay optimal: €X (+€X durch Aufbereitung)\n"
                "- Kleinanzeigen optimal: €X\n"
                "- Flohmarkt optimal: €X\n"
                "- Mehrwert gesamt: +€X (+X%)\n\n"

                "🏆 BESTE PLATTFORM: [Welche + warum] für €X\n"
                "🎯 KONFIDENZ: Identifikation X% | Preisschätzung X% | Gesamt X%\n"
                "⚠️ FÄLSCHUNGS-CHECK: [Niedrig/Mittel/Hoch] | Red Flags: [oder 'keine']\n"
                "✨ AUFBEREITUNG: [Methode + Kosten + Wertsteigerung +€X]\n"
                "👥 ZIELGRUPPE: [Wer kauft + wo finden]\n"
                "📅 TIMING: [Beste Monate] | Jetzt verkaufen: [Ja/Nein/Warten bis...]\n"
                "📝 FERTIGE ANZEIGE: Titel:[max 60Z] | Text:[3 überzeugende Sätze] | Preis:€X\n"
                "🗺️ BESTER BERLINER MARKT: 🥇[Markt+Tag+Preis+Uhrzeit] 🥈[Markt+€X]\n"
                "🌟 RARITÄT: [Seltenheit + Höchstpreis bei Sammler]\n"
                "💰 GEWINN-RECHNUNG: EK€X + Aufbereitung€X → VK€X → Gebühren€X → Netto€X → ROI X%\n"
                "---\n"
                "GESAMT ALLE ARTIKEL: €X | Wertvollster: [Name] | Sofort verkaufen: [Name]"
            )

            if schnell_modus:
                # SCHNELL-MODUS: 1 KI direkt
                with st.status("⚡ Schnell-Analyse...",expanded=True):
                    st.write("⚡ Schnell-Modus: 1 KI direkt...")
                    ergebnis = ki(prompt, bilder=st.session_state.fotos if hat_fotos else None)
                    st.markdown(ergebnis)
                    st.session_state["ana_ergebnis"] = ergebnis
            else:
                # ULTIMATE-MODUS: 4 Experten gleichzeitig
                with st.status("🔬 Stufe 2: 3 Experten-KIs + Richter analysieren...",expanded=True):
                    vorab_k = ("\n\nVORAB:\n" + st.session_state.vorabinfo) if st.session_state.get("vorabinfo","") else ""
                    kat_k = ("\nErkannte Kategorie: " + st.session_state.get("auto_kat","")) if st.session_state.get("auto_kat") else ""
                    lern = ""
                    # Eigene echte Flohmarkt-Verkäufe ZUERST und mit Nachdruck (wichtigste Datenquelle!)
                    floh_verkaeufe = [v for v in st.session_state.get("verkauf_log",[]) if v.get("plattform")=="Flohmarkt"]
                    if floh_verkaeufe:
                        lern += "\n\n⚠️ MEINE ECHTEN FLOHMARKT-VERKÄUFE (das sind REALE Barpreise die ich am Stand bekommen habe — richte den FLOHMARKT-WERT NACH DIESEN, nicht nach Online-Preisen!):\n"
                        lern += "\n".join([f"- {v['artikel']} ({v.get('zustand','?')}): €{v['vk']} bar in {v.get('tage','?')} Tagen verkauft" for v in floh_verkaeufe[-12:]])
                    if st.session_state.mein_wissen:
                        lern += "\n\nMein Wissen:\n" + "\n".join([f"- {w}" for w in st.session_state.mein_wissen[-10:]])
                    if st.session_state.preis_korrekturen:
                        lern += "\n\nEchte Preise:\n" + "\n".join([f"- {k}: \u20ac{v}" for k,v in list(st.session_state.preis_korrekturen.items())[-10:]])
                    extra = ""
                    if beschr.strip(): extra += " Händler: " + beschr + "."
                    if url_text and not url_text.startswith("[URL"): extra += "\n\nWebseite:\n" + url_text[:1500]

                    analyse_prompt = (
                        "Du bist Profi-Experte für Secondhand/Flohmarkt in Deutschland.\n"
                        "Ich bin Händler (Kleinanzeigen, Vinted, Facebook, eBay, Flohmärkte)." + kat_k + "\n"
                        "Gebrauchsspuren: " + g_beschr + "\n"
                        "Defekt: " + d_beschr + extra + vorab_k + lern + "\n\n"
                        "Analysiere das Bild. Auf DEUTSCH. KEINE chinesischen Zeichen!\n\n"

                        "GANZ WICHTIG — Beginne IMMER mit diesen 3 Kernwerten (eine konkrete Zahl, KEINE Spanne!):\n"
                        "PREIS-REGELN (damit gleiche Artikel gleiche Preise bekommen):\n"
                        "- Schätze NÜCHTERN den marktüblichen Durchschnittspreis, NICHT den Höchstpreis.\n"
                        "- Runde auf glatte Zehner (z.B. 120, nicht 117).\n"
                        "- Bei Unsicherheit: nimm die MITTE der realistischen Spanne, nicht das obere Ende.\n"
                        "- ONLINE-WERT = typischer erzielbarer Verkaufspreis bei Kleinanzeigen/eBay in DE.\n\n"
                        "ONLINE-WERT: \u20acX  (realistischer Gesamt-Verkaufswert online, eBay/Kleinanzeigen)\n"
                        "H\u00c4NDLERPREIS: \u20acX  (was ein anderer H\u00e4ndler/Wiederverk\u00e4ufer dir SOFORT bar zahlen w\u00fcrde, ca. 35-55% vom Online-Wert)\n"
                        "FLOHMARKT-WERT: \u20acX  (realistischer Gesamt-Erl\u00f6s am Flohmarkt-Stand)\n\n"

                        "Dann je nachdem:\n\n"

                        "FALLS KONVOLUT (mehrere Sachen/Kartons/Lot — typisch bei Auktionen):\n"
                        "\U0001f4e6 Was ist drin? [Liste die erkennbaren Kategorien: Geschirr, Kleidung, Elektronik, Glas, Deko, Werkzeug etc.]\n"
                        "\U0001f4e6 Gesch\u00e4tzte St\u00fcckzahl: ca. X Teile\n"
                        "\U0001f4e6 Auff\u00e4llige Marken/Besonderheiten: [falls Markenporzellan, Markengeschirr, gute Elektronik erkennbar]\n"
                        "\U0001f48e Top 4 wertvollste Einzelteile (die man rausnehmen + einzeln verkaufen sollte):\n"
                        "  1. [konkreter Artikel]: \u20acX\n"
                        "  2. [konkreter Artikel]: \u20acX\n"
                        "  3. [konkreter Artikel]: \u20acX\n"
                        "  4. [konkreter Artikel]: \u20acX\n"
                        "\U0001f4a1 Strategie: [Alles als Paket ODER Top-Teile einzeln + Rest als Paket? Was bringt mehr Gewinn?]\n\n"

                        "FALLS EINZELARTIKEL:\n"
                        "**Artikel: [Name]**\n"
                        "- Was genau? [Marke, Material, Modell]\n"
                        "- Alter: [Jahr/Epoche]\n"
                        "- ZUSTAND: [Gesamtzustand + Gebrauchsspuren-Grad X% + jeder Kratzer/Delle einzeln]\n"
                        "- Verk\u00e4uflichkeit: \U0001f7e2schnell / \U0001f7e1mittel / \U0001f534langsam\n\n"

                        "DANN IMMER (beide F\u00e4lle) — alle Plattform-Preise einzeln:\n"
                        "- \U0001f6d2 eBay: \u20acX\n"
                        "- \U0001f4f1 Kleinanzeigen: \u20acX\n"
                        "- \U0001f457 Vinted: \u20acX\n"
                        "- \U0001f465 Facebook: \u20acX\n"
                        "- \U0001f3aa Flohmarkt: \u20acX\n"
                        "- \U0001f4b5 Max. Ankauf: \u20acX\n\n"

                        "\u26a0\ufe0f RISIKO: Stufe [\U0001f7e2/\U0001f7e1/\U0001f534] | Max. Einkauf \u20acX | Verkauf in [Zeit] | Empfehlung [\u2705/\u26a0\ufe0f/\u274c]\n"
                        "\U0001f5fa\ufe0f BERLIN-M\u00c4RKTE: \U0001f947[Markt] \U0001f948[Markt]\n"
                        "\U0001f4b0 GEWINN: EK\u20acX \u2192 VK\u20acX \u2192 Gewinn\u20acX (ROI X%)\n\n"
                        "FAZIT: [2 S\u00e4tze auf Deutsch]"
                    )

                    # 3 Experten-KIs analysieren GLEICHZEITIG
                    st.write("🚀 3 Top-Experten analysieren gleichzeitig...")
                    experten_modelle = [
                        ("google/gemini-2.5-flash",      "🥇 Gemini 2.5",      "google/gemini-2.5-flash-lite"),
                        ("openai/gpt-4o",                "🥈 GPT-4o",          "openai/gpt-4o-mini"),
                        ("google/gemini-2.5-flash-lite", "🥉 Gemini 2.5 Lite", "google/gemma-3-27b-it"),
                    ]
                    # Bilder VOR dem Thread vorbereiten (session_state geht nicht in Threads!)
                    bilder_fuer_experten = [komprimiere(b) for b in st.session_state.fotos[:3]] if hat_fotos else None

                    def experte_arbeitet(modell_info):
                        # Jeder Experte hat eigene Fallback-Modelle!
                        primaer_id, modell_name, fallback_id = modell_info
                        bilder_komp = bilder_fuer_experten
                        for versuch_id in [primaer_id, fallback_id]:
                            try:
                                klient = _oai.OpenAI(api_key=OR_KEY, base_url="https://openrouter.ai/api/v1")
                                if hat_fotos:
                                    inhalt = [{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b}"}} for b in bilder_komp]
                                    inhalt.append({"type":"text","text":analyse_prompt})
                                    nachrichten = [{"role":"user","content":inhalt}]
                                else:
                                    nachrichten = [{"role":"user","content":analyse_prompt}]
                                antwort_obj = klient.chat.completions.create(
                                    model=versuch_id, messages=nachrichten,
                                    max_tokens=1800, temperature=0.2, extra_headers=_hdrs()
                                )
                                antwort_text = antwort_obj.choices[0].message.content
                                if antwort_text and len(antwort_text) > 100:
                                    return (modell_name, antwort_text)
                            except Exception:
                                continue
                        return (modell_name, None)

                    experten_ergebnisse = {}
                    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                        futures_map = {executor.submit(experte_arbeitet, m): m for m in experten_modelle}
                        for future in concurrent.futures.as_completed(futures_map):
                            name_e, antwort_e = future.result()
                            if antwort_e:
                                experten_ergebnisse[name_e] = antwort_e
                                st.write(f"✅ {name_e} fertig!")

                    # KONFIDENZ-Anzeige
                    anzahl_experten = len(experten_ergebnisse)
                    if anzahl_experten == 3:
                        st.success(f"🎯 Konfidenz: **100%** — Alle 3 Experten einig! Höchst zuverlässig!")
                    elif anzahl_experten == 2:
                        st.success(f"🎯 Konfidenz: **75%** — 2 von 3 Experten einig!")
                    elif anzahl_experten == 1:
                        st.warning(f"🎯 Konfidenz: **50%** — Nur 1 Experte — Ergebnis prüfen!")

                    if anzahl_experten == 0:
                        # Fallback auf einzelne KI mit voller Fallback-Kette
                        st.info("ℹ️ Nutze Einzel-KI mit 9-Modell-Fallback-Kette...")
                        with st.spinner("🤖 KI arbeitet — versucht alle Modelle..."):
                            ergebnis = ki(analyse_prompt, bilder=st.session_state.fotos if hat_fotos else None)
                        if ergebnis and "❌" not in ergebnis:
                            st.success("✅ Analyse erfolgreich!")
                    elif anzahl_experten == 1:
                        # Nur eine Antwort — direkt nehmen
                        ergebnis = list(experten_ergebnisse.values())[0]
                    else:
                        # Richter-KI fasst alle zusammen
                        st.write(f"⚖️ Richter-KI fasst {anzahl_experten} Experten zusammen...")

                        # ECHTEN Median der Preise pro Experte per Code berechnen
                        # (verhindert Schwankung — KI soll nicht 'im Kopf' mitteln)
                        import re as _re_j, statistics as _stat
                        def _zieh_preis(muster, txt):
                            m = _re_j.search(muster, txt, _re_j.IGNORECASE)
                            if m:
                                try: return float(m.group(1).replace(".","").replace(",","."))
                                except: return None
                            return None
                        _online, _haendler, _floh = [], [], []
                        for _ant in experten_ergebnisse.values():
                            o = _zieh_preis(r"ONLINE[- ]?WERT[:\s]*\u20ac\s*(\d+(?:[.,]\d+)?)", _ant)
                            h = _zieh_preis(r"H\u00c4NDLER[- ]?PREIS[:\s]*\u20ac\s*(\d+(?:[.,]\d+)?)", _ant)
                            f_ = _zieh_preis(r"FLOHMARKT[- ]?WERT[:\s]*\u20ac\s*(\d+(?:[.,]\d+)?)", _ant)
                            if o: _online.append(o)
                            if h: _haendler.append(h)
                            if f_: _floh.append(f_)
                        _vorgabe = ""
                        if _online or _floh:
                            _vorgabe = "\nVERBINDLICHE PREISE (exakt so \u00fcbernehmen, NICHT \u00e4ndern):\n"
                            if _online:   _vorgabe += "ONLINE-WERT: \u20ac" + str(round(_stat.median(_online))) + "\n"
                            if _haendler: _vorgabe += "H\u00c4NDLERPREIS: \u20ac" + str(round(_stat.median(_haendler))) + "\n"
                            if _floh:     _vorgabe += "FLOHMARKT-WERT: \u20ac" + str(round(_stat.median(_floh))) + "\n"

                        experten_teile = []
                        for e_name, e_antwort in experten_ergebnisse.items():
                            experten_teile.append("==" + e_name + "==\n" + e_antwort[:800])
                        experten_zusammen = "\n\n".join(experten_teile)
                        richter_prompt_final = (
                            "Du bist Chef-Experte für Secondhand in Deutschland.\n"
                            + str(anzahl_experten) + " Experten haben den Artikel analysiert.\n"
                            + "Erstelle EINE perfekte, vollständige finale Antwort auf Deutsch.\n"
                            + "Nimm das Beste + Präziseste aus jeder Analyse.\n"
                            + _vorgabe
                            + "Behalte ALLE Abschnitte (Zustand, alle 5 Preise, Gewinn, Berlin-Märkte etc.)!\n\n"
                            + "Experten-Analysen:\n"
                            + experten_zusammen
                            + "\n\nFINALE EXPERTEN-ANTWORT:"
                        )
                        ergebnis = ki(richter_prompt_final)

                    st.markdown(ergebnis)

                    # PROFI-DARSTELLUNG wie Vorbild
                    import re as _re
                    def finde_preis(muster, text):
                        m = _re.search(muster, text, _re.IGNORECASE)
                        if m:
                            try: return float(m.group(1).replace(",","."))
                            except: return None
                        return None

                    online_wert = (
                        finde_preis(r"ONLINE[- ]?WERT[:\s]*\u20ac\s*(\d+(?:[.,]\d+)?)", ergebnis)
                        or finde_preis(r"eBay[:\s]*\u20ac\s*(\d+(?:[.,]\d+)?)", ergebnis)
                        or finde_preis(r"Gesamtwert[^\n]*?\u20ac\s*(\d+(?:[.,]\d+)?)", ergebnis)
                    )
                    floh_wert = (
                        finde_preis(r"FLOHMARKT[- ]?WERT[:\s]*\u20ac\s*(\d+(?:[.,]\d+)?)", ergebnis)
                        or finde_preis(r"Flohmarkt[:\s]*\u20ac\s*(\d+(?:[.,]\d+)?)", ergebnis)
                        or finde_preis(r"Flohmarkt[^\n]*?\u20ac\s*(\d+(?:[.,]\d+)?)", ergebnis)
                    )
                    haendler_wert = finde_preis(r"H\u00c4NDLER[- ]?PREIS[:\s]*\u20ac\s*(\d+(?:[.,]\d+)?)", ergebnis)
                    # Objekt-Name + Kategorie extrahieren
                    obj_match = _re.search(r"Artikel[:\s]+([^\n(]+)", ergebnis)
                    obj_name = obj_match.group(1).strip()[:35] if obj_match else (st.session_state.get("auto_kat","") or "Artikel")
                    kat_name = st.session_state.get("auto_kat","Haushaltswaren")

                    if online_wert and floh_wert:
                        if not haendler_wert:
                            haendler_wert = round(online_wert * 0.45, 2)
                        quote = round((floh_wert / online_wert) * 100, 1) if online_wert > 0 else 0
                        # Wertverlust aus dem von der KI genannten Gebrauchsspuren-% ableiten
                        _vp = _re.search(r"(\d{1,2})\s*%", ergebnis)
                        _verlust_proz = (int(_vp.group(1)) / 100.0) if _vp else 0.10
                        # Neuwert-Schätzung = Online-Wert / (1 - Verlust%), Verlust = Differenz
                        if _verlust_proz < 0.9:
                            _neuwert = online_wert / (1 - _verlust_proz)
                            wertverlust = round(_neuwert - online_wert, 2)
                        else:
                            wertverlust = round(online_wert * 0.10, 2)
                        schnell = round(floh_wert * 0.57, 2)
                        mittel  = round(online_wert * 0.47, 2)
                        maximal = online_wert

                        # HEADER: Objekt + Kategorie
                        h1, h2 = st.columns(2)
                        with h1:
                            st.markdown(
                                "<div style='color:#888;font-size:13px'>Identifiziertes Objekt</div>"
                                "<div style='color:#333;font-size:26px;font-weight:300'>" + obj_name + "</div>",
                                unsafe_allow_html=True)
                        with h2:
                            st.markdown(
                                "<div style='color:#888;font-size:13px'>Kategorie</div>"
                                "<div style='color:#333;font-size:26px;font-weight:300'>" + kat_name + "</div>",
                                unsafe_allow_html=True)

                        st.markdown("")
                        st.markdown("### 💰 Preisschätzung (Zustandsbereinigt)")
                        c1, c2, c3, c4 = st.columns(4)
                        with c1:
                            st.markdown(
                                "<div style='color:#888;font-size:14px'>📈 Est. Online-Wert</div>"
                                "<div style='color:#333;font-size:34px;font-weight:400'>" + f"{online_wert:.2f}".replace(".",",") + " €</div>",
                                unsafe_allow_html=True)
                        with c2:
                            st.markdown(
                                "<div style='color:#888;font-size:14px'>🤝 Händlerpreis</div>"
                                "<div style='color:#333;font-size:34px;font-weight:400'>" + f"{haendler_wert:.2f}".replace(".",",") + " €</div>",
                                unsafe_allow_html=True)
                        with c3:
                            st.markdown(
                                "<div style='color:#888;font-size:14px'>🎪 Est. Flohmarkt-Wert</div>"
                                "<div style='color:#333;font-size:34px;font-weight:400'>" + f"{floh_wert:.2f}".replace(".",",") + " €</div>",
                                unsafe_allow_html=True)
                        with c4:
                            st.markdown(
                                "<div style='color:#888;font-size:14px'>📉 Wertverlust durch Mängel</div>"
                                "<div style='color:#333;font-size:34px;font-weight:400'>-" + f"{wertverlust:.2f}".replace(".",",") + " €</div>",
                                unsafe_allow_html=True)

                        st.markdown(f"**Flohmarkt-Erlös-Quote: {quote}% des Online-Wertes**")
                        st.progress(min(int(quote), 100) / 100)

                        st.markdown("### ⏱️ Liquiditäts- & Verkaufsgeschwindigkeit")
                        l1, l2, l3 = st.columns(3)
                        with l1:
                            st.markdown(
                                "<div style='background:rgba(46,204,113,0.10);padding:18px;border-radius:14px;height:100%'>"
                                "<div style='color:#27ae60;font-size:15px;font-weight:700'>🟢 Schnell (1-3 Tage)</div>"
                                "<div style='color:#27ae60;font-size:24px;font-weight:800;margin:8px 0'>" + f"{schnell:.2f}".replace(".",",") + " €</div>"
                                "<div style='color:#777;font-size:12px;line-height:1.5'>Komplettes Lot unverändert als Paket auf Kleinanzeigen oder lokalen Marktplätzen anbieten. Abholung durch Käufer. Ziel: schnelle Räumung.</div>"
                                "</div>", unsafe_allow_html=True)
                        with l2:
                            st.markdown(
                                "<div style='background:rgba(241,196,15,0.12);padding:18px;border-radius:14px;height:100%'>"
                                "<div style='color:#d4a017;font-size:15px;font-weight:700'>🟡 Mittel (1-2 Wochen)</div>"
                                "<div style='color:#d4a017;font-size:24px;font-weight:800;margin:8px 0'>" + f"{mittel:.2f}".replace(".",",") + " €</div>"
                                "<div style='color:#777;font-size:12px;line-height:1.5'>Das Lot grob vorsortieren (Geschirr, Kleingeräte, Sonstiges) und in 2-3 kleinere Pakete aufteilen. Sets bilden und gesondert anbieten.</div>"
                                "</div>", unsafe_allow_html=True)
                        with l3:
                            st.markdown(
                                "<div style='background:rgba(231,76,60,0.08);padding:18px;border-radius:14px;height:100%'>"
                                "<div style='color:#e74c3c;font-size:15px;font-weight:700'>🔴 Maximal (1-3 Monate)</div>"
                                "<div style='color:#e74c3c;font-size:24px;font-weight:800;margin:8px 0'>" + f"{maximal:.2f}".replace(".",",") + " €</div>"
                                "<div style='color:#777;font-size:12px;line-height:1.5'>Jedes Teil einzeln prüfen. Wertvolle Stücke (Markengeschirr, Geräte) mit Fotos online. Rest in kleineren Paketen oder am Flohmarkt.</div>"
                                "</div>", unsafe_allow_html=True)

                        # Bei KONVOLUT: Top-Einzelteile als Bonus zeigen
                        ist_konvolut = "KONVOLUT" in ergebnis.upper() or "Stückzahl" in ergebnis or "Teile" in ergebnis
                        if ist_konvolut:
                            # Extrahiere Top-Einzelteile (Format: "1. [Name]: €X")
                            einzelteile = _re.findall(r"\d+\.\s*([^:\n]+):\s*\u20ac\s*(\d+(?:[.,]\d+)?)", ergebnis)
                            if einzelteile:
                                st.markdown("### 💎 Wertvollste Einzelteile (einzeln verkaufen lohnt!)")
                                cols_e = st.columns(min(len(einzelteile[:4]), 4))
                                for i, (name, preis) in enumerate(einzelteile[:4]):
                                    with cols_e[i % len(cols_e)]:
                                        st.markdown(
                                            "<div style='background:rgba(108,71,255,0.08);padding:12px;border-radius:12px;text-align:center'>"
                                            "<div style='color:#666;font-size:12px'>" + name.strip()[:25] + "</div>"
                                            "<div style='color:#6c47ff;font-size:22px;font-weight:800'>\u20ac" + preis + "</div>"
                                            "</div>", unsafe_allow_html=True)
                                st.markdown("")

                        # ═══════════════════════════════════════════════════
                        # 🎯 PROFI-EXTRAS (nutzen bereits berechnete Werte)
                        # ═══════════════════════════════════════════════════
                        import re as _re_x
                        from datetime import datetime as _dt_x

                        # --- 1. SCHNELL-EMPFEHLUNG: Lohnt sich der Einkauf? ---
                        st.markdown("---")
                        marge_floh = (floh_wert - (haendler_wert or 0)) if (floh_wert and haendler_wert) else 0
                        if floh_wert and haendler_wert and online_wert:
                            if marge_floh >= 20 and floh_wert >= haendler_wert * 1.5:
                                _farbe = "linear-gradient(135deg,#3a7a3a,#5fa55f)"
                                _emoji = "✅"
                                _kern = "JA — KAUFEN"
                                _detail = f"Max. €{haendler_wert:.0f} zahlen · Marge ca. €{marge_floh:.0f} bar am Stand"
                            elif marge_floh >= 10:
                                _farbe = "linear-gradient(135deg,#c8862a,#e8a93a)"
                                _emoji = "🟡"
                                _kern = "VIELLEICHT — verhandeln"
                                _detail = f"Nur unter €{(haendler_wert*0.8):.0f} kaufen · Marge knapp"
                            else:
                                _farbe = "linear-gradient(135deg,#7a3a3a,#a55f5f)"
                                _emoji = "❌"
                                _kern = "NEIN — lohnt nicht"
                                _detail = "Marge zu dünn — lass die Finger davon"
                            st.markdown(
                                f"<div style='background:{_farbe};padding:18px 22px;border-radius:16px;"
                                f"color:#fff;box-shadow:0 10px 30px rgba(0,0,0,0.15);margin:8px 0'>"
                                f"<div style='font-size:13px;letter-spacing:2px;opacity:0.85;font-weight:600'>SCHNELL-ENTSCHEIDUNG</div>"
                                f"<div style='font-size:26px;font-weight:900;font-family:Playfair Display,serif;margin:4px 0'>"
                                f"{_emoji} {_kern}</div>"
                                f"<div style='font-size:14px;opacity:0.95'>{_detail}</div>"
                                f"</div>", unsafe_allow_html=True)

                        # --- 2. VERHANDLUNGS-TIPP + 4. SAISON + 6. RISIKO-AMPEL nebeneinander ---
                        sp1, sp2, sp3 = st.columns(3)

                        # VERHANDLUNGS-TIPP
                        with sp1:
                            _zielpreis = round((haendler_wert or floh_wert*0.6) * 0.75) if haendler_wert else 0
                            st.markdown(
                                "<div style='background:linear-gradient(180deg,#fffdf7,#fcf5e1);"
                                "padding:16px;border-radius:14px;border:1px solid rgba(200,160,80,0.3);"
                                "box-shadow:0 6px 20px rgba(60,45,20,0.06);height:100%'>"
                                "<div style='color:#c8862a;font-size:11px;letter-spacing:1.5px;font-weight:700'>💬 VERHANDLUNG</div>"
                                f"<div style='font-size:24px;font-weight:800;color:#7a5520;font-family:Playfair Display,serif;margin:6px 0'>€{_zielpreis}</div>"
                                "<div style='font-size:12px;color:#5a4a30;line-height:1.5'>"
                                "<b>Sag dem Verkäufer:</b><br>"
                                f"„Funktion unklar, Risiko bei mir. Ich zahl dir €{_zielpreis} bar, deal?\"</div>"
                                "</div>", unsafe_allow_html=True)

                        # SAISON-HINWEIS
                        with sp2:
                            _monat = _dt_x.now().month
                            _txt = ergebnis.lower()
                            _saison_emoji = "🟢"
                            _saison_titel = "JETZT VERKAUFEN"
                            _saison_text = "Ganzjahres-Artikel — jederzeit absetzbar."
                            # Sommer-Artikel (April-Sep)
                            if any(w in _txt for w in ["sommer","strand","grill","garten","badminton","camping","fahrrad","ventilator","kühl","klima","sonnen"]):
                                if 4 <= _monat <= 8:
                                    _saison_emoji, _saison_titel, _saison_text = "🟢", "PEAK-SAISON", "Sommer-Artikel — JETZT raus damit, beste Zeit!"
                                else:
                                    _saison_emoji, _saison_titel, _saison_text = "🟡", "WARTEN", "Sommer-Artikel — bis April lagern, dann +30%."
                            # Winter-Artikel
                            elif any(w in _txt for w in ["winter","schnee","ski","schlitten","heizung","heizer","weihnacht","advent","wolle","skier"]):
                                if _monat in [11,12,1,2]:
                                    _saison_emoji, _saison_titel, _saison_text = "🟢", "PEAK-SAISON", "Winter-Artikel — Hochsaison, max. Preis!"
                                else:
                                    _saison_emoji, _saison_titel, _saison_text = "🟡", "WARTEN", "Winter-Artikel — bis November warten."
                            # Vintage/Sammler
                            elif any(w in _txt for w in ["vintage","retro","antik","sammler","alt","70er","80er","60er"]):
                                _saison_emoji, _saison_titel, _saison_text = "🟢", "ZEITLOS", "Sammlerstück — Saison egal, Käufer warten."
                            st.markdown(
                                "<div style='background:linear-gradient(180deg,#fffdf7,#fcf5e1);"
                                "padding:16px;border-radius:14px;border:1px solid rgba(200,160,80,0.3);"
                                "box-shadow:0 6px 20px rgba(60,45,20,0.06);height:100%'>"
                                "<div style='color:#c8862a;font-size:11px;letter-spacing:1.5px;font-weight:700'>🗓️ SAISON</div>"
                                f"<div style='font-size:24px;font-weight:800;color:#7a5520;font-family:Playfair Display,serif;margin:6px 0'>{_saison_emoji} {_saison_titel}</div>"
                                f"<div style='font-size:12px;color:#5a4a30;line-height:1.5'>{_saison_text}</div>"
                                "</div>", unsafe_allow_html=True)

                        # RISIKO-AMPEL
                        with sp3:
                            _risiko_punkte = 0
                            _gruende = []
                            _txt2 = ergebnis.lower()
                            if "defekt" in _txt2 or "unklar" in _txt2 or "nicht getest" in _txt2:
                                _risiko_punkte += 35; _gruende.append("Funktion unklar")
                            if floh_wert and haendler_wert and floh_wert < haendler_wert * 1.4:
                                _risiko_punkte += 25; _gruende.append("Marge dünn")
                            if "selten" in _txt2 or "nische" in _txt2 or "spezial" in _txt2:
                                _risiko_punkte += 20; _gruende.append("Nischen-Käufer")
                            if online_wert and online_wert < 30:
                                _risiko_punkte += 15; _gruende.append("Günstig-Segment")
                            if not _gruende:
                                _gruende.append("Solide Sache")
                            if _risiko_punkte >= 50:
                                _ri_emoji, _ri_titel = "🔴", "HOCH"
                            elif _risiko_punkte >= 25:
                                _ri_emoji, _ri_titel = "🟡", "MITTEL"
                            else:
                                _ri_emoji, _ri_titel = "🟢", "GERING"
                            st.markdown(
                                "<div style='background:linear-gradient(180deg,#fffdf7,#fcf5e1);"
                                "padding:16px;border-radius:14px;border:1px solid rgba(200,160,80,0.3);"
                                "box-shadow:0 6px 20px rgba(60,45,20,0.06);height:100%'>"
                                "<div style='color:#c8862a;font-size:11px;letter-spacing:1.5px;font-weight:700'>⚠️ RISIKO</div>"
                                f"<div style='font-size:24px;font-weight:800;color:#7a5520;font-family:Playfair Display,serif;margin:6px 0'>{_ri_emoji} {_ri_titel} ({_risiko_punkte}%)</div>"
                                f"<div style='font-size:12px;color:#5a4a30;line-height:1.5'>"
                                + " · ".join(_gruende[:3]) +
                                "</div></div>", unsafe_allow_html=True)

                        # --- 7. SPRACHAUSGABE: Browser-eigene Text-to-Speech, kein API-Call ---
                        _kurz = f"{_kern if 'kern' in dir() or floh_wert else 'Analyse fertig'}. "
                        if online_wert: _kurz += f"Online {online_wert:.0f} Euro. "
                        if haendler_wert: _kurz += f"Händler {haendler_wert:.0f} Euro. "
                        if floh_wert: _kurz += f"Flohmarkt {floh_wert:.0f} Euro. "
                        _kurz_esc = _kurz.replace("'","").replace('"','').replace("\n"," ")
                        st.markdown(
                            "<div style='text-align:center;margin:16px 0 4px'>"
                            f"<button onclick=\"var u=new SpeechSynthesisUtterance('{_kurz_esc}');"
                            "u.lang='de-DE';u.rate=1.05;speechSynthesis.cancel();speechSynthesis.speak(u);\" "
                            "style='background:linear-gradient(135deg,#1a1612,#2a2218);color:#f5d48a;"
                            "border:1px solid rgba(232,169,58,0.4);border-radius:12px;padding:10px 24px;"
                            "font-weight:600;cursor:pointer;font-size:13px;letter-spacing:1px;"
                            "box-shadow:0 6px 18px rgba(28,22,18,0.2)'>"
                            "🔊 ERGEBNIS VORLESEN</button></div>",
                            unsafe_allow_html=True)
                        st.markdown("---")

                        # Volltext-Analyse einklappbar
                        with st.expander("📄 Vollständige Detail-Analyse anzeigen"):
                            st.markdown(ergebnis)
                    else:
                        # Fallback: zeige normalen Text wenn Werte nicht gefunden
                        st.markdown(ergebnis)

                    st.session_state["ana_ergebnis"] = ergebnis
                    st.session_state["vorabinfo"] = ""
                    st.session_state["auto_kat"] = ""

            # Suchbegriff extrahieren
            suchbegriff="Vintage Artikel"
            for line in ergebnis.split("\n"):
                if "**Artikel:" in line:
                    t=line.split(":")
                    if len(t)>1: suchbegriff=t[1].strip().strip("*[] ")[:40]
                    break
            # Klammer-Zusätze entfernen (z.B. "Rosita Hi-Fi Anlage (Kompaktanlage)" → "Rosita Hi-Fi Anlage")
            if "(" in suchbegriff:
                suchbegriff = suchbegriff.split("(")[0].strip()

            # ── STUFE 3: PREIS-ENSEMBLE + WEB ──
            with st.status("📡 Stufe 3: Google+Tavily+You.com + 3 Preis-KIs...",expanded=True):
                ebay_url=f"https://www.ebay.de/sch/i.html?_nkw={urllib.parse.quote(suchbegriff)}&LH_Complete=1&LH_Sold=1"
                ka_url=f"https://www.kleinanzeigen.de/s-{urllib.parse.quote(suchbegriff)}/k0"
                vi_url=f"https://www.vinted.de/catalog?search_text={urllib.parse.quote(suchbegriff)}"
                fb_url=f"https://www.facebook.com/marketplace/search/?query={urllib.parse.quote(suchbegriff)}"
                st.write(f"🌐 Suche echte Preise für: **{suchbegriff}** — im GANZEN Web")
                # 3 Suchmaschinen gleichzeitig, durchsuchen das ganze Web (nicht nur eBay/Kleinanzeigen)
                def hole_gezielte_preise():
                    query = suchbegriff + " gebraucht Preis Euro verkauft Deutschland"
                    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as _ex:
                        _fg = _ex.submit(google_suche, query)
                        _ft = _ex.submit(tavily_suche, suchbegriff + " gebraucht verkauft Marktpreis Secondhand")
                        _fy = _ex.submit(you_suche, query)
                        _fd = _ex.submit(ddg_suche, suchbegriff + " gebraucht verkauft")
                        g = _fg.result()
                        t = _ft.result()
                        y = _fy.result()
                        dd = _fd.result()
                    return g, t, y, dd

                google_r, tavily_r, you_r, ddg_r = hole_gezielte_preise()

                # Diagnose: zeigen welche Suchmaschine geantwortet hat
                _quellen = []
                if google_r: _quellen.append("Google")
                if tavily_r: _quellen.append("Tavily")
                if you_r: _quellen.append("You.com")
                if ddg_r: _quellen.append("DuckDuckGo")
                if _quellen:
                    st.caption("🔎 Antwort von: " + ", ".join(_quellen))
                else:
                    st.warning("⚠️ Keine Suchmaschine hat geantwortet — evtl. API-Schlüssel abgelaufen oder Limit erreicht. Preise sind dann reine KI-Schätzung.")

                # Prüfe ob Ergebnisse brauchbar sind (locker: 1 passendes Wort ODER ein Preis reicht)
                def passt_zum_artikel(text, artikel):
                    if not text: return False
                    hat_preis = ("€" in text or "eur" in text.lower() or "preis" in text.lower())
                    if not artikel: return hat_preis
                    woerter = [w for w in artikel.lower().split() if len(w) > 3]
                    treffer = sum(1 for w in woerter if w in text.lower())
                    # Behalten wenn: mind. 1 Wort passt, ODER ein Preis drinsteht
                    return treffer >= 1 or hat_preis

                web_text = ""
                if google_r and passt_zum_artikel(google_r, suchbegriff):
                    web_text += google_r
                if tavily_r and passt_zum_artikel(tavily_r, suchbegriff):
                    web_text += "\n" + tavily_r
                if you_r and passt_zum_artikel(you_r, suchbegriff):
                    web_text += "\n" + you_r
                if ddg_r and passt_zum_artikel(ddg_r, suchbegriff):
                    web_text += "\n" + ddg_r

                # ECHTE PREISE aus den Web-Treffern herausziehen und auswerten
                preis_auswertung = extrahiere_preise(web_text)
                web_preis_vorgabe = ""
                if preis_auswertung:
                    st.success(
                        f"💶 **{preis_auswertung['anzahl']} echte Preise im Web gefunden:** "
                        f"Median **€{preis_auswertung['median']}** "
                        f"(Spanne €{preis_auswertung['min']}–€{preis_auswertung['max']})"
                    )
                    web_preis_vorgabe = (
                        "\n\nECHTE GEFUNDENE PREISE (aus " + str(preis_auswertung['anzahl'])
                        + " Web-Treffern): Median €" + str(preis_auswertung['median'])
                        + ", Spanne €" + str(preis_auswertung['min']) + "–€" + str(preis_auswertung['max'])
                        + ". Der ONLINE-WERT soll nahe am Median liegen!\n"
                    )

                # 3 Preis-Experten bewerten GLEICHZEITIG
                st.write("⚖️ 3 Preis-Experten bewerten gleichzeitig...")
                preis_prompt = (
                    "Preisexperte Secondhand Deutschland. Auf DEUTSCH antworten!\n"
                    "Artikel: " + suchbegriff + "\n"
                    "Zustand: " + g_beschr + "\n"
                    + web_preis_vorgabe
                    + ("ECHTE MARKTDATEN AUS DEM WEB (nutze diese Zahlen als Hauptgrundlage, NICHT deine eigene Schätzung!):\n" + web_text[:2500] if web_text else "Keine Web-Daten gefunden — schätze konservativ aus Erfahrung, eher zu niedrig als zu hoch.") + "\n\n"
                    "Wenn echte Web-Preise vorliegen: richte dich nach diesen, nicht nach deinem Bauchgefühl.\n"
                    "Gib realistische Preise. NUR konkrete Einzelzahlen — KEINE Spannen! Auf glatte Zehner runden.\n"
                    "Der Flohmarkt-Preis liegt erfahrungsgemäß bei 40-60% des Online-Werts (Barverkauf am Stand).\n"
                    "Format:\n"
                    "- eBay: €X\n"
                    "- Kleinanzeigen: €X\n"
                    "- Vinted: €X\n"
                    "- Facebook: €X\n"
                    "- Flohmarkt: €X\n"
                    "- Empfehlung: €X\n"
                    "- Trend: ↑/↓/→ + kurze Begründung"
                )
                preis_modelle = [
                    ("google/gemini-2.5-flash", "Gemini 2.5"),
                    ("google/gemini-2.5-flash",       "Gemini 2.5"),
                    ("openai/gpt-4o-mini",            "GPT-4o"),
                ]
                def preis_experte_arbeitet(modell_info):
                    m_id, m_name = modell_info
                    try:
                        kl = _oai.OpenAI(api_key=OR_KEY, base_url="https://openrouter.ai/api/v1")
                        r = kl.chat.completions.create(
                            model=m_id, messages=[{"role":"user","content":preis_prompt}],
                            max_tokens=400, temperature=0.2, extra_headers=_hdrs()
                        )
                        a = r.choices[0].message.content
                        if a and "€" in a: return (m_name, a)
                    except Exception:
                        pass
                    return (m_name, None)

                preis_meinungen = {}
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
                    fut = {ex.submit(preis_experte_arbeitet, m): m for m in preis_modelle}
                    for f in concurrent.futures.as_completed(fut):
                        n, a = f.result()
                        if a: preis_meinungen[n] = a; st.write(f"✅ {n} bewertet!")

                if preis_meinungen:
                    if web_text:
                        st.success("✅ Echte Web-Daten + 3 Preis-Experten:")
                    else:
                        st.info("💡 3 Preis-Experten (KI-Schätzung):")
                    # Richter fasst Preise zusammen
                    if len(preis_meinungen) > 1:
                        preis_teile = []
                        for pn, pa in preis_meinungen.items():
                            preis_teile.append("[" + pn + "]: " + pa[:300])
                        preis_zusammen = "\n\n".join(preis_teile)
                        pk = ki(
                            str(len(preis_meinungen)) + " Preisexperten haben bewertet:\n"
                            + preis_zusammen + "\n\n"
                            "Erstelle finalen Preis-Konsens. NUR Einzelzahlen, KEINE Spannen!\n"
                            "Format: eBay: €X | Kleinanzeigen: €X | Vinted: €X | Facebook: €X | Flohmarkt: €X | Empfehlung: €X | Trend: ↑/↓/→"
                        )
                    else:
                        pk = list(preis_meinungen.values())[0]
                    st.markdown("💰 **Preis-Konsens für " + suchbegriff + ":**\n" + pk)
                else:
                    st.info("ℹ️ Preise siehe Stufe 2 (Hauptanalyse)")

                # ═══════════════════════════════════════════════════
                # 🔍 ÄHNLICHE ANZEIGEN — echte Treffer + Plattform-Buttons
                # ═══════════════════════════════════════════════════
                st.markdown("---")
                st.markdown(
                    "<div style='color:#c8862a;font-size:13px;letter-spacing:2px;font-weight:700;margin-bottom:8px'>"
                    "🔍 ÄHNLICHE ANZEIGEN IM WEB</div>", unsafe_allow_html=True)

                with st.spinner("Suche echte Anzeigen..."):
                    anzeigen = hole_anzeigen(suchbegriff, max_treffer=4)

                if anzeigen:
                    st.caption(f"💡 {len(anzeigen)} ähnliche Anzeigen gefunden — klick zum Anschauen:")
                    az_cols = st.columns(2)
                    for i, az in enumerate(anzeigen):
                        with az_cols[i % 2]:
                            _preis_html = (
                                f"<div style='background:linear-gradient(135deg,#f5d48a,#e8a93a);"
                                f"color:#1a1612;padding:4px 10px;border-radius:8px;font-weight:800;"
                                f"font-size:13px;display:inline-block'>€{az['preis']}</div>"
                                if az['preis'] else
                                "<div style='color:#888;font-size:12px;font-style:italic'>kein Preis sichtbar</div>"
                            )
                            st.markdown(
                                "<div style='background:linear-gradient(180deg,#fffdf7,#fcf5e1);"
                                "padding:14px;border-radius:14px;border:1px solid rgba(200,160,80,0.3);"
                                "box-shadow:0 6px 18px rgba(60,45,20,0.06);margin-bottom:10px;height:160px;"
                                "display:flex;flex-direction:column;justify-content:space-between'>"
                                f"<div><div style='color:#c8862a;font-size:10px;letter-spacing:1.5px;font-weight:700;margin-bottom:4px'>"
                                f"📍 {az['quelle'].upper()}</div>"
                                f"<div style='font-weight:700;color:#2a2218;font-size:13px;line-height:1.3;margin-bottom:6px'>"
                                f"{az['titel'][:65]}{'...' if len(az['titel'])>65 else ''}</div>"
                                f"<div style='color:#666;font-size:11px;line-height:1.4'>"
                                f"{az['snippet'][:90]}{'...' if len(az['snippet'])>90 else ''}</div></div>"
                                f"<div style='display:flex;justify-content:space-between;align-items:center;margin-top:8px'>"
                                f"{_preis_html}"
                                f"<a href='{az['url']}' target='_blank' "
                                f"style='background:#1a1612;color:#f5d48a;padding:5px 12px;border-radius:8px;"
                                f"font-size:12px;font-weight:600;text-decoration:none'>ANSEHEN →</a>"
                                f"</div></div>", unsafe_allow_html=True)
                else:
                    st.info("ℹ️ Keine direkten Anzeigen-Treffer — nutze die Plattform-Buttons unten.")

                # Plattform-Suchbuttons (laufen IMMER, auch wenn echte Treffer fehlen)
                st.markdown(
                    "<div style='color:#c8862a;font-size:12px;letter-spacing:2px;font-weight:700;margin:14px 0 8px'>"
                    "🛒 SELBST SUCHEN AUF DEN PLATTFORMEN</div>", unsafe_allow_html=True)
                pb1, pb2, pb3, pb4 = st.columns(4)
                with pb1:
                    st.link_button("🛒 eBay verkauft", ebay_url, use_container_width=True)
                with pb2:
                    st.link_button("📱 Kleinanzeigen", ka_url, use_container_width=True)
                with pb3:
                    st.link_button("👗 Vinted", vi_url, use_container_width=True)
                with pb4:
                    st.link_button("👥 Facebook", fb_url, use_container_width=True)

            # ── STUFE 4: ZUSAMMENFASSUNG ──
            with st.status("✅ Stufe 4: Finale Zusammenfassung...",expanded=True):
                ana=st.session_state.get("ana_ergebnis","")
                if len(ana)>200 and "€" in ana:
                    fazit = ki("Kurze Zusammenfassung 5 Zeilen. Fakten. Deutsch.\n\u2022 Artikel:\n\u2022 \U0001f7e2 Schnell:\n\u2022 \U0001f7e1 Mittel:\n\u2022 \U0001f534 Langsam:\n\u2022 Gesamtwert: \u20acX\n\nAnalyse:\n" + ana[:800])
                    st.info("📊 "+fazit)

                    # ── VERLAUF SPEICHERN ──
                    st.session_state.analyse_history.append({
                        "datum": datetime.now().strftime("%d.%m.%Y %H:%M"),
                        "artikel": suchbegriff,
                        "zustand": g_beschr,
                        "ergebnis": fazit,
                        "modus": "Schnell" if schnell_modus else "Ultimate"
                    })
                    if len(st.session_state.analyse_history) > 20:
                        st.session_state.analyse_history = st.session_state.analyse_history[-20:]

                    # ── EXPORT ──
                    export_text = (
                        f"MarktRadar Analyse — {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
                        f"{'='*50}\n"
                        f"Artikel: {suchbegriff}\n"
                        f"Zustand: {g_beschr} | {d_beschr}\n"
                        f"{'='*50}\n\n"
                        f"{ana}\n\n"
                        f"{'='*50}\n"
                        f"ZUSAMMENFASSUNG:\n{fazit}"
                    )
                    st.download_button(
                        label="💾 Analyse speichern (TXT)",
                        data=export_text,
                        file_name=f"analyse_{suchbegriff[:20]}_{datetime.now().strftime('%d%m%Y')}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                else:
                    st.warning("⚠️ Keine vollständige Analyse vorhanden.")

    # ── LERN-SYSTEM ──
    st.markdown("---")
    st.markdown("### 🧠 KI Lern-System")

    # Statistik
    total = (len(st.session_state.mein_wissen) +
             len(st.session_state.preis_korrekturen) +
             len(st.session_state.verkauf_log) +
             len(st.session_state.ki_korrekturen))
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("💡 Wissen", len(st.session_state.mein_wissen))
    c2.metric("💰 Preise", len(st.session_state.preis_korrekturen))
    c3.metric("✅ Verkäufe", len(st.session_state.verkauf_log))
    c4.metric("🎯 Korrekturen", len(st.session_state.ki_korrekturen))

    lern_tab1, lern_tab2, lern_tab3, lern_tab4 = st.tabs([
        "💰 Preis korrigieren", "📝 Wissen", "✅ Verkauf eintragen", "🎯 KI war falsch"
    ])

    with lern_tab1:
        st.markdown("KI hat den Preis falsch geschätzt? Korrigieren Sie es!")
        c1,c2,c3 = st.columns(3)
        fb_art  = c1.text_input("Artikel", key="fb_art")
        fb_echt = c2.number_input("Echter Preis €", min_value=0.1, value=50.0, key="fb_echt")
        fb_pl   = c3.selectbox("Plattform", ["Kleinanzeigen","eBay","Vinted","Facebook","Flohmarkt"], key="fb_pl")
        fb_ki   = st.number_input("KI hatte geschätzt €", min_value=0.0, value=0.0, key="fb_ki",
                                   help="Was hat die KI geschätzt? 0 = unbekannt")
        if st.button("💾 Preis speichern", use_container_width=True, key="fb_save"):
            if fb_art:
                key = f"{fb_art} auf {fb_pl}"
                st.session_state.preis_korrekturen[key] = fb_echt
                if fb_ki > 0:
                    diff = fb_echt - fb_ki
                    richtung = "zu hoch" if diff < 0 else "zu niedrig"
                    st.session_state.ki_korrekturen.append(
                        f"{fb_art}: KI sagte €{fb_ki}, echt war €{fb_echt} ({richtung} um €{abs(diff):.0f})"
                    )
                st.success(f"✅ Gespeichert! KI lernt: {fb_art} auf {fb_pl} = €{fb_echt}")
                speichere_lerndaten()

        if st.session_state.preis_korrekturen:
            st.markdown("**Gespeicherte Preise:**")
            for k,v in list(st.session_state.preis_korrekturen.items())[-5:]:
                st.markdown(f"• {k}: **€{v}**")

    with lern_tab2:
        st.markdown("Eigenes Wissen eingeben — KI nutzt das bei jeder Analyse!")
        fb_k = st.text_area("Ihr Wissen:", height=80, key="fb_know",
            placeholder="z.B. Meissen auf Fehrbelliner Platz bringt mehr als online")
        if st.button("💾 Wissen speichern", use_container_width=True, key="fb_ks"):
            if fb_k.strip():
                st.session_state.mein_wissen.append(fb_k.strip())
                speichere_lerndaten()
                st.success("✅ Gespeichert! KI nutzt das ab sofort!")
        if st.session_state.mein_wissen:
            st.markdown("**Mein Wissen:**")
            for i, w in enumerate(st.session_state.mein_wissen[-5:]):
                c1,c2 = st.columns([4,1])
                c1.markdown(f"• {w}")
                if c2.button("🗑️", key=f"del_w_{i}"):
                    idx = len(st.session_state.mein_wissen) - 5 + i
                    if 0 <= idx < len(st.session_state.mein_wissen):
                        st.session_state.mein_wissen.pop(idx)
                    speichere_lerndaten()
                    st.rerun()

    with lern_tab3:
        st.markdown("Artikel verkauft? Eintragen — KI lernt Ihre echten Preise!")
        c1,c2 = st.columns(2)
        with c1:
            vk_art  = st.text_input("Artikel", key="vk_art")
            vk_ek   = st.number_input("EK €", min_value=0.0, value=5.0, key="vk_ek")
            vk_preis = st.number_input("Verkauft für €", min_value=0.1, value=30.0, key="vk_preis")
        with c2:
            vk_pl   = st.selectbox("Plattform", ["Kleinanzeigen","eBay","Vinted","Facebook","Flohmarkt"], key="vk_pl")
            vk_tage = st.number_input("Tage bis Verkauf", min_value=0, value=3, key="vk_tage")
            vk_zust = st.selectbox("Zustand", ["Wie neu","Sehr gut","Gut","Gebraucht"], key="vk_zust")
        if st.button("✅ Verkauf speichern", type="primary", use_container_width=True, key="vk_save"):
            if vk_art:
                gewinn = vk_preis - vk_ek
                roi = (gewinn/vk_ek*100) if vk_ek > 0 else 0
                eintrag = {
                    "datum": datetime.now().strftime("%d.%m.%Y"),
                    "artikel": vk_art, "ek": vk_ek, "vk": vk_preis,
                    "gewinn": round(gewinn,2), "roi": round(roi,1),
                    "plattform": vk_pl, "tage": vk_tage, "zustand": vk_zust
                }
                st.session_state.verkauf_log.append(eintrag)
                # Automatisch in Preis-Korrekturen
                st.session_state.preis_korrekturen[f"{vk_art} auf {vk_pl}"] = vk_preis
                # Automatisch in Wissen
                st.session_state.mein_wissen.append(
                    f"{vk_art} ({vk_zust}) verkauft für €{vk_preis} auf {vk_pl} in {vk_tage} Tagen"
                )
                st.success(f"✅ Gespeichert! Gewinn: €{gewinn:.2f} | ROI: {roi:.0f}%")
                speichere_lerndaten()
                st.rerun()

        if st.session_state.verkauf_log:
            st.markdown("**Letzte Verkäufe:**")
            ges_g = sum(v["gewinn"] for v in st.session_state.verkauf_log)
            st.info(f"💰 Gesamt-Gewinn aus {len(st.session_state.verkauf_log)} Verkäufen: **€{ges_g:.2f}**")
            for v in reversed(st.session_state.verkauf_log[-5:]):
                st.markdown(f"• **{v['artikel']}** → €{v['vk']} auf {v['plattform']} | Gewinn: €{v['gewinn']} | {v['datum']}")

    with lern_tab4:
        st.markdown("KI lag falsch? Sagen Sie es ihr — sie wird besser!")
        corr_text = st.text_area("Was war falsch?", height=70, key="corr_text",
            placeholder="z.B. KI dachte Villeroy & Boch aber es war Rosenthal")
        if st.button("💾 Korrektur speichern", use_container_width=True, key="corr_save"):
            if corr_text.strip():
                st.session_state.ki_korrekturen.append(
                    f"[{datetime.now().strftime('%d.%m.%Y')}] {corr_text.strip()}"
                )
                st.session_state.mein_wissen.append("KORREKTUR: " + corr_text.strip())
                speichere_lerndaten()
                st.success("✅ KI merkt sich das!")

        if st.session_state.ki_korrekturen:
            st.markdown("**Korrekturen:**")
            for k in st.session_state.ki_korrekturen[-5:]:
                st.markdown(f"• {k}")

    if total > 0:
        if st.button("🤖 KI analysiert mein Lern-Profil", use_container_width=True, key="lern_analyse"):
            with st.spinner("🧠 KI analysiert..."):
                profil = (
                    "Verkäufe: " + str(len(st.session_state.verkauf_log)) + "\n"
                    + "Wissen: " + str(len(st.session_state.mein_wissen)) + " Einträge\n"
                    + "Preise: " + str(len(st.session_state.preis_korrekturen)) + " Einträge\n"
                    + "Korrekturen: " + str(len(st.session_state.ki_korrekturen)) + "\n"
                )
                if st.session_state.verkauf_log:
                    profil += "\nVerkäufe:\n" + "\n".join([f"- {v['artikel']}: €{v['vk']} auf {v['plattform']}" for v in st.session_state.verkauf_log[-10:]])
                if st.session_state.mein_wissen:
                    profil += "\nWissen:\n" + "\n".join([f"- {w}" for w in st.session_state.mein_wissen[-10:]])

                analyse_prompt = (
                    "Analysiere dieses Händler-Profil aus Berlin. Auf Deutsch.\n" + profil + "\n\n"
                    "1. Was macht er gut?\n"
                    "2. Welche Artikel bringen ihm am meisten?\n"
                    "3. Beste Plattform für ihn?\n"
                    "4. Top 3 Empfehlungen um mehr zu verdienen?\n"
                    "5. Was sollte er als nächstes kaufen/verkaufen?"
                )
                analyse = ensemble_ki(analyse_prompt)
                st.markdown(analyse)

with T[1]:
    st.header("💬 Anschreib-Bot")
    c1,c2=st.columns(2)
    with c1:
        ab_art=st.text_input("Artikel",key="ab_art")
        ab_mp=st.number_input("Mein Angebot €",min_value=1.0,value=20.0,key="ab_mp")
        ab_vk=st.number_input("Verkäufer-Preis €",min_value=1.0,value=50.0,key="ab_vk")
    with c2:
        ab_stil=st.selectbox("Stil",["Freundlich","Bestimmt","Dringend","Paket-Deal","Letztes Angebot"],key="ab_stil")
        ab_pl=st.selectbox("Plattform",["Kleinanzeigen","eBay","Facebook","Vinted","Flohmarkt"],key="ab_pl")
    ab_kunde=st.text_area("📩 Kunden-Nachricht (optional):",height=80,key="ab_kunde")
    if st.button("✍️ Generieren",type="primary",use_container_width=True,key="ab_btn"):
        if ab_art:
            with st.spinner("✍️ 3 KIs schreiben..."):
                kt=f"\nKunden-Nachricht: '{ab_kunde}'" if ab_kunde.strip() else ""
                web_ab = google_suche(ab_art+" Preis Kleinanzeigen eBay Deutschland")
                markt_k = f"\nAktueller Marktpreis laut Web: {web_ab[:150]}" if web_ab else ""
                p=(f"Verhandlungs-Nachricht auf Deutsch. Stil: {ab_stil} | {ab_pl}\n"
                   f"Artikel: {ab_art} | Angebot: €{ab_mp} | Verkäufer: €{ab_vk}{kt}{markt_k}\n"
                   f"Nutze Marktpreise als Argument falls vorhanden.\n"
                   f"Max 5 Sätze. Psychologisch optimiert. NUR die fertige Nachricht!")
                st.text_area("📩 Kopieren:",value=ensemble_ki(p),height=180,key="ab_r")

# ════════════════════════════════════════════════════════════
# TAB 3 — LAGER
# ════════════════════════════════════════════════════════════
with T[2]:
    st.header("📦 Lagerbestand")
    c1,c2=st.columns(2)
    with c1:
        la=st.text_input("Artikel",key="la"); lek=st.number_input("EK €",min_value=0.0,value=10.0,key="lek")
        lvk=st.number_input("Ziel-VK €",min_value=0.0,value=45.0,key="lvk")
    with c2:
        lzu=st.selectbox("Zustand",["Sehr gut","Gut","Gebraucht","Beschädigt"],key="lzu")
        lpl=st.selectbox("Plattform",["Kleinanzeigen","eBay","Vinted","Facebook","Flohmarkt"],key="lpl")
        lta=st.number_input("Liegezeit Tage",min_value=0,value=0,key="lta")
    if st.button("📦 Hinzufügen",type="primary",use_container_width=True,key="la_btn"):
        if la:
            g=lvk-lek-(lvk*0.05)
            st.session_state.lager.append({"artikel":la,"ek":lek,"vk":lvk,"zustand":lzu,"plattform":lpl,"tage":lta,"gewinn":round(g,2)})
            st.success(f"✅ Gewinn: €{g:.2f}"); st.rerun()
    if st.session_state.lager:
        c1,c2,c3=st.columns(3)
        c1.metric("Artikel",len(st.session_state.lager))
        c2.metric("Kapital",f"€{sum(i['ek'] for i in st.session_state.lager):.2f}")
        c3.metric("Gewinn",f"€{sum(i['gewinn'] for i in st.session_state.lager):.2f}")
        st.markdown("---")
        for it in st.session_state.lager:
            tage = it["tage"]
            # Alarm-Farbe je nach Liegezeit
            if tage >= 60:
                alarm = f"🔴 **{tage} Tage!** SOFORT verkaufen — Preis senken!"
                st.error(f"⛔ {it['artikel']}: {alarm}")
            elif tage >= 30:
                alarm = f"🟡 **{tage} Tage** — langsam Preis senken"
                st.warning(f"⚠️ {it['artikel']}: {alarm}")
            elif tage >= 14:
                st.info(f"ℹ️ {it['artikel']}: {tage} Tage — beobachten")

            c1,c2,c3,c4,c5 = st.columns([3,1,1,1,1])
            # Farbe je nach Liegezeit
            tage_farbe = "🔴" if tage>=60 else "🟡" if tage>=30 else "🟢" if tage<14 else "🟠"
            c1.markdown(f"**{it['artikel']}** ({it['zustand']}) — {it['plattform']}")
            c2.markdown(f"€{it['ek']:.0f}")
            c3.markdown(f"→ €{it['vk']:.0f}")
            c4.markdown(f"**+€{it['gewinn']:.0f}**")
            c5.markdown(f"{tage_farbe} {tage}T")

# ════════════════════════════════════════════════════════════
# TAB 4 — OCR
# ════════════════════════════════════════════════════════════
with T[3]:
    st.header("📚 OCR Medien-Scanner")
    ocr_b=st.file_uploader("📷 Stapel fotografieren",type=["jpg","jpeg","png"],key="ocr_b")
    ocr_t=st.selectbox("Typ",["Bücher","CDs/Vinyl","Video-Spiele","DVDs","Gemischt"],key="ocr_t")
    if st.button("🔍 Analysieren",type="primary",use_container_width=True,key="ocr_btn"):
        if ocr_b:
            with st.spinner("🤖 3 KIs scannen + Web verifiziert..."):
                b64=base64.b64encode(ocr_b.read()).decode()
                p=(f"Scanne ALLE {ocr_t}. Für jeden: Titel | eBay:€X | KA:€X | Vinted:€X | FM:€X\n"
                   f"Top-3 wertvollste + Gesamtwert. Deutsch.")
                scan_ergebnis = ensemble_ki(p,bilder=[b64])
                st.markdown(scan_ergebnis)
                # Web verifiziert Top-Artikel
                erste_zeile = scan_ergebnis.split("\n")[0][:40] if scan_ergebnis else ""
                if erste_zeile:
                    web_ocr = multi_suche(erste_zeile+" Preis eBay Deutschland "+datetime.now().strftime("%Y"))
                    if web_ocr:
                        st.success("✅ Web-Preisverifikation:")
                        preis_check = ki(f"Vergleiche diese Web-Preise mit dem Scan-Ergebnis für '{erste_zeile}'.\nWeb: {web_ocr[:400]}\nScan: {scan_ergebnis[:300]}\nKurzes Fazit: Sind die Preise realistisch? Empfehlung? Deutsch.")
                        st.info("🌐 "+preis_check)

# ════════════════════════════════════════════════════════════
# TAB 5 — REPARATUR
# ════════════════════════════════════════════════════════════
with T[4]:
    st.header("🔧 Reparatur-Rechner")
    rep_fotos=st.file_uploader("📷 Fotos",type=["jpg","jpeg","png"],accept_multiple_files=True,key="rep_fotos")
    if rep_fotos:
        cols=st.columns(min(len(rep_fotos),4))
        for i,f in enumerate(rep_fotos):
            with cols[i%4]: st.image(f,caption=f"Foto {i+1}",use_column_width=True)
    c1,c2=st.columns(2)
    with c1:
        ra=st.text_input("Artikel",key="ra"); rek2=st.number_input("EK €",min_value=0.0,value=15.0,key="rek2")
        rm=st.number_input("Material €",min_value=0.0,value=25.0,key="rm"); rs=st.number_input("Stunden",min_value=0.5,value=3.0,step=0.5,key="rs")
    with c2:
        rvk=st.number_input("VK €",min_value=0.0,value=120.0,key="rvk")
        rpl=st.selectbox("Plattform",["Kleinanzeigen","eBay","Vinted","Facebook","Flohmarkt"],key="rpl")
        rb=st.text_area("Was reparieren?",height=70,key="rb")
    if st.button("🔧 Berechnen",type="primary",use_container_width=True,key="r_btn"):
        geb=rvk*(0.119 if "eBay" in rpl else 0.05 if "Vinted" in rpl else 0.02)
        gk=rek2+rm+(rvk*0.02)+geb; gw=rvk-gk; sl=gw/rs if rs>0 else 0
        c1,c2,c3,c4=st.columns(4)
        c1.metric("Kosten",f"€{gk:.2f}"); c2.metric("Gewinn",f"€{gw:.2f}")
        c3.metric("Stundenlohn",f"€{sl:.2f}/h"); c4.metric("ROI",f"{(gw/gk*100) if gk>0 else 0:.0f}%")
        if sl>=15: st.success("✅ LOHNT SICH!")
        elif sl>=8: st.warning("⚠️ Grenzfall")
        else: st.error("❌ Lohnt nicht")
        if rb:
            with st.spinner("💡 3 KIs + Web..."):
                rep_b=[base64.b64encode(f.read()).decode() for f in rep_fotos] if rep_fotos else None
                web_rep = google_suche(f"{ra} Reparatur Materialkosten Deutschland "+rb[:30])
                mat_k = f"\nAktuelle Materialpreise laut Web: {web_rep[:200]}" if web_rep else ""
                st.markdown(ensemble_ki(
                    f"3 konkrete Reparatur-Tipps für '{ra}': {rb}.{mat_k}\n"
                    f"Methode, Materialkosten, Zeitaufwand, Wertsteigerung. Deutsch.",bilder=rep_b))

# ════════════════════════════════════════════════════════════
# TAB 6 — TRENDS (ECHTZEIT ENSEMBLE)
# ════════════════════════════════════════════════════════════
with T[5]:
    st.header("📈 Markt-Trends — Echtzeit Ensemble")
    st.markdown(f"Live {datetime.now().strftime('%d.%m.%Y')} · 3 KIs + Google/Tavily/You.com")
    c1,c2=st.columns(2)
    with c1: tr_kat=st.selectbox("Kategorie:",["Alles","Kleidung","Porzellan","Elektronik","Möbel","Spielzeug","Bücher"],key="tr_kat")
    with c2: tr_region=st.selectbox("Region:",["Berlin","Deutschland"],key="tr_region")
    if st.button("🔥 Live-Ensemble Analyse",type="primary",use_container_width=True,key="tr_btn"):
        with st.spinner("🌐 Web + 3 KIs analysieren..."):
            # Aktuelle Woche UND letzte Woche gleichzeitig suchen
            from datetime import timedelta
            letzte_woche = (datetime.now() - timedelta(days=7)).strftime("%B %Y")
            jetzt = datetime.now().strftime("%B %Y")

            def suche_jetzt():
                return multi_suche(tr_kat+" Secondhand Trend "+jetzt+" "+tr_region)
            def suche_vorher():
                return google_suche(tr_kat+" Secondhand Preise "+letzte_woche+" "+tr_region)

            web_jetzt = web_vorher = None
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
                fj = ex.submit(suche_jetzt)
                fv = ex.submit(suche_vorher)
                web_jetzt  = fj.result()
                web_vorher = fv.result()

            web_k = ""
            if web_jetzt:  web_k += "\nAKTUELL:\n" + web_jetzt[:300]
            if web_vorher: web_k += "\nLETZTE WOCHE:\n" + web_vorher[:200]

            if web_jetzt or web_vorher: st.success("✅ Aktuelle + vergangene Web-Daten!")

            p = (
                "Markt-Analyst " + tr_region + " " + jetzt + "." + web_k + "\n"
                "Analysiere: " + tr_kat + ". Deutsch.\n\n"
                "📊 VERGLEICH DIESE WOCHE vs LETZTE WOCHE:\n"
                "- Was ist neu gestiegen? ↑\n"
                "- Was ist gefallen? ↓\n"
                "- Was ist stabil? →\n\n"
                "🔥 TOP 5 ARTIKEL JETZT: Name | €X | Trend ↑↓→\n"
                "📈 PREISE STEIGEN:\n"
                "📉 PREISE FALLEN:\n"
                "💎 GEHEIMTIPP " + datetime.now().strftime("%B") + ":\n"
                "🗓️ JETZT VERKAUFEN:\n"
                "🔍 GOLD-SUCHBEGRIFFE:"
            )
            st.markdown(ensemble_ki(p))
    st.markdown("---")
    tf=st.text_input("🤖 Frage:",key="tf")
    if st.button("Analysieren",key="t_btn"):
        if tf:
            with st.spinner("..."):
                web2=tavily_suche(tf+" "+datetime.now().strftime("%B %Y"))
                p2=f"Experte {tr_region} {datetime.now().strftime('%B %Y')}. {('Web: '+web2) if web2 else ''}\nKonkret Deutsch: {tf}"
                st.markdown(ensemble_ki(p2))

# ════════════════════════════════════════════════════════════
# TAB 7 — VERHANDLUNG
# ════════════════════════════════════════════════════════════
with T[6]:
    st.header("🎭 Verhandlungs-Simulator")
    c1,c2=st.columns(2)
    with c1:
        va=st.text_input("Artikel",key="va"); vvk=st.number_input("Verkäufer €",min_value=1.0,value=80.0,key="vvk")
        vz=st.number_input("Ihr Ziel €",min_value=1.0,value=40.0,key="vz")
    with c2:
        vt=st.selectbox("Typ",["Sturköpfig","Freundlich","Gestresst","Unentschlossen","Profi"],key="vt")
        vpl=st.selectbox("Wo?",["Flohmarkt","Kleinanzeigen","Facebook"],key="vpl")
    if st.button("🎭 Start",type="primary",use_container_width=True,key="v_start"):
        if va:
            st.session_state.sim=[]
            # Web sucht aktuelle Preise für bessere Simulation
            web_v = google_suche(va+" Preis Deutschland Secondhand")
            preis_k = f" Aktueller Marktpreis laut Web: {web_v[:100]}" if web_v else ""
            r=ensemble_ki("Du bist Verkäufer (" + vt + ") auf " + vpl + ". Artikel: " + va + " für €" + str(vvk) + "." + preis_k + "\nErste Reaktion auf Verhandlungsfrage. 2-3 Sätze. Deutsch. Rolle bleiben!")
            st.session_state.sim.append({"r":"🏪","t":r}); st.rerun()
    if st.session_state.sim:
        st.markdown("---")
        for m in st.session_state.sim:
            if m["r"]=="🏪": st.info(f"**🏪:** {m['t']}")
            else: st.success(f"**🛒:** {m['t']}")
        km=st.text_area("📩 Kunden-Nachricht:",height=60,key="v_kunde")
        ai=st.text_input("Ihre Antwort:",key="v_inp")
        c1,c2=st.columns(2)
        with c1:
            if st.button("📤 Senden",type="primary",use_container_width=True,key="v_send"):
                eingabe=km.strip() if km.strip() else ai
                if eingabe:
                    st.session_state.sim.append({"r":"🛒","t":eingabe})
                    verl="\n".join([f"{m['r']}: {m['t']}" for m in st.session_state.sim])
                    r=ensemble_ki(f"Verkäufer ({vt}) {va} €{vvk}. Verlauf:\n{verl}\nAntworte als Verkäufer (2-3 Sätze, Deutsch, Rolle bleiben)!")
                    st.session_state.sim.append({"r":"🏪","t":r}); st.rerun()
        with c2:
            if st.button("🧠 Strategie",use_container_width=True,key="v_str"):
                verl="\n".join([f"{m['r']}: {m['t']}" for m in st.session_state.sim])
                st.markdown(ensemble_ki(f"Verhandlungsanalyse {va}, Ziel €{vz}.\n{verl}\n1.Was gut? 2.Besser? 3.Nächste Nachricht? Deutsch."))

# ════════════════════════════════════════════════════════════
# TAB 8 — FOTO-COACH
# ════════════════════════════════════════════════════════════
with T[7]:
    st.header("📸 Foto-Coach")
    fc_b=st.file_uploader("Foto hochladen",type=["jpg","jpeg","png"],key="fc_b")
    fc_p=st.selectbox("Plattform",["Kleinanzeigen","Vinted","eBay","Facebook","Alle"],key="fc_p")
    if st.button("📸 Analysieren",type="primary",use_container_width=True,key="fc_btn"):
        if fc_b:
            with st.spinner("🔍 3 KIs bewerten..."):
                b64=base64.b64encode(fc_b.read()).decode()
                c1,c2=st.columns(2)
                with c1: fc_b.seek(0); st.image(fc_b,caption="Ihr Foto",use_column_width=True)
                with c2: st.markdown(ensemble_ki(
                    f"Foto-Experte {fc_p}. Bewerte + verbessere. Deutsch.\n"
                    f"Note 1-10: Helligkeit,Hintergrund,Schärfe,Winkel\n"
                    f"Probleme + 3 Verbesserungen + Perfektes Foto + Preis-Potenzial +X%",bilder=[b64]))

# ════════════════════════════════════════════════════════════
# TAB 9 — FLOHMÄRKTE
# ════════════════════════════════════════════════════════════
with T[8]:
    st.header("🗺️ Berliner Flohmärkte")

    # Datum + Woche + Wochentag
    jetzt = datetime.now()
    tage_de = {"Monday":"Montag","Tuesday":"Dienstag","Wednesday":"Mittwoch",
               "Thursday":"Donnerstag","Friday":"Freitag","Saturday":"Samstag","Sunday":"Sonntag"}
    heute_de = tage_de.get(jetzt.strftime("%A"), "Heute")
    kw = jetzt.isocalendar()[1]  # Kalenderwoche

    # Info-Leiste
    c1,c2,c3 = st.columns(3)
    c1.metric("📅 Heute", f"{heute_de}, {jetzt.strftime('%d.%m.%Y')}")
    c2.metric("📆 Kalenderwoche", f"KW {kw} / {jetzt.year}")
    c3.metric("🗓️ Monat", jetzt.strftime("%B %Y"))

    # Wochenübersicht
    from datetime import timedelta
    montag = jetzt - timedelta(days=jetzt.weekday())
    sonntag = montag + timedelta(days=6)
    st.info(
        f"📆 **Aktuelle Woche {kw}:** "
        f"{montag.strftime('%d.%m.')} – {sonntag.strftime('%d.%m.%Y')} · "
        f"Heute ist **{heute_de}**"
    )
    if st.button(f"🔴 Live-Update für {heute_de} abrufen",type="primary",use_container_width=True,key="floh_live"):
        with st.spinner("🌐 Suche aktuelle Marktinfos..."):
            # Echtzeit-Suche für heute
            web1 = google_suche("Flohmarkt Berlin " + heute_de + " " + datetime.now().strftime("%B %Y") + " offen Termine")
            web2 = tavily_suche("Flohmarkt Trödelmarkt Berlin " + heute_de + " " + datetime.now().strftime("%d.%m.%Y"))

            web_info = ""
            if web1: web_info += web1[:200]
            if web2: web_info += web2[:200]

            p = (
                "Berliner Flohmarkt-Experte. Heute ist " + heute_de + " " +
                datetime.now().strftime("%d.%m.%Y") + ".\n" +
                ("Aktuelle Web-Infos:\n" + web_info + "\n\n" if web_info else "") +
                "Antworte kurz auf Deutsch:\n"
                "🏪 HEUTE OFFEN: [Märkte die heute definitiv offen sind]\n"
                "⭐ EMPFEHLUNG: [Welcher Markt ist heute am besten für Reseller?]\n"
                "💡 TIPP: [Ein konkreter Tipp für heute " + heute_de + "]\n"
                "⚠️ GESCHLOSSEN: [Welche Märkte heute nicht öffnen]"
            )
            st.info("📅 " + ki(p))
    st.markdown("---")
    # NUR echte Flohmärkte mit Ständen — keine Läden, keine Einkaufszentren!
    maerkte=[

        # ══════ MONTAG ══════
        # ══════ MONTAG ══════
        # Hinweis: Montags gibt es in Berlin kaum reguläre Flohmärkte.
        # Die meisten Außenmärkte öffnen erst Di oder Fr!

        # ══════ DIENSTAG ══════
        ("Di","Kunst- & Trödelmarkt Fehrbelliner Platz","Fehrbelliner Pl., 10707 Berlin","Di & Fr 8-15h",
         "Burdack Märkte: info@burdack-maerkte.de","🏺 Antiquitäten, Kunst, Porzellan, Silber","⭐⭐⭐⭐⭐",
         "Echter Außen-Flohmarkt mit Händler-Ständen! Di weniger Leute = beste Verhandlung",
         "https://maps.google.com/?q=Fehrbelliner+Platz+Berlin"),

        # ══════ MITTWOCH ══════
        ("Mi","Trödelmarkt Weißenfelser Str.","Weißenfelser Str. 6, 12627 Berlin-Marzahn","Mi-So 8-18:30h",
         "Vor Ort anmelden","🛍️ Gemischt, Haushalt, Kleidung","⭐⭐⭐",
         "Echter Außen-Trödelmarkt Mi-So! Günstige Standgebühren",
         "https://maps.google.com/?q=Weißenfelser+Straße+6+Berlin+Marzahn"),

        # ══════ DONNERSTAG ══════
        ("Do","Trödelmarkt Weißenfelser Str.","Weißenfelser Str. 6, 12627 Berlin-Marzahn","Mi-So 8-18:30h",
         "Vor Ort anmelden","🛍️ Gemischt, Haushalt","⭐⭐⭐",
         "Do meist ruhig — gut für schnelle Verkäufe unter der Woche",
         "https://maps.google.com/?q=Weißenfelser+Straße+6+Berlin+Marzahn"),

        # ══════ FREITAG ══════
        ("Fr","Kunst- & Trödelmarkt Fehrbelliner Platz","Fehrbelliner Pl., 10707 Berlin","Di & Fr 8-15h",
         "Burdack Märkte: info@burdack-maerkte.de","🏺 Antiquitäten, Kunst, Porzellan, Silber","⭐⭐⭐⭐⭐",
         "Fr = BESTE AUSWAHL der Woche! Früh kommen für Schnäppchen",
         "https://maps.google.com/?q=Fehrbelliner+Platz+Berlin"),

        ("Fr","Antik & Sammlermarkt Ostbahnhof","Erich-Steinfurth-Str. 1, 10243 Berlin-Friedrichshain","Fr-So 9-16h",
         "oldthing märkte — online: www.oldthing.de","🛍️ Antiquitäten, Sammler, Bücher","⭐⭐⭐⭐",
         "Fr = wenig Besucher, beste Preise! Sa/So deutlich voller",
         "https://maps.google.com/?q=Flohmarkt+Ostbahnhof+Berlin"),

        ("Fr","Trödelmarkt Weißenfelser Str.","Weißenfelser Str. 6, 12627 Berlin-Marzahn","Mi-So 8-18:30h",
         "Vor Ort anmelden","🛍️ Gemischt, Haushalt","⭐⭐⭐",
         "Fr = letzter Werktag, Händler räumen Restbestände günstig!",
         "https://maps.google.com/?q=Weißenfelser+Straße+6+Berlin+Marzahn"),

        # ══════ SAMSTAG ══════
        ("Sa","Flohmarkt Straße des 17. Juni","Str. des 17. Juni 17, 10623 Berlin (S Tiergarten)","Sa & So 10-17h",
         "Berliner Trödel GmbH: 030-2655000","🏺 Hochwertige Antiquitäten, Kunst, Schmuck","⭐⭐⭐⭐⭐",
         "Größter Antik-Flohmarkt Berlins! Professionelle Händler-Stände",
         "https://maps.google.com/?q=Flohmarkt+Straße+des+17+Juni+Berlin"),

        ("Sa","RAW Flohmarkt","Revaler Str. 99, 10245 Berlin-Friedrichshain","Sa & So 10-18h",
         "info@raw-flohmarkt.de","🕶️ Vintage Mode, Vinyl, Streetwear","⭐⭐⭐⭐⭐",
         "Beste Vintage-Kleidung Berlins! Junges kaufkräftiges Publikum",
         "https://maps.google.com/?q=RAW+Gelände+Berlin"),

        ("Sa","Antik & Sammlermarkt Ostbahnhof","Erich-Steinfurth-Str. 1, 10243 Berlin","Fr-So 9-16h",
         "oldthing märkte — online: www.oldthing.de","🛍️ Antiquitäten, Sammler","⭐⭐⭐⭐",
         "Sa voller als Fr — trotzdem gute Auswahl",
         "https://maps.google.com/?q=Flohmarkt+Ostbahnhof+Berlin"),

        ("Sa","Antik & Buchmarkt am Bodemuseum","Am Kupfergraben 3, 10117 Berlin-Mitte","Sa & So 11-17h",
         "M.S.P-Marktservice UG — vor Ort","🏛️ Antiquitäten, Bücher, Kunst","⭐⭐⭐⭐",
         "Traumhafte Lage am Museumsufer! Hochwertiges Angebot",
         "https://maps.google.com/?q=Am+Kupfergraben+Berlin+Bodemuseum"),

        ("Sa","Flohmarkt Rathaus Schöneberg","John-F.-Kennedy-Pl., 10825 Berlin-Schöneberg","Sa & So 8-16h",
         "Bezirksamt Tempelhof-Schöneberg","🛍️ Gemischt, Haushalt, Kleidung","⭐⭐⭐⭐",
         "Wöchentlich Sa & So! Großer Außenmarkt, viele private Verkäufer",
         "https://maps.google.com/?q=Rathaus+Schöneberg+Berlin+Flohmarkt"),

        ("Sa","Trödelmarkt Bergmannstraße","Marheinekeplatz, 10961 Berlin-Kreuzberg","Sa 8-16h",
         "Vor Ort anmelden","🌿 Vintage, Kreuzberg-Flair, Design","⭐⭐⭐⭐",
         "Echter Außen-Flohmarkt! Kreuzberger Atmosphäre, junges Publikum",
         "https://maps.google.com/?q=Marheinekeplatz+Berlin+Kreuzberg"),

        ("Sa","Kosmonauten Markt Marzahn","Beilsteiner Str. 51, 12681 Berlin-Marzahn","Sa 9-18h",
         "01624942851 | info@kosmonautenmarkt.de","🔧 Haushalt, Technik, Gemischt","⭐⭐⭐",
         "Ganzjährig jeden Sa! Günstige Standgebühren für Händler",
         "https://maps.google.com/?q=Beilsteiner+Straße+51+Berlin+Marzahn"),

        ("Sa","ICK TRÖDEL — Spandau Ollenhauer Str.","Ollenhauer Str. 107, 13583 Berlin-Spandau","Sa 8-16h",
         "Ahmet Yesildag: 0179 483 05 42 | icktroedel.de","🛍️ Gemischt, Haushalt","⭐⭐⭐",
         "ICK TRÖDEL samstags! Günstiger Außenmarkt in Spandau",
         "https://maps.google.com/?q=Ollenhauer+Straße+107+Berlin+Spandau"),

        ("Sa","Trödelmarkt Weißenfelser Str.","Weißenfelser Str. 6, 12627 Berlin-Marzahn","Mi-So 8-18:30h",
         "Vor Ort anmelden","🛍️ Gemischt, Haushalt","⭐⭐⭐",
         "Sa mehr Besucher! Guter Umsatz möglich",
         "https://maps.google.com/?q=Weißenfelser+Straße+6+Berlin+Marzahn"),

        ("Sa","Hallentrödelmarkt Arena Berlin","Eichenstr. 4, 12435 Berlin-Treptow","Sa & So 10-17h",
         "Arena Berlin: 030-53320340","🏛️ Gemischt, Überdacht","⭐⭐⭐⭐",
         "Überdacht! Bei jedem Wetter. Große Halle mit vielen Ständen",
         "https://maps.google.com/?q=Arena+Berlin+Eichenstraße+4"),

        # ══════ SONNTAG ══════
        ("So","Flohmarkt im Mauerpark","Bernauer Str. 63-64, 13355 Berlin-Mitte","So 10-18h | Aufbau ab 8h",
         "Tel: 030-29772486 | info@flohmarktimmauerpark.de | Stand: So 10-13h am Infostand",
         "🎭 Vintage, Mode, Vinyl, Kuriositäten","⭐⭐⭐⭐⭐",
         "Berlins berühmtester Flohmarkt! ~150 Stände. Stand: persönlich So 10-13h buchen",
         "https://maps.google.com/?q=Mauerpark+Flohmarkt+Berlin"),

        ("So","Flohmarkt am Boxhagener Platz","Boxhagener Pl. 1, 10245 Berlin-Friedrichshain","So 10-18h",
         "Vor Ort anmelden (direkt beim Marktleiter)","🏺 Antiquitäten, Porzellan, Bücher, Vinyl","⭐⭐⭐⭐⭐",
         "TOP für Porzellan & Antiquitäten! Echte Sammler kaufen hier",
         "https://maps.google.com/?q=Boxhagener+Platz+Flohmarkt+Berlin"),

        ("So","ICK TRÖDEL — OBI Spandau","Wilhelmstr. 8, 13595 Berlin-Spandau","So 8-16h | Aufbau bis 7:30h",
         "Ahmet Yesildag: 0179 483 05 42 | Tel: 030-38307044 | icktroedel.de",
         "🛍️ Gemischt, Haushalt, Kleidung, Vintage","⭐⭐⭐⭐⭐",
         "IHR STAMMMARKT! Jeden So. Marktbude 30€ (überdacht) oder Freifläche 9€/lm",
         "https://maps.google.com/?q=Wilhelmstraße+8+13595+Berlin+Spandau"),

        ("So","Flohmarkt Kaufland Spandau","Pichelswerderstr. 6, 13597 Berlin (neben IKEA)","So 8-16h",
         "Höfges Event Group GmbH","🛍️ Gemischt, Haushalt, Kleidung","⭐⭐⭐⭐",
         "Jeden So! Großer Außenparkplatz, viele Besucher aus Spandau",
         "https://maps.google.com/?q=Pichelswerderstraße+6+13597+Berlin"),

        ("So","Flohmarkt Straße des 17. Juni","Str. des 17. Juni 17, 10623 Berlin","Sa & So 10-17h",
         "Berliner Trödel GmbH: 030-2655000","🏺 Hochwertige Antiquitäten, Kunst","⭐⭐⭐⭐⭐",
         "So professionelle Händler — hochpreisig aber lohnend",
         "https://maps.google.com/?q=Flohmarkt+Straße+des+17+Juni+Berlin"),

        ("So","Antik & Sammlermarkt Ostbahnhof","Erich-Steinfurth-Str. 1, 10243 Berlin","Fr-So 9-16h",
         "oldthing märkte — www.oldthing.de","🛍️ Antiquitäten, Sammler","⭐⭐⭐⭐",
         "So am vollsten — früh kommen! Fr deutlich ruhiger",
         "https://maps.google.com/?q=Flohmarkt+Ostbahnhof+Berlin"),

        ("So","Arkonaplatz Flohmarkt","Arkonaplatz, 10435 Berlin-Prenzlauer Berg","So 10-16h",
         "Keine Standanmeldung nötig — einfach kommen","🏛️ Antiquitäten, Raritäten, Bücher","⭐⭐⭐⭐",
         "Klein aber fein! Echte Raritäten, kaum Touristenware",
         "https://maps.google.com/?q=Arkonaplatz+Flohmarkt+Berlin"),

        ("So","Flohmarkt Rathaus Schöneberg","John-F.-Kennedy-Pl., 10825 Berlin-Schöneberg","Sa & So 8-16h",
         "Bezirksamt Tempelhof-Schöneberg","🛍️ Gemischt, Haushalt, Kleidung","⭐⭐⭐⭐",
         "So viele private Verkäufer! Groß und zentraler Standort",
         "https://maps.google.com/?q=Rathaus+Schöneberg+Berlin+Flohmarkt"),

        ("So","Nowkoelln Flowmarkt","Maybachufer, 12047 Berlin-Neukölln","2. & 4. So im Monat 11-18h",
         "info@nowkoelln.de | www.nowkoelln.de","🎨 Design, Vintage, Handgemachtes","⭐⭐⭐⭐",
         "Nur 2x im Monat! Kreatives Publikum, gute Preise für Besonderes",
         "https://maps.google.com/?q=Maybachufer+Neukölln+Berlin"),

        ("So","Treptower Park Flohmarkt","Alt-Treptow, 12435 Berlin-Treptow","So 8-16h",
         "Vor Ort anmelden","🔧 Elektronik, Werkzeug, DDR-Artikel","⭐⭐⭐⭐",
         "Gut für DDR-Artikel & Elektronik! Günstige Preise",
         "https://maps.google.com/?q=Treptower+Park+Flohmarkt+Berlin"),

        ("So","Hallentrödelmarkt Arena Berlin","Eichenstr. 4, 12435 Berlin-Treptow","Sa & So 10-17h",
         "Arena Berlin: 030-53320340","🏛️ Gemischt, überdacht","⭐⭐⭐⭐",
         "Überdacht! Bei jedem Wetter. So mehr Besucher als Sa",
         "https://maps.google.com/?q=Arena+Berlin+Eichenstraße+4"),

        ("So","Antik & Buchmarkt am Bodemuseum","Am Kupfergraben 3, 10117 Berlin-Mitte","Sa & So 11-17h",
         "M.S.P-Marktservice UG","🏛️ Antiquitäten, Bücher, Kunst","⭐⭐⭐⭐",
         "Traumhafte Lage! So mehr Publikum als Sa",
         "https://maps.google.com/?q=Am+Kupfergraben+Berlin+Bodemuseum"),

        ("So","ICK TRÖDEL — EDEKA Spandau","Falkenseer Chaussee 239, 13583 Berlin-Spandau","So 8-16h",
         "ICK TRÖDEL: 0179 483 05 42 | icktroedel.de","🛍️ Gemischt, Kleidung","⭐⭐⭐",
         "Wöchentlich! Günstiger Spandauer Außenmarkt",
         "https://maps.google.com/?q=Falkenseer+Chaussee+239+Berlin"),

        ("So","Trödelmarkt Weißenfelser Str.","Weißenfelser Str. 6, 12627 Berlin-Marzahn","Mi-So 8-18:30h",
         "Vor Ort anmelden","🛍️ Gemischt, Haushalt","⭐⭐⭐",
         "So am meisten Besucher! Guter Umsatz",
         "https://maps.google.com/?q=Weißenfelser+Straße+6+Berlin+Marzahn"),

    ]
    tage=["Alle","Mo","Di","Mi","Do","Fr","Sa","So"]
    fw=st.radio("📅 Tag:",tage,horizontal=True,key="fw")
    st.markdown("---")
    liste=maerkte if fw=="Alle" else [m for m in maerkte if m[0]==fw]
    if fw=="Alle":
        for tag in tage[1:]:
            tm=[m for m in maerkte if m[0]==tag]
            if tm:
                st.markdown(f"### 📅 {tag}")
                for m in tm:
                    with st.expander(f"{m[6]} **{m[1]}**"):
                        c1,c2=st.columns([2,1])
                        with c1: st.markdown(f"📍 {m[2]}\n\n🕐 {m[3]}\n\n📞 **{m[4]}**\n\n🏷️ {m[5]}\n\n💡 *{m[7]}*")
                        with c2: st.markdown(m[6]); st.link_button("🗺️",m[8],use_container_width=True)
    else:
        for m in liste:
            with st.expander(f"{m[6]} **{m[1]}**"):
                c1,c2=st.columns([2,1])
                with c1: st.markdown(f"📍 {m[2]}\n\n🕐 {m[3]}\n\n📞 **{m[4]}**\n\n🏷️ {m[5]}\n\n💡 *{m[7]}*")
                with c2: st.markdown(m[6]); st.link_button("🗺️",m[8],use_container_width=True)

    st.markdown("---")
    fq=st.text_input("🤖 Frage:",key="fq")
    if st.button("Fragen",type="primary",use_container_width=True,key="f_btn"):
        if fq:
            with st.spinner("..."):
                wf=google_suche(fq+" Flohmarkt Berlin")
                p=f"Berliner Flohmarkt-Experte {datetime.now().strftime('%B %Y')}. {('Web: '+wf[:200]) if wf else ''}\nDeutsch: {fq}"
                st.markdown(ensemble_ki(p))

# ════════════════════════════════════════════════════════════
# TAB 10 — MARKEN
# ════════════════════════════════════════════════════════════
with T[9]:
    st.header("🔬 Marken-Scanner")
    ms_b=st.file_uploader("📷 Stempel/Logo",type=["jpg","jpeg","png"],key="ms_b")
    ms_k=st.selectbox("Kategorie",["Porzellan","Silber","Uhren","Schmuck","Elektronik","Kleidung","Spielzeug","Unbekannt"],key="ms_k")
    if st.button("🔬 Identifizieren",type="primary",use_container_width=True,key="ms_btn"):
        if ms_b:
            with st.spinner("3 KIs identifizieren + Web-Recherche..."):
                b64=base64.b64encode(ms_b.read()).decode()
                c1,c2=st.columns(2)
                with c1: ms_b.seek(0); st.image(ms_b,caption="Stempel",use_column_width=True)
                with c2:
                    marken_analyse = ensemble_ki(
                        f"Marken-Experte {ms_k}. Identifiziere Stempel/Logo. Deutsch.\n"
                        f"Marke, Herkunft, Jahr, Echtheit, Seltenheit, Wert €X, eBay-Suchbegriff.",bilder=[b64])
                    st.markdown(marken_analyse)
                    # eBay-Suchbegriff aus Analyse extrahieren
                    ebay_begriff = ""
                    for line in marken_analyse.split("\n"):
                        if "eBay-Suchbegriff:" in line:
                            teil = line.split(":")[-1].strip().strip("[]")
                            if len(teil) > 2: ebay_begriff = teil[:50]; break
                    if not ebay_begriff:
                        ebay_begriff = marken_analyse.split("\n")[0][:40]

                    # Direkte Links zu Auktionsplattformen
                    if ebay_begriff:
                        st.markdown("---")
                        st.markdown("**🔗 Direkt suchen auf:**")
                        enc = urllib.parse.quote(ebay_begriff)
                        cl1,cl2 = st.columns(2)
                        with cl1:
                            st.link_button("🛒 eBay Auktionen", "https://www.ebay.de/sch/i.html?_nkw="+enc+"&LH_Auction=1", use_container_width=True)
                            st.link_button("📱 Kleinanzeigen", "https://www.kleinanzeigen.de/s-"+enc+"/k0", use_container_width=True)
                        with cl2:
                            st.link_button("🏛️ Catawiki", "https://www.catawiki.com/de/l?q="+enc, use_container_width=True)
                            st.link_button("🔍 Dorotheum", "https://www.dorotheum.com/suche/?q="+enc, use_container_width=True)

                    # Web-Recherche
                    marke_name = marken_analyse.split("\n")[0][:40] if marken_analyse else ""
                    if marke_name:
                        web_mk = multi_suche(marke_name+" "+ms_k+" Wert Preis eBay Auktion")
                        if web_mk:
                            mk_bewertung = ki("Bewerte Web-Infos zur Marke '" + marke_name + "'. Deutsch. Fazit: Wert, Seltenheit, wo verkaufen.\n" + web_mk[:400])
                            st.info("🌐 "+mk_bewertung)

# ════════════════════════════════════════════════════════════
# TAB 11 — TIMING
# ════════════════════════════════════════════════════════════
with T[10]:
    st.header("📅 Saisonaler Timing-Planer")
    ti_a=st.text_input("Artikel",key="ti_a")
    ti_m=st.selectbox("Monat",["Januar","Februar","März","April","Mai","Juni",
        "Juli","August","September","Oktober","November","Dezember"],index=datetime.now().month-1,key="ti_m")
    if st.button("📅 Analysieren",type="primary",use_container_width=True,key="ti_btn"):
        if ti_a:
            with st.spinner("3 KIs + Web..."):
                web=google_suche(ti_a+" Secondhand Saison Trend "+ti_m)
                p=(f"Timing-Experte. Artikel: {ti_a} | {ti_m}. {('Web: '+web[:200]) if web else ''}\n"
                   f"Beste/schlechteste Monate + Monatstabelle + Jetzt-Empfehlung. Deutsch.")
                st.markdown(ensemble_ki(p))

# ════════════════════════════════════════════════════════════
# TAB 12 — ANZEIGEN-KI
# ════════════════════════════════════════════════════════════
with T[11]:
    st.header("✨ Anzeigen-Optimierer")
    ao_fotos=st.file_uploader("📷 Fotos",type=["jpg","jpeg","png"],accept_multiple_files=True,key="ao_fotos")
    if ao_fotos:
        cols=st.columns(min(len(ao_fotos),4))
        for i,f in enumerate(ao_fotos): cols[i%4].image(f,caption=f"Foto {i+1}",use_column_width=True)
    c1,c2=st.columns(2)
    with c1:
        ao_l=st.selectbox("Plattform",["Kleinanzeigen","Vinted","eBay","Facebook"],key="ao_l")
        ao_p=st.number_input("Preis €",min_value=0.0,value=45.0,key="ao_p")
    with c2:
        ao_k=st.selectbox("Kategorie",["Haushalt","Kleidung","Elektronik","Möbel","Spielzeug","Sonstiges"],key="ao_k")
        ao_t2=st.number_input("Tage online",min_value=0,value=7,key="ao_t2")
    ao_ti=st.text_input("Titel:",key="ao_ti"); ao_tx=st.text_area("Beschreibung:",height=80,key="ao_tx")
    if st.button("✨ Optimieren",type="primary",use_container_width=True,key="ao_btn"):
        if ao_ti or ao_tx or ao_fotos:
            with st.spinner("3 KIs optimieren..."):
                ao_b=[base64.b64encode(f.read()).decode() for f in ao_fotos] if ao_fotos else None
                web=google_suche(f"{ao_ti} {ao_k} Preis Kleinanzeigen eBay Deutschland")
                p=(f"Anzeigen-Experte {ao_l}. {ao_k}. €{ao_p}. {ao_t2} Tage online.\n"
                   f"Titel: {ao_ti}\nText: {ao_tx}\n{('Web-Preise: '+web[:200]) if web else ''}\n"
                   f"Note 1-10 + Schwächen + Neuer Titel + Neue Beschreibung + Preis + Keywords + Tipps. Deutsch.")
                st.markdown(ensemble_ki(p,bilder=ao_b))

# ════════════════════════════════════════════════════════════
# TAB 13 — CHAT
# ════════════════════════════════════════════════════════════
with T[12]:
    st.header("🤖 KI-Reselling-Chat — Ultimate")
    st.markdown("Chat mit **Fotos · Lagerbestand · Lern-System · Web-Suche · 3 KIs gleichzeitig**")

    # ── KONTEXT-ANZEIGE ──
    c1,c2,c3 = st.columns(3)
    with c1:
        lager_n = len(st.session_state.lager)
        st.metric("📦 Lager", f"{lager_n} Artikel")
    with c2:
        wissen_n = len(st.session_state.mein_wissen) + len(st.session_state.preis_korrekturen)
        st.metric("🧠 Wissen", f"{wissen_n} Einträge")
    with c3:
        st.metric("💬 Nachrichten", len(st.session_state.chat_history))

    # ── FOTO-UPLOAD FÜR CHAT ──
    with st.expander("📷 Foto zum Chat hinzufügen (optional)"):
        chat_foto = st.file_uploader("Foto hochladen",
            type=["jpg","jpeg","png","webp"], key="chat_foto")
        if chat_foto:
            st.image(chat_foto, caption="Foto für Chat", use_column_width=True)

    # ── CHAT-VERLAUF ──
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── EINGABE ──
    if prompt_chat := st.chat_input("Fragen Sie alles — auch über Fotos, Lager, Preise..."):
        st.session_state.chat_history.append({"role":"user","content":prompt_chat})
        with st.chat_message("user"):
            st.markdown(prompt_chat)

        with st.chat_message("assistant"):
            with st.spinner("🤖 3 KIs + Web denken nach..."):

                # ── KONTEXT AUFBAUEN ──
                # 1. Lagerbestand
                lager_kontext = ""
                if st.session_state.lager:
                    lager_kontext = "\n\nMein aktueller Lagerbestand:\n"
                    for it in st.session_state.lager[-10:]:
                        lager_kontext += f"- {it['artikel']}: EK€{it['ek']} → VK€{it['vk']} ({it['zustand']}) {it['tage']} Tage\n"

                # 2. Lern-System
                lern_kontext = ""
                if st.session_state.mein_wissen:
                    lern_kontext += "\nMein persönliches Wissen:\n"
                    lern_kontext += "\n".join([f"- {w}" for w in st.session_state.mein_wissen[-5:]])
                if st.session_state.preis_korrekturen:
                    lern_kontext += "\nEchte Verkaufspreise die ich erzielt habe:\n"
                    lern_kontext += "\n".join([f"- {k}: €{v}" for k,v in list(st.session_state.preis_korrekturen.items())[-5:]])

                # 3. Gesprächsverlauf (letzte 6 Nachrichten)
                verlauf = ""
                if len(st.session_state.chat_history) > 1:
                    verlauf = "\nBisheriger Gesprächsverlauf:\n"
                    for m in st.session_state.chat_history[-6:]:
                        rolle = "Ich" if m["role"] == "user" else "KI"
                        verlauf += f"{rolle}: {m['content'][:100]}\n"

                # 4. Web-Suche
                web = tavily_suche(prompt_chat + " " + datetime.now().strftime("%B %Y"))
                web_kontext = ""
                if web and len(web) > 50:
                    # Prüfe ob Web-Ergebnis relevant
                    frage_wort = prompt_chat.split()[0].lower() if prompt_chat else ""
                    if any(w in web.lower() for w in prompt_chat.lower().split()[:3]):
                        web_kontext = "\nAktuelle Web-Infos: " + web[:300]

                # 5. Foto verarbeiten
                chat_bilder = None
                if chat_foto:
                    chat_foto.seek(0)
                    b64 = base64.b64encode(chat_foto.read()).decode()
                    chat_bilder = [b64]

                # ── PROMPT ZUSAMMENBAUEN ──
                system = (
                    "Du bist ein persönlicher Reselling-Experte und Assistent für einen Berliner "
                    "Flohmarkt-Händler. Du kennst Kleinanzeigen, Vinted, Facebook, eBay und alle "
                    "Berliner Flohmärkte perfekt. Antworte immer auf Deutsch, konkret und hilfreich."
                )
                prompt_final = (
                    system + lager_kontext + lern_kontext + web_kontext + verlauf +
                    "\n\nAktuelle Frage: " + prompt_chat
                )

                antwort = ensemble_ki(prompt_final, bilder=chat_bilder)
                st.markdown(antwort)

        st.session_state.chat_history.append({"role":"assistant","content":antwort})

    # ── BUTTONS ──
    c1,c2 = st.columns(2)
    with c1:
        if st.button("🗑️ Chat löschen", use_container_width=True, key="chat_clear"):
            st.session_state.chat_history = []
            st.rerun()
    with c2:
        if st.button("💡 Tipp anfordern", use_container_width=True, key="chat_tipp"):
            with st.spinner("💡 ..."):
                tipp = ensemble_ki(
                    "Du bist Reselling-Experte. Gib einen konkreten Tipp für heute "
                    f"({datetime.now().strftime('%A, %d.%m.%Y')}) — was sollte ich kaufen/verkaufen? "
                    "Basierend auf Saison und aktuellen Trends. Kurz und konkret. Deutsch."
                )
                st.session_state.chat_history.append({"role":"assistant","content":"💡 Tipp des Tages: " + tipp})
                st.rerun()

# ════════════════════════════════════════════════════════════
# TAB 14 — KONKURRENZ
# ════════════════════════════════════════════════════════════
with T[13]:
    st.header("🔎 Konkurrenz-Checker")
    kk_url=st.text_input("🔗 Konkurrenz-Link:",key="kk_url")
    kk_art=st.text_input("Ihr Artikel:",key="kk_art"); kk_preis=st.number_input("Ihr Preis €:",min_value=0.0,value=80.0,key="kk_preis")
    if st.button("🔎 Analysieren",type="primary",use_container_width=True,key="kk_btn"):
        if kk_url:
            with st.spinner("3 KIs + Web analysieren..."):
                seite=lies_url(kk_url)
                web=multi_suche(kk_art+" Preis Deutschland Secondhand") if kk_art else None
                p=(f"Konkurrenz-Analyse. Mein Artikel: {kk_art} | Mein Preis: €{kk_preis}\n"
                   f"Konkurrenz-Seite:\n{seite[:1500]}\n"
                   f"{('Web-Marktpreise:\n'+web[:300]) if web else ''}\n"
                   f"Analyse: Konkurrenz-Preis, Stärken/Schwächen, Wie besser sein, Mein optimaler Preis, Fazit. Deutsch.")
                st.markdown(ensemble_ki(p))

# ════════════════════════════════════════════════════════════
# TAB 15 — BUSINESS
# ════════════════════════════════════════════════════════════
with T[14]:
    st.header("📊 Business-Coach")
    if st.session_state.gwlog:
        gg=sum(i["g"] for i in st.session_state.gwlog); ge=sum(i["ek"] for i in st.session_state.gwlog)
        c1,c2,c3=st.columns(3)
        c1.metric("Verkäufe",len(st.session_state.gwlog)); c2.metric("Gewinn",f"€{gg:.2f}"); c3.metric("ROI",f"{(gg/ge*100) if ge>0 else 0:.0f}%")
        if st.button("🤖 Analysieren",type="primary",use_container_width=True,key="bc_btn"):
            with st.spinner("3 KIs analysieren Ihr Business..."):
                log="\n".join([f"{e['a']}: EK€{e['ek']} VK€{e['vk']} G€{e['g']} {e['pl']}" for e in st.session_state.gwlog])
                web=google_suche("Reselling Deutschland Tipps "+datetime.now().strftime("%Y"))
                p=(f"Business-Coach Reseller Deutschland.\n{('Market-Tipps: '+web[:200]) if web else ''}\n"
                   f"Verkäufe:\n{log}\nStärken, Schwächen, Top-3 Empfehlungen, Potenzial, Beste Plattform. Deutsch.")
                st.markdown(ensemble_ki(p))
    else: st.info("💡 Erst Verkäufe eintragen!")

# ════════════════════════════════════════════════════════════
# TAB 16 — LAGER-KI
# ════════════════════════════════════════════════════════════
with T[15]:
    st.header("📦 Lager-Optimierer")
    if st.session_state.lager:
        if st.button("🤖 Lager analysieren",type="primary",use_container_width=True,key="lo_btn"):
            with st.spinner("3 KIs + Web prüft Marktpreise..."):
                lt="\n".join([f"{it['artikel']}: EK€{it['ek']} VK€{it['vk']} {it['tage']}T {it['plattform']}" for it in st.session_state.lager])
                # Web sucht aktuelle Preise für alle Artikel
                artikel_namen=" ".join([it["artikel"] for it in st.session_state.lager[:3]])
                web_lag=multi_suche(artikel_namen+" Preis Kleinanzeigen eBay "+datetime.now().strftime("%Y"))
                web_k=f"\n\nAktuelle Web-Marktpreise:\n{web_lag[:400]}" if web_lag else ""
                if web_lag: st.success("✅ Aktuelle Marktpreise geladen!")
                p=(f"Lager-Analyse:\n{lt}{web_k}\n"
                   f"Sofort verkaufen, Diese Woche, Bundle-Tipps, "
                   f"Preis-Anpassungen (Web-Preise beachten!), Note 1-10. Deutsch.")
                st.markdown(ensemble_ki(p))
    else: st.info("💡 Erst Artikel im Lager eintragen!")

# ════════════════════════════════════════════════════════════
# TAB 17 — MARKT-NEWS
# ════════════════════════════════════════════════════════════
with T[16]:
    st.header("📰 Markt-News")
    mn_kat=st.selectbox("Kategorie:",["Alles","Kleidung","Elektronik","Porzellan","Spielzeug","Möbel","Bücher"],key="mn_kat")
    if st.button("📰 Live-Analyse",type="primary",use_container_width=True,key="mn_btn"):
        with st.spinner("Web + 3 KIs..."):
            web=multi_suche(mn_kat+" Secondhand Markt Trend "+datetime.now().strftime("%B %Y")+" Deutschland")
            if web: st.success("✅ Echte Web-Daten!")
            p=(f"Markt-Analyst {datetime.now().strftime('%B %Y')}. {('Web:\n'+web[:400]) if web else ''}\n"
               f"Report {mn_kat}: TOP-5 gesucht+Preise, Steigen, Fallen, Geheimtipp, Saisontipp. Deutsch.")
            st.markdown(ensemble_ki(p))

# ════════════════════════════════════════════════════════════
# TAB 18 — PROFI-TEXT
# ════════════════════════════════════════════════════════════
with T[17]:
    st.header("✍️ Profi-Text Generator")
    pt_fotos=st.file_uploader("📷 Fotos",type=["jpg","jpeg","png"],accept_multiple_files=True,key="pt_fotos")
    if pt_fotos:
        cols=st.columns(min(len(pt_fotos),4))
        for i,f in enumerate(pt_fotos): cols[i%4].image(f,caption=f"Foto {i+1}",use_column_width=True)
    c1,c2=st.columns(2)
    with c1:
        pt_art=st.text_input("Artikel:",key="pt_art"); pt_zust=st.selectbox("Zustand:",["Wie neu","Sehr gut","Gut","Gebraucht"],key="pt_zust")
        pt_preis=st.number_input("Preis €:",min_value=0.0,value=120.0,key="pt_preis")
    with c2: pt_det=st.text_area("Details:",height=100,key="pt_details")
    if st.button("✍️ Texte erstellen",type="primary",use_container_width=True,key="pt_btn"):
        if pt_art or pt_fotos:
            with st.spinner("3 KIs schreiben..."):
                pt_b=[base64.b64encode(f.read()).decode() for f in pt_fotos] if pt_fotos else None
                web=google_suche(f"{pt_art} Kleinanzeigen eBay Preis")
                p=(f"Profi-Verkaufstexte alle Plattformen. Artikel: {pt_art} | {pt_zust} | €{pt_preis}\n"
                   f"Details: {pt_det}\n{('Web: '+web[:150]) if web else ''}\n"
                   f"Kleinanzeigen-Titel+Text, Vinted, Facebook, eBay, Keywords. Deutsch.")
                st.markdown(ensemble_ki(p,bilder=pt_b))

# ── FOOTER ────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<p style='text-align:center;color:#888;font-size:12px'>"
    f"⚡ MarktRadar OS PRO v8.0 ULTIMATE · 9 Vision-KIs · Ensemble · Google+Tavily+You.com · "
    f"Zoran Berlin · {datetime.now().strftime('%d.%m.%Y')}</p>",
    unsafe_allow_html=True
)
