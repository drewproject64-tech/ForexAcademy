# Telegram Ads Destination Checklist

## 1. Use the bot link as the ad destination

The URL field in Telegram Ads must point to the actual Telegram bot. Do not enter `svg`, a GitHub URL, an image file, or a website that is not the advertised bot.

Use:

`https://t.me/YOUR_BOT_USERNAME`

For example, if BotFather gave the bot the username `@ForexAcademyTraderBot`, use:

`https://t.me/ForexAcademyTraderBot`

## 2. Before submitting the ad

Open the bot from both Telegram mobile and desktop and test:

- /start
- /menu
- /help
- /learn
- /calculators
- /glossary
- /risk
- /about
- /privacy
- Main-menu buttons
- Inline lesson buttons
- Calculator inputs and results
- Home buttons

The bot must be online while Telegram reviews the destination.

## 3. Bot profile

In BotFather, make sure the bot has:

- A professional profile photo
- A complete About/short description
- A complete Description

The application also refreshes the bot command menu and descriptions every time it starts.

## 4. Recommended ad

Ad title:
Forex Academy Trader

Ad text:
Learn forex trading concepts, market analysis basics, risk management, and useful trading tools with Forex Academy Trader.

Destination:
https://t.me/YOUR_BOT_USERNAME

Do not add a second destination link in the ad text.

## 5. Deployment

For Render, use a Background Worker for polling when possible. If using a Web Service, the bot now exposes a simple health endpoint using the PORT environment variable.

Set:

BOT_TOKEN=your_bot_token

The Docker image starts with:

python bot.py

## 6. Why the previous rejection happened

Telegram says destination bots must be active, technically complete, and respond properly to commands on mobile and desktop. The bot has now been updated with explicit commands, command-menu registration, complete profile text, stronger fallback handling, and a health endpoint.

Telegram also requires the promoted destination to match the ad and does not allow empty or abandoned bots.
