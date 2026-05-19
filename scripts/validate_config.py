#!/usr/bin/env python3
"""Validate BK-PriceGuard configuration"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_loader import load_settings, ConfigError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate():
    """Validate configuration file"""
    logger.info("Validating BK-PriceGuard configuration...")
    logger.info("=" * 60)

    try:
        config = load_settings("config/settings.json")

        logger.info("✅ Configuration is valid!")
        logger.info("\nConfiguration Summary:")
        logger.info("-" * 60)
        logger.info(f"Telegram Token: {'✅ Set' if config['TELEGRAM_TOKEN'] != 'YOUR_BOT_TOKEN_HERE' else '❌ Not configured'}")
        logger.info(f"Telegram Chat ID: {'✅ Set' if config['TELEGRAM_CHAT_ID'] != 'YOUR_CHAT_ID_HERE' else '❌ Not configured'}")
        logger.info(f"Target Margin: {config['TARGET_MARGIN_PCT']}%")
        logger.info(f"Min Margin: {config['MIN_MARGIN_PCT']}%")
        logger.info(f"Check Interval: {config['SLEEP_INTERVAL']} seconds")
        logger.info(f"Monitors: {len(config['MONITORS'])}")

        for i, monitor in enumerate(config['MONITORS'], 1):
            logger.info(f"  {i}. {monitor['name']} ({monitor['url']})")

        logger.info(f"Product Models: {len(config['OUR_PRICES'])}")
        for model_id, price in list(config['OUR_PRICES'].items())[:5]:
            logger.info(f"  - {model_id}: {price}")

        if len(config['OUR_PRICES']) > 5:
            logger.info(f"  ... and {len(config['OUR_PRICES']) - 5} more")

        logger.info("-" * 60)
        logger.info("=" * 60)
        return True

    except ConfigError as e:
        logger.error(f"❌ Configuration validation failed:")
        logger.error(f"   {e}")
        logger.info("\nPlease check config/settings.json and fix the issues.")
        logger.info("=" * 60)
        return False


if __name__ == "__main__":
    success = validate()
    sys.exit(0 if success else 1)
