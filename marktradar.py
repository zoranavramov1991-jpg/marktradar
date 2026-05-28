# 4. Analyse Logik - REPARIERTE STRUKTUR
if st.button("🚀 EXPERTEN-ANALYSE STARTEN"):
    with st.spinner("Sachverständige prüfen Marktdaten..."):
        try:
            client = Groq(api_key=GROQ_API_KEY)
            
            # 1. Den Text-Teil vorbereiten
            expert_prompt = (
                f"Du bist ein unerbittlicher Gutachter für Resale-Ware. Schrott-Anteil: {defekt_prozent}%.\n"
                f"Analysiere die Bilder und den Kontext extrem konservativ.\n\n"
                f"Aufgabe:\n"
                f"1. Tabelle: [Artikel] | [Zustand] | [Flohmarkt-Preis (Min)] | [Sicherheits-Gebot].\n"
                f"2. Berechne den 'SICHEREN ANKAUFS-WERT': Marktpreis minus 70% Risiko-Abschlag.\n"
                f"3. Nenne das absolute Maximalgebot für den gesamten Posten.\n"
                f"4. Nenne die 3 größten Risiken dieses Deals."
            )
            
            # 2. Die exakt korrekte Struktur für die Groq Vision API
            # WICHTIG: Das Bild MUSS innerhalb des 'content' als Teil der Liste stehen
            message_content = [{"type": "text", "text": expert_prompt}]
            
            if uploaded_files:
                for f in uploaded_files:
                    f.seek(0)
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                    # Bild-Objekt korrekt einfügen
                    message_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                    })

            # 3. API-Aufruf
            # Wir verwenden 'llama-3.2-11b-vision-preview', da dies das Standard-Modell für Bilder ist
            response = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[{"role": "user", "content": message_content}]
            )
            
            st.success("Analyse erfolgreich abgeschlossen.")
            st.markdown("---")
            st.write(response.choices[0].message.content)
            
        except Exception as e:
            st.error(f"Technischer Fehler: {e}")
