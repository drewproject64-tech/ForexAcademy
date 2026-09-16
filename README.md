# Forex Academy Trader

A focused Telegram-native bot for learning forex concepts, understanding common analysis methods, and performing simple educational trading calculations.

## Three core functions

1. **Learn Forex** — short lessons on core forex concepts, including currency pairs, candlesticks, market structure, risk management, and trading psychology.
2. **Analysis Basics** — concise explanations of technical analysis, fundamental analysis, support/resistance, and trading sessions.
3. **Calculators** — percentage, risk/reward, and simplified position-size calculations.

The bot intentionally avoids accounts, payments, external redirects, signal promises, and unnecessary data storage.

## Commands

- `/start` — open the main menu
- `/help` — explain the three functions

`/start` also safely accepts an optional Telegram start payload.

## Local setup

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

Set:

```text
BOT_TOKEN=your_bot_token
```

Run:

```bash
python bot.py
```

Run tests:

```bash
pytest -q
```

## Render / Docker

The Docker image uses Python 3.12 and starts the actual entry point:

```text
python bot.py
```

The process runs Telegram polling and also exposes `/` and `/health` on `PORT` for a Render Web Service. Set `BOT_TOKEN` as a secret environment variable.

A Render Background Worker is also suitable for polling; in that mode the health endpoint is harmless but not required.

## Environment variables

- `BOT_TOKEN` — required Telegram bot token
- `PORT` — optional HTTP health port; defaults to `8080`
- `LOG_LEVEL` — optional logging level; defaults to `INFO`

No credentials are stored in source code.

## Telegram Ads destination readiness

The bot is designed to be a genuine destination: users can complete all core interactions inside Telegram without being sent to an external website. The advertised destination should be the bot's actual Telegram username, and the ad copy should accurately describe these three functions.

Before submission, manually test `/start`, `/help`, every main-menu button, every topic button, every calculator with valid and invalid input, Run Again, and Main Menu on Telegram mobile and desktop.

## Disclaimer

Educational and informational content only. The bot does not provide personalized investment advice or guarantee profits.
