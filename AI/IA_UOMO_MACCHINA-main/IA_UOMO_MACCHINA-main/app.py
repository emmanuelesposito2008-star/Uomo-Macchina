import streamlit as st
from google import genai
from google.genai import types

# ---------------------------------------------------------
# CONFIGURAZIONE PAGINA MOBILE
# ---------------------------------------------------------
st.set_page_config(
    page_title="Fame AI - L'Uomo e la Macchina",
    page_icon="avatars/page_icon.jpg",
    layout="centered",
    initial_sidebar_state="collapsed"
)

if "GEMINI_API_KEY" not in st.secrets:
    st.error("API Key non configurata nei Secrets di Streamlit.")
    st.stop()

# Memorizza il client per non ricrearlo ad ogni messaggio
@st.cache_resource
def get_client():
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

client = get_client()

def load_prompt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read().strip()

# ---------------------------------------------------------
# DATABASE PERSONAGGI E SYSTEM PROMPTS
# ---------------------------------------------------------
PERSONAGGI = {
    "Saverio": {   #Bruno Martelli
        "ruolo": "Musica & Sintetizzatori",
        "avatar": "avatars/01_saverio.png", #bruno_martelli
        "prompt": load_prompt("prompts/bruno_martelli.txt")
    },
    "Carmen Diaz": {
        "ruolo": "Fama & Ambizione",
        "avatar": "avatars/carmen_diaz.png",
        "prompt": load_prompt("prompts/carmen_diaz.txt")
    },
    "Leroy Johnson": {
        "ruolo": "Talento Grezzo & Istinto",
        "avatar": "avatars/leroy_johnson.png",
        "prompt": load_prompt("prompts/leroy_johnson.txt")
    },
    "Doris Finsecker": {
        "ruolo": "Identità & Vulnerabilità",
        "avatar": "avatars/doris_finsecker.png",
        "prompt": load_prompt("prompts/doris_finsecker.txt")
    },
    "Prof. Shorofsky": {
        "ruolo": "Maestro & Tradizione",
        "avatar": "avatars/prof_shorofsky.png",
        "prompt": load_prompt("prompts/prof_shorofsky.txt")
    }
}

USER_AVATAR = "avatars/user.png"

# ---------------------------------------------------------
# INTERFACCIA GRAFICA E LOGICA DI CHAT
# ---------------------------------------------------------
#st.title("🎭 Fame AI: L'Uomo e la Macchina")
#st.caption("Laboratorio Interattivo di Dialogo Filosofico")
col_logo, col_title = st.columns([1, 7], vertical_alignment="center")
with col_logo:
    st.image("avatars/page_icon.jpg", width=64)
with col_title:
    st.subheader("Fame AI: L'Uomo e la Macchina")

scelta_personaggio = st.selectbox(
    "Scegli il personaggio con cui dialogare:",
    options=list(PERSONAGGI.keys()),
    index=0
)

info_char = PERSONAGGI[scelta_personaggio]
col_av, col_info = st.columns([1, 8], vertical_alignment="center")
with col_av:
    st.image(info_char["avatar"], width=48)
with col_info:
    st.info(f"**{scelta_personaggio}** — *{info_char['ruolo']}*")

if "current_char" not in st.session_state or st.session_state.current_char != scelta_personaggio:
    st.session_state.current_char = scelta_personaggio
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=msg.get("avatar")):
        st.markdown(msg["content"])

# Generatore per lo streaming in tempo reale
def stream_risposta(contents, system_prompt):
    response = client.models.generate_content_stream(
        model="gemini-3.5-flash-lite",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=200,
        )
    )
    for chunk in response:
        if chunk.text:
            yield chunk.text

if prompt := st.chat_input("Scrivi un messaggio..."):
    st.session_state.messages.append({"role": "user", "content": prompt, "avatar": USER_AVATAR})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    try:
        # Limita lo storico agli ultimi 6 messaggi per mantenere veloce l'invio
        recent_messages = st.session_state.messages[-6:]
        contents = [
            types.Content(
                role="user" if m["role"] == "user" else "model",
                parts=[types.Part.from_text(text=m["content"])]
            )
            for m in recent_messages
        ]

        with st.chat_message("assistant", avatar=info_char["avatar"]):
            reply_text = st.write_stream(stream_risposta(contents, info_char["prompt"]))

        st.session_state.messages.append({
            "role": "assistant", 
            "content": reply_text, 
            "avatar": info_char["avatar"]
        })

    except Exception as e:
        st.error(f"Errore di connessione: {str(e)}")
