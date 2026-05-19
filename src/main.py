"""Main monitoring orchestrator for BK-PriceGuard"""

import logging
import signal
import sys
import time
from datetime import datetime
from typing import Dict, List

from rich.console import Console
from rich.table import Table

from src.bot import TelegramNotifier
from src.config_loader import load_settings
from src.database import DatabaseManager
from src.engine import find_opportunities
from src.scraper import scrape_product

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/price_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Rich console for beautiful output (with Windows compatibility)
try:
    console = Console(legacy_windows=True, force_unicode=False)
except TypeError:
    # Fallback for older versions of rich
    console = Console()


class PriceMonitor:
    """Main price monitoring orchestrator"""

    def __init__(self, config_path: str = "config/settings.json"):
        """Initialize price monitor

        Args:
            config_path: Path to configuration file
        """
        self.config = load_settings(config_path)
        self.db = DatabaseManager(self.config['DATABASE']['PATH'])
        self.notifier = TelegramNotifier(
            self.config['TELEGRAM_TOKEN'],
            str(self.config['TELEGRAM_CHAT_ID'])
        )
        self.running = True
        self.stats = {
            'total_checks': 0,
            'opportunities_found': 0,
            'dumping_alerts': 0,
            'advantage_alerts': 0,
            'errors': 0,
            'cycle_count': 0
        }

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("Price Monitor initialized")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.warning(f"Received signal {signum}, shutting down...")
        self.running = False

    def scrape_all_monitors(self) -> List[dict]:
        """Scrape all configured monitors

        Returns:
            List of scraped product data
        """
        self._print_safe("\n>>> Scraping all monitors...", "cyan")
        scraped_data = []

        for monitor in self.config['MONITORS']:
            try:
                monitor_name = monitor.get('name', 'Unknown')
                url = monitor.get('url', '')
                selectors = monitor.get('selectors', {})

                if not url:
                    logger.warning(f"Monitor {monitor_name} has no URL")
                    continue

                self._print_safe(f"  Scraping: {monitor_name}", "yellow")

                result = scrape_product(url, selectors, use_mock=True)

                if result['success']:
                    # Map to SKU if possible
                    sku = self._identify_sku_from_url(url)
                    result['sku'] = sku
                    scraped_data.append(result)
                    self._print_safe(f"    OK {result['price']:.0f} - {result['stock']}", "green")
                else:
                    self._print_safe(f"    FAILED to scrape", "red")
                    self.stats['errors'] += 1

                self.stats['total_checks'] += 1

            except Exception as e:
                logger.error(f"Error scraping monitor {monitor.get('name')}: {e}")
                self.stats['errors'] += 1
                self._print_safe(f"    ERROR: {e}", "red")

        return scraped_data

    def _print_safe(self, text: str, style: str = "") -> None:
        """Safe print that falls back to standard print on error"""
        try:
            console.print(text, style=style if style else "")
        except Exception:
            print(text)

    def _identify_sku_from_url(self, url: str) -> str:
        """Try to identify SKU from URL

        Args:
            url: Product URL

        Returns:
            SKU identifier or 'UNKNOWN'
        """
        # Simple heuristic: extract model number from URL
        if 'model-001' in url or 'ac-model-001' in url:
            return 'MODEL_001'
        elif 'model-002' in url or 'ac-model-002' in url:
            return 'MODEL_002'
        elif 'model-003' in url or 'ac-003' in url:
            return 'MODEL_003'
        elif 'model-004' in url or 'ac-004' in url:
            return 'MODEL_004'
        else:
            return 'UNKNOWN'

    def analyze_opportunities(self, scraped_data: List[dict]) -> List:
        """Analyze scraped data for price opportunities

        Args:
            scraped_data: List of scraped product data

        Returns:
            List of PriceOpportunity objects
        """
        if not scraped_data:
            self._print_safe("No data to analyze", "yellow")
            return []

        self._print_safe("\n>>> Analyzing opportunities...", "cyan")

        opportunities = find_opportunities(
            self.config['OUR_PRICES'],
            scraped_data,
            self.config
        )

        if opportunities:
            for opp in opportunities:
                if opp.opportunity_type == "DUMPING":
                    self.stats['dumping_alerts'] += 1
                    self._print_safe(
                        f"  ALERT DUMPING: {opp.sku} "
                        f"({opp.competitor_price:.0f}) "
                        f"margin={opp.margin_pct:.1f}%",
                        "red"
                    )
                else:
                    self.stats['advantage_alerts'] += 1
                    self._print_safe(
                        f"  OK ADVANTAGE: {opp.sku} "
                        f"({opp.competitor_price:.0f}) "
                        f"margin={opp.margin_pct:.1f}%",
                        "green"
                    )

            self.stats['opportunities_found'] += len(opportunities)
        else:
            self._print_safe("  No opportunities found", "yellow")

        return opportunities

    def save_opportunities(self, opportunities: List) -> None:
        """Save opportunities to database and send alerts

        Args:
            opportunities: List of PriceOpportunity objects
        """
        if not opportunities:
            return

        self._print_safe("\n>>> Saving opportunities...", "cyan")

        for opp in opportunities:
            # Save to database
            record = {
                'sku': opp.sku,
                'original_price': opp.competitor_price,
                'target_price': opp.our_cost_price,
                'delta': opp.competitor_price - opp.our_cost_price,
                'source_url': opp.competitor_url,
                'timestamp': opp.timestamp
            }

            success = self.db.save_price(record)
            if success:
                self._print_safe(f"  OK Saved {opp.sku}", "green")

                # Send Telegram notification
                if self.config['TELEGRAM_TOKEN'] != 'YOUR_BOT_TOKEN_HERE':
                    self.notifier.notify_opportunity(opp)
                else:
                    logger.info(f"[MOCK] Would send alert for {opp.sku} to Telegram")
            else:
                self._print_safe(f"  FAILED to save {opp.sku}", "red")
                self.stats['errors'] += 1

    def print_cycle_summary(self) -> None:
        """Print cycle summary in a nice table"""
        try:
            table = Table(title="Monitoring Cycle Summary")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Cycle Number", str(self.stats['cycle_count']))
            table.add_row("Total Checks", str(self.stats['total_checks']))
            table.add_row("Opportunities", str(self.stats['opportunities_found']))
            table.add_row("  - Dumping Alerts", str(self.stats['dumping_alerts']))
            table.add_row("  - Our Advantages", str(self.stats['advantage_alerts']))
            table.add_row("Errors", str(self.stats['errors']))
            table.add_row("Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            console.print(table)
        except Exception:
            print("\n--- Monitoring Cycle Summary ---")
            print(f"Cycle: {self.stats['cycle_count']}")
            print(f"Total Checks: {self.stats['total_checks']}")
            print(f"Opportunities: {self.stats['opportunities_found']}")
            print(f"  - Dumping: {self.stats['dumping_alerts']}")
            print(f"  - Advantage: {self.stats['advantage_alerts']}")
            print(f"Errors: {self.stats['errors']}")
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    def run_cycle(self) -> None:
        """Run one monitoring cycle"""
        self.stats['cycle_count'] += 1

        self._print_safe(
            f"\n=== Cycle #{self.stats['cycle_count']} "
            f"({datetime.now().strftime('%H:%M:%S')}) ===",
            "magenta"
        )

        # Scrape all monitors
        scraped_data = self.scrape_all_monitors()

        # Analyze for opportunities
        opportunities = self.analyze_opportunities(scraped_data)

        # Save and notify
        self.save_opportunities(opportunities)

        # Print summary
        self.print_cycle_summary()

    def run(self, test_mode: bool = False) -> None:
        """Main monitoring loop

        Args:
            test_mode: Run only one cycle if True
        """
        logger.info("Starting price monitoring...")
        print("BK-PriceGuard - Price Monitoring Started")
        print(f"Target Margin: {self.config['TARGET_MARGIN_PCT']}%")
        print(f"Min Margin: {self.config['MIN_MARGIN_PCT']}%")
        print(f"Check Interval: {self.config['SLEEP_INTERVAL']} seconds")
        print(f"Monitors: {len(self.config['MONITORS'])}")
        print(f"Models: {len(self.config['OUR_PRICES'])}\n")

        try:
            while self.running:
                try:
                    self.run_cycle()

                    # Wait before next cycle
                    sleep_time = self.config['SLEEP_INTERVAL']
                    self._print_safe(
                        f"\nWaiting {sleep_time}s before next check... "
                        f"(Press Ctrl+C to exit)",
                        "dim"
                    )

                    time.sleep(sleep_time)

                    if test_mode:
                        break

                except Exception as e:
                    logger.error(f"Error in monitoring cycle: {e}")
                    self.stats['errors'] += 1
                    self._print_safe(f"\nError: {e}", "red")

                    # Send error notification if configured
                    if self.config['TELEGRAM_TOKEN'] != 'YOUR_BOT_TOKEN_HERE':
                        self.notifier.notify_error(str(e), "MONITORING_ERROR")

                    time.sleep(5)  # Wait before retry

        except KeyboardInterrupt:
            logger.info("Monitoring interrupted by user")
            self._print_safe("\nMonitoring interrupted by user", "yellow")
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        """Graceful shutdown"""
        logger.info("Shutting down...")
        print("\n=== Shutting Down ===")

        # Print final statistics
        print("\n=== Final Statistics ===")
        print(f"Total Cycles: {self.stats['cycle_count']}")
        print(f"Total Checks: {self.stats['total_checks']}")
        print(f"Total Opportunities: {self.stats['opportunities_found']}")
        print(f"  - Dumping Alerts: {self.stats['dumping_alerts']}")
        print(f"  - Advantage Alerts: {self.stats['advantage_alerts']}")
        print(f"Total Errors: {self.stats['errors']}")

        # Cleanup
        self.running = False
        logger.info("Monitoring stopped")
        print("\nMonitoring stopped. Goodbye!\n")


def main():
    """Entry point"""
    try:
        monitor = PriceMonitor()
        monitor.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        console.print(f"\n[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
