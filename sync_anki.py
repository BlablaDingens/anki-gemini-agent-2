import requests
import json

ANKI_URL = "http://localhost:8765"
WEBDAV_URL = "https://tubcloud.tu-berlin.de/remote.php/dav/files/6c15e8e8-a12e-103c-98d9-7f3a285a3c9f/Anki"
USERNAME = "b.wolbring"
APP_PASSWORD = "im6zt-2nPKS-zdD8b-jp6j7-oRAG5"

TURKISH_DECK_NAME = "Türkisch" 

def sync():
    try:
        # Priorität 1: Kürzlich gelernt/wiederholt ("rated:365" im Türkisch-Deck)
        query_str = f'deck:"{TURKISH_DECK_NAME}" rated:365'
        res = requests.post(ANKI_URL, json={"action": "findNotes", "version": 6, "params": {"query": query_str}}).json()
        note_ids = res.get("result", [])

        # Fallback: Falls keine Reviews im letzten Jahr stattfanden, nimm alle Karten des Decks
        if not note_ids:
            query_str = f'deck:"{TURKISH_DECK_NAME}"'
            res = requests.post(ANKI_URL, json={"action": "findNotes", "version": 6, "params": {"query": query_str}}).json()
            note_ids = res.get("result", [])

        if not note_ids:
            return False, f"Keine Karten im Deck '{TURKISH_DECK_NAME}' gefunden."

        # Nimm die letzten (neuesten/kürzlich bearbeiteten) bis zu 200 Notizen
        recent_ids = note_ids[-200:]
        notes_info = requests.post(ANKI_URL, json={"action": "notesInfo", "version": 6, "params": {"notes": recent_ids}}).json().get("result", [])
        
        vocab_list = []
        for note in reversed(notes_info):  # Neueste Vokabeln zuerst
            fields = note.get("fields", {})
            front = fields.get("Vorderseite", {}).get("value", "").strip()
            back = fields.get("Rückseite", {}).get("value", "").strip()
                    
            if front and back:
                vocab_list.append({"tr": front, "de": back})

        target_url = f"{WEBDAV_URL.strip('/')}/anki_vocab.json"
        upload_res = requests.put(
            target_url,
            data=json.dumps(vocab_list, ensure_ascii=False).encode('utf-8'),
            auth=(USERNAME, APP_PASSWORD),
            headers={"Content-Type": "application/json"}
        )
        
        if upload_res.status_code in [200, 201, 204]:
            return True, f"{len(vocab_list)} Türkisch-Vokabeln (zuletzt wiederholt/erstellt) synchronisiert!"
        else:
            return False, f"Upload-Fehler: {upload_res.status_code}"
    except Exception as e:
        return False, f"Verbindungsfehler: {e}"

if __name__ == "__main__":
    success, msg = sync()
    print(msg)
