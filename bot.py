import asyncio
import logging
import os
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BotCommand, CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("forex_academy")


@dataclass(frozen=True)
class Config:
    token: str
    port: int


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable is required")
    return Config(token=token, port=int(os.getenv("PORT", "8080")))


router = Router()

HOME_TEXT = (
    "<b>📚 Forex Academy Trader</b>\n\n"
    "A practical educational toolkit for learning forex concepts, market analysis basics, "
    "risk management, terminology, and simple trading calculations.\n\n"
    "⚠️ <b>Educational information only.</b> This bot does not guarantee profits "
    "and does not provide personalized investment advice."
)

LESSONS = {
    "forex": "<b>💱 What Is Forex?</b>\n\nForex is the global market where currencies are exchanged. Currency pairs such as EUR/USD show the value of one currency relative to another. Prices can be affected by rates, economic data, central-bank policy, sentiment, and liquidity.",
    "pairs": "<b>💱 Currency Pairs</b>\n\nMajor, minor, and exotic pairs can differ in liquidity and spread. The first currency is the base currency and the second is the quote currency. Always check your broker's exact contract specifications.",
    "candles": "<b>🕯 Candlestick Basics</b>\n\nA candlestick summarizes open, high, low, and close prices for a selected period. Patterns describe historical price behavior; they do not guarantee the next move.",
    "structure": "<b>📈 Market Structure</b>\n\nMarket structure describes sequences such as higher highs, higher lows, lower highs, and lower lows. It is a framework for describing price behavior, not a certain forecast.",
    "support": "<b>📏 Support & Resistance</b>\n\nSupport and resistance are price areas where market participants may have reacted before. Treat them as zones rather than exact lines because price can break or revisit them.",
    "technical": "<b>📐 Technical Analysis</b>\n\nTechnical analysis uses historical price information to study trends, momentum, volatility, and market behavior. Common tools include moving averages, trend lines, and momentum indicators. No indicator guarantees an outcome.",
    "fundamental": "<b>🌐 Fundamental Analysis</b>\n\nFundamental analysis examines inflation, employment, GDP, interest rates, central-bank policy, and broader economic conditions.",
    "risk": "<b>🛡 Risk Management</b>\n\nRisk management focuses on limiting the impact of adverse outcomes. Concepts include position sizing, risk limits, stop-loss planning, leverage awareness, and keeping a trading record.",
    "psychology": "<b>🧠 Trading Psychology</b>\n\nCommon challenges include fear of missing out, revenge trading, overtrading, and changing rules after a loss. Consistent processes and journaling can help reduce emotional decision-making.",
}

GLOSSARY = {
    "pair": "A quoted relationship between two currencies, such as EUR/USD.",
    "pip": "A commonly used unit for describing a small change in a forex quote. Exact conventions can vary.",
    "lot": "A standardized trading size. Contract size varies by instrument and broker.",
    "spread": "The difference between the bid and ask price.",
    "leverage": "A mechanism that increases market exposure relative to posted margin. It can amplify both gains and losses.",
    "margin": "Funds required by a broker to support a leveraged position.",
    "drawdown": "A decline from a previous peak in an account or strategy value.",
    "stop_loss": "A rule or order intended to reduce or close exposure when a specified price condition is reached.",
    "take_profit": "A rule or order intended to close exposure when a specified target condition is reached.",
}


class CalcState(StatesGroup):
    percentage = State()
    risk_reward = State()
    position = State()


def home_keyboard():
    kb = ReplyKeyboardBuilder()
    for label in ("📚 Learn Forex", "📊 Analysis Basics", "🧮 Calculators", "📖 Glossary", "🛡 Risk Management", "ℹ️ About"):
        kb.button(text=label)
    kb.adjust(2, 2, 2)
    return kb.as_markup(resize_keyboard=True, is_persistent=True)


def learn_keyboard():
    kb = InlineKeyboardBuilder()
    items = [
        ("💱 What Is Forex?", "forex"), ("💱 Currency Pairs", "pairs"),
        ("🕯 Candlesticks", "candles"), ("📈 Market Structure", "structure"),
        ("📏 Support & Resistance", "support"), ("📐 Technical Analysis", "technical"),
        ("🌐 Fundamental Analysis", "fundamental"), ("🛡 Risk Management", "risk"),
        ("🧠 Trading Psychology", "psychology"),
    ]
    for label, key in items:
        kb.button(text=label, callback_data=f"lesson:{key}")
    kb.button(text="↩️ Home", callback_data="home")
    kb.adjust(2, 2, 2, 2, 2, 1)
    return kb.as_markup()


def analysis_keyboard():
    kb = InlineKeyboardBuilder()
    for label, data in [
        ("🕯 Candlesticks", "lesson:candles"),
        ("📈 Market Structure", "lesson:structure"),
        ("📏 Support & Resistance", "lesson:support"),
        ("📐 Technical Analysis", "lesson:technical"),
        ("🌐 Fundamental Analysis", "lesson:fundamental"),
        ("⏰ Trading Sessions", "sessions"),
        ("📅 Economic Events", "economic"),
        ("↩️ Home", "home"),
    ]:
        kb.button(text=label, callback_data=data)
    kb.adjust(2, 2, 2, 1, 1)
    return kb.as_markup()


def calculator_keyboard():
    kb = InlineKeyboardBuilder()
    for label, data in [
        ("📐 Percentage", "calc:percentage"),
        ("📏 Risk / Reward", "calc:rr"),
        ("💰 Position Size", "calc:position"),
        ("↩️ Home", "home"),
    ]:
        kb.button(text=label, callback_data=data)
    kb.adjust(1, 1, 1, 1)
    return kb.as_markup()


def glossary_keyboard():
    kb = InlineKeyboardBuilder()
    for label, key in [
        ("Currency Pair", "pair"), ("Pip", "pip"), ("Lot", "lot"),
        ("Spread", "spread"), ("Leverage", "leverage"), ("Margin", "margin"),
        ("Drawdown", "drawdown"), ("Stop Loss", "stop_loss"), ("Take Profit", "take_profit"),
    ]:
        kb.button(text=label, callback_data=f"glossary:{key}")
    kb.button(text="↩️ Home", callback_data="home")
    kb.adjust(3, 3, 3, 1)
    return kb.as_markup()


def back_home_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="↩️ Home", callback_data="home")
    return kb.as_markup()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(HOME_TEXT, reply_markup=home_keyboard())


@router.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "<b>Help</b>\n\n"
        "/start — Open the main menu\n"
        "/menu — Open the main menu\n"
        "/help — Show help\n"
        "/learn — Forex lessons\n"
        "/calculators — Trading calculators\n"
        "/glossary — Forex glossary\n"
        "/risk — Risk management\n"
        "/about — About the bot\n"
        "/privacy — Privacy note",
        reply_markup=home_keyboard(),
    )


@router.message(Command("menu"))
@router.message(F.text == "ℹ️ Main Menu")
async def menu_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(HOME_TEXT, reply_markup=home_keyboard())


@router.message(Command("about"))
@router.message(F.text == "ℹ️ About")
async def about_handler(message: Message):
    await message.answer(
        "<b>About Forex Academy Trader</b>\n\n"
        "An educational Telegram bot for learning forex concepts, analysis basics, "
        "risk management, terminology, and simple trading tools.\n\n"
        "No profit guarantees, signal promises, or personalized investment recommendations."
    )


@router.message(Command("privacy"))
async def privacy_handler(message: Message):
    await message.answer(
        "<b>Privacy</b>\n\n"
        "The bot does not request passwords, broker credentials, payment details, or access to financial accounts. "
        "Telegram may provide basic account and message metadata needed for bot operation."
    )


@router.message(Command("learn"))
@router.message(F.text == "📚 Learn Forex")
async def learn_handler(message: Message):
    await message.answer("<b>📚 Learn Forex</b>\n\nChoose a topic:", reply_markup=learn_keyboard())


@router.message(F.text == "📊 Analysis Basics")
async def analysis_handler(message: Message):
    await message.answer(
        "<b>📊 Analysis Basics</b>\n\nExplore common ways traders describe market behavior and economic conditions.",
        reply_markup=analysis_keyboard(),
    )


@router.message(Command("risk"))
@router.message(F.text == "🛡 Risk Management")
async def risk_handler(message: Message):
    await message.answer(LESSONS["risk"], reply_markup=back_home_keyboard())


@router.message(Command("calculators"))
@router.message(F.text == "🧮 Calculators")
async def calculators_handler(message: Message):
    await message.answer(
        "<b>🧮 Calculators</b>\n\nChoose a calculator. These tools perform simple educational mathematics.",
        reply_markup=calculator_keyboard(),
    )


@router.message(Command("glossary"))
@router.message(F.text == "📖 Glossary")
async def glossary_handler(message: Message):
    await message.answer("<b>📖 Forex Glossary</b>\n\nChoose a term:", reply_markup=glossary_keyboard())


@router.callback_query(F.data == "home")
async def home_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(HOME_TEXT)
    await callback.message.answer("Main menu", reply_markup=home_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("lesson:"))
async def lesson_callback(callback: CallbackQuery):
    key = callback.data.split(":", 1)[1]
    text = LESSONS.get(key)
    if not text:
        await callback.answer("Lesson unavailable", show_alert=True)
        return
    await callback.message.edit_text(text, reply_markup=back_home_keyboard())
    await callback.answer()


@router.callback_query(F.data == "sessions")
async def sessions_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        "<b>⏰ Trading Sessions</b>\n\n"
        "Forex is commonly discussed using Asian, London, and New York sessions. "
        "Session overlaps may have different liquidity and volatility characteristics. "
        "Exact hours can vary with daylight-saving changes and broker schedules.",
        reply_markup=back_home_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "economic")
async def economic_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        "<b>📅 Economic Events</b>\n\n"
        "Economic calendars commonly list inflation, employment, GDP, interest-rate decisions, "
        "and central-bank statements. Major releases can affect volatility. Verify current schedules with a reputable live calendar.",
        reply_markup=back_home_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("glossary:"))
async def glossary_callback(callback: CallbackQuery):
    key = callback.data.split(":", 1)[1]
    explanation = GLOSSARY.get(key)
    if not explanation:
        await callback.answer("Term unavailable", show_alert=True)
        return
    await callback.message.edit_text(
        f"<b>{key.replace('_', ' ').title()}</b>\n\n{explanation}",
        reply_markup=back_home_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "calc:percentage")
async def percentage_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CalcState.percentage)
    await callback.message.edit_text("<b>📐 Percentage Calculator</b>\n\nSend: <code>value percentage</code>\nExample: <code>2500 1.5</code>")
    await callback.answer()


@router.callback_query(F.data == "calc:rr")
async def rr_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CalcState.risk_reward)
    await callback.message.edit_text("<b>📏 Risk / Reward Calculator</b>\n\nSend: <code>risk reward</code>\nExample: <code>50 100</code>")
    await callback.answer()


@router.callback_query(F.data == "calc:position")
async def position_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CalcState.position)
    await callback.message.edit_text(
        "<b>💰 Position Size Calculator</b>\n\n"
        "Send: <code>account risk_percent stop_distance</code>\nExample: <code>1000 1 50</code>\n\n"
        "This is a simplified educational calculation."
    )
    await callback.answer()


@router.message(CalcState.percentage)
async def percentage_calculation(message: Message, state: FSMContext):
    try:
        value, pct = map(float, (message.text or "").replace(",", ".").split())
        await message.answer(f"<b>Result:</b> {value * pct / 100:.2f}", reply_markup=home_keyboard())
        await state.clear()
    except (ValueError, TypeError):
        await message.answer("Please send exactly two numbers, for example: <code>2500 1.5</code>")


@router.message(CalcState.risk_reward)
async def rr_calculation(message: Message, state: FSMContext):
    try:
        risk, reward = map(float, (message.text or "").replace(",", ".").split())
        if risk <= 0 or reward <= 0:
            raise ValueError
        await message.answer(f"<b>Risk / Reward:</b> {reward / risk:.2f}R", reply_markup=home_keyboard())
        await state.clear()
    except (ValueError, TypeError):
        await message.answer("Please send two positive numbers, for example: <code>50 100</code>")


@router.message(CalcState.position)
async def position_calculation(message: Message, state: FSMContext):
    try:
        account, risk_pct, stop_distance = map(float, (message.text or "").replace(",", ".").split())
        if account <= 0 or risk_pct < 0 or stop_distance <= 0:
            raise ValueError
        risk_cash = account * risk_pct / 100
        units = risk_cash / stop_distance
        await message.answer(
            f"<b>Risk amount:</b> {risk_cash:.2f}\n<b>Simplified units:</b> {units:.4f}\n\n"
            "This is not a broker-specific lot calculation.",
            reply_markup=home_keyboard(),
        )
        await state.clear()
    except (ValueError, TypeError):
        await message.answer("Please send three valid numbers, for example: <code>1000 1 50</code>")


@router.message(F.text)
async def fallback_handler(message: Message):
    await message.answer("I didn't recognize that option. Please use the menu or /help.", reply_markup=home_keyboard())


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health"):
            body = b"Forex Academy Trader is running"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        return


def start_health_server(port: int):
    server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logger.info("Health server listening on port %s", port)


async def configure_bot(bot: Bot):
    await bot.set_my_commands([
        BotCommand(command="start", description="Open the main menu"),
        BotCommand(command="menu", description="Open the main menu"),
        BotCommand(command="help", description="Show help"),
        BotCommand(command="learn", description="Forex lessons"),
        BotCommand(command="calculators", description="Open calculators"),
        BotCommand(command="glossary", description="Forex glossary"),
        BotCommand(command="risk", description="Risk management"),
        BotCommand(command="about", description="About the bot"),
        BotCommand(command="privacy", description="Privacy note"),
    ])
    await bot.set_my_short_description(
        "Forex education, analysis concepts, risk management and practical trading calculators."
    )
    await bot.set_my_description(
        "Forex Academy Trader is an educational toolkit for learning forex concepts, analysis basics, "
        "risk management, terminology and simple calculators. Educational information only; no profit guarantees "
        "or personalized investment advice."
    )


async def main():
    config = load_config()
    start_health_server(config.port)

    bot = Bot(token=config.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await configure_bot(bot)

    me = await bot.get_me()
    logger.info("Started @%s", me.username)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
