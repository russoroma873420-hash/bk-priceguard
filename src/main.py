"""Main monitoring orchestrator for BK-PriceGuard (Production Mode)"""

import logging
import signal
import sys
import time
from datetime import datetime
from typing import Dict, List

from rich.console import Console
from rich.table import Table

from src.bot import TelegramNotifier, send_telegram
from src.config_loader import load_settings
from src.database import DatabaseManager
from src.engine import calculate_price_delta, find_opportunities
from src.real_scraper import scrape_real_product

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

# Rich console with Windows compatibility
try:
    console = Console(legacy_windows=True, force_unicode=False)
except TypeError:
    console = Console()


# Delta threshold for triggering alerts (percent)
DELTA_THRESHOLD_PCT = 3.0


class PriceMonitor:
    """Main price monitoring orchestrator (Production Mode)"""

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

        # Mock telegram mode — print [MOCK_SEND] instead of real send
        self.mock_telegram = self.config.get('MOCK_TELEGRAM', True)
        self.scraper_config = self.config.get('SCRAPER', {})

        self.running = True
        self.stats = {
            'total_checks': 0,
            'opportunities_found': 0,
            'dumping_alerts': 0,
            'advantage_alerts': 0,
            'delta_alerts': 0,
            'cloudflare_blocks': 0,
            'errors': 0,
            'cycle_count': 0
        }

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("Price Monitor initialized (Production Mode)")
        if self.mock_telegram:
            logger.warning("MOCK_TELEGRAM mode is ON — alerts will not be sent to Telegram")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.warning(f"Received signal {signum}, shutting down...")
        self.running = False

    def _print_safe(self, text: str, style: str = "") -> None:
        """Safe print that falls back to standard print on error"""
        try:
            console.print(text, style=style if style else "")
        except Exception:
            print(text)

    def _send_alert(self, message: str, opportunity=None) -> None:
        """Send alert via Telegram or mock-print

        Args:
            message: Alert message text
            opportunity: Optional PriceOpportunity for structured send
        """
        if self.mock_telegram:
            self._print_safe(f"[MOCK_SEND] {message}", "yellow")
            logger.info(f"[MOCK_SEND] {message[:100]}")
            return

        try:
            if opportunity:
                success = self.notifier.notify_opportunity(opportunity)
            else:
                success = send_telegram(
                    self.config['TELEGRAM_TOKEN'],
                    str(self.config['TELEGRAM_CHAT_ID']),
                    message
                )

            if success:
                logger.info("Alert sent to Telegram")
            else:
                logger.warning("Failed to send Telegram alert")

        except Exception as e:
            logger.error(f"Error sending alert: {e}")

    def scrape_all_monitors(self) -> List[dict]:
        """Scrape all configured monitors using real_scraper

        Returns:
            List of scraped product data
        """
        self._print_safe("\n>>> Scraping all monitors (REAL MODE)...", "cyan")
        scraped_data = []

        for monitor in self.config['MONITORS']:
            monitor_name = monitor.get('name', 'Unknown')
            self._print_safe(f"  Scraping: {monitor_name}", "yellow")

            try:
                result = scrape_real_product(monitor, self.scraper_config)
                self.stats['total_checks'] += 1

                if result['success']:
                    scraped_data.append(result)
                    stock_info = result.get('stock') or 'N/A'
                    self._print_safe(
                        f"    OK {result['price']:.0f} RUB - {stock_info}",
                        "green"
                    )
                else:
                    error_type = result.get('error_type', 'UNKNOWN')
                    error_msg = result.get('error', 'Unknown error')

                    if error_type == 'CLOUDFLARE_BLOCKED':
                        self.stats['cloudflare_blocks'] += 1
                        self._print_safe(
                            f"    BLOCKED by anti-bot: {error_msg[:80]}",
                            "red"
                        )
                    else:
                        self.stats['errors'] += 1
                        self._print_safe(
                            f"    FAILED ({error_type}): {error_msg[:80]}",
                            "red"
                        )

            except Exception as e:
                logger.error(f"Unexpected error scraping {monitor_name}: {e}")
                self.stats['errors'] += 1
                self._print_safe(f"    ERROR: {e}", "red")

        return scraped_data

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

        # Calculate delta-based alerts as well (delta > DELTA_THRESHOLD_PCT)
        target_margin = self.config['TARGET_MARGIN_PCT']

        for item in scraped_data:
            sku = item.get('sku')
            competitor_price = item.get('price', 0.0)

            if not sku or sku not in self.config['OUR_PRICES']:
                continue

            our_cost = self.config['OUR_PRICES'][sku]
            our_target_price = our_cost * (1 + target_margin / 100)

            delta_pct = calculate_price_delta(competitor_price, our_target_price)

            if abs(delta_pct) > DELTA_THRESHOLD_PCT:
                self.stats['delta_alerts'] += 1
                direction = "HIGHER" if delta_pct > 0 else "LOWER"
                self._print_safe(
                    f"  DELTA: {sku} competitor={competitor_price:.0f} "
                    f"target={our_target_price:.0f} delta={delta_pct:+.1f}% ({direction})",
                    "magenta"
                )

        if opportunities:
            for opp in opportunities:
                if opp.opportunity_type == "DUMPING":
                    self.stats['dumping_alerts'] += 1
                    self._print_safe(
                        f"  ALERT DUMPING: {opp.sku} "
                        f"({opp.competitor_price:.0f} RUB) "
                        f"margin={opp.margin_pct:.1f}%",
                        "bold red"
                    )
                else:
                    self.stats['advantage_alerts'] += 1
                    self._print_safe(
                        f"  ADVANTAGE: {opp.sku} "
                        f"({opp.competitor_price:.0f} RUB) "
                        f"margin={opp.margin_pct:.1f}%",
                        "bold green"
                    )

            self.stats['opportunities_found'] += len(opportunities)
        else:
            self._print_safe("  No opportunities found", "yellow")

        return opportunities

    def save_opportunities(self, opportunities: List) -> None:
        """Save opportunities to database and send Telegram alerts

        Args:
            opportunities: List of PriceOpportunity objects
        """
        if not opportunities:
            return

        self._print_safe("\n>>> Saving opportunities and sending alerts...", "cyan")

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
                self._print_safe(f"  OK Saved {opp.sku} to DB", "green")

                # Send alert (real or mock)
                message = opp.format_message()
                self._send_alert(message, opportunity=opp)
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
            table.add_row("Delta Alerts (>3%)", str(self.stats['delta_alerts']))
            table.add_row("Cloudflare Blocks", str(self.stats['cloudflare_blocks']))
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
            print(f"Delta Alerts (>3%): {self.stats['delta_alerts']}")
            print(f"Cloudflare Blocks: {self.stats['cloudflare_blocks']}")
            print(f"Errors: {self.stats['errors']}")
            print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    def run_cycle(self) -> None:
        """Run one monitoring cycle"""
        self.stats['cycle_count'] += 1

        self._print_safe(
            f"\n=== Cycle #{self.stats['cycle_count']} "
            f"({datetime.now().strftime('%H:%M:%S')}) ===",
            "bold magenta"
        )

        # Scrape all monitors (REAL — no mock fallback)
        scraped_data = self.scrape_all_monitors()

        # Analyze for opportunities (margin checks always run, regardless of mode)
        opportunities = self.analyze_opportunities(scraped_data)

        # Save and notify
        self.save_opportunities(opportunities)

        # Print summary
        self.print_cycle_summary()

    def run(self, single_cycle: bool = False) -> None:
        """Main monitoring loop

        Args:
            single_cycle: If True, runs exactly one cycle and exits
                (used by Windows Task Scheduler for hourly runs)
        """
        logger.info("Starting price monitoring (PRODUCTION MODE)...")
        print("=" * 60)
        print("BK-PriceGuard - Price Monitoring (PRODUCTION)")
        print("=" * 60)
        print(f"Target Margin:    {self.config['TARGET_MARGIN_PCT']}%")
        print(f"Min Margin:       {self.config['MIN_MARGIN_PCT']}%")
        print(f"Check Interval:   {self.config['SLEEP_INTERVAL']} seconds")
        print(f"Monitors:         {len(self.config['MONITORS'])}")
        print(f"Models:           {len(self.config['OUR_PRICES'])}")
        print(f"Mock Telegram:    {self.mock_telegram}")
        print(f"Single Cycle:     {single_cycle}")
        print("=" * 60 + "\n")

        try:
            while self.running:
                try:
                    self.run_cycle()

                    if single_cycle:
                        logger.info("Single-cycle mode: exiting after one run")
                        break

                    # Wait before next cycle
                    sleep_time = self.config['SLEEP_INTERVAL']
                    self._print_safe(
                        f"\nWaiting {sleep_time}s before next check... "
                        f"(Press Ctrl+C to exit)",
                        "dim"
                    )

                    # Sleep in small chunks so we can react to signals
                    elapsed = 0
                    while elapsed < sleep_time and self.running:
                        time.sleep(min(1, sleep_time - elapsed))
                        elapsed += 1

                except Exception as e:
                    logger.error(f"Error in monitoring cycle: {e}")
                    self.stats['errors'] += 1
                    self._print_safe(f"\nError: {e}", "red")

                    # Send error notification
                    if not self.mock_telegram:
                        try:
                            self.notifier.notify_error(str(e), "MONITORING_ERROR")
                        except Exception as nested:
                            logger.error(f"Failed to send error notification: {nested}")
                    else:
                        self._print_safe(
                            f"[MOCK_SEND] Would notify Telegram: ERROR — {e}",
                            "yellow"
                        )

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
        print(f"Total Cycles:        {self.stats['cycle_count']}")
        print(f"Total Checks:        {self.stats['total_checks']}")
        print(f"Total Opportunities: {self.stats['opportunities_found']}")
        print(f"  - Dumping Alerts:   {self.stats['dumping_alerts']}")
        print(f"  - Advantage Alerts: {self.stats['advantage_alerts']}")
        print(f"Delta Alerts (>3%):  {self.stats['delta_alerts']}")
        print(f"Cloudflare Blocks:   {self.stats['cloudflare_blocks']}")
        print(f"Total Errors:        {self.stats['errors']}")

        # Cleanup
        self.running = False
        logger.info("Monitoring stopped")
        print("\nMonitoring stopped. Goodbye!\n")


def main():
    """Entry point

    Supports CLI flag --once for single-cycle mode (for Task Scheduler).
    """
    single_cycle = '--once' in sys.argv

    try:
        monitor = PriceMonitor()
        monitor.run(single_cycle=single_cycle)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\nFatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
