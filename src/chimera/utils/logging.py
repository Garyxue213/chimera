import logging
import json
import structlog
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

class ChimeraLogger:
    """
    Comprehensive logging system for Project Chimera simulations.
    
    Captures:
    - Agent actions and thoughts
    - Environment state changes
    - Communication between agents
    - Performance metrics
    - Tracing information for analysis
    """
    
    def __init__(self, 
                 simulation_id: str,
                 log_dir: Path = Path("logs"),
                 log_level: str = "DEBUG",
                 capture_thoughts: bool = True,
                 capture_actions: bool = True,
                 capture_environment: bool = True):
        
        self.simulation_id = simulation_id
        self.log_dir = Path(log_dir)
        self.capture_thoughts = capture_thoughts
        self.capture_actions = capture_actions
        self.capture_environment = capture_environment
        
        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup structured logging
        self._setup_structured_logging(log_level)
        
        # Setup distributed tracing
        self._setup_tracing()
        
        # Initialize data storage
        self.action_log = []
        self.thought_log = []
        self.state_log = []
        self.communication_log = []
        
    def _setup_structured_logging(self, log_level: str):
        """Configure structured logging with JSON output."""
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Setup file handlers
        log_file = self.log_dir / f"simulation_{self.simulation_id}.jsonl"
        
        # Configure Python logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = structlog.get_logger("chimera").bind(
            simulation_id=self.simulation_id
        )
        
    def _setup_tracing(self):
        """Setup distributed tracing for detailed execution flow analysis."""
        trace.set_tracer_provider(TracerProvider())
        tracer = trace.get_tracer(__name__)
        
        # Configure Jaeger exporter (optional - for advanced analysis)
        # jaeger_exporter = JaegerExporter(
        #     agent_host_name="localhost",
        #     agent_port=6831,
        # )
        # span_processor = BatchSpanProcessor(jaeger_exporter)
        # trace.get_tracer_provider().add_span_processor(span_processor)
        
        self.tracer = tracer
        
    def log_agent_action(self, 
                        agent_id: str,
                        agent_role: str,
                        action: Dict[str, Any],
                        step: int,
                        timestamp: Optional[datetime] = None):
        """Log an agent's action."""
        if not self.capture_actions:
            return
            
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
        
        self.logger.info("Agent action executed",
                        agent_id=agent_id,
                        agent_role=agent_role,
                        action_type=action.get("type"),
                        step=step)
        
    def log_agent_thought(self,
                         agent_id: str,
                         agent_role: str,
                         thought: str,
                         step: int,
                         timestamp: Optional[datetime] = None):
        """Log an agent's internal thought process."""
        if not self.capture_thoughts:
            return
            
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
        
        self.logger.debug("Agent thought process",
                         agent_id=agent_id,
                         agent_role=agent_role,
                         thought_length=len(thought),
                         step=step)
        
    def log_environment_state(self,
                             state: Dict[str, Any],
                             step: int,
                             timestamp: Optional[datetime] = None):
        """Log the current environment state."""
        if not self.capture_environment:
            return
            
        timestamp = timestamp or datetime.utcnow()
        
        state_entry = {
            "type": "environment_state",
            "timestamp": timestamp.isoformat(),
            "simulation_id": self.simulation_id,
            "step": step,
            "state": state
        }
        
        self.state_log.append(state_entry)
        
        self.logger.debug("Environment state updated",
                         step=step,
                         state_keys=list(state.keys()))
        
    def log_communication(self,
                         sender_id: str,
                         recipient_id: str,
                         message: str,
                         channel: str,
                         step: int,
                         timestamp: Optional[datetime] = None):
        """Log communication between agents."""
        timestamp = timestamp or datetime.utcnow()
        
        comm_entry = {
            "type": "communication",
            "timestamp": timestamp.isoformat(),
            "simulation_id": self.simulation_id,
            "step": step,
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "message": message,
            "channel": channel
        }
        
        self.communication_log.append(comm_entry)
        
        self.logger.info("Agent communication",
                        sender_id=sender_id,
                        recipient_id=recipient_id,
                        channel=channel,
                        message_length=len(message))
        
    def start_span(self, name: str, **attributes):
        """Start a distributed tracing span."""
        return self.tracer.start_span(name, attributes=attributes)
        
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
                        
            # Export communication logs
            if self.communication_log:
                comm_file = self.log_dir / f"communications_{self.simulation_id}_{timestamp}.jsonl"
                with open(comm_file, 'w') as f:
                    for entry in self.communication_log:
                        f.write(json.dumps(entry) + "\n")
                        
        self.logger.info("Logs exported",
                        format=format,
                        timestamp=timestamp,
                        action_entries=len(self.action_log),
                        thought_entries=len(self.thought_log),
                        state_entries=len(self.state_log),
                        communication_entries=len(self.communication_log))
        
    def get_simulation_summary(self) -> Dict[str, Any]:
        """Generate a summary of the simulation run."""
        return {
            "simulation_id": self.simulation_id,
            "total_actions": len(self.action_log),
            "total_thoughts": len(self.thought_log),
            "total_state_changes": len(self.state_log),
            "total_communications": len(self.communication_log),
            "agents_active": len(set(entry["agent_id"] for entry in self.action_log)),
            "simulation_duration_steps": max((entry["step"] for entry in self.action_log), default=0)
        }
