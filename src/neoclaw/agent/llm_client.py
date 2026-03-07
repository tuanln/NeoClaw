"""LLM client with Gemini (Google) API and Ollama support."""
from __future__ import annotations

import logging
import os
from typing import Generator

from neoclaw.config.settings import get_settings

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified LLM client supporting Gemini API (primary) and Ollama (fallback)."""

    def __init__(self):
        self._settings = get_settings().ai
        self._client = None
        self._available: bool | None = None
        self._provider = self._settings.provider

    def _get_api_key(self) -> str:
        return (
            self._settings.api_key
            or os.environ.get("GEMINI_API_KEY", "")
            or os.environ.get("GOOGLE_API_KEY", "")
        )

    def _get_client(self):
        if self._client is not None:
            return self._client

        if self._provider == "gemini":
            try:
                from openai import OpenAI
                api_key = self._get_api_key()
                if not api_key:
                    logger.warning("No Gemini API key found (set GEMINI_API_KEY)")
                    return None
                self._client = OpenAI(api_key=api_key, base_url=self._settings.api_base_url)
            except ImportError:
                logger.warning("openai package not installed")
                return None
        elif self._provider == "ollama":
            try:
                import ollama
                self._client = ollama.Client(host=self._settings.ollama_host)
            except ImportError:
                logger.warning("ollama package not installed")
                return None
        else:
            return None

        return self._client

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available

        if self._provider == "offline":
            self._available = False
            return False

        client = self._get_client()
        if client is None:
            self._available = False
            return False

        if self._provider == "gemini":
            try:
                client.models.list()
                self._available = True
            except Exception as e:
                logger.warning(f"Gemini API not available: {e}")
                self._available = False
        elif self._provider == "ollama":
            try:
                client.list()
                self._available = True
            except Exception as e:
                logger.warning(f"Ollama not available: {e}")
                self._available = False

        return self._available  # type: ignore[return-value]

    def generate(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int = 512,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        client = self._get_client()
        if client is None:
            return ""

        messages = self._build_messages(system_prompt, history, prompt)

        if self._provider == "gemini":
            return self._generate_gemini(client, messages, max_tokens)
        elif self._provider == "ollama":
            return self._generate_ollama(client, messages, max_tokens)
        return ""

    def generate_stream(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int = 512,
        history: list[dict[str, str]] | None = None,
    ) -> Generator[str, None, None]:
        client = self._get_client()
        if client is None:
            return

        messages = self._build_messages(system_prompt, history, prompt)

        if self._provider == "gemini":
            yield from self._stream_gemini(client, messages, max_tokens)
        elif self._provider == "ollama":
            yield from self._stream_ollama(client, messages, max_tokens)

    def _build_messages(
        self, system_prompt: str, history: list[dict[str, str]] | None, prompt: str
    ) -> list[dict[str, str]]:
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})
        return messages

    # ── Gemini (OpenAI-compatible) ──

    def _generate_gemini(self, client, messages: list, max_tokens: int) -> str:
        try:
            response = client.chat.completions.create(
                model=self._settings.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=self._settings.temperature,
                top_p=0.9,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            return self._try_fallback_gemini(client, messages, max_tokens)

    def _stream_gemini(self, client, messages: list, max_tokens: int) -> Generator[str, None, None]:
        try:
            stream = client.chat.completions.create(
                model=self._settings.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=self._settings.temperature,
                top_p=0.9,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")

    def _try_fallback_gemini(self, client, messages: list, max_tokens: int) -> str:
        try:
            response = client.chat.completions.create(
                model=self._settings.fallback_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=self._settings.temperature,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Gemini fallback error: {e}")
            return ""

    # ── Ollama ──

    def _generate_ollama(self, client, messages: list, max_tokens: int) -> str:
        try:
            response = client.chat(
                model=self._settings.model,
                messages=messages,
                options={"num_predict": max_tokens, "temperature": self._settings.temperature},
            )
            return response["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            return self._try_fallback_ollama(client, messages, max_tokens)

    def _stream_ollama(self, client, messages: list, max_tokens: int) -> Generator[str, None, None]:
        try:
            stream = client.chat(
                model=self._settings.model,
                messages=messages,
                options={"num_predict": max_tokens, "temperature": self._settings.temperature},
                stream=True,
            )
            for chunk in stream:
                yield chunk["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama streaming error: {e}")

    def _try_fallback_ollama(self, client, messages: list, max_tokens: int) -> str:
        try:
            response = client.chat(
                model=self._settings.fallback_model,
                messages=messages,
                options={"num_predict": max_tokens, "temperature": self._settings.temperature},
            )
            return response["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama fallback error: {e}")
            return ""

    def get_model_info(self) -> dict:
        return {
            "provider": self._provider,
            "model": self._settings.model,
            "fallback": self._settings.fallback_model,
            "available": self.is_available(),
        }

    def reset_availability(self) -> None:
        self._available = None
        self._client = None
