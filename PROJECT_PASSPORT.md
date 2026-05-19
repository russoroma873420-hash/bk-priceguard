# 🧊 BK-PriceGuard
**Цель:** Автономный мониторинг цен конкурентов + защита маржи (Zero-Loss)  
**Стек:** Python 3.14, Playwright, SQLAlchemy, SQLite, Telegram Bot API, Rich  
**Запуск:** `python -m src.main --once` (или каждый час через Task Scheduler)  
**Конфиг:** `config/settings.json` (SKU, cost_price, selectors, proxy, margins)  
**Логика:** Если competitor_price < cost × 1.5 → `DUMPING`. Если > → `OUR_ADVANTAGE`.  
**Алерты:** В Telegram (chat_id + token). Mock: `MOCK_TELEGRAM=true`  
**Известные фиксы:** Unicode → `try/except` для `£/€`; DNS → `wait_for_selector 10s`; прокси → в `settings.json.PROXY`  
**Куда интегрировать:** 1С (CSV/ODATA), Битрикс24 (Webhook), Power BI (CSV connector)  
**Архив данных:** `data/price_monitor.db` → экспорт в CSV через `scripts/export_report.py`
