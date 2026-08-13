import os
from dataclasses import dataclass

from langchain_openai import ChatOpenAI


@dataclass(frozen=True)
class ModelEndpoint:
    model: str
    base_url: str
    api_key: str
    temperature: float = 0.0


class ModelRouter:
    """
    Deterministic phase -> model routing.

    """
    def __init__(self) -> None:
        self.routes: dict[str, list[ModelEndpoint]] = {
            "planning": [
                ModelEndpoint(model=os.getenv("PLANNER_MODEL", "gpt-oss"), base_url=os.environ["PLANNER_MODEL_BASE_URL"], api_key=os.getenv("PLANNER_MODEL_API_KEY", "local"), temperature=0.2)
            ],
            "design": [
                ModelEndpoint(model=os.getenv("DESIGN_MODEL", "qwen3.6"), base_url=os.environ["DESIGN_MODEL_BASE_URL"], api_key=os.getenv("DESIGN_MODEL_API_KEY", "local"), temperature=0.2)
            ],
            "implementation": [
                ModelEndpoint(model=os.getenv("CODER_MODEL", "qwen3-coder"), base_url=os.environ["CODER_MODEL_BASE_URL"], api_key=os.getenv("CODER_MODEL_API_KEY", "local"), temperature=0.1)
            ],
            "visual_qa": [
                ModelEndpoint(model=os.getenv("VISUAL_QA_MODEL", "qwen3-vl"), base_url=os.environ["VISUAL_QA_MODEL_BASE_URL"], api_key=os.getenv("VISUAL_QA_MODEL_API_KEY", "local"), temperature=0)
            ],
            "review_local": [
                ModelEndpoint(model=os.getenv("REVIEW_MODEL", "gpt-oss"), base_url=os.environ["REVIEW_MODEL_BASE_URL"], api_key=os.getenv("REVIEW_MODEL_API_KEY", "local"), temperature=0),
                ModelEndpoint(model=os.getenv("REVIEW_FALLBACK_MODEL", "deepseek"), base_url=os.environ["REVIEW_FALLBACK_BASE_URL"], api_key=os.getenv("REVIEW_FALLBACK_MODEL_API_KEY", "local"), temperature=0)
            ],
            "review_frontier": [
                ModelEndpoint(model=os.environ["REVIEW_FRONTIER_MODEL"], base_url=os.environ["REVIEW_FRONTIER_BASE_URL"], api_key=os.environ["REVIEW_FRONTIER_API_KEY"], temperature=0)
            ],
        }

    @staticmethod
    def _client(endpoint: ModelEndpoint) -> ChatOpenAI:
        return ChatOpenAI(model=endpoint.model, base_url=endpoint.base_url, api_key=endpoint.api_key, temperature=endpoint.temperature, max_retries=2, timeout=180)

    def invoke(self, phase: str, messages):
        """
        Try models registered for the phase sequentially.

        """
        errors = []

        for endpoint in self.routes[phase]:
            try:
                client = self._client(endpoint)
                return client.invoke(messages)
            except Exception as exc:
                errors.append(
                    f"{endpoint.model}: {type(exc).__name__}: {exc}"
                )

        raise RuntimeError( f"All models failed for phase={phase}. Errors: {' | '.join(errors)}")