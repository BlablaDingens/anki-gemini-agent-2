import requests
import json

ANKI_URL = "http://localhost:8765"
EXPORT_WEBDAV_URL = "https://tubcloud.tu-berlin.de/remote.php/dav/files/6c15e8e8-a12e-103c-98d9-7f3a285a3c9f/Anki/anki_new_exports.json"
USERNAME = "b.wolbring"
APP_PASSWORD = "im6zt-2nPKS-zdD8b-jp6j7-oRAG5"
TURKISH_DECK_NAME = "Türkisch"

def import_cards():
    try:
        # 1. Gespeicherte neue Karten aus Nextcloud abrufen
        res = requests.get(EXPORT_WEBDAV_URL, auth=(USERNAME, APP_PASSWORD))
        if res.status_code != 200:
            print("Keine neuen Karten zum Importieren in Nextcloud gefunden.")
            return

        new_cards = res.json()
        if not new_cards:
            print("Importliste ist leer.")
            return

        imported_count = 0
        for card in new_cards:
            note_payload = {
                "action": "addNote",
                "version": 6,
                "params": {
                    "note": {
                        "deckName": TURKISH_DECK_NAME,
                        "modelName": "Einfach",  # Oder dein Kartentyp, z.B. 'Standard'
                        "fields": {
                            "Vorderseite": card["vorderseite"],
                            "Rückseite": card["rueckseite"]
                        },
                        "tags": ["gemini_agent", "reverse_sync"]
                    }
                }
            }
            res_anki = requests.post(ANKI_URL, json=note_payload).json()
            if not res_anki.get("error"):
                imported_count += 1

        print(f"✅ {imported_count} von {len(new_cards)} Karten erfolgreich nach Anki importiert!")

        # 2. Liste in Nextcloud nach erfolgreichem Import leeren
        requests.put(
            EXPORT_WEBDAV_URL,
            data=json.dumps([], ensure_ascii=False).encode('utf-8'),
            auth=(USERNAME, APP_PASSWORD),
            headers={"Content-Type": "application/json"}
        )

    except Exception as e:
        print(f"Fehler beim Import: {e}")

if __name__ == "__main__":
    import_cards()
