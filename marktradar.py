import streamlit as st

st.title("Test-Modus")
st.write("Die App läuft!")

if "GROQ_API_KEY" in st.secrets:
    st.success("API-Key wurde erfolgreich gefunden!")
else:
    st.error("Kein API-Key in den Secrets gefunden.")
