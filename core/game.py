import time
import traceback
from dataclasses import dataclass
from typing import Callable, Dict, Any, List


@dataclass(frozen=True)
class Goal:
    priority: int
    name: str
    description: str


class Action:
    def __init__(self,
                 name: str,
                 function: Callable,
                 description: str,
                 parameters: Dict,
                 terminal: bool = False):
        self.name = name
        self.function = function
        self.description = description
        self.terminal = terminal
        self.parameters = parameters

    def execute(self, **args) -> Any:
        """Execute the action's function"""
        return self.function(**args)


class ActionRegistry:
    def __init__(self):
        self.actions = {}

    def register(self, action: Action):
        self.actions[action.name] = action

    def get_action(self, name: str) -> [Action, None]:
        return self.actions.get(name, None)

    def get_actions(self) -> List[Action]:
        """Get all registered actions"""
        return list(self.actions.values())


class Memory:
    def __init__(self):
        self.items = []

    def add_memory(self, memory: dict):
        self.items.append(memory)

    def get_memories(self, limit: int = None) -> List[Dict]:
        return self.items[:limit]


class Environment:
    def execute_action(self, action: Action, args: dict) -> dict:
        try:
            result = action.execute(**args)
            return self.format_result(result)
        except Exception as e:
            return {
                "tool_executed": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def format_result(self, result: Any) -> dict:
        return {
            "tool_executed": True,
            "result": result,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%Z")
        }