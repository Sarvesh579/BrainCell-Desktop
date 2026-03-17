from llm.ollama_client import OllamaClient

class BrainCellController:
    def __init__(self):
        self.running = False
        self.llm = OllamaClient()

    def run(self, history, token_callback, done_callback):
        self.running = True
        for token in self.llm.stream(history):
            if not self.running:
                break
            token_callback(token)
        self.running = False
        done_callback()

    def stop(self):
        self.running = False