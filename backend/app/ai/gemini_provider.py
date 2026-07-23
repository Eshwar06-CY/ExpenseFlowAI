"""
Google Gemini Provider Implementation - ExpenseFlowAI

Uses the official google-genai SDK (from google import genai) to interact with
Gemini models (default: gemini-3.6-flash).
Fully satisfies the abstract LLMProvider interface with synchronous/asynchronous text generation,
first-token token streaming, client instance caching, diagnostic logging, and health checks.
"""

import logging
import asyncio
import time
import traceback
import threading
from typing import Optional, Dict, Any, List, AsyncGenerator

try:
    from google import genai
    from google.genai import types
    _SDK_VERSION = getattr(genai, "__version__", "unknown")
    _GEMINI_AVAILABLE = True
except Exception:
    genai = None
    types = None
    _SDK_VERSION = "uninstalled"
    _GEMINI_AVAILABLE = False

from app.core.config import settings
from app.ai.provider import LLMProvider

logger = logging.getLogger(__name__)

# Primary recommended fallback models if configured model is deprecated/sunsetted (404 NOT_FOUND)
SUPPORTED_FALLBACK_MODELS = ["gemini-3.6-flash", "gemini-flash-latest", "gemini-3.5-flash-lite"]

# Thread-safe client cache to reduce HTTP socket re-creation latency across requests
_CLIENT_CACHE: Dict[str, Any] = {}
_CLIENT_LOCK = threading.Lock()


class GeminiProvider(LLMProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        max_output_tokens: Optional[int] = None,
        **kwargs
    ):
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", None)
        self.model = model or getattr(settings, "GEMINI_MODEL", "gemini-3.6-flash")
        self.timeout = timeout if timeout is not None else getattr(settings, "GEMINI_TIMEOUT", 60.0)
        self.temperature = temperature if temperature is not None else getattr(settings, "GEMINI_TEMPERATURE", 0.3)
        self.top_p = top_p if top_p is not None else getattr(settings, "GEMINI_TOP_P", 0.9)
        self.top_k = top_k if top_k is not None else getattr(settings, "GEMINI_TOP_K", 40)
        self.max_output_tokens = max_output_tokens if max_output_tokens is not None else getattr(settings, "GEMINI_MAX_OUTPUT_TOKENS", 1024)
        self.provider_name = "gemini"

    def _get_client(self):
        if not _GEMINI_AVAILABLE:
            raise RuntimeError("The 'google-genai' package is not installed. Install with `pip install google-genai`.")

        key = self.api_key or getattr(settings, "GEMINI_API_KEY", None)
        if not key:
            raise RuntimeError("GEMINI_API_KEY environment variable is not configured.")

        # Thread-safe singleton reuse per API key
        with _CLIENT_LOCK:
            if key not in _CLIENT_CACHE:
                try:
                    logger.debug("[GeminiProvider] Creating new cached genai.Client instance...")
                    _CLIENT_CACHE[key] = genai.Client(api_key=key)
                except Exception as e:
                    logger.error("[GeminiProvider] Client initialization failed: %s", str(e))
                    raise RuntimeError(f"Failed to initialize Gemini Client: {str(e)}") from e
            return _CLIENT_CACHE[key]

    def _build_config(self, system_prompt: Optional[str] = None) -> Any:
        config_kwargs: Dict[str, Any] = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "max_output_tokens": self.max_output_tokens,
        }
        if system_prompt:
            config_kwargs["system_instruction"] = system_prompt

        return types.GenerateContentConfig(**config_kwargs)

    def _log_request_details(self, request_type: str, target_model: str, endpoint: str):
        """Outputs structured debug log before every request to Gemini API without exposing secrets."""
        logger.info("[Gemini Request Audit] ==========================================")
        logger.info("[Gemini Request Audit] Configured Model : %s", target_model)
        logger.info("[Gemini Request Audit] API Key Present  : %s", bool(self.api_key))
        logger.info("[Gemini Request Audit] SDK Version      : %s", _SDK_VERSION)
        logger.info("[Gemini Request Audit] Request Type     : %s", request_type)
        logger.info("[Gemini Request Audit] Target Endpoint  : %s", endpoint)
        logger.info("[Gemini Request Audit] ==========================================")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        summary: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Generates a complete text response via Google Gemini API.
        Includes diagnostic logging, auto-recovery for deprecated models, and error retries.
        """
        client = self._get_client()
        config = self._build_config(system_prompt=system_prompt)
        start_time = time.perf_counter()
        current_model = self.model
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent"

        self._log_request_details(
            request_type="generate_content (non-streaming)",
            target_model=current_model,
            endpoint=endpoint
        )

        max_retries = 2
        retry_delay = 0.5

        for attempt in range(max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=current_model,
                    contents=prompt,
                    config=config,
                )
                text = (response.text or "").strip()
                if not text:
                    logger.warning("[GeminiProvider] Returned empty response text.")
                    return "I am unable to generate advice at this moment. Please try again shortly."

                elapsed = time.perf_counter() - start_time
                logger.info("[Gemini Sync Chat SUCCESS] Model: %s | Status: 200 OK | Latency: %.2fs", current_model, elapsed)
                return text

            except Exception as exc:
                exc_str = str(exc)
                logger.error("[Gemini Request Error] Attempt %d/%d for model '%s': %s", attempt + 1, max_retries + 1, current_model, exc_str)
                logger.debug("[Gemini Exception Traceback]:\n%s", traceback.format_exc())

                # Auto-detect deprecated or 404 NOT_FOUND model errors
                if ("404" in exc_str or "NOT_FOUND" in exc_str or "no longer available" in exc_str) and current_model not in SUPPORTED_FALLBACK_MODELS:
                    fallback_model = SUPPORTED_FALLBACK_MODELS[0]
                    logger.warning(
                        "[Gemini Auto-Recovery] Model '%s' is unavailable or deprecated. Automatically failing over to supported model '%s'.",
                        current_model,
                        fallback_model
                    )
                    current_model = fallback_model
                    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent"
                    self._log_request_details(
                        request_type="generate_content (fallback retry)",
                        target_model=current_model,
                        endpoint=endpoint
                    )
                    continue

                if attempt < max_retries:
                    logger.warning("[Gemini Retry %d/%d] Retrying in %.2fs...", attempt + 1, max_retries, retry_delay)
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error("[GeminiProvider] Generation failed after %d retries.", max_retries)
                    raise RuntimeError(f"Gemini API error: {exc_str}") from exc

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        messages: Optional[List[Dict[str, str]]] = None,
        summary: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Streams response tokens asynchronously as generated by Google Gemini API.
        Includes TTFT measurement, diagnostic logging, and error handling.
        """
        client = self._get_client()
        config = self._build_config(system_prompt=system_prompt)
        start_time = time.perf_counter()
        first_token_time = None
        current_model = self.model
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:streamGenerateContent?alt=sse"

        self._log_request_details(
            request_type="generate_content_stream (streaming)",
            target_model=current_model,
            endpoint=endpoint
        )

        try:
            response_stream = client.models.generate_content_stream(
                model=current_model,
                contents=prompt,
                config=config,
            )

            for chunk in response_stream:
                if chunk:
                    chunk_text = None
                    try:
                        chunk_text = chunk.text
                    except Exception:
                        if hasattr(chunk, "candidates") and chunk.candidates:
                            try:
                                for cand in chunk.candidates:
                                    if cand.content and cand.content.parts:
                                        for part in cand.content.parts:
                                            if hasattr(part, "text") and part.text:
                                                chunk_text = (chunk_text or "") + part.text
                            except Exception:
                                pass

                    if chunk_text:
                        if first_token_time is None:
                            first_token_time = time.perf_counter() - start_time
                        yield chunk_text
                        await asyncio.sleep(0)

            total_sec = time.perf_counter() - start_time
            ttft_str = f" | TTFT: {first_token_time*1000:.1f}ms" if first_token_time else ""
            logger.info("[Gemini Stream Chat SUCCESS] Model: %s%s | Total Latency: %.2fs", current_model, ttft_str, total_sec)

        except Exception as exc:
            exc_str = str(exc)
            logger.error("[Gemini Streaming Error] Model '%s': %s", current_model, exc_str)
            logger.debug("[Gemini Stream Traceback]:\n%s", traceback.format_exc())

            # Auto-detect deprecated or 404 NOT_FOUND model error on streaming
            if ("404" in exc_str or "NOT_FOUND" in exc_str or "no longer available" in exc_str) and current_model not in SUPPORTED_FALLBACK_MODELS:
                fallback_model = SUPPORTED_FALLBACK_MODELS[0]
                logger.warning(
                    "[Gemini Stream Auto-Recovery] Model '%s' is unavailable or deprecated. Failing over to '%s'.",
                    current_model,
                    fallback_model
                )
                try:
                    fb_stream = client.models.generate_content_stream(
                        model=fallback_model,
                        contents=prompt,
                        config=config,
                    )
                    for chunk in fb_stream:
                        if chunk and chunk.text:
                            yield chunk.text
                            await asyncio.sleep(0)
                    return
                except Exception as fb_exc:
                    logger.error("[Gemini Fallback Stream Error]: %s", str(fb_exc))
                    yield f"\n[Gemini API Error: {str(fb_exc)}]"
                    return

            yield f"\n[Gemini API Error: {exc_str}]"

    def health_check(self) -> Dict[str, Any]:
        """
        Checks Gemini API connectivity and API key validity.
        """
        if not _GEMINI_AVAILABLE:
            return {
                "provider": self.provider_name,
                "model": self.model,
                "status": "unhealthy",
                "details": {"error": "google-genai SDK not installed"}
            }

        key = self.api_key or getattr(settings, "GEMINI_API_KEY", None)
        if not key:
            return {
                "provider": self.provider_name,
                "model": self.model,
                "status": "unhealthy",
                "details": {"error": "GEMINI_API_KEY not configured"}
            }

        try:
            client = self._get_client()
            model_info = client.models.get(model=self.model)
            return {
                "provider": self.provider_name,
                "model": self.model,
                "status": "healthy",
                "details": {
                    "model_name": getattr(model_info, "name", self.model),
                    "display_name": getattr(model_info, "display_name", self.model)
                }
            }
        except Exception as exc:
            return {
                "provider": self.provider_name,
                "model": self.model,
                "status": "degraded",
                "details": {"error": str(exc), "model": self.model}
            }
