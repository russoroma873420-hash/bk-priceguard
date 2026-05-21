#!/usr/bin/env python3
"""Test script for BK-PriceGuard functionality"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.bot import send_telegram, format_status_report, TelegramNotifier
from src.config_loader import load_settings
from src.database import DatabaseManager
from src.engine import (
    PriceOpportunity,
    analyze_competitor_price,
    calc_price_strategy,
    find_opportunities,
    rank_opportunities
)
from src.scraper import fetch_url, parse_price, parse_stock, scrape_product

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_scraper():
    """Test scraper functionality"""
    logger.info("=" * 60)
    logger.info("Testing Scraper Module")
    logger.info("=" * 60)

    # Test fetch_url
    logger.info("\n1. Testing fetch_url with mock data...")
    url = 'https://example.com/ac-model-001'
    html = fetch_url(url, use_mock=True)
    if html:
        logger.info("✓ fetch_url works")
    else:
        logger.error("✗ fetch_url failed")
        return False

    # Test parse_price
    logger.info("\n2. Testing parse_price...")
    price = parse_price(html, 'span.price')
    if price > 0:
        logger.info(f"✓ Parsed price: {price}")
    else:
        logger.error("✗ parse_price failed")
        return False

    # Test parse_stock
    logger.info("\n3. Testing parse_stock...")
    stock = parse_stock(html, 'div.stock')
    if stock:
        logger.info(f"✓ Parsed stock: {stock}")
    else:
        logger.warning("⚠ Stock not found (may be optional)")

    # Test scrape_product
    logger.info("\n4. Testing scrape_product...")
    result = scrape_product(url, {
        'price': 'span.price',
        'stock': 'div.stock',
        'name': 'h1.product-title'
    }, use_mock=True)
    if result['success']:
        logger.info(f"✓ Scraped product: {result['name']} - {result['price']}")
    else:
        logger.error("✗ scrape_product failed")
        return False

    return True


def test_engine():
    """Test engine functionality"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Engine Module")
    logger.info("=" * 60)

    # Test calc_price_strategy
    logger.info("\n1. Testing calc_price_strategy...")
    cost = 5000
    margin = 20
    target = calc_price_strategy(cost, margin)
    expected = 6000
    if target == expected:
        logger.info(f"✓ calc_price_strategy: {cost} + {margin}% = {target}")
    else:
        logger.error(f"✗ calc_price_strategy failed: expected {expected}, got {target}")
        return False

    # Test analyze_competitor_price
    logger.info("\n2. Testing analyze_competitor_price...")
    competitor_price = 5500
    analysis = analyze_competitor_price(competitor_price, cost)
    logger.info(f"✓ Margin: {analysis['margin_pct']:.1f}%")
    logger.info(f"  Dumping: {analysis['is_dumping']}")
    logger.info(f"  Advantage: {analysis['is_advantage']}")

    # Test find_opportunities
    logger.info("\n3. Testing find_opportunities...")
    our_skus = {
        'MODEL_001': 5000,
        'MODEL_002': 7500,
        'MODEL_003': 9000
    }

    scraped_prices = [
        {
            'sku': 'MODEL_001',
            'price': 5500,
            'url': 'https://example.com/1',
            'success': True
        },
        {
            'sku': 'MODEL_002',
            'price': 7200,
            'url': 'https://example.com/2',
            'success': True
        },
        {
            'sku': 'MODEL_003',
            'price': 15000,
            'url': 'https://example.com/3',
            'success': True
        }
    ]

    config = {
        'TARGET_MARGIN_PCT': 20,
        'MIN_MARGIN_PCT': 15
    }

    opportunities = find_opportunities(our_skus, scraped_prices, config)
    logger.info(f"✓ Found {len(opportunities)} opportunities")
    for opp in opportunities:
        logger.info(f"  - {opp.sku}: {opp.opportunity_type} (margin: {opp.margin_pct:.1f}%)")

    # Test rank_opportunities
    logger.info("\n4. Testing rank_opportunities...")
    ranked = rank_opportunities(opportunities, sort_by='margin_pct')
    logger.info(f"✓ Ranked {len(ranked)} opportunities by margin")

    return True


def test_database():
    """Test database functionality"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Database Module")
    logger.info("=" * 60)

    try:
        db = DatabaseManager("data/test_price_monitor.db")

        # Test save_price
        logger.info("\n1. Testing save_price...")
        record = {
            'sku': 'TEST_001',
            'original_price': 5500,
            'target_price': 5000,
            'delta': 500,
            'source_url': 'https://test.example.com'
        }
        success = db.save_price(record)
        if success:
            logger.info("✓ Saved test record")
        else:
            logger.error("✗ Failed to save record")
            return False

        # Test get_unsaved_alerts
        logger.info("\n2. Testing get_unsaved_alerts...")
        alerts = db.get_unsaved_alerts(hour_limit=24)
        logger.info(f"✓ Found {len(alerts)} unsaved alerts")

        # Test export_to_csv
        logger.info("\n3. Testing export_to_csv...")
        csv_file = "data/test_report.csv"
        success = db.export_to_csv(csv_file, hours=24)
        if success:
            logger.info(f"✓ Exported to {csv_file}")
        else:
            logger.warning("⚠ No records to export")

        # Test get_price_stats
        logger.info("\n4. Testing get_price_stats...")
        stats = db.get_price_stats('TEST_001', hours=24)
        if stats:
            logger.info(f"✓ Stats: min={stats['min_price']}, "
                       f"max={stats['max_price']}, avg={stats['avg_price']:.0f}")
        else:
            logger.info("✓ No stats available (first record)")

        return True

    except Exception as e:
        logger.error(f"Database test failed: {e}")
        return False


def test_bot():
    """Test bot functionality"""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Bot Module")
    logger.info("=" * 60)

    config = load_settings()
    token = config['TELEGRAM_TOKEN']
    chat_id = config['TELEGRAM_CHAT_ID']

    # Test send_telegram
    logger.info("\n1. Testing send_telegram...")
    result = send_telegram(
        token,
        chat_id,
        "[TEST] This is a test message",
        use_mock=True
    )
    if result:
        logger.info("✓ send_telegram works (mock mode)")
    else:
        logger.info("ℹ Token not configured for real Telegram")

    # Test format_status_report
    logger.info("\n2. Testing format_status_report...")
    status = {
        'total_checks': 10,
        'opportunities_found': 2,
        'dumping_alerts': 1,
        'advantage_alerts': 1,
        'errors': 0,
        'timestamp': '2026-05-19 13:30:00'
    }
    message = format_status_report(status)
    logger.info("✓ Formatted status report")
    logger.info(f"\n{message}")

    # Test TelegramNotifier
    logger.info("\n3. Testing TelegramNotifier...")
    notifier = TelegramNotifier(token, chat_id)
    logger.info(f"✓ Created notifier")
    logger.info(f"  Messages sent: {notifier.get_stats()['total_messages_sent']}")

    return True


def main():
    """Run all tests"""
    logger.info("\n" + "=" * 60)
    logger.info("BK-PriceGuard Functionality Test Suite")
    logger.info("=" * 60)

    tests = [
        ("Scraper", test_scraper),
        ("Engine", test_engine),
        ("Database", test_database),
        ("Bot", test_bot),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"Test {name} crashed: {e}")
            results[name] = False

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)

    for name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        logger.info(f"{name:20} {status}")

    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    logger.info("-" * 60)
    logger.info(f"Total: {passed_count}/{total_count} tests passed")
    logger.info("=" * 60)

    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
