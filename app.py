import streamlit as st
from google import genai
from google.genai import types
import requests
import json
import datetime
import random

st.set_page_config(page_title="Türkisch Agent", page_icon="🇹🇷", layout="wide")

GEMINI_API_KEY = "AQ.Ab8RN6IEUjYRk7-brzXFIjVKV3QHb8R5Q8x8kzsVqC3iHfbH9g"
WEBDAV_URL = "https://tubcloud.tu-berlin.de/remote.php/dav/files/6c15e8e8-a12e-103c-98d9-7f3a285a3c9f/Anki/anki_vocab.json"
USERNAME = "b.wolbring"
APP_PASSWORD = "im6zt-2nPKS-zdD8b-jp6j7-oRAG5"

client = genai.Client(api_key=GEMINI_API_KEY)

@st.cache_data(ttl=5)
def load_data_from_nextcloud():
    try:
        res = requests.get(WEBDAV_URL, auth=(USERNAME, APP_PASSWORD))
        if res.status_code == 200:
            data = res.json()
            last_mod = res.headers.get("Last-Modified")
            if not last_mod:
                now = datetime.datetime.now().strftime("%H:%M:%S (%d.%m.%Y)")
                last_mod = f"Zuletzt abgerufen um {now}"
            
            # Abwärtskompatibilität, falls noch alte Listenstruktur existiert
            if isinstance(data, list):
                return {"recent": data, "all": data, "stats": {"total_in_deck": len(data), "total_recent": len(data)}}, last_mod
            return data, last_mod
    except Exception:
        pass
    return {"recent": [], "all": [], "stats": {"total_in_deck": 0, "total_recent": 0}}, "Keine Daten"

vocab_data, last_sync = load_data_from_nextcloud()

# ==========================================
# SIDEBAR: EINSTELLUNGEN & MODUS-AUSWAHL
# ==========================================
st.sidebar.title("🇹🇷 Agent Einstellungen")

# 1. Reload Button
if st.sidebar.button("🔄 Nextcloud Vokabeln neu laden"):
    st.cache_data.clear()
    now_time = datetime.datetime.now().strftime("%H:%M:%S")
    st.sidebar.success(f"Vokabeln um {now_time} Uhr neu geladen!")
    st.rerun()

st.sidebar.caption(f"Status: {last_sync}")
st.sidebar.divider()

# 2. Vokabel-Modus wählen
st.sidebar.subheader("🎯 Vokabel-Fokus")
vocab_mode = st.sidebar.radio(
    "Welche Vokabeln soll der Bot nutzen?",
    [
        "🔥 Kürzlich gelernt / wiederholt",
        "🎲 Zufallsmix aus ALLEN Karten (gesamter Stapel)"
    ]
)

if "Kürzlich" in vocab_mode:
    active_pool = vocab_data.get("recent", [])
else:
    active_pool = vocab_data.get("all", [])

# Zufällige Durchmischung, falls "Alle Karten" gewählt ist
if "Zufallsmix" in vocab_mode and active_pool:
    active_pool = random.sample(active_pool, len(active_pool))

max_vocab = st.sidebar.slider(
    "Anzahl Vokabeln im Prompt:",
    min_value=5,
    max_value=max(len(active_pool), 10) if active_pool else 50,
    value=min(30, len(active_pool)) if active_pool else 10
)
selected_vocab = active_pool[:max_vocab]

# 3. System-Instruction / Prompt Anweisungen anpassen
st.sidebar.divider()
st.sidebar.subheader("📝 System-Anweisungen")

default_instruction = """Du bist ein türkischer Gesprächspartner und Sprachlehrer.
- Antworte primär auf Türkisch im gewählten Tonfall.
- Baue bevorzugt die angegebenen Vokabeln natürlich in das Gespräch ein.
- Wenn Fehler auftreten, korrigiere sie kurz auf Deutsch am Ende deiner Antwort.
- Beende deine Antwort immer mit einer offenen Frage auf Türkisch."""

custom_instruction = st.sidebar.text_area(
    "Verhalten / Regeln des Bots anpassen:",
    value=default_instruction,
    height=170
)

tone = st.sidebar.selectbox(
    "Tonfall / Stil:",
    ["Umgangssprachlich / Slang (Freunde)", "Neutral & Geduldig (Lehrer)", "Sehr formell / Höflich (Siz)", "Sehr spontan & lustig"]
)

# 4. Chat-Verwaltung
st.sidebar.divider()
st.sidebar.subheader("💬 Parallele Chats")

if "chats" not in st.session_state:
    st.session_state.chats = {"Chat 1": []}
if "active_chat" not in st.session_state:
    st.session_state.active_chat = "Chat 1"

new_chat_name = st.sidebar.text_input("Neuer Chat-Name", placeholder="z. B. Urlaub, Grammatik...")
if st.sidebar.button("➕ Chat erstellen") and new_chat_name:
    if new_chat_name not in st.session_state.chats:
        st.session_state.chats[new_chat_name] = []
        st.session_state.active_chat = new_chat_name
        st.rerun()

st.session_state.active_chat = st.sidebar.radio("Ausgewählter Chat:", list(st.session_state.chats.keys()))

with st.sidebar.expander("📊 Geladene Vokabeln", expanded=False):
    stats = vocab_data.get("stats", {})
    st.write(f"Gesamt-Stapel in Anki: **{stats.get('total_in_deck', 0)}**")
    st.write(f"Kürzlich gelernt: **{stats.get('total_recent', 0)}**")
    st.write(f"Im Prompt aktiv: **{len(selected_vocab)}**")
    if selected_vocab:
        st.dataframe(selected_vocab)

# ==========================================
# CHAT INTERFACE
# ==========================================
st.title(f"Sohbet: {st.session_state.active_chat}")

current_messages = st.session_state.chats[st.session_state.active_chat]

for msg in current_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_input := st.chat_input("Schreibe auf Türkisch oder frage nach Grammatik..."):
    current_messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    vocab_formatted = "\n".join([f"- {v['tr']} ({v['de']})" for v in selected_vocab])
    
    full_system_instruction = f"""
    {custom_instruction}
    
    GEWÄHLTER TONFALL: {tone}
    
    AKTUELLE VOKABELN AUS ANKI ({vocab_mode}):
    {vocab_formatted}
    """

    with st.chat_message("assistant"):
        with st.spinner("Antwortet..."):
            history_str = "\n".join([f"{m['role']}: {m['content']}" for m in current_messages])
            
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=f"{history_str}\nuser: {user_input}",
                config=types.GenerateContentConfig(
                    system_instruction=full_system_instruction,
                    temperature=0.8
                )
            )
            
            reply = response.text
            st.markdown(reply)
            current_messages.append({"role": "assistant", "content": reply})
