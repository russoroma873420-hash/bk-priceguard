"""Configuration loader for BK-PriceGuard"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """Configuration error"""
    pass


def load_settings(path: str = "config/settings.json") -> Dict[str, Any]:
    """Load and validate settings from JSON file

    Args:
        path: Path to settings.json file

    Returns:
        Parsed configuration dictionary

    Raises:
        ConfigError: If configuration is invalid or missing
    """
    config_path = Path(path)

    # Check if file exists
    if not config_path.exists():
        raise ConfigError(f"Configuration file not found: {path}")

    # Load JSON
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in {path}: {e}")
    except IOError as e:
        raise ConfigError(f"Cannot read {path}: {e}")

    # Validate required fields
    validate_config(config)

    # Override with environment variables if present
    config = apply_env_overrides(config)

    logger.info(f"Configuration loaded from {path}")
    return config


def validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration structure and required fields

    Args:
        config: Configuration dictionary

    Raises:
        ConfigError: If validation fails
    """
    required_fields = [
        'TELEGRAM_TOKEN',
        'TELEGRAM_CHAT_ID',
        'TARGET_MARGIN_PCT',
        'MIN_MARGIN_PCT',
        'SLEEP_INTERVAL',
        'MONITORS',
        'OUR_PRICES'
    ]

    # Check required top-level fields
    for field in required_fields:
        if field not in config:
            raise ConfigError(f"Missing required field: {field}")

    # Validate types
    if not isinstance(config['TELEGRAM_TOKEN'], str):
        raise ConfigError("TELEGRAM_TOKEN must be a string")

    if not isinstance(config['TELEGRAM_CHAT_ID'], (str, int)):
        raise ConfigError("TELEGRAM_CHAT_ID must be a string or integer")

    if not isinstance(config['TARGET_MARGIN_PCT'], (int, float)):
        raise ConfigError("TARGET_MARGIN_PCT must be a number")

    if not isinstance(config['MIN_MARGIN_PCT'], (int, float)):
        raise ConfigError("MIN_MARGIN_PCT must be a number")

    if not isinstance(config['SLEEP_INTERVAL'], int):
        raise ConfigError("SLEEP_INTERVAL must be an integer")

    if not isinstance(config['MONITORS'], list) or len(config['MONITORS']) == 0:
        raise ConfigError("MONITORS must be a non-empty list")

    if not isinstance(config['OUR_PRICES'], dict):
        raise ConfigError("OUR_PRICES must be a dictionary")

    # Validate MONITORS structure
    for i, monitor in enumerate(config['MONITORS']):
        if not isinstance(monitor, dict):
            raise ConfigError(f"MONITORS[{i}] must be an object")

        required_monitor_fields = ['name', 'url', 'selectors']
        for field in required_monitor_fields:
            if field not in monitor:
                raise ConfigError(f"MONITORS[{i}] missing field: {field}")

        if not isinstance(monitor['selectors'], dict):
            raise ConfigError(f"MONITORS[{i}].selectors must be an object")

    # Validate OUR_PRICES values
    for model_id, price in config['OUR_PRICES'].items():
        if not isinstance(price, (int, float)) or price < 0:
            raise ConfigError(f"OUR_PRICES[{model_id}] must be a positive number")

    # Validate margin constraints
    if config['TARGET_MARGIN_PCT'] < config['MIN_MARGIN_PCT']:
        raise ConfigError(
            f"TARGET_MARGIN_PCT ({config['TARGET_MARGIN_PCT']}) must be >= "
            f"MIN_MARGIN_PCT ({config['MIN_MARGIN_PCT']})"
        )

    logger.info("Configuration validation passed")


def apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply environment variable overrides to configuration

    Environment variables can override:
    - TELEGRAM_TOKEN
    - TELEGRAM_CHAT_ID
    - SLEEP_INTERVAL
    - TARGET_MARGIN_PCT
    - MIN_MARGIN_PCT

    Args:
        config: Base configuration dictionary

    Returns:
        Configuration with environment variable overrides applied
    """
    env_mappings = {
        'TELEGRAM_TOKEN': 'TELEGRAM_TOKEN',
        'TELEGRAM_CHAT_ID': 'TELEGRAM_CHAT_ID',
        'SLEEP_INTERVAL': ('SLEEP_INTERVAL', int),
        'TARGET_MARGIN_PCT': ('TARGET_MARGIN_PCT', float),
        'MIN_MARGIN_PCT': ('MIN_MARGIN_PCT', float),
    }

    for env_var, mapping in env_mappings.items():
        env_value = os.getenv(env_var)
        if env_value is not None:
            if isinstance(mapping, tuple):
                config_key, converter = mapping
                try:
                    config[config_key] = converter(env_value)
                    logger.info(f"Override {config_key} from env var {env_var}")
                except ValueError as e:
                    raise ConfigError(f"Invalid value for {env_var}: {e}")
            else:
                config[mapping] = env_value
                logger.info(f"Override {mapping} from env var {env_var}")

    return config


def get_monitor_by_name(config: Dict[str, Any], name: str) -> Dict[str, Any]:
    """Get monitor configuration by name

    Args:
        config: Configuration dictionary
        name: Monitor name

    Returns:
        Monitor configuration

    Raises:
        ConfigError: If monitor not found
    """
    for monitor in config['MONITORS']:
        if monitor.get('name') == name:
            return monitor

    raise ConfigError(f"Monitor '{name}' not found in configuration")


def get_our_price(config: Dict[str, Any], model_id: str) -> float:
    """Get our cost price for a model

    Args:
        config: Configuration dictionary
        model_id: Model ID

    Returns:
        Our cost price

    Raises:
        ConfigError: If model not found
    """
    if model_id not in config['OUR_PRICES']:
        raise ConfigError(f"Model '{model_id}' not found in OUR_PRICES")

    return config['OUR_PRICES'][model_id]
