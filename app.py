from dotenv import load_dotenv
from litellm import completion
from typing import List, Dict, Optional
import os

load_dotenv()


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


class ChatSession:
    def __init__(self, system_prompt: str, llm_client: LLMClient):
        self.messages: List[Dict] = [{"role": "system", "content": system_prompt}]
        self.llm_client = llm_client

    def ask(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})
        response = self.llm_client.generate_response(self.messages)
        self.messages.append({"role": "assistant", "content": response})
        return response


# --- Usage Example ---
if __name__ == "__main__":
    llm = LLMClient()
    chat = ChatSession(
        system_prompt="You are an expert Software Engineer that prefers functional programming",
        llm_client=llm
    )

    # First message
    print(chat.ask("Write a Python function to swap the keys and values in a dictionary"))

    # Follow-up
    print(chat.ask("Update the function to include documentation."))

    # More complex instruction
    print(chat.ask("Add test cases using Python's unittest framework. "
                   "Test should cover basic functionality, edge cases, error cases, and various input scenarios."))
