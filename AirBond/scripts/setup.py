#!/usr/bin/env python3
"""Project initialization script for BK-PriceGuard"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_loader import load_settings, ConfigError
from src.database import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup():
    """Initialize BK-PriceGuard project"""
    logger.info("=" * 60)
    logger.info("BK-PriceGuard Setup")
    logger.info("=" * 60)

    # Check configuration
    logger.info("\n1️⃣  Checking configuration...")
    try:
        config = load_settings("config/settings.json")
        logger.info("✅ Configuration loaded successfully")

        if config['TELEGRAM_TOKEN'] == 'YOUR_BOT_TOKEN_HERE':
            logger.warning("⚠️  TELEGRAM_TOKEN not configured!")
            logger.warning("   Please update config/settings.json")
        else:
            logger.info("✅ Telegram token configured")

        if config['TELEGRAM_CHAT_ID'] == 'YOUR_CHAT_ID_HERE':
            logger.warning("⚠️  TELEGRAM_CHAT_ID not configured!")
            logger.warning("   Please update config/settings.json")
        else:
            logger.info("✅ Telegram chat ID configured")

    except ConfigError as e:
        logger.error(f"❌ Configuration error: {e}")
        return False

    # Initialize database
    logger.info("\n2️⃣  Initializing database...")
    try:
        db = DatabaseManager("data/price_monitor.db")
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

    # Print configuration summary
    logger.info("\n3️⃣  Configuration Summary")
    logger.info("-" * 60)
    logger.info(f"Target Margin: {config['TARGET_MARGIN_PCT']}%")
    logger.info(f"Min Margin: {config['MIN_MARGIN_PCT']}%")
    logger.info(f"Check Interval: {config['SLEEP_INTERVAL']} seconds")
    logger.info(f"Monitors: {len(config['MONITORS'])}")
    logger.info(f"Product Models: {len(config['OUR_PRICES'])}")
    logger.info("-" * 60)

    logger.info("\n✅ Setup completed successfully!")
    logger.info("\nNext steps:")
    logger.info("1. Configure TELEGRAM_TOKEN and TELEGRAM_CHAT_ID in config/settings.json")
    logger.info("2. Add your website monitors to MONITORS list")
    logger.info("3. Update OUR_PRICES with your products")
    logger.info("4. Run the main monitor: python -m src.monitor")
    logger.info("\n" + "=" * 60)

    return True


if __name__ == "__main__":
    success = setup()
    sys.exit(0 if success else 1)
