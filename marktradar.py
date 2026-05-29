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
def ki(prompt, bild_b64=None, alle_bilder=None):
    """KI-Analyse - unterstützt 1 oder mehrere Bilder"""
    try:
        if not OPENROUTER_KEY:
            return "❌ Kein API-Key konfiguriert!"
        client = OpenAI(api_key=OPENROUTER_KEY, base_url="https://openrouter.ai/api/v1")

        # Mehrere Bilder
        if alle_bilder and len(alle_bilder) > 0:
            model = "openai/gpt-4o"
            inhalt = []
            for b64 in alle_bilder:
                inhalt.append({"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}","detail":"high"}})
            inhalt.append({"type":"text","text":prompt})
            msgs = [{"role":"user","content":inhalt}]

        # Ein Bild
        elif bild_b64:
            model = "openai/gpt-4o"
            msgs  = [{"role":"user","content":[
                {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{bild_b64}","detail":"high"}},
                {"type":"text","text":prompt}]}]
        # Nur Text
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
t1, t2, t3, t4, t5, t6, t7, t8, t9, t10, t11 = st.tabs([
    "🔍 Artikel Analyse",
    "💬 Anschreib-Bot",
    "📦 Lager",
    "📚 OCR Scanner",
    "🔧 Reparatur",
    "📦 Post-Duell",
    "📈 Trends",
    "🎭 Verhandlungs-Sim",
    "📸 Foto-Coach",
    "🗺️ Flohmarkt Berlin",
    "🧮 Lot-Kalkulator"
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
            "📷 Fotos hochladen (mehrere möglich — alle bleiben!)",
            type=["jpg","jpeg","png","webp"],
            accept_multiple_files=True
        )
        if bild_input:
            st.success(f"✅ {len(bild_input)} Foto(s) geladen")
            cols = st.columns(min(len(bild_input), 4))
            for idx, img in enumerate(bild_input):
                with cols[idx % 4]:
                    st.image(img, caption=f"Foto {idx+1}", use_column_width=True)

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

            # ── STUFE 2: TIEFEN-SCAN - Jeder Artikel einzeln ──
            with st.status("🔬 Stufe 2: Tiefen-Scan läuft — jeder Artikel wird einzeln erfasst...", expanded=True):

                kontext_text = f"\n\nINFO VON WEBSEITE:\n{artikel_info[:3000]}" if artikel_info else ""

                # Defekt-Beschreibung
                defekt_text = ""
                if defekt <= 20:
                    defekt_beschr = f"Fast neu / Wie neu ({defekt}% Defektgrad)"
                elif defekt <= 40:
                    defekt_beschr = f"Leicht gebraucht, kleine Mängel ({defekt}% Defektgrad)"
                elif defekt <= 60:
                    defekt_beschr = f"Deutlich gebraucht, sichtbare Mängel ({defekt}% Defektgrad)"
                elif defekt <= 80:
                    defekt_beschr = f"Stark beschädigt, größere Mängel ({defekt}% Defektgrad)"
                else:
                    defekt_beschr = f"Fast unbrauchbar, total defekt ({defekt}% Defektgrad)"

                zusatz = ""
                if beschreibung:
                    zusatz += f"\n\nHÄNDLER BESCHREIBUNG: {beschreibung}"
                zusatz += f"\nDEFEKT-GRAD: {defekt}% — {defekt_beschr}"

                prompt_scan = f"""Du bist ein Experten-Scanner für einen deutschen Reselling-Händler.
Analysiere das Bild mit maximaler Präzision. Erkenne JEDEN sichtbaren Gegenstand.
Antworte IMMER vollständig auf Deutsch. Nie auf Englisch. Nie verweigern.
Bei Screenshots: extrahiere alle Produkt- und Preisinformationen.
Bei Fotos: scanne jeden einzelnen Artikel von links nach rechts, oben nach unten.
Bei mehreren Fotos: alle Fotos zusammen analysieren, Artikel nicht doppelt zählen.
Foto 1, Foto 2 usw. wenn nötig unterscheiden.{kontext_text}{zusatz}

WICHTIG FÜR PREISBERECHNUNG: Der Händler hat den Defektgrad mit {defekt}% angegeben ({defekt_beschr}).
Berücksichtige das bei allen Preisschätzungen — ein höherer Defektgrad = niedrigere Preise!

SCHRITT 1 — INVENTAR-LISTE:
Zähle zuerst alle sichtbaren Artikel auf (nummeriert):
1. [Artikel]
2. [Artikel]
usw.

SCHRITT 2 — KURZBESCHREIBUNG (für jeden Artikel, 2-3 Sätze):
Schreibe für jeden Artikel eine kurze, klare Beschreibung:
• Was ist es genau?
• Was fällt sofort auf? (Besonderheiten, Marke, Zustand)
• Warum ist es interessant oder nicht?

SCHRITT 3 — DETAIL-ANALYSE für jeden Artikel:

═══════════════════════════════════════════
ARTIKEL [N]: [NAME IN GROSSBUCHSTABEN]
═══════════════════════════════════════════

📌 KURZBESCHREIBUNG:
[2-3 Sätze: Was ist es? Was fällt auf? Besonderheiten?]

🔍 IDENTIFIKATION (maximum detail):
• Exakte Bezeichnung: [Was ist es?]
• Marke/Hersteller: [Name + Herkunftsland]
• Modell/Serie: [falls erkennbar]
• Material: [genaues Material]
• Farbe/Design: [Beschreibung]
• Maße (geschätzt): [Größe/Gewicht]
• Stempel/Logos/Punzen: [alles was sichtbar ist]
• Seriennummer/Codes: [falls sichtbar]
• Echtheit: [Echt ✓ / Wahrscheinlich echt / Replik ✗ / Unsicher ?]

📅 ALTERSBESTIMMUNG:
• Herstellungsjahr: [Genaues Jahr ODER "ca. 1965" ODER "1960-1970"]
• Epoche: [z.B. "Westdeutschland 1950er" / "DDR 1970er" / "80er Jahre" / "Modern 2000+"]
• Altersbeweis: [Konkrete Merkmale: Schriftart, Design, Material, Stempel, Farben]

🚦 MARKTBEWERTUNG:
• Ampel: [🟢 GRÜN / 🟡 GELB / 🔴 ROT]
• Verkaufszeit: [🟢 1-7 Tage / 🟡 1-4 Wochen / 🔴 1-3 Monate]
• Nachfrage: [Sehr hoch / Hoch / Mittel / Niedrig / Kaum]
• Zielgruppe: [Wer kauft das? z.B. Sammler, Vintage-Fans, Haushalte]
• Besonderheit: [Was macht es wertvoll/wertlos?]

💶 PREISTABELLE:
| Plattform | Min | Max | Schnitt |
|-----------|-----|-----|---------|
| eBay DE | €X | €Y | €Z |
| Kleinanzeigen | €X | €Y | €Z |
| Vinted | €X | €Y | €Z |
| Facebook | €X | €Y | €Z |
| Flohmarkt | €X | €Y | €Z |
| **Max. Ankauf** | | | **€Z** |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🏆 GESAMT-AUSWERTUNG ALLER ARTIKEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
| Ampel | Anzahl | Wert |
|-------|--------|------|
| 🟢 Schnell (1-7 Tage) | X | €X–€Y |
| 🟡 Mittel (1-4 Wochen) | X | €X–€Y |
| 🔴 Langsam (1-3 Monate) | X | €X–€Y |

• Gesamtwert alle Artikel: €X – €Y
• Maximaler Ankaufspreis gesamt: €X
• Wertvollster Artikel: [Name] (€X)
• Schnellster Verkauf: [Name] (🟢 X Tage)
• Ältester Artikel: [Name] (ca. [Jahr])
• Seltenster Fund: [Name + warum selten]"""

                with st.spinner(f"🔬 Scanne {len(alle_bilder) if alle_bilder else 0} Foto(s)..."):
                    scan_ergebnis = ki(prompt_scan, bild_b64=bild_b64, alle_bilder=alle_bilder if alle_bilder else None)

                st.markdown(scan_ergebnis)
                st.session_state["letzte_analyse"] = scan_ergebnis

                # Suchbegriff für Stufe 3 extrahieren
                suchbegriff = "Vintage Artikel"
                for line in scan_ergebnis.split("\n"):
                    if "ARTIKEL 1:" in line or "Artikel 1:" in line:
                        parts = line.split(":")
                        if len(parts) > 1:
                            suchbegriff = parts[1].strip().strip("*[] ").split("\n")[0][:40]
                        break

            # ── STUFE 3: Plattform-Recherche ──
            with st.status("📡 Stufe 3: Preise auf allen Plattformen recherchieren...", expanded=True):

                ka_url     = f"https://www.kleinanzeigen.de/s-{urllib.parse.quote(suchbegriff)}/k0"
                vinted_url = f"https://www.vinted.de/catalog?search_text={urllib.parse.quote(suchbegriff)}"
                fb_url     = f"https://www.facebook.com/marketplace/search/?query={urllib.parse.quote(suchbegriff)}"
                ebay_url   = f"https://www.ebay.de/sch/i.html?_nkw={urllib.parse.quote(suchbegriff)}&LH_Complete=1&LH_Sold=1"

                st.markdown(f"### 🔗 Suche nach: **{suchbegriff}**")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"🛒 [eBay beendete Verkäufe →]({ebay_url})")
                    st.markdown(f"📱 [Kleinanzeigen →]({ka_url})")
                with col2:
                    st.markdown(f"👗 [Vinted →]({vinted_url})")
                    st.markdown(f"👥 [Facebook →]({fb_url})")

                # KI Marktrecherche
                markt = ki(f"""Marktpreis-Recherche für deutsche Plattformen.
Artikel: "{suchbegriff}"
Nur Fakten, keine Empfehlungen. Auf Deutsch.

Realistische Preise:
• eBay DE (beendete Verkäufe): €X – €Y
• Kleinanzeigen: €X – €Y
• Vinted: €X – €Y
• Facebook: €X – €Y
• Flohmarkt: €X – €Y
• Max. Ankaufspreis: €X

🚦 Ampel: [🟢/🟡/🔴] + Begründung (1 Satz)
⏱️ Typische Verkaufszeit: [X Tage/Wochen]""")

                st.markdown("### 💡 Markt-Recherche:")
                st.markdown(markt)

            # ── STUFE 4: Zusammenfassung ──
            with st.status("✅ Stufe 4: Zusammenfassung...", expanded=True):

                zusammen = ki(f"""Erstelle eine kurze Zusammenfassung für diesen Händler.
Analyse: {scan_ergebnis[:800]}
Nur Fakten. Kein Ratschlag. Auf Deutsch. Max 5 Zeilen.
Format:
• Artikel gefunden: X
• 🟢 Schnell: [Namen]
• 🟡 Mittel: [Namen]
• 🔴 Langsam: [Namen]
• Gesamtwert: €X – €Y""")

                st.info(f"📊 {zusammen}")

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
# TAB 4 — LAGER
# ══════════════════════════════════════════════════════════════
with t3:
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
with t4:
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
with t5:
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
with t6:
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
with t7:
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

# ══════════════════════════════════════════════════════════════
# TAB 8 — VERHANDLUNGS-SIMULATOR
# ══════════════════════════════════════════════════════════════
with t8:
    st.header("🎭 KI-Verhandlungs-Simulator")
    st.markdown("Üben Sie Verhandlungen — KI spielt den Verkäufer!")

    col1, col2 = st.columns(2)
    with col1:
        sim_artikel   = st.text_input("Artikel", placeholder="z.B. Vintage Kamera", key="sim_art")
        sim_preis_vk  = st.number_input("Verkäufer-Preis (€)", min_value=1.0, value=80.0, key="sim_vk")
        sim_ziel      = st.number_input("Ihr Ziel-Preis (€)", min_value=1.0, value=40.0, key="sim_ziel")
    with col2:
        sim_typ = st.selectbox("Verkäufer-Typ", [
            "Sturköpfig — gibt kaum nach",
            "Freundlich — aber realistisch",
            "Gestresst — will schnell verkaufen",
            "Unentschlossen — unsicher über Wert",
            "Professioneller Händler — kennt Preise"
        ], key="sim_typ")
        sim_plattform = st.selectbox("Wo?", ["Flohmarkt persönlich", "Kleinanzeigen Chat", "Facebook"], key="sim_pl")

    if "sim_verlauf" not in st.session_state:
        st.session_state.sim_verlauf = []

    if st.button("🎭 Neue Simulation starten", type="primary", use_container_width=True):
        st.session_state.sim_verlauf = []
        if sim_artikel:
            start_msg = ki(f"""Du spielst einen deutschen Verkäufer auf {sim_plattform}.
Du verkaufst: {sim_artikel} für €{sim_preis_vk}.
Dein Typ: {sim_typ}
Schreibe NUR deine erste Verkäufer-Antwort (2-3 Sätze) wenn ein Käufer fragt ob der Preis verhandelbar ist.
Auf Deutsch. Bleib in der Rolle!""")
            st.session_state.sim_verlauf.append({"rolle": "🏪 Verkäufer", "text": start_msg})

    if st.session_state.sim_verlauf:
        st.markdown("---")
        st.markdown("### 💬 Verhandlungs-Verlauf:")
        for msg in st.session_state.sim_verlauf:
            if msg["rolle"] == "🏪 Verkäufer":
                st.info(f"**{msg['rolle']}:** {msg['text']}")
            else:
                st.success(f"**{msg['rolle']}:** {msg['text']}")

        mein_angebot = st.text_input("✍️ Ihre Antwort:", placeholder="z.B. 'Würden Sie €45 akzeptieren?'", key="sim_input")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 Senden", type="primary", use_container_width=True):
                if mein_angebot:
                    st.session_state.sim_verlauf.append({"rolle": "🛒 Sie", "text": mein_angebot})
                    verlauf_text = "\n".join([f"{m['rolle']}: {m['text']}" for m in st.session_state.sim_verlauf])
                    antwort = ki(f"""Du spielst Verkäufer ({sim_typ}) von {sim_artikel} (Preis: €{sim_preis_vk}).
Verlauf bisher:\n{verlauf_text}
Antworte als Verkäufer (2-3 Sätze). Auf Deutsch. In der Rolle bleiben!
Dein Minimalpreis intern: €{sim_ziel + (sim_preis_vk - sim_ziel) * 0.3:.0f}""")
                    st.session_state.sim_verlauf.append({"rolle": "🏪 Verkäufer", "text": antwort})
                    st.rerun()

        with col2:
            if st.button("🧠 KI-Strategie anzeigen", use_container_width=True):
                verlauf_text = "\n".join([f"{m['rolle']}: {m['text']}" for m in st.session_state.sim_verlauf])
                strategie = ki(f"""Analysiere diese Verhandlung als Experte.
Artikel: {sim_artikel} | Verkäufer-Preis: €{sim_preis_vk} | Ziel: €{sim_ziel}
Verlauf:\n{verlauf_text}

Gib auf Deutsch:
1. Was lief gut?
2. Was hätte besser sein können?
3. Optimale nächste Nachricht um €{sim_ziel} zu erreichen""")
                st.markdown("### 🧠 KI-Strategie:")
                st.markdown(strategie)

# ══════════════════════════════════════════════════════════════
# TAB 9 — FOTO-COACH
# ══════════════════════════════════════════════════════════════
with t9:
    st.header("📸 Profi-Foto-Coach")
    st.markdown("Foto hochladen → KI sagt wie Sie es besser machen für maximalen Verkaufspreis!")

    foto_coach = st.file_uploader("📷 Ihr aktuelles Foto hochladen", type=["jpg","jpeg","png"], key="foto_coach")
    foto_plattform = st.selectbox("Für welche Plattform?", ["Kleinanzeigen", "Vinted", "Facebook", "Alle"], key="foto_pl")

    if st.button("📸 Foto analysieren & verbessern", type="primary", use_container_width=True):
        if foto_coach:
            with st.spinner("🔍 Analysiere Ihr Foto..."):
                b64 = base64.b64encode(foto_coach.read()).decode()
                col1, col2 = st.columns(2)
                with col1:
                    foto_coach.seek(0)
                    st.image(foto_coach, caption="Ihr aktuelles Foto", use_column_width=True)

                analyse_foto = ki(f"""Du bist Experte für Produkt-Fotografie auf deutschen Secondhand-Plattformen.
Analysiere dieses Verkaufsfoto für {foto_plattform}.
Antworte auf Deutsch.

## 📊 FOTO-BEWERTUNG (Note 1-10):
- Helligkeit: X/10
- Hintergrund: X/10
- Schärfe: X/10
- Winkel: X/10
- Gesamteindruck: X/10

## ❌ PROBLEME:
[Was ist schlecht am aktuellen Foto?]

## ✅ SOFORT-VERBESSERUNGEN (konkret):
1. [Verbesserung]
2. [Verbesserung]
3. [Verbesserung]

## 📱 PERFEKTES FOTO - So machen Sie es:
- Hintergrund: [Was nehmen?]
- Licht: [Wie aufstellen?]
- Winkel: [Von wo fotografieren?]
- Extras: [Was noch zeigen? Stempel, Details etc.]
- Tageszeit: [Wann am besten?]

## 💰 PREIS-AUSWIRKUNG:
Mit perfektem Foto könnten Sie X% mehr erzielen.""", bild_b64=b64)

                st.markdown(analyse_foto)
        else:
            st.info("💡 Laden Sie ein Foto hoch das Sie verbessern möchten!")

# ══════════════════════════════════════════════════════════════
# TAB 10 — BERLIN FLOHMARKT-KALENDER
# ══════════════════════════════════════════════════════════════
with t10:
    st.header("🗺️ Berlin Flohmarkt-Kalender")
    st.markdown("Alle wichtigen Flohmärkte in Berlin — immer aktuell!")

    # Nach Wochentag sortiert
    flohmärkte = [
        # ── MONTAG ──
        {
            "tag": "Montag",
            "name": "Flohmarkt am Rathaus Steglitz",
            "adresse": "Schloßstraße 37, 12163 Berlin",
            "wann": "Montag – Samstag, 9:00 – 18:00 Uhr",
            "telefon": "+49 30 79706820",
            "typ": "🏠 Haushalt, Kleidung, Bücher",
            "bewertung": "⭐⭐⭐",
            "tipp": "Günstige Alltagsartikel, gut für Haushaltswaren",
            "maps": "https://maps.google.com/?q=Rathaus+Steglitz+Berlin"
        },
        {
            "tag": "Montag",
            "name": "Trödelmarkt Berliner Straße",
            "adresse": "Berliner Str. 16, 10715 Berlin",
            "wann": "Montag – Freitag, 10:00 – 17:00 Uhr",
            "telefon": "+49 30 8537240",
            "typ": "🛍️ Gemischt, Antiquitäten, Haushalt",
            "bewertung": "⭐⭐⭐",
            "tipp": "Kleine Händler, gute Verhandlungsbasis",
            "maps": "https://maps.google.com/?q=Berliner+Straße+16+Berlin"
        },
        # ── DIENSTAG ──
        {
            "tag": "Dienstag",
            "name": "Flohmarkt Fehrbelliner Platz",
            "adresse": "Fehrbelliner Platz, 10707 Berlin",
            "wann": "Dienstag & Freitag, 8:00 – 15:00 Uhr",
            "telefon": "+49 30 28097272",
            "typ": "🏺 Antiquitäten, Porzellan, Schmuck",
            "bewertung": "⭐⭐⭐⭐",
            "tipp": "Top für Porzellan & Silber — früh kommen!",
            "maps": "https://maps.google.com/?q=Fehrbelliner+Platz+Berlin"
        },
        {
            "tag": "Dienstag",
            "name": "Antikmarkt Charlottenburg",
            "adresse": "Kantstraße 17, 10623 Berlin",
            "wann": "Dienstag – Samstag, 10:00 – 18:00 Uhr",
            "telefon": "+49 30 3138030",
            "typ": "🏛️ Antiquitäten, Kunst, Sammlerstücke",
            "bewertung": "⭐⭐⭐⭐",
            "tipp": "Hochwertige Antiquitäten, gute Preise möglich",
            "maps": "https://maps.google.com/?q=Kantstraße+17+Berlin"
        },
        # ── MITTWOCH ──
        {
            "tag": "Mittwoch",
            "name": "Flohmarkt Alexanderplatz",
            "adresse": "Alexanderplatz, 10178 Berlin",
            "wann": "Täglich, 10:00 – 19:00 Uhr",
            "telefon": "+49 30 24632425",
            "typ": "🏙️ Gemischt, Vintage, Souvenirs",
            "bewertung": "⭐⭐⭐",
            "tipp": "Täglich offen — spontane Käufe möglich",
            "maps": "https://maps.google.com/?q=Alexanderplatz+Flohmarkt+Berlin"
        },
        {
            "tag": "Mittwoch",
            "name": "Trödelmarkt Spandau",
            "adresse": "Carl-Schurz-Str. 13, 13597 Berlin",
            "wann": "Mittwoch & Samstag, 8:00 – 14:00 Uhr",
            "telefon": "+49 30 3545080",
            "typ": "🔧 Werkzeug, Haushalt, Kleidung",
            "bewertung": "⭐⭐⭐",
            "tipp": "Günstige Werkzeuge & Haushaltswaren",
            "maps": "https://maps.google.com/?q=Carl-Schurz-Straße+Spandau+Berlin"
        },
        # ── DONNERSTAG ──
        {
            "tag": "Donnerstag",
            "name": "Flohmarkt am Fehrbelliner Platz",
            "adresse": "Fehrbelliner Platz, 10707 Berlin",
            "wann": "Dienstag & Freitag, 8:00 – 15:00 Uhr",
            "telefon": "+49 30 28097272",
            "typ": "🏺 Antiquitäten, Porzellan, Schmuck",
            "bewertung": "⭐⭐⭐⭐",
            "tipp": "Auch Donnerstags manchmal geöffnet — anrufen!",
            "maps": "https://maps.google.com/?q=Fehrbelliner+Platz+Berlin"
        },
        {
            "tag": "Donnerstag",
            "name": "Trödelmarkt Schöneberg",
            "adresse": "Winterfeldtplatz, 10781 Berlin",
            "wann": "Donnerstag (klein) & Samstag (groß), 8:00 – 14:00 Uhr",
            "telefon": "+49 30 7262290",
            "typ": "🌿 Bio, Vintage, Haushalt, Mode",
            "bewertung": "⭐⭐⭐⭐",
            "tipp": "Donnerstags ruhiger und günstiger als Samstag",
            "maps": "https://maps.google.com/?q=Winterfeldtplatz+Berlin"
        },
        # ── FREITAG ──
        {
            "tag": "Freitag",
            "name": "Flohmarkt am Fehrbelliner Platz",
            "adresse": "Fehrbelliner Platz, 10707 Berlin",
            "wann": "Dienstag & Freitag, 8:00 – 15:00 Uhr",
            "telefon": "+49 30 28097272",
            "typ": "🏺 Antiquitäten, Porzellan, Schmuck",
            "bewertung": "⭐⭐⭐⭐⭐",
            "tipp": "Freitags am besten! Frisch aufgebaut, beste Auswahl",
            "maps": "https://maps.google.com/?q=Fehrbelliner+Platz+Berlin"
        },
        {
            "tag": "Freitag",
            "name": "Antik & Trödelmarkt Ostbahnhof",
            "adresse": "Erich-Steinfurth-Str. 1, 10243 Berlin",
            "wann": "Freitag – Sonntag, 9:00 – 16:00 Uhr",
            "telefon": "+49 30 2936028",
            "typ": "🛍️ Großer Gemischtmarkt",
            "bewertung": "⭐⭐⭐⭐",
            "tipp": "Freitags die wenigsten Leute — beste Verhandlung!",
            "maps": "https://maps.google.com/?q=Flohmarkt+Ostbahnhof+Berlin"
        },
        # ── SAMSTAG ──
        {
            "tag": "Samstag",
            "name": "RAW Flohmarkt",
            "adresse": "Revaler Str. 99, 10245 Berlin",
            "wann": "Samstag & Sonntag, 10:00 – 18:00 Uhr",
            "telefon": "+49 30 29367840",
            "typ": "🕶️ Vintage Mode, Vinyl, Streetwear",
            "bewertung": "⭐⭐⭐⭐⭐",
            "tipp": "BESTE Quelle für Vintage-Kleidung in Berlin!",
            "maps": "https://maps.google.com/?q=RAW+Gelände+Berlin"
        },
        {
            "tag": "Samstag",
            "name": "Winterfeldtmarkt",
            "adresse": "Winterfeldtplatz, 10781 Berlin",
            "wann": "Jeden Samstag, 8:00 – 14:00 Uhr",
            "telefon": "+49 30 7262290",
            "typ": "🌿 Bio, Vintage, Haushalt, Mode, Kunst",
            "bewertung": "⭐⭐⭐⭐⭐",
            "tipp": "Einer der besten Berliner Märkte — Pflicht!",
            "maps": "https://maps.google.com/?q=Winterfeldtmarkt+Berlin"
        },
        {
            "tag": "Samstag",
            "name": "Antik & Trödelmarkt Ostbahnhof",
            "adresse": "Erich-Steinfurth-Str. 1, 10243 Berlin",
            "wann": "Freitag – Sonntag, 9:00 – 16:00 Uhr",
            "telefon": "+49 30 2936028",
            "typ": "🛍️ Großer Gemischtmarkt",
            "bewertung": "⭐⭐⭐⭐",
            "tipp": "Groß & günstig — viel Auswahl für alle Kategorien",
            "maps": "https://maps.google.com/?q=Flohmarkt+Ostbahnhof+Berlin"
        },
        {
            "tag": "Samstag",
            "name": "Trödelmarkt Spandau",
            "adresse": "Carl-Schurz-Str. 13, 13597 Berlin",
            "wann": "Mittwoch & Samstag, 8:00 – 14:00 Uhr",
            "telefon": "+49 30 3545080",
            "typ": "🔧 Werkzeug, Haushalt, Kleidung",
            "bewertung": "⭐⭐⭐",
            "tipp": "Samstags viel größer als Mittwoch",
            "maps": "https://maps.google.com/?q=Carl-Schurz-Straße+Spandau+Berlin"
        },
        # ── SONNTAG ──
        {
            "tag": "Sonntag",
            "name": "Mauerpark Flohmarkt",
            "adresse": "Bernauer Str. 63-64, 13355 Berlin",
            "wann": "Jeden Sonntag, 9:00 – 18:00 Uhr",
            "telefon": "+49 30 40505380",
            "typ": "🎭 Gemischt — Vintage, Kleidung, Kuriositäten",
            "bewertung": "⭐⭐⭐⭐⭐",
            "tipp": "MUSS! Vor 10 Uhr kommen für beste Funde",
            "maps": "https://maps.google.com/?q=Mauerpark+Flohmarkt+Berlin"
        },
        {
            "tag": "Sonntag",
            "name": "Flohmarkt am Boxhagener Platz",
            "adresse": "Boxhagener Platz, 10245 Berlin",
            "wann": "Jeden Sonntag, 10:00 – 18:00 Uhr",
            "telefon": "+49 30 29362596",
            "typ": "🏺 Antiquitäten, Porzellan, Bücher",
            "bewertung": "⭐⭐⭐⭐⭐",
            "tipp": "Top für Porzellan & Antiquitäten — früh da sein!",
            "maps": "https://maps.google.com/?q=Boxhagener+Platz+Flohmarkt+Berlin"
        },
        {
            "tag": "Sonntag",
            "name": "Treptower Flohmarkt",
            "adresse": "Treptower Park, Alt-Treptow, 12435 Berlin",
            "wann": "Jeden Sonntag, 8:00 – 16:00 Uhr",
            "telefon": "+49 30 5321555",
            "typ": "🔧 Werkzeug, Elektronik, DDR-Artikel",
            "bewertung": "⭐⭐⭐⭐",
            "tipp": "Gut für Elektronik & DDR-Sammlerstücke",
            "maps": "https://maps.google.com/?q=Treptower+Park+Flohmarkt+Berlin"
        },
        {
            "tag": "Sonntag",
            "name": "RAW Flohmarkt",
            "adresse": "Revaler Str. 99, 10245 Berlin",
            "wann": "Samstag & Sonntag, 10:00 – 18:00 Uhr",
            "telefon": "+49 30 29367840",
            "typ": "🕶️ Vintage Mode, Vinyl, Streetwear",
            "bewertung": "⭐⭐⭐⭐⭐",
            "tipp": "Sonntags entspannter als Samstag",
            "maps": "https://maps.google.com/?q=RAW+Gelände+Berlin"
        },
        {
            "tag": "Sonntag",
            "name": "Arkonaplatz Flohmarkt",
            "adresse": "Arkonaplatz, 10435 Berlin",
            "wann": "Jeden Sonntag, 10:00 – 16:00 Uhr",
            "telefon": "+49 30 7861003",
            "typ": "🏛️ Antiquitäten, Bücher, Kunst, Raritäten",
            "bewertung": "⭐⭐⭐⭐",
            "tipp": "Klein aber fein — echte Raritäten möglich!",
            "maps": "https://maps.google.com/?q=Arkonaplatz+Flohmarkt+Berlin"
        },
        {
            "tag": "Sonntag",
            "name": "Nowkoelln Flowmarkt",
            "adresse": "Maybachufer, 12047 Berlin",
            "wann": "Jeden 2. & 4. Sonntag, 11:00 – 18:00 Uhr",
            "telefon": "+49 30 62908811",
            "typ": "🎨 Design, Handmade, Vintage",
            "bewertung": "⭐⭐⭐⭐",
            "tipp": "Kreativ & günstig — gute Kleidung & Deko",
            "maps": "https://maps.google.com/?q=Maybachufer+Berlin"
        },
        {
            "tag": "Sonntag",
            "name": "Antik & Trödelmarkt Ostbahnhof",
            "adresse": "Erich-Steinfurth-Str. 1, 10243 Berlin",
            "wann": "Freitag – Sonntag, 9:00 – 16:00 Uhr",
            "telefon": "+49 30 2936028",
            "typ": "🛍️ Großer Gemischtmarkt",
            "bewertung": "⭐⭐⭐⭐",
            "tipp": "Sonntags am vollsten — früh kommen!",
            "maps": "https://maps.google.com/?q=Flohmarkt+Ostbahnhof+Berlin"
        },
    ]


    # Filter nach Wochentag
    tage = ["Alle", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    filter_tag = st.radio("📅 Tag wählen:", tage, horizontal=True, key="floh_tag")

    st.markdown("---")

    # Gefilterte Märkte anzeigen
    gefiltert = [m for m in flohmärkte if filter_tag == "Alle" or m["tag"] == filter_tag]
    st.markdown(f"**{len(gefiltert)} Märkte gefunden**")

    # Nach Tag gruppieren wenn "Alle"
    if filter_tag == "Alle":
        for tag in ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]:
            tag_märkte = [m for m in flohmärkte if m["tag"] == tag]
            if tag_märkte:
                st.markdown(f"### 📅 {tag}")
                for markt in tag_märkte:
                    with st.expander(f"{markt['bewertung']} **{markt['name']}**"):
                        col1, col2 = st.columns([2,1])
                        with col1:
                            st.markdown(f"📍 {markt['adresse']}")
                            st.markdown(f"🕐 {markt['wann']}")
                            st.markdown(f"📞 **{markt['telefon']}**")
                            st.markdown(f"🏷️ {markt['typ']}")
                            st.markdown(f"💡 *{markt['tipp']}*")
                        with col2:
                            st.markdown(markt['bewertung'])
                            st.link_button("🗺️ Maps", markt['maps'], use_container_width=True)
    else:
        for markt in gefiltert:
            with st.expander(f"{markt['bewertung']} **{markt['name']}**"):
                col1, col2 = st.columns([2,1])
                with col1:
                    st.markdown(f"📍 {markt['adresse']}")
                    st.markdown(f"🕐 {markt['wann']}")
                    st.markdown(f"📞 **{markt['telefon']}**")
                    st.markdown(f"🏷️ {markt['typ']}")
                    st.markdown(f"💡 *{markt['tipp']}*")
                with col2:
                    st.markdown(markt['bewertung'])
                    st.link_button("🗺️ Maps", markt['maps'], use_container_width=True)

    st.markdown("---")
    st.markdown("### 🤖 Flohmarkt-Tipps vom KI")
    floh_frage = st.text_input("Frage stellen:", placeholder="Welcher Flohmarkt ist gut für Porzellan?", key="floh_frage")
    if st.button("Fragen", key="floh_btn"):
        if floh_frage:
            with st.spinner("🤖 Analysiere..."):
                st.markdown(ki(f"Berliner Flohmarkt-Experte. Kurze Antwort auf Deutsch: {floh_frage}"))

# ══════════════════════════════════════════════════════════════
# TAB 11 — LOT-KALKULATOR
# ══════════════════════════════════════════════════════════════
with t11:
    st.header("🧮 Lot-Kalkulator")
    st.markdown("Ganze Kiste oder Lot kaufen? Berechnen Sie ob es sich lohnt!")

    col1, col2 = st.columns(2)
    with col1:
        lot_preis     = st.number_input("💸 Preis für das Lot (€)", min_value=0.0, value=50.0, key="lot_preis")
        lot_transport = st.number_input("🚗 Transportkosten (€)", min_value=0.0, value=0.0, key="lot_transport")
        lot_zeit      = st.number_input("⏰ Geschätzte Arbeitszeit (Std.)", min_value=0.5, value=2.0, step=0.5, key="lot_zeit")
    with col2:
        lot_beschr    = st.text_area("📦 Was ist im Lot?", placeholder="z.B. Kiste mit 20 Büchern, 5 CDs, altes Geschirr, Küchenutensilien", height=100, key="lot_beschr")

    st.markdown("### ➕ Artikel im Lot eintragen:")

    if "lot_artikel" not in st.session_state:
        st.session_state.lot_artikel = []

    col1, col2, col3 = st.columns([3,1,1])
    with col1:
        neu_artikel = st.text_input("Artikel-Name", placeholder="z.B. Rosenthal Teller", key="lot_art_neu")
    with col2:
        neu_preis_min = st.number_input("Min €", min_value=0.0, value=5.0, key="lot_min")
    with col3:
        neu_preis_max = st.number_input("Max €", min_value=0.0, value=20.0, key="lot_max")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Artikel hinzufügen", use_container_width=True):
            if neu_artikel:
                st.session_state.lot_artikel.append({
                    "name": neu_artikel,
                    "min": neu_preis_min,
                    "max": neu_preis_max,
                    "schnitt": (neu_preis_min + neu_preis_max) / 2
                })
                st.rerun()
    with col2:
        if st.button("🗑️ Liste leeren", use_container_width=True):
            st.session_state.lot_artikel = []
            st.rerun()

    if st.session_state.lot_artikel:
        st.markdown("---")
        st.markdown("### 📋 Artikel im Lot:")

        gesamt_min = 0
        gesamt_max = 0

        for i, artikel in enumerate(st.session_state.lot_artikel):
            col1, col2, col3, col4 = st.columns([3,1,1,1])
            col1.markdown(f"**{artikel['name']}**")
            col2.markdown(f"Min: €{artikel['min']:.0f}")
            col3.markdown(f"Max: €{artikel['max']:.0f}")
            col4.markdown(f"Ø €{artikel['schnitt']:.0f}")
            gesamt_min += artikel['min']
            gesamt_max += artikel['max']

        gesamt_schnitt = (gesamt_min + gesamt_max) / 2
        gesamtkosten   = lot_preis + lot_transport
        gewinn_min     = gesamt_min - gesamtkosten
        gewinn_max     = gesamt_max - gesamtkosten
        gewinn_schnitt = gesamt_schnitt - gesamtkosten
        stundenlohn    = gewinn_schnitt / lot_zeit if lot_zeit > 0 else 0

        st.markdown("---")
        st.markdown("### 💰 KALKULATION:")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Lot-Kosten", f"€{gesamtkosten:.2f}")
        col2.metric("Verkaufswert", f"€{gesamt_min:.0f} – €{gesamt_max:.0f}")
        col3.metric("Gewinn", f"€{gewinn_min:.0f} – €{gewinn_max:.0f}")
        col4.metric("Stundenlohn", f"€{stundenlohn:.2f}/h")

        st.markdown("---")

        if gewinn_schnitt > 20 and stundenlohn > 10:
            st.success(f"🟢 **LOHNT SICH!** Ø Gewinn: €{gewinn_schnitt:.0f} | Stundenlohn: €{stundenlohn:.2f}/h")
        elif gewinn_schnitt > 0:
            st.warning(f"🟡 **GRENZFALL** Ø Gewinn: €{gewinn_schnitt:.0f} | Stundenlohn: €{stundenlohn:.2f}/h")
        else:
            st.error(f"🔴 **LOHNT NICHT** Verlust: €{abs(gewinn_schnitt):.0f}")

        # KI Analyse des Lots
        if lot_beschr and st.button("🤖 KI analysiert das Lot", use_container_width=True, key="lot_ki"):
            with st.spinner("🤖 Analysiere Lot..."):
                artikel_liste = "\n".join([f"- {a['name']}: €{a['min']}-€{a['max']}" for a in st.session_state.lot_artikel])
                ki_lot = ki(f"""Analysiere dieses Lot für einen deutschen Reseller.
Lot-Inhalt: {lot_beschr}
Eingetragene Artikel:\n{artikel_liste}
Lot-Preis: €{lot_preis} | Transport: €{lot_transport}

Bewerte auf Deutsch:
1. Welche Artikel im Lot sind am wertvollsten?
2. Welche Artikel fehlen vielleicht noch im Lot?
3. Beste Verkaufsstrategie (Einzeln / Sets / Flohmarkt)?
4. Ampel: 🟢/🟡/🔴 — lohnt sich das Lot?""")
                st.markdown(ki_lot)

