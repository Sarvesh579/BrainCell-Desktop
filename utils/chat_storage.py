import json
import os

CHAT_DIR = "chats"

def save_chat(history, filename):
    if not os.path.exists(CHAT_DIR):
        os.makedirs(CHAT_DIR)
    path = f"{CHAT_DIR}/{filename}"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def load_chats():
    if not os.path.exists(CHAT_DIR):
        return []
    return sorted(os.listdir(CHAT_DIR))