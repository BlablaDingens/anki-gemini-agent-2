#!/bin/bash
cd /home/benno/anki-gemini-agent

# 1. Erst neue Karten aus der Cloud nach Anki importieren
IMPORT_OUT=$(./venv/bin/python import_to_anki.py 2>&1)

# 2. Dann Anki-Stand in die Cloud hochladen
SYNC_OUT=$(./venv/bin/python sync_anki.py 2>&1)

# Benachrichtigung anzeigen
notify-send "Anki Sync & Import 🇹🇷" "$IMPORT_OUT\n$SYNC_OUT" --icon=dialog-information
