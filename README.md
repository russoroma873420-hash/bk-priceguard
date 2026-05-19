# BK-PriceGuard

**Система мониторинга цен и защиты маржи для кондиционеров**

BK-PriceGuard — автоматизированная система, которая отслеживает цены конкурентов
на кондиционеры, вычисляет разницу с нашими ценами и отправляет уведомления в
Telegram при выявлении угрозы маржи (дампинг) или возможности увеличения наценки.

## 📋 Возможности

- ✅ **Реальный парсинг** сайтов (requests + BeautifulSoup, без mock-fallback в production)
- ✅ Поддержка нескольких CSS-селекторов (`<span>`, `<div>`, `<h3>`) с автоматическим fallback
- ✅ Обнаружение Cloudflare / антибот-защиты
- ✅ Локальное хранилище данных (SQLite + SQLAlchemy)
- ✅ Уведомления в Telegram (с MOCK-режимом для разработки)
- ✅ Аналитика цен и экспорт в CSV
- ✅ Конфигурируемые пороги маржи
- ✅ Логирование всех операций
- ✅ Поддержка Windows Task Scheduler (запуск каждый час)

---

## 🚀 Установка

### Требования
- Python 3.9+
- pip
- Доступ в интернет

### Шаги установки

```bash
# 1. Перейти в директорию проекта
cd D:\bk-priceguard

# 2. Создать виртуальное окружение (рекомендуется)
python -m venv venv
venv\Scripts\activate

# 3. Установить зависимости
pip install -r requirements.txt

# 4. Проверить конфигурацию
python scripts/validate_config.py

# 5. Инициализировать базу данных
python scripts/setup.py
```

---

## ⚙️ Настройка Telegram

### Шаг 1: Получить токен бота через @BotFather

1. Откройте Telegram и найдите бота **@BotFather**
2. Отправьте команду `/newbot`
3. Введите имя для бота (например, `BK PriceGuard Bot`)
4. Введите уникальный username (должен заканчиваться на `bot`, например, `bk_priceguard_bot`)
5. **@BotFather пришлёт вам токен** вида:
   ```
   7234567890:AAEbcDeFgHiJkLmNoPqRsTuVwXyZ1234567
   ```
6. Скопируйте этот токен и вставьте в `config/settings.json` в поле `TELEGRAM_TOKEN`

### Шаг 2: Узнать свой chat_id

**Способ 1: через @userinfobot**
1. Найдите в Telegram бота **@userinfobot**
2. Отправьте ему `/start`
3. Он пришлёт ваш числовой `id` (например, `123456789`)

**Способ 2: через своего бота**
1. Запустите своего бота (нажмите Start)
2. Отправьте ему любое сообщение
3. Откройте в браузере:
   ```
   https://api.telegram.org/bot<ВАШ_ТОКЕН>/getUpdates
   ```
   Замените `<ВАШ_ТОКЕН>` на токен из шага 1.
4. В JSON-ответе найдите `"chat":{"id": 123456789, ...}` — это ваш chat_id

**Для группового чата:**
1. Добавьте бота в группу
2. Отправьте сообщение в группу
3. Откройте тот же URL `getUpdates`
4. Найдите `"chat":{"id": -100123456789, ...}` (отрицательное число для групп)

### Шаг 3: Заполнить конфиг

Откройте `config/settings.json` и замените заглушки:

```json
{
  "TELEGRAM_TOKEN": "7234567890:AAEbcDeFgHiJkLmNoPqRsTuVwXyZ1234567",
  "TELEGRAM_CHAT_ID": "123456789",
  "MOCK_TELEGRAM": false,
  ...
}
```

> ⚠️ **Важно:** Пока идёт разработка, оставьте `"MOCK_TELEGRAM": true` —
> бот будет выводить `[MOCK_SEND] ...` в консоль вместо реальной отправки,
> чтобы не спамить в чат. Когда будете готовы к боевой работе,
> установите `false`.

### Шаг 4: Проверить отправку

```bash
python -c "from src.bot import send_telegram; from src.config_loader import load_settings; c=load_settings(); print(send_telegram(c['TELEGRAM_TOKEN'], str(c['TELEGRAM_CHAT_ID']), 'Test message from BK-PriceGuard'))"
```

Если вернёт `True` и придёт сообщение в Telegram — настройка успешна.

---

## 🖥️ Настройка Windows Task Scheduler (запуск каждый час)

Для того чтобы скрипт запускался автоматически каждый час, используется
встроенный **Планировщик задач Windows (Task Scheduler)**.

### Способ 1: Через GUI (рекомендуется)

1. **Откройте Task Scheduler**
   - Нажмите `Win + R`, введите `taskschd.msc`, нажмите Enter
   - Или: Пуск → "Планировщик заданий"

2. **Создайте задачу**
   - В правой панели: **Создать задачу...** (Create Task — не "Create Basic Task")

3. **Вкладка "Общие" (General)**
   - **Имя:** `BK-PriceGuard`
   - **Описание:** `Мониторинг цен кондиционеров`
   - ✅ **Выполнять для всех пользователей** (Run whether user is logged on or not)
   - ✅ **Выполнить с наивысшими правами** (Run with highest privileges)
   - **Настроить для:** Windows 10/11

4. **Вкладка "Триггеры" (Triggers)**
   - Нажмите **Создать...**
   - **Начать задачу:** По расписанию (On a schedule)
   - **Параметры:** Ежедневно (Daily), время старта: `09:00:00`
   - ✅ **Повторять задачу каждые:** `1 час`
   - **В течение:** `1 день` (или `Неопределённо` — Indefinitely)
   - ✅ Включено
   - OK

5. **Вкладка "Действия" (Actions)**
   - Нажмите **Создать...**
   - **Действие:** Запуск программы
   - **Программа или сценарий:**
     ```
     C:\Path\To\Python\python.exe
     ```
     (узнать путь: `where python` в cmd)
   - **Добавить аргументы (необязательно):**
     ```
     -m src.main --once
     ```
   - **Рабочая папка (необязательно):**
     ```
     D:\bk-priceguard
     ```
   - OK

6. **Вкладка "Условия" (Conditions)**
   - Снимите галку **Запускать только при подключении к сети переменного тока**
     (если работаете на ноутбуке)

7. **Вкладка "Параметры" (Settings)**
   - ✅ **Выполнить задачу немедленно, если плановый запуск был пропущен**
   - **Если задача уже выполняется:** Не запускать новую копию
   - OK

8. **Введите пароль** учётной записи (нужно для "Run whether user is logged on or not")

9. **Тестирование:**
   - Правый клик по задаче `BK-PriceGuard` → **Выполнить**
   - Проверьте логи: `data/price_monitor.log`

### Способ 2: Через CLI (PowerShell)

```powershell
# Запустите PowerShell от имени администратора

$action = New-ScheduledTaskAction `
    -Execute "C:\Path\To\Python\python.exe" `
    -Argument "-m src.main --once" `
    -WorkingDirectory "D:\bk-priceguard"

$trigger = New-ScheduledTaskTrigger `
    -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Hours 1) `
    -RepetitionDuration (New-TimeSpan -Days 365)

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName "BK-PriceGuard" `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Мониторинг цен кондиционеров каждый час" `
    -RunLevel Highest
```

### Способ 3: Через .bat файл

Создайте файл `D:\bk-priceguard\run_hourly.bat`:

```bat
@echo off
cd /d D:\bk-priceguard
python -m src.main --once
```

Затем в Task Scheduler вместо `python.exe` укажите этот `.bat` файл.

### Проверка работы

После настройки задачи:
- Логи: `D:\bk-priceguard\data\price_monitor.log`
- БД с историей цен: `D:\bk-priceguard\data\price_monitor.db`
- История запусков задачи: Task Scheduler → правый клик по задаче → **История**

---

## 📁 Структура проекта

```
bk-priceguard/
├── src/                       # Основной код
│   ├── __init__.py
│   ├── main.py                # Оркестратор (production)
│   ├── real_scraper.py        # Реальный парсер (no mock)
│   ├── scraper.py             # Старый парсер с mock (для тестов)
│   ├── engine.py              # Анализ цен и маржи
│   ├── bot.py                 # Telegram уведомления
│   ├── database.py            # SQLAlchemy модели
│   └── config_loader.py       # Загрузка конфига
├── tests/                     # Тесты
├── scripts/
│   ├── setup.py               # Инициализация
│   ├── validate_config.py     # Проверка конфига
│   ├── check_db.py            # Статус БД
│   ├── export_report.py       # CSV отчёт
│   └── test_functionality.py  # Тесты модулей
├── config/
│   └── settings.json          # Конфигурация
├── data/
│   ├── price_monitor.db       # SQLite БД
│   └── price_monitor.log      # Логи
├── requirements.txt
└── README.md
```

---

## ⚙️ Конфигурация (config/settings.json)

| Поле | Тип | Описание |
|------|-----|----------|
| `TELEGRAM_TOKEN` | string | Токен бота от @BotFather |
| `TELEGRAM_CHAT_ID` | string | ID чата для уведомлений |
| `TARGET_MARGIN_PCT` | float | Целевая маржа в % (default: 20) |
| `MIN_MARGIN_PCT` | float | Минимальная маржа в % (default: 15) |
| `SLEEP_INTERVAL` | int | Интервал между проверками в секундах |
| `PRODUCTION_MODE` | bool | Production режим (default: true) |
| `MOCK_TELEGRAM` | bool | Не отправлять реально, выводить `[MOCK_SEND]` |
| `MONITORS` | list | Список сайтов с CSS селекторами |
| `OUR_PRICES` | dict | Наши цены закупки `{SKU: price}` |
| `SCRAPER.REQUEST_TIMEOUT` | int | Таймаут HTTP запроса (сек) |
| `SCRAPER.RETRY_COUNT` | int | Количество повторов при ошибке |
| `SCRAPER.RETRY_DELAY` | int | Задержка между повторами (сек) |

### Структура монитора

```json
{
  "name": "Название источника",
  "url": "https://...",
  "sku": "MODEL_001",
  "selectors": {
    "price": "span.price-current",
    "price_alt": "div.product-price",
    "price_alt2": "h3.price-value",
    "stock": "div.availability",
    "product_name": "h1.product-title"
  },
  "headers": {
    "User-Agent": "Mozilla/5.0 ...",
    "Accept-Language": "ru-RU,ru;q=0.9"
  }
}
```

Парсер пробует селекторы по порядку: `price` → `price_alt` → `price_alt2`,
что позволяет одной конфигурацией работать с разной вёрсткой (span / div / h3).

---

## 🚀 Запуск

### Один цикл (для Task Scheduler)

```bash
python -m src.main --once
```

### Непрерывный мониторинг (с интервалом из конфига)

```bash
python -m src.main
```

Остановка: `Ctrl+C` (graceful shutdown с сохранением статистики).

### Утилиты

```bash
# Валидация конфигурации
python scripts/validate_config.py

# Статус БД
python scripts/check_db.py

# Экспорт отчёта в CSV
python scripts/export_report.py --hours 24

# Полный тест-сьют (модули)
python scripts/test_functionality.py
```

---

## 🔍 Логика обнаружения

### Дампинг (DUMPING_ALERT)
Срабатывает, если `competitor_price < cost_price * 1.5`
(маржа конкурента < 50%) — конкурент демпингует.

### Наша выгода (OUR_ADVANTAGE)
Срабатывает, если `competitor_price > cost_price * 1.5`
(маржа конкурента > 50%) — можем поднять свою цену.

### Delta Alert
Срабатывает, если разница нашей `target_price` и `competitor_price` > **3%**.
Используется для тонкой настройки цен.

---

## 🐞 Что делать, если сайт блокирует парсер

При обнаружении Cloudflare/антибот-защиты `real_scraper.py` возвращает
ошибку `CloudflareBlockedError` (без mock-fallback). Что можно сделать:

1. **Проверить User-Agent** — обновить на свежий браузерный
2. **Добавить дополнительные заголовки** в `headers` монитора
3. **Использовать Playwright** для рендеринга JavaScript (для будущих версий)
4. **Использовать прокси-сервис** (для версии 2.0)
5. **Снизить частоту запросов** — увеличить `SLEEP_INTERVAL`

В логе вы увидите:
```
[CLOUDFLARE_BLOCKED] Anti-bot protection detected: 'cloudflare' (url=...)
```

---

## 📊 Просмотр истории цен

```bash
# Текущая БД
python scripts/check_db.py

# Экспорт в CSV
python scripts/export_report.py --hours 168  # за неделю
```

CSV-отчёт сохраняется в `data/reports/price_report_YYYYMMDD_HHMMSS.csv`.

---

## 📞 Поддержка

При проблемах:
1. Проверьте `data/price_monitor.log`
2. Запустите `python scripts/validate_config.py`
3. Проверьте интернет-соединение и доступность сайтов

## 📄 Лицензия

MIT License
