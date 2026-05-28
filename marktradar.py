from groq import Groq # Stelle sicher, dass 'groq' in requirements.txt steht!

# ... (dein Code von oben) ...

if st.button("Cloud-KI Analyse starten"):
    if link:
        st.write("Analyse läuft...")
        text = extrahiere_webseiten_text(link)
        
        # KI-Aufruf
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": f"Analysiere diese Auktion: {text}"}]
        )
        st.success(response.choices[0].message.content)
    else:
        st.warning("Bitte gib einen Link ein.")
