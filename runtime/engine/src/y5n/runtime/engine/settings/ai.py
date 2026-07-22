import os
from dataclasses import dataclass


@dataclass
class OllamaSettings:
    url: str = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
    model: str = os.getenv("OLLAMA_MODEL", "llama3")
    timeout: float = float(os.getenv("OLLAMA_TIMEOUT", "60.0"))


class OpenAISettings:
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    model: str = os.getenv("OPENAI_MODEL", "gpt-4")
    temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    timeout: float = float(os.getenv("OPENAI_TIMEOUT", "60.0"))


class AISettings:
    backend: str = os.getenv("YAKOON_AI_BACKEND", "ollama")
    ollama = OllamaSettings()
    openai = OpenAISettings()
