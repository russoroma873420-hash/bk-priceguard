"""Price analysis and opportunity detection engine"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PriceOpportunity:
    """Represents a price opportunity (alert)"""

    def __init__(self, sku: str, competitor_url: str, competitor_price: float,
                 our_cost_price: float, opportunity_type: str, margin_pct: float):
        self.sku = sku
        self.competitor_url = competitor_url
        self.competitor_price = competitor_price
        self.our_cost_price = our_cost_price
        self.opportunity_type = opportunity_type  # "DUMPING" or "OUR_ADVANTAGE"
        self.margin_pct = margin_pct
        self.timestamp = datetime.utcnow()

    def __repr__(self):
        return (f"<PriceOpportunity(sku={self.sku}, type={self.opportunity_type}, "
                f"margin={self.margin_pct:.1f}%, price={self.competitor_price})>")

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage"""
        return {
            'sku': self.sku,
            'competitor_url': self.competitor_url,
            'competitor_price': self.competitor_price,
            'our_cost_price': self.our_cost_price,
            'opportunity_type': self.opportunity_type,
            'margin_pct': self.margin_pct,
            'timestamp': self.timestamp
        }

    def format_message(self) -> str:
        """Format opportunity as human-readable message"""
        if self.opportunity_type == "DUMPING":
            return (f"[DUMPING ALERT] {self.sku}\n"
                    f"Competitor price: {self.competitor_price:.0f}\n"
                    f"Our cost: {self.our_cost_price:.0f}\n"
                    f"Margin: {self.margin_pct:.1f}%\n"
                    f"Source: {self.competitor_url}")
        else:
            return (f"[ADVANTAGE] {self.sku}\n"
                    f"Competitor price: {self.competitor_price:.0f}\n"
                    f"Our cost: {self.our_cost_price:.0f}\n"
                    f"Margin: {self.margin_pct:.1f}%\n"
                    f"Source: {self.competitor_url}")


def calc_price_strategy(cost_price: float, margin_pct: float) -> float:
    """Calculate target selling price based on cost and desired margin

    Args:
        cost_price: Our cost price
        margin_pct: Desired margin percentage

    Returns:
        Target selling price
    """
    if cost_price <= 0:
        logger.warning(f"Invalid cost price: {cost_price}")
        return 0.0

    target_price = cost_price * (1 + margin_pct / 100)
    logger.debug(f"Calculated target price: {target_price} (cost={cost_price}, margin={margin_pct}%)")
    return target_price


def analyze_competitor_price(competitor_price: float, our_cost_price: float) -> dict:
    """Analyze competitor price relative to our cost

    Args:
        competitor_price: Competitor's selling price
        our_cost_price: Our cost price

    Returns:
        Dictionary with analysis:
            {
                'margin_pct': float,           # Margin percentage
                'is_dumping': bool,            # Is dumping (< 50% margin)
                'is_advantage': bool,          # Is our advantage (> 50% margin)
                'dumping_threshold': float,    # Dumping price threshold (1.5 * cost)
                'advantage_threshold': float   # Advantage threshold (1.5 * cost)
            }
    """
    if our_cost_price <= 0:
        logger.warning(f"Invalid cost price: {our_cost_price}")
        return {
            'margin_pct': 0.0,
            'is_dumping': False,
            'is_advantage': False,
            'dumping_threshold': 0.0,
            'advantage_threshold': 0.0
        }

    # Calculate margin percentage
    margin_pct = ((competitor_price - our_cost_price) / our_cost_price) * 100

    # Define thresholds
    dumping_threshold = our_cost_price * 1.5    # < 1.5x cost = dumping
    advantage_threshold = our_cost_price * 1.5   # > 1.5x cost = our advantage

    is_dumping = competitor_price < dumping_threshold
    is_advantage = competitor_price > advantage_threshold

    logger.debug(f"Analyzed price {competitor_price}: margin={margin_pct:.1f}%, "
                 f"dumping={is_dumping}, advantage={is_advantage}")

    return {
        'margin_pct': margin_pct,
        'is_dumping': is_dumping,
        'is_advantage': is_advantage,
        'dumping_threshold': dumping_threshold,
        'advantage_threshold': advantage_threshold
    }


def find_opportunities(our_skus: Dict[str, float], scraped_prices: List[dict],
                      config: Dict) -> List[PriceOpportunity]:
    """Find price opportunities by comparing competitor prices with ours

    Args:
        our_skus: Dictionary {model_id: cost_price}
        scraped_prices: List of dicts from scraper with keys:
            {
                'sku': model_id,
                'price': competitor_price,
                'url': source_url,
                'success': bool
            }
        config: Configuration dict with:
            - TARGET_MARGIN_PCT: target margin
            - MIN_MARGIN_PCT: minimum acceptable margin

    Returns:
        List of PriceOpportunity objects
    """
    opportunities = []
    target_margin = config.get('TARGET_MARGIN_PCT', 20.0)
    min_margin = config.get('MIN_MARGIN_PCT', 15.0)

    logger.info(f"Analyzing {len(scraped_prices)} competitor prices")

    for competitor_data in scraped_prices:
        if not competitor_data.get('success'):
            logger.debug(f"Skipping unsuccessful scrape: {competitor_data}")
            continue

        sku = competitor_data.get('sku')
        competitor_price = competitor_data.get('price', 0.0)
        competitor_url = competitor_data.get('url', '')

        if not sku or sku not in our_skus:
            logger.debug(f"SKU {sku} not in our catalog")
            continue

        our_cost_price = our_skus[sku]

        # Analyze the competitor price
        analysis = analyze_competitor_price(competitor_price, our_cost_price)
        margin_pct = analysis['margin_pct']

        # Determine opportunity type
        if analysis['is_dumping']:
            logger.warning(f"DUMPING detected: {sku} at {competitor_price} "
                          f"(cost={our_cost_price}, margin={margin_pct:.1f}%)")
            opportunity = PriceOpportunity(
                sku=sku,
                competitor_url=competitor_url,
                competitor_price=competitor_price,
                our_cost_price=our_cost_price,
                opportunity_type="DUMPING",
                margin_pct=margin_pct
            )
            opportunities.append(opportunity)

        elif analysis['is_advantage']:
            logger.info(f"ADVANTAGE: {sku} at {competitor_price} "
                       f"(cost={our_cost_price}, margin={margin_pct:.1f}%)")
            opportunity = PriceOpportunity(
                sku=sku,
                competitor_url=competitor_url,
                competitor_price=competitor_price,
                our_cost_price=our_cost_price,
                opportunity_type="OUR_ADVANTAGE",
                margin_pct=margin_pct
            )
            opportunities.append(opportunity)

        # Log if margin is below minimum
        if margin_pct < min_margin:
            logger.warning(f"Margin below minimum: {sku} ({margin_pct:.1f}% < {min_margin}%)")

    logger.info(f"Found {len(opportunities)} opportunities")
    return opportunities


def calculate_price_delta(competitor_price: float, our_target_price: float) -> float:
    """Calculate price difference percentage

    Args:
        competitor_price: Competitor's price
        our_target_price: Our target selling price

    Returns:
        Price delta as percentage
    """
    if our_target_price <= 0:
        return 0.0

    delta = ((competitor_price - our_target_price) / our_target_price) * 100
    return delta


def should_adjust_price(competitor_price: float, our_target_price: float,
                       delta_threshold_pct: float = 3.0) -> tuple:
    """Determine if we should adjust our price

    Args:
        competitor_price: Competitor's price
        our_target_price: Our target price
        delta_threshold_pct: Threshold delta percentage for action

    Returns:
        Tuple (should_adjust: bool, direction: str, delta_pct: float)
            direction: 'UP', 'DOWN', or 'HOLD'
    """
    delta = calculate_price_delta(competitor_price, our_target_price)

    if abs(delta) < delta_threshold_pct:
        return False, 'HOLD', delta

    if delta > 0:
        return True, 'DOWN', delta  # Competitor is more expensive, we should lower
    else:
        return True, 'UP', delta    # Competitor is cheaper, we should raise


def rank_opportunities(opportunities: List[PriceOpportunity],
                      sort_by: str = 'margin_pct') -> List[PriceOpportunity]:
    """Rank opportunities by severity

    Args:
        opportunities: List of PriceOpportunity objects
        sort_by: Sort field ('margin_pct' or 'timestamp')

    Returns:
        Sorted list of opportunities
    """
    if sort_by == 'margin_pct':
        return sorted(opportunities, key=lambda x: x.margin_pct)
    elif sort_by == 'timestamp':
        return sorted(opportunities, key=lambda x: x.timestamp)
    else:
        return opportunities
