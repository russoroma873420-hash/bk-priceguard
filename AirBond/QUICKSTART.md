# BK-PriceGuard Quick Start Guide

## ⚡ Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Инициализация проекта

```bash
# Проверить конфигурацию
python scripts/validate_config.py

# Инициализировать БД
python scripts/setup.py
```

### 3. Настройка Telegram

1. Создайте бота в Telegram через [@BotFather](https://t.me/BotFather)
2. Получите `TELEGRAM_TOKEN`
3. Отправьте сообщение боту и получите `TELEGRAM_CHAT_ID`
4. Отредактируйте `config/settings.json`:

```json
{
  "TELEGRAM_TOKEN": "ваш_токен_здесь",
  "TELEGRAM_CHAT_ID": "ваш_id_здесь",
  ...
}
```

### 4. Добавление мониторов сайтов

Обновите массив `MONITORS` в `config/settings.json`:

```json
"MONITORS": [
  {
    "name": "Название магазина",
    "url": "https://shop.example.com/products",
    "selectors": {
      "product_name": "h1.product-title",
      "price": "span.price",
      "model_id": "div.model-id"
    }
  }
]
```

### 5. Обновление цен

Обновите `OUR_PRICES` с вашими ценами закупки:

```json
"OUR_PRICES": {
  "MODEL_001": 5000,
  "MODEL_002": 7500,
  "AC_PRO_3000": 9500
}
```

## 📊 Использование

### Проверить статус БД

```bash
python scripts/check_db.py
```

### Экспортировать отчёт

```bash
# Последние 24 часа
python scripts/export_report.py

# Последние 48 часов в конкретную папку
python scripts/export_report.py --hours 48 --output ./reports
```

### Работа с БД в Python

```python
from src.database import DatabaseManager
from src.config_loader import load_settings

# Загрузить конфиг
config = load_settings()

# Инициализировать БД
db = DatabaseManager()

# Сохранить цену
db.save_price({
    'sku': 'MODEL_001',
    'original_price': 5500,
    'target_price': 5000,
    'delta': 500,
    'source_url': 'https://example.com'
})

# Получить непроверенные оповещения (последний час)
alerts = db.get_unsaved_alerts(hour_limit=1)
print(f"Непроверенных оповещений: {len(alerts)}")

# Получить статистику по модели
stats = db.get_price_stats('MODEL_001', hours=24)
print(f"Min: {stats['min_price']}, Max: {stats['max_price']}, Avg: {stats['avg_price']}")

# Экспортировать в CSV
db.export_to_csv('report.csv', hours=24)

# Очистить старые данные
deleted = db.cleanup_old_records(days=30)
print(f"Удалено {deleted} старых записей")
```

## 🔧 Переменные окружения

Можно переопределить параметры через env variables:

```bash
export TELEGRAM_TOKEN=your_token
export TELEGRAM_CHAT_ID=123456
export SLEEP_INTERVAL=600
export TARGET_MARGIN_PCT=25
export MIN_MARGIN_PCT=18
```

## 📁 Структура данных

### config/settings.json
- `TELEGRAM_TOKEN` — токен бота
- `TELEGRAM_CHAT_ID` — ID чата
- `TARGET_MARGIN_PCT` — целевая маржа (%)
- `MIN_MARGIN_PCT` — минимальная маржа (%)
- `SLEEP_INTERVAL` — интервал проверки (сек)
- `MONITORS` — список сайтов
- `OUR_PRICES` — наши цены

### data/price_monitor.db
SQLite база данных с таблицей `price_logs`:
- `id` — PK
- `timestamp` — когда записано
- `sku` — модель товара
- `original_price` — цена конкурента
- `target_price` — наша цена
- `delta` — разница
- `source_url` — откуда взято
- `alerted` — отправлено ли уведомление

## 🧪 Примеры скриптов

### Пример 1: Парсинг и сохранение

```python
from src.database import DatabaseManager
from src.config_loader import load_settings

config = load_settings()
db = DatabaseManager()

# Ваш код парсинга здесь
competitor_price = 5500
model_id = 'MODEL_001'

if model_id in config['OUR_PRICES']:
    our_price = config['OUR_PRICES'][model_id]
    delta = competitor_price - our_price
    
    db.save_price({
        'sku': model_id,
        'original_price': competitor_price,
        'target_price': our_price,
        'delta': delta,
        'source_url': 'https://...'
    })
```

### Пример 2: Проверка оповещений

```python
from src.database import DatabaseManager

db = DatabaseManager()

# Получить непроверенные оповещения за последний час
alerts = db.get_unsaved_alerts(hour_limit=1)

alert_ids = []
for alert in alerts:
    margin_pct = (alert['delta'] / alert['target_price']) * 100
    
    if margin_pct < 15:  # Маржа ниже 15%
        print(f"ALERT: {alert['sku']} - маржа {margin_pct:.1f}%")
        alert_ids.append(alert['id'])

# Отметить как отправленные
if alert_ids:
    db.mark_alerts_sent(alert_ids)
```

## ❓ FAQ

**Q: Как добавить новый монитор?**
A: Добавьте объект в массив `MONITORS` в `config/settings.json` с name, url и selectors.

**Q: Как найти CSS селекторы для сайта?**
A: Откройте DevTools (F12), используйте Inspect Element (Ctrl+Shift+I), чтобы найти нужные элементы.

**Q: Что означает "delta"?**
A: Разница между ценой конкурента и нашей ценой. Позитивная = конкурент дороже.

**Q: Как удалить старые данные?**
A: Используйте `db.cleanup_old_records(days=30)` для удаления данных старше 30 дней.

**Q: Может ли работать на VPS/облаке?**
A: Да! Просто убедитесь, что установлены все зависимости и есть доступ в интернет.

## 📞 Помощь

- Проверьте логи: `cat data/price_monitor.log`
- Запустите валидацию: `python scripts/validate_config.py`
- Проверьте БД: `python scripts/check_db.py`
