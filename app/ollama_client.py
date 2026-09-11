import httpx


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:3b"


def generate(prompt: str) -> str:
    """Generate text using the local Ollama model."""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 700,
        },
    }

    response = httpx.post(
        OLLAMA_URL,
        json=payload,
        timeout=180.0,
    )

    response.raise_for_status()

    data = response.json()

    return data["response"]