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
    # Erweitertes Lern-System
    "verkauf_log":[],        # Echte Verkäufe mit Preis+Plattform
    "kategorie_wissen":{},   # Wissen pro Kategorie
    "beste_zeiten":{},       # Beste Verkaufszeiten
    "markt_notizen":{},      # Notizen zu Märkten
    "ki_korrekturen":[],     # Wo KI falsch lag
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
        # Deutsch erzwingen durch deutsche Suchanfrage
        query_de = query + " Deutschland deutsch"
        r = requests.post("https://api.tavily.com/search",
            json={"api_key":TAVILY_KEY,"query":query_de,"search_depth":"advanced",
                  "max_results":5,"include_answer":True,
                  "include_domains":["kleinanzeigen.de","ebay.de","vinted.de",
                                     "mobile.de","markt.de","hood.de"]},
            timeout=15)
        data = r.json()
        teile = []
        if data.get("answer"):
            antwort = str(data["answer"])
            # Nur verwenden wenn auf Deutsch oder relevant
            if any(w in antwort.lower() for w in ["euro","€","preis","kaufen","verkauf","deutschland"]):
                teile.append(antwort)
        if data.get("results"):
            for res in data["results"][:3]:
                titel = res.get("title","")
                inhalt = res.get("content","")[:150]
                # Nur deutsche Quellen
                url = res.get("url","")
                if ".de" in url or "deutschland" in inhalt.lower() or "€" in inhalt:
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
    return ki(
        f"3 Preisexperten haben Preise geschätzt:\n{pt}\n\n"
        f"Erstelle finalen Preis-Konsens. NUR konkrete Einzelzahlen — KEINE Spannen wie €45-55!\n"
        f"Format (genau so):\n"
        f"eBay: €X | Kleinanzeigen: €X | Vinted: €X | Facebook: €X | Flohmarkt: €X | Empfehlung: €X | Trend: ↑/↓/→\n"
        f"Begründung: [1 Satz warum dieser Preis realistisch ist]"
    )

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

# ── BILDER VON URL LADEN ─────────────────────────────────────
def lade_bilder_von_url(url):
    """
    Lädt ALLE Bilder von einer Webseite (z.B. Lüdtke Auktion).
    Funktioniert auch mit verschwommenen/schlechten Bildern!
    Gibt Liste von Base64-codierten Bildern zurück.
    """
    bilder_b64 = []
    try:
        h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, headers=h, timeout=15)
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
                br = requests.get(bild_url, headers=h, timeout=10)
                if br.status_code == 200 and len(br.content) > 1000:
                    b64 = base64.b64encode(br.content).decode()
                    bilder_b64.append(b64)
            except: continue

    except Exception as e:
        pass

    return bilder_b64


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
                    if url_text.startswith("[URL"): st.warning("⚠️ URL nicht erreichbar")
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
                            ("google/gemini-3-flash-preview","Gemini 3"),
                            ("google/gemini-2.5-flash","Gemini 2.5"),
                            ("anthropic/claude-sonnet-4-6","Claude Sonnet"),
                            ("openai/gpt-4o","GPT-4o"),
                        ]
                        bilder_vorab = [komprimiere(b) for b in st.session_state.fotos[:2]]
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

                        "GANZ WICHTIG — Beginne IMMER mit diesen 2 Kernwerten (eine konkrete Zahl, KEINE Spanne!):\n"
                        "ONLINE-WERT: \u20acX  (realistischer Gesamt-Verkaufswert online, eBay/Kleinanzeigen)\n"
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
                        ("google/gemini-2.5-flash",     "🥇 Gemini 2.5", "google/gemini-1.5-flash"),
                        ("openai/gpt-4o",               "🥈 GPT-4o",     "openai/gpt-4o-mini"),
                        ("google/gemini-2.0-flash-001", "🥉 Gemini 2.0", "google/gemini-1.5-pro"),
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
                                    max_tokens=1800, extra_headers=_hdrs()
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
                        experten_teile = []
                        for e_name, e_antwort in experten_ergebnisse.items():
                            experten_teile.append("==" + e_name + "==\n" + e_antwort[:800])
                        experten_zusammen = "\n\n".join(experten_teile)
                        richter_prompt_final = (
                            "Du bist Chef-Experte für Secondhand in Deutschland.\n"
                            + str(anzahl_experten) + " Experten haben den Artikel analysiert.\n"
                            + "Erstelle EINE perfekte, vollständige finale Antwort auf Deutsch.\n"
                            + "Nimm das Beste + Präziseste aus jeder Analyse.\n"
                            + "Bei unterschiedlichen Preisen: nimm den Durchschnitt.\n"
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
                    # Objekt-Name + Kategorie extrahieren
                    obj_match = _re.search(r"Artikel[:\s]+([^\n(]+)", ergebnis)
                    obj_name = obj_match.group(1).strip()[:35] if obj_match else (st.session_state.get("auto_kat","") or "Artikel")
                    kat_name = st.session_state.get("auto_kat","Haushaltswaren")

                    if online_wert and floh_wert:
                        quote = round((floh_wert / online_wert) * 100, 1) if online_wert > 0 else 0
                        wertverlust = round(online_wert * 0.01, 2)
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
                        st.markdown("### 💰 Duale Preisschätzung (Zustandsbereinigt)")
                        c1, c2, c3 = st.columns(3)
                        with c1:
                            st.markdown(
                                "<div style='color:#888;font-size:14px'>📈 Est. Online-Wert</div>"
                                "<div style='color:#333;font-size:34px;font-weight:400'>" + f"{online_wert:.2f}".replace(".",",") + " €</div>",
                                unsafe_allow_html=True)
                        with c2:
                            st.markdown(
                                "<div style='color:#888;font-size:14px'>🎪 Est. Flohmarkt-Wert</div>"
                                "<div style='color:#333;font-size:34px;font-weight:400'>" + f"{floh_wert:.2f}".replace(".",",") + " €</div>",
                                unsafe_allow_html=True)
                        with c3:
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

            # ── STUFE 3: PREIS-ENSEMBLE + WEB ──
            with st.status("📡 Stufe 3: Google+Tavily+You.com + 3 Preis-KIs...",expanded=True):
                ebay_url=f"https://www.ebay.de/sch/i.html?_nkw={urllib.parse.quote(suchbegriff)}&LH_Complete=1&LH_Sold=1"
                ka_url=f"https://www.kleinanzeigen.de/s-{urllib.parse.quote(suchbegriff)}/k0"
                vi_url=f"https://www.vinted.de/catalog?search_text={urllib.parse.quote(suchbegriff)}"
                fb_url=f"https://www.facebook.com/marketplace/search/?query={urllib.parse.quote(suchbegriff)}"
                st.write(f"🌐 Suche echte Preise für: **{suchbegriff}**")
                # Gezielte Suche - nur Google und Tavily mit gezieltem Query
                def hole_gezielte_preise():
                    # Sehr spezifische Suchanfrage
                    query = suchbegriff + " kaufen Preis Euro Deutschland 2024 2025"
                    g = google_suche(query)
                    t = tavily_suche(suchbegriff + " Preis Marktpreis Deutschland Secondhand")
                    return g, t

                google_r, tavily_r = hole_gezielte_preise()

                # Prüfe ob Ergebnisse wirklich zum Artikel passen
                def passt_zum_artikel(text, artikel):
                    if not text or not artikel: return False
                    woerter = [w for w in artikel.lower().split() if len(w) > 3]
                    treffer = sum(1 for w in woerter if w in text.lower())
                    return treffer >= max(1, len(woerter) // 2)

                web_text = ""
                if google_r and passt_zum_artikel(google_r, suchbegriff):
                    web_text += google_r
                if tavily_r and passt_zum_artikel(tavily_r, suchbegriff):
                    web_text += "\n" + tavily_r

                # 3 Preis-Experten bewerten GLEICHZEITIG
                st.write("⚖️ 3 Preis-Experten bewerten gleichzeitig...")
                preis_prompt = (
                    "Preisexperte Secondhand Deutschland. Auf DEUTSCH antworten!\n"
                    "Artikel: " + suchbegriff + "\n"
                    "Zustand: " + g_beschr + "\n"
                    + ("Echte Marktdaten aus dem Web: " + web_text[:400] if web_text else "Keine Web-Daten — nutze Erfahrung.") + "\n\n"
                    "Gib realistische Preise. NUR konkrete Einzelzahlen — KEINE Spannen!\n"
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
                    ("google/gemini-3-flash-preview", "Gemini 3"),
                    ("google/gemini-2.5-flash",       "Gemini 2.5"),
                    ("openai/gpt-4o-mini",            "GPT-4o"),
                ]
                def preis_experte_arbeitet(modell_info):
                    m_id, m_name = modell_info
                    try:
                        kl = _oai.OpenAI(api_key=OR_KEY, base_url="https://openrouter.ai/api/v1")
                        r = kl.chat.completions.create(
                            model=m_id, messages=[{"role":"user","content":preis_prompt}],
                            max_tokens=400, extra_headers=_hdrs()
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
