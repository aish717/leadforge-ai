import httpx


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:3b"


def generate(prompt: str) -> str:
    """Generate structured text using the local Ollama model."""

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.0,
            "num_predict": 800,
        },
    }

    response = httpx.post(
        OLLAMA_URL,
        json=payload,
        timeout=300.0,
    )

    response.raise_for_status()

    data = response.json()

    return data["response"]