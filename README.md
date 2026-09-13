# Forex Academy Trader

A Telegram bot for forex education, analysis concepts, terminology, risk-management education, and simple calculators.

## Features

- `/start`, `/help`, `/about`, `/privacy`
- Persistent reply-keyboard main menu
- Forex lessons and analysis basics
- Candlestick, market structure, support/resistance, technical and fundamental analysis
- Risk-management and trading-psychology education
- Forex glossary
- Percentage, risk/reward, and simplified position-size calculators
- Educational disclaimers and no profit guarantees
- Python 3.12 + aiogram 3.x

## Run locally

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

Set the environment variable:

```bash
BOT_TOKEN=your_bot_token
```

Then run:

```bash
python bot.py
```

## Render / Docker

Use the repository as a Docker deployment and set `BOT_TOKEN` as an environment variable. The container runs `python bot.py`.

## Telegram Ads positioning

The bot is designed as a real educational destination rather than a redirect-only bot. Ad copy should accurately describe the available educational tools and should avoid guarantees, exaggerated performance claims, fake testimonials, or personalized investment promises.

## Disclaimer

Educational and informational content only. The bot does not provide personalized investment advice, does not guarantee profits, and does not request broker credentials, passwords, or payment details.
