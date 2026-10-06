"""Provider interface abstraction and response protocols for Domain 11 AI."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class AIProviderResponse(BaseModel):
    """Normalized response contract returned by any AI model provider."""
    content: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    finish_reason: str = "stop"
    raw_response: Optional[Dict[str, Any]] = None


class AIEmbeddingResponse(BaseModel):
    """Normalized embedding vectors."""
    vectors: List[List[float]]
    model: str
    tokens_used: int = 0


class AIProvider(ABC):
    """Abstract provider interface ensuring future model replacibility."""

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> AIProviderResponse:
        """Generate conversational completion."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        messages: List[Dict[str, str]],
        schema: type[BaseModel],
        system_instruction: Optional[str] = None,
    ) -> BaseModel:
        """Generate structured completion validated against a Pydantic schema."""
        pass

    @abstractmethod
    async def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
    ) -> AIEmbeddingResponse:
        """Generate vector embeddings for retrieval."""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Probes API key validity and provider reachability."""
        pass
