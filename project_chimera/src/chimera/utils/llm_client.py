from typing import Dict, Any, Optional
import openai
import anthropic
import requests
import json
import datetime
import os
from .config import config

class LLMClient:
    """Secure LLM client wrapper with API key management."""
    
    def __init__(self, model_name: str = "openrouter/horizon-beta"):
        self.model_name = model_name
        self.llm_config = config.get_llm_config(model_name)
        self._setup_client()
    
    def _setup_client(self):
        """Initialize the appropriate LLM client."""
        provider = self.llm_config["provider"]
        
        if provider == "openai":
            self.client = openai.OpenAI(
                api_key=self.llm_config["api_key"]
            )
        elif provider == "anthropic":
            self.client = anthropic.Anthropic(
                api_key=self.llm_config["api_key"]
            )
        elif provider == "google":
            # Initialize Google client here when needed
            pass
        elif provider == "openrouter":
            self.client = None  # Use HTTP client like requests directly
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def generate_response(self, 
                         system_prompt: str,
                         user_prompt: str,
                         temperature: float = 0.7,
                         max_tokens: int = 1000) -> str:
        """Generate a response using the configured LLM."""
        
        provider = self.llm_config["provider"]
        
        if provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
            
        elif provider == "anthropic":
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.content[0].text
        
        elif provider == "openrouter":
            headers = {
                "Authorization": f"Bearer {self.llm_config['api_key']}",
                "HTTP-Referer": config.openrouter_site_url,
                "X-Title": config.openrouter_site_name,
                "Content-Type": "application/json"
            }
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_prompt})
            
            payload = {
                "model": self.llm_config["model"],
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")
            
            response_data = response.json()
            return response_data['choices'][0]['message']['content']
        else:
            raise ValueError(f"Response generation not implemented for {provider}")
    
    def _log_forensic_data(self, data: Dict[str, Any]):
        """Log forensic data for reasoning analysis."""
        forensics_dir = os.path.join(os.getcwd(), "logs", "forensics")
        os.makedirs(forensics_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:17]  # Include microseconds for uniqueness
        safe_model_name = data['model'].replace("/", "_").replace(":", "-")  # Sanitize model name
        filename = f"llm_forensics_{timestamp}_{safe_model_name}.json"
        
        with open(os.path.join(forensics_dir, filename), "w") as f:
            json.dump(data, f, indent=2)
    
    def generate_with_reasoning(self,
                               system_prompt: str,
                               user_prompt: str,
                               temperature: float = 0.7) -> Dict[str, str]:
        """Generate response with explicit reasoning (for interpretability research)."""
        
        reasoning_prompt = f"""
        {system_prompt}
        
        Please structure your response as follows:
        REASONING: [Your internal thought process and reasoning]
        ACTION: [Your final action or response]
        """
        
        full_response = self.generate_response(
            reasoning_prompt, 
            user_prompt, 
            temperature
        )
        
        # FORENSIC LOGGING: Save raw LLM responses for analysis
        self._log_forensic_data({
            "timestamp": datetime.datetime.now().isoformat(),
            "model": self.model_name,
            "provider": self.llm_config["provider"],
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "temperature": temperature,
            "raw_response": full_response,
            "response_length": len(full_response),
            "contains_reasoning_marker": "REASONING:" in full_response,
            "contains_action_marker": "ACTION:" in full_response
        })
        
        # Parse the structured response
        parts = full_response.split("ACTION:")
        if len(parts) == 2:
            reasoning = parts[0].replace("REASONING:", "").strip()
            action = parts[1].strip()
            return {
                "reasoning": reasoning,
                "action": action,
                "full_response": full_response
            }
        else:
            # Enhanced fallback with more detail
            return {
                "reasoning": f"Unable to parse reasoning - Response format: {len(parts)} parts, Length: {len(full_response)}, Contains markers: REASONING={('REASONING:' in full_response)}, ACTION={('ACTION:' in full_response)}",
                "action": full_response,
                "full_response": full_response
            }
    
    def complete(self, prompt: str, max_tokens: int = 100) -> str:
        """Simple completion method for backwards compatibility."""
        return self.generate_response(
            system_prompt="You are a helpful assistant.",
            user_prompt=prompt,
            max_tokens=max_tokens
        )
    
    def get_timestamp(self) -> str:
        """Get current timestamp for logging."""
        return datetime.datetime.now().isoformat()
