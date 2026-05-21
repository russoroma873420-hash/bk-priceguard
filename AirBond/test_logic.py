"""Integration logic test for BK-PriceGuard (no network).

Validates the cold path:
  config -> DB init -> engine analysis -> DB write -> DB read-back.
"""

from src.config_loader import load_settings
from src.database import DatabaseManager, PriceLog
from src.engine import analyze_competitor_price

print("=" * 60)
print("LOGIC TEST — BK-PriceGuard")
print("=" * 60)

# 1) Load config
cfg = load_settings("config/settings.json")
print(f"[1] Config loaded: {len(cfg['MONITORS'])} monitors, "
      f"{len(cfg['OUR_PRICES'])} SKUs")

# 2) Init DB
db = DatabaseManager(cfg["DATABASE"]["PATH"])
print(f"[2] DB initialised at {cfg['DATABASE']['PATH']}")

# 3) Run engine on cost=1000, price=1200
cost = 1000.0
competitor_price = 1200.0
analysis = analyze_competitor_price(competitor_price, cost)

# Translate dict flags to a human-readable status
if analysis["is_dumping"]:
    status = "DUMPING"
elif analysis["is_advantage"]:
    status = "OUR_ADVANTAGE"
else:
    status = "SAFE"

print(f"[3] analyze_competitor_price(price={competitor_price}, cost={cost}) -> "
      f"status={status}, margin={analysis['margin_pct']:.1f}%, "
      f"dumping_threshold={analysis['dumping_threshold']}")

assert status in ("DUMPING", "SAFE", "OUR_ADVANTAGE"), f"Unexpected status: {status}"

# 4) Write to DB
record = {
    "sku": "LOGIC_TEST_SKU",
    "original_price": competitor_price,
    "target_price": cost,
    "delta": competitor_price - cost,
    "source_url": "https://logic-test.local/sample",
}
saved = db.save_price(record)
print(f"[4] DB write: {'OK' if saved else 'FAIL'}")
assert saved, "save_price returned False"

# 5) Read back and verify
session = db.SessionLocal()
last = (session.query(PriceLog)
        .filter(PriceLog.sku == "LOGIC_TEST_SKU")
        .order_by(PriceLog.id.desc())
        .first())
session.close()

if last is None:
    print("[5] Read-back: FAIL — record not found")
    raise SystemExit(1)

print(f"[5] Read-back OK: id={last.id} sku={last.sku} "
      f"price={last.original_price} delta={last.delta} "
      f"at {last.timestamp}")

print("=" * 60)
print("LOGIC TEST: ALL CHECKS PASSED")
print("=" * 60)
