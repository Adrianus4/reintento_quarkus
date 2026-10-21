from abc import ABC, abstractmethod
from typing import Dict, Tuple


class BaseLLMClient(ABC):
    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 8192,
        temperature: float = 0.2,
    ) -> Tuple[str, int, int]:
        """
        Generate text output from the model.
        Returns: (output_text, prompt_tokens, completion_tokens)
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Verify API Key authenticity and model reachability."""
        pass

