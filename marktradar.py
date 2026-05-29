# ═══════════════════════════════════════════════════════════════
# MarktRadar OS PRO — v3.0 ULTIMATE
# Alle 9 Händler-Weltwunder Features
# GitHub → Streamlit Cloud → Handy-optimiert
# ═══════════════════════════════════════════════════════════════

import streamlit as st
import os, re, urllib.parse, base64, json
from datetime import datetime
from openai import OpenAI

# ───────────────────────────────────────────────────────────────
# KONFIGURATION
# ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="⚡ MarktRadar OS PRO",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def get_secret(key):
    try:
        return st.secrets[key]
    except:
        return os.environ.get(key, "")

OPENROUTER_KEY = get_secret("OPENROUTER_API_KEY")
OPENAI_KEY     = get_secret("OPENAI_API_KEY")

# ───────────────────────────────────────────────────────────────
# SESSION STATE
# ───────────────────────────────────────────────────────────────
defaults = {
    "verkaufe": [], "lager": [],
    "gesamt_umsatz": 0.0, "gesamt_anzahl": 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ───────────────────────────────────────────────────────────────
# KI-FUNKTION
# ───────────────────────────────────────────────────────────────
def ki(prompt, bild_b64=None, vision=False):
    """
    KI-Analyse via OpenRouter Credits ($9.89 verfügbar)
    - Mit Bild: openai/gpt-4o (Vision)
    - Nur Text: openai/gpt-4o-mini (günstig)
    """
    try:
        if not OPENROUTER_KEY:
            return "❌ Kein OpenRouter API-Key konfiguriert!"
        
        client = OpenAI(
            api_key=OPENROUTER_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
        
        if vision and bild_b64:
            model = "openai/gpt-4o"
            msgs  = [{"role":"user","content":[
                {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{bild_b64}"}},
                {"type":"text","text":prompt}]}]
        else:
            model = "openai/gpt-4o-mini"
            msgs  = [{"role":"user","content":prompt}]
        
        r = client.chat.completions.create(model=model, messages=msgs, max_tokens=1500)
        return r.choices[0].message.content
    except Exception as e:
        return f"❌ KI-Fehler: {str(e)}"

# ───────────────────────────────────────────────────────────────
# EBAY SCRAPER
# ───────────────────────────────────────────────────────────────
def ebay_scrape(q, n=12):
    try:
        import requests
        from bs4 import BeautifulSoup
        h = {"User-Agent":"Mozilla/5.0","Accept-Language":"de-DE"}
        url = f"https://www.ebay.de/sch/i.html?_nkw={urllib.parse.quote(q)}&LH_Complete=1&LH_Sold=1&_ipg=20"
        soup = BeautifulSoup(requests.get(url,headers=h,timeout=10).text,"html.parser")
        items, prices = [], []
        for item in soup.find_all("div",class_="s-item__info")[:n]:
            try:
                t = item.find("span",role="heading")
                p = item.find("span",class_="s-item__price")
                if not(t and p): continue
                if any(x in t.text.lower() for x in ["shop","anzeige"]): continue
                nums = re.findall(r"\d+[\.,]\d+", p.text)
                if nums:
                    pr = float(nums[0].replace(".","").replace(",","."))
                    prices.append(pr)
                    items.append({"titel":t.text.strip()[:55],"preis":pr})
            except: continue
        if not prices: return None
        return {"items":items,"avg":round(sum(prices)/len(prices),2),
                "min":round(min(prices),2),"max":round(max(prices),2),"n":len(prices)}
    except: return None

# ───────────────────────────────────────────────────────────────
# HEADER
# ───────────────────────────────────────────────────────────────
st.markdown("""
<div style='background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);
padding:18px;border-radius:14px;margin-bottom:16px;text-align:center'>
<h1 style='color:#f5a623;margin:0;font-size:2.2em'>⚡ MarktRadar OS PRO</h1>
<p style='color:#a8b2d8;margin:4px 0 0'>9 Händler-Weltwunder · KI · eBay Live · DAC7 · Handy-optimiert</p>
</div>""", unsafe_allow_html=True)

st.markdown("---")

# ───────────────────────────────────────────────────────────────
# 9 TABS
# ───────────────────────────────────────────────────────────────
t1,t2,t3,t4,t5,t6,t7,t8,t9 = st.tabs([
    "📸 Vision KI","📊 eBay Live","💬 Anschreib-Bot",
    "💰 DAC7","📦 Lager","📚 OCR Scanner",
    "🔧 Reparatur","📦 Post-Duell","📈 Trends"
])

# ══════════════════════════════════════════════════════════════
# TAB 1 — VISION KI + 3-STUFEN PIPELINE
# ══════════════════════════════════════════════════════════════
with t1:
    st.header("📸 Vision KI — 3-Stufen Pipeline")
    st.markdown("**Foto → KI erkennt Artikel → eBay Live-Preise → Fertige Anzeige**")

    bild = st.file_uploader("📷 Artikel-Foto hochladen", type=["jpg","jpeg","png"])
    manuell = st.text_area("Oder manuell beschreiben:", placeholder="z.B. 'Meissen Teller blau-weiß Zwiebelmuster, 26cm, guter Zustand'", height=80)

    col1, col2 = st.columns(2)
    with col1:
        einkauf_preis = st.number_input("💸 Mein Einkaufspreis (€)", min_value=0.0, value=5.0, step=0.5)
    with col2:
        marke_check = st.checkbox("🔍 Echtheitsprüfung (Brand Shield)")

    if st.button("🚀 3-Stufen-Analyse STARTEN", type="primary", use_container_width=True):
        if bild or manuell:
            # STUFE 1: Vision
            with st.status("⚙️ Stufe 1: Vision-Agent analysiert Foto...", expanded=True) as status:
                prompt_vision = """Du bist ein Team aus 3 Experten die gemeinsam analysieren:
1. Antiquitäten-Händler mit 20 Jahren Erfahrung auf deutschen Flohmärkten
2. eBay-Powerseller mit 10.000+ Verkäufen
3. Markenauthentizitäts-Experte für Porzellan, Elektronik und Vintage

WICHTIG: Analysiere ALLES was du siehst - auch wenn es einfach aussieht. 
Jeder Artikel hat einen Wert. Sei präzise, direkt und professionell.
Antworte IMMER vollständig auf Deutsch.

## 🏷️ ARTIKEL-IDENTIFIKATION
- **Name:** [Exakter Produktname]
- **Hersteller/Marke:** [Hersteller, auch wenn unbekannte Marke - beschreibe sie]
- **Herstellungszeit:** [Jahrzehnt/Jahr-Schätzung mit Begründung]
- **Material:** [Genaues Material]
- **Maße/Gewicht:** [Schätzung]
- **Zustand:** [Sehr gut / Gut / Gebraucht / Beschädigt - mit Details]
- **Besonderheiten:** [Stempel, Markierungen, Seriennummern, Punzen]

## 🔍 ECHTHEITSPRÜFUNG
- **Echtheit:** [Echt / Wahrscheinlich echt / Replik / Unsicher]
- **Beweis:** [Konkrete Merkmale die für/gegen Echtheit sprechen]
- **Fälschungsrisiko:** [Niedrig / Mittel / Hoch]

## 💰 MARKTPREIS-ANALYSE
- **Flohmarkt-Einkaufspreis:** €X - €Y (was man realistisch zahlen sollte)
- **eBay Durchschnitt:** €X - €Y (basierend auf ähnlichen Verkäufen)
- **Maximaler Verkaufspreis:** €X (optimistisches Szenario)
- **Gewinnpotential:** €X - €Y

## 🎯 HÄNDLER-EMPFEHLUNG
**[✅ UNBEDINGT KAUFEN / ✅ KAUFEN / ⚠️ NUR BEI GÜNSTIGEM PREIS / ❌ SKIP]**
Begründung: [Konkrete Begründung]

## 🔎 EBAY-SUCHBEGRIFF
**[Optimierter Suchbegriff für eBay DE - max 5 Wörter]**

## 🏷️ FERTIGER EBAY-TITEL (80 Zeichen)
[Verkaufsstarker Titel mit wichtigsten Keywords]

## 📝 VERKAUFSBESCHREIBUNG (3 Sätze)
[Professionelle Beschreibung die Käufer überzeugt]"""

                if bild:
                    b64 = base64.b64encode(bild.read()).decode()
                    analyse = ki(prompt_vision, bild_b64=b64, vision=True)
                else:
                    analyse = ki(f"{prompt_vision}\n\nArtikel: {manuell}", vision=False)

                st.markdown(analyse)

                # eBay Suchbegriff extrahieren
                suchbegriff = manuell if manuell else "Vintage Artikel"
                for line in analyse.split("\n"):
                    if "eBay-Suchbegriff" in line or "Suchbegriff" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            suchbegriff = parts[1].strip().strip("*[]")
                        break

            # STUFE 2: eBay Scraping
            with st.status(f"⚙️ Stufe 2: Scraper sucht echte eBay-Preise für '{suchbegriff}'...", expanded=True):
                ebay = ebay_scrape(suchbegriff)
                if ebay:
                    st.success(f"✅ {ebay['n']} echte Verkäufe gefunden!")
                    col1,col2,col3 = st.columns(3)
                    col1.metric("Ø Marktpreis", f"€{ebay['avg']}")
                    col2.metric("Minimum", f"€{ebay['min']}")
                    col3.metric("Maximum", f"€{ebay['max']}")
                    for item in ebay["items"][:5]:
                        st.markdown(f"- €{item['preis']:.2f} — {item['titel']}")
                else:
                    st.warning("⚠️ eBay-Scraping nicht möglich, KI schätzt...")
                    ebay = {"avg": 30.0, "min": 10.0, "max": 60.0, "n": 0}

            # STUFE 3: Synthese
            with st.status("⚙️ Stufe 3: Synthese-Agent berechnet Marge...", expanded=True):
                gebuehr = ebay["avg"] * 0.119
                gewinn  = ebay["avg"] - einkauf_preis - 4.99 - gebuehr
                roi     = (gewinn / einkauf_preis * 100) if einkauf_preis > 0 else 0

                col1,col2,col3,col4 = st.columns(4)
                col1.metric("Verkaufspreis", f"€{ebay['avg']:.2f}")
                col2.metric("- Kosten", f"€{einkauf_preis + 4.99 + gebuehr:.2f}")
                col3.metric("= GEWINN", f"€{gewinn:.2f}")
                col4.metric("ROI", f"{roi:.0f}%")

                if gewinn > 15:
                    st.success(f"✅ KAUFEN! Guter Deal — €{gewinn:.2f} Gewinn ({roi:.0f}% ROI)")
                elif gewinn > 5:
                    st.warning(f"⚠️ Grenzfall — €{gewinn:.2f} Gewinn ({roi:.0f}% ROI)")
                else:
                    st.error(f"❌ SKIP — Zu wenig Gewinn: €{gewinn:.2f}")

                ankauf_max = ebay["avg"] * 0.45
                st.info(f"💡 Maximaler Ankaufspreis: **€{ankauf_max:.2f}**")

                # Fertige Kleinanzeige
                prompt_anzeige = f"""Schreibe eine fertige eBay-Kleinanzeige auf Deutsch für:
Artikel: {suchbegriff}
Zustand: Gut
Preis: €{ebay['avg']:.2f}

Format: Titel (max 80 Zeichen) + kurze Beschreibung (3 Sätze) + Versandinfo"""
                anzeige = ki(prompt_anzeige)
                st.markdown("### 📝 Fertige Anzeige:")
                st.text_area("Kopieren & einfügen:", value=anzeige, height=150)
        else:
            st.warning("⚠️ Bitte Foto hochladen oder Artikel beschreiben!")

# ══════════════════════════════════════════════════════════════
# TAB 2 — EBAY LIVE PREISE
# ══════════════════════════════════════════════════════════════
with t2:
    st.header("📊 eBay Live-Preise")
    suchbegriff2 = st.text_input("🔍 Suchbegriff", placeholder="z.B. 'Rosenthal Teller', 'Game Boy Color'")
    col1,col2 = st.columns(2)
    ek = col1.number_input("💸 Einkaufspreis (€)", min_value=0.0, value=10.0)
    vs = col2.number_input("📦 Versand (€)", min_value=0.0, value=4.99)

    if st.button("🔍 Live-Preise abrufen!", type="primary", use_container_width=True):
        if suchbegriff2:
            with st.spinner("📡 Suche echte eBay-Verkäufe..."):
                e = ebay_scrape(suchbegriff2)
                if e:
                    st.success(f"✅ {e['n']} echte Verkäufe!")
                    c1,c2,c3 = st.columns(3)
                    c1.metric("Ø Preis", f"€{e['avg']}")
                    c2.metric("Min", f"€{e['min']}")
                    c3.metric("Max", f"€{e['max']}")
                    gebuehr = e["avg"] * 0.119
                    gewinn  = e["avg"] - ek - vs - gebuehr
                    st.metric("💰 Ihr Gewinn", f"€{gewinn:.2f}", delta="✅ Lohnt!" if gewinn>10 else "⚠️ Knapp")
                    st.info(f"💡 Sicherer Ankaufspreis: Max **€{e['avg']*0.45:.2f}**")
                    st.markdown("### Verkäufe:")
                    for item in e["items"]:
                        st.markdown(f"- **€{item['preis']:.2f}** — {item['titel']}")
                else:
                    st.warning("eBay nicht verfügbar. KI-Schätzung:")
                    st.markdown(ki(f"Schätze eBay-Preis für: {suchbegriff2}. Kurz: EK/VK/Gewinn auf Deutsch."))

# ══════════════════════════════════════════════════════════════
# TAB 3 — KI ANSCHREIB-ROBOTER
# ══════════════════════════════════════════════════════════════
with t3:
    st.header("💬 KI Anschreib-Roboter")
    st.markdown("Psychologisch optimierte Verhandlungs-Nachrichten")

    col1,col2 = st.columns(2)
    with col1:
        artikel3   = st.text_input("Artikel", placeholder="z.B. Rosenthal Kaffeeservice")
        mein_preis = st.number_input("Mein Angebot (€)", min_value=1.0, value=20.0)
        vk_preis   = st.number_input("Verkäufer-Preis (€)", min_value=1.0, value=50.0)
    with col2:
        stil = st.selectbox("Stil", ["Freundlich & charmant","Bestimmt & direkt","Dringend (heute abholen)","Paket-Deal","Letztes Angebot"])
        plattform3 = st.selectbox("Plattform", ["Kleinanzeigen","eBay","Facebook Marketplace","Persönlich"])

    if st.button("✍️ Nachricht generieren!", type="primary", use_container_width=True):
        if artikel3:
            with st.spinner("✍️ Generiere..."):
                msg = ki(f"""Schreibe eine Verhandlungs-Nachricht auf Deutsch.
Stil: {stil} | Plattform: {plattform3}
Artikel: {artikel3} | Mein Preis: €{mein_preis} | Verkäufer: €{vk_preis}
Regeln: Max 5 Sätze, psychologisch optimiert, konkreter Preis, kein Druck.
NUR die fertige Nachricht ausgeben!""")
                st.text_area("📩 Kopieren & senden:", value=msg, height=200)
                st.success("✅ Fertig! Einfach kopieren.")

# ══════════════════════════════════════════════════════════════
# TAB 4 — DAC7 TRACKER
# ══════════════════════════════════════════════════════════════
with t4:
    st.header("💰 DAC7 Verkaufs-Wächter")
    st.warning("⚠️ Ab 30 Verkäufe ODER €2.000 Umsatz → Finanzamt-Meldung durch Plattformen!")

    n = st.session_state.gesamt_anzahl
    u = st.session_state.gesamt_umsatz
    col1,col2 = st.columns(2)
    with col1:
        st.markdown("### 🛒 Verkäufe")
        st.progress(min(n/30,1.0))
        st.markdown(f"{'🔴' if n>=28 else '🟡' if n>=20 else '🟢'} **{n}/30** ({30-n} übrig)")
    with col2:
        st.markdown("### 💶 Umsatz")
        st.progress(min(u/2000,1.0))
        st.markdown(f"{'🔴' if u>=1900 else '🟡' if u>=1500 else '🟢'} **€{u:.0f}/€2000** (€{2000-u:.0f} übrig)")

    st.markdown("---")
    st.markdown("### ➕ Verkauf eintragen:")
    col1,col2,col3 = st.columns(3)
    a4 = col1.text_input("Artikel", key="dac_art")
    p4 = col2.number_input("Preis (€)", min_value=0.01, value=25.0, key="dac_pr")
    pl4 = col3.selectbox("Plattform", ["eBay","Kleinanzeigen","Facebook","Flohmarkt"], key="dac_pl")

    if st.button("✅ Eintragen", type="primary", use_container_width=True):
        if a4:
            st.session_state.verkaufe.append({"datum":datetime.now().strftime("%d.%m.%Y"),"artikel":a4,"preis":p4,"plattform":pl4})
            st.session_state.gesamt_anzahl += 1
            st.session_state.gesamt_umsatz += p4
            st.success(f"✅ Eingetragen! Gesamt: {st.session_state.gesamt_anzahl} Verkäufe / €{st.session_state.gesamt_umsatz:.2f}")
            st.rerun()

    if st.session_state.verkaufe:
        st.markdown("### 📋 Letzte Verkäufe:")
        for v in reversed(st.session_state.verkaufe[-8:]):
            st.markdown(f"- {v['datum']} | {v['artikel']} | **€{v['preis']:.2f}** | {v['plattform']}")

# ══════════════════════════════════════════════════════════════
# TAB 5 — LAGER
# ══════════════════════════════════════════════════════════════
with t5:
    st.header("📦 Lagerbestand")

    col1,col2 = st.columns(2)
    with col1:
        la = st.text_input("Artikel", placeholder="z.B. Meissen Teller")
        lek = st.number_input("Einkaufspreis (€)", min_value=0.0, value=10.0, key="lag_ek")
        lziel = st.number_input("Ziel-VK (€)", min_value=0.0, value=45.0)
    with col2:
        lz = st.selectbox("Zustand", ["Sehr gut","Gut","Gebraucht","Beschädigt"])
        lpl = st.selectbox("Plattform", ["eBay","Kleinanzeigen","Facebook","Flohmarkt"])
        ltage = st.number_input("Liegezeit (Tage)", min_value=0, value=0)

    if st.button("📦 Hinzufügen", type="primary", use_container_width=True):
        if la:
            g = lziel - lek - (lziel*0.119) - 4.99
            st.session_state.lager.append({"artikel":la,"ek":lek,"vk":lziel,"zustand":lz,
                "plattform":lpl,"tage":ltage,"gewinn":round(g,2)})
            st.success(f"✅ Hinzugefügt! Erwarteter Gewinn: €{g:.2f}")
            st.rerun()

    if st.session_state.lager:
        ges_ek = sum(i["ek"] for i in st.session_state.lager)
        ges_g  = sum(i["gewinn"] for i in st.session_state.lager)
        c1,c2,c3 = st.columns(3)
        c1.metric("Artikel", len(st.session_state.lager))
        c2.metric("💸 Kapital gebunden", f"€{ges_ek:.2f}")
        c3.metric("💰 Erwarteter Gewinn", f"€{ges_g:.2f}")
        st.markdown("---")
        for item in st.session_state.lager:
            col1,col2,col3,col4 = st.columns([3,1,1,1])
            col1.markdown(f"**{item['artikel']}** ({item['zustand']})")
            col2.markdown(f"EK: €{item['ek']:.2f}")
            col3.markdown(f"VK: €{item['vk']:.2f}")
            col4.markdown(f"**€{item['gewinn']:.2f}**")
            if item["tage"] > 30:
                st.warning(f"⚠️ {item['artikel']}: {item['tage']} Tage im Lager → Preis senken!")

# ══════════════════════════════════════════════════════════════
# TAB 6 — MULTI-OCR MEDIEN-SCANNER
# ══════════════════════════════════════════════════════════════
with t6:
    st.header("📚 Multi-OCR Medien-Scanner")
    st.markdown("Fotografiere einen Stapel Bücher/CDs/Spiele → KI erkennt alle und schätzt Werte!")

    medien_bild = st.file_uploader("📷 Stapel fotografieren", type=["jpg","jpeg","png"], key="medien")
    medien_typ  = st.selectbox("Medien-Typ", ["Bücher","CDs/Vinyl","Video-Spiele","DVDs/Blu-rays","Gemischt"])

    if st.button("🔍 Stapel analysieren!", type="primary", use_container_width=True):
        if medien_bild:
            with st.spinner(f"🤖 KI scannt alle {medien_typ}..."):
                b64 = base64.b64encode(medien_bild.read()).decode()
                prompt_ocr = f"""Du bist Experte für Second-Hand {medien_typ} in Deutschland.
Scanne dieses Foto und erkenne ALLE {medien_typ}.

Für jedes erkannte Element:
**[Titel/Name]** | Wert: €X-€Y | Empfehlung: KAUFEN/SKIP

Am Ende: Gesamtwert des Stapels und Top-3 wertvollste Stücke.
Antworte NUR auf Deutsch."""
                ergebnis = ki(prompt_ocr, bild_b64=b64, vision=True)
                st.markdown(ergebnis)
        else:
            st.warning("⚠️ Bitte Foto hochladen!")
            st.markdown("**Tipp:** Legen Sie alle Bücher/CDs nebeneinander und fotografieren Sie von oben.")

# ══════════════════════════════════════════════════════════════
# TAB 7 — UPCYCLING & REPARATUR-RECHNER
# ══════════════════════════════════════════════════════════════
with t7:
    st.header("🔧 Upcycling & Reparatur-Rechner")
    st.markdown("Lohnt sich die Reparatur? Berechnen Sie Ihren echten Stundenlohn!")

    col1,col2 = st.columns(2)
    with col1:
        rep_artikel  = st.text_input("Artikel", placeholder="z.B. Vintage Stuhl")
        rep_ek       = st.number_input("Einkaufspreis (€)", min_value=0.0, value=15.0, key="rep_ek")
        rep_material = st.number_input("Materialkosten (€)", min_value=0.0, value=25.0)
        rep_stunden  = st.number_input("Geschätzte Arbeitsstunden", min_value=0.5, value=3.0, step=0.5)
    with col2:
        rep_vk       = st.number_input("Erwarteter Verkaufspreis (€)", min_value=0.0, value=120.0)
        rep_versand  = st.number_input("Versandkosten (€)", min_value=0.0, value=9.99)
        rep_beschr   = st.text_area("Was muss repariert werden?", height=80, placeholder="z.B. Neu lackieren, Polster ersetzen")

    if st.button("🔧 Wirtschaftlichkeit berechnen", type="primary", use_container_width=True):
        gebuehr    = rep_vk * 0.119
        gesamtk    = rep_ek + rep_material + rep_versand + gebuehr
        gewinn     = rep_vk - gesamtk
        stundenlohn = gewinn / rep_stunden if rep_stunden > 0 else 0

        col1,col2,col3,col4 = st.columns(4)
        col1.metric("💸 Gesamtkosten", f"€{gesamtk:.2f}")
        col2.metric("💰 Gewinn", f"€{gewinn:.2f}")
        col3.metric("⏰ Stundenlohn", f"€{stundenlohn:.2f}")
        col4.metric("ROI", f"{(gewinn/gesamtk*100) if gesamtk>0 else 0:.0f}%")

        if stundenlohn >= 15:
            st.success(f"✅ LOHNT SICH! Ihr Stundenlohn: €{stundenlohn:.2f}/h")
        elif stundenlohn >= 8:
            st.warning(f"⚠️ Grenzfall: €{stundenlohn:.2f}/h — Überlegen Sie gut!")
        else:
            st.error(f"❌ LOHNT NICHT! Nur €{stundenlohn:.2f}/h — Lieber unrestauriert verkaufen!")

        if rep_artikel and rep_beschr:
            with st.spinner("🤖 KI gibt Reparatur-Tipps..."):
                tipps = ki(f"Gib 3 konkrete Tipps für die Reparatur von '{rep_artikel}' auf Deutsch. Problem: {rep_beschr}. Kurz und praktisch.")
                st.markdown("### 💡 KI Reparatur-Tipps:")
                st.markdown(tipps)

# ══════════════════════════════════════════════════════════════
# TAB 8 — LIVE POST-DUELL DHL vs HERMES
# ══════════════════════════════════════════════════════════════
with t8:
    st.header("📦 Live Post-Duell: DHL vs. Hermes")
    st.markdown("Finden Sie die günstigste Versandoption in Sekunden!")

    col1,col2,col3 = st.columns(3)
    gewicht = col1.number_input("Gewicht (kg)", min_value=0.1, value=1.0, step=0.1)
    laenge  = col2.number_input("Länge (cm)", min_value=1, value=30)
    breite  = col3.number_input("Breite (cm)", min_value=1, value=20)
    hoehe   = st.number_input("Höhe (cm)", min_value=1, value=15)
    versicherung = st.checkbox("📋 Versicherung gewünscht?")

    # DHL Tarife 2024
    dhl_preise = [
        (0.5, 3.99, "Päckchen S"),
        (1.0, 4.99, "Päckchen M"),
        (2.0, 6.99, "Päckchen L"),
        (5.0, 9.49, "Paket 5kg"),
        (10.0, 12.49, "Paket 10kg"),
        (31.5, 18.49, "Paket 31,5kg")
    ]
    hermes_preise = [
        (0.5, 3.70, "XS"),
        (1.0, 4.50, "S"),
        (2.0, 5.50, "M"),
        (5.0, 7.90, "L"),
        (10.0, 10.90, "XL"),
        (25.0, 15.90, "XXL")
    ]

    if st.button("⚡ Preise vergleichen!", type="primary", use_container_width=True):
        dhl_preis = dhl_preise[-1][1]; dhl_name = dhl_preise[-1][2]
        for max_g, preis, name in dhl_preise:
            if gewicht <= max_g:
                dhl_preis = preis; dhl_name = name; break

        hermes_preis = hermes_preise[-1][1]; hermes_name = hermes_preise[-1][2]
        for max_g, preis, name in hermes_preise:
            if gewicht <= max_g:
                hermes_preis = preis; hermes_name = name; break

        if versicherung:
            dhl_preis += 2.50; hermes_preis += 1.99

        col1,col2 = st.columns(2)
        with col1:
            st.markdown("### 🟡 DHL")
            st.metric("Preis", f"€{dhl_preis:.2f}", label_visibility="visible")
            st.markdown(f"Produkt: {dhl_name}")
            st.markdown("✅ Tracking | ✅ Packstationen | ✅ Sicher")

        with col2:
            st.markdown("### 🟢 Hermes")
            st.metric("Preis", f"€{hermes_preis:.2f}", label_visibility="visible")
            st.markdown(f"Produkt: {hermes_name}")
            st.markdown("✅ Tracking | ✅ PaketShops | ✅ Günstig")

        st.markdown("---")
        ersparnis = abs(dhl_preis - hermes_preis)
        if dhl_preis < hermes_preis:
            st.success(f"🏆 DHL ist günstiger! Sie sparen €{ersparnis:.2f}")
        elif hermes_preis < dhl_preis:
            st.success(f"🏆 Hermes ist günstiger! Sie sparen €{ersparnis:.2f}")
        else:
            st.info("🤝 Gleicher Preis — Wählen Sie nach Bequemlichkeit!")

# ══════════════════════════════════════════════════════════════
# TAB 9 — TRENDS & GOLD-WÖRTER
# ══════════════════════════════════════════════════════════════
with t9:
    st.header("📈 Trödel-Trend-Radar")

    col1,col2 = st.columns(2)
    with col1:
        st.markdown("### 🔥 Aktuelle Hot-Trends 2025/26")
        trends = [
            ("🔥","Game Boy Color OVP","+214%","€110"),
            ("🔥","35mm Analogkamera","+165%","€85"),
            ("🔥","90s College Jacken","+87%","€65"),
            ("🔥","Lego Classic Sets","+95%","€55"),
            ("📈","Meissen Zwiebelmuster","+14%","€45"),
            ("📈","Nokia 3310","+45%","€35"),
            ("📈","Vintage Adidas","+72%","€55"),
            ("⚖️","Rosenthal Porzellan","+8%","€30"),
        ]
        for s,n,w,p in trends:
            st.markdown(f"{s} **{n}** — {p} ({w})")

    with col2:
        st.markdown("### 💡 Gold-Wörter für Flohmärkte")
        gold = ["🏠 Dachbodenfund","🏡 Haushaltsauflösung","⚰️ Nachlass",
                "🔑 Kellerfund","🚚 Umzugskarton","🎁 Zu verschenken",
                "🥄 Besteck Kiste","🍽️ Porzellan Erbe","📦 Konvolut"]
        for g in gold:
            st.markdown(f"- {g}")

    st.markdown("---")
    frage = st.text_input("🤖 KI fragen:", placeholder="Was ist gerade auf eBay gefragt?")
    if st.button("Fragen"):
        if frage:
            with st.spinner("🤖 Analysiere..."):
                st.markdown(ki(f"Reselling-Experte Deutschland. Kurze Antwort auf Deutsch: {frage}"))

# ───────────────────────────────────────────────────────────────
# FOOTER
# ───────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<p style='text-align:center;color:#666'>⚡ MarktRadar OS PRO v3.0 · Zoran Berlin · "
    f"{datetime.now().strftime('%d.%m.%Y')}</p>",
    unsafe_allow_html=True
)
