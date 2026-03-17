import json
import os
import time

CHAT_DIR = "chats"


def save_chat(history):
    if not os.path.exists(CHAT_DIR):
        os.makedirs(CHAT_DIR)

    filename = f"{CHAT_DIR}/chat_{int(time.time())}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)


def load_chats():
    if not os.path.exists(CHAT_DIR):
        return []

    return sorted(os.listdir(CHAT_DIR))