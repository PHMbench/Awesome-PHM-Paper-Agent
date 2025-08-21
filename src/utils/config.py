"""
Configuration management utilities for APPA system.

This module provides functions to load, validate, and manage system configuration
from the config.yaml file.
"""

import os
import yaml
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Exception raised for configuration-related errors."""
    pass


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration data
        
    Raises:
        ConfigError: If configuration file is missing or invalid
    """
    if not os.path.exists(config_path):
        raise ConfigError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Validate required sections
        validate_config(config)
        return config
        
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in configuration file: {e}")
    except Exception as e:
        raise ConfigError(f"Error loading configuration: {e}")


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration structure and required fields.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ConfigError: If configuration is invalid
    """
    required_sections = [
        'search_parameters',
        'quality_filters',
        'output_preferences',
        'api_configuration'
    ]

    for section in required_sections:
        if section not in config:
            raise ConfigError(f"Missing required configuration section: {section}")

    # Validate search parameters
    search_params = config['search_parameters']
    if 'keywords' not in search_params or not search_params['keywords']:
        raise ConfigError("Search keywords are required")

    if 'time_range' not in search_params:
        raise ConfigError("Time range is required")

    # Validate time range format
    time_range = search_params['time_range']
    if not isinstance(time_range, str) or '-' not in time_range:
        raise ConfigError("Time range must be in format 'YYYY-YYYY'")

    try:
        start_year, end_year = map(int, time_range.split('-'))
        current_year = datetime.now().year
        if start_year > end_year or end_year > current_year:
            raise ConfigError("Invalid time range")
    except ValueError:
        raise ConfigError("Time range must contain valid years")

    # Validate incremental update date
    if 'incremental_update_date' in search_params:
        try:
            datetime.fromisoformat(search_params['incremental_update_date'])
        except ValueError:
            raise ConfigError("Incremental update date must be in ISO format (YYYY-MM-DD)")

    # Validate filesystem configuration
    if 'filesystem' in config:
        fs_config = config['filesystem']
        output_dir = fs_config.get('output_directory', '.')

        # Validate output directory path
        if not isinstance(output_dir, str):
            raise ConfigError("Output directory must be a string path")

        # Check if output directory is writable (create if doesn't exist)
        import os
        try:
            os.makedirs(output_dir, exist_ok=True)
            if not os.access(output_dir, os.W_OK):
                raise ConfigError(f"Output directory is not writable: {output_dir}")
        except OSError as e:
            raise ConfigError(f"Cannot create or access output directory {output_dir}: {e}")

    # Validate LLM configuration
    if 'llm' in config:
        llm_config = config['llm']

        if llm_config.get('enabled', False):
            provider = llm_config.get('provider', 'openai')

            if provider not in ['openai', 'anthropic', 'local', 'disabled']:
                raise ConfigError(f"Invalid LLM provider: {provider}. Must be one of: openai, anthropic, local, disabled")

            # Validate provider-specific configuration
            providers = llm_config.get('providers', {})
            if provider in providers:
                provider_config = providers[provider]

                if provider in ['openai', 'anthropic']:
                    # Check for API key (can be in config or environment)
                    api_key = provider_config.get('api_key', '')
                    env_var = f"{provider.upper()}_API_KEY"

                    if not api_key and not os.environ.get(env_var):
                        logger.warning(f"No API key found for {provider}. Set in config or environment variable {env_var}")

                # Validate model parameters
                max_tokens = provider_config.get('max_tokens', 2000)
                if not isinstance(max_tokens, int) or max_tokens <= 0:
                    raise ConfigError(f"max_tokens must be a positive integer for {provider}")

                temperature = provider_config.get('temperature', 0.3)
                if not isinstance(temperature, (int, float)) or not 0 <= temperature <= 2:
                    raise ConfigError(f"temperature must be a number between 0 and 2 for {provider}")


def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get configuration value using dot notation.
    
    Args:
        config: Configuration dictionary
        key_path: Dot-separated path to the value (e.g., 'search_parameters.keywords')
        default: Default value if key is not found
        
    Returns:
        Configuration value or default
    """
    keys = key_path.split('.')
    value = config
    
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default


def update_config_value(config: Dict[str, Any], key_path: str, value: Any) -> None:
    """
    Update configuration value using dot notation.
    
    Args:
        config: Configuration dictionary to update
        key_path: Dot-separated path to the value
        value: New value to set
    """
    keys = key_path.split('.')
    current = config
    
    # Navigate to the parent of the target key
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    # Set the final value
    current[keys[-1]] = value


def save_config(config: Dict[str, Any], config_path: str = "config.yaml") -> None:
    """
    Save configuration to YAML file.
    
    Args:
        config: Configuration dictionary to save
        config_path: Path to save the configuration file
        
    Raises:
        ConfigError: If unable to save configuration
    """
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        logger.info(f"Configuration saved to {config_path}")
    except Exception as e:
        raise ConfigError(f"Error saving configuration: {e}")


if __name__ == "__main__":
    # Test configuration loading
    try:
        config = load_config()
        print("Configuration loaded successfully")
        print(f"Keywords: {get_config_value(config, 'search_parameters.keywords')}")
        print(f"Time range: {get_config_value(config, 'search_parameters.time_range')}")
    except ConfigError as e:
        print(f"Configuration error: {e}")
