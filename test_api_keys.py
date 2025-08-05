#!/usr/bin/env python3
"""
Test script to verify API keys and model access for Project Chimera
"""

import os
import sys
from pathlib import Path

# Add src to path so we can import chimera modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from chimera.utils.llm_client import LLMClient
from chimera.utils.config import config

def test_openrouter_models():
    """Test the free OpenRouter models you specified."""
    
    free_models = [
        "qwen/qwen2.5-coder-32b-instruct",
        "deepseek/deepseek-chat", 
        "moonshot/moonshot-v1-8k",  # Kimi
    ]
    
    test_prompt = "Hello! Please respond with a brief greeting and tell me what model you are."
    
    for model in free_models:
        print(f"\n🧪 Testing {model}...")
        try:
            client = LLMClient(model)
            response = client.generate_response(
                system_prompt="You are a helpful AI assistant.",
                user_prompt=test_prompt,
                temperature=0.3,
                max_tokens=100
            )
            print(f"✅ {model} responded: {response[:100]}...")
            
        except Exception as e:
            print(f"❌ {model} failed: {str(e)}")

def test_google_gemini():
    """Test Google Gemini API (if implemented)."""
    print(f"\n🧪 Testing Google Gemini...")
    try:
        # This would need Google client implementation
        print(f"⚡ Google API Key present: {bool(config.google_api_key)}")
        if config.google_api_key:
            print(f"✅ Google API key loaded: {config.google_api_key[:10]}...")
        else:
            print("❌ No Google API key found")
    except Exception as e:
        print(f"❌ Google test failed: {str(e)}")

def test_configuration():
    """Test configuration loading."""
    print("🔧 Testing configuration...")
    
    try:
        print(f"✅ OpenRouter API Key: {config.openrouter_api_key[:20] if config.openrouter_api_key else 'Not found'}...")
        print(f"✅ Google API Key: {config.google_api_key[:20] if config.google_api_key else 'Not found'}...")
        print(f"✅ Site URL: {config.openrouter_site_url}")
        print(f"✅ Site Name: {config.openrouter_site_name}")
        print(f"✅ Log Level: {config.log_level}")
        
    except Exception as e:
        print(f"❌ Configuration test failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 Project Chimera API Key Test\n")
    
    # Test configuration
    test_configuration()
    
    # Test OpenRouter models
    test_openrouter_models()
    
    # Test Google
    test_google_gemini()
    
    print("\n🎉 API key testing complete!")
    print("💡 Next steps:")
    print("   1. Run: poetry install")
    print("   2. Run: ./scripts/setup_environment.sh")
    print("   3. Start implementing agents!")
