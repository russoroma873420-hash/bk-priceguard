#!/usr/bin/env python3
"""Export price monitoring reports to CSV"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def export_report(hours=24, output_dir="data/reports"):
    """Export price data to CSV report"""
    logger.info(f"Exporting price data for last {hours} hours...")

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_path / f"price_report_{timestamp}.csv"

    # Export from database
    db = DatabaseManager("data/price_monitor.db")
    success = db.export_to_csv(str(filename), hours=hours)

    if success:
        logger.info(f"✅ Report exported to {filename}")
        return True
    else:
        logger.error(f"❌ Failed to export report")
        return False


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description="Export price monitoring reports to CSV"
    )
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Include data from last N hours (default: 24)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/reports",
        help="Output directory for reports (default: data/reports)"
    )

    args = parser.parse_args()

    success = export_report(hours=args.hours, output_dir=args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
