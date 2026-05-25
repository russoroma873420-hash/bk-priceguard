# BK-PriceGuard + AirBond — рабочие заметки для Claude Code

## Структура репозитория
В корне только: `AirBond/`, `CLAUDE.md`, `.github/`, `.gitignore`. Корневого `src/`/`config/`/`data/` нет.
- `AirBond/website-v2/` — лендинг AirBond (деплоится на GitHub Pages)
- `AirBond/src/` — Python-бэкенд BK-PriceGuard (main.py, scraper.py, bot.py, engine.py, database.py, ...)
- `AirBond/config/` — конфиги (`settings.json` в gitignore, см. `settings.example.json`)
- `AirBond/website/` — v1 лендинга, архив, НЕ трогать

## Роль при работе с AirBond
Когда задача про `AirBond/website-v2/` или сайт airbond.ru — ты Senior Frontend / UX-дизайнер. Делаешь быстрые, конверсионные лендинги.

### Реальный стек AirBond (НЕ Tailwind!)
- Чистый HTML5 + **своя `css/style.css`** (эко-минимализм, зелёная палитра) + **Vanilla JS**
- Шрифты: Google Fonts — Playfair Display (заголовки) + Inter (текст)
- Tailwind / FontAwesome НЕ используются
- Анимации: Intersection Observer (появление при скролле), CSS hover

### Архитектура AirBond
`AirBond/website-v2/` с отдельными файлами:
- `index.html` (17 секций контента)
- `css/style.css` (все стили)
- `js/main.js` (анимации, меню, виртуальный дом, FAQ), `js/calculator.js` (квиз, Telegram-лиды, модалка)
- `privacy.html` (ФЗ-152), `CNAME` (`airbond.ru`)
- Фото: реальные WebP — `ComfyUI_00225_.webp` (77 КБ), `ComfyUI_00226_.webp` (89 КБ). Тяжёлые `.png` — не трогать.
- Лид-форма шлёт заявку напрямую из JS в Telegram-бот (без бэкенда)

## Роль при работе с BK-PriceGuard
Когда задача про `AirBond/src/` или Python — ты backend-разработчик. Стек: Python 3, requests, BeautifulSoup, Playwright, SQLAlchemy, python-telegram-bot, SQLite.

## Владелец и реквизиты

| Параметр | Значение |
|----------|---------|
| Имя | Александр Михайлович Бондаренко |
| Статус | Самозанятый (НПД) |
| ИНН | 223504139171 |
| Телефон | +7 902-998-7030 |
| Email | info@airbond.ru |
| Город | Барнаул |
| Telegram-бот | @airbond_barnaul_bot |
| chat_id | 652328822 |
| BOT_TOKEN | 8931211239:AAHx779bSDIBcde6Dlzn1lBcVvn-wKGJ7GQ |
| Яндекс.Метрика | 109337901 |

## Ветка и деплой
- **Ветка:** `claude/create-airbond-repo-OqJQu`
- **URL сайта:** `https://russoroma873420-hash.github.io/bk-priceguard/`
- **Целевой домен:** `airbond.ru`
- **Деплой:** авто через `.github/workflows/pages.yml` при пуше в ветку

## Что уже сделано по сайту (не переделывать)
- [x] Единое модальное окно `#leadModal` для всех CTA
- [x] Telegram-лиды напрямую из JS → @airbond_barnaul_bot (проверено)
- [x] Маска телефона, валидация (имя + телефон + согласие ПД)
- [x] Яндекс.Метрика 109337901, цель `lead_submit`
- [x] `privacy.html` (ФЗ-152), ссылка в footer работает
- [x] Ценовая подсказка «от 85 000 ₽» в калькуляторе
- [x] Footer: ИНН, Барнаул. SEO: meta description, keywords, og:, canonical
- [x] Телефон в шапке (скрыт на мобиле <600px)
- [x] WebP вместо тяжёлых PNG, `CNAME` = airbond.ru

## Статус домена (на 25.05.2026)
- ✅ Домен куплен на reg.ru, DNS верный (4 A-записи GitHub Pages + CNAME www)
- ✅ Custom domain `airbond.ru` привязан в GitHub Pages, «DNS check successful»
- ✅ Сайт открывается на `https://airbond.ru` (проверено в браузере)
- ⏳ Осталось: дождаться выпуска SSL и поставить галочку **Enforce HTTPS** в Settings → Pages (станет активной через 15–60 мин)

> ⚠️ Прим.: из песочницы Claude Code внешние домены недоступны — `curl` к airbond.ru/github.io даёт `403 host_not_allowed` (сетевой фильтр окружения, НЕ статус сайта). Разрешён только github.com. Проверять домен — с телефона/браузера или по статусу GitHub Pages, не через curl.

## Фаза 2 (после зелёного замка)
1. Реставрация фото (приоритет — задача от Екатерины, первый денежный поток)
2. Контент-серия на TenChat (ЯКОРЬ + ОТРАЖЕНИЯ)
3. На airbond.ru: портфолио + ROI-калькулятор для консалтинга
4. Kwork-гиги: мониторинг заявок
5. Маркетинг AirBond: Avito по районам Барнаула, Яндекс.Карты/2ГИС, партнёры-дизайнеры (10% от чека)

## Будущее разделение репозиториев (не сейчас)
Когда сайт стабильно работает — `AirBond/` переедет в отдельный репозиторий `airbond`, в bk-priceguard останется только Python-бэкенд.

## Стиль ответов
- Без вступлений («Отлично! Сейчас разберёмся...»), сразу суть
- В конце — одно конкретное действие для Александра, если нужно
- «Почему» объясняй; «что делаю» — не объясняй. Готовый код, без лишних лекций.

## Команды экономии контекста
- `/clear` — после выполненной задачи
- `/compact` — сжать длинный чат вручную
- `@файл` — указывать конкретный файл (`@AirBond/website-v2/index.html`)
- Plan Mode — для крупных изменений сначала план, потом код

## Правила работы
- Перед коммитом всегда показывать diff и ждать подтверждения
- git commit/push требуют подтверждения (см. `.claude/settings.json`); чтение и git status/diff/log — без
