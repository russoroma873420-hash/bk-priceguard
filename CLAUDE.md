# BK-PriceGuard + AirBond — рабочие заметки для Claude Code

## Структура репозитория
- `src/` — BK-PriceGuard, Python-бэкенд мониторинга цен (основной проект)
- `AirBond/` — лендинг (HTML/CSS/JS, GitHub Pages)
- `config/` — конфиги (settings.json в gitignore, использовать settings.example.json)
- `data/` — SQLite + логи (в gitignore)

## Стек
- BK-PriceGuard: Python 3, requests, BeautifulSoup, Playwright, SQLAlchemy, python-telegram-bot, SQLite
- AirBond: HTML5, TailwindCSS (CDN), Vanilla JS, GitHub Pages

## Статус
- Бэкенд BK-PriceGuard: готов на 90%. Не хватает config/settings.json с TELEGRAM_TOKEN + TELEGRAM_CHAT_ID
- AirBond: сайт собран, ждёт настройки DNS на reg.ru для домена airbond.ru
- Тесты: папка tests/ пустая
- Текущая фаза: настройка DNS для airbond.ru → зелёный замок → Фаза 2 (портфолио, ROI-график)

## Стиль ответов
- Без вступлений ("Отлично! Сейчас разберёмся..."), сразу суть
- В конце ответа — одно конкретное действие для пользователя
- Кратко, по делу

## Команды экономии контекста
- /clear — начать с чистого листа после выполненной задачи
- /compact — сжать длинный чат вручную, не ждать автосжатия
- @файл — указывать конкретный файл (например @src/main.py)
- Plan Mode — для крупных изменений сначала план, потом код

## Правила работы
- Перед коммитом всегда показывать diff
- git commit/push требуют подтверждения (см. .claude/settings.json)
- Чтение файлов и git status/diff/log — без подтверждения
