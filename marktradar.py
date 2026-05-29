import streamlit as st
import os, re, base64, urllib.parse, json
from datetime import datetime
import requests
from openai import OpenAI

st.set_page_config(page_title="⚡ MarktRadar OS PRO", page_icon="⚡",
    layout="wide", initial_sidebar_state="collapsed")

# ── SECRETS ─────────────────────────────────────────────────
def secret(k):
    try: return st.secrets[k]
    except: return os.environ.get(k,"")

OR_KEY = secret("OPENROUTER_API_KEY")

# ── SESSION STATE ────────────────────────────────────────────
for k,v in {"lager":[],"sim":[],"lot":[],"gwlog":[],"fotos":[],"fcnt":0}.items():
    if k not in st.session_state: st.session_state[k]=v

# ── KI ENGINE ────────────────────────────────────────────────
def ki(prompt, bilder=None):
    """
    bilder = Liste von Base64-Strings
    Gibt immer einen String zurück.
    """
    if not OR_KEY:
        return "❌ Kein API-Key! Bitte in Streamlit Secrets eintragen: OPENROUTER_API_KEY"
    try:
        client = OpenAI(api_key=OR_KEY, base_url="https://openrouter.ai/api/v1")
        if bilder and len(bilder) > 0:
            model = "openai/gpt-4o"
            inhalt = []
            for b64 in bilder[:4]:  # max 4 Bilder
                inhalt.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"}
                })
            inhalt.append({"type": "text", "text": prompt})
            msgs = [{"role": "user", "content": inhalt}]
        else:
            model = "openai/gpt-4o-mini"
            msgs  = [{"role": "user", "content": prompt}]
        r = client.chat.completions.create(model=model, messages=msgs, max_tokens=2500)
        return r.choices[0].message.content
    except Exception as e:
        return f"❌ KI-Fehler: {str(e)}"

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
    defekt_info = {
        (1,20):  "Fast neu — minimale Gebrauchsspuren",
        (21,40): "Leicht gebraucht — kleine sichtbare Mängel",
        (41,60): "Deutlich gebraucht — sichtbare Mängel",
        (61,80): "Stark beschädigt — größere Schäden",
        (81,100):"Fast unbrauchbar — erhebliche Defekte",
    }
    defekt_text = next((v for (lo,hi),v in defekt_info.items() if lo<=defekt<=hi), "")

    extra = ""
    if beschreibung.strip():
        extra += f"\n\nHAENDLER-HINWEIS: {beschreibung}"
    if url_text.strip() and not url_text.startswith("[URL"):
        extra += f"\n\nWEBSEITE-INHALT:\n{url_text[:2000]}"

    return f"""Du bist ein erfahrener deutscher Reselling-Experte.
Analysiere ALLE sichtbaren Artikel im Bild (oder Webseiten-Inhalt).
Antworte IMMER vollstaendig auf Deutsch. Niemals verweigern.
Zustand laut Haendler: {defekt}% Defekt — {defekt_text}{extra}

Ampel-System:
GRUEN = schnell verkaeuflich (1-7 Tage)
GELB  = mittlere Verkaufszeit (1-4 Wochen)
ROT   = langsame Verkaeuflichkeit (1-3 Monate)

Fuer JEDEN sichtbaren Artikel:

ARTIKEL [Nummer]: [Name in Grossbuchstaben]
Kurzbeschreibung: [2-3 Saetze: Was ist es? Besonderheiten? Zustand?]
Marke/Hersteller: [Name oder nicht erkennbar]
Material: [genaues Material]
Alter/Epoche: [ca. Jahr oder Jahrzehnt, z.B. 1960er DDR]
Stempel/Logos: [was sichtbar ist oder keine]
Echtheit: [Echt / Wahrscheinlich echt / Unsicher / Replik]
Ampel: [GRUEN / GELB / ROT]
Verkaufszeit: [X Tage oder X Wochen]
Nachfrage: [Sehr hoch / Hoch / Mittel / Niedrig]
Zielgruppe: [Wer kauft das?]
Preise (Defekt {defekt}% beruecksichtigt):
  eBay: EUR X bis EUR Y
  Kleinanzeigen: EUR X bis EUR Y
  Vinted: EUR X bis EUR Y
  Facebook: EUR X bis EUR Y
  Flohmarkt: EUR X bis EUR Y
  Max. Ankaufspreis: EUR X

---

[Naechster Artikel genau so]

GESAMT-AUSWERTUNG:
Artikel gefunden: X
GRUEN (schnell): X Artikel
GELB (mittel): X Artikel
ROT (langsam): X Artikel
Gesamtwert: EUR X bis EUR Y
Max. Ankauf gesamt: EUR X
Wertvollster Artikel: [Name] (EUR X)"""

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
    "🔍 Analyse","💬 Anschreib","📦 Lager","📚 OCR",
    "🔧 Reparatur","📦 Post","📈 Trends","🎭 Verhandlung",
    "📸 Foto-Coach","🗺️ Flohmärkte","🧮 Lot",
    "✉️ Nachrichten","📉 Preissenker","🔬 Marken",
    "📦 Bundle","🛡️ Reklamation","📅 Timing",
    "💰 Gewinn","✨ Anzeigen-KI","🗓️ Tagesplan"
])

# ════════════════════════════════════════════════════════════
# TAB 1 — ANALYSE
# ════════════════════════════════════════════════════════════
with T[0]:
    st.header("🔍 Artikel-Analyse")
    st.markdown("Fotos + Links werden **vollständig** analysiert — jeder Artikel einzeln mit Preisen!")

    typ = st.radio("Was analysieren?",["📸 Foto","🔗 Link","📸 + 🔗 Beides"],
                   horizontal=True, key="a_typ")

    url_text = ""
    url_inp  = ""

    # ── FOTO-UPLOAD MIT PERMANENTEM SPEICHER ──
    if "Foto" in typ:
        st.markdown("##### 📷 Fotos hochladen")

        neu = st.file_uploader(
            "Foto auswählen (einzeln hochladen, dann speichern)",
            type=["jpg","jpeg","png","webp"],
            accept_multiple_files=False,
            key=f"fu_{st.session_state.fcnt}"
        )

        c1,c2 = st.columns(2)
        with c1:
            if st.button("➕ Foto speichern", type="primary", use_container_width=True):
                if neu:
                    neu.seek(0)
                    st.session_state.fotos.append(base64.b64encode(neu.read()).decode())
                    st.session_state.fcnt += 1
                    st.rerun()
                else:
                    st.warning("Zuerst Foto auswählen!")
        with c2:
            if st.button("🗑️ Alle löschen", use_container_width=True):
                st.session_state.fotos = []
                st.session_state.fcnt += 1
                st.rerun()

        n = len(st.session_state.fotos)
        if n > 0:
            st.success(f"✅ {n} Foto(s) gespeichert und bereit!")
            cols = st.columns(min(n,4))
            for i,b64 in enumerate(st.session_state.fotos):
                with cols[i%4]:
                    st.image(base64.b64decode(b64), caption=f"Foto {i+1}", use_column_width=True)
        else:
            st.info("Noch keine Fotos. Foto auswählen → 'Foto speichern' drücken.")

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
            with st.status("✅ Stufe 4: Zusammenfassung...", expanded=True):
                ana_kurz = st.session_state.get("ana_ergebnis","")[:800]
                fazit = ki(
                    "Erstelle eine sehr kurze Zusammenfassung (max 5 Zeilen) fuer diesen Haendler.\n"
                    "Nur Fakten auf Deutsch. Kein Ratschlag.\n"
                    "Format:\n"
                    "• Artikel: [Anzahl und Namen]\n"
                    "• GRUEN (schnell): [Namen]\n"
                    "• GELB (mittel): [Namen]\n"
                    "• ROT (langsam): [Namen]\n"
                    "• Gesamtwert: EUR X bis EUR Y\n\n"
                    f"Analyse:\n{ana_kurz}"
                )
                st.info(f"📊 {fazit}")

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
    if st.button("✍️ Nachricht", type="primary", use_container_width=True, key="ab_btn"):
        if ab_art:
            with st.spinner("✍️ ..."):
                r = ki(f"Schreibe eine Verhandlungs-Nachricht auf Deutsch.\n"
                       f"Stil: {ab_stil} | Plattform: {ab_pl}\n"
                       f"Artikel: {ab_art} | Angebot: EUR{ab_mp} | Verkäufer: EUR{ab_vk}\n"
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
    st.header("📦 DHL vs. Hermes")
    c1,c2 = st.columns(2)
    with c1:
        pg = st.number_input("Gewicht (kg)",min_value=0.1,value=1.0,step=0.1,key="pg")
    with c2:
        pv = st.checkbox("Versicherung?",key="pv")
    dhl_t = [(0.5,3.99,"S"),(1.0,4.99,"M"),(2.0,6.99,"L"),(5.0,9.49,"5kg"),(10.0,12.49,"10kg"),(31.5,18.49,"31kg")]
    her_t = [(0.5,3.70,"XS"),(1.0,4.50,"S"),(2.0,5.50,"M"),(5.0,7.90,"L"),(10.0,10.90,"XL"),(25.0,15.90,"XXL")]
    if st.button("⚡ Vergleichen",type="primary",use_container_width=True,key="p_btn"):
        dp,dn = dhl_t[-1][1],dhl_t[-1][2]
        for mx,p,n in dhl_t:
            if pg<=mx: dp,dn=p,n; break
        hp,hn = her_t[-1][1],her_t[-1][2]
        for mx,p,n in her_t:
            if pg<=mx: hp,hn=p,n; break
        if pv: dp+=2.5; hp+=1.99
        c1,c2 = st.columns(2)
        c1.markdown(f"### 🟡 DHL\n**€{dp:.2f}** — {dn}")
        c2.markdown(f"### 🟢 Hermes\n**€{hp:.2f}** — {hn}")
        st.markdown("---")
        if dp<hp: st.success(f"🏆 DHL günstiger! Ersparnis €{hp-dp:.2f}")
        elif hp<dp: st.success(f"🏆 Hermes günstiger! Ersparnis €{dp-hp:.2f}")
        else: st.info("🤝 Gleicher Preis!")

# ════════════════════════════════════════════════════════════
# TAB 7 — TRENDS
# ════════════════════════════════════════════════════════════
with T[6]:
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
with T[7]:
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
        ai  = st.text_input("Ihre Antwort:",key="v_inp")
        c1,c2 = st.columns(2)
        with c1:
            if st.button("📤 Senden",type="primary",use_container_width=True,key="v_send"):
                if ai:
                    st.session_state.sim.append({"r":"🛒","t":ai})
                    verl = "\n".join([f"{m['r']}: {m['t']}" for m in st.session_state.sim])
                    r = ki(f"Verkäufer ({vt}) von {va} (EUR{vvk}). Verlauf:\n{verl}\nAntwort (2-3 Saetze, Deutsch, in Rolle)!")
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
with T[8]:
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
with T[9]:
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
    fq = st.text_input("🤖 Frage:",key="fq")
    if st.button("Fragen",key="f_btn"):
        if fq:
            with st.spinner("..."): st.markdown(ki(f"Berliner Flohmarkt-Experte. Kurz auf Deutsch: {fq}"))

# ════════════════════════════════════════════════════════════
# TAB 11 — LOT
# ════════════════════════════════════════════════════════════
with T[10]:
    st.header("🧮 Lot-Kalkulator")
    c1,c2 = st.columns(2)
    with c1:
        lop = st.number_input("Lot-Preis (€)",min_value=0.0,value=50.0,key="lop")
        lot = st.number_input("Transport (€)",min_value=0.0,value=0.0,key="lot2")
        los = st.number_input("Stunden",min_value=0.5,value=2.0,step=0.5,key="los")
    with c2:
        lob = st.text_area("Was ist im Lot?",height=90,key="lob")
    c1,c2,c3 = st.columns([3,1,1])
    with c1: nla = st.text_input("Artikel",key="nla")
    with c2: nmin = st.number_input("Min€",min_value=0.0,value=5.0,key="nmin")
    with c3: nmax = st.number_input("Max€",min_value=0.0,value=20.0,key="nmax")
    c1,c2 = st.columns(2)
    with c1:
        if st.button("➕ Hinzufügen",use_container_width=True,key="lo_add"):
            if nla:
                st.session_state.lot.append({"name":nla,"min":nmin,"max":nmax,"s":(nmin+nmax)/2})
                st.rerun()
    with c2:
        if st.button("🗑️ Leeren",use_container_width=True,key="lo_clr"):
            st.session_state.lot=[]; st.rerun()
    if st.session_state.lot:
        gmin=gmax=0
        for a in st.session_state.lot:
            c1,c2,c3,c4=st.columns([3,1,1,1])
            c1.markdown(f"**{a['name']}**"); c2.markdown(f"€{a['min']:.0f}")
            c3.markdown(f"€{a['max']:.0f}"); c4.markdown(f"Ø€{a['s']:.0f}")
            gmin+=a['min']; gmax+=a['max']
        gs=(gmin+gmax)/2; kosten=lop+lot; gws=gs-kosten; sl=gws/los if los>0 else 0
        st.markdown("---")
        c1,c2,c3,c4=st.columns(4)
        c1.metric("Kosten",f"€{kosten:.0f}"); c2.metric("Wert",f"€{gmin:.0f}–€{gmax:.0f}")
        c3.metric("Gewinn",f"€{gws:.0f}"); c4.metric("Stundenlohn",f"€{sl:.2f}/h")
        if gws>20 and sl>10: st.success(f"🟢 LOHNT! €{gws:.0f} / €{sl:.2f}/h")
        elif gws>0: st.warning(f"🟡 Grenzfall: €{gws:.0f}")
        else: st.error(f"🔴 Lohnt nicht: Verlust €{abs(gws):.0f}")
        if lob and st.button("🤖 KI-Analyse",use_container_width=True,key="lo_ki"):
            with st.spinner("..."):
                al="\n".join([f"- {a['name']}: EUR{a['min']}–EUR{a['max']}" for a in st.session_state.lot])
                st.markdown(ki(f"Lot-Analyse fuer deutschen Reseller.\nInhalt: {lob}\nArtikel:\n{al}\nPreis: EUR{lop}\n1.Wertvollste? 2.Strategie? 3.Ampel? Auf Deutsch."))

# ════════════════════════════════════════════════════════════
# TAB 12 — KUNDENNACHRICHTEN
# ════════════════════════════════════════════════════════════
with T[11]:
    st.header("✉️ Kundennachrichten-KI")
    st.markdown("Käufer schreibt → KI schreibt perfekte Antwort!")
    c1,c2 = st.columns(2)
    with c1:
        kn_pl = st.selectbox("Plattform",["Kleinanzeigen","Vinted","eBay","Facebook"],key="kn_pl")
        kn_a  = st.text_input("Ihr Artikel",key="kn_a")
        kn_p  = st.number_input("Ihr Preis (€)",min_value=0.0,value=50.0,key="kn_p")
    with c2:
        kn_z  = st.selectbox("Ziel",["Verkauf abschließen","Preis verteidigen","Auf Mängel antworten",
            "Termin vereinbaren","Kleinen Nachlass anbieten"],key="kn_z")
    kn_m = st.text_area("📩 Käufer-Nachricht:",height=80,key="kn_m")
    if st.button("✉️ Antwort generieren",type="primary",use_container_width=True,key="kn_btn"):
        if kn_m:
            with st.spinner("✍️ ..."):
                r = ki(f"Verkäufer auf {kn_pl}. Artikel: {kn_a} fuer EUR{kn_p}.\n"
                       f"Käufer: '{kn_m}'\nZiel: {kn_z}\n"
                       f"Schreibe perfekte Antwort (max 4 Saetze, professionell, freundlich). NUR die Nachricht!")
                st.text_area("📩 Ihre Antwort:",value=r,height=150,key="kn_r")
                st.success("✅ Kopieren & senden!")

# ════════════════════════════════════════════════════════════
# TAB 13 — PREISSENKER
# ════════════════════════════════════════════════════════════
with T[12]:
    st.header("📉 Preissenkung-Planer")
    c1,c2 = st.columns(2)
    with c1:
        ps_a = st.text_input("Artikel",key="ps_a")
        ps_p = st.number_input("Aktueller Preis (€)",min_value=1.0,value=45.0,key="ps_p")
        ps_e = st.number_input("Ihr EK (€)",min_value=0.0,value=10.0,key="ps_e")
    with c2:
        ps_t = st.number_input("Liegezeit (Tage)",min_value=0,value=14,key="ps_t")
        ps_l = st.selectbox("Plattform",["Kleinanzeigen","eBay","Vinted","Facebook"],key="ps_l")
        ps_v = st.number_input("Aufrufe",min_value=0,value=25,key="ps_v")
    if st.button("📉 Strategie",type="primary",use_container_width=True,key="ps_btn"):
        with st.spinner("🤖 ..."):
            r = ki(f"Preisoptimierung fuer: {ps_a}, EUR{ps_p}, EK EUR{ps_e}, {ps_l}, {ps_t} Tage, {ps_v} Aufrufe.\n"
                   f"Erstelle auf Deutsch:\n"
                   f"ANALYSE: Warum kein Verkauf?\n"
                   f"PREISPLAN: Tabelle mit Datum, neuem Preis, Aktion\n"
                   f"TIPPS: Neuer Titel, bester Wochentag, Min-Preis EUR{ps_e*1.1:.0f}")
            st.markdown(r)

# ════════════════════════════════════════════════════════════
# TAB 14 — MARKEN-SCANNER
# ════════════════════════════════════════════════════════════
with T[13]:
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
with T[14]:
    st.header("📦 Bundle-KI")
    st.markdown("KI schlägt vor welche Artikel zusammen mehr Gewinn bringen!")
    if st.session_state.lager:
        st.success(f"✅ {len(st.session_state.lager)} Artikel aus Lager verfügbar")
        for i in st.session_state.lager:
            st.markdown(f"- **{i['artikel']}** → €{i['vk']:.0f}")
    else:
        st.info("💡 Erst Artikel im Lager-Tab eintragen!")
    bu_extra = st.text_area("Weitere Artikel:",height=80,key="bu_extra")
    bu_ziel  = st.selectbox("Ziel",["Max. Gewinn","Schneller Verkauf","Beste Plattform"],key="bu_ziel")
    if st.button("📦 Bundle-Strategie",type="primary",use_container_width=True,key="bu_btn"):
        al = "\n".join([f"- {i['artikel']} (EUR{i['vk']:.0f})" for i in st.session_state.lager])
        if bu_extra: al += f"\n{bu_extra}"
        if al:
            with st.spinner("🤖 ..."):
                r = ki(f"Bundle-Strategie fuer deutschen Reseller. Ziel: {bu_ziel}\nArtikel:\n{al}\n"
                       f"Schlage 3 optimale Bundles vor. Fuer jedes: Name, Inhalt, Einzelpreis, Bundle-Preis, Mehrgewinn, Plattform, Titel. Auf Deutsch.")
                st.markdown(r)

# ════════════════════════════════════════════════════════════
# TAB 16 — REKLAMATION
# ════════════════════════════════════════════════════════════
with T[15]:
    st.header("🛡️ Reklamations-Helfer")
    c1,c2 = st.columns(2)
    with c1:
        rk_a = st.text_input("Artikel",key="rk_a")
        rk_p = st.number_input("VK-Preis (€)",min_value=0.0,value=50.0,key="rk_p")
        rk_l = st.selectbox("Plattform",["Kleinanzeigen","eBay","Vinted","Facebook"],key="rk_l")
    with c2:
        rk_t = st.selectbox("Art",["Nicht wie beschrieben","Beschädigt angekommen","Will zurückgeben",
            "Behauptet Fälschung","Versand zu langsam","Preis-Beschwerde"],key="rk_t")
    rk_m = st.text_area("📩 Käufer-Nachricht:",height=80,key="rk_m")
    if st.button("🛡️ Antwort erstellen",type="primary",use_container_width=True,key="rk_btn"):
        if rk_m:
            with st.spinner("✍️ ..."):
                r = ki(f"Experte fuer Kaeufer-Verkaeufer-Kommunikation auf {rk_l}.\n"
                       f"Artikel: {rk_a} EUR{rk_p}. Problem: {rk_t}. Kaeufer: '{rk_m}'\n"
                       f"Schreibe: 1. Professionelle Antwort (beruhigt Kaeufer, rechtssicher, keine Rueckgabe provozieren)\n"
                       f"2. Rechtliche Lage (Pflichten & Rechte) 3. Beste Strategie. Auf Deutsch.")
                st.markdown(r)

# ════════════════════════════════════════════════════════════
# TAB 17 — TIMING
# ════════════════════════════════════════════════════════════
with T[16]:
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
with T[17]:
    st.header("💰 Gewinn-Tagebuch")
    c1,c2,c3,c4 = st.columns(4)
    with c1: gb_a = st.text_input("Artikel",key="gb_a")
    with c2: gb_e = st.number_input("EK (€)",min_value=0.0,value=10.0,key="gb_e")
    with c3: gb_v = st.number_input("VK (€)",min_value=0.0,value=35.0,key="gb_v")
    with c4: gb_l = st.selectbox("Plattform",["Kleinanzeigen","eBay","Vinted","Facebook","Flohmarkt"],key="gb_l")
    if st.button("✅ Eintragen",type="primary",use_container_width=True,key="gb_btn"):
        if gb_a:
            g=gb_v-gb_e-(gb_v*0.05)
            st.session_state.gwlog.append({"d":datetime.now().strftime("%d.%m.%Y"),"a":gb_a,"ek":gb_e,"vk":gb_v,"g":round(g,2),"pl":gb_l})
            st.success(f"✅ Gewinn: €{g:.2f}"); st.rerun()
    if st.session_state.gwlog:
        ge=sum(i["ek"] for i in st.session_state.gwlog)
        gv=sum(i["vk"] for i in st.session_state.gwlog)
        gg=sum(i["g"] for i in st.session_state.gwlog)
        roi=(gg/ge*100) if ge>0 else 0
        c1,c2,c3,c4=st.columns(4)
        c1.metric("Verkäufe",len(st.session_state.gwlog))
        c2.metric("Investiert",f"€{ge:.2f}")
        c3.metric("Gewinn",f"€{gg:.2f}")
        c4.metric("ROI",f"{roi:.0f}%")
        st.markdown("---")
        for e in reversed(st.session_state.gwlog[-10:]):
            farbe="🟢" if e["g"]>20 else "🟡" if e["g"]>0 else "🔴"
            st.markdown(f"{farbe} {e['d']} | **{e['a']}** | €{e['ek']:.0f}→€{e['vk']:.0f} | **+€{e['g']:.2f}** | {e['pl']}")
        if st.button("🤖 KI-Analyse",use_container_width=True,key="gb_ki"):
            with st.spinner("..."):
                log="\n".join([f"{e['a']}: EK{e['ek']} VK{e['vk']} G{e['g']} {e['pl']}" for e in st.session_state.gwlog])
                st.markdown(ki(f"Analysiere diese Verkaeufe. Auf Deutsch. 1.Bester ROI? 2.Beste Plattform? 3.Tipps?\n{log}"))

# ════════════════════════════════════════════════════════════
# TAB 19 — ANZEIGEN-KI
# ════════════════════════════════════════════════════════════
with T[18]:
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
        if ao_ti or ao_tx:
            with st.spinner("✨ ..."):
                r = ki(f"Verkaufsanzeigen-Experte fuer {ao_l}. Kategorie: {ao_k}. Preis: EUR{ao_p}. {ao_t2} Tage online.\n"
                       f"Titel: {ao_ti}\nBeschreibung: {ao_tx}\n"
                       f"Analysiere und verbessere. Auf Deutsch.\n"
                       f"1. Analyse (Note 1-10 + Schwaechen)\n"
                       f"2. NEUER TITEL (max 60 Zeichen, kopierfertig)\n"
                       f"3. NEUE BESCHREIBUNG (kopierfertig, alle Keywords)\n"
                       f"4. Preis-Empfehlung (jetzt EUR{ao_p} — besser: EUR?)\n"
                       f"5. Keywords fuer {ao_l}\n"
                       f"6. Tipps: Foto, Posting-Zeit, erwartete Verbesserung +X%")
                st.markdown(r)

# ════════════════════════════════════════════════════════════
# TAB 20 — TAGESPLAN
# ════════════════════════════════════════════════════════════
with T[19]:
    st.header("🗓️ Tagesplan Generator")
    c1,c2 = st.columns(2)
    with c1:
        tp_t = st.selectbox("Tag",["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"],key="tp_t")
        tp_b = st.number_input("Budget (€)",min_value=10.0,value=100.0,step=10.0,key="tp_b")
    with c2:
        tp_f = st.selectbox("Fokus",["Alles","Kleidung & Mode","Porzellan","Elektronik","Möbel","Bücher"],key="tp_f")
        tp_r = st.selectbox("Transport",["Auto","Fahrrad","U-Bahn/Bus","Zu Fuß"],key="tp_r")
    if st.button("🗓️ Tagesplan erstellen",type="primary",use_container_width=True,key="tp_btn"):
        with st.spinner("🤖 ..."):
            r = ki(f"Berliner Flohmarkt-Experte. Erstelle optimalen Tagesplan. Auf Deutsch.\n"
                   f"Tag: {tp_t} | Budget: EUR{tp_b} | Fokus: {tp_f} | Transport: {tp_r}\n"
                   f"1. ZEITPLAN: Tabelle mit Uhrzeit, Markt, Adresse, Warum\n"
                   f"2. BUDGET-AUFTEILUNG: Wie viel wo ausgeben?\n"
                   f"3. WAS SUCHEN bei {tp_f}: konkrete Artikel\n"
                   f"4. TRANSPORT-TIPP fuer {tp_r}\n"
                   f"5. ERWARTETES ERGEBNIS: EUR{tp_b} Budget → EUR X–Y Gewinn moeglich")
            st.markdown(r)

# ── FOOTER ──────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"<p style='text-align:center;color:#666'>⚡ MarktRadar OS PRO v5.0 · Zoran Berlin · {datetime.now().strftime('%d.%m.%Y')}</p>", unsafe_allow_html=True)
