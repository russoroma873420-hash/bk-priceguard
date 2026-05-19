"""Database module for BK-PriceGuard using SQLAlchemy"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from sqlalchemy import Column, DateTime, Float, Integer, String, create_engine, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)

Base = declarative_base()


class PriceLog(Base):
    """Price log entry model"""
    __tablename__ = 'price_logs'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    sku = Column(String(100), nullable=False)
    original_price = Column(Float, nullable=False)
    target_price = Column(Float, nullable=False)
    delta = Column(Float, nullable=False)
    source_url = Column(String(500), nullable=False)
    alerted = Column(Integer, default=0)  # 0 = not alerted, 1 = alerted

    def __repr__(self):
        return (f"<PriceLog(id={self.id}, sku={self.sku}, "
                f"original_price={self.original_price}, delta={self.delta})>")


class DatabaseManager:
    """Manages database operations for price monitoring"""

    def __init__(self, db_path: str = "data/price_monitor.db"):
        """Initialize database connection

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_data_dir()
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.init_db()

    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        data_dir = Path(self.db_path).parent
        data_dir.mkdir(parents=True, exist_ok=True)

    def init_db(self):
        """Initialize database tables"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def save_price(self, record: dict) -> bool:
        """Save price record to database

        Args:
            record: Dictionary with keys:
                - sku: Product SKU/model ID
                - original_price: Current market price
                - target_price: Our target price
                - delta: Price difference (original - target)
                - source_url: URL where price was found

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            session = self.SessionLocal()
            price_log = PriceLog(
                sku=record['sku'],
                original_price=record['original_price'],
                target_price=record['target_price'],
                delta=record['delta'],
                source_url=record['source_url'],
                timestamp=record.get('timestamp', datetime.utcnow())
            )
            session.add(price_log)
            session.commit()
            logger.info(f"Saved price record for {record['sku']}: {record['original_price']}")
            session.close()
            return True
        except Exception as e:
            logger.error(f"Failed to save price record: {e}")
            session.close()
            return False

    def get_unsaved_alerts(self, hour_limit: int = 1) -> list:
        """Get price records that should trigger alerts

        Args:
            hour_limit: Only get records from last N hours

        Returns:
            List of unsaved alert records
        """
        try:
            session = self.SessionLocal()
            cutoff_time = datetime.utcnow() - timedelta(hours=hour_limit)

            alerts = session.query(PriceLog).filter(
                PriceLog.timestamp >= cutoff_time,
                PriceLog.alerted == 0
            ).all()

            result = [
                {
                    'id': alert.id,
                    'timestamp': alert.timestamp,
                    'sku': alert.sku,
                    'original_price': alert.original_price,
                    'target_price': alert.target_price,
                    'delta': alert.delta,
                    'source_url': alert.source_url
                }
                for alert in alerts
            ]

            session.close()
            return result
        except Exception as e:
            logger.error(f"Failed to get unsaved alerts: {e}")
            session.close()
            return []

    def mark_alerts_sent(self, alert_ids: list) -> bool:
        """Mark alerts as sent (alerted=1)

        Args:
            alert_ids: List of alert IDs to mark as sent

        Returns:
            True if successful, False otherwise
        """
        try:
            session = self.SessionLocal()
            session.query(PriceLog).filter(
                PriceLog.id.in_(alert_ids)
            ).update({PriceLog.alerted: 1})
            session.commit()
            session.close()
            return True
        except Exception as e:
            logger.error(f"Failed to mark alerts as sent: {e}")
            session.close()
            return False

    def export_to_csv(self, filename: str, hours: int = 24) -> bool:
        """Export price logs to CSV file

        Args:
            filename: Output CSV file path
            hours: Include records from last N hours

        Returns:
            True if exported successfully, False otherwise
        """
        try:
            session = self.SessionLocal()
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            records = session.query(PriceLog).filter(
                PriceLog.timestamp >= cutoff_time
            ).all()

            if not records:
                logger.warning(f"No records to export for the last {hours} hours")
                session.close()
                return False

            data = {
                'Timestamp': [r.timestamp for r in records],
                'SKU': [r.sku for r in records],
                'Original Price': [r.original_price for r in records],
                'Target Price': [r.target_price for r in records],
                'Delta': [r.delta for r in records],
                'Source URL': [r.source_url for r in records],
                'Alerted': [bool(r.alerted) for r in records]
            }

            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            logger.info(f"Exported {len(records)} records to {filename}")
            session.close()
            return True
        except Exception as e:
            logger.error(f"Failed to export to CSV: {e}")
            session.close()
            return False

    def get_price_stats(self, sku: str, hours: int = 24) -> dict:
        """Get price statistics for a SKU

        Args:
            sku: Product SKU
            hours: Analyze last N hours

        Returns:
            Dictionary with min, max, avg prices
        """
        try:
            session = self.SessionLocal()
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            stats = session.query(
                func.min(PriceLog.original_price).label('min_price'),
                func.max(PriceLog.original_price).label('max_price'),
                func.avg(PriceLog.original_price).label('avg_price'),
                func.count(PriceLog.id).label('count')
            ).filter(
                PriceLog.sku == sku,
                PriceLog.timestamp >= cutoff_time
            ).first()

            session.close()

            if stats.count == 0:
                return None

            return {
                'sku': sku,
                'min_price': float(stats.min_price),
                'max_price': float(stats.max_price),
                'avg_price': float(stats.avg_price),
                'count': stats.count
            }
        except Exception as e:
            logger.error(f"Failed to get price stats: {e}")
            session.close()
            return None

    def cleanup_old_records(self, days: int = 30) -> int:
        """Delete records older than N days

        Args:
            days: Delete records older than this many days

        Returns:
            Number of deleted records
        """
        try:
            session = self.SessionLocal()
            cutoff_time = datetime.utcnow() - timedelta(days=days)

            count = session.query(PriceLog).filter(
                PriceLog.timestamp < cutoff_time
            ).delete()

            session.commit()
            session.close()
            logger.info(f"Deleted {count} old records (older than {days} days)")
            return count
        except Exception as e:
            logger.error(f"Failed to cleanup old records: {e}")
            session.close()
            return 0
