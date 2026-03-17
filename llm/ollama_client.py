import ollama

class OllamaClient:
    def __init__(self, model="llama3:8b"):
        self.model = model

    def stream(self, messages):
        stream = ollama.chat(
            model = self.model,
            messages = messages,
            stream = True
        )

        for chunk in stream:
            yield chunk["message"]["content"]