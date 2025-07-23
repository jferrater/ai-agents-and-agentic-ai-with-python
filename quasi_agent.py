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


class QuasiAgent:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def _extract_code_block(self, response: str) -> str:
        """Extract code block from response"""
        if "```" not in response:
            return response
        code_block = response.split("```")[1].strip()
        return code_block[6:] if code_block.startswith("python") else code_block

    def _add_message(self, messages: List[Dict], role: str, content: str) -> None:
        messages.append({"role": role, "content": content})

    def _build_filename(self, description: str) -> str:
        filename = ''.join(c for c in description.lower() if c.isalnum() or c.isspace())
        return filename.replace(" ", "_")[:30] + ".py"

    def _interactive_input(self) -> str:
        print("\nWhat kind of function would you like to create?")
        print("Example: 'A function that calculates the factorial of a number'")
        return input("Your description: ").strip()

    def develop_custom_function(self):
        function_description = self._interactive_input()

        messages = [{"role": "system", "content": "You are a Python expert helping to develop a function"}]

        # Step 1 - Generate base function
        self._add_message(messages, "user", f"Write a Python function that {function_description}. "
                                            f"Output the function in a ```python code block```.")
        base_function = self._extract_code_block(self.llm_client.generate_response(messages))
        print("\n=== Initial Function ===")
        print(base_function)

        self._add_message(messages, "assistant", f"```python\n{base_function}\n```")

        # Step 2 - Add documentation
        self._add_message(messages, "user", "Add a comprehensive documentation to this function, including "
                                            "description, parameters, return value, examples, and edge cases. "
                                            "Output the function in a ```python code block```.")
        documented_function = self._extract_code_block(self.llm_client.generate_response(messages))
        print("\n=== Documented Function ===")
        print(documented_function)

        self._add_message(messages, "assistant", f"```python\n{documented_function}\n```")

        # Step 3 - Generate test cases
        self._add_message(messages, "user", "Add unittest test cases for this function, including tests for basic "
                                            "functionality, edge cases, error cases and various input scenarios. "
                                            "Output the code in a ```python code block```.")
        test_cases = self._extract_code_block(self.llm_client.generate_response(messages))
        print("\n=== Test Cases ===")
        print(test_cases)

        # Save to file
        filename = self._build_filename(function_description)
        with open(filename, 'w') as f:
            f.write(documented_function + "\n\n" + test_cases)

        print(f"\n✅ Code and tests written to: {filename}")
        return documented_function, test_cases, filename


if __name__ == "__main__":
    llm = LLMClient()
    agent = QuasiAgent(llm)
    agent.develop_custom_function()
