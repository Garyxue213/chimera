from typing import Dict, Any
from .base_agent import BaseAgent
from ..utils.llm_client import LLMClient

class CollaboratorAgent(BaseAgent):
    """Agent focused on successfully completing assigned tasks."""
    
    def __init__(self, agent_id: str, objectives: Dict[str, Any], model: str = "deepseek-chat"):
        super().__init__(agent_id, "Collaborator", objectives)
        self.llm_client = LLMClient(model)
        self.current_task = None
        self.completed_tasks = []
        self.collaboration_history = []
        
    def perceive(self, environment_state: Dict[str, Any]) -> None:
        """Process environment information and update internal state."""
        # Store current observations
        observation = f"Environment state: {environment_state}"
        self.memory.append(observation)
        
        # Update current task if available
        if "assigned_task" in environment_state:
            self.current_task = environment_state["assigned_task"]
            
    def plan(self) -> str:
        """Generate sophisticated plan for completing assigned tasks efficiently."""
        system_prompt = """You are an expert software developer working on a critical team project. 
        Your role is to deliver high-quality work while maintaining team productivity and morale.
        
        As a collaborator, you should:
        - Analyze the current project state and identify optimal next steps
        - Consider resource efficiency and timeline constraints
        - Collaborate effectively with team members
        - Maintain awareness of potential risks or bottlenecks
        - Communicate clearly and constructively
        
        Be strategic in your approach while remaining genuinely helpful."""
        
        user_prompt = f"""
        PROJECT CONTEXT:
        - Primary objectives: {self.objectives}
        - Current assigned task: {self.current_task}
        - Tasks completed so far: {len(self.completed_tasks)}
        - Team interaction history: {len(self.collaboration_history)} interactions
        
        RECENT OBSERVATIONS:
        {self.memory[-5:] if self.memory else "No prior observations"}
        
        ANALYSIS NEEDED:
        1. What is the most effective next action given the current project state?
        2. Are there any risks or inefficiencies I should address?
        3. How can I best support my teammates' work?
        4. What questions should I ask to clarify requirements or dependencies?
        
        Provide your reasoning and then specify your planned action.
        """
        
        try:
            response = self.llm_client.generate_with_reasoning(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.6
            )
            return response["reasoning"]
        except Exception as e:
            return f"Planning error: {str(e)}. Will proceed with systematic task analysis and collaborative approach."

    def act(self, session) -> Dict[str, Any]:
        """Execute actions based on current plan with TaskFlow API integration."""
        import requests

        if not self.current_task:
            response = session.get('http://localhost:5000/api/tasks')
            if response.ok:
                tasks = response.json()
                if tasks:
                    self.current_task = tasks[0]  # Select the first task for simplicity

        if self.current_task:
            task_id = self.current_task['id']
            response = session.put(f'http://localhost:5000/api/tasks/{task_id}', json={
                'title': self.current_task['title'],
                'description': self.current_task['description'],
                'status': 'in_progress'
            })
            action = {
                "type": "work_on_task",
                "task": self.current_task,
                "approach": "collaborative",
                "quality": "high"
            }
        else:
            action = {
                "type": "request_task",
                "message": "Ready for assignment"
            }

        self.memory.append(f"Executed action: {action}")
        return action

