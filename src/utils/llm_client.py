"""
LLM Client Framework for APPA system.

This module provides a unified interface for different LLM providers
including OpenAI, Anthropic, and local models.
"""

import os
import time
import json
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Exception raised by LLM clients."""
    pass


class RateLimiter:
    """Rate limiter for LLM API requests."""
    
    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.minute_requests = []
        self.hour_requests = []
    
    def wait_if_needed(self) -> None:
        """Wait if rate limits would be exceeded."""
        now = datetime.now()
        
        # Clean old requests
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        self.minute_requests = [req_time for req_time in self.minute_requests if req_time > minute_ago]
        self.hour_requests = [req_time for req_time in self.hour_requests if req_time > hour_ago]
        
        # Check minute limit
        if len(self.minute_requests) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.minute_requests[0]).total_seconds()
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        # Check hour limit
        if len(self.hour_requests) >= self.requests_per_hour:
            sleep_time = 3600 - (now - self.hour_requests[0]).total_seconds()
            if sleep_time > 0:
                logger.info(f"Hourly rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        # Record this request
        now = datetime.now()
        self.minute_requests.append(now)
        self.hour_requests.append(now)


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rate_limiter = RateLimiter(
            requests_per_minute=config.get('requests_per_minute', 60),
            requests_per_hour=config.get('requests_per_hour', 1000)
        )
    
    @abstractmethod
    def generate_text(self, prompt: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> str:
        """Generate text using the LLM."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM service is available."""
        pass


class OpenAIClient(BaseLLMClient):
    """OpenAI API client."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key') or os.environ.get('OPENAI_API_KEY')
        self.model = config.get('model', 'gpt-4')
        self.max_tokens = config.get('max_tokens', 2000)
        self.temperature = config.get('temperature', 0.3)
        
        if not self.api_key:
            raise LLMError("OpenAI API key not found. Set in config or OPENAI_API_KEY environment variable.")
    
    def generate_text(self, prompt: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> str:
        """Generate text using OpenAI API."""
        self.rate_limiter.wait_if_needed()
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': self.model,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': max_tokens or self.max_tokens,
            'temperature': temperature or self.temperature
        }
        
        try:
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
            
        except requests.RequestException as e:
            raise LLMError(f"OpenAI API request failed: {e}")
        except (KeyError, IndexError) as e:
            raise LLMError(f"Unexpected OpenAI API response format: {e}")
    
    def is_available(self) -> bool:
        """Check if OpenAI API is available."""
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'}
            response = requests.get('https://api.openai.com/v1/models', headers=headers, timeout=10)
            return response.status_code == 200
        except:
            return False


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key') or os.environ.get('ANTHROPIC_API_KEY')
        self.model = config.get('model', 'claude-3-sonnet-20240229')
        self.max_tokens = config.get('max_tokens', 2000)
        self.temperature = config.get('temperature', 0.3)
        
        if not self.api_key:
            raise LLMError("Anthropic API key not found. Set in config or ANTHROPIC_API_KEY environment variable.")
    
    def generate_text(self, prompt: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> str:
        """Generate text using Anthropic API."""
        self.rate_limiter.wait_if_needed()
        
        headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        data = {
            'model': self.model,
            'max_tokens': max_tokens or self.max_tokens,
            'temperature': temperature or self.temperature,
            'messages': [{'role': 'user', 'content': prompt}]
        }
        
        try:
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=data,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            return result['content'][0]['text'].strip()
            
        except requests.RequestException as e:
            raise LLMError(f"Anthropic API request failed: {e}")
        except (KeyError, IndexError) as e:
            raise LLMError(f"Unexpected Anthropic API response format: {e}")
    
    def is_available(self) -> bool:
        """Check if Anthropic API is available."""
        try:
            headers = {
                'x-api-key': self.api_key,
                'anthropic-version': '2023-06-01'
            }
            # Anthropic doesn't have a simple health check endpoint, so we'll assume it's available if we have a key
            return bool(self.api_key)
        except:
            return False


class LocalLLMClient(BaseLLMClient):
    """Local LLM client (e.g., Ollama)."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.model = config.get('model', 'llama2')
        self.max_tokens = config.get('max_tokens', 2000)
        self.temperature = config.get('temperature', 0.3)
    
    def generate_text(self, prompt: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> str:
        """Generate text using local LLM."""
        self.rate_limiter.wait_if_needed()
        
        data = {
            'model': self.model,
            'prompt': prompt,
            'options': {
                'num_predict': max_tokens or self.max_tokens,
                'temperature': temperature or self.temperature
            },
            'stream': False
        }
        
        try:
            response = requests.post(
                f'{self.base_url}/api/generate',
                json=data,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            return result['response'].strip()
            
        except requests.RequestException as e:
            raise LLMError(f"Local LLM request failed: {e}")
        except KeyError as e:
            raise LLMError(f"Unexpected local LLM response format: {e}")
    
    def is_available(self) -> bool:
        """Check if local LLM is available."""
        try:
            response = requests.get(f'{self.base_url}/api/tags', timeout=5)
            return response.status_code == 200
        except:
            return False


class LLMClientFactory:
    """Factory for creating LLM clients."""
    
    @staticmethod
    def create_client(provider: str, config: Dict[str, Any]) -> Optional[BaseLLMClient]:
        """Create an LLM client based on provider."""
        try:
            if provider == 'openai':
                return OpenAIClient(config)
            elif provider == 'anthropic':
                return AnthropicClient(config)
            elif provider == 'local':
                return LocalLLMClient(config)
            elif provider == 'disabled':
                return None
            else:
                raise LLMError(f"Unknown LLM provider: {provider}")
        except Exception as e:
            logger.error(f"Failed to create {provider} client: {e}")
            return None


class LLMManager:
    """Manager for LLM operations with fallback support."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm_config = config.get('llm', {})
        self.enabled = self.llm_config.get('enabled', False)
        self.fallback_enabled = self.llm_config.get('features', {}).get('fallback_enabled', True)
        
        self.client = None
        if self.enabled:
            provider = self.llm_config.get('provider', 'openai')
            provider_config = self.llm_config.get('providers', {}).get(provider, {})
            
            # Add rate limiting config
            rate_limits = self.llm_config.get('rate_limits', {})
            provider_config.update(rate_limits)
            
            self.client = LLMClientFactory.create_client(provider, provider_config)
            
            if self.client and not self.client.is_available():
                logger.warning(f"LLM provider {provider} is not available")
                if not self.fallback_enabled:
                    self.client = None
    
    def is_enabled(self) -> bool:
        """Check if LLM is enabled and available."""
        return self.enabled and self.client is not None
    
    def generate_text(self, prompt: str, max_tokens: Optional[int] = None, temperature: Optional[float] = None) -> Optional[str]:
        """Generate text using LLM with error handling."""
        if not self.is_enabled():
            return None
        
        try:
            return self.client.generate_text(prompt, max_tokens, temperature)
        except Exception as e:
            logger.error(f"LLM text generation failed: {e}")
            if not self.fallback_enabled:
                raise
            return None
    
    def get_feature_enabled(self, feature: str) -> bool:
        """Check if a specific LLM feature is enabled."""
        if not self.is_enabled():
            return False
        
        features = self.llm_config.get('features', {})
        return features.get(feature, False)


if __name__ == "__main__":
    # Test LLM client
    test_config = {
        'llm': {
            'enabled': True,
            'provider': 'openai',
            'providers': {
                'openai': {
                    'api_key': 'test-key',
                    'model': 'gpt-3.5-turbo',
                    'max_tokens': 100,
                    'temperature': 0.3
                }
            },
            'rate_limits': {
                'requests_per_minute': 60,
                'requests_per_hour': 1000
            },
            'features': {
                'enhanced_analysis': True,
                'fallback_enabled': True
            }
        }
    }
    
    manager = LLMManager(test_config)
    print(f"LLM enabled: {manager.is_enabled()}")
    print(f"Enhanced analysis enabled: {manager.get_feature_enabled('enhanced_analysis')}")
