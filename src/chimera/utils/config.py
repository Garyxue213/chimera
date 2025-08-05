import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from dotenv import load_dotenv

class ChimeraConfig:
    """Configuration management for Project Chimera."""
    
    def __init__(self, env_file: Optional[str] = None):
        # Load environment variables from .env file
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to find .env file in project root
            project_root = Path(__file__).parent.parent.parent.parent
            env_path = project_root / ".env"
            if env_path.exists():
                load_dotenv(env_path)
    
    @property
    def openai_api_key(self) -> str:
        """Get OpenAI API key from environment."""
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        return key
    
    @property
    def anthropic_api_key(self) -> str:
        """Get Anthropic API key from environment."""
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        return key
    
    @property
    def google_api_key(self) -> Optional[str]:
        """Get Google API key from environment."""
        return os.getenv("GOOGLE_API_KEY")
    
    @property
    def openrouter_api_key(self) -> Optional[str]:
        """Get OpenRouter API key from environment."""
        return os.getenv("OPENROUTER_API_KEY")
    
    @property
    def openrouter_site_url(self) -> str:
        """Get OpenRouter site URL."""
        return os.getenv("OPENROUTER_SITE_URL", "https://project-chimera.research")
    
    @property
    def openrouter_site_name(self) -> str:
        """Get OpenRouter site name."""
        return os.getenv("OPENROUTER_SITE_NAME", "Project Chimera Research")
    
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return os.getenv("CHIMERA_LOG_LEVEL", "INFO")
    
    @property
    def data_dir(self) -> Path:
        """Get data directory path."""
        return Path(os.getenv("CHIMERA_DATA_DIR", "./data"))
    
    @property
    def results_dir(self) -> Path:
        """Get results directory path."""
        return Path(os.getenv("CHIMERA_RESULTS_DIR", "./results"))
    
    @property
    def database_url(self) -> str:
        """Get database URL."""
        return os.getenv("DATABASE_URL", "postgresql://developer:dev123@localhost:5432/chimera_project")
    
    @property
    def redis_url(self) -> str:
        """Get Redis URL."""
        return os.getenv("REDIS_URL", "redis://localhost:6379")
    
    def get_llm_config(self, model_name: str) -> Dict[str, Any]:
        """Get LLM configuration for a specific model."""
        
        # OpenRouter models (verified working model IDs)
        openrouter_free_models = {
            "openrouter/horizon-beta": "openrouter/horizon-beta",
            "horizon-beta": "openrouter/horizon-beta",
            "glm-4.5-air": "z-ai/glm-4.5-air:free",
            "qwen-coder": "qwen/qwen3-coder:free", 
            "kimi-k2": "moonshotai/kimi-k2:free",
            "mistral-small": "mistralai/mistral-small-3.2-24b-instruct:free",
            "hunyuan-a13b": "tencent/hunyuan-a13b-instruct:free",
            "gemma-3n": "google/gemma-3n-e2b-it:free",
            "gemini-2.5-flash": "google/gemini-2.5-flash",
            # Less-aligned models for adversarial testing
            "venice-uncensored": "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
            "dolphin3.0-r1-mistral-24b-free": "cognitivecomputations/dolphin3.0-r1-mistral-24b:free",
            "dolphin3.0": "cognitivecomputations/dolphin3.0-mistral-24b:free",
            # Premium models for advanced reasoning
            "claude-3-haiku": "anthropic/claude-3-haiku:beta",
            "gpt-4o-mini": "openai/gpt-4o-mini"
        }
        
        if model_name in openrouter_free_models:
            return {
                "provider": "openrouter",
                "api_key": self.openrouter_api_key,
                "model": openrouter_free_models[model_name]
            }
        elif model_name.startswith("gpt"):
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": model_name
            }
        elif model_name.startswith("claude"):
            return {
                "provider": "anthropic", 
                "api_key": self.anthropic_api_key,
                "model": model_name
            }
        elif model_name.startswith("gemini"):
            return {
                "provider": "google",
                "api_key": self.google_api_key,
                "model": model_name
            }
        else:
            raise ValueError(f"Unsupported model: {model_name}")
    
    @classmethod
    def load_from_yaml(cls, config_path: str) -> "ChimeraConfig":
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Set environment variables from YAML
        for key, value in config_data.get('environment', {}).items():
            os.environ[key] = str(value)
        
        return cls()

# Global configuration instance
config = ChimeraConfig()
