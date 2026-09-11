import streamlit as st
from google import genai
from google.genai import types
import requests
import json
import datetime
import random

st.set_page_config(page_title="Türkisch Agent Pro", page_icon="🇹🇷", layout="wide")

GEMINI_API_KEY = "AQ.Ab8RN6IEUjYRk7-brzXFIjVKV3QHb8R5Q8x8kzsVqC3iHfbH9g"
WEBDAV_URL = "https://tubcloud.tu-berlin.de/remote.php/dav/files/6c15e8e8-a12e-103c-98d9-7f3a285a3c9f/Anki/anki_vocab.json"
EXPORT_WEBDAV_URL = "https://tubcloud.tu-berlin.de/remote.php/dav/files/6c15e8e8-a12e-103c-98d9-7f3a285a3c9f/Anki/anki_new_exports.json"
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
            if isinstance(data, list):
                return {"recent": data, "all": data, "stats": {"total_in_deck": len(data), "total_recent": len(data)}}, last_mod
            return data, last_mod
    except Exception:
        pass
    return {"recent": [], "all": [], "stats": {"total_in_deck": 0, "total_recent": 0}}, "Keine Daten"

vocab_data, last_sync = load_data_from_nextcloud()

if "anki_export_list" not in st.session_state:
    st.session_state.anki_export_list = []

# ==========================================
# SIDEBAR: EINSTELLUNGEN, MODI & VOKABEL-ANZEIGE
# ==========================================
st.sidebar.title("🇹🇷 Agent Einstellungen")

if st.sidebar.button("🔄 Nextcloud Vokabeln neu laden"):
    st.cache_data.clear()
    now_time = datetime.datetime.now().strftime("%H:%M:%S")
    st.sidebar.success(f"Vokabeln um {now_time} Uhr neu geladen!")
    st.rerun()

st.sidebar.caption(f"Status: {last_sync}")
st.sidebar.divider()

# 1. SZENARIO & MODUS AUSWAHL
st.sidebar.subheader("🎭 Szenario / Modus")
scenario = st.sidebar.selectbox(
    "Wähle deine Lernsituation:",
    [
        "💬 Freies Gespräch & Smalltalk",
        "🛒 Pazar / Market (Feilschen & Einkaufen)",
        "🍽️ Restoran (Bestellen & Bezahlen)",
        "🚕 Taksi & Adres (Wegbeschreibung)",
        "👨‍⚕️ Doktor / Eczane (Arzt & Apotheke)",
        "📜 Atasözleri & Deyimler (Redewendungen & Kultur)"
    ]
)

# 2. VOKABEL-FOKUS & SLIDER
st.sidebar.divider()
st.sidebar.subheader("🎯 Vokabel-Fokus")
vocab_mode = st.sidebar.radio(
    "Welche Vokabeln einbinden?",
    ["🔥 Kürzlich gelernt / wiederholt", "🎲 Zufallsmix aus ALLEN Karten"]
)

if "Kürzlich" in vocab_mode:
    active_pool = vocab_data.get("recent", [])
else:
    active_pool = vocab_data.get("all", [])

if "Zufallsmix" in vocab_mode and active_pool:
    active_pool = random.sample(active_pool, len(active_pool))

max_vocab = st.sidebar.slider("Anzahl Anki-Vokabeln im Prompt:", 5, max(len(active_pool), 10) if active_pool else 50, min(30, len(active_pool)) if active_pool else 10)
selected_vocab = active_pool[:max_vocab]

# 📊 HIER IST WIEDER DIE VOKABEL-ÜBERSICHT
with st.sidebar.expander("📊 Geladene Vokabeln (Tabelle)", expanded=True):
    stats = vocab_data.get("stats", {})
    st.write(f"Gesamt-Stapel in Anki: **{stats.get('total_in_deck', 0)}**")
    st.write(f"Kürzlich gelernt/wiederholt: **{stats.get('total_recent', 0)}**")
    st.write(f"Aktuell im Prompt aktiv: **{len(selected_vocab)}**")
    st.divider()
    if selected_vocab:
        st.caption("Aktiv im Prompt geladene Karten:")
        st.dataframe(selected_vocab, use_container_width=True)
    else:
        st.warning("Keine Vokabeln verfügbar.")

# 3. REVERSE-SYNC / ANKI EXPORT LISTE
st.sidebar.divider()
st.sidebar.subheader("📥 Neue Karten für Anki")

if st.session_state.anki_export_list:
    st.sidebar.write(f"Bereit zum Export: **{len(st.session_state.anki_export_list)} Karten**")
    with st.sidebar.expander("Vorschau Export-Karten", expanded=False):
        for item in st.session_state.anki_export_list:
            st.markdown(f"**{item['vorderseite']}**")
            st.caption(f"→ {item['rueckseite']}")
            st.divider()
    
    if st.sidebar.button("🚀 In tubCloud für Anki-Import speichern"):
        try:
            existing_res = requests.get(EXPORT_WEBDAV_URL, auth=(USERNAME, APP_PASSWORD))
            existing_data = existing_res.json() if existing_res.status_code == 200 else []
            
            combined_data = existing_data + st.session_state.anki_export_list
            
            upload_res = requests.put(
                EXPORT_WEBDAV_URL,
                data=json.dumps(combined_data, ensure_ascii=False, indent=2).encode('utf-8'),
                auth=(USERNAME, APP_PASSWORD),
                headers={"Content-Type": "application/json"}
            )
            if upload_res.status_code in [200, 201, 204]:
                st.sidebar.success("Erfolgreich in tubCloud gespeichert!")
                st.session_state.anki_export_list = []
                st.rerun()
            else:
                st.sidebar.error(f"Fehler: {upload_res.status_code}")
        except Exception as e:
            st.sidebar.error(f"Verbindungsfehler: {e}")
else:
    st.sidebar.info("Noch keine neuen Vokabeln gemerkt.")

# ==========================================
# CHAT INTERFACE & PROMPT-BUILDER
# ==========================================
st.title(f"🇹🇷 Sohbet: {scenario.split(' ')[1] if ' ' in scenario else scenario}")

if "chats" not in st.session_state:
    st.session_state.chats = {"Hauptchat": []}
if "active_chat" not in st.session_state:
    st.session_state.active_chat = "Hauptchat"

current_messages = st.session_state.chats[st.session_state.active_chat]

for idx, msg in enumerate(current_messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        if msg["role"] == "assistant" and "anki_suggestions" in msg:
            st.markdown("---")
            st.caption("💡 **Vorgeschlagene Anki-Karten aus dieser Antwort:")
            cols = st.columns(len(msg["anki_suggestions"]))
            for c_idx, card in enumerate(msg["anki_suggestions"]):
                with cols[c_idx]:
                    st.write(f"**")
                    st.caption(card['rueckseite'])
                    if st.button("➕ Merken", key=f"card_{idx}_{c_idx}"):
                        if card not in st.session_state.anki_export_list:
                            st.session_state.anki_export_list.append(card)
                            st.toast(f"Gemerkt: {card['vorderseite']}")
                            st.rerun()

if user_input := st.chat_input("Schreibe auf Türkisch..."):
    current_messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    vocab_formatted = "\n".join([f"- {v['tr']} ({v['de']})" for v in selected_vocab])

    system_instruction = f"""
    Du bist ein türkischer Muttersprachler und Sprachlehrer.
    AKTUELLES SZENARIO / ROLLE: {scenario}

    AUFGABE:
    1. Antworte passend zum Szenario auf Türkisch.
    2. Wenn sinnvoll, baue Vokabeln aus dieser Liste ein:
    {vocab_formatted}

    FORMATIERUNG DEINER ANTWORT:
    Gib deine Antwort IMMER im folgenden JSON-Format zurück:
    {{
        "reply_tr": "Deine Antwort auf Türkisch...",
        "translation_de": "Kurze deutsche Übersetzung deiner Antwort...",
        "suffix_analysis": [
            {{"word": "geliyorum", "breakdown": "gel-iyor-um", "meaning": "kommen + Präsens + ich"}},
            {{"word": "evlerinizden", "breakdown": "ev-ler-iniz-den", "meaning": "Haus + Plural + Euer + aus"}}
        ],
        "cultural_notes_or_idioms": "Erklärung von Redewendungen/Kulturfloskeln falls vorhanden (sonst null)",
        "anki_card_suggestions": [
            {{
                "vorderseite": "geliyorum (Grundform: gelmek)",
                "rueckseite": "ich komme\\n\\nBeispiel: Şimdi eve geliyorum. (Ich komme jetzt nach Hause.)"
            }}
        ]
    }}

    WICHTIG FÜR ANKI-KARTEN (anki_card_suggestions):
    - Schlage 1-3 neue/nützliche Wörter oder Redewendungen aus deiner Antwort als Anki-Karte vor.
    - Format Vorderseite: Nutze bei konjugierten Verben oder deklinierten Nomen IMMER das Format: 'VERWENDETE_FORM (Grundform: INFINITIV_ODER_NOMINATIV)'.
    - Bei Redewendungen: Nimm die vollständige Redewendung auf die Vorderseite.
    """

    with st.chat_message("assistant"):
        with st.spinner("Denkt nach und analysiert Suffixe..."):
            history_str = "\n".join([f"{m['role']}: {m['content']}" for m in current_messages])
            
            try:
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=f"{history_str}\nuser: {user_input}",
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.7
                    )
                )
                
                res_data = json.loads(response.text)
                
                output_md = f"{res_data.get('reply_tr', '')}\n\n*({res_data.get('translation_de', '')})*"
                
                if res_data.get("suffix_analysis"):
                    output_md += "\n\n---\n**🔬 Suffix-Analyse:**\n"
                    for item in res_data["suffix_analysis"]:
                        output_md += f"- **{item['word']}** (`{item['breakdown']}`): *{item['meaning']}*\n"
                
                if res_data.get("cultural_notes_or_idioms"):
                    output_md += f"\n\n💡 **Kultur & Redewendung:**\n{res_data['cultural_notes_or_idioms']}\n"

                st.markdown(output_md)
                
                msg_object = {
                    "role": "assistant",
                    "content": output_md,
                    "anki_suggestions": res_data.get("anki_card_suggestions", [])
                }
                current_messages.append(msg_object)
                st.rerun()

            except Exception as e:
                st.error(f"Fehler bei der Antwortgenerierung: {e}")
