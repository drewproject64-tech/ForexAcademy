# Telegram Ads Destination Setup

## Destination

The promoted URL must point to the actual Telegram bot, not a file, GitHub repository, image, or redirect page.

Use the bot's real Telegram URL, for example:

`https://t.me/YOUR_BOT_USERNAME`

Replace `YOUR_BOT_USERNAME` with the username configured in BotFather.

## Before submitting

Keep the bot online and manually test:

- `/start`
- `/start campaign123`
- `/help`
- Learn Forex and every lesson button
- Analysis Basics and every topic button
- Calculators with valid and invalid input
- Run Again
- Main Menu

Test the same flow on Telegram mobile and desktop.

## Profile consistency

Bot name, username, profile image, About text, Description, /start, /help, menu labels, and ad text should describe the same product.

The application sets these two commands at startup:

- `/start` — Open the main menu
- `/help` — How to use the bot

## Deployment

Required:

`BOT_TOKEN`

Optional:

`PORT` (defaults to 8080)
`LOG_LEVEL` (defaults to INFO)

Docker starts:

`python bot.py`

For a Render Web Service, the process exposes `/health`. For a Render Background Worker, polling works without the health endpoint being required.

## Ad copy

Keep the ad factual and consistent with the actual bot. Do not advertise signals, guaranteed returns, investment results, or features that are not present.

Example factual text:

`Learn forex concepts, analysis basics, and practical trading calculations in Forex Academy Trader.`

## Important

A working repository alone does not prove that the live Telegram destination is active. After deployment, open the real bot and complete the manual journey before submitting the ad.
