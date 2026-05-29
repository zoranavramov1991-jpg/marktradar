# ═══════════════════════════════════════════════════════════════
# MarktRadar OS PRO — v4.0 ULTIMATE
# Für Zoran Berlin — Flohmarkt & Reselling Profi
# Plattformen: Kleinanzeigen · Vinted · Facebook · Flohmärkte
# ═══════════════════════════════════════════════════════════════

import streamlit as st
import os, re, base64, json, urllib.parse
from datetime import datetime
from openai import OpenAI
import requests

st.set_page_config(
    page_title="⚡ MarktRadar OS PRO",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ───────────────────────────────────────────────────────────────
# API SETUP
# ───────────────────────────────────────────────────────────────
def get_secret(key):
    try:
        return st.secrets[key]
    except:
        return os.environ.get(key, "")

OPENROUTER_KEY = get_secret("OPENROUTER_API_KEY")

# ───────────────────────────────────────────────────────────────
# SESSION STATE
# ───────────────────────────────────────────────────────────────
for k, v in {"verkaufe": [], "lager": [], "umsatz": 0.0, "anzahl": 0}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ───────────────────────────────────────────────────────────────
# KI ENGINE — OpenRouter Credits
# ───────────────────────────────────────────────────────────────
def ki(prompt, bild_b64=None):
    try:
        if not OPENROUTER_KEY:
            return "❌ Kein API-Key konfiguriert!"
        client = OpenAI(api_key=OPENROUTER_KEY, base_url="https://openrouter.ai/api/v1")
        if bild_b64:
            model = "openai/gpt-4o"
            msgs  = [{"role":"user","content":[
                {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{bild_b64}","detail":"high"}},
                {"type":"text","text":prompt}]}]
        else:
            model = "openai/gpt-4o-mini"
            msgs  = [{"role":"user","content":prompt}]
        r = client.chat.completions.create(model=model, messages=msgs, max_tokens=2000)
        return r.choices[0].message.content
    except Exception as e:
        return f"❌ KI-Fehler: {str(e)}"

# ───────────────────────────────────────────────────────────────
# URL AUSLESEN
# ───────────────────────────────────────────────────────────────
def url_auslesen(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "de-DE,de;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        
        # Entferne Scripts & Styles
        for tag in soup(["script","style","nav","footer","header"]):
            tag.decompose()
        
        text = soup.get_text(separator="\n", strip=True)
        # Nur relevante Zeilen behalten
        zeilen = [z.strip() for z in text.split("\n") if len(z.strip()) > 15]
        inhalt = "\n".join(zeilen[:150])
        
        # Bilder finden
        bilder = []
        for img in soup.find_all("img", src=True)[:5]:
            src = img["src"]
            if src.startswith("http"):
                bilder.append(src)
            elif src.startswith("//"):
                bilder.append("https:" + src)
        
        return {"text": inhalt[:4000], "bilder": bilder, "ok": True}
    except Exception as e:
        return {"text": "", "bilder": [], "ok": False, "fehler": str(e)}

# ───────────────────────────────────────────────────────────────
# HEADER
# ───────────────────────────────────────────────────────────────
st.markdown("""
<div style='background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);
padding:20px;border-radius:14px;margin-bottom:20px;text-align:center'>
<h1 style='color:#f5a623;margin:0;font-size:2.2em'>⚡ MarktRadar OS PRO</h1>
<p style='color:#a8b2d8;margin:6px 0 0'>
Kleinanzeigen · Vinted · Facebook · eBay · Flohmärkte · Auktionen
</p>
</div>""", unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────
# TABS
# ───────────────────────────────────────────────────────────────
t1, t2, t3, t4, t5, t6, t7, t8 = st.tabs([
    "🔍 Artikel Analyse",
    "💬 Anschreib-Bot",
    "💰 DAC7",
    "📦 Lager",
    "📚 OCR Scanner",
    "🔧 Reparatur",
    "📦 Post-Duell",
    "📈 Trends"
])

# ══════════════════════════════════════════════════════════════
# TAB 1 — HAUPT-ANALYSE (Foto + URL)
# ══════════════════════════════════════════════════════════════
with t1:
    st.header("🔍 Artikel-Analyse")
    st.markdown("**Foto hochladen ODER Link eingeben → Vollständige Experten-Analyse**")

    eingabe_typ = st.radio(
        "Was möchten Sie analysieren?",
        ["📸 Foto hochladen", "🔗 Link eingeben", "📸 + 🔗 Beides"],
        horizontal=True
    )

    bild_input = None
    url_input  = None

    if eingabe_typ in ["📸 Foto hochladen", "📸 + 🔗 Beides"]:
        bild_input = st.file_uploader(
            "📷 Artikel-Foto hochladen (auch mehrere möglich)",
            type=["jpg","jpeg","png","webp"],
            accept_multiple_files=False
        )

    if eingabe_typ in ["🔗 Link eingeben", "📸 + 🔗 Beides"]:
        url_input = st.text_input(
            "🔗 Link eingeben",
            placeholder="z.B. https://luedtke-auktion-online.de/auktion/238/283488/ oder Kleinanzeigen-Link"
        )

    if st.button("🚀 VOLLANALYSE STARTEN", type="primary", use_container_width=True):
        if bild_input or url_input:

            artikel_info = ""
            bild_b64     = None

            # ── STUFE 1: Daten sammeln ──
            with st.status("📡 Stufe 1: Daten werden gesammelt...", expanded=True):

                if url_input:
                    st.write(f"🌐 Lese URL aus: {url_input}")
                    seite = url_auslesen(url_input)
                    if seite["ok"]:
                        artikel_info = seite["text"]
                        st.success(f"✅ Seite ausgelesen! {len(artikel_info)} Zeichen gefunden")
                        if seite["bilder"]:
                            st.write(f"📷 {len(seite['bilder'])} Bilder gefunden")
                    else:
                        st.warning(f"⚠️ URL konnte nicht ausgelesen werden: {seite.get('fehler','')}")

                if bild_input:
                    bild_b64 = base64.b64encode(bild_input.read()).decode()
                    st.success("✅ Foto geladen & bereit für KI-Analyse")

            # ── STUFE 2: KI Experten-Analyse ──
            with st.status("🤖 Stufe 2: Experten-KI analysiert jeden Detail...", expanded=True):

                kontext = f"\n\nZUSATZ-INFO VON DER WEBSEITE:\n{artikel_info[:2000]}" if artikel_info else ""

                prompt_analyse = f"""Du bist ein neutrales Analyse-System für einen deutschen Reselling-Profi.

DEINE AUFGABE: Reine Fakten liefern. Keine Empfehlungen. Keine Ratschläge.
Der Händler entscheidet selbst was er kauft oder verkauft.
Identifiziere und bewerte JEDEN einzelnen sichtbaren Artikel im Bild.
NIEMALS "kann nicht analysieren" - jeden Gegenstand beschreiben.
Nur auf Deutsch. Konkrete Eurobeträge immer angeben.{kontext}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ARTIKEL-ANALYSE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Für JEDEN sichtbaren Artikel:

---
**[Artikel-Name]**
- Was: [Genaue Beschreibung, Material, Größe]
- Marke: [Markenname oder "keine Marke erkennbar"]
- Hergestellt: [Jahrzehnt/Epoche]
- Zustand: [Sehr gut / Gut / Gebraucht / Beschädigt]
- Echtheit: [Echt / Wahrscheinlich echt / Unsicher / Replik]
- Besonderheiten: [Stempel, Logos, Seriennummern, Punzen]

💶 MARKTPREISE:
| Plattform | Preis |
|-----------|-------|
| eBay DE | €X – €Y |
| Kleinanzeigen | €X – €Y |
| Vinted | €X – €Y |
| Facebook | €X – €Y |
| Flohmarkt | €X – €Y |
| Ankaufspreis max. | €X |

---

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GESAMT-ÜBERSICHT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Anzahl Artikel: [X]
- Gesamtwert (Verkauf): €X – €Y
- Gesamter Ankaufspreis max.: €X
- Bester Einzelartikel: [Name] (€X)
- Schwächster Artikel: [Name] (€X)"""

                analyse = ki(prompt_analyse, bild_b64=bild_b64)
                st.markdown(analyse)
                st.session_state["letzte_analyse"] = analyse

            # ── STUFE 3: Preisrecherche ──
            with st.status("📊 Stufe 3: Preise auf deutschen Plattformen recherchieren...", expanded=True):

                # Suchbegriff aus Analyse extrahieren
                suchbegriff = "Vintage Artikel"
                for line in analyse.split("\n"):
                    if "**Name:**" in line or "Name:" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            suchbegriff = parts[1].strip().strip("*[] ")[:40]
                        break

                # Kleinanzeigen Suche
                ka_url = f"https://www.kleinanzeigen.de/s-{urllib.parse.quote(suchbegriff)}/k0"
                vinted_url = f"https://www.vinted.de/catalog?search_text={urllib.parse.quote(suchbegriff)}"
                fb_url = f"https://www.facebook.com/marketplace/search/?query={urllib.parse.quote(suchbegriff)}"

                ebay_url = f"https://www.ebay.de/sch/i.html?_nkw={urllib.parse.quote(suchbegriff)}&LH_Complete=1&LH_Sold=1"
                st.markdown(f"""
### 🔗 Direkte Suche-Links für: **{suchbegriff}**

| Plattform | Link |
|-----------|------|
| 🛒 eBay (beendete Verkäufe) | [Jetzt suchen →]({ebay_url}) |
| 📱 Kleinanzeigen | [Jetzt suchen →]({ka_url}) |
| 👗 Vinted | [Jetzt suchen →]({vinted_url}) |
| 👥 Facebook | [Jetzt suchen →]({fb_url}) |
""")

                # KI Preisrecherche
                preis_analyse = ki(f"""Als Reselling-Experte für deutsche Plattformen:
Recherchiere realistische Preise für: "{suchbegriff}"
Alle Plattformen: eBay, Kleinanzeigen, Vinted, Facebook Marketplace, Flohmärkte.

Antworte kurz auf Deutsch:
- eBay Ø (beendete Verkäufe): €X
- Kleinanzeigen Ø: €X
- Vinted Ø: €X  
- Facebook Ø: €X
- Flohmarkt: €X
- Empfohlener Ankaufspreis: max €X
- Notiz: [Besonderheit falls relevant]""")

                st.markdown("### 💡 KI Preiseinschätzung:")
                st.markdown(preis_analyse)

            # ── STUFE 4: Fazit ──
            with st.status("✅ Stufe 4: Ultimatives Fazit...", expanded=True):
                fazit = ki(f"""Basierend auf dieser Artikel-Analyse:
{analyse[:500]}

Erstelle eine kurze ZUSAMMENFASSUNG (3 Punkte, keine Empfehlungen):
1. Welche Artikel haben den höchsten Marktwert?
2. Auf welchen Plattformen werden solche Artikel gehandelt?
3. Welche Artikel sind selten/begehrt auf dem deutschen Markt?

Nur Fakten, keine Ratschläge. Auf Deutsch.""")

                st.info(f"📊 **ZUSAMMENFASSUNG:** {fazit}")

        else:
            st.warning("⚠️ Bitte Foto hochladen oder Link eingeben!")

# ══════════════════════════════════════════════════════════════
# TAB 2 — ANSCHREIB-BOT
# ══════════════════════════════════════════════════════════════
with t2:
    st.header("💬 Anschreib-Roboter")
    st.markdown("Psychologisch optimierte Verhandlungs-Nachrichten")

    col1, col2 = st.columns(2)
    with col1:
        artikel3   = st.text_input("Artikel", placeholder="z.B. Vintage Stuhl", key="anschreib_art")
        mein_preis = st.number_input("Mein Angebot (€)", min_value=1.0, value=20.0, key="anschreib_mein")
        vk_preis   = st.number_input("Verkäufer-Preis (€)", min_value=1.0, value=50.0, key="anschreib_vk")
    with col2:
        stil = st.selectbox("Stil", [
            "Freundlich & charmant",
            "Bestimmt & direkt",
            "Dringend (heute abholen)",
            "Paket-Deal (mehrere Artikel)",
            "Letztes Angebot"
        ], key="anschreib_stil")
        plattform3 = st.selectbox("Plattform", [
            "Kleinanzeigen",
            "eBay",
            "Facebook Marketplace",
            "Vinted",
            "Persönlich auf Flohmarkt"
        ], key="anschreib_pl")

    if st.button("✍️ Nachricht generieren!", type="primary", use_container_width=True):
        if artikel3:
            with st.spinner("✍️ Generiere..."):
                msg = ki(f"""Schreibe eine Verhandlungs-Nachricht auf Deutsch.
Stil: {stil} | Plattform: {plattform3}
Artikel: {artikel3} | Mein Preis: €{mein_preis} | Verkäufer: €{vk_preis}
Regeln: Max 5 Sätze, psychologisch optimiert, konkreter Preis, freundlich aber bestimmt.
NUR die fertige Nachricht ausgeben!""")
                st.text_area("📩 Kopieren & senden:", value=msg, height=200)
                st.success("✅ Fertig! Einfach kopieren.")

# ══════════════════════════════════════════════════════════════
# TAB 3 — DAC7 TRACKER
# ══════════════════════════════════════════════════════════════
with t3:
    st.header("💰 DAC7 Steuer-Wächter")
    st.warning("⚠️ Ab 30 Verkäufe ODER €2.000 → Finanzamt-Meldung durch Plattformen!")

    n = st.session_state.anzahl
    u = st.session_state.umsatz

    col1, col2 = st.columns(2)
    with col1:
        st.progress(min(n/30, 1.0))
        st.markdown(f"{'🔴' if n>=28 else '🟡' if n>=20 else '🟢'} **{n}/30 Verkäufe** ({30-n} übrig)")
    with col2:
        st.progress(min(u/2000, 1.0))
        st.markdown(f"{'🔴' if u>=1900 else '🟡' if u>=1500 else '🟢'} **€{u:.0f}/€2000** (€{2000-u:.0f} übrig)")

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    a4  = col1.text_input("Artikel", key="dac_art")
    p4  = col2.number_input("Preis (€)", min_value=0.01, value=25.0, key="dac_pr")
    pl4 = col3.selectbox("Plattform", ["Kleinanzeigen","eBay","Vinted","Facebook","Flohmarkt"], key="dac_pl")

    if st.button("✅ Verkauf eintragen", type="primary", use_container_width=True):
        if a4:
            st.session_state.verkaufe.append({
                "datum": datetime.now().strftime("%d.%m.%Y"),
                "artikel": a4, "preis": p4, "plattform": pl4
            })
            st.session_state.anzahl += 1
            st.session_state.umsatz += p4
            st.success(f"✅ Eingetragen! {st.session_state.anzahl} Verkäufe / €{st.session_state.umsatz:.2f}")
            st.rerun()

    if st.session_state.verkaufe:
        st.markdown("### 📋 Letzte Verkäufe:")
        for v in reversed(st.session_state.verkaufe[-8:]):
            st.markdown(f"- {v['datum']} | {v['artikel']} | **€{v['preis']:.2f}** | {v['plattform']}")

# ══════════════════════════════════════════════════════════════
# TAB 4 — LAGER
# ══════════════════════════════════════════════════════════════
with t4:
    st.header("📦 Lagerbestand")

    col1, col2 = st.columns(2)
    with col1:
        la   = st.text_input("Artikel", placeholder="z.B. Vintage Stuhl", key="lager_art")
        lek  = st.number_input("Einkaufspreis (€)", min_value=0.0, value=10.0, key="lag_ek")
        lziel = st.number_input("Ziel-Verkaufspreis (€)", min_value=0.0, value=45.0, key="lager_ziel")
    with col2:
        lz  = st.selectbox("Zustand", ["Sehr gut","Gut","Gebraucht","Beschädigt"], key="lager_z")
        lpl = st.selectbox("Plattform", ["Kleinanzeigen","eBay","Vinted","Facebook","Flohmarkt"], key="lager_pl")
        ltage = st.number_input("Liegezeit (Tage)", min_value=0, value=0, key="lager_tage")

    if st.button("📦 Hinzufügen", type="primary", use_container_width=True):
        if la:
            g = lziel - lek - (lziel * 0.05)
            st.session_state.lager.append({
                "artikel": la, "ek": lek, "vk": lziel,
                "zustand": lz, "plattform": lpl, "tage": ltage, "gewinn": round(g, 2)
            })
            st.success(f"✅ Hinzugefügt! Erwarteter Gewinn: €{g:.2f}")
            st.rerun()

    if st.session_state.lager:
        ges_ek = sum(i["ek"] for i in st.session_state.lager)
        ges_g  = sum(i["gewinn"] for i in st.session_state.lager)
        c1,c2,c3 = st.columns(3)
        c1.metric("Artikel", len(st.session_state.lager))
        c2.metric("💸 Kapital", f"€{ges_ek:.2f}")
        c3.metric("💰 Erwarteter Gewinn", f"€{ges_g:.2f}")
        st.markdown("---")
        for item in st.session_state.lager:
            col1,col2,col3,col4 = st.columns([3,1,1,1])
            col1.markdown(f"**{item['artikel']}** ({item['zustand']}) — {item['plattform']}")
            col2.markdown(f"€{item['ek']:.2f}")
            col3.markdown(f"→ €{item['vk']:.2f}")
            col4.markdown(f"**+€{item['gewinn']:.2f}**")
            if item["tage"] > 30:
                st.warning(f"⏰ {item['artikel']}: {item['tage']} Tage — Preis senken!")

# ══════════════════════════════════════════════════════════════
# TAB 5 — OCR SCANNER
# ══════════════════════════════════════════════════════════════
with t5:
    st.header("📚 Multi-OCR Medien-Scanner")
    st.markdown("Fotografiere Bücher/CDs/Spiele-Stapel → KI erkennt alle und schätzt Werte!")

    medien_bild = st.file_uploader("📷 Stapel fotografieren", type=["jpg","jpeg","png"], key="medien")
    medien_typ  = st.selectbox("Medien-Typ", ["Bücher","CDs/Vinyl","Video-Spiele","DVDs","Gemischt"], key="ocr_typ")

    if st.button("🔍 Stapel analysieren!", type="primary", use_container_width=True):
        if medien_bild:
            with st.spinner("🤖 Scanne alle Artikel..."):
                b64 = base64.b64encode(medien_bild.read()).decode()
                ergebnis = ki(f"""Experte für Second-Hand {medien_typ} in Deutschland.
Scanne ALLE {medien_typ} auf dem Foto.

Für jeden Artikel:
**[Titel]** | eBay: €X | Kleinanzeigen: €X | Vinted: €X | Flohmarkt: €X | Empfehlung: KAUFEN/SKIP

Am Ende: Top-3 wertvollste + Gesamtwert des Stapels.
Plattformen: eBay, Kleinanzeigen, Vinted, Facebook. Auf Deutsch.""", bild_b64=b64)
                st.markdown(ergebnis)
        else:
            st.info("💡 Legen Sie alle Artikel nebeneinander und fotografieren Sie von oben!")

# ══════════════════════════════════════════════════════════════
# TAB 6 — REPARATUR-RECHNER
# ══════════════════════════════════════════════════════════════
with t6:
    st.header("🔧 Reparatur & Upcycling-Rechner")

    col1, col2 = st.columns(2)
    with col1:
        rep_artikel  = st.text_input("Artikel", placeholder="z.B. Vintage Stuhl", key="rep_art")
        rep_ek       = st.number_input("Einkaufspreis (€)", min_value=0.0, value=15.0, key="rep_ek")
        rep_material = st.number_input("Materialkosten (€)", min_value=0.0, value=25.0, key="rep_mat")
        rep_stunden  = st.number_input("Arbeitsstunden", min_value=0.5, value=3.0, step=0.5, key="rep_std")
    with col2:
        rep_vk      = st.number_input("Erwarteter VK (€)", min_value=0.0, value=120.0, key="rep_vk2")
        rep_plattform = st.selectbox("Plattform", ["Kleinanzeigen","eBay","Vinted","Facebook","Flohmarkt"], key="rep_pl")
        rep_beschr  = st.text_area("Was reparieren?", height=80)

    if st.button("🔧 Berechnen", type="primary", use_container_width=True):
        plattform_gebuehr = 0.05 if rep_plattform == "Vinted" else 0.02
        gesamtk   = rep_ek + rep_material + (rep_vk * plattform_gebuehr)
        gewinn    = rep_vk - gesamtk
        stundenlohn = gewinn / rep_stunden if rep_stunden > 0 else 0

        col1,col2,col3,col4 = st.columns(4)
        col1.metric("💸 Gesamtkosten", f"€{gesamtk:.2f}")
        col2.metric("💰 Gewinn", f"€{gewinn:.2f}")
        col3.metric("⏰ Stundenlohn", f"€{stundenlohn:.2f}/h")
        col4.metric("ROI", f"{(gewinn/gesamtk*100) if gesamtk>0 else 0:.0f}%")

        if stundenlohn >= 15:
            st.success(f"✅ LOHNT SICH! €{stundenlohn:.2f}/h")
        elif stundenlohn >= 8:
            st.warning(f"⚠️ Grenzfall: €{stundenlohn:.2f}/h")
        else:
            st.error(f"❌ Lohnt nicht! Nur €{stundenlohn:.2f}/h")

        if rep_beschr:
            with st.spinner("💡 KI-Tipps..."):
                tipps = ki(f"3 Reparatur-Tipps für '{rep_artikel}': {rep_beschr}. Kurz auf Deutsch.")
                st.markdown(tipps)

# ══════════════════════════════════════════════════════════════
# TAB 7 — POST-DUELL
# ══════════════════════════════════════════════════════════════
with t7:
    st.header("📦 Post-Duell: DHL vs. Hermes")

    col1,col2,col3 = st.columns(3)
    gewicht = col1.number_input("Gewicht (kg)", min_value=0.1, value=1.0, step=0.1)
    col2.number_input("Länge (cm)", min_value=1, value=30)
    col3.number_input("Breite (cm)", min_value=1, value=20)
    versicherung = st.checkbox("Versicherung?", key="post_vers")

    dhl_tarife    = [(0.5,3.99,"Päckchen S"),(1.0,4.99,"Päckchen M"),(2.0,6.99,"Päckchen L"),(5.0,9.49,"Paket 5kg"),(10.0,12.49,"Paket 10kg"),(31.5,18.49,"Paket 31kg")]
    hermes_tarife = [(0.5,3.70,"XS"),(1.0,4.50,"S"),(2.0,5.50,"M"),(5.0,7.90,"L"),(10.0,10.90,"XL"),(25.0,15.90,"XXL")]

    if st.button("⚡ Vergleichen!", type="primary", use_container_width=True):
        dp, dn = dhl_tarife[-1][1], dhl_tarife[-1][2]
        for mx, p, n in dhl_tarife:
            if gewicht <= mx: dp, dn = p, n; break
        hp, hn = hermes_tarife[-1][1], hermes_tarife[-1][2]
        for mx, p, n in hermes_tarife:
            if gewicht <= mx: hp, hn = p, n; break
        if versicherung: dp += 2.50; hp += 1.99

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### 🟡 DHL — **€{dp:.2f}**")
            st.markdown(f"Produkt: {dn}")
        with col2:
            st.markdown(f"### 🟢 Hermes — **€{hp:.2f}**")
            st.markdown(f"Produkt: {hn}")

        st.markdown("---")
        if dp < hp:
            st.success(f"🏆 DHL günstiger! Ersparnis: €{hp-dp:.2f}")
        elif hp < dp:
            st.success(f"🏆 Hermes günstiger! Ersparnis: €{dp-hp:.2f}")
        else:
            st.info("🤝 Gleicher Preis!")

# ══════════════════════════════════════════════════════════════
# TAB 8 — TRENDS
# ══════════════════════════════════════════════════════════════
with t8:
    st.header("📈 Markt-Trends")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🔥 Hot-Trends 2025/26")
        for s,n,w,p in [
            ("🔥","Vintage Levi's 501","+187%","€45"),
            ("🔥","Game Boy Color","+214%","€110"),
            ("🔥","90s Sportjacken","+92%","€55"),
            ("🔥","Analoge Kameras","+165%","€75"),
            ("📈","Meissen Porzellan","+14%","€45"),
            ("📈","LEGO Classic","+95%","€55"),
            ("📈","Vintage Adidas","+72%","€50"),
            ("⚖️","Kaffeemaschinen","+8%","€25"),
        ]:
            st.markdown(f"{s} **{n}** — {p} ({w})")

    with col2:
        st.markdown("### 💡 Gold-Wörter")
        for g in ["🏠 Dachbodenfund","🏡 Haushaltsauflösung","⚰️ Nachlass",
                  "🔑 Kellerfund","🚚 Umzugskarton","🎁 Zu verschenken",
                  "📦 Konvolut Kiste","👵 Oma entrümpelt"]:
            st.markdown(f"- {g}")

    st.markdown("---")
    frage = st.text_input("🤖 Trend-Frage stellen:", placeholder="Was ist gerade auf Kleinanzeigen/Vinted gefragt?", key="trends_frage")
    if st.button("Fragen", use_container_width=True):
        if frage:
            with st.spinner("🤖 Analysiere..."):
                st.markdown(ki(f"Reselling-Experte Deutschland, alle Plattformen: eBay/Kleinanzeigen/Vinted/Facebook/Flohmarkt. Kurz auf Deutsch: {frage}"))

# ───────────────────────────────────────────────────────────────
# FOOTER
# ───────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<p style='text-align:center;color:#666'>⚡ MarktRadar OS PRO v4.0 · Zoran Berlin · "
    f"{datetime.now().strftime('%d.%m.%Y')}</p>",
    unsafe_allow_html=True
)
