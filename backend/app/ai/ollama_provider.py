"""
Ollama Local LLM Provider Implementation - ExpenseFlowAI

Interacts directly with the local Ollama HTTP API (http://localhost:11434).
Supports standard synchronous/asynchronous generation, streaming token output,
and automated health checks.
"""

import json
import logging
from typing import Optional, Dict, Any, AsyncGenerator
import httpx

from app.core.config import settings
from app.ai.provider import LLMProvider

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT
        self.provider_name = "ollama"

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generates a complete single text response via Ollama HTTP API (/api/generate).
        Handles connection failures, timeouts, invalid/empty responses safely.
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        if system_prompt:
            payload["system"] = system_prompt

        url = f"{self.base_url}/api/generate"

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                text_response = data.get("response", "").strip()
                if not text_response:
                    logger.warning("Ollama returned empty response string.")
                    return "I am unable to generate advice at this moment. Please try again shortly."
                
                return text_response

        except httpx.TimeoutException as exc:
            logger.error("Ollama connection timed out (%ss): %s", self.timeout, str(exc))
            raise RuntimeError(f"Ollama connection timed out after {self.timeout} seconds.") from exc

        except httpx.ConnectError as exc:
            logger.error("Could not connect to Ollama at %s: %s", self.base_url, str(exc))
            raise RuntimeError(f"Could not connect to local Ollama server at {self.base_url}. Ensure Ollama service is running.") from exc

        except httpx.HTTPStatusError as exc:
            logger.error("Ollama HTTP Error %s: %s", exc.response.status_code, exc.response.text)
            raise RuntimeError(f"Ollama API error ({exc.response.status_code}): {exc.response.text}") from exc

        except Exception as exc:
            logger.error("Unexpected error during Ollama generation: %s", str(exc))
            raise RuntimeError(f"Ollama generation error: {str(exc)}") from exc

    async def generate_stream(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Streams response tokens asynchronously as JSON lines from Ollama HTTP API.
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": True
        }
        if system_prompt:
            payload["system"] = system_prompt

        url = f"{self.base_url}/api/generate"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                token = chunk.get("response", "")
                                if token:
                                    yield token
                            except json.JSONDecodeError:
                                continue
        except Exception as exc:
            logger.error("Error during streaming generation from Ollama: %s", str(exc))
            yield f"\n[Streaming error: {str(exc)}]"

    def health_check(self) -> Dict[str, Any]:
        """
        Checks local Ollama service status and model availability.
        """
        url = f"{self.base_url}/api/tags"
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    models = [m.get("name", "") for m in data.get("models", [])]
                    
                    # Check if requested model or matching prefix exists
                    model_found = any(self.model in m or m.startswith(self.model.split(":")[0]) for m in models)
                    
                    return {
                        "provider": "ollama",
                        "model": self.model,
                        "status": "healthy" if (model_found or len(models) > 0) else "degraded",
                        "details": {
                            "base_url": self.base_url,
                            "available_models": models,
                            "model_matched": model_found
                        }
                    }
                else:
                    return {
                        "provider": "ollama",
                        "model": self.model,
                        "status": "unhealthy",
                        "details": {"http_status": response.status_code, "error": response.text}
                    }
        except Exception as exc:
            return {
                "provider": "ollama",
                "model": self.model,
                "status": "unhealthy",
                "details": {"error": str(exc), "base_url": self.base_url}
            }
