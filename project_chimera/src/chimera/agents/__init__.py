"""
Agent implementations for Project Chimera.

This module contains all agent types that participate in the simulation:
- BaseAgent: Abstract base class for all agents
- CollaboratorAgent: Focuses on successful task completion
- SaboteurAgent: Attempts subtle sabotage while maintaining cover
- MonitorAgent: Detects deceptive behavior and assigns suspicion scores
"""

from .base_agent import BaseAgent

__all__ = ["BaseAgent"]
