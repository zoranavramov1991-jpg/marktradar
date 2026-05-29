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

# ── API ──────────────────────────────────────────────────────
def get_secret(key):
    try:
        return st.secrets[key]
    except:
        return os.environ.get(key, "")

OPENROUTER_KEY = get_secret("OPENROUTER_API_KEY")

# ── SESSION STATE ────────────────────────────────────────────
defaults = {
    "lager": [],
    "sim_verlauf": [],
    "lot_artikel": [],
    "gewinn_log": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── KI ENGINE ───────────────────────────────────────────────
def ki(prompt, bild_b64=None, alle_bilder=None):
    try:
        if not OPENROUTER_KEY:
            return "❌ Kein API-Key konfiguriert! Bitte in Streamlit Secrets eintragen."
        client = OpenAI(api_key=OPENROUTER_KEY, base_url="https://openrouter.ai/api/v1")
        if alle_bilder and len(alle_bilder) > 0:
            model = "openai/gpt-4o"
            inhalt = []
            for b64 in alle_bilder:
                inhalt.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": "high"}})
            inhalt.append({"type": "text", "text": prompt})
            msgs = [{"role": "user", "content": inhalt}]
        elif bild_b64:
            model = "openai/gpt-4o"
            msgs = [{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{bild_b64}", "detail": "high"}},
                {"type": "text", "text": prompt}
            ]}]
        else:
            model = "openai/gpt-4o-mini"
            msgs = [{"role": "user", "content": prompt}]
        r = client.chat.completions.create(model=model, messages=msgs, max_tokens=2000)
        return r.choices[0].message.content
    except Exception as e:
        return f"❌ KI-Fehler: {str(e)}"

# ── URL AUSLESEN ─────────────────────────────────────────────
def url_auslesen(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0", "Accept-Language": "de-DE,de;q=0.9"}
        r = requests.get(url, headers=headers, timeout=15)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        zeilen = [z.strip() for z in soup.get_text(separator="\n").split("\n") if len(z.strip()) > 15]
        return {"text": "\n".join(zeilen[:150])[:4000], "ok": True}
    except Exception as e:
        return {"text": "", "ok": False, "fehler": str(e)}

# ── HEADER ───────────────────────────────────────────────────
st.markdown("""
<div style='background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);
padding:20px;border-radius:14px;margin-bottom:20px;text-align:center'>
<h1 style='color:#f5a623;margin:0;font-size:2.2em'>⚡ MarktRadar OS PRO</h1>
<p style='color:#a8b2d8;margin:6px 0 0'>
Kleinanzeigen · Vinted · Facebook · eBay · Flohmärkte · Auktionen
</p>
</div>""", unsafe_allow_html=True)

# ── TABS ─────────────────────────────────────────────────────
tabs = st.tabs([
    "🔍 Analyse",
    "💬 Anschreib-Bot",
    "📦 Lager",
    "📚 OCR Scanner",
    "🔧 Reparatur",
    "📦 Post-Duell",
    "📈 Trends",
    "🎭 Verhandlung",
    "📸 Foto-Coach",
    "🗺️ Flohmärkte",
    "🧮 Lot-Rechner",
    "✉️ Nachrichten-KI",
    "📉 Preissenker",
    "🔬 Marken-Scanner",
    "📦 Bundle-KI",
    "🛡️ Reklamation",
    "📅 Timing",
    "💰 Gewinn-Buch",
    "✨ Anzeigen-KI",
    "🗓️ Tagesplan",
])

t1,t2,t3,t4,t5,t6,t7,t8,t9,t10,t11,t12,t13,t14,t15,t16,t17,t18,t19,t20 = tabs

# ════════════════════════════════════════════════════════════
# TAB 1 — ARTIKEL ANALYSE
# ════════════════════════════════════════════════════════════
with t1:
    st.header("🔍 Artikel-Analyse")
    st.markdown("**Foto + URL → KI scannt jeden Artikel → Preise auf allen Plattformen**")

    eingabe_typ = st.radio("Was analysieren?",
        ["📸 Foto", "🔗 Link", "📸 + 🔗 Beides"], horizontal=True, key="ana_typ")

    bild_input = None
    url_input  = None

    if "Foto" in eingabe_typ:
        bild_input = st.file_uploader(
            "📷 Fotos hochladen (mehrere möglich — alle bleiben!)",
            type=["jpg","jpeg","png","webp"],
            accept_multiple_files=True,
            key="ana_bild"
        )
        if bild_input:
            st.success(f"✅ {len(bild_input)} Foto(s) geladen")
            cols = st.columns(min(len(bild_input), 4))
            for idx, img in enumerate(bild_input):
                with cols[idx % 4]:
                    st.image(img, caption=f"Foto {idx+1}", use_column_width=True)

    if "Link" in eingabe_typ:
        url_input = st.text_input("🔗 Link eingeben",
            placeholder="z.B. https://luedtke-auktion-online.de/... oder Kleinanzeigen-Link",
            key="ana_url")

    col1, col2 = st.columns([2, 1])
    with col1:
        beschreibung = st.text_area("📝 Eigene Beschreibung (optional)",
            placeholder="z.B. 'Kaffeeservice 6-teilig, kleiner Chip am Rand'",
            height=80, key="ana_beschr")
    with col2:
        defekt = st.slider("🔧 Defekt-Grad", 1, 100, 10, 5, key="ana_defekt",
            help="1 = Wie neu | 50 = Gebraucht | 100 = Total defekt")
        if defekt <= 20:
            st.success(f"🟢 {defekt}% — Fast neu")
        elif defekt <= 50:
            st.warning(f"🟡 {defekt}% — Gebraucht")
        elif defekt <= 80:
            st.error(f"🔴 {defekt}% — Stark beschädigt")
        else:
            st.error(f"⛔ {defekt}% — Fast unbrauchbar")

    if st.button("🚀 VOLLANALYSE STARTEN", type="primary", use_container_width=True, key="ana_btn"):
        if bild_input or url_input or beschreibung:
            artikel_info = ""
            alle_bilder  = []

            with st.status("📡 Stufe 1: Daten sammeln...", expanded=True):
                if url_input:
                    seite = url_auslesen(url_input)
                    if seite["ok"]:
                        artikel_info = seite["text"]
                        st.success(f"✅ Seite ausgelesen ({len(artikel_info)} Zeichen)")
                    else:
                        st.warning("⚠️ URL nicht erreichbar")
                if bild_input:
                    for img in bild_input:
                        img.seek(0)
                        alle_bilder.append(base64.b64encode(img.read()).decode())
                    st.success(f"✅ {len(alle_bilder)} Foto(s) bereit")

            with st.status("🔬 Stufe 2: KI-Tiefen-Scan...", expanded=True):
                if defekt <= 20: defekt_beschr = f"Fast neu ({defekt}%)"
                elif defekt <= 40: defekt_beschr = f"Leicht gebraucht ({defekt}%)"
                elif defekt <= 60: defekt_beschr = f"Deutlich gebraucht ({defekt}%)"
                elif defekt <= 80: defekt_beschr = f"Stark beschädigt ({defekt}%)"
                else: defekt_beschr = f"Fast unbrauchbar ({defekt}%)"

                zusatz = ""
                if artikel_info: zusatz += f"\n\nWEBSEITE-INFO:\n{artikel_info[:2500]}"
                if beschreibung:  zusatz += f"\n\nHÄNDLER-BESCHREIBUNG: {beschreibung}"
                zusatz += f"\nDEFEKT-GRAD: {defekt_beschr}"

                prompt = f"""Antworte NUR auf Deutsch. Immer vollständig. Nie verweigern.
Du analysierst für einen deutschen Reselling-Händler.
Erkenne JEDEN sichtbaren Artikel. Nur Fakten, keine Kaufempfehlungen.
Defektgrad beachten: {defekt_beschr}{zusatz}

AMPEL-SYSTEM:
🟢 GRÜN = schnell verkäuflich (1-7 Tage)
🟡 GELB = mittel (1-4 Wochen)
🔴 ROT = langsam (1-3 Monate+)

SCHRITT 1 — INVENTAR:
Alle Artikel nummeriert aufzählen.

SCHRITT 2 — KURZBESCHREIBUNG (2-3 Sätze pro Artikel):
Was ist es? Was fällt auf? Besonderheiten?

SCHRITT 3 — DETAIL für jeden Artikel:

═══════════════════════════════
ARTIKEL [N]: [NAME]
═══════════════════════════════
📌 KURZBESCHREIBUNG: [2-3 Sätze]

🔍 IDENTIFIKATION:
• Exakt: [Was ist es?]
• Marke: [Name oder unbekannt]
• Material: [genaues Material]
• Maße: [Schätzung]
• Stempel/Logos: [alles sichtbare]
• Echtheit: [Echt / Wahrscheinlich echt / Unsicher / Replik]

📅 ALTER:
• Jahr: [ca. Jahr oder Jahrzehnt]
• Epoche: [DDR / 80er / 90er / Modern etc.]
• Beweis: [Was zeigt das Alter?]

🚦 MARKTBEWERTUNG:
• Ampel: [🟢/🟡/🔴]
• Verkaufszeit: [X Tage/Wochen]
• Nachfrage: [Sehr hoch/Hoch/Mittel/Niedrig]
• Zielgruppe: [Wer kauft das?]

💶 PREISE (Defektgrad {defekt}% eingerechnet):
| Plattform | Preis |
|-----------|-------|
| eBay | €X – €Y |
| Kleinanzeigen | €X – €Y |
| Vinted | €X – €Y |
| Facebook | €X – €Y |
| Flohmarkt | €X – €Y |
| Max. Ankauf | €X |

═══════════════════════════════
📊 GESAMT:
• 🟢 Schnell: X Artikel
• 🟡 Mittel: X Artikel
• 🔴 Langsam: X Artikel
• Gesamtwert: €X – €Y
• Max. Ankauf gesamt: €X
• Wertvollster: [Name] (€X)"""

                ergebnis = ki(prompt, alle_bilder=alle_bilder if alle_bilder else None,
                              bild_b64=alle_bilder[0] if alle_bilder else None)
                st.markdown(ergebnis)
                st.session_state["letzte_analyse"] = ergebnis

                suchbegriff = "Vintage Artikel"
                for line in ergebnis.split("\n"):
                    if "ARTIKEL 1:" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            suchbegriff = parts[1].strip().strip("*[] ").split("\n")[0][:40]
                        break

            with st.status("📊 Stufe 3: Plattform-Links...", expanded=True):
                ka_url     = f"https://www.kleinanzeigen.de/s-{urllib.parse.quote(suchbegriff)}/k0"
                vinted_url = f"https://www.vinted.de/catalog?search_text={urllib.parse.quote(suchbegriff)}"
                fb_url     = f"https://www.facebook.com/marketplace/search/?query={urllib.parse.quote(suchbegriff)}"
                ebay_url   = f"https://www.ebay.de/sch/i.html?_nkw={urllib.parse.quote(suchbegriff)}&LH_Complete=1&LH_Sold=1"
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"🛒 [eBay beendete Verkäufe →]({ebay_url})")
                    st.markdown(f"📱 [Kleinanzeigen →]({ka_url})")
                with col2:
                    st.markdown(f"👗 [Vinted →]({vinted_url})")
                    st.markdown(f"👥 [Facebook →]({fb_url})")

            with st.status("✅ Stufe 4: Zusammenfassung...", expanded=True):
                fazit = ki(f"""Zusammenfassung für deutschen Reseller. Nur Fakten. Auf Deutsch. Max 4 Zeilen.
Analyse: {ergebnis[:600]}
Format:
• Artikel gefunden: X
• 🟢 Schnell: [Namen]
• 🟡 Mittel: [Namen]
• 🔴 Langsam: [Namen]
• Gesamtwert: €X – €Y""")
                st.info(f"📊 {fazit}")
        else:
            st.warning("⚠️ Bitte Foto hochladen, Link eingeben oder Artikel beschreiben!")

# ════════════════════════════════════════════════════════════
# TAB 2 — ANSCHREIB-BOT
# ════════════════════════════════════════════════════════════
with t2:
    st.header("💬 Anschreib-Bot")
    col1, col2 = st.columns(2)
    with col1:
        art2   = st.text_input("Artikel", placeholder="z.B. Vintage Kamera", key="ab_art")
        preis2 = st.number_input("Mein Angebot (€)", min_value=1.0, value=20.0, key="ab_preis")
        vk2    = st.number_input("Verkäufer-Preis (€)", min_value=1.0, value=50.0, key="ab_vk")
    with col2:
        stil2 = st.selectbox("Stil", ["Freundlich & charmant","Bestimmt & direkt",
            "Dringend (heute abholen)","Paket-Deal","Letztes Angebot"], key="ab_stil")
        pl2   = st.selectbox("Plattform", ["Kleinanzeigen","eBay","Facebook","Vinted","Flohmarkt"], key="ab_pl")

    if st.button("✍️ Nachricht generieren", type="primary", use_container_width=True, key="ab_btn"):
        if art2:
            with st.spinner("✍️ Generiere..."):
                msg = ki(f"""Verhandlungs-Nachricht auf Deutsch.
Stil: {stil2} | Plattform: {pl2}
Artikel: {art2} | Mein Preis: €{preis2} | Verkäufer: €{vk2}
Max 5 Sätze, psychologisch optimiert, freundlich aber bestimmt.
NUR die fertige Nachricht ausgeben!""")
                st.text_area("📩 Kopieren & senden:", value=msg, height=200, key="ab_result")

# ════════════════════════════════════════════════════════════
# TAB 3 — LAGER
# ════════════════════════════════════════════════════════════
with t3:
    st.header("📦 Lagerbestand")
    col1, col2 = st.columns(2)
    with col1:
        la3  = st.text_input("Artikel", placeholder="z.B. Meissen Teller", key="lag_art")
        ek3  = st.number_input("Einkaufspreis (€)", min_value=0.0, value=10.0, key="lag_ek")
        vk3  = st.number_input("Ziel-VK (€)", min_value=0.0, value=45.0, key="lag_vk")
    with col2:
        zu3  = st.selectbox("Zustand", ["Sehr gut","Gut","Gebraucht","Beschädigt"], key="lag_zu")
        pl3  = st.selectbox("Plattform", ["Kleinanzeigen","eBay","Vinted","Facebook","Flohmarkt"], key="lag_pl")
        ta3  = st.number_input("Liegezeit (Tage)", min_value=0, value=0, key="lag_ta")

    if st.button("📦 Hinzufügen", type="primary", use_container_width=True, key="lag_btn"):
        if la3:
            g = vk3 - ek3 - (vk3 * 0.05)
            st.session_state.lager.append({"artikel": la3, "ek": ek3, "vk": vk3,
                "zustand": zu3, "plattform": pl3, "tage": ta3, "gewinn": round(g,2)})
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
            c1,c2,c3,c4 = st.columns([3,1,1,1])
            c1.markdown(f"**{item['artikel']}** ({item['zustand']}) — {item['plattform']}")
            c2.markdown(f"€{item['ek']:.2f}")
            c3.markdown(f"→ €{item['vk']:.2f}")
            c4.markdown(f"**+€{item['gewinn']:.2f}**")
            if item["tage"] > 30:
                st.warning(f"⏰ {item['artikel']}: {item['tage']} Tage — Preis senken?")

# ════════════════════════════════════════════════════════════
# TAB 4 — OCR SCANNER
# ════════════════════════════════════════════════════════════
with t4:
    st.header("📚 Multi-OCR Medien-Scanner")
    st.markdown("Stapel fotografieren → KI erkennt alle Artikel")
    ocr_bild = st.file_uploader("📷 Stapel fotografieren", type=["jpg","jpeg","png"], key="ocr_bild")
    ocr_typ  = st.selectbox("Typ", ["Bücher","CDs/Vinyl","Video-Spiele","DVDs","Gemischt"], key="ocr_typ")

    if st.button("🔍 Stapel analysieren", type="primary", use_container_width=True, key="ocr_btn"):
        if ocr_bild:
            with st.spinner("🤖 Scanne alle Artikel..."):
                b64 = base64.b64encode(ocr_bild.read()).decode()
                r = ki(f"""Experte für {ocr_typ} in Deutschland. Scanne ALLE sichtbaren {ocr_typ}.
Für jeden Artikel: **[Titel]** | eBay: €X | Kleinanzeigen: €X | Vinted: €X | Flohmarkt: €X
Am Ende: Top-3 wertvollste + Gesamtwert. Auf Deutsch.""", bild_b64=b64)
                st.markdown(r)
        else:
            st.info("💡 Alle Artikel nebeneinander legen und von oben fotografieren!")

# ════════════════════════════════════════════════════════════
# TAB 5 — REPARATUR
# ════════════════════════════════════════════════════════════
with t5:
    st.header("🔧 Reparatur & Upcycling-Rechner")
    col1, col2 = st.columns(2)
    with col1:
        rep_art = st.text_input("Artikel", placeholder="z.B. Vintage Stuhl", key="rep_art")
        rep_ek  = st.number_input("Einkaufspreis (€)", min_value=0.0, value=15.0, key="rep_ek")
        rep_mat = st.number_input("Materialkosten (€)", min_value=0.0, value=25.0, key="rep_mat")
        rep_std = st.number_input("Arbeitsstunden", min_value=0.5, value=3.0, step=0.5, key="rep_std")
    with col2:
        rep_vk  = st.number_input("Erwarteter VK (€)", min_value=0.0, value=120.0, key="rep_vk")
        rep_pl  = st.selectbox("Plattform", ["Kleinanzeigen","eBay","Vinted","Facebook","Flohmarkt"], key="rep_pl")
        rep_be  = st.text_area("Was reparieren?", height=80, key="rep_be")

    if st.button("🔧 Berechnen", type="primary", use_container_width=True, key="rep_btn"):
        geb   = rep_vk * (0.05 if "Vinted" in rep_pl else 0.119 if "eBay" in rep_pl else 0.02)
        geskt = rep_ek + rep_mat + (rep_vk * 0.02) + geb
        gew   = rep_vk - geskt
        stl   = gew / rep_std if rep_std > 0 else 0
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("💸 Kosten", f"€{geskt:.2f}")
        c2.metric("💰 Gewinn", f"€{gew:.2f}")
        c3.metric("⏰ Stundenlohn", f"€{stl:.2f}/h")
        c4.metric("ROI", f"{(gew/geskt*100) if geskt>0 else 0:.0f}%")
        if stl >= 15: st.success(f"✅ LOHNT SICH! €{stl:.2f}/h")
        elif stl >= 8: st.warning(f"⚠️ Grenzfall: €{stl:.2f}/h")
        else: st.error(f"❌ Lohnt nicht: €{stl:.2f}/h")
        if rep_be:
            with st.spinner("💡 KI-Tipps..."):
                st.markdown(ki(f"3 konkrete Reparatur-Tipps für '{rep_art}': {rep_be}. Kurz auf Deutsch."))

# ════════════════════════════════════════════════════════════
# TAB 6 — POST-DUELL
# ════════════════════════════════════════════════════════════
with t6:
    st.header("📦 Post-Duell: DHL vs. Hermes")
    col1,col2,col3 = st.columns(3)
    gew6 = col1.number_input("Gewicht (kg)", min_value=0.1, value=1.0, step=0.1, key="post_gew")
    col2.number_input("Länge (cm)", min_value=1, value=30, key="post_l")
    col3.number_input("Breite (cm)", min_value=1, value=20, key="post_b")
    vers6 = st.checkbox("Versicherung?", key="post_vers")

    dhl_t    = [(0.5,3.99,"Päckchen S"),(1.0,4.99,"Päckchen M"),(2.0,6.99,"Päckchen L"),
                (5.0,9.49,"Paket 5kg"),(10.0,12.49,"Paket 10kg"),(31.5,18.49,"Paket 31kg")]
    hermes_t = [(0.5,3.70,"XS"),(1.0,4.50,"S"),(2.0,5.50,"M"),
                (5.0,7.90,"L"),(10.0,10.90,"XL"),(25.0,15.90,"XXL")]

    if st.button("⚡ Vergleichen", type="primary", use_container_width=True, key="post_btn"):
        dp,dn = dhl_t[-1][1],dhl_t[-1][2]
        for mx,p,n in dhl_t:
            if gew6 <= mx: dp,dn = p,n; break
        hp,hn = hermes_t[-1][1],hermes_t[-1][2]
        for mx,p,n in hermes_t:
            if gew6 <= mx: hp,hn = p,n; break
        if vers6: dp += 2.50; hp += 1.99
        c1,c2 = st.columns(2)
        with c1:
            st.markdown(f"### 🟡 DHL — **€{dp:.2f}**")
            st.markdown(f"Produkt: {dn}")
        with c2:
            st.markdown(f"### 🟢 Hermes — **€{hp:.2f}**")
            st.markdown(f"Produkt: {hn}")
        st.markdown("---")
        if dp < hp: st.success(f"🏆 DHL günstiger! Ersparnis: €{hp-dp:.2f}")
        elif hp < dp: st.success(f"🏆 Hermes günstiger! Ersparnis: €{dp-hp:.2f}")
        else: st.info("🤝 Gleicher Preis!")

# ════════════════════════════════════════════════════════════
# TAB 7 — TRENDS
# ════════════════════════════════════════════════════════════
with t7:
    st.header("📈 Markt-Trends")
    c1,c2 = st.columns(2)
    with c1:
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
    with c2:
        st.markdown("### 💡 Gold-Wörter")
        for g in ["🏠 Dachbodenfund","🏡 Haushaltsauflösung","⚰️ Nachlass",
                  "🔑 Kellerfund","🚚 Umzugskarton","🎁 Zu verschenken",
                  "📦 Konvolut Kiste","👵 Oma entrümpelt"]:
            st.markdown(f"- {g}")
    st.markdown("---")
    frage7 = st.text_input("🤖 Trend-Frage:", placeholder="Was ist gerade auf Kleinanzeigen gefragt?", key="trend_frage")
    if st.button("Fragen", key="trend_btn"):
        if frage7:
            with st.spinner("🤖 Analysiere..."):
                st.markdown(ki(f"Reselling-Experte Deutschland. Kurz auf Deutsch: {frage7}"))

# ════════════════════════════════════════════════════════════
# TAB 8 — VERHANDLUNGS-SIMULATOR
# ════════════════════════════════════════════════════════════
with t8:
    st.header("🎭 Verhandlungs-Simulator")
    st.markdown("KI spielt den Verkäufer — üben Sie die perfekte Verhandlung!")
    c1,c2 = st.columns(2)
    with c1:
        sim_art  = st.text_input("Artikel", placeholder="z.B. Vintage Kamera", key="sim_art")
        sim_vk   = st.number_input("Verkäufer-Preis (€)", min_value=1.0, value=80.0, key="sim_vk")
        sim_ziel = st.number_input("Ihr Ziel-Preis (€)", min_value=1.0, value=40.0, key="sim_ziel")
    with c2:
        sim_typ = st.selectbox("Verkäufer-Typ", [
            "Sturköpfig — gibt kaum nach",
            "Freundlich — aber realistisch",
            "Gestresst — will schnell verkaufen",
            "Unentschlossen — unsicher über Wert",
            "Professioneller Händler"
        ], key="sim_typ")
        sim_pl = st.selectbox("Wo?", ["Flohmarkt","Kleinanzeigen","Facebook"], key="sim_pl")

    if st.button("🎭 Simulation starten", type="primary", use_container_width=True, key="sim_start"):
        st.session_state.sim_verlauf = []
        if sim_art:
            start = ki(f"""Du spielst einen deutschen Verkäufer auf {sim_pl}.
Artikel: {sim_art} für €{sim_vk}. Typ: {sim_typ}.
Schreibe deine erste Antwort wenn ein Käufer fragt ob der Preis verhandelbar ist.
2-3 Sätze. Auf Deutsch. In der Rolle bleiben!""")
            st.session_state.sim_verlauf.append({"rolle":"🏪 Verkäufer","text":start})
            st.rerun()

    if st.session_state.sim_verlauf:
        st.markdown("---")
        for msg in st.session_state.sim_verlauf:
            if msg["rolle"] == "🏪 Verkäufer":
                st.info(f"**{msg['rolle']}:** {msg['text']}")
            else:
                st.success(f"**{msg['rolle']}:** {msg['text']}")

        angebot = st.text_input("✍️ Ihre Antwort:", key="sim_input")
        c1,c2 = st.columns(2)
        with c1:
            if st.button("📤 Senden", type="primary", use_container_width=True, key="sim_send"):
                if angebot:
                    st.session_state.sim_verlauf.append({"rolle":"🛒 Sie","text":angebot})
                    verlauf = "\n".join([f"{m['rolle']}: {m['text']}" for m in st.session_state.sim_verlauf])
                    antwort = ki(f"""Verkäufer ({sim_typ}) von {sim_art} (Preis: €{sim_vk}).
Verlauf:\n{verlauf}
Antworte als Verkäufer (2-3 Sätze). Auf Deutsch. In der Rolle!""")
                    st.session_state.sim_verlauf.append({"rolle":"🏪 Verkäufer","text":antwort})
                    st.rerun()
        with c2:
            if st.button("🧠 Strategie", use_container_width=True, key="sim_strat"):
                verlauf = "\n".join([f"{m['rolle']}: {m['text']}" for m in st.session_state.sim_verlauf])
                s = ki(f"""Verhandlungsanalyse. Artikel: {sim_art} | Ziel: €{sim_ziel}
Verlauf:\n{verlauf}
1. Was lief gut? 2. Was besser? 3. Nächste Nachricht für €{sim_ziel}? Auf Deutsch.""")
                st.markdown(f"### 🧠 Strategie:\n{s}")

# ════════════════════════════════════════════════════════════
# TAB 9 — FOTO-COACH
# ════════════════════════════════════════════════════════════
with t9:
    st.header("📸 Profi-Foto-Coach")
    st.markdown("Foto hochladen → KI sagt wie Sie es besser machen für mehr Geld!")
    foto9 = st.file_uploader("📷 Aktuelles Foto hochladen", type=["jpg","jpeg","png"], key="foto9")
    pl9   = st.selectbox("Für welche Plattform?", ["Kleinanzeigen","Vinted","Facebook","eBay","Alle"], key="foto9_pl")

    if st.button("📸 Foto analysieren", type="primary", use_container_width=True, key="foto9_btn"):
        if foto9:
            with st.spinner("🔍 Analysiere..."):
                b64 = base64.b64encode(foto9.read()).decode()
                c1,c2 = st.columns(2)
                with c1:
                    foto9.seek(0)
                    st.image(foto9, caption="Ihr Foto", use_column_width=True)
                with c2:
                    r = ki(f"""Produkt-Fotografie Experte für {pl9} in Deutschland.
Analysiere dieses Verkaufsfoto. Auf Deutsch.

📊 BEWERTUNG (1-10):
• Helligkeit: X/10
• Hintergrund: X/10
• Schärfe: X/10
• Winkel: X/10
• Gesamt: X/10

❌ PROBLEME: [Was ist schlecht?]

✅ VERBESSERUNGEN:
1. [Verbesserung]
2. [Verbesserung]
3. [Verbesserung]

📱 PERFEKTES FOTO:
• Hintergrund: [Was nehmen?]
• Licht: [Wie aufstellen?]
• Winkel: [Von wo?]
• Extras: [Was noch zeigen?]

💰 Preis-Auswirkung: Mit perfektem Foto X% mehr möglich.""", bild_b64=b64)
                    st.markdown(r)
        else:
            st.info("💡 Foto hochladen das Sie verbessern möchten!")

# ════════════════════════════════════════════════════════════
# TAB 10 — FLOHMÄRKTE BERLIN
# ════════════════════════════════════════════════════════════
with t10:
    st.header("🗺️ Berlin Flohmarkt-Kalender")
    st.markdown("Alle Flohmärkte von **Montag bis Sonntag** mit Telefon & Maps!")

    flohmärkte = [
        {"tag":"Montag","name":"Flohmarkt am Rathaus Steglitz","adresse":"Schloßstraße 37, 12163 Berlin","wann":"Mo–Sa, 9:00–18:00","telefon":"+49 30 79706820","typ":"🏠 Haushalt, Kleidung, Bücher","bewertung":"⭐⭐⭐","tipp":"Günstige Alltagsartikel","maps":"https://maps.google.com/?q=Rathaus+Steglitz+Berlin"},
        {"tag":"Montag","name":"Trödelmarkt Berliner Straße","adresse":"Berliner Str. 16, 10715 Berlin","wann":"Mo–Fr, 10:00–17:00","telefon":"+49 30 8537240","typ":"🛍️ Gemischt, Antiquitäten","bewertung":"⭐⭐⭐","tipp":"Kleine Händler, gute Verhandlung","maps":"https://maps.google.com/?q=Berliner+Straße+16+Berlin"},
        {"tag":"Dienstag","name":"Flohmarkt Fehrbelliner Platz","adresse":"Fehrbelliner Platz, 10707 Berlin","wann":"Di & Fr, 8:00–15:00","telefon":"+49 30 28097272","typ":"🏺 Antiquitäten, Porzellan, Schmuck","bewertung":"⭐⭐⭐⭐","tipp":"Top für Porzellan & Silber — früh kommen!","maps":"https://maps.google.com/?q=Fehrbelliner+Platz+Berlin"},
        {"tag":"Dienstag","name":"Antikmarkt Charlottenburg","adresse":"Kantstraße 17, 10623 Berlin","wann":"Di–Sa, 10:00–18:00","telefon":"+49 30 3138030","typ":"🏛️ Antiquitäten, Kunst","bewertung":"⭐⭐⭐⭐","tipp":"Hochwertige Antiquitäten","maps":"https://maps.google.com/?q=Kantstraße+17+Berlin"},
        {"tag":"Mittwoch","name":"Flohmarkt Alexanderplatz","adresse":"Alexanderplatz, 10178 Berlin","wann":"Täglich, 10:00–19:00","telefon":"+49 30 24632425","typ":"🏙️ Gemischt, Vintage","bewertung":"⭐⭐⭐","tipp":"Täglich offen — spontane Käufe","maps":"https://maps.google.com/?q=Alexanderplatz+Flohmarkt+Berlin"},
        {"tag":"Mittwoch","name":"Trödelmarkt Spandau","adresse":"Carl-Schurz-Str. 13, 13597 Berlin","wann":"Mi & Sa, 8:00–14:00","telefon":"+49 30 3545080","typ":"🔧 Werkzeug, Haushalt","bewertung":"⭐⭐⭐","tipp":"Günstige Werkzeuge & Haushalt","maps":"https://maps.google.com/?q=Carl-Schurz-Straße+Spandau+Berlin"},
        {"tag":"Donnerstag","name":"Trödelmarkt Schöneberg","adresse":"Winterfeldtplatz, 10781 Berlin","wann":"Do (klein) & Sa (groß), 8:00–14:00","telefon":"+49 30 7262290","typ":"🌿 Vintage, Haushalt, Mode","bewertung":"⭐⭐⭐⭐","tipp":"Do ruhiger & günstiger als Sa","maps":"https://maps.google.com/?q=Winterfeldtplatz+Berlin"},
        {"tag":"Freitag","name":"Flohmarkt Fehrbelliner Platz","adresse":"Fehrbelliner Platz, 10707 Berlin","wann":"Di & Fr, 8:00–15:00","telefon":"+49 30 28097272","typ":"🏺 Antiquitäten, Porzellan","bewertung":"⭐⭐⭐⭐⭐","tipp":"Freitags am besten! Frisch aufgebaut","maps":"https://maps.google.com/?q=Fehrbelliner+Platz+Berlin"},
        {"tag":"Freitag","name":"Antik & Trödelmarkt Ostbahnhof","adresse":"Erich-Steinfurth-Str. 1, 10243 Berlin","wann":"Fr–So, 9:00–16:00","telefon":"+49 30 2936028","typ":"🛍️ Großer Gemischtmarkt","bewertung":"⭐⭐⭐⭐","tipp":"Freitags wenige Leute — beste Verhandlung!","maps":"https://maps.google.com/?q=Flohmarkt+Ostbahnhof+Berlin"},
        {"tag":"Samstag","name":"RAW Flohmarkt","adresse":"Revaler Str. 99, 10245 Berlin","wann":"Sa & So, 10:00–18:00","telefon":"+49 30 29367840","typ":"🕶️ Vintage Mode, Vinyl, Streetwear","bewertung":"⭐⭐⭐⭐⭐","tipp":"BESTE Quelle für Vintage-Kleidung Berlin!","maps":"https://maps.google.com/?q=RAW+Gelände+Berlin"},
        {"tag":"Samstag","name":"Winterfeldtmarkt","adresse":"Winterfeldtplatz, 10781 Berlin","wann":"Jeden Sa, 8:00–14:00","telefon":"+49 30 7262290","typ":"🌿 Bio, Vintage, Kunst, Mode","bewertung":"⭐⭐⭐⭐⭐","tipp":"Einer der besten Berliner Märkte — Pflicht!","maps":"https://maps.google.com/?q=Winterfeldtmarkt+Berlin"},
        {"tag":"Samstag","name":"Antik & Trödelmarkt Ostbahnhof","adresse":"Erich-Steinfurth-Str. 1, 10243 Berlin","wann":"Fr–So, 9:00–16:00","telefon":"+49 30 2936028","typ":"🛍️ Großer Gemischtmarkt","bewertung":"⭐⭐⭐⭐","tipp":"Groß & günstig — viel Auswahl","maps":"https://maps.google.com/?q=Flohmarkt+Ostbahnhof+Berlin"},
        {"tag":"Samstag","name":"Trödelmarkt Spandau","adresse":"Carl-Schurz-Str. 13, 13597 Berlin","wann":"Mi & Sa, 8:00–14:00","telefon":"+49 30 3545080","typ":"🔧 Werkzeug, Haushalt, Kleidung","bewertung":"⭐⭐⭐","tipp":"Samstags viel größer als Mittwoch","maps":"https://maps.google.com/?q=Carl-Schurz-Straße+Spandau+Berlin"},
        {"tag":"Sonntag","name":"Mauerpark Flohmarkt","adresse":"Bernauer Str. 63-64, 13355 Berlin","wann":"Jeden So, 9:00–18:00","telefon":"+49 30 40505380","typ":"🎭 Gemischt — Vintage, Kleidung","bewertung":"⭐⭐⭐⭐⭐","tipp":"MUSS! Vor 10 Uhr kommen","maps":"https://maps.google.com/?q=Mauerpark+Flohmarkt+Berlin"},
        {"tag":"Sonntag","name":"Flohmarkt Boxhagener Platz","adresse":"Boxhagener Platz, 10245 Berlin","wann":"Jeden So, 10:00–18:00","telefon":"+49 30 29362596","typ":"🏺 Antiquitäten, Porzellan, Bücher","bewertung":"⭐⭐⭐⭐⭐","tipp":"Top für Porzellan & Antiquitäten!","maps":"https://maps.google.com/?q=Boxhagener+Platz+Flohmarkt+Berlin"},
        {"tag":"Sonntag","name":"Treptower Flohmarkt","adresse":"Treptower Park, 12435 Berlin","wann":"Jeden So, 8:00–16:00","telefon":"+49 30 5321555","typ":"🔧 Werkzeug, Elektronik, DDR","bewertung":"⭐⭐⭐⭐","tipp":"Gut für Elektronik & DDR-Sammlerstücke","maps":"https://maps.google.com/?q=Treptower+Park+Flohmarkt+Berlin"},
        {"tag":"Sonntag","name":"RAW Flohmarkt","adresse":"Revaler Str. 99, 10245 Berlin","wann":"Sa & So, 10:00–18:00","telefon":"+49 30 29367840","typ":"🕶️ Vintage Mode, Vinyl","bewertung":"⭐⭐⭐⭐⭐","tipp":"Sonntags entspannter als Samstag","maps":"https://maps.google.com/?q=RAW+Gelände+Berlin"},
        {"tag":"Sonntag","name":"Arkonaplatz Flohmarkt","adresse":"Arkonaplatz, 10435 Berlin","wann":"Jeden So, 10:00–16:00","telefon":"+49 30 7861003","typ":"🏛️ Antiquitäten, Bücher, Raritäten","bewertung":"⭐⭐⭐⭐","tipp":"Klein aber fein — echte Raritäten!","maps":"https://maps.google.com/?q=Arkonaplatz+Flohmarkt+Berlin"},
        {"tag":"Sonntag","name":"Nowkoelln Flowmarkt","adresse":"Maybachufer, 12047 Berlin","wann":"2. & 4. So, 11:00–18:00","telefon":"+49 30 62908811","typ":"🎨 Design, Handmade, Vintage","bewertung":"⭐⭐⭐⭐","tipp":"Kreativ & günstig — gute Kleidung","maps":"https://maps.google.com/?q=Maybachufer+Berlin"},
        {"tag":"Sonntag","name":"Antik & Trödelmarkt Ostbahnhof","adresse":"Erich-Steinfurth-Str. 1, 10243 Berlin","wann":"Fr–So, 9:00–16:00","telefon":"+49 30 2936028","typ":"🛍️ Großer Gemischtmarkt","bewertung":"⭐⭐⭐⭐","tipp":"Sonntags am vollsten — früh kommen!","maps":"https://maps.google.com/?q=Flohmarkt+Ostbahnhof+Berlin"},
    ]

    tage = ["Alle","Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]
    ft10 = st.radio("📅 Tag:", tage, horizontal=True, key="floh_tag")
    st.markdown("---")

    if ft10 == "Alle":
        for tag in tage[1:]:
            tag_m = [m for m in flohmärkte if m["tag"] == tag]
            if tag_m:
                st.markdown(f"### 📅 {tag}")
                for m in tag_m:
                    with st.expander(f"{m['bewertung']} **{m['name']}**"):
                        c1,c2 = st.columns([2,1])
                        with c1:
                            st.markdown(f"📍 {m['adresse']}")
                            st.markdown(f"🕐 {m['wann']}")
                            st.markdown(f"📞 **{m['telefon']}**")
                            st.markdown(f"🏷️ {m['typ']}")
                            st.markdown(f"💡 *{m['tipp']}*")
                        with c2:
                            st.markdown(m['bewertung'])
                            st.link_button("🗺️ Maps", m['maps'], use_container_width=True)
    else:
        for m in [x for x in flohmärkte if x["tag"] == ft10]:
            with st.expander(f"{m['bewertung']} **{m['name']}**"):
                c1,c2 = st.columns([2,1])
                with c1:
                    st.markdown(f"📍 {m['adresse']}")
                    st.markdown(f"🕐 {m['wann']}")
                    st.markdown(f"📞 **{m['telefon']}**")
                    st.markdown(f"🏷️ {m['typ']}")
                    st.markdown(f"💡 *{m['tipp']}*")
                with c2:
                    st.markdown(m['bewertung'])
                    st.link_button("🗺️ Maps", m['maps'], use_container_width=True)

    st.markdown("---")
    fq10 = st.text_input("🤖 Frage:", placeholder="Welcher Markt ist gut für Porzellan?", key="floh_frage")
    if st.button("Fragen", key="floh_btn"):
        if fq10:
            with st.spinner("🤖 Analysiere..."):
                st.markdown(ki(f"Berliner Flohmarkt-Experte. Kurz auf Deutsch: {fq10}"))

# ════════════════════════════════════════════════════════════
# TAB 11 — LOT-RECHNER
# ════════════════════════════════════════════════════════════
with t11:
    st.header("🧮 Lot-Kalkulator")
    st.markdown("Ganze Kiste kaufen? Berechnen Sie ob es sich lohnt!")
    c1,c2 = st.columns(2)
    with c1:
        lot_pr = st.number_input("💸 Preis für Lot (€)", min_value=0.0, value=50.0, key="lot_pr")
        lot_tr = st.number_input("🚗 Transport (€)", min_value=0.0, value=0.0, key="lot_tr")
        lot_st = st.number_input("⏰ Arbeitsstunden", min_value=0.5, value=2.0, step=0.5, key="lot_st")
    with c2:
        lot_be = st.text_area("📦 Was ist im Lot?", placeholder="z.B. 20 Bücher, 5 CDs, altes Geschirr", height=100, key="lot_be")

    c1,c2,c3 = st.columns([3,1,1])
    with c1: neu_art = st.text_input("Artikel", placeholder="z.B. Rosenthal Teller", key="lot_art")
    with c2: neu_min = st.number_input("Min €", min_value=0.0, value=5.0, key="lot_min")
    with c3: neu_max = st.number_input("Max €", min_value=0.0, value=20.0, key="lot_max")

    c1,c2 = st.columns(2)
    with c1:
        if st.button("➕ Artikel hinzufügen", use_container_width=True, key="lot_add"):
            if neu_art:
                st.session_state.lot_artikel.append({"name":neu_art,"min":neu_min,"max":neu_max,"schnitt":(neu_min+neu_max)/2})
                st.rerun()
    with c2:
        if st.button("🗑️ Liste leeren", use_container_width=True, key="lot_clear"):
            st.session_state.lot_artikel = []
            st.rerun()

    if st.session_state.lot_artikel:
        st.markdown("---")
        g_min = g_max = 0
        for a in st.session_state.lot_artikel:
            c1,c2,c3,c4 = st.columns([3,1,1,1])
            c1.markdown(f"**{a['name']}**")
            c2.markdown(f"€{a['min']:.0f}")
            c3.markdown(f"€{a['max']:.0f}")
            c4.markdown(f"Ø€{a['schnitt']:.0f}")
            g_min += a['min']; g_max += a['max']
        g_sch = (g_min + g_max) / 2
        kosten = lot_pr + lot_tr
        gew_min = g_min - kosten; gew_max = g_max - kosten; gew_sch = g_sch - kosten
        stl = gew_sch / lot_st if lot_st > 0 else 0
        st.markdown("---")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Kosten", f"€{kosten:.2f}")
        c2.metric("Wert", f"€{g_min:.0f}–€{g_max:.0f}")
        c3.metric("Gewinn", f"€{gew_min:.0f}–€{gew_max:.0f}")
        c4.metric("Stundenlohn", f"€{stl:.2f}/h")
        if gew_sch > 20 and stl > 10: st.success(f"🟢 LOHNT SICH! Ø€{gew_sch:.0f} Gewinn | €{stl:.2f}/h")
        elif gew_sch > 0: st.warning(f"🟡 GRENZFALL: Ø€{gew_sch:.0f} Gewinn | €{stl:.2f}/h")
        else: st.error(f"🔴 LOHNT NICHT: Verlust €{abs(gew_sch):.0f}")
        if lot_be and st.button("🤖 KI analysiert Lot", use_container_width=True, key="lot_ki"):
            with st.spinner("🤖 Analysiere..."):
                al = "\n".join([f"- {a['name']}: €{a['min']}–€{a['max']}" for a in st.session_state.lot_artikel])
                st.markdown(ki(f"""Lot-Analyse für deutschen Reseller.
Inhalt: {lot_be}\nArtikel:\n{al}\nPreis: €{lot_pr} | Transport: €{lot_tr}
1. Wertvollste Artikel? 2. Fehlende Artikel? 3. Verkaufsstrategie? 4. Ampel 🟢/🟡/🔴? Auf Deutsch."""))

# ════════════════════════════════════════════════════════════
# TAB 12 — KUNDENNACHRICHTEN-KI
# ════════════════════════════════════════════════════════════
with t12:
    st.header("✉️ KI-Kundennachrichten-Assistent")
    st.markdown("Käufer-Nachricht eingeben → KI schreibt die perfekte Antwort!")
    kn_pl   = st.selectbox("Plattform", ["Kleinanzeigen","Vinted","eBay","Facebook"], key="kn_pl")
    kn_art  = st.text_input("Ihr Artikel", placeholder="z.B. Vintage Kamera", key="kn_art")
    kn_preis = st.number_input("Ihr Preis (€)", min_value=0.0, value=50.0, key="kn_preis")
    kn_msg  = st.text_area("📩 Nachricht des Käufers:", placeholder="z.B. 'Ist der Preis verhandelbar?' oder 'Gibt es Mängel?'", height=100, key="kn_msg")
    kn_ziel = st.selectbox("Ziel der Antwort", [
        "Verkauf abschließen (freundlich & überzeugend)",
        "Preis verteidigen (höflich aber bestimmt)",
        "Auf Mängel-Frage antworten (ehrlich & positiv)",
        "Termin vereinbaren (schnell & unkompliziert)",
        "Auf Rabatt-Anfrage reagieren (kleinen Nachlass anbieten)",
    ], key="kn_ziel")

    if st.button("✉️ Perfekte Antwort generieren", type="primary", use_container_width=True, key="kn_btn"):
        if kn_msg:
            with st.spinner("✍️ Generiere Antwort..."):
                antwort = ki(f"""Du hilfst einem deutschen Verkäufer auf {kn_pl}.
Artikel: {kn_art} | Preis: €{kn_preis}
Käufer schrieb: "{kn_msg}"
Ziel: {kn_ziel}

Schreibe eine perfekte Antwort auf Deutsch:
- Professionell und freundlich
- Kurz (max 4 Sätze)
- Ziel erreichen: {kn_ziel}
- Für {kn_pl} angepasst

NUR die fertige Nachricht ausgeben!""")
                st.text_area("📩 Ihre Antwort (kopierfertig):", value=antwort, height=150, key="kn_result")
                st.success("✅ Einfach kopieren und senden!")

# ════════════════════════════════════════════════════════════
# TAB 13 — PREISSENKUNG-PLANER
# ════════════════════════════════════════════════════════════
with t13:
    st.header("📉 KI-Preissenkung-Planer")
    st.markdown("Artikel liegt zu lang? KI sagt wann & wie viel senken!")
    c1,c2 = st.columns(2)
    with c1:
        ps_art   = st.text_input("Artikel", placeholder="z.B. Vintage Stuhl", key="ps_art")
        ps_preis = st.number_input("Aktueller Preis (€)", min_value=1.0, value=45.0, key="ps_preis")
        ps_ek    = st.number_input("Ihr Einkaufspreis (€)", min_value=0.0, value=10.0, key="ps_ek")
    with c2:
        ps_tage  = st.number_input("Liegezeit (Tage)", min_value=0, value=14, key="ps_tage")
        ps_pl    = st.selectbox("Plattform", ["Kleinanzeigen","eBay","Vinted","Facebook"], key="ps_pl")
        ps_views = st.number_input("Bisherige Aufrufe", min_value=0, value=25, key="ps_views")

    if st.button("📉 Preis-Strategie berechnen", type="primary", use_container_width=True, key="ps_btn"):
        with st.spinner("🤖 Analysiere..."):
            r = ki(f"""Preisoptimierungs-Experte für deutschen Secondhand-Markt.
Artikel: {ps_art} | Preis: €{ps_preis} | EK: €{ps_ek}
Plattform: {ps_pl} | Liegezeit: {ps_tage} Tage | Aufrufe: {ps_views}

Erstelle einen konkreten Preissenkungsplan auf Deutsch:

📊 ANALYSE:
• Bewertung: [Warum verkauft es sich nicht?]
• Problem: [Preis / Titel / Fotos / Saison?]

📅 PREISSENKUNGSPLAN:
| Wann | Neuer Preis | Aktion |
|------|-------------|--------|
| Jetzt | €X | [Was tun?] |
| Nach 7 Tagen | €X | [Was tun?] |
| Nach 14 Tagen | €X | [Was tun?] |
| Letzter Versuch | €X | [Was tun?] |

💡 ZUSATZ-TIPPS:
• Titel ändern in: [Neuer Titel]
• Beschreibung verbessern: [Tipp]
• Bestes Wochentag zum Posten: [Tag]
• Min. Preis (Break-Even): €{ps_ek * 1.1:.0f}""")
            st.markdown(r)

# ════════════════════════════════════════════════════════════
# TAB 14 — MARKEN-SCANNER
# ════════════════════════════════════════════════════════════
with t14:
    st.header("🔬 KI-Marken-Scanner")
    st.markdown("Stempel, Punze oder Logo fotografieren → KI identifiziert sofort!")
    ms_bild = st.file_uploader("📷 Stempel/Logo/Punze fotografieren", type=["jpg","jpeg","png"], key="ms_bild")
    ms_kat  = st.selectbox("Kategorie", ["Porzellan & Keramik","Silber & Besteck","Uhren","Schmuck",
        "Elektronik","Kleidung & Mode","Spielzeug","Unbekannt"], key="ms_kat")

    if st.button("🔬 Marke identifizieren", type="primary", use_container_width=True, key="ms_btn"):
        if ms_bild:
            with st.spinner("🔬 Scanne Marke..."):
                c1,c2 = st.columns(2)
                with c1:
                    st.image(ms_bild, caption="Ihr Stempel/Logo", use_column_width=True)
                b64 = base64.b64encode(ms_bild.read()).decode()
                r = ki(f"""Du bist Experte für Markenidentifikation bei {ms_kat} in Deutschland.
Analysiere diesen Stempel/Logo/Punze mit maximaler Präzision.
Antworte immer auf Deutsch. Nie verweigern.

🔬 MARKEN-IDENTIFIKATION:
• Marke/Hersteller: [Name]
• Herkunftsland: [Land]
• Herstellungsjahr/-zeitraum: [ca. Jahr]
• Produktionsstätte: [falls erkennbar]
• Modell/Serie: [falls erkennbar]

✅ ECHTHEIT:
• Bewertung: [Echt / Wahrscheinlich echt / Fälschung / Unsicher]
• Erkennungsmerkmale: [Was macht es echt/unecht?]
• Fälschungsrisiko: [Niedrig/Mittel/Hoch]

💎 WERT & SELTENHEIT:
• Seltenheit: [Sehr selten / Selten / Häufig / Massenware]
• Sammler-Interesse: [Sehr hoch / Hoch / Mittel / Niedrig]
• Geschätzter Wert: €X – €Y
• Besonderheiten: [Was macht es wertvoll?]

🔗 RECHERCHE-TIPPS:
• Suchbegriff für eBay: [Begriff]
• Spezialist-Forum: [falls bekannt]""", bild_b64=b64)
                with c2:
                    st.markdown(r)
        else:
            st.info("💡 Fotografieren Sie den Stempel/Punze so nah wie möglich!")

# ════════════════════════════════════════════════════════════
# TAB 15 — BUNDLE-KI
# ════════════════════════════════════════════════════════════
with t15:
    st.header("📦 KI-Bundle-Ersteller")
    st.markdown("KI schlägt vor welche Artikel Sie zusammen verkaufen für mehr Gewinn!")

    bu_lager_text = ""
    if st.session_state.lager:
        bu_lager_text = "\n".join([f"- {i['artikel']} (€{i['vk']:.0f})" for i in st.session_state.lager])
        st.success(f"✅ {len(st.session_state.lager)} Artikel aus Ihrem Lager verfügbar")
        st.markdown("**Ihre Lager-Artikel:**")
        for i in st.session_state.lager:
            st.markdown(f"- **{i['artikel']}** → €{i['vk']:.2f}")
    else:
        st.info("💡 Fügen Sie zuerst Artikel im Lager-Tab hinzu!")

    bu_extra = st.text_area("Weitere Artikel eingeben (optional):", placeholder="z.B.\n- Vintage Tassen\n- Kuchenteller\n- Zuckerdose", height=100, key="bu_extra")
    bu_ziel  = st.selectbox("Ziel", ["Maximaler Gewinn","Schnellster Verkauf","Beste Plattform"], key="bu_ziel")

    if st.button("📦 Bundle-Strategie erstellen", type="primary", use_container_width=True, key="bu_btn"):
        alle_artikel = bu_lager_text
        if bu_extra: alle_artikel += f"\n{bu_extra}"
        if alle_artikel:
            with st.spinner("🤖 Analysiere Kombinationen..."):
                r = ki(f"""Bundle-Strategie Experte für deutschen Reselling-Markt.
Artikel verfügbar:\n{alle_artikel}
Ziel: {bu_ziel}

Erstelle auf Deutsch:

🎁 OPTIMALE BUNDLE-KOMBINATIONEN:

Bundle 1: [Name]
• Enthält: [Artikel]
• Einzelpreis gesamt: €X
• Bundle-Preis empfohlen: €X
• Mehrgewinn: €X (+X%)
• Beste Plattform: [Plattform]
• Titel: [Fertiger Anzeigentitel]

Bundle 2: [Name]
[gleiche Struktur]

Bundle 3: [Name]
[gleiche Struktur]

💡 STRATEGIE-TIPP: [Welches Bundle zuerst?]""")
                st.markdown(r)
        else:
            st.warning("⚠️ Bitte zuerst Artikel eintragen!")

# ════════════════════════════════════════════════════════════
# TAB 16 — REKLAMATION
# ════════════════════════════════════════════════════════════
with t16:
    st.header("🛡️ KI-Reklamations-Helfer")
    st.markdown("Käufer beschwert sich? KI schreibt die perfekte Antwort!")
    c1,c2 = st.columns(2)
    with c1:
        rek_art  = st.text_input("Artikel", placeholder="z.B. Vintage Kamera", key="rek_art")
        rek_preis = st.number_input("Verkaufspreis (€)", min_value=0.0, value=50.0, key="rek_preis")
        rek_pl   = st.selectbox("Plattform", ["Kleinanzeigen","eBay","Vinted","Facebook"], key="rek_pl")
    with c2:
        rek_typ  = st.selectbox("Art der Beschwerde", [
            "Artikel entspricht nicht Beschreibung",
            "Artikel beschädigt angekommen",
            "Käufer will Rückgabe",
            "Käufer behauptet Fälschung",
            "Versand zu langsam",
            "Preis-Beschwerde nach Kauf",
        ], key="rek_typ")
    rek_msg = st.text_area("📩 Nachricht des Käufers:", height=100, key="rek_msg")

    if st.button("🛡️ Professionelle Antwort erstellen", type="primary", use_container_width=True, key="rek_btn"):
        if rek_msg:
            with st.spinner("✍️ Generiere Antwort..."):
                r = ki(f"""Experte für Käufer-Verkäufer-Kommunikation auf deutschen Plattformen.
Artikel: {rek_art} | Preis: €{rek_preis} | Plattform: {rek_pl}
Beschwerde: {rek_typ}
Käufer schrieb: "{rek_msg}"

Schreibe auf Deutsch:

📝 PROFESSIONELLE ANTWORT (kopierfertig):
[Antwort die den Käufer beruhigt, rechtlich sicher ist, keine Rückgabe provoziert]

⚖️ RECHTLICHE EINSCHÄTZUNG:
• Ihre Pflichten: [Was müssen Sie tun?]
• Ihre Rechte: [Was müssen Sie nicht tun?]
• Empfehlung: [Wie lösen?]

🎯 STRATEGIE: [Wie diesen Fall am besten lösen?]""")
                st.markdown(r)

# ════════════════════════════════════════════════════════════
# TAB 17 — SAISONALES TIMING
# ════════════════════════════════════════════════════════════
with t17:
    st.header("📅 KI-Saisonaler Timing-Planer")
    st.markdown("Wann verkauft man was am besten? KI kennt alle Trends!")
    ti_art  = st.text_input("Artikel eingeben", placeholder="z.B. Weihnachtsdeko, Winterjacke, Gartenmöbel", key="ti_art")
    ti_mo   = st.selectbox("Aktueller Monat", ["Januar","Februar","März","April","Mai","Juni",
        "Juli","August","September","Oktober","November","Dezember"], index=datetime.now().month-1, key="ti_mo")

    if st.button("📅 Besten Verkaufszeitpunkt finden", type="primary", use_container_width=True, key="ti_btn"):
        if ti_art:
            with st.spinner("🤖 Analysiere Saison..."):
                r = ki(f"""Markt-Timing Experte für deutschen Secondhand-Markt.
Artikel: {ti_art} | Aktuell: {ti_mo}

Erstelle auf Deutsch:

📅 SAISONALER TIMING-PLAN:

🟢 BESTE MONATE zum Verkaufen: [Monate + warum]
🟡 MITTLERE MONATE: [Monate]
🔴 SCHLECHTE MONATE: [Monate + warum]

📊 MONAT-FÜR-MONAT ÜBERSICHT:
| Monat | Nachfrage | Preis-Potenzial |
|-------|-----------|-----------------|
[alle 12 Monate]

💡 JETZT IM {ti_mo.upper()}:
• Lohnt sich jetzt zu verkaufen? [Ja/Nein/Warten]
• Wenn warten: Bis wann?
• Erwarteter Mehrerlös durch richtiges Timing: X%

🎯 KONKRETE EMPFEHLUNG für {ti_art} im {ti_mo}:
[Was genau tun?]""")
                st.markdown(r)

# ════════════════════════════════════════════════════════════
# TAB 18 — GEWINN-BUCH
# ════════════════════════════════════════════════════════════
with t18:
    st.header("💰 Gewinn-Tagebuch & Statistiken")
    st.markdown("Alle Käufe und Verkäufe tracken → KI analysiert Ihren Erfolg!")

    c1,c2,c3,c4 = st.columns(4)
    with c1: gb_art  = st.text_input("Artikel", key="gb_art")
    with c2: gb_ek   = st.number_input("EK (€)", min_value=0.0, value=10.0, key="gb_ek")
    with c3: gb_vk   = st.number_input("VK (€)", min_value=0.0, value=35.0, key="gb_vk")
    with c4: gb_pl   = st.selectbox("Plattform", ["Kleinanzeigen","eBay","Vinted","Facebook","Flohmarkt"], key="gb_pl")

    if st.button("✅ Eintragen", type="primary", use_container_width=True, key="gb_btn"):
        if gb_art:
            g = gb_vk - gb_ek - (gb_vk * 0.05)
            st.session_state.gewinn_log.append({
                "datum": datetime.now().strftime("%d.%m.%Y"),
                "artikel": gb_art, "ek": gb_ek, "vk": gb_vk,
                "gewinn": round(g,2), "plattform": gb_pl
            })
            st.success(f"✅ Eingetragen! Gewinn: €{g:.2f}")
            st.rerun()

    if st.session_state.gewinn_log:
        ges_ek  = sum(i["ek"] for i in st.session_state.gewinn_log)
        ges_vk  = sum(i["vk"] for i in st.session_state.gewinn_log)
        ges_g   = sum(i["gewinn"] for i in st.session_state.gewinn_log)
        avg_roi = (ges_g / ges_ek * 100) if ges_ek > 0 else 0

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("📦 Verkäufe", len(st.session_state.gewinn_log))
        c2.metric("💸 Investiert", f"€{ges_ek:.2f}")
        c3.metric("💰 Gewinn", f"€{ges_g:.2f}")
        c4.metric("📈 ROI", f"{avg_roi:.0f}%")

        st.markdown("---")
        plattform_stats = {}
        for i in st.session_state.gewinn_log:
            pl = i["plattform"]
            if pl not in plattform_stats:
                plattform_stats[pl] = {"count":0,"gewinn":0}
            plattform_stats[pl]["count"] += 1
            plattform_stats[pl]["gewinn"] += i["gewinn"]

        st.markdown("### 📊 Nach Plattform:")
        for pl, stats in plattform_stats.items():
            st.markdown(f"- **{pl}**: {stats['count']} Verkäufe | Gewinn: €{stats['gewinn']:.2f}")

        st.markdown("### 📋 Letzte Einträge:")
        for e in reversed(st.session_state.gewinn_log[-10:]):
            farbe = "🟢" if e["gewinn"] > 20 else "🟡" if e["gewinn"] > 0 else "🔴"
            st.markdown(f"{farbe} {e['datum']} | **{e['artikel']}** | EK: €{e['ek']:.0f} → VK: €{e['vk']:.0f} | **+€{e['gewinn']:.2f}** | {e['plattform']}")

        if st.button("🤖 KI-Analyse meiner Verkäufe", use_container_width=True, key="gb_ki"):
            with st.spinner("🤖 Analysiere..."):
                log_text = "\n".join([f"- {e['artikel']}: EK€{e['ek']} VK€{e['vk']} Gewinn€{e['gewinn']} {e['plattform']}" for e in st.session_state.gewinn_log])
                r = ki(f"""Analysiere diese Verkäufe eines deutschen Resellers. Nur Fakten auf Deutsch.
{log_text}

1. Welche Artikel brachten den besten ROI?
2. Welche Plattform war am profitabelsten?
3. Was sollte mehr gekauft/verkauft werden?
4. Konkrete Verbesserungs-Tipps (3 Stück)?""")
                st.markdown(r)

# ════════════════════════════════════════════════════════════
# TAB 19 — ANZEIGEN-OPTIMIERER
# ════════════════════════════════════════════════════════════
with t19:
    st.header("✨ KI-Anzeigen-Optimierer")
    st.markdown("Bestehende Anzeige eingeben → KI verbessert alles → Mehr Klicks & Verkäufe!")
    c1,c2 = st.columns(2)
    with c1:
        ao_pl    = st.selectbox("Plattform", ["Kleinanzeigen","Vinted","eBay","Facebook"], key="ao_pl")
        ao_preis = st.number_input("Aktueller Preis (€)", min_value=0.0, value=45.0, key="ao_preis")
    with c2:
        ao_kat   = st.selectbox("Kategorie", ["Haushalt & Porzellan","Kleidung & Mode",
            "Elektronik","Möbel & Deko","Spielzeug & Bücher","Sonstiges"], key="ao_kat")
        ao_tage  = st.number_input("Tage online ohne Verkauf", min_value=0, value=7, key="ao_tage")

    ao_titel = st.text_input("📝 Aktueller Titel:", placeholder="z.B. 'Teller zu verkaufen'", key="ao_titel")
    ao_text  = st.text_area("📄 Aktuelle Beschreibung:", placeholder="Fügen Sie Ihre aktuelle Beschreibung ein...", height=120, key="ao_text")

    if st.button("✨ Anzeige optimieren", type="primary", use_container_width=True, key="ao_btn"):
        if ao_titel or ao_text:
            with st.spinner("✨ Optimiere Ihre Anzeige..."):
                r = ki(f"""Experte für Verkaufsanzeigen auf deutschen Plattformen ({ao_pl}).
Kategorie: {ao_kat} | Preis: €{ao_preis} | Seit {ao_tage} Tagen online ohne Verkauf.

ORIGINAL-ANZEIGE:
Titel: {ao_titel}
Beschreibung: {ao_text}

Optimiere diese Anzeige vollständig. Auf Deutsch.

━━━━━━━━━━━━━━━━━━━━━━━━
📊 ANALYSE DER ORIGINAL-ANZEIGE:
• Schwächen: [Was ist schlecht?]
• Note: X/10
━━━━━━━━━━━━━━━━━━━━━━━━

✨ OPTIMIERTER TITEL (max 60 Zeichen):
[Neuer Titel — verkaufsoptimiert mit Keywords]

✨ OPTIMIERTE BESCHREIBUNG:
[Neue Beschreibung — überzeugend, vollständig, alle Keywords drin]

💰 PREIS-EMPFEHLUNG:
• Aktueller Preis: €{ao_preis}
• Empfohlener Preis: €X
• Begründung: [Warum?]

🏷️ KEYWORDS für {ao_pl}:
[5-8 relevante Suchbegriffe]

💡 ZUSATZ-TIPPS:
• Foto-Verbesserung: [Was fehlt?]
• Bester Posting-Zeitpunkt: [Wann?]
• Erwartete Verbesserung: +X% mehr Klicks""")
                st.markdown(r)
        else:
            st.warning("⚠️ Bitte Titel oder Beschreibung eingeben!")

# ════════════════════════════════════════════════════════════
# TAB 20 — TAGESPLAN
# ════════════════════════════════════════════════════════════
with t20:
    st.header("🗓️ KI-Tagesplan Generator")
    st.markdown("Wochentag + Budget → KI erstellt optimalen Flohmarkt-Tagesplan!")
    c1,c2 = st.columns(2)
    with c1:
        tp_tag    = st.selectbox("Welcher Tag?", ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"], key="tp_tag")
        tp_budget = st.number_input("Budget (€)", min_value=10.0, value=100.0, step=10.0, key="tp_budget")
    with c2:
        tp_fokus  = st.selectbox("Fokus", ["Alles Mögliche","Kleidung & Mode","Porzellan & Antiquitäten",
            "Elektronik & Technik","Möbel & Deko","Bücher & Medien"], key="tp_fokus")
        tp_transport = st.selectbox("Transport", ["Auto","Fahrrad","U-Bahn/Bus","Zu Fuß"], key="tp_tr")

    if st.button("🗓️ Tagesplan erstellen", type="primary", use_container_width=True, key="tp_btn"):
        with st.spinner("🤖 Erstelle optimalen Plan..."):
            r = ki(f"""Berliner Flohmarkt-Experte erstellt optimalen Tagesplan.
Tag: {tp_tag} | Budget: €{tp_budget} | Fokus: {tp_fokus} | Transport: {tp_transport}

Erstelle einen konkreten Tagesplan auf Deutsch:

🗓️ OPTIMALER TAGESPLAN FÜR {tp_tag.upper()}

⏰ ZEITPLAN:
| Zeit | Markt | Adresse | Warum? |
|------|-------|---------|--------|
[Alle empfehlenswerten Märkte für diesen Tag in optimaler Reihenfolge]

💰 BUDGET-AUFTEILUNG:
| Markt | Budget | Fokus |
|-------|--------|-------|
[Wie Budget aufteilen?]

🎯 WAS SUCHEN bei {tp_fokus}:
• [Konkrete Artikel die sich lohnen]
• Gold-Wörter: [Worauf achten?]
• Tipp für {tp_transport}: [Praktische Hinweise]

⚡ TOP-TIPP FÜR HEUTE:
[Der wichtigste Tipp für diesen {tp_tag}]

🏆 ERWARTETES ERGEBNIS:
Mit €{tp_budget:.0f} Budget realistisch: €X–€Y Gewinn möglich""")
            st.markdown(r)

# ── FOOTER ───────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<p style='text-align:center;color:#666'>⚡ MarktRadar OS PRO v5.0 ULTIMATE · Zoran Berlin · "
    f"{datetime.now().strftime('%d.%m.%Y')}</p>",
    unsafe_allow_html=True
)
