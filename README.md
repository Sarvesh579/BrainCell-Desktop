## BrainCell Desktop — Local AI Desktop Assistant

### Description

Privacy-preserving desktop AI assistant running **Llama-3 8B locally on GPU**.
Can read local files, process data, and automate tasks using natural language.

### Features

* Local LLM inference (Ollama)
* Natural language → system actions
* File search & document analysis
* Excel/data processing
* Secure sandboxed code execution
* Desktop automation

### Requirements

* Python 3.10+
* Ollama
* NVIDIA GPU (RTX 4060 8GB recommended)

### Setup

```
pip install -r requirements.txt
ollama pull llama3
python app/main.py
```

### Project Structure

Short tree of folders.

### Security Model

* Read access: system files
* Write/execute: **sandbox only**

### License

MIT / project license.
