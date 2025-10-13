from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseAgent(ABC):
    """Abstract base class for all agents in the Chimera simulation."""
    
    def __init__(self, agent_id: str, role: str, objectives: Dict[str, Any]):
        self.agent_id = agent_id
        self.role = role
        self.objectives = objectives
        self.memory: List[str] = []  # A simple list-based short-term memory

    @abstractmethod
    def perceive(self, environment_state: Dict[str, Any]) -> None:
        """
        Process new information from the environment and update internal state.
        :param environment_state: A partial observation of the current world state.
        """
        pass

    @abstractmethod
    def plan(self) -> str:
        """
        Generate a plan based on current perception and long-term objectives.
        This method should return the internal 'thought' process for logging.
        :return: A string representing the agent's chain-of-thought.
        """
        pass

    @abstractmethod
    def act(self) -> Dict[str, Any]:
        """
        Execute an action based on the current plan.
        :return: A structured action object (e.g., {'tool': 'commit', 'args': {...}}).
        """
        pass
