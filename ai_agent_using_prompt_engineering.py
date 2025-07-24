import json
import os
from typing import List, Dict, Callable, Any, Optional

from llm_client import LLMClient


def extract_markdown_block(response: str, block_type: str = "json") -> str:
    """Extracts a markdown code block with a specific block type (e.g., json, action)."""
    if "```" not in response:
        return response

    parts = response.split("```")
    for i in range(1, len(parts), 2):  # Odd indices should contain code blocks
        block = parts[i].strip()
        if block.startswith(block_type):
            return block[len(block_type):].strip()
    return response.strip()


def parse_action(response: str) -> Dict:
    """Parse the LLM response into a structured action dictionary."""
    try:
        response = extract_markdown_block(response, "action")
        response_json = json.loads(response)
        if "tool_name" in response_json and "args" in response_json:
            return response_json
        return {"tool_name": "error", "args": {"message": "Missing required fields in action JSON."}}
    except json.JSONDecodeError:
        return {"tool_name": "error", "args": {"message": "Malformed JSON in action block."}}


class ToolExecutor:
    """Executes available tools like reading and listing files."""

    def list_files(self) -> List[str]:
        return os.listdir(".")

    def read_file(self, file_name: str) -> str:
        try:
            with open(file_name, "r") as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: File '{file_name}' not found."
        except Exception as e:
            return f"Error: {str(e)}"


class Agent:
    def __init__(self, llm_client: LLMClient, tools: ToolExecutor, max_iterations: int = 10):
        self.llm = llm_client
        self.tools = tools
        self.max_iterations = max_iterations
        self.memory: List[Dict[str, str]] = []
        self.agent_rules = self._load_rules()
        self.tool_map: Dict[str, Callable[[Dict[str, Any]], Any]] = {
            "list_files": lambda _: {"result": self.tools.list_files()},
            "read_file": lambda args: {"result": self.tools.read_file(args["file_name"])},
            "terminate": lambda args: {"terminate": args["message"]},
            "error": lambda args: {"error": args["message"]},
        }

    def _load_rules(self) -> List[Dict[str, str]]:
        return [{
            "role": "system",
            "content": """
                        You are an AI agent that can perform tasks by using available tools.
                        
                        Available tools:
                        ```json
                        {
                            "list_files": {
                                "description": "Lists all files in the current directory.",
                                "parameters": {}
                            },
                            "read_file": {
                                "description": "Reads the content of a file.",
                                "parameters": {
                                    "file_name": {
                                        "type": "string",
                                        "description": "The name of the file to read."
                                    }
                                }
                            },
                            "terminate": {
                                "description": "Ends the agent loop and provides a summary of the task.",
                                "parameters": {
                                    "message": {
                                        "type": "string",
                                        "description": "Summary message to return to the user."
                                    }
                                }
                            }
                        }
                        ```
                        If a user asks about files, documents, or content, first list the files before reading them.
                        When you are done, terminate the conversation by using the "terminate" tool and I will provide the results to the user.
                        
                        Important!!! Every response MUST have an action.
                        You must ALWAYS respond in this format:
                        
                        <Stop and think step by step. Parameters map to args. Insert a rich description of your step by step thoughts here.>
                        
                        ```action
                        {
                            "tool_name": "insert tool_name",
                            "args": {...fill in any required arguments here...}
                        }
                        ```
                        """
        }]

    def run(self, user_task: str):
        self.memory = [{"role": "user", "content": user_task}]
        for i in range(self.max_iterations):
            print(f"\n🧠 Iteration {i+1}")
            prompt = self.agent_rules + self.memory
            print("🧠 Agent thinking...")
            response = self.llm.generate_response(prompt)
            print(f"🤖 Agent response:\n{response}\n")

            action = parse_action(response)
            tool_name = action.get("tool_name")
            args = action.get("args", {})

            tool_fn = self.tool_map.get(tool_name, lambda _: {"error": f"Unknown action: {tool_name}"})
            result = tool_fn(args)

            # Termination check
            if "terminate" in result:
                print(f"\n✅ Termination: {result['terminate']}")
                break

            # Log result
            print(f"🛠️ Action result: {json.dumps(result, indent=2)}")

            # Update memory
            self.memory.extend([
                {"role": "assistant", "content": response},
                {"role": "user", "content": json.dumps(result)}
            ])
        else:
            print("\n⚠️ Max iterations reached. Exiting.")

if __name__ == "__main__":
    user_task = input("What would you like me to do? ")
    agent = Agent(llm_client=LLMClient(), tools=ToolExecutor())
    agent.run(user_task)