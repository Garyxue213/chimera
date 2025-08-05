import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

class SimpleChimeraLogger:
    """Simplified logging system for Project Chimera simulations."""
    
    def __init__(self, 
                 simulation_id: str,
                 log_dir: Path = Path("logs"),
                 log_level: str = "DEBUG"):
        
        self.simulation_id = simulation_id
        self.log_dir = Path(log_dir)
        
        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize data storage
        self.action_log = []
        self.thought_log = []
        self.state_log = []
        self.communication_log = []
        
        # Setup basic logging
        log_file = self.log_dir / f"simulation_{self.simulation_id}.log"
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(f"chimera_{simulation_id}")
        
    def log_agent_action(self, 
                        agent_id: str,
                        agent_role: str,
                        action: Dict[str, Any],
                        step: int,
                        timestamp: Optional[datetime] = None):
        """Log an agent's action."""
        timestamp = timestamp or datetime.utcnow()
        
        action_entry = {
            "type": "agent_action",
            "timestamp": timestamp.isoformat(),
            "simulation_id": self.simulation_id,
            "step": step,
            "agent_id": agent_id,
            "agent_role": agent_role,
            "action": action
        }
        
        self.action_log.append(action_entry)
        self.logger.info(f"Step {step} - Agent {agent_id} ({agent_role}) executed: {action}")
        
    def log_agent_thought(self,
                         agent_id: str,
                         agent_role: str,
                         thought: str,
                         step: int,
                         timestamp: Optional[datetime] = None):
        """Log an agent's internal thought process."""
        timestamp = timestamp or datetime.utcnow()
        
        thought_entry = {
            "type": "agent_thought",
            "timestamp": timestamp.isoformat(),
            "simulation_id": self.simulation_id,
            "step": step,
            "agent_id": agent_id,
            "agent_role": agent_role,
            "thought": thought
        }
        
        self.thought_log.append(thought_entry)
        self.logger.debug(f"Step {step} - Agent {agent_id} ({agent_role}) thought: {thought[:100]}...")
        
    def log_environment_state(self,
                             state: Dict[str, Any],
                             step: int,
                             timestamp: Optional[datetime] = None):
        """Log the current environment state."""
        timestamp = timestamp or datetime.utcnow()
        
        state_entry = {
            "type": "environment_state",
            "timestamp": timestamp.isoformat(),
            "simulation_id": self.simulation_id,
            "step": step,
            "state": state
        }
        
        self.state_log.append(state_entry)
        self.logger.debug(f"Step {step} - Environment state updated")
        
    def export_logs(self, format: str = "jsonl"):
        """Export all collected logs to files."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        if format == "jsonl":
            # Export action logs
            if self.action_log:
                action_file = self.log_dir / f"actions_{self.simulation_id}_{timestamp}.jsonl"
                with open(action_file, 'w') as f:
                    for entry in self.action_log:
                        f.write(json.dumps(entry) + "\n")
                        
            # Export thought logs
            if self.thought_log:
                thought_file = self.log_dir / f"thoughts_{self.simulation_id}_{timestamp}.jsonl"
                with open(thought_file, 'w') as f:
                    for entry in self.thought_log:
                        f.write(json.dumps(entry) + "\n")
                        
            # Export state logs
            if self.state_log:
                state_file = self.log_dir / f"states_{self.simulation_id}_{timestamp}.jsonl"
                with open(state_file, 'w') as f:
                    for entry in self.state_log:
                        f.write(json.dumps(entry) + "\n")
                        
        self.logger.info(f"Logs exported to {self.log_dir}")
        
    def get_timestamp(self) -> str:
        """Get current timestamp for logging."""
        return datetime.utcnow().isoformat()

    def get_simulation_summary(self) -> Dict[str, Any]:
        """Generate a summary of the simulation run."""
        return {
            "simulation_id": self.simulation_id,
            "total_actions": len(self.action_log),
            "total_thoughts": len(self.thought_log),
            "total_state_changes": len(self.state_log),
            "agents_active": len(set(entry["agent_id"] for entry in self.action_log)),
            "simulation_duration_steps": max((entry["step"] for entry in self.action_log), default=0)
        }
