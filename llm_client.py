from typing import Optional, List, Dict

from litellm import completion


class LLMClient:
    def __init__(
            self,
            model: str = "ollama/llama3.2:latest",
            api_base: str = "http://localhost:11434",
            max_tokens: Optional[int] = None,
    ):
        self.model = model
        self.api_base = api_base
        self.max_tokens = max_tokens

    def generate_response(self, messages: List[Dict]) -> str:
        response = completion(
            model=self.model,
            messages=messages,
            api_base=self.api_base,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content
