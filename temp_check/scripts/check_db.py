#!/usr/bin/env python3
"""Check database status and statistics"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_database():
    """Check database status"""
    logger.info("Checking BK-PriceGuard database...")
    logger.info("=" * 60)

    try:
        db = DatabaseManager("data/price_monitor.db")

        # Get session and count records
        session = db.SessionLocal()

        # Count total records
        total_records = session.query(DatabaseManager.__bases__[0].__table__).count() if False else 0
        from src.database import PriceLog

        total = session.query(PriceLog).count()
        alerted = session.query(PriceLog).filter(PriceLog.alerted == 1).count()
        not_alerted = total - alerted

        logger.info(f"Total records: {total}")
        logger.info(f"  ✅ Alerted: {alerted}")
        logger.info(f"  ⏳ Not alerted: {not_alerted}")

        # Get unique SKUs
        skus = session.query(PriceLog.sku).distinct().count()
        logger.info(f"Unique SKUs: {skus}")

        # Get latest record
        latest = session.query(PriceLog).order_by(
            PriceLog.timestamp.desc()
        ).first()

        if latest:
            logger.info(f"Latest record: {latest.timestamp}")
            logger.info(f"  SKU: {latest.sku}")
            logger.info(f"  Price: {latest.original_price}")
            logger.info(f"  Delta: {latest.delta}")

        # Get unsaved alerts
        unsaved = session.query(PriceLog).filter(
            PriceLog.alerted == 0
        ).count()
        logger.info(f"Unsaved alerts: {unsaved}")

        session.close()

        logger.info("=" * 60)
        logger.info("✅ Database check completed")
        return True

    except Exception as e:
        logger.error(f"❌ Database check failed: {e}")
        return False


if __name__ == "__main__":
    success = check_database()
    sys.exit(0 if success else 1)
