# BK-PriceGuard

**Система мониторинга цен и защиты маржи для кондиционеров**

BK-PriceGuard — это автоматизированная система, которая отслеживает цены конкурентов на кондиционеры, вычисляет разницу с нашими ценами и отправляет уведомления в Telegram при выявлении угрозы маржи.

## 📋 Возможности

- ✅ Парсинг цен с множественных источников (Playwright + BeautifulSoup)
- ✅ Локальное хранилище данных (SQLite + SQLAlchemy)
- ✅ Уведомления в Telegram при срабатывании условий
- ✅ Аналитика цен и экспорт в CSV
- ✅ Конфигурируемые пороги маржи
- ✅ Логирование всех операций

## 🚀 Установка

### Требования
- Python 3.9+
- pip

### Шаги установки

1. **Клонируйте репозиторий**
   ```bash
   cd bk-priceguard
   ```

2. **Создайте виртуальное окружение**
   ```bash
   python -m venv venv
   
   # Активация на Windows
   venv\Scripts\activate
   
   # Активация на Linux/Mac
   source venv/bin/activate
   ```

3. **Установите зависимости**
   ```bash
   pip install -r requirements.txt
   ```

4. **Инициализируйте Playwright**
   ```bash
   playwright install chromium
   ```

5. **Настройте конфигурацию**
   ```bash
   # Отредактируйте config/settings.json
   # Добавьте TELEGRAM_TOKEN и TELEGRAM_CHAT_ID
   ```

## ⚙️ Конфигурация

### config/settings.json

```json
{
  "TELEGRAM_TOKEN": "YOUR_BOT_TOKEN_HERE",
  "TELEGRAM_CHAT_ID": "YOUR_CHAT_ID_HERE",
  "TARGET_MARGIN_PCT": 20.0,
  "MIN_MARGIN_PCT": 15.0,
  "SLEEP_INTERVAL": 300,
  "MONITORS": [ ... ],
  "OUR_PRICES": { ... }
}
```

**Основные параметры:**
- `TELEGRAM_TOKEN` — токен бота Telegram
- `TELEGRAM_CHAT_ID` — ID чата для уведомлений
- `TARGET_MARGIN_PCT` — целевая маржа (%)
- `MIN_MARGIN_PCT` — минимальная маржа (%)
- `SLEEP_INTERVAL` — интервал между проверками (сек)
- `MONITORS` — список сайтов для парсинга
- `OUR_PRICES` — наши цены закупки по моделям

### Переменные окружения

Можно переопределить параметры через переменные окружения:

```bash
export TELEGRAM_TOKEN="your_token"
export TELEGRAM_CHAT_ID="123456"
export SLEEP_INTERVAL=600
export TARGET_MARGIN_PCT=25
```

## 📁 Структура проекта

```
bk-priceguard/
├── src/                    # Основной код приложения
│   ├── __init__.py
│   ├── config_loader.py    # Загрузка и валидация конфигурации
│   ├── database.py         # SQLAlchemy модели и операции БД
│   ├── parser.py           # Парсеры для сайтов (будет добавлено)
│   ├── telegram.py         # Отправка уведомлений (будет добавлено)
│   └── monitor.py          # Основная логика мониторинга (будет добавлено)
├── tests/                  # Тесты
│   └── __init__.py
├── config/                 # Конфигурация
│   └── settings.json
├── data/                   # Данные (БД, логи)
│   ├── price_monitor.db
│   └── price_monitor.log
├── scripts/                # Скрипты для деплоя и запуска
│   ├── setup.sh
│   ├── run.sh
│   └── export_report.py
├── requirements.txt        # Python зависимости
├── .gitignore
└── README.md
```

## 🔧 Использование

### Инициализация БД

```python
from src.database import DatabaseManager

db = DatabaseManager()
```

### Загрузка конфигурации

```python
from src.config_loader import load_settings

config = load_settings("config/settings.json")
print(config['TARGET_MARGIN_PCT'])
```

### Сохранение цены

```python
record = {
    'sku': 'MODEL_001',
    'original_price': 5500,
    'target_price': 5000,
    'delta': 500,
    'source_url': 'https://example.com/product'
}

db.save_price(record)
```

### Получение непроверенных оповещений

```python
alerts = db.get_unsaved_alerts(hour_limit=1)
for alert in alerts:
    print(f"{alert['sku']}: {alert['original_price']}")
```

### Экспорт в CSV

```python
db.export_to_csv('reports/prices_24h.csv', hours=24)
```

## 📊 Примеры

### Пример 1: Проверка цен

```python
from src.config_loader import load_settings
from src.database import DatabaseManager

# Загрузить конфиг
config = load_settings()

# Получить наши цены
our_price = config['OUR_PRICES'].get('MODEL_001', 5000)
competitor_price = 5500

# Вычислить маржу
delta = competitor_price - our_price
margin_pct = (delta / our_price) * 100

# Сохранить в БД
db = DatabaseManager()
db.save_price({
    'sku': 'MODEL_001',
    'original_price': competitor_price,
    'target_price': our_price,
    'delta': delta,
    'source_url': 'https://example.com'
})
```

## 🧪 Тестирование

```bash
# Проверить валидность конфигурации
python -c "from src.config_loader import load_settings; load_settings()"

# Проверить БД
python -c "from src.database import DatabaseManager; db = DatabaseManager(); print('DB OK')"
```

## 📝 Логирование

Все операции логируются в `data/price_monitor.log`

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 🔐 Безопасность

- **Не коммитьте** `config/secrets.json` или `TELEGRAM_TOKEN`
- Используйте переменные окружения для чувствительных данных
- Регулярно удаляйте старые данные: `db.cleanup_old_records(days=30)`

## 📞 Поддержка

Для вопросов и предложений используйте Issues в репозитории.

## 📄 Лицензия

MIT License
