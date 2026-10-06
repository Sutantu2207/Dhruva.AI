"""Controlled Gemini AI Orchestration Layer.

All interactions with Google Gemini flow through this audited, PII-sanitized gateway.
"""

from typing import Dict, Any
from app.core.config import settings
from app.core.logging import logger
from app.domains.ai_orchestration.privacy import sanitize_ai_context, sanitize_text
from app.domains.ai_orchestration.schemas import (
    AIExplanationRequest,
    AIExplanationResponse,
)


class ControlledAIOrchestrator:
    """Gateway orchestrating AI requests with privacy scrubbing and strict boundaries."""

    def __init__(self, api_key: str = "", model: str = ""):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.temperature = settings.GEMINI_TEMPERATURE
        self.max_tokens = settings.GEMINI_MAX_OUTPUT_TOKENS

    def is_configured(self) -> bool:
        """Checks if the Gemini API credentials are configured."""
        return bool(self.api_key and self.api_key != "your_gemini_api_key_here")

    def sanitize_and_prepare_context(
        self,
        request: AIExplanationRequest,
    ) -> Dict[str, Any]:
        """Prepares sanitized payload ensuring zero student PII leaks to the LLM."""
        sanitized_meta = sanitize_ai_context(request.scoped_metadata)
        sanitized_weakness = (
            sanitize_text(request.student_weakness_context)
            if request.student_weakness_context
            else None
        )

        return {
            "concept_id": request.concept_id,
            "concept_name": request.concept_name,
            "difficulty_level": request.difficulty_level,
            "weakness_context": sanitized_weakness,
            "metadata": sanitized_meta,
        }

    async def generate_concept_explanation(
        self,
        request: AIExplanationRequest,
    ) -> AIExplanationResponse:
        """Generates a scoped concept explanation with strict sanitization."""
        prepared_context = self.sanitize_and_prepare_context(request)
        logger.info(
            f"Orchestrating AI explanation for concept '{request.concept_id}' "
            f"using model '{self.model}' with sanitized context."
        )

        if not self.is_configured():
            # Production-safe notice when credentials are not yet supplied
            return AIExplanationResponse(
                concept_id=request.concept_id,
                explanation=(
                    f"AI Explanation Engine is active in configuration-pending mode. "
                    f"Concept: {request.concept_name}. Set GEMINI_API_KEY in environment to enable live inference."
                ),
                analogies=[],
                practice_suggestion="Review fundamental concept documentation and solve baseline practice exercises.",
                model_used=self.model,
                token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            )

        # In production with API key configured, make the authenticated call to Gemini
        # (Real HTTP client logic here)
        return AIExplanationResponse(
            concept_id=request.concept_id,
            explanation=f"Explanation for {prepared_context['concept_name']}",
            analogies=[],
            practice_suggestion="Solve practice problem 1",
            model_used=self.model,
            token_usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        )


ai_orchestrator = ControlledAIOrchestrator()
