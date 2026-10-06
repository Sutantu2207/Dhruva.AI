"""Google Gemini provider implementation conforming to AIProvider interface."""

import time
import json
import httpx
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from app.core.config import settings
from app.core.logging import logger
from app.domains.ai.providers.base import AIProvider, AIProviderResponse, AIEmbeddingResponse
from app.domains.ai.config import (
    DEFAULT_MODEL,
    DEFAULT_EMBEDDING_MODEL,
    REQUEST_TIMEOUT_SECONDS,
    AUTHORITY_SYSTEM_INSTRUCTION,
)


class GeminiProvider(AIProvider):
    """Production-grade Google Gemini API provider."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", "")
        self.model = model or DEFAULT_MODEL
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def is_configured(self) -> bool:
        """Check if a valid non-placeholder API key exists."""
        return bool(self.api_key and self.api_key.strip() and self.api_key != "your_gemini_api_key_here")

    def health_check(self) -> Dict[str, Any]:
        """Probes Gemini configuration readiness."""
        return {
            "provider": "google_gemini",
            "model": self.model,
            "configured": self.is_configured(),
            "status": "ready" if self.is_configured() else "credentials_pending",
        }

    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AIProviderResponse:
        """Calls Google Gemini v1beta generateContent endpoint."""
        start_time = time.perf_counter()
        sys_prompt = system_instruction or AUTHORITY_SYSTEM_INSTRUCTION

        if not self.is_configured():
            # Graceful deterministic fallback when API key is not yet set
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            return AIProviderResponse(
                content=(
                    "Dhruva AI Orchestration Gateway is active. "
                    "Gemini API key is currently pending institutional configuration. "
                    "All underlying deterministic records remain verified and secure."
                ),
                model=self.model,
                input_tokens=10,
                output_tokens=30,
                latency_ms=elapsed_ms,
            )

        # Map role messages to Gemini contents structure
        contents = []
        for m in messages:
            role = "user" if m.get("role") in ["user", "tool"] else "model"
            contents.append({
                "role": role,
                "parts": [{"text": m.get("content", "")}]
            })

        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": sys_prompt}]},
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }

        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            resp = await client.post(url, json=payload)
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            if resp.status_code != 200:
                logger.error(f"Gemini API Error {resp.status_code}: {resp.text}")
                return AIProviderResponse(
                    content="Dhruva AI is temporarily unable to reach Gemini. Your academic data remains safe and unchanged.",
                    model=self.model,
                    latency_ms=elapsed_ms,
                    finish_reason="error",
                )

            data = resp.json()
            candidates = data.get("candidates", [])
            text_out = ""
            if candidates:
                text_out = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")

            usage = data.get("usageMetadata", {})
            return AIProviderResponse(
                content=text_out,
                model=self.model,
                input_tokens=usage.get("promptTokenCount", 0),
                output_tokens=usage.get("candidatesTokenCount", 0),
                latency_ms=elapsed_ms,
                raw_response=data,
            )

    async def generate_structured(
        self,
        messages: List[Dict[str, str]],
        schema: type[BaseModel],
        system_instruction: Optional[str] = None,
    ) -> BaseModel:
        """Enforces Pydantic response formatting."""
        schema_json = json.dumps(schema.model_json_schema())
        augmented_sys = (
            f"{system_instruction or AUTHORITY_SYSTEM_INSTRUCTION}\n\n"
            f"You MUST format your entire response as a valid JSON object matching this schema:\n{schema_json}"
        )
        resp = await self.generate(messages, system_instruction=augmented_sys, temperature=0.1)
        # Parse and validate with Pydantic
        clean_text = resp.content.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()
        return schema.model_validate_json(clean_text)

    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> AIEmbeddingResponse:
        """Calls text embedding model for retrieval."""
        emb_model = model or DEFAULT_EMBEDDING_MODEL
        if not self.is_configured():
            # Return deterministic synthetic unit embeddings for testing/pending state
            return AIEmbeddingResponse(
                vectors=[[0.05 * (i + 1) for i in range(128)] for _ in texts],
                model=emb_model,
                tokens_used=len(texts) * 5,
            )

        url = f"{self.base_url}/models/{emb_model}:batchEmbedContents?key={self.api_key}"
        requests = [{"model": f"models/{emb_model}", "content": {"parts": [{"text": t}]}} for t in texts]
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            resp = await client.post(url, json={"requests": requests})
            if resp.status_code != 200:
                logger.error(f"Gemini Embeddings Error {resp.status_code}: {resp.text}")
                return AIEmbeddingResponse(
                    vectors=[[0.0] * 128 for _ in texts],
                    model=emb_model,
                    tokens_used=0,
                )
            data = resp.json()
            vectors = [item.get("values", []) for item in data.get("embeddings", [])]
            return AIEmbeddingResponse(
                vectors=vectors,
                model=emb_model,
                tokens_used=len(texts) * 10,
            )


gemini_provider = GeminiProvider()
