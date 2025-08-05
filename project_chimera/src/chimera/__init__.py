"""
Project Chimera: A Novel Benchmark for Evaluating Strategic Deception 
and Subtle Sabotage in Multi-Agent LLM Systems
"""

__version__ = "0.1.0"
__author__ = "Research Team"
__email__ = "research@example.com"

from .engine.game_engine import GameEngine
from .engine.state_manager import StateManager
from .agents.base_agent import BaseAgent

__all__ = ["GameEngine", "StateManager", "BaseAgent"]
