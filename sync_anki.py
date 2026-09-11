import requests
import json
import random

ANKI_URL = "http://localhost:8765"
WEBDAV_URL = "https://tubcloud.tu-berlin.de/remote.php/dav/files/6c15e8e8-a12e-103c-98d9-7f3a285a3c9f/Anki"
USERNAME = "b.wolbring"
APP_PASSWORD = "im6zt-2nPKS-zdD8b-jp6j7-oRAG5"

TURKISH_DECK_NAME = "Türkisch"

def extract_vocab(notes_info):
    vocab_list = []
    for note in notes_info:
        fields = note.get("fields", {})
        front = fields.get("Vorderseite", {}).get("value", "").strip()
        back = fields.get("Rückseite", {}).get("value", "").strip()
        if front and back:
            vocab_list.append({"tr": front, "de": back})
    return vocab_list

def sync():
    try:
        # 1. ALLE Karten des Decks abfragen
        all_query = f'deck:"{TURKISH_DECK_NAME}"'
        res_all = requests.post(ANKI_URL, json={"action": "findNotes", "version": 6, "params": {"query": all_query}}).json()
        all_ids = res_all.get("result", [])
        
        if not all_ids:
            return False, f"Keine Karten im Deck '{TURKISH_DECK_NAME}' gefunden."

        # 2. Kürzlich gelernt/wiederholt abfragen (rated:365)
        recent_query = f'deck:"{TURKISH_DECK_NAME}" rated:365'
        res_recent = requests.post(ANKI_URL, json={"action": "findNotes", "version": 6, "params": {"query": recent_query}}).json()
        recent_ids = res_recent.get("result", [])
        
        # Falls keine Reviews im letzten Jahr, als Fallback die neusten 100
        if not recent_ids:
            recent_ids = all_ids[-100:]

        # Daten für Kürzlich Gelernt holen (neueste zuerst)
        info_recent = requests.post(ANKI_URL, json={"action": "notesInfo", "version": 6, "params": {"notes": recent_ids[-100:]}}).json().get("result", [])
        recent_vocab = extract_vocab(reversed(info_recent))

        # Daten für Alle Karten holen (Zufallsauswahl aus allen Karten)
        sample_all_ids = random.sample(all_ids, min(len(all_ids), 300))
        info_all = requests.post(ANKI_URL, json={"action": "notesInfo", "version": 6, "params": {"notes": sample_all_ids}}).json().get("result", [])
        all_vocab = extract_vocab(info_all)

        # Zusammen als strukturierte JSON-Struktur speichern
        payload = {
            "recent": recent_vocab,
            "all": all_vocab,
            "stats": {
                "total_in_deck": len(all_ids),
                "total_recent": len(recent_vocab)
            }
        }

        target_url = f"{WEBDAV_URL.strip('/')}/anki_vocab.json"
        upload_res = requests.put(
            target_url,
            data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            auth=(USERNAME, APP_PASSWORD),
            headers={"Content-Type": "application/json"}
        )
        
        if upload_res.status_code in [200, 201, 204]:
            return True, f"Erfolg: {len(all_ids)} Gesamtkarten & {len(recent_vocab)} kürzlich gelernte Vokabeln synchronisiert!"
        else:
            return False, f"Upload-Fehler: {upload_res.status_code}"
    except Exception as e:
        return False, f"Verbindungsfehler: {e}"

if __name__ == "__main__":
    success, msg = sync()
    print(msg)
