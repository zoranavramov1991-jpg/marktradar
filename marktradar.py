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
.stApp { background: linear-gradient(135deg, #f0f4ff 0%, #faf5ff 50%, #f0f9ff 100%); }
[data-testid="stVerticalBlock"] > div { transition: transform 0.2s ease; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; background: rgba(255,255,255,0.7); border-radius: 16px; padding: 8px; flex-wrap: wrap; box-shadow: 0 2px 8px rgba(0,0,0,0.08), inset 0 1px 0 rgba(255,255,255,0.9); backdrop-filter: blur(10px); }
.stTabs [data-baseweb="tab"] { background: transparent; border-radius: 10px; color: #666; font-size: 13px; font-weight: 600; padding: 7px 14px; border: none; transition: all 0.25s cubic-bezier(0.34,1.56,0.64,1); }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, #6c47ff 0%, #9b6dff 100%) !important; color: #fff !important; font-weight: 700 !important; box-shadow: 0 4px 15px rgba(108,71,255,0.4) !important; transform: translateY(-1px) scale(1.02) !important; }
.stTabs [data-baseweb="tab"]:hover { background: rgba(108,71,255,0.1); color: #6c47ff; transform: translateY(-1px); }
.stTabs [data-baseweb="tab-panel"] { background: rgba(255,255,255,0.6); border-radius: 16px; padding: 1.5rem; border: 0.5px solid rgba(255,255,255,0.9); margin-top: 10px; box-shadow: 0 8px 32px rgba(31,38,135,0.1), inset 0 1px 0 rgba(255,255,255,0.8); backdrop-filter: blur(12px); }
.stButton > button { background: linear-gradient(135deg, #f5a623 0%, #f7c948 50%, #e8850a 100%) !important; color: #fff !important; font-weight: 700 !important; border: none !important; border-radius: 12px !important; padding: 0.65rem 1.5rem !important; font-size: 14px !important; box-shadow: 0 6px 20px rgba(245,166,35,0.35), inset 0 1px 0 rgba(255,255,255,0.3) !important; transform: perspective(500px) translateZ(0); transition: all 0.2s cubic-bezier(0.34,1.56,0.64,1) !important; }
.stButton > button:hover { transform: perspective(500px) translateZ(6px) translateY(-2px) !important; box-shadow: 0 10px 28px rgba(245,166,35,0.45) !important; }
[data-testid="metric-container"] { background: rgba(255,255,255,0.8) !important; border-radius: 16px !important; padding: 1.2rem !important; box-shadow: 0 8px 24px rgba(31,38,135,0.08) !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #6c47ff !important; font-size: 24px !important; font-weight: 800 !important; }
.stTextInput > div > div > input, .stTextArea > div > div > textarea, .stNumberInput > div > div > input { background: rgba(255,255,255,0.9) !important; border: 1.5px solid rgba(108,71,255,0.15) !important; border-radius: 12px !important; color: #333 !important; }
.stSelectbox > div > div { background: rgba(255,255,255,0.9) !important; border: 1.5px solid rgba(108,71,255,0.15) !important; border-radius: 12px !important; }
[data-testid="stFileUploader"] { background: rgba(255,255,255,0.7) !important; border: 2px dashed rgba(108,71,255,0.3) !important; border-radius: 16px !important; }
.stSlider [data-baseweb="thumb"] { background: linear-gradient(135deg, #6c47ff, #9b6dff) !important; border: 2px solid white !important; }
.stSlider [data-baseweb="track"] > div:first-child { background: linear-gradient(90deg, #6c47ff, #f5a623) !important; }
.stRadio label { background: rgba(255,255,255,0.8) !important; border: 1px solid rgba(108,71,255,0.15) !important; border-radius: 10px !important; padding: 6px 14px !important; cursor: pointer !important; transition: all 0.2s !important; }
.stRadio label:has(input:checked) { background: linear-gradient(135deg, rgba(108,71,255,0.1), rgba(155,109,255,0.1)) !important; border-color: #6c47ff !important; color: #6c47ff !important; }
.stAlert { border-radius: 12px !important; border: none !important; }
::-webkit-scrollbar { width: 5px; } ::-webkit-scrollbar-thumb { background: linear-gradient(#6c47ff, #f5a623); border-radius: 10px; }
@media (max-width: 768px) { .stTabs [data-baseweb="tab"] { font-size: 11px !important; padding: 5px 8px !important; } }
</style>
""", unsafe_allow_html=True)

# ── SECRETS ──────────────────────────────────────────────────
def secret(k):
    try: return st.secrets[k]
    except: return os.environ.get(k,"")

OR_KEY      = secret("OPENROUTER_API_KEY")
TAVILY_KEY  = secret("TAVILY_API_KEY")
YOU_KEY     = secret("YOU_API_KEY")
GOOGLE_KEY  = secret("GOOGLE_API_KEY")
GOOGLE_CSE  = secret("GOOGLE_CSE_ID")

# ── WEB-SUCHE (TAVILY + YOU.COM) ─────────────────────────────
def web_suche(query, max_results=5):
    """Echte Websuche: Tavily zuerst, You.com als Fallback"""
    # 1. TAVILY
    if TAVILY_KEY:
        try:
            r = requests.post(
                "https://api.tavily.com/search",
                json={"api_key": TAVILY_KEY, "query": query,
                      "search_depth": "advanced", "max_results": max_results,
                      "include_answer": True},
                timeout=15
            )
            data = r.json()
            teile = []
            if data.get("answer"):
                teile.append("📊 ZUSAMMENFASSUNG: " + str(data["answer"]))
            if data.get("results"):
                teile.append("🔗 QUELLEN:")
                for res in data["results"][:3]:
                    titel   = str(res.get("title", ""))
                    inhalt  = str(res.get("content", ""))[:200]
                    teile.append("• " + titel + ": " + inhalt)
            if teile:
                return "\n".join(teile)
        except Exception:
            pass
    # 2. YOU.COM Fallback
    if YOU_KEY:
        try:
            r = requests.get(
                "https://api.ydc-index.io/search",
                headers={"X-API-Key": YOU_KEY},
                params={"query": query, "num_web_results": max_results},
                timeout=15
            )
            data = r.json()
            if data.get("hits"):
                teile = ["🔍 SUCHERGEBNISSE:"]
                for hit in data["hits"][:3]:
                    snippets = hit.get("snippets", [])
                    titel    = str(hit.get("title", ""))
                    if snippets:
                        teile.append("• " + titel + ": " + str(snippets[0])[:200])
                if len(teile) > 1:
                    return "\n".join(teile)
        except Exception:
            pass
    return None

def google_suche(query, num=5):
    """Echte Google-Suche über Custom Search API"""
    if not GOOGLE_KEY or not GOOGLE_CSE:
        return None
    try:
        r = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": GOOGLE_KEY,
                "cx":  GOOGLE_CSE,
                "q":   query,
                "num": num,
                "hl":  "de",
                "gl":  "de",
            },
            timeout=10
        )
        data = r.json()
        if data.get("items"):
            teile = ["🔍 GOOGLE-ERGEBNISSE:"]
            for item in data["items"][:4]:
                titel   = str(item.get("title", ""))
                snippet = str(item.get("snippet", ""))[:200]
                link    = str(item.get("link", ""))
                teile.append("• " + titel + "\n  " + snippet + "\n  🔗 " + link)
            return "\n\n".join(teile)
    except Exception:
        pass
    return None


def suche_preise(artikel):
    """Suche aktuelle Marktpreise — Google zuerst, dann Tavily, dann You.com"""
    query = artikel + " Preis kaufen Deutschland Kleinanzeigen eBay Vinted " + datetime.now().strftime("%Y")

    # 1. Google (beste Ergebnisse)
    r = google_suche(query)
    if r: return "📊 GOOGLE: " + r

    # 2. Tavily
    r = web_suche(query)
    if r: return r

    return None

# ── SESSION STATE ─────────────────────────────────────────────
for k,v in {
    "lager":[],"sim":[],"gwlog":[],"fotos":[],"fcnt":0,
    "feedback_log":[],"analyse_history":[],"mein_wissen":[],"preis_korrekturen":{},
    "chat_history":[],"trends_auto":"",
}.items():
    if k not in st.session_state: st.session_state[k]=v

# ── KI ENGINE ─────────────────────────────────────────────────
def komprimiere(b64):
    try:
        from PIL import Image
        import io as _io
        img = Image.open(_io.BytesIO(base64.b64decode(b64)))
        if img.mode not in ("RGB",): img = img.convert("RGB")
        img.thumbnail((1024,1024), Image.Resampling.LANCZOS)
        buf = _io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        return base64.b64encode(buf.getvalue()).decode()
    except: return b64

def ki(prompt, bilder=None):
    if not OR_KEY:
        return "❌ Kein API-Key! Bitte OPENROUTER_API_KEY in Streamlit Secrets eintragen."
    client = OpenAI(api_key=OR_KEY, base_url="https://openrouter.ai/api/v1")
    hdrs = {"HTTP-Referer": "https://marktradar.streamlit.app", "X-Title": "MarktRadar"}
    vision_modelle = [
        "google/gemini-3-flash-preview",              # 🥇 Neuestes & bestes Gemini 2026
        "google/gemini-2.5-flash",                    # 🥈 Mit Thinking-Funktion
        "google/gemini-2.5-flash-lite",               # 🥉 Ultra-schnell & günstig
        "anthropic/claude-sonnet-4-6",                # 💎 Beste für Antiquitäten & Stempel
        "google/gemini-1.5-flash",                    # Bewährt & zuverlässig
        "google/gemini-1.5-pro",                      # Bewährt Pro
        "qwen/qwen-vl-plus",                          # Alibaba Vision
        "meta-llama/llama-3.2-11b-vision-instruct:free",  # Kostenlos!
        "openai/gpt-4o",                              # Letzter Ausweg
    ]
    verweigerungen = ["tut mir leid","kann nicht helfen","cannot assist","can't help","i'm sorry","unable to"]
    try:
        if bilder and len(bilder) > 0:
            bilder_k = [komprimiere(b) for b in bilder[:4]]
            def mache_msgs(bl):
                inhalt = [{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b}"}} for b in bl]
                inhalt.append({"type":"text","text":prompt})
                return [{"role":"user","content":inhalt}]
            for model in vision_modelle:
                try:
                    r = client.chat.completions.create(model=model, messages=mache_msgs(bilder_k), max_tokens=2500, extra_headers=hdrs)
                    antwort = r.choices[0].message.content
                    hat_preise = "eur" in antwort.lower() or "€" in antwort
                    ist_verw = any(v in antwort.lower() for v in verweigerungen)
                    if hat_preise or (not ist_verw and len(antwort) > 200): return antwort
                except Exception as e:
                    continue
            return ki(prompt)
        else:
            r = client.chat.completions.create(model="openai/gpt-4o-mini",
                messages=[{"role":"user","content":prompt}], max_tokens=2500, extra_headers=hdrs)
            return r.choices[0].message.content
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

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
<div style='background:rgba(255,255,255,0.7);padding:24px;border-radius:20px;margin-bottom:20px;text-align:center;
border:0.5px solid rgba(255,255,255,0.95);box-shadow:0 20px 60px rgba(108,71,255,0.12),inset 0 1px 0 rgba(255,255,255,1);backdrop-filter:blur(20px);position:relative;overflow:hidden'>
<div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,#6c47ff,#f5a623,#6c47ff);border-radius:20px 20px 0 0"></div>
<div style='font-size:3em;margin-bottom:8px'>⚡</div>
<h1 style='background:linear-gradient(135deg,#6c47ff,#f5a623);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin:0;font-size:2em;font-weight:900'>MarktRadar OS PRO</h1>
<p style='color:#888;margin:10px 0 0;font-size:12px;letter-spacing:2px;font-weight:600'>KLEINANZEIGEN &nbsp;·&nbsp; VINTED &nbsp;·&nbsp; FACEBOOK &nbsp;·&nbsp; EBAY &nbsp;·&nbsp; FLOHMÄRKTE</p>
</div>""", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────
T = st.tabs([
    "🔍 Analyse","💬 Anschreib-Bot","📦 Lager","📚 OCR Scanner",
    "🔧 Reparatur","📈 Trends","🎭 Verhandlung","📸 Foto-Coach",
    "🗺️ Flohmärkte","🔬 Marken-Scanner","📅 Timing","✨ Anzeigen-KI",
    "🤖 Reselling-Chat","🔎 Konkurrenz","📊 Business-Coach",
    "📦 Lager-KI","📰 Markt-News","✍️ Profi-Text",
])

# ════════════════════════════════════════════════════════════
# TAB 1 — ANALYSE
# ════════════════════════════════════════════════════════════
with T[0]:
    st.header("🔍 Artikel-Analyse")
    st.markdown("Fotos + Links werden **vollständig** analysiert — jeder Artikel einzeln mit Preisen!")

    typ = st.radio("Was analysieren?",["📸 Foto","🔗 Link","📸 + 🔗 Beides"], horizontal=True, key="a_typ")
    url_text = ""
    url_inp  = ""

    if "Foto" in typ:
        st.markdown("##### 📷 Fotos hochladen")
        st.caption("📱 Handy: Ein Foto auswählen → 'Foto hinzufügen' drücken → wiederholen für mehr")

        # Einzelnes Foto hochladen (zuverlässiger auf Handy!)
        neu_foto = st.file_uploader(
            "📷 Foto auswählen",
            type=["jpg","jpeg","png","webp"],
            accept_multiple_files=False,
            key=f"fu_{st.session_state.fcnt}"
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("➕ Foto hinzufügen", type="primary", use_container_width=True, key="foto_add"):
                if neu_foto is not None:
                    neu_foto.seek(0)
                    b64 = base64.b64encode(neu_foto.read()).decode()
                    if b64 not in st.session_state.fotos:
                        st.session_state.fotos.append(b64)
                        st.session_state.fcnt += 1
                        st.rerun()
                else:
                    st.warning("⚠️ Zuerst Foto auswählen!")
        with c2:
            if st.button("🗑️ Alle löschen", use_container_width=True, key="foto_clear"):
                st.session_state.fotos = []
                st.session_state.fcnt += 1
                st.rerun()

        # Gespeicherte Fotos anzeigen
        n = len(st.session_state.fotos)
        if n > 0:
            st.success(f"✅ {n} Foto(s) gespeichert und bereit!")
            cols = st.columns(min(n, 3))
            for i, b64 in enumerate(st.session_state.fotos):
                with cols[i % 3]:
                    st.image(base64.b64decode(b64), caption=f"Foto {i+1}", use_column_width=True)
        else:
            st.info("📷 Noch keine Fotos. Foto auswählen → 'Foto hinzufügen' drücken!")

    if "Link" in typ:
        url_inp = st.text_input("🔗 Link eingeben",
            placeholder="https://luedtke-auktion-online.de/... oder Kleinanzeigen/Vinted-Link", key="a_url")

    st.markdown("---")

    # ── OPTIONEN ──
    col1, col2 = st.columns([2,1])
    with col1:
        beschr = st.text_area("📝 Eigene Beschreibung (optional)",
            placeholder="z.B. 'Kaffeeservice 6-teilig, kleiner Chip am Rand'",
            height=70, key="a_beschr")
    with col2:
        # ── GEBRAUCHSSPUREN SLIDER ──
        st.markdown("**🔍 Gebrauchsspuren**")
        gebrauch = st.slider("", 1, 100, 15, 5, key="a_gebrauch",
            help="1 = Keine Spuren | 50 = Deutlich gebraucht | 100 = Sehr stark")
        if   gebrauch <= 20: st.success(f"🟢 {gebrauch}% — Kaum Spuren")
        elif gebrauch <= 50: st.warning(f"🟡 {gebrauch}% — Gebraucht")
        elif gebrauch <= 80: st.error(f"🔴 {gebrauch}% — Stark gebraucht")
        else:                 st.error(f"⛔ {gebrauch}% — Sehr stark")

        # ── DEFEKT RADIO ──
        st.markdown("**🔧 Defekt vorhanden?**")
        defekt_ja = st.radio("", ["❓ Weiß nicht", "✅ Nein — funktioniert", "❌ Ja — defekt"],
            key="a_defekt_radio")

    hat_fotos  = len(st.session_state.fotos) > 0
    hat_url    = bool(url_inp.strip())
    hat_beschr = bool(beschr.strip())

    if st.button("🚀 VOLLANALYSE STARTEN", type="primary", use_container_width=True, key="a_start"):
        if not (hat_fotos or hat_url or hat_beschr):
            st.warning("⚠️ Bitte Foto hochladen, Link eingeben oder Artikel beschreiben!")
        else:
            # Zustand aufbereiten
            if   gebrauch <= 20: gebrauch_beschr = f"Kaum Gebrauchsspuren ({gebrauch}%)"
            elif gebrauch <= 50: gebrauch_beschr = f"Sichtbare Gebrauchsspuren ({gebrauch}%)"
            elif gebrauch <= 80: gebrauch_beschr = f"Starke Gebrauchsspuren ({gebrauch}%)"
            else:                gebrauch_beschr = f"Sehr starke Gebrauchsspuren ({gebrauch}%)"

            if "Nein"  in defekt_ja: defekt_beschr = "Kein Defekt — funktioniert einwandfrei"
            elif "Ja"  in defekt_ja: defekt_beschr = "DEFEKT — funktioniert nicht!"
            else:                     defekt_beschr = "Defekt unbekannt — bitte prüfen"

            with st.status("📡 Stufe 1: Daten sammeln & KI-Voranalyse...", expanded=True):
                if hat_url:
                    url_text = lies_url(url_inp)
                    if url_text.startswith("[URL"):
                        st.warning("⚠️ URL nicht erreichbar")
                    else:
                        st.success(f"✅ {len(url_text)} Zeichen ausgelesen")
                        # KI + Google analysieren URL-Inhalt
                        st.write("🤖 KI + Google analysieren...")
                        url_analyse = ki(
                            "Du bist Experte für Secondhand und Reselling in Deutschland. "
                            "Lies diesen Webseiten-Inhalt und extrahiere: "
                            "1. Artikel-Name und Beschreibung "
                            "2. Genannte Preise "
                            "3. Zustand "
                            "4. Besonderheiten "
                            "Auf Deutsch, kurz und präzise:\n\n" + url_text[:3000]
                        )
                        # Google sucht zusätzliche Infos zum Artikel
                        artikel_name = url_analyse.split("\n")[0][:50] if url_analyse else ""
                        if artikel_name:
                            google_infos = google_suche(artikel_name + " Wert Preis Deutschland")
                            if google_infos:
                                url_analyse += "\n\nGOOGLE-ZUSATZINFOS:\n" + google_infos[:500]
                        st.info("📄 " + url_analyse)
                        url_text = url_text + "\n\nKI-VORANALYSE DER WEBSEITE:\n" + url_analyse

                if hat_fotos:
                    st.success(f"✅ {len(st.session_state.fotos)} Foto(s) bereit")
                    # Alle Vision-Modelle scannen die Fotos vor
                    st.write("🔭 Alle Vision-KIs scannen Fotos vor...")
                    vorscans = []
                    vision_modelle_scan = [
                        ("google/gemini-3-flash-preview",  "Gemini 3 Flash"),
                        ("google/gemini-2.5-flash",        "Gemini 2.5 Flash"),
                        ("anthropic/claude-sonnet-4-6",    "Claude Sonnet 4.6"),
                        ("openai/gpt-4o",                  "GPT-4o"),
                    ]
                    import openai as _oai
                    _client = _oai.OpenAI(api_key=OR_KEY, base_url="https://openrouter.ai/api/v1")
                    for model_id, model_name in vision_modelle_scan:
                        try:
                            inhalt = []
                            for b64 in st.session_state.fotos[:2]:
                                inhalt.append({"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{komprimiere(b64)}"}})
                            inhalt.append({"type":"text","text":"Was siehst du? Beschreibe kurz alle Artikel, Marken und besondere Merkmale. Auf Deutsch."})
                            r = _client.chat.completions.create(
                                model=model_id,
                                messages=[{"role":"user","content":inhalt}],
                                max_tokens=400,
                                extra_headers={"HTTP-Referer":"https://marktradar.streamlit.app","X-Title":"MarktRadar"}
                            )
                            scan = r.choices[0].message.content
                            if scan and len(scan) > 20:
                                vorscans.append(f"[{model_name}]: {scan}")
                                st.write(f"✅ {model_name} bereit")
                        except Exception:
                            pass
                    if vorscans:
                        vorabinfo = "\n\n".join(vorscans)
                        st.session_state["vorabinfo"] = vorabinfo
                        st.success(f"✅ {len(vorscans)} KI-Modelle haben Fotos vorgelesen!")

            with st.status("🔬 Stufe 2: Experten-Ensemble analysiert...", expanded=True):
                # Vorabinfo aus Stufe 1
                vorabinfo = st.session_state.get("vorabinfo", "")
                vorab_kontext = ("\n\nVORAB-SCAN:\n" + vorabinfo) if vorabinfo else ""

                # Lern-Kontext
                lern = ""
                if st.session_state.mein_wissen:
                    lern += "\n\nMein Wissen:\n" + "\n".join([f"- {w}" for w in st.session_state.mein_wissen[-5:]])
                if st.session_state.preis_korrekturen:
                    lern += "\n\nEchte Preise:\n" + "\n".join([f"- {k}: €{v}" for k,v in list(st.session_state.preis_korrekturen.items())[-5:]])

                extra = ""
                if beschr.strip(): extra += f" Händler: {beschr}."
                if url_text and not url_text.startswith("[URL"): extra += f"\n\nWebseite:\n{url_text[:1500]}"

                # ── ENSEMBLE PROMPT ──────────────────────────────
                ensemble_prompt = (
                    f"Ich bin Händler auf deutschen Flohmärkten (Kleinanzeigen, Vinted, Facebook, eBay).\n"
                    f"Gebrauchsspuren: {gebrauch_beschr}\n"
                    f"Defekt: {defekt_beschr}{extra}{vorab_kontext}{lern}\n\n"
                    f"Analysiere JEDEN sichtbaren Artikel. Auf Deutsch. Sei Experte!\n\n"
                    f"Für JEDEN Artikel:\n"
                    f"**Artikel: [Name]**\n"
                    f"- Was genau? [Marke, Material, Modell]\n"
                    f"- Alter: [Jahr / Epoche / Land / Antik?]\n"
                    f"- Zustand: [Erkannter Zustand + Mängel + Defektgrad %]\n"
                    f"- Verkäuflichkeit: 🟢 schnell / 🟡 mittel / 🔴 langsam\n\n"
                    f"PREISE (nur EINE Zahl pro Plattform!):\n"
                    f"Jetzt ({gebrauch_beschr}):\n"
                    f"eBay: €X | Kleinanzeigen: €X | Vinted: €X | Facebook: €X | Flohmarkt: €X\n"
                    f"Max. Ankauf: €X\n\n"
                    f"Nach Aufbereitung: eBay: €X | Kleinanzeigen: €X | Mehrwert: +€X (+X%)\n\n"
                    f"🏆 BESTE PLATTFORM: [Welche + warum + Preis €X]\n"
                    f"🎯 KONFIDENZ: X%\n"
                    f"⚠️ FÄLSCHUNG: [Niedrig/Mittel/Hoch] | Red Flags: [oder keine]\n"
                    f"✨ AUFBEREITUNG: [Methode] → +€X\n"
                    f"👥 ZIELGRUPPE: [Wer kauft + wo]\n"
                    f"📅 TIMING: [Beste Monate] | Jetzt: [Ja/Nein]\n"
                    f"📝 ANZEIGE: Titel: [60 Zeichen] | Text: [3 Sätze] | Preis: €X\n"
                    f"🗺️ BERLINER MARKT: 🥇[Markt+Tag+Preis] 🥈[Markt]\n"
                    f"🌟 RARITÄT: [Seltenheit + Höchstpreis]\n"
                    f"💰 GEWINN: EK €X → VK €X → Gewinn €X → ROI X%\n"
                    f"---\nGESAMT: €X | Wertvollster: [Name]"
                )

                # ── 3 EXPERTEN GLEICHZEITIG ──────────────────────
                import concurrent.futures
                import openai as _oai

                experten = [
                    ("google/gemini-3-flash-preview",  "🥇 Gemini 3 Flash"),
                    ("google/gemini-2.5-flash",         "🥈 Gemini 2.5 Flash"),
                    ("anthropic/claude-sonnet-4-6",     "🥉 Claude Sonnet 4.6"),
                ]

                def experte_analysiert(model_info):
                    model_id, model_name = model_info
                    try:
                        _client = _oai.OpenAI(
                            api_key=OR_KEY,
                            base_url="https://openrouter.ai/api/v1"
                        )
                        if hat_fotos:
                            bilder_k = [komprimiere(b) for b in st.session_state.fotos[:3]]
                            inhalt = []
                            for b64 in bilder_k:
                                inhalt.append({"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}})
                            inhalt.append({"type":"text","text":ensemble_prompt})
                            msgs = [{"role":"user","content":inhalt}]
                        else:
                            msgs = [{"role":"user","content":ensemble_prompt}]

                        r = _client.chat.completions.create(
                            model=model_id, messages=msgs, max_tokens=1500,
                            extra_headers={"HTTP-Referer":"https://marktradar.streamlit.app","X-Title":"MarktRadar"}
                        )
                        antwort = r.choices[0].message.content
                        if antwort and len(antwort) > 100:
                            return (model_name, antwort)
                    except Exception as e:
                        pass
                    return (model_name, None)

                # Alle 3 gleichzeitig starten!
                st.write("🚀 3 Experten analysieren gleichzeitig...")
                experten_antworten = {}
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    futures = {executor.submit(experte_analysiert, e): e for e in experten}
                    for future in concurrent.futures.as_completed(futures):
                        name, antwort = future.result()
                        if antwort:
                            experten_antworten[name] = antwort
                            st.write(f"✅ {name} fertig!")

                if not experten_antworten:
                    # Fallback auf einzelnes Modell
                    st.warning("⚠️ Ensemble fehlgeschlagen — Fallback...")
                    with st.spinner("🤖 ..."):
                        ergebnis = ki(ensemble_prompt, bilder=st.session_state.fotos if hat_fotos else None)
                else:
                    # ── RICHTER-KI: Alle Antworten zusammenfassen ──
                    st.write(f"⚖️ Richter-KI fasst {len(experten_antworten)} Experten-Meinungen zusammen...")

                    experten_text = ""
                    for name, antwort in experten_antworten.items():
                        experten_text += f"\n\n=== {name} ===\n{antwort[:800]}"

                    richter_prompt = (
                        f"Du bist der Chef-Experte für Secondhand und Reselling in Deutschland.\n"
                        f"3 Experten haben diesen Artikel analysiert. Lies alle Meinungen und erstelle "
                        f"EINE perfekte, vollständige finale Antwort auf Deutsch.\n"
                        f"Nimm das Beste aus jeder Analyse. Bei Preis-Unterschieden: nimm den Durchschnitt.\n"
                        f"Sei sehr präzise und konkret. Nutze die gleiche Struktur wie die Experten.\n"
                        f"Experten-Analysen:{experten_text}\n\n"
                        f"FINALE EXPERTEN-ANTWORT (vollständig, alle Punkte):"
                    )

                    with st.spinner("⚖️ Richter-KI arbeitet..."):
                        ergebnis = ki(richter_prompt)

                st.markdown(ergebnis)
                st.session_state["ana_ergebnis"] = ergebnis
                st.session_state["vorabinfo"] = ""

                suchbegriff = "Vintage Artikel"
                for line in ergebnis.split("\n"):
                    if "**Artikel:" in line:
                        teile = line.split(":")
                        if len(teile) > 1:
                            suchbegriff = teile[1].strip().strip("*[] ")[:40]
                        break

            with st.status("📡 Stufe 3: Echtzeit-Preise + KI-Preis-Ensemble...", expanded=True):
                ebay_url = f"https://www.ebay.de/sch/i.html?_nkw={urllib.parse.quote(suchbegriff)}&LH_Complete=1&LH_Sold=1"
                ka_url   = f"https://www.kleinanzeigen.de/s-{urllib.parse.quote(suchbegriff)}/k0"
                vi_url   = f"https://www.vinted.de/catalog?search_text={urllib.parse.quote(suchbegriff)}"
                fb_url   = f"https://www.facebook.com/marketplace/search/?query={urllib.parse.quote(suchbegriff)}"

                # ── SCHRITT 1: Alle Quellen gleichzeitig suchen ──
                st.write("🌐 Google + Tavily + You.com suchen gleichzeitig...")

                def hole_google():
                    return google_suche(suchbegriff + " Preis eBay Kleinanzeigen Deutschland")

                def hole_tavily():
                    return web_suche(suchbegriff + " Secondhand Preis Deutschland " + datetime.now().strftime("%Y"))

                google_data = tavily_data = None
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
                    f_google = ex.submit(hole_google)
                    f_tavily = ex.submit(hole_tavily)
                    google_data = f_google.result()
                    tavily_data = f_tavily.result()

                alle_web_daten = ""
                if google_data:
                    st.success("✅ Google: Echte Preise gefunden!")
                    alle_web_daten += "GOOGLE ERGEBNISSE:\n" + google_data + "\n\n"
                if tavily_data:
                    st.success("✅ Tavily: Aktuelle Marktdaten!")
                    alle_web_daten += "TAVILY ERGEBNISSE:\n" + tavily_data + "\n\n"
                if not alle_web_daten:
                    st.info("ℹ️ Web-Suche nicht verfügbar")

                # ── SCHRITT 2: 3 KIs bewerten Preise gleichzeitig ──
                if alle_web_daten:
                    st.write("⚖️ 3 KI-Experten bewerten Preise gleichzeitig...")

                    preis_prompt = (
                        f"Du bist Preisexperte für deutschen Secondhand-Markt.\n"
                        f"Artikel: {suchbegriff}\n"
                        f"Zustand: {gebrauch_beschr} | {defekt_beschr}\n"
                        f"Web-Daten:\n{alle_web_daten}\n\n"
                        f"Bewerte auf Deutsch:\n"
                        f"• Realistischer eBay-Preis: €X\n"
                        f"• Realistischer Kleinanzeigen-Preis: €X\n"
                        f"• Realistischer Flohmarkt-Preis: €X\n"
                        f"• Empfohlener Verkaufspreis: €X\n"
                        f"• Markt-Trend: [steigend/stabil/fallend]\n"
                        f"• Fazit: [2 Sätze]"
                    )

                    def preis_experte(model_info):
                        model_id, model_name = model_info
                        try:
                            _client = _oai.OpenAI(api_key=OR_KEY, base_url="https://openrouter.ai/api/v1")
                            r = _client.chat.completions.create(
                                model=model_id,
                                messages=[{"role":"user","content":preis_prompt}],
                                max_tokens=400,
                                extra_headers={"HTTP-Referer":"https://marktradar.streamlit.app","X-Title":"MarktRadar"}
                            )
                            antwort = r.choices[0].message.content
                            if antwort and len(antwort) > 50:
                                return (model_name, antwort)
                        except Exception:
                            pass
                        return (model_name, None)

                    preis_experten = [
                        ("google/gemini-3-flash-preview", "Gemini 3"),
                        ("google/gemini-2.5-flash",        "Gemini 2.5"),
                        ("openai/gpt-4o-mini",             "GPT-4o-mini"),
                    ]

                    preis_meinungen = {}
                    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
                        futures = {ex.submit(preis_experte, e): e for e in preis_experten}
                        for future in concurrent.futures.as_completed(futures):
                            name, antwort = future.result()
                            if antwort:
                                preis_meinungen[name] = antwort
                                st.write(f"✅ {name} bewertet!")

                    if preis_meinungen:
                        # Richter-KI für Preise
                        preis_texte = "\n\n".join([f"[{n}]: {a}" for n,a in preis_meinungen.items()])
                        preis_fazit = ki(
                            f"3 Preisexperten haben {suchbegriff} bewertet.\n"
                            f"Erstelle EINE finale Preis-Empfehlung auf Deutsch.\n"
                            f"Nimm Durchschnitt bei Unterschieden.\n"
                            f"Format: eBay €X | Kleinanzeigen €X | Flohmarkt €X | Empfehlung €X | Trend: [↑↓→]\n"
                            f"Experten:\n{preis_texte}"
                        )
                        st.info("💰 **Preis-Konsens aller 3 KIs:** " + preis_fazit)

                st.markdown("---")
                st.markdown("**🔗 Direkt suchen:**")
                c1,c2 = st.columns(2)
                with c1:
                    st.markdown(f"🛒 [eBay →]({ebay_url})")
                    st.markdown(f"📱 [Kleinanzeigen →]({ka_url})")
                with c2:
                    st.markdown(f"👗 [Vinted →]({vi_url})")
                    st.markdown(f"👥 [Facebook →]({fb_url})")

            with st.status("✅ Stufe 4: Zusammenfassung...", expanded=True):
                ana_text = st.session_state.get("ana_ergebnis","")
                if len(ana_text) > 200 and "€" in ana_text:
                    fazit = ki(f"Kurze Zusammenfassung (5 Zeilen max) aus dieser Analyse. Nur Fakten. Deutsch.\nFormat:\n• Artikel: [Namen]\n• 🟢 Schnell: [Namen]\n• 🟡 Mittel: [Namen]\n• 🔴 Langsam: [Namen]\n• Gesamtwert: €X\n\nAnalyse:\n{ana_text[:800]}")
                    st.info(f"📊 {fazit}")
                else:
                    st.warning("⚠️ Keine vollständige Analyse vorhanden.")

    # ── LERN-SYSTEM ──
    if st.session_state.get("ana_ergebnis","") and len(st.session_state.get("ana_ergebnis","")) > 200:
        st.markdown("---")
        st.markdown("### 🧠 KI verbessern")
        with st.expander("👍 Preis korrigieren"):
            c1,c2,c3 = st.columns(3)
            fb_art  = c1.text_input("Artikel", key="fb_art")
            fb_echt = c2.number_input("Echter Preis (€)", min_value=1.0, value=50.0, key="fb_echt")
            fb_pl   = c3.selectbox("Plattform", ["Kleinanzeigen","eBay","Vinted","Facebook","Flohmarkt"], key="fb_pl")
            if st.button("💾 Speichern", use_container_width=True, key="fb_save"):
                if fb_art:
                    st.session_state.preis_korrekturen[f"{fb_art} auf {fb_pl}"] = fb_echt
                    st.success(f"✅ Gespeichert!")
        with st.expander("📝 Eigenes Wissen hinzufügen"):
            fb_know = st.text_input("Ihr Wissen:", placeholder="z.B. 'Peg Perego in Berlin meist €150'", key="fb_know")
            if st.button("💾 Hinzufügen", use_container_width=True, key="fb_know_save"):
                if fb_know:
                    st.session_state.mein_wissen.append(fb_know)
                    st.success("✅ Gespeichert!")
        total = len(st.session_state.feedback_log) + len(st.session_state.mein_wissen) + len(st.session_state.preis_korrekturen)
        if total > 0:
            st.info(f"🧠 KI kennt bereits **{total}** Informationen von Ihnen!")

# ════════════════════════════════════════════════════════════
# TAB 2 — ANSCHREIB-BOT
# ════════════════════════════════════════════════════════════
with T[1]:
    st.header("💬 Anschreib-Bot")
    c1,c2 = st.columns(2)
    with c1:
        ab_art = st.text_input("Artikel", placeholder="z.B. Vintage Kamera", key="ab_art")
        ab_mp  = st.number_input("Mein Angebot (€)", min_value=1.0, value=20.0, key="ab_mp")
        ab_vk  = st.number_input("Verkäufer-Preis (€)", min_value=1.0, value=50.0, key="ab_vk")
    with c2:
        ab_stil = st.selectbox("Stil", ["Freundlich & charmant","Bestimmt & direkt","Dringend (heute)","Paket-Deal","Letztes Angebot"], key="ab_stil")
        ab_pl   = st.selectbox("Plattform", ["Kleinanzeigen","eBay","Facebook","Vinted","Flohmarkt"], key="ab_pl")
    ab_kunde = st.text_area("📩 Nachricht des Kunden (optional):", placeholder="Kunden-Nachricht einfügen — KI antwortet darauf!", height=80, key="ab_kunde")
    if st.button("✍️ Nachricht generieren", type="primary", use_container_width=True, key="ab_btn"):
        if ab_art:
            with st.spinner("✍️ ..."):
                kt = f"\nKunden-Nachricht: '{ab_kunde}'" if ab_kunde.strip() else ""
                r = ki(f"Verhandlungs-Nachricht auf Deutsch. Stil: {ab_stil} | Plattform: {ab_pl}\nArtikel: {ab_art} | Angebot: EUR{ab_mp} | Verkäufer: EUR{ab_vk}{kt}\nMax 5 Sätze, NUR die fertige Nachricht!")
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
        c1,c2,c3 = st.columns(3)
        c1.metric("Artikel",len(st.session_state.lager))
        c2.metric("Kapital",f"€{sum(i['ek'] for i in st.session_state.lager):.2f}")
        c3.metric("Gewinn",f"€{sum(i['gewinn'] for i in st.session_state.lager):.2f}")
        st.markdown("---")
        for it in st.session_state.lager:
            c1,c2,c3,c4 = st.columns([3,1,1,1])
            c1.markdown(f"**{it['artikel']}** ({it['zustand']}) — {it['plattform']}")
            c2.markdown(f"€{it['ek']:.0f}"); c3.markdown(f"→ €{it['vk']:.0f}"); c4.markdown(f"**+€{it['gewinn']:.0f}**")
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
            with st.spinner("🤖 ..."):
                b64 = base64.b64encode(ocr_b.read()).decode()
                r = ki(f"Scanne ALLE {ocr_t} im Foto. Für jeden: [Titel] | eBay: €X | Kleinanzeigen: €X | Vinted: €X | Flohmarkt: €X\nTop-3 wertvollste + Gesamtwert. Auf Deutsch.", bilder=[b64])
                st.markdown(r)

# ════════════════════════════════════════════════════════════
# TAB 5 — REPARATUR
# ════════════════════════════════════════════════════════════
with T[4]:
    st.header("🔧 Reparatur-Rechner")
    rep_fotos = st.file_uploader("📷 Fotos (mehrere möglich)", type=["jpg","jpeg","png"], accept_multiple_files=True, key="rep_fotos")
    if rep_fotos:
        cols = st.columns(min(len(rep_fotos),4))
        for i,f in enumerate(rep_fotos):
            with cols[i%4]: st.image(f, caption=f"Foto {i+1}", use_column_width=True)
    c1,c2 = st.columns(2)
    with c1:
        ra   = st.text_input("Artikel",key="ra")
        rek2 = st.number_input("EK (€)",min_value=0.0,value=15.0,key="rek2")
        rm   = st.number_input("Material (€)",min_value=0.0,value=25.0,key="rm")
        rs   = st.number_input("Stunden",min_value=0.5,value=3.0,step=0.5,key="rs")
    with c2:
        rvk = st.number_input("VK (€)",min_value=0.0,value=120.0,key="rvk")
        rpl = st.selectbox("Plattform",["Kleinanzeigen","eBay","Vinted","Facebook","Flohmarkt"],key="rpl")
        rb  = st.text_area("Was reparieren?",height=70,key="rb")
    if st.button("🔧 Berechnen",type="primary",use_container_width=True,key="r_btn"):
        geb = rvk*(0.119 if "eBay" in rpl else 0.05 if "Vinted" in rpl else 0.02)
        gk = rek2+rm+(rvk*0.02)+geb; gw = rvk-gk; sl = gw/rs if rs>0 else 0
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Kosten",f"€{gk:.2f}"); c2.metric("Gewinn",f"€{gw:.2f}")
        c3.metric("Stundenlohn",f"€{sl:.2f}/h"); c4.metric("ROI",f"{(gw/gk*100) if gk>0 else 0:.0f}%")
        if sl>=15: st.success("✅ LOHNT SICH!")
        elif sl>=8: st.warning("⚠️ Grenzfall")
        else: st.error("❌ Lohnt nicht")
        if rb:
            with st.spinner("💡 ..."):
                rep_b = [base64.b64encode(f.read()).decode() for f in rep_fotos] if rep_fotos else None
                st.markdown(ki(f"3 Reparatur-Tipps für '{ra}': {rb}. Auf Deutsch.", bilder=rep_b))

# ════════════════════════════════════════════════════════════
# TAB 6 — TRENDS (ECHTZEIT KI)
# ════════════════════════════════════════════════════════════
with T[5]:
    st.header("📈 Markt-Trends — Echtzeit KI")
    st.markdown(f"**Live-Analyse vom {datetime.now().strftime('%d.%m.%Y')}**")
    c1,c2 = st.columns(2)
    with c1: tr_kat = st.selectbox("Kategorie:", ["Alles","Kleidung & Mode","Porzellan & Antiquitäten","Elektronik","Möbel","Spielzeug","Bücher"], key="tr_kat")
    with c2: tr_region = st.selectbox("Region:", ["Berlin","Deutschland gesamt"], key="tr_region")
    if st.button("🔥 Live-Analyse starten", type="primary", use_container_width=True, key="tr_btn"):
        with st.spinner("🌐 Suche echte Marktdaten..."):
            web_data = web_suche("Secondhand Markt Trends " + tr_kat + " " + tr_region + " " + datetime.now().strftime("%B %Y") + " Preise")
            web_kontext = ("\n\nECHTE WEB-DATEN:\n" + web_data) if web_data else ""
            prompt_tr = ("Markt-Analyst fuer " + tr_region + ", " + datetime.now().strftime("%B %Y") + "." + web_kontext + "\n"
                "Analysiere LIVE: " + tr_kat + ". Auf Deutsch.\n"
                "TOP 5 HEISSESTE ARTIKEL: Name, Preis, Nachfrage, Trend.\n"
                "PREISE STEIGEN: [was wird teurer?]\n"
                "PREISE FALLEN: [was ist uebersaettigt?]\n"
                "GEHEIMTIPP: [1 unterschaetzter Artikel]\n"
                "JETZT VERKAUFEN: [was jetzt verkaufen?]\n"
                "GOLD-SUCHBEGRIFFE: [5 Begriffe]")
            r = ki(prompt_tr)
            if web_data: st.success("✅ Echte Web-Daten eingeflossen!")
            st.markdown(r)
    st.markdown("---")
    tf = st.text_input("🤖 Frage:", placeholder="z.B. Wie läuft gerade Vintage Kleidung?", key="tf")
    if st.button("Analysieren", key="t_btn"):
        if tf:
            with st.spinner("..."):
                st.markdown(ki(f"Reselling-Experte {tr_region} {datetime.now().strftime('%B %Y')}. Konkret auf Deutsch: {tf}"))

# ════════════════════════════════════════════════════════════
# TAB 7 — VERHANDLUNG
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
            r = ki(f"Du bist Verkäufer ({vt}) auf {vpl}. Artikel: {va} für EUR{vvk}. Erste Reaktion wenn Käufer fragt ob Preis verhandelbar. 2-3 Sätze. Deutsch. In Rolle!")
            st.session_state.sim.append({"r":"🏪","t":r})
            st.rerun()
    if st.session_state.sim:
        st.markdown("---")
        for m in st.session_state.sim:
            if m["r"]=="🏪": st.info(f"**🏪 Verkäufer:** {m['t']}")
            else: st.success(f"**🛒 Sie:** {m['t']}")
        kunden_msg = st.text_area("📩 Kunden-Nachricht (optional):", placeholder="Nachricht einfügen — KI antwortet optimal", height=70, key="v_kunde")
        ai = st.text_input("Ihre Antwort:", key="v_inp")
        c1,c2 = st.columns(2)
        with c1:
            if st.button("📤 Senden",type="primary",use_container_width=True,key="v_send"):
                eingabe = kunden_msg.strip() if kunden_msg.strip() else ai
                if eingabe:
                    st.session_state.sim.append({"r":"🛒","t":eingabe})
                    verl = "\n".join([f"{m['r']}: {m['t']}" for m in st.session_state.sim])
                    r = ki(f"Verkäufer ({vt}) von {va} (EUR{vvk}). Verlauf:\n{verl}\nAntworte als Verkäufer (2-3 Sätze, Deutsch, Rolle)!")
                    st.session_state.sim.append({"r":"🏪","t":r})
                    st.rerun()
        with c2:
            if st.button("🧠 Strategie",use_container_width=True,key="v_str"):
                verl = "\n".join([f"{m['r']}: {m['t']}" for m in st.session_state.sim])
                st.markdown(ki(f"Verhandlungsanalyse für {va}, Ziel EUR{vz}. Verlauf:\n{verl}\n1.Was gut? 2.Was besser? 3.Nächste Nachricht? Deutsch."))

# ════════════════════════════════════════════════════════════
# TAB 8 — FOTO-COACH
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
                with c1: fc_b.seek(0); st.image(fc_b,caption="Ihr Foto",use_column_width=True)
                with c2: st.markdown(ki(f"Foto-Experte für {fc_p}. Bewerte dieses Foto. Auf Deutsch.\nBewertung (1-10): Helligkeit, Hintergrund, Schärfe, Winkel\nProbleme + Verbesserungen + Tipps + Preis-Potenzial +X%", bilder=[b64]))

# ════════════════════════════════════════════════════════════
# TAB 9 — FLOHMÄRKTE BERLIN (ECHTZEIT)
# ════════════════════════════════════════════════════════════
with T[8]:
    st.header("🗺️ Berliner Flohmärkte")
    st.markdown(f"Markt-Daten + **Live KI-Updates** vom {datetime.now().strftime('%d.%m.%Y')}")
    heute_de = {"Monday":"Montag","Tuesday":"Dienstag","Wednesday":"Mittwoch","Thursday":"Donnerstag","Friday":"Freitag","Saturday":"Samstag","Sunday":"Sonntag"}.get(datetime.now().strftime("%A"),"Heute")
    if st.button(f"🔴 Live-Update für {heute_de} abrufen", type="primary", use_container_width=True, key="floh_live"):
        with st.spinner("🤖 ..."):
            st.info(ki(f"Berliner Flohmarkt-Experte. Heute ist {heute_de}, {datetime.now().strftime('%d.%m.%Y')}. Welche Märkte sind heute offen? Was ist heute empfehlenswert? Aktuelle Tipps. Auf Deutsch."))
    st.markdown("---")
    maerkte = [
        ("Montag","Rathaus Steglitz","Schloßstraße 37","Mo–Sa 9–18h","+49 30 79706820","🏠 Haushalt","⭐⭐⭐","Günstige Alltagsartikel","https://maps.google.com/?q=Rathaus+Steglitz+Berlin"),
        ("Dienstag","Fehrbelliner Platz","Fehrbelliner Pl. 10707","Di & Fr 8–15h","+49 30 28097272","🏺 Antiquitäten, Porzellan","⭐⭐⭐⭐","Top für Porzellan & Silber!","https://maps.google.com/?q=Fehrbelliner+Platz+Berlin"),
        ("Mittwoch","Alexanderplatz","Alexanderplatz 10178","Täglich 10–19h","+49 30 24632425","🏙️ Gemischt","⭐⭐⭐","Täglich offen","https://maps.google.com/?q=Alexanderplatz+Flohmarkt+Berlin"),
        ("Donnerstag","Winterfeldtplatz","Winterfeldtplatz 10781","Do & Sa 8–14h","+49 30 7262290","🌿 Vintage, Mode","⭐⭐⭐⭐","Do ruhiger & günstiger!","https://maps.google.com/?q=Winterfeldtplatz+Berlin"),
        ("Freitag","Fehrbelliner Platz","Fehrbelliner Pl. 10707","Di & Fr 8–15h","+49 30 28097272","🏺 Antiquitäten","⭐⭐⭐⭐⭐","Freitags BESTE Auswahl!","https://maps.google.com/?q=Fehrbelliner+Platz+Berlin"),
        ("Freitag","Ostbahnhof","Erich-Steinfurth-Str. 1","Fr–So 9–16h","+49 30 2936028","🛍️ Gemischt","⭐⭐⭐⭐","Freitags wenig Leute!","https://maps.google.com/?q=Flohmarkt+Ostbahnhof+Berlin"),
        ("Samstag","RAW Flohmarkt","Revaler Str. 99","Sa & So 10–18h","+49 30 29367840","🕶️ Vintage Mode, Vinyl","⭐⭐⭐⭐⭐","BESTE Vintage-Kleidung!","https://maps.google.com/?q=RAW+Gelände+Berlin"),
        ("Samstag","Winterfeldtmarkt","Winterfeldtplatz 10781","Jeden Sa 8–14h","+49 30 7262290","🌿 Bio, Vintage, Kunst","⭐⭐⭐⭐⭐","Einer der besten Märkte!","https://maps.google.com/?q=Winterfeldtmarkt+Berlin"),
        ("Sonntag","Mauerpark","Bernauer Str. 63","So 9–18h","+49 30 40505380","🎭 Gemischt, Vintage","⭐⭐⭐⭐⭐","MUSS! Vor 10 Uhr!","https://maps.google.com/?q=Mauerpark+Flohmarkt+Berlin"),
        ("Sonntag","Boxhagener Platz","Boxhagener Pl. 10245","So 10–18h","+49 30 29362596","🏺 Antiquitäten, Porzellan","⭐⭐⭐⭐⭐","Top für Porzellan!","https://maps.google.com/?q=Boxhagener+Platz+Flohmarkt+Berlin"),
        ("Sonntag","Treptower Park","Treptower Park 12435","So 8–16h","+49 30 5321555","🔧 Elektronik, DDR","⭐⭐⭐⭐","Gut für DDR & Elektronik!","https://maps.google.com/?q=Treptower+Park+Flohmarkt+Berlin"),
        ("Sonntag","RAW Flohmarkt","Revaler Str. 99","Sa & So 10–18h","+49 30 29367840","🕶️ Vintage Mode","⭐⭐⭐⭐⭐","So entspannter als Sa","https://maps.google.com/?q=RAW+Gelände+Berlin"),
        ("Sonntag","Arkonaplatz","Arkonaplatz 10435","So 10–16h","+49 30 7861003","🏛️ Antiquitäten, Raritäten","⭐⭐⭐⭐","Klein aber fein!","https://maps.google.com/?q=Arkonaplatz+Flohmarkt+Berlin"),
    ]
    tage = ["Alle","Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]
    fw = st.radio("📅 Tag:",tage,horizontal=True,key="fw")
    st.markdown("---")
    liste = maerkte if fw=="Alle" else [m for m in maerkte if m[0]==fw]
    if fw=="Alle":
        for tag in tage[1:]:
            tm = [m for m in maerkte if m[0]==tag]
            if tm:
                st.markdown(f"### 📅 {tag}")
                for m in tm:
                    with st.expander(f"{m[6]} **{m[1]}**"):
                        c1,c2 = st.columns([2,1])
                        with c1: st.markdown(f"📍 {m[2]}\n\n🕐 {m[3]}\n\n📞 **{m[4]}**\n\n🏷️ {m[5]}\n\n💡 *{m[7]}*")
                        with c2: st.markdown(m[6]); st.link_button("🗺️ Maps",m[8],use_container_width=True)
    else:
        for m in liste:
            with st.expander(f"{m[6]} **{m[1]}**"):
                c1,c2 = st.columns([2,1])
                with c1: st.markdown(f"📍 {m[2]}\n\n🕐 {m[3]}\n\n📞 **{m[4]}**\n\n🏷️ {m[5]}\n\n💡 *{m[7]}*")
                with c2: st.markdown(m[6]); st.link_button("🗺️ Maps",m[8],use_container_width=True)
    st.markdown("---")
    fq = st.text_input("🤖 Frage:", placeholder="z.B. Wo finde ich heute gute Antiquitäten?", key="fq")
    if st.button("🗺️ KI fragen", type="primary", use_container_width=True, key="f_btn"):
        if fq:
            with st.spinner("..."): st.markdown(ki(f"Berliner Flohmarkt-Experte {datetime.now().strftime('%B %Y')}. Konkret auf Deutsch: {fq}"))

# ════════════════════════════════════════════════════════════
# TAB 10 — MARKEN-SCANNER
# ════════════════════════════════════════════════════════════
with T[9]:
    st.header("🔬 Marken-Scanner")
    ms_b = st.file_uploader("📷 Stempel/Logo fotografieren",type=["jpg","jpeg","png"],key="ms_b")
    ms_k = st.selectbox("Kategorie",["Porzellan & Keramik","Silber & Besteck","Uhren","Schmuck","Elektronik","Kleidung","Spielzeug","Unbekannt"],key="ms_k")
    if st.button("🔬 Identifizieren",type="primary",use_container_width=True,key="ms_btn"):
        if ms_b:
            with st.spinner("..."):
                b64 = base64.b64encode(ms_b.read()).decode()
                c1,c2 = st.columns(2)
                with c1: ms_b.seek(0); st.image(ms_b,caption="Stempel",use_column_width=True)
                with c2: st.markdown(ki(f"Marken-Experte für {ms_k}. Identifiziere Stempel/Logo. Auf Deutsch.\nMarke, Herkunft, Jahr, Echtheit, Wert, eBay-Suchbegriff.", bilder=[b64]))

# ════════════════════════════════════════════════════════════
# TAB 11 — TIMING
# ════════════════════════════════════════════════════════════
with T[10]:
    st.header("📅 Saisonaler Timing-Planer")
    ti_a = st.text_input("Artikel",placeholder="z.B. Winterjacke, Weihnachtsdeko",key="ti_a")
    ti_m = st.selectbox("Monat",["Januar","Februar","März","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"],index=datetime.now().month-1,key="ti_m")
    if st.button("📅 Timing analysieren",type="primary",use_container_width=True,key="ti_btn"):
        if ti_a:
            with st.spinner("..."):
                st.markdown(ki(f"Timing-Experte. Artikel: {ti_a} | Monat: {ti_m}. Beste/schlechteste Monate + Monatstabelle + Jetzt-Empfehlung. Auf Deutsch."))

# ════════════════════════════════════════════════════════════
# TAB 12 — ANZEIGEN-KI
# ════════════════════════════════════════════════════════════
with T[11]:
    st.header("✨ Anzeigen-Optimierer")
    ao_fotos = st.file_uploader("📷 Fotos (mehrere möglich)", type=["jpg","jpeg","png"], accept_multiple_files=True, key="ao_fotos")
    if ao_fotos:
        cols = st.columns(min(len(ao_fotos),4))
        for i,f in enumerate(ao_fotos):
            with cols[i%4]: st.image(f, caption=f"Foto {i+1}", use_column_width=True)
    c1,c2 = st.columns(2)
    with c1:
        ao_l  = st.selectbox("Plattform",["Kleinanzeigen","Vinted","eBay","Facebook"],key="ao_l")
        ao_p  = st.number_input("Preis (€)",min_value=0.0,value=45.0,key="ao_p")
    with c2:
        ao_k  = st.selectbox("Kategorie",["Haushalt","Kleidung","Elektronik","Möbel","Spielzeug","Sonstiges"],key="ao_k")
        ao_t2 = st.number_input("Tage online",min_value=0,value=7,key="ao_t2")
    ao_ti = st.text_input("Aktueller Titel:",key="ao_ti")
    ao_tx = st.text_area("Aktuelle Beschreibung:",height=100,key="ao_tx")
    if st.button("✨ Optimieren",type="primary",use_container_width=True,key="ao_btn"):
        if ao_ti or ao_tx or ao_fotos:
            with st.spinner("..."):
                ao_b = [base64.b64encode(f.read()).decode() for f in ao_fotos] if ao_fotos else None
                st.markdown(ki(f"Anzeigen-Experte für {ao_l}. Kategorie: {ao_k}. Preis: €{ao_p}. {ao_t2} Tage online.\nTitel: {ao_ti}\nText: {ao_tx}\nAnalysiere + verbessere. Note 1-10 + Schwächen + Neuer Titel + Neue Beschreibung + Preis-Empfehlung + Keywords + Tipps. Auf Deutsch.", bilder=ao_b))

# ════════════════════════════════════════════════════════════
# TAB 13 — RESELLING-CHAT
# ════════════════════════════════════════════════════════════
with T[12]:
    st.header("🤖 KI-Reselling-Chat")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    if prompt_chat := st.chat_input("Fragen Sie alles über Reselling, Preise, Flohmärkte..."):
        st.session_state.chat_history.append({"role":"user","content":prompt_chat})
        with st.chat_message("user"): st.markdown(prompt_chat)
        with st.chat_message("assistant"):
            with st.spinner("🤖 ..."):
                antwort = ki("Erfahrener deutscher Reselling-Experte. Kleinanzeigen, Vinted, Facebook, eBay. Deutsch, konkret, praktisch. Frage: " + prompt_chat)
                st.markdown(antwort)
        st.session_state.chat_history.append({"role":"assistant","content":antwort})
    if st.button("🗑️ Chat löschen", key="chat_clear"): st.session_state.chat_history = []; st.rerun()

# ════════════════════════════════════════════════════════════
# TAB 14 — KONKURRENZ
# ════════════════════════════════════════════════════════════
with T[13]:
    st.header("🔎 Konkurrenz-Checker")
    kk_url   = st.text_input("🔗 Konkurrenz-Link:", key="kk_url")
    kk_art   = st.text_input("Ihr Artikel:", key="kk_art")
    kk_preis = st.number_input("Ihr Preis (€):", min_value=0.0, value=80.0, key="kk_preis")
    if st.button("🔎 Analysieren", type="primary", use_container_width=True, key="kk_btn"):
        if kk_url:
            with st.spinner("..."):
                seite = lies_url(kk_url)
                st.markdown(ki(f"Konkurrenz-Analyse. Inhalt:\n{seite[:2000]}\nMein Artikel: {kk_art} | Mein Preis: €{kk_preis}\nKonkurrenz-Analyse + Wie ich besser sein kann + Optimaler Preis + Fazit. Auf Deutsch."))

# ════════════════════════════════════════════════════════════
# TAB 15 — BUSINESS-COACH
# ════════════════════════════════════════════════════════════
with T[14]:
    st.header("📊 Business-Coach")
    if st.session_state.gwlog:
        c1,c2,c3 = st.columns(3)
        ges_g = sum(i["g"] for i in st.session_state.gwlog); ges_e = sum(i["ek"] for i in st.session_state.gwlog)
        c1.metric("Verkäufe",len(st.session_state.gwlog)); c2.metric("Gewinn",f"€{ges_g:.2f}"); c3.metric("ROI",f"{(ges_g/ges_e*100) if ges_e>0 else 0:.0f}%")
        if st.button("🤖 Analysieren", type="primary", use_container_width=True, key="bc_btn"):
            with st.spinner("..."):
                log = "\n".join([f"{e['a']}: EK€{e['ek']} VK€{e['vk']} G€{e['g']} {e['pl']}" for e in st.session_state.gwlog])
                st.markdown(ki(f"Business-Coach für deutschen Reseller. Verkäufe:\n{log}\nStärken, Schwächen, Top-3 Empfehlungen, Gewinn-Potenzial. Auf Deutsch."))
    else: st.info("💡 Erst Verkäufe eintragen!")

# ════════════════════════════════════════════════════════════
# TAB 16 — LAGER-KI
# ════════════════════════════════════════════════════════════
with T[15]:
    st.header("📦 Lager-Optimierer")
    if st.session_state.lager:
        if st.button("🤖 Lager analysieren", type="primary", use_container_width=True, key="lo_btn"):
            with st.spinner("..."):
                lt = "\n".join([f"{it['artikel']}: EK€{it['ek']} VK€{it['vk']} {it['tage']}T {it['plattform']}" for it in st.session_state.lager])
                st.markdown(ki(f"Lager-Analyse:\n{lt}\nSofort verkaufen, Diese Woche, Bundle-Tipps, Preis-Anpassungen, Note 1-10. Auf Deutsch."))
    else: st.info("💡 Erst Artikel im Lager eintragen!")

# ════════════════════════════════════════════════════════════
# TAB 17 — MARKT-NEWS
# ════════════════════════════════════════════════════════════
with T[16]:
    st.header("📰 Markt-News")
    mn_kat = st.selectbox("Kategorie:", ["Alles","Kleidung","Elektronik","Porzellan","Spielzeug","Möbel","Bücher"], key="mn_kat")
    if st.button("📰 Aktuelle Trends", type="primary", use_container_width=True, key="mn_btn"):
        with st.spinner("..."):
            st.markdown(ki(f"Markt-Analyst {datetime.now().strftime('%B %Y')}. Report für {mn_kat}.\nTOP-5 meistgesucht + Preise steigen + Preise fallen + Geheimtipp + Saisonaler Tipp {datetime.now().strftime('%B')}. Auf Deutsch."))

# ════════════════════════════════════════════════════════════
# TAB 18 — PROFI-TEXT
# ════════════════════════════════════════════════════════════
with T[17]:
    st.header("✍️ Profi-Text Generator")
    pt_fotos = st.file_uploader("📷 Fotos (mehrere möglich)", type=["jpg","jpeg","png"], accept_multiple_files=True, key="pt_fotos")
    if pt_fotos:
        cols = st.columns(min(len(pt_fotos),4))
        for i,f in enumerate(pt_fotos):
            with cols[i%4]: st.image(f, caption=f"Foto {i+1}", use_column_width=True)
    c1,c2 = st.columns(2)
    with c1:
        pt_art   = st.text_input("Artikel:", key="pt_art")
        pt_zust  = st.selectbox("Zustand:", ["Wie neu","Sehr gut","Gut","Gebraucht"], key="pt_zust")
        pt_preis = st.number_input("Preis (€):", min_value=0.0, value=120.0, key="pt_preis")
    with c2:
        pt_det = st.text_area("Details:", height=100, key="pt_details")
    if st.button("✍️ Texte erstellen", type="primary", use_container_width=True, key="pt_btn"):
        if pt_art or pt_fotos:
            with st.spinner("..."):
                pt_b = [base64.b64encode(f.read()).decode() for f in pt_fotos] if pt_fotos else None
                st.markdown(ki(f"Profi-Verkaufstexte für alle Plattformen. Artikel: {pt_art} | Zustand: {pt_zust} | Preis: €{pt_preis}\nDetails: {pt_det}\nKleinanzeigen-Titel+Text, Vinted, Facebook, eBay, Keywords. Auf Deutsch.", bilder=pt_b))

# ── FOOTER ────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"<p style='text-align:center;color:#666'>⚡ MarktRadar OS PRO v7.0 · Zoran Berlin · {datetime.now().strftime('%d.%m.%Y')}</p>", unsafe_allow_html=True)
