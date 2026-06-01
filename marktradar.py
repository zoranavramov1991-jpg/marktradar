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
import os, base64, urllib.parse, concurrent.futures
from datetime import datetime
import requests
from openai import OpenAI
import openai as _oai

st.set_page_config(page_title="⚡ MarktRadar OS PRO", page_icon="⚡",
    layout="wide", initial_sidebar_state="collapsed")

# ── CSS ───────────────────────────────────────────────────────
st.markdown("""<style>
.stApp{background:linear-gradient(135deg,#f0f4ff 0%,#faf5ff 50%,#f0f9ff 100%)}
.stTabs [data-baseweb="tab-list"]{gap:6px;background:rgba(255,255,255,0.7);border-radius:16px;padding:8px;flex-wrap:wrap;box-shadow:0 2px 8px rgba(0,0,0,0.08);backdrop-filter:blur(10px)}
.stTabs [data-baseweb="tab"]{background:transparent;border-radius:10px;color:#666;font-size:13px;font-weight:600;padding:7px 14px;border:none;transition:all 0.25s}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#6c47ff,#9b6dff)!important;color:#fff!important;font-weight:700!important;box-shadow:0 4px 15px rgba(108,71,255,0.4)!important;transform:translateY(-1px) scale(1.02)!important}
.stTabs [data-baseweb="tab-panel"]{background:rgba(255,255,255,0.6);border-radius:16px;padding:1.5rem;border:0.5px solid rgba(255,255,255,0.9);margin-top:10px;box-shadow:0 8px 32px rgba(31,38,135,0.1);backdrop-filter:blur(12px)}
.stButton>button{background:linear-gradient(135deg,#f5a623,#f7c948,#e8850a)!important;color:#fff!important;font-weight:700!important;border:none!important;border-radius:12px!important;padding:0.65rem 1.5rem!important;box-shadow:0 6px 20px rgba(245,166,35,0.35),inset 0 1px 0 rgba(255,255,255,0.3)!important;transition:all 0.2s!important}
.stButton>button:hover{transform:perspective(500px) translateZ(6px) translateY(-2px)!important;box-shadow:0 10px 28px rgba(245,166,35,0.45)!important}
[data-testid="metric-container"]{background:rgba(255,255,255,0.8)!important;border-radius:16px!important;padding:1.2rem!important;box-shadow:0 8px 24px rgba(31,38,135,0.08)!important}
[data-testid="metric-container"] [data-testid="stMetricValue"]{color:#6c47ff!important;font-size:24px!important;font-weight:800!important}
.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stNumberInput>div>div>input{background:rgba(255,255,255,0.9)!important;border:1.5px solid rgba(108,71,255,0.15)!important;border-radius:12px!important}
.stSelectbox>div>div{background:rgba(255,255,255,0.9)!important;border:1.5px solid rgba(108,71,255,0.15)!important;border-radius:12px!important}
[data-testid="stFileUploader"]{background:rgba(255,255,255,0.7)!important;border:2px dashed rgba(108,71,255,0.3)!important;border-radius:16px!important}
.stSlider [data-baseweb="thumb"]{background:linear-gradient(135deg,#6c47ff,#9b6dff)!important;border:2px solid white!important}
.stSlider [data-baseweb="track"]>div:first-child{background:linear-gradient(90deg,#6c47ff,#f5a623)!important}
.stRadio label{background:rgba(255,255,255,0.8)!important;border:1px solid rgba(108,71,255,0.15)!important;border-radius:10px!important;padding:6px 14px!important;cursor:pointer!important;transition:all 0.2s!important}
.stRadio label:has(input:checked){background:linear-gradient(135deg,rgba(108,71,255,0.1),rgba(155,109,255,0.1))!important;border-color:#6c47ff!important;color:#6c47ff!important}
.stAlert{border-radius:12px!important;border:none!important}
::-webkit-scrollbar{width:5px}::-webkit-scrollbar-thumb{background:linear-gradient(#6c47ff,#f5a623);border-radius:10px}
@media(max-width:768px){.stTabs [data-baseweb="tab"]{font-size:11px!important;padding:5px 8px!important}}
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
for k,v in {
    "lager":[],"sim":[],"gwlog":[],"fotos":[],"fcnt":0,
    "feedback_log":[],"analyse_history":[],"mein_wissen":[],
    "preis_korrekturen":{},"chat_history":[],"vorabinfo":"",
}.items():
    if k not in st.session_state: st.session_state[k]=v

# ══════════════════════════════════════════════════════════════
# KI ENGINE — ULTIMATE
# ══════════════════════════════════════════════════════════════

# Vision-Fallback-Kette (9 Modelle)
VISION_KETTE = [
    "google/gemini-3-flash-preview",
    "google/gemini-2.5-flash",
    "google/gemini-2.5-flash-lite",
    "anthropic/claude-sonnet-4-6",
    "google/gemini-1.5-flash",
    "google/gemini-1.5-pro",
    "qwen/qwen-vl-plus",
    "meta-llama/llama-3.2-11b-vision-instruct:free",
    "openai/gpt-4o",
]

# Ensemble-Modelle (3 beste gleichzeitig)
ENSEMBLE_VISION = [
    ("google/gemini-3-flash-preview", "🥇 Gemini 3 Flash"),
    ("google/gemini-2.5-flash",       "🥈 Gemini 2.5 Flash"),
    ("anthropic/claude-sonnet-4-6",   "🥉 Claude Sonnet"),
]
ENSEMBLE_TEXT = [
    ("google/gemini-3-flash-preview", "🥇 Gemini 3"),
    ("google/gemini-2.5-flash",       "🥈 Gemini 2.5"),
    ("openai/gpt-4o-mini",            "🥉 GPT-4o-mini"),
]

def _client():
    return OpenAI(api_key=OR_KEY, base_url="https://openrouter.ai/api/v1")

def _hdrs():
    return {"HTTP-Referer":"https://marktradar.streamlit.app","X-Title":"MarktRadar"}

def komprimiere(b64):
    try:
        from PIL import Image
        import io as _io
        img = Image.open(_io.BytesIO(base64.b64decode(b64)))
        if img.mode != "RGB": img = img.convert("RGB")
        img.thumbnail((1024,1024), Image.Resampling.LANCZOS)
        buf = _io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        return base64.b64encode(buf.getvalue()).decode()
    except: return b64

def ki(prompt, bilder=None):
    """Einzelne KI mit Fallback-Kette"""
    if not OR_KEY: return "❌ Kein API-Key!"
    c = _client()
    verweigerungen = ["tut mir leid","kann nicht helfen","cannot assist","i'm sorry"]
    try:
        if bilder:
            bilder_k = [komprimiere(b) for b in bilder[:4]]
            for model in VISION_KETTE:
                try:
                    inhalt = [{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b}"}} for b in bilder_k]
                    inhalt.append({"type":"text","text":prompt})
                    r = c.chat.completions.create(model=model,
                        messages=[{"role":"user","content":inhalt}],
                        max_tokens=2500, extra_headers=_hdrs())
                    a = r.choices[0].message.content
                    if a and ("€" in a or "eur" in a.lower() or len(a)>200) and not any(v in a.lower() for v in verweigerungen):
                        return a
                except: continue
            return "❌ Alle Vision-Modelle nicht verfügbar"
        else:
            r = c.chat.completions.create(model="openai/gpt-4o-mini",
                messages=[{"role":"user","content":prompt}],
                max_tokens=2500, extra_headers=_hdrs())
            return r.choices[0].message.content
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
                max_tokens=max_tokens, extra_headers=_hdrs())
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
def google_suche(query):
    if not GOOGLE_KEY or not GOOGLE_CSE: return None
    try:
        r = requests.get("https://www.googleapis.com/customsearch/v1",
            params={"key":GOOGLE_KEY,"cx":GOOGLE_CSE,"q":query,"num":5,"hl":"de","gl":"de"},
            timeout=10)
        data = r.json()
        if data.get("items"):
            teile = ["🔍 GOOGLE:"]
            for item in data["items"][:4]:
                teile.append("• " + item.get("title","") + ": " + item.get("snippet","")[:150])
            return "\n".join(teile)
    except: pass
    return None

def tavily_suche(query):
    if not TAVILY_KEY: return None
    try:
        r = requests.post("https://api.tavily.com/search",
            json={"api_key":TAVILY_KEY,"query":query,"search_depth":"advanced",
                  "max_results":5,"include_answer":True},
            timeout=15)
        data = r.json()
        teile = []
        if data.get("answer"): teile.append("📊 " + str(data["answer"]))
        if data.get("results"):
            teile.append("🔗 QUELLEN:")
            for res in data["results"][:3]:
                teile.append("• " + res.get("title","") + ": " + res.get("content","")[:150])
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
    return "\n\n".join([f"=={k}==\n{v}" for k,v in ergebnisse.items()])

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
        ("google/gemini-3-flash-preview", "G3"),
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
    return ki(f"3 Preisexperten:\n{pt}\nErstelle Preis-Konsens (eine Zeile): eBay €X | KA €X | FM €X | Best: €X | Trend: ↑/↓/→")

# ── URL LESEN ─────────────────────────────────────────────────
def lies_url(url):
    try:
        h = {"User-Agent":"Mozilla/5.0","Accept-Language":"de-DE,de;q=0.9"}
        r = requests.get(url, headers=h, timeout=15)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup(["script","style","nav","footer","header"]): t.decompose()
        zeilen = [z.strip() for z in soup.get_text("\n").split("\n") if len(z.strip())>15]
        return "\n".join(zeilen[:150])[:5000]
    except Exception as e: return f"[URL-Fehler: {e}]"

# ── HEADER ────────────────────────────────────────────────────
st.markdown("""
<div style='background:rgba(255,255,255,0.7);padding:24px;border-radius:20px;
margin-bottom:20px;text-align:center;border:0.5px solid rgba(255,255,255,0.95);
box-shadow:0 20px 60px rgba(108,71,255,0.12);backdrop-filter:blur(20px);position:relative;overflow:hidden'>
<div style="position:absolute;top:0;left:0;right:0;height:3px;
background:linear-gradient(90deg,#6c47ff,#f5a623,#6c47ff);border-radius:20px 20px 0 0"></div>
<div style='font-size:3em;margin-bottom:8px'>⚡</div>
<h1 style='background:linear-gradient(135deg,#6c47ff,#f5a623);
-webkit-background-clip:text;-webkit-text-fill-color:transparent;
background-clip:text;margin:0;font-size:2em;font-weight:900'>MarktRadar OS PRO</h1>
<p style='color:#888;margin:10px 0 0;font-size:12px;letter-spacing:2px;font-weight:600'>
KLEINANZEIGEN &nbsp;·&nbsp; VINTED &nbsp;·&nbsp; FACEBOOK &nbsp;·&nbsp; EBAY &nbsp;·&nbsp; FLOHMÄRKTE
</p></div>""", unsafe_allow_html=True)

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
                    neu_foto.seek(0)
                    b64 = base64.b64encode(neu_foto.read()).decode()
                    if b64 not in st.session_state.fotos:
                        st.session_state.fotos.append(b64)
                    st.session_state.fcnt += 1
                    st.rerun()
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

            # ── STUFE 1: Daten + Vorab-KI ──
            with st.status("📡 Stufe 1: Daten sammeln + KI-Vorab-Scan...",expanded=True):
                if hat_url:
                    url_text = lies_url(url_inp)
                    if url_text.startswith("[URL"): st.warning("⚠️ URL nicht erreichbar")
                    else:
                        st.success(f"✅ {len(url_text)} Zeichen ausgelesen")
                        url_ki = ki("Secondhand-Experte. Extrahiere: Artikel, Preis, Zustand. Kurz Deutsch:\n"+url_text[:2000])
                        st.info("📄 "+url_ki)
                        # Google sucht zusätzlich
                        artikel_name = url_ki.split("\n")[0][:40]
                        g = google_suche(artikel_name+" Wert Preis")
                        if g: url_text += "\nGOOGLE:\n"+g[:300]

                if hat_fotos:
                    st.success(f"✅ {len(st.session_state.fotos)} Foto(s) bereit")
                    st.write("🔭 4 Vision-KIs scannen gleichzeitig vor...")
                    scan_modelle = [
                        ("google/gemini-3-flash-preview","Gemini 3"),
                        ("google/gemini-2.5-flash","Gemini 2.5"),
                        ("anthropic/claude-sonnet-4-6","Claude Sonnet"),
                        ("openai/gpt-4o","GPT-4o"),
                    ]
                    def vorab_scan(info):
                        mid, name = info
                        try:
                            c2 = _oai.OpenAI(api_key=OR_KEY,base_url="https://openrouter.ai/api/v1")
                            bk = [komprimiere(b) for b in st.session_state.fotos[:2]]
                            inhalt=[{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b}"}} for b in bk]
                            inhalt.append({"type":"text","text":"Was siehst du? Beschreibe kurz Artikel, Marke, Besonderheiten. Deutsch."})
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

            # ── STUFE 2: ENSEMBLE HAUPT-ANALYSE ──
            with st.status("🔬 Stufe 2: 3 Experten-KIs analysieren gleichzeitig...",expanded=True):
                vorab_k=("\n\nVORAB:\n"+st.session_state.vorabinfo) if st.session_state.vorabinfo else ""
                lern=""
                if st.session_state.mein_wissen:
                    lern+="\n\nMein Wissen:\n"+"\n".join([f"- {w}" for w in st.session_state.mein_wissen[-5:]])
                if st.session_state.preis_korrekturen:
                    lern+="\n\nEchte Preise:\n"+"\n".join([f"- {k}: €{v}" for k,v in list(st.session_state.preis_korrekturen.items())[-5:]])
                extra=""
                if beschr.strip(): extra+=f" Händler: {beschr}."
                if url_text and not url_text.startswith("[URL"): extra+=f"\n\nWebseite:\n{url_text[:1500]}"

                prompt=(
                    f"Ich bin Händler (Kleinanzeigen,Vinted,Facebook,eBay,Flohmärkte).\n"
                    f"Gebrauchsspuren: {g_beschr}\nDefekt: {d_beschr}{extra}{vorab_k}{lern}\n\n"
                    f"Analysiere JEDEN Artikel im Bild. Auf Deutsch. Sei Profi-Experte!\n\n"
                    f"**Artikel: [Name]**\n"
                    f"- Was genau? [Marke, Material, Modell]\n"
                    f"- Alter: [Jahr/Epoche/Land/Antik?]\n"
                    f"- Zustand: [Erkannt + Mängel + Defektgrad%]\n"
                    f"- Verkäuflichkeit: 🟢schnell / 🟡mittel / 🔴langsam\n\n"
                    f"PREISE (NUR eine Zahl!):\nJetzt:\neBay: €X | KA: €X | Vinted: €X | FB: €X | FM: €X | Ankauf: €X\n"
                    f"Nach Aufbereitung: eBay: €X | KA: €X | FM: €X | Mehrwert: +€X (+X%)\n\n"
                    f"🏆 BESTE PLATTFORM: [Plattform + warum + €X]\n"
                    f"🎯 KONFIDENZ: X% | ⚠️ FÄLSCHUNG: [Niedrig/Mittel/Hoch]\n"
                    f"✨ AUFBEREITUNG: [Methode + +€X]\n"
                    f"👥 ZIELGRUPPE: [Wer + wo]\n"
                    f"📅 TIMING: [Beste Monate + Jetzt: Ja/Nein]\n"
                    f"📝 ANZEIGE: Titel:[60Z] | Text:[3S] | Preis:€X\n"
                    f"🗺️ BERLIN: 🥇[Markt+Tag+€X] 🥈[Markt+€X]\n"
                    f"🌟 RARITÄT: [Seltenheit + Höchstpreis]\n"
                    f"💰 GEWINN: EK€X → VK€X → Gewinn€X → ROI X%\n"
                    f"---\nGESAMT: €X | Wertvollster: [Name]"
                )

                st.write("🚀 Starte 3 Experten gleichzeitig...")
                modelle_e=[
                    ("google/gemini-3-flash-preview","🥇 Gemini 3 Flash"),
                    ("google/gemini-2.5-flash","🥈 Gemini 2.5 Flash"),
                    ("anthropic/claude-sonnet-4-6","🥉 Claude Sonnet"),
                ]
                def experte_analysiert(info):
                    mid,name=info
                    try:
                        c2=_oai.OpenAI(api_key=OR_KEY,base_url="https://openrouter.ai/api/v1")
                        if hat_fotos:
                            bk=[komprimiere(b) for b in st.session_state.fotos[:3]]
                            inhalt=[{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b}"}} for b in bk]
                            inhalt.append({"type":"text","text":prompt})
                            msgs=[{"role":"user","content":inhalt}]
                        else:
                            msgs=[{"role":"user","content":prompt}]
                        r=c2.chat.completions.create(model=mid,messages=msgs,max_tokens=1500,extra_headers=_hdrs())
                        a=r.choices[0].message.content
                        if a and len(a)>100: return (name,a)
                    except: pass
                    return (name,None)

                ea={}
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
                    fs={ex.submit(experte_analysiert,m):m for m in modelle_e}
                    for f in concurrent.futures.as_completed(fs):
                        n,a=f.result()
                        if a: ea[n]=a; st.write(f"✅ {n} fertig!")

                if not ea:
                    st.warning("⚠️ Ensemble fehlgeschlagen — Fallback...")
                    ergebnis=ki(prompt,bilder=st.session_state.fotos if hat_fotos else None)
                else:
                    st.write(f"⚖️ Richter-KI fasst {len(ea)} Experten zusammen...")
                    et="\n\n".join([f"=={n}==\n{a[:800]}" for n,a in ea.items()])
                    ergebnis=ki(
                        f"Chef-Experte Secondhand Deutschland.\n"
                        f"{len(ea)} Experten haben analysiert.\n"
                        f"Erstelle EINE perfekte vollständige finale Antwort auf Deutsch.\n"
                        f"Bestes aus jeder Analyse. Bei Preisen: Durchschnitt.\n"
                        f"Experten:\n{et}\n\nFINALE EXPERTEN-ANTWORT:"
                    )

                st.markdown(ergebnis)
                st.session_state["ana_ergebnis"]=ergebnis
                st.session_state.vorabinfo=""
                suchbegriff="Vintage Artikel"
                for line in ergebnis.split("\n"):
                    if "**Artikel:" in line:
                        t=line.split(":")
                        if len(t)>1: suchbegriff=t[1].strip().strip("*[] ")[:40]
                        break

            # ── STUFE 3: PREIS-ENSEMBLE + WEB ──
            with st.status("📡 Stufe 3: Google+Tavily+You.com + 3 Preis-KIs...",expanded=True):
                ebay_url=f"https://www.ebay.de/sch/i.html?_nkw={urllib.parse.quote(suchbegriff)}&LH_Complete=1&LH_Sold=1"
                ka_url=f"https://www.kleinanzeigen.de/s-{urllib.parse.quote(suchbegriff)}/k0"
                vi_url=f"https://www.vinted.de/catalog?search_text={urllib.parse.quote(suchbegriff)}"
                fb_url=f"https://www.facebook.com/marketplace/search/?query={urllib.parse.quote(suchbegriff)}"

                st.write("🌐 Google + Tavily + You.com suchen gleichzeitig...")
                web_daten=multi_suche(suchbegriff+" Preis Deutschland Secondhand")
                if web_daten:
                    st.success("✅ Echte Preisdaten aus dem Web!")
                    st.markdown(web_daten[:400]+"...")
                    st.write("⚖️ 3 Preis-Experten bewerten gleichzeitig...")
                    pk=preis_ensemble(suchbegriff,g_beschr,web_daten)
                    if pk: st.info("💰 **Preis-Konsens:** "+pk)
                else:
                    st.info("ℹ️ Web-Suche nicht verfügbar")

                st.markdown("**🔗 Direkt suchen:**")
                c1,c2=st.columns(2)
                with c1:
                    st.markdown(f"🛒 [eBay →]({ebay_url})")
                    st.markdown(f"📱 [Kleinanzeigen →]({ka_url})")
                with c2:
                    st.markdown(f"👗 [Vinted →]({vi_url})")
                    st.markdown(f"👥 [Facebook →]({fb_url})")

            # ── STUFE 4: ZUSAMMENFASSUNG ──
            with st.status("✅ Stufe 4: Finale Zusammenfassung...",expanded=True):
                ana=st.session_state.get("ana_ergebnis","")
                if len(ana)>200 and "€" in ana:
                    st.info("📊 "+ki(f"Kurze Zusammenfassung 5 Zeilen. Fakten. Deutsch.\n• Artikel:\n• 🟢 Schnell:\n• 🟡 Mittel:\n• 🔴 Langsam:\n• Gesamtwert: €X\n\nAnalyse:\n{ana[:800]}"))
                else:
                    st.warning("⚠️ Keine vollständige Analyse vorhanden.")

            # ── LERN-SYSTEM ──
            st.markdown("---")
            st.markdown("### 🧠 KI verbessern")
            with st.expander("👍 Preis korrigieren"):
                c1,c2,c3=st.columns(3)
                fb_art=c1.text_input("Artikel",key="fb_art")
                fb_echt=c2.number_input("Echter Preis €",min_value=1.0,value=50.0,key="fb_echt")
                fb_pl=c3.selectbox("Plattform",["Kleinanzeigen","eBay","Vinted","Facebook","Flohmarkt"],key="fb_pl")
                if st.button("💾 Speichern",use_container_width=True,key="fb_save"):
                    if fb_art:
                        st.session_state.preis_korrekturen[f"{fb_art} auf {fb_pl}"]=fb_echt
                        st.success("✅ Gespeichert!")
            with st.expander("📝 Eigenes Wissen"):
                fb_k=st.text_input("Ihr Wissen:",key="fb_know")
                if st.button("💾 Hinzufügen",use_container_width=True,key="fb_ks"):
                    if fb_k: st.session_state.mein_wissen.append(fb_k); st.success("✅!")
            total=len(st.session_state.mein_wissen)+len(st.session_state.preis_korrekturen)
            if total>0: st.info(f"🧠 KI kennt **{total}** Infos von Ihnen!")

# ════════════════════════════════════════════════════════════
# TAB 2 — ANSCHREIB
# ════════════════════════════════════════════════════════════
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
            c1,c2,c3,c4=st.columns([3,1,1,1])
            c1.markdown(f"**{it['artikel']}** ({it['zustand']}) — {it['plattform']}")
            c2.markdown(f"€{it['ek']:.0f}"); c3.markdown(f"→ €{it['vk']:.0f}"); c4.markdown(f"**+€{it['gewinn']:.0f}**")
            if it["tage"]>30: st.warning(f"⏰ {it['artikel']}: {it['tage']} Tage!")

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
            web=multi_suche(tr_kat+" Secondhand Markt Trend "+datetime.now().strftime("%B %Y")+" "+tr_region)
            web_k=("\n\nWEB-DATEN:\n"+web) if web else ""
            if web: st.success("✅ Echte Web-Daten!")
            p=(f"Markt-Analyst {tr_region} {datetime.now().strftime('%B %Y')}.{web_k}\n"
               f"Analysiere: {tr_kat}. Deutsch.\n"
               f"TOP 5 Artikel+Preis+Trend | Preise steigen | Preise fallen | Geheimtipp | Jetzt verkaufen | Gold-Suchbegriffe")
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
    st.markdown(f"Live KI-Updates · {datetime.now().strftime('%d.%m.%Y')}")
    tage_de={"Monday":"Montag","Tuesday":"Dienstag","Wednesday":"Mittwoch",
              "Thursday":"Donnerstag","Friday":"Freitag","Saturday":"Samstag","Sunday":"Sonntag"}
    heute_de=tage_de.get(datetime.now().strftime("%A"),"Heute")
    if st.button(f"🔴 Live-Update {heute_de}",type="primary",use_container_width=True,key="floh_live"):
        with st.spinner("🤖 KI + Web..."):
            web=google_suche(f"Flohmarkt Berlin {heute_de} {datetime.now().strftime('%d.%m.%Y')} offen")
            web_k=("\nAktuelle Infos:\n"+web) if web else ""
            st.info(ki(f"Berliner Flohmarkt-Experte. {heute_de} {datetime.now().strftime('%d.%m.%Y')}.{web_k}\nWelche Märkte heute offen? Tipps. Deutsch."))
    st.markdown("---")
    maerkte=[
        ("Mo","Rathaus Steglitz","Schloßstr.37","Mo-Sa 9-18h","+49 30 79706820","🏠 Haushalt","⭐⭐⭐","Alltagsartikel","https://maps.google.com/?q=Rathaus+Steglitz+Berlin"),
        ("Di","Fehrbelliner Platz","Fehrbelliner Pl.","Di&Fr 8-15h","+49 30 28097272","🏺 Antiquitäten","⭐⭐⭐⭐","Top Porzellan&Silber!","https://maps.google.com/?q=Fehrbelliner+Platz+Berlin"),
        ("Mi","Alexanderplatz","Alexanderplatz","Tägl. 10-19h","+49 30 24632425","🏙️ Gemischt","⭐⭐⭐","Täglich offen","https://maps.google.com/?q=Alexanderplatz+Flohmarkt+Berlin"),
        ("Do","Winterfeldtplatz","Winterfeldtpl.","Do&Sa 8-14h","+49 30 7262290","🌿 Vintage","⭐⭐⭐⭐","Do günstiger!","https://maps.google.com/?q=Winterfeldtplatz+Berlin"),
        ("Fr","Fehrbelliner Platz","Fehrbelliner Pl.","Di&Fr 8-15h","+49 30 28097272","🏺 Antiquitäten","⭐⭐⭐⭐⭐","Fr BESTE Auswahl!","https://maps.google.com/?q=Fehrbelliner+Platz+Berlin"),
        ("Fr","Ostbahnhof","Erich-Steinfurth-Str.1","Fr-So 9-16h","+49 30 2936028","🛍️ Gemischt","⭐⭐⭐⭐","Fr wenig Leute!","https://maps.google.com/?q=Flohmarkt+Ostbahnhof+Berlin"),
        ("Sa","RAW Flohmarkt","Revaler Str.99","Sa&So 10-18h","+49 30 29367840","🕶️ Vintage","⭐⭐⭐⭐⭐","BESTE Vintage Berlin!","https://maps.google.com/?q=RAW+Gelände+Berlin"),
        ("Sa","Winterfeldtmarkt","Winterfeldtpl.","Sa 8-14h","+49 30 7262290","🌿 Bio,Vintage","⭐⭐⭐⭐⭐","Einer der besten!","https://maps.google.com/?q=Winterfeldtmarkt+Berlin"),
        ("So","Mauerpark","Bernauer Str.63","So 9-18h","+49 30 40505380","🎭 Vintage","⭐⭐⭐⭐⭐","MUSS! Vor 10 Uhr!","https://maps.google.com/?q=Mauerpark+Flohmarkt+Berlin"),
        ("So","Boxhagener Platz","Boxhagener Pl.","So 10-18h","+49 30 29362596","🏺 Antiquitäten","⭐⭐⭐⭐⭐","Top Porzellan!","https://maps.google.com/?q=Boxhagener+Platz+Flohmarkt+Berlin"),
        ("So","Treptower Park","Treptower Park","So 8-16h","+49 30 5321555","🔧 Elektronik,DDR","⭐⭐⭐⭐","Gut für DDR!","https://maps.google.com/?q=Treptower+Park+Flohmarkt+Berlin"),
        ("So","Arkonaplatz","Arkonaplatz","So 10-16h","+49 30 7861003","🏛️ Raritäten","⭐⭐⭐⭐","Klein aber fein!","https://maps.google.com/?q=Arkonaplatz+Flohmarkt+Berlin"),
    ]
    tage=["Alle","Mo","Di","Mi","Do","Fr","Sa","So"]
    fw=st.radio("📅",tage,horizontal=True,key="fw")
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
                    # Web sucht Marken-Infos
                    marke_name = marken_analyse.split("\n")[0][:40] if marken_analyse else ""
                    if marke_name:
                        web_mk = multi_suche(marke_name+" "+ms_k+" Wert Preis eBay Auktion Deutschland")
                        if web_mk:
                            st.success("✅ Web-Recherche zur Marke:")
                            mk_bewertung = ki(f"Bewerte diese Web-Infos zur Marke '{marke_name}' für Reseller.\n{web_mk[:500]}\nKurzes Fazit: Wert, Seltenheit, Empfehlung. Deutsch.")
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
    st.header("🤖 KI-Reselling-Chat")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    if prompt_chat:=st.chat_input("Fragen Sie alles über Reselling, Preise, Flohmärkte..."):
        st.session_state.chat_history.append({"role":"user","content":prompt_chat})
        with st.chat_message("user"): st.markdown(prompt_chat)
        with st.chat_message("assistant"):
            with st.spinner("🤖 3 KIs denken nach..."):
                web=tavily_suche(prompt_chat+" "+datetime.now().strftime("%B %Y"))
                p=(f"Reselling-Experte Deutschland. Kleinanzeigen,Vinted,Facebook,eBay. Deutsch, konkret.\n"
                   f"{('Aktuelle Web-Infos: '+web[:200]) if web else ''}\nFrage: {prompt_chat}")
                antwort=ensemble_ki(p)
                st.markdown(antwort)
        st.session_state.chat_history.append({"role":"assistant","content":antwort})
    if st.button("🗑️ Löschen",key="chat_clear"): st.session_state.chat_history=[]; st.rerun()

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
            with st.spinner("3 KIs analysieren..."):
                lt="\n".join([f"{it['artikel']}: EK€{it['ek']} VK€{it['vk']} {it['tage']}T {it['plattform']}" for it in st.session_state.lager])
                p=f"Lager-Analyse:\n{lt}\nSofort verkaufen, Diese Woche, Bundle-Tipps, Preis-Anpassungen, Note 1-10. Deutsch."
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
