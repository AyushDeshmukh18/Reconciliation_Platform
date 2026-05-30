from datetime import datetime, timezone
from pathlib import Path

import httpx
from jinja2 import Environment, FileSystemLoader, select_autoescape

from backend.config import get_settings

STATIC_EXPLANATIONS = {
    "timing_gap": "This transaction occurred near month-end and has not yet appeared in bank settlement files. Funds are expected in the next settlement cycle.",
    "rounding_difference": "A minor rounding variance exists between platform and bank amounts, within configured tolerance bands.",
    "duplicate_entry": "Duplicate records were detected with the same or similar transaction attributes within a short time window.",
    "orphan_refund": "A refund or reversal exists on the platform without a matching parent transaction or bank debit.",
    "partial_settlement": "The bank settled less than the full platform amount; the remainder may still be outstanding.",
    "failed_reversal": "The platform shows a reversal but the bank still settled funds — potential financial loss requiring urgent action.",
    "split_settlement": "Multiple bank settlement records sum to the platform amount across different batches or dates.",
    "stale_retry": "The bank submitted a second settlement for the same reference days after the first.",
    "settlement_truncation": "Batch-level floor rounding caused a systematic small shortfall across many transactions.",
    "status_mismatch": "Amounts match but platform and bank statuses disagree — investigate immediately.",
    "idempotency_failure": "Duplicate bank settlements exist for the same idempotency key — recall the extra settlement.",
    "unclassified": "This exception could not be automatically classified and requires manual review.",
}

STATIC_RESOLUTIONS = {
    "timing_gap": "Monitor for settlement in the next batch. If not received within 5 business days, contact the acquiring bank.",
    "failed_reversal": "Initiate bank recall immediately. Document compliance timeline and notify finance leadership.",
    "status_mismatch": "Pull gateway logs and bank confirmation. Align statuses before closing.",
    "unclassified": "Perform manual investigation using transaction ID and bank reference. Document findings before resolution.",
}


class OllamaUnavailableError(Exception):
    pass


class CircuitBreaker:
    def __init__(self, threshold: int, reset_seconds: int):
        self.failure_count = 0
        self.threshold = threshold
        self.reset_seconds = reset_seconds
        self.tripped_at: datetime | None = None

    def is_open(self) -> bool:
        if self.tripped_at and (datetime.now(timezone.utc) - self.tripped_at).total_seconds() < self.reset_seconds:
            return True
        if self.tripped_at:
            self.reset()
        return False

    def record_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.threshold:
            self.tripped_at = datetime.now(timezone.utc)

    def reset(self):
        self.failure_count = 0
        self.tripped_at = None


class OllamaService:
    def __init__(self, settings=None):
        self.settings = settings or get_settings()
        self.base_url = self.settings.OLLAMA_BASE_URL
        self.model = self.settings.OLLAMA_MODEL
        self.timeout = self.settings.OLLAMA_TIMEOUT_SECONDS
        self.circuit_breaker = CircuitBreaker(
            self.settings.OLLAMA_CIRCUIT_BREAKER_THRESHOLD,
            self.settings.OLLAMA_CIRCUIT_BREAKER_RESET_SECONDS,
        )
        prompts_dir = Path(__file__).resolve().parents[2] / "prompts"
        self.env = Environment(
            loader=FileSystemLoader(str(prompts_dir)),
            autoescape=select_autoescape(),
        )

    async def generate_explanation(self, gap_type: str, field_values: dict, rule_definition: str) -> str:
        try:
            template = self.env.get_template("explanation.j2")
            prompt = template.render(
                gap_type=gap_type,
                field_values=field_values,
                rule_definition=rule_definition,
            )
            return await self._call_ollama(prompt)
        except OllamaUnavailableError:
            return STATIC_EXPLANATIONS.get(gap_type, STATIC_EXPLANATIONS["unclassified"])

    async def suggest_resolution(self, gap_type: str, tx_metadata: dict, historical_actions: list[str]) -> str:
        try:
            template = self.env.get_template("resolution_suggestion.j2")
            prompt = template.render(
                gap_type=gap_type,
                tx_metadata=tx_metadata,
                historical_actions=historical_actions or ["Manual review and document outcome"],
            )
            return await self._call_ollama(prompt)
        except OllamaUnavailableError:
            return STATIC_RESOLUTIONS.get(
                gap_type,
                f"Review {gap_type.replace('_', ' ')} exception and document resolution steps taken.",
            )

    async def _call_ollama(self, prompt: str) -> str:
        if self.circuit_breaker.is_open():
            raise OllamaUnavailableError("Circuit breaker open")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False},
                    timeout=self.timeout,
                )
                response.raise_for_status()
                self.circuit_breaker.reset()
                return response.json()["response"]
        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPError):
            self.circuit_breaker.record_failure()
            raise OllamaUnavailableError("Ollama timeout or connection error")


ollama_service = OllamaService()
