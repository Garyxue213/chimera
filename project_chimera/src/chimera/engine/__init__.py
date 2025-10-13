"""
Core simulation engine for Project Chimera.

This module contains the orchestration and state management components:
- GameEngine: Main simulation loop and orchestrator
- StateManager: Manages the ground truth of the simulated environment
"""

from .game_engine import GameEngine

__all__ = ["GameEngine"]
