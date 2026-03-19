import logging
import time
import requests
from concurrent.futures import ThreadPoolExecutor

class OllamaClient:
    def __init__(self, url: str = "http://localhost:11434/api/generate", model: str = "qwen3:30b", max_retries: int = 3, temperature: float = 0.7, num_ctx: int = 8192):
        self.url = url
        self.model = model
        self.max_retries = max_retries
        self.temperature = temperature
        self.num_ctx = num_ctx
        self._cache: dict[str, str] = {}


    def call_generate(self, prompt: str) -> str:
        """Llamada robusta a Ollama local con sistema de caché simple."""
        if prompt in self._cache:
            logging.debug("Usando respuesta de caché para el prompt.")
            return self._cache[prompt]

        payload = {
            "model": self.model, 
            "prompt": prompt, 
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_ctx": self.num_ctx
            }
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.post(self.url, json=payload, timeout=300)
                if resp.status_code != 200:
                    raise requests.exceptions.HTTPError(f"HTTP Error {resp.status_code}: {resp.text}")
                response_text = resp.json().get("response", "")

                self._cache[prompt] = response_text
                return response_text
            except Exception as e:
                logging.warning(f"Intento {attempt}/{self.max_retries} fallido para Ollama: {e}")
                if attempt == self.max_retries:
                    raise
                time.sleep(2 * attempt)
        return ""

    def process_parallel(self, prompts: list, max_workers: int = 3):
        """Procesa múltiples prompts en paralelo."""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            return list(executor.map(self.call_generate, prompts))
