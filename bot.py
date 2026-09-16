import asyncio
import logging
import os
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BotCommand, CallbackQuery, ErrorEvent, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("forex_academy")

router = Router()


@dataclass(frozen=True)
class Config:
    token: str
    port: int


def load_config() -> Config:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable is required")

    try:
        port = int(os.getenv("PORT", "8080"))
    except ValueError as exc:
        raise RuntimeError("PORT must be a valid integer") from exc

    if not 1 <= port <= 65535:
        raise RuntimeError("PORT must be between 1 and 65535")

    return Config(token=token, port=port)


WELCOME_TEXT = (
    "<b>📚 Forex Academy Trader</b>\n\n"
    "A simple Telegram-native learning tool for forex concepts, "
    "market analysis basics, and practical trading calculations.\n\n"
    "<b>Choose a function:</b>\n"
    "• 📚 Learn Forex — core forex concepts\n"
    "• 📊 Analysis Basics — understand common analysis methods\n"
    "• 🧮 Calculators — simple educational calculations\n\n"
    "⚠️ Educational information only. No profit guarantees or personalized investment advice."
)

HELP_TEXT = (
    "<b>Help</b>\n\n"
    "Use the three buttons in the main menu:\n"
    "• 📚 <b>Learn Forex</b> — study core concepts.\n"
    "• 📊 <b>Analysis Basics</b> — review common market-analysis concepts.\n"
    "• 🧮 <b>Calculators</b> — run simple percentage, risk/reward, or position-size calculations.\n\n"
    "For a fresh start, send /start. You can return to the main menu from any section."
)

LEARN_TEXT = (
    "<b>📚 Learn Forex</b>\n\n"
    "Choose a topic. Each topic gives a short, educational explanation."
)

LESSONS = {
    "forex": (
        "<b>💱 What Is Forex?</b>\n\n"
        "Forex is the market where currencies are exchanged. A currency pair such as EUR/USD "
        "shows one currency relative to another. Prices can be affected by economic data, "
        "interest rates, central-bank policy, sentiment, and liquidity."
    ),
    "pairs": (
        "<b>💱 Currency Pairs</b>\n\n"
        "Major, minor, and exotic pairs can differ in liquidity and spread. "
        "The first currency is the base currency and the second is the quote currency."
    ),
    "candles": (
        "<b>🕯 Candlestick Basics</b>\n\n"
        "A candlestick summarizes open, high, low, and close prices for a selected period. "
        "Patterns describe historical price behavior; they do not guarantee the next move."
    ),
    "structure": (
        "<b>📈 Market Structure</b>\n\n"
        "Market structure describes sequences such as higher highs, higher lows, lower highs, "
        "and lower lows. It is a framework for describing price behavior, not a certain forecast."
    ),
    "risk": (
        "<b>🛡 Risk Management</b>\n\n"
        "Risk management focuses on limiting the impact of adverse outcomes. "
        "Concepts include position sizing, risk limits, stop-loss planning, leverage awareness, "
        "and keeping a trading record."
    ),
    "psychology": (
        "<b>🧠 Trading Psychology</b>\n\n"
        "Common challenges include fear of missing out, revenge trading, overtrading, "
        "and changing rules after a loss. Consistent processes and journaling can help."
    ),
}

ANALYSIS_TEXT = (
    "<b>📊 Analysis Basics</b>\n\n"
    "Choose a topic to learn how traders commonly describe price behavior and economic conditions."
)

ANALYSIS = {
    "technical": (
        "<b>📐 Technical Analysis</b>\n\n"
        "Technical analysis uses historical price information to study trends, momentum, "
        "volatility, and market behavior. Common tools include moving averages, trend lines, "
        "and momentum indicators. No indicator guarantees an outcome."
    ),
    "fundamental": (
        "<b>🌐 Fundamental Analysis</b>\n\n"
        "Fundamental analysis examines factors such as inflation, employment, GDP, "
        "interest rates, and central-bank policy."
    ),
    "support": (
        "<b>📏 Support & Resistance</b>\n\n"
        "Support and resistance are price areas where market participants may have reacted before. "
        "Treat them as zones rather than exact lines because price can break or revisit them."
    ),
    "sessions": (
        "<b>⏰ Trading Sessions</b>\n\n"
        "Forex is commonly discussed using Asian, London, and New York sessions. "
        "Session overlaps can have different liquidity and volatility characteristics."
    ),
}


class CalcState(StatesGroup):
    percentage = State()
    risk_reward = State()
    position = State()


def main_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="📚 Learn Forex", callback_data="menu:learn")
    kb.button(text="📊 Analysis Basics", callback_data="menu:analysis")
    kb.button(text="🧮 Calculators", callback_data="menu:calculators")
    kb.button(text="❓ Help", callback_data="menu:help")
    kb.adjust(1)
    return kb.as_markup()


def learn_menu():
    kb = InlineKeyboardBuilder()
    for label, key in (
        ("💱 What Is Forex?", "forex"),
        ("💱 Currency Pairs", "pairs"),
        ("🕯 Candlesticks", "candles"),
        ("📈 Market Structure", "structure"),
        ("🛡 Risk Management", "risk"),
        ("🧠 Trading Psychology", "psychology"),
    ):
        kb.button(text=label, callback_data=f"learn:{key}")
    kb.button(text="↩️ Main Menu", callback_data="home")
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup()


def analysis_menu():
    kb = InlineKeyboardBuilder()
    for label, key in (
        ("📐 Technical Analysis", "technical"),
        ("🌐 Fundamental Analysis", "fundamental"),
        ("📏 Support & Resistance", "support"),
        ("⏰ Trading Sessions", "sessions"),
    ):
        kb.button(text=label, callback_data=f"analysis:{key}")
    kb.button(text="↩️ Main Menu", callback_data="home")
    kb.adjust(2, 2, 1)
    return kb.as_markup()


def calculator_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="📐 Percentage", callback_data="calc:percentage")
    kb.button(text="📏 Risk / Reward", callback_data="calc:rr")
    kb.button(text="💰 Position Size", callback_data="calc:position")
    kb.button(text="↩️ Main Menu", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()


def input_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔁 Run Again", callback_data="calculator:again")
    kb.button(text="↩️ Main Menu", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()


def back_home():
    kb = InlineKeyboardBuilder()
    kb.button(text="↩️ Main Menu", callback_data="home")
    return kb.as_markup()


async def show_home(message: Message, state: FSMContext | None = None):
    if state:
        await state.clear()
    await message.answer(WELCOME_TEXT, reply_markup=main_menu())


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    # CommandStart safely accepts /start with an optional payload.
    await show_home(message, state)


@router.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(HELP_TEXT, reply_markup=main_menu())


@router.callback_query(F.data == "home")
async def home_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(WELCOME_TEXT, reply_markup=main_menu())


@router.callback_query(F.data == "menu:help")
async def help_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(HELP_TEXT, reply_markup=main_menu())


@router.callback_query(F.data == "menu:learn")
async def learn_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(LEARN_TEXT, reply_markup=learn_menu())


@router.callback_query(F.data == "menu:analysis")
async def analysis_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(ANALYSIS_TEXT, reply_markup=analysis_menu())


@router.callback_query(F.data == "menu:calculators")
async def calculators_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(CALCULATOR_TEXT, reply_markup=calculator_menu())


@router.callback_query(F.data.startswith("learn:"))
async def lesson_callback(callback: CallbackQuery):
    key = (callback.data or "").split(":", 1)[1]
    text = LESSONS.get(key)
    if not text:
        await callback.answer("That topic is unavailable.", show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=back_home())


@router.callback_query(F.data.startswith("analysis:"))
async def analysis_topic_callback(callback: CallbackQuery):
    key = (callback.data or "").split(":", 1)[1]
    text = ANALYSIS.get(key)
    if not text:
        await callback.answer("That topic is unavailable.", show_alert=True)
        return
    await callback.answer()
    await callback.message.edit_text(text, reply_markup=back_home())


@router.callback_query(F.data == "calc:percentage")
async def percentage_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CalcState.percentage)
    await callback.answer()
    await callback.message.edit_text(
        "<b>📐 Percentage Calculator</b>\n\n"
        "Send two numbers: <code>value percentage</code>\n"
        "Example: <code>2500 1.5</code>",
        reply_markup=calculator_menu(),
    )


@router.callback_query(F.data == "calc:rr")
async def rr_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CalcState.risk_reward)
    await callback.answer()
    await callback.message.edit_text(
        "<b>📏 Risk / Reward Calculator</b>\n\n"
        "Send two positive numbers: <code>risk reward</code>\n"
        "Example: <code>50 100</code>",
        reply_markup=calculator_menu(),
    )


@router.callback_query(F.data == "calc:position")
async def position_callback(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CalcState.position)
    await callback.answer()
    await callback.message.edit_text(
        "<b>💰 Position Size Calculator</b>\n\n"
        "Send: <code>account risk_percent stop_distance</code>\n"
        "Example: <code>1000 1 50</code>\n\n"
        "This is a simplified educational calculation, not a broker-specific lot calculation.",
        reply_markup=calculator_menu(),
    )


@router.callback_query(F.data == "calculator:again")
async def calculator_again_callback(callback: CallbackQuery, state: FSMContext):
    current = await state.get_state()
    await callback.answer()
    if current == CalcState.percentage.state:
        await callback.message.edit_text(
            "<b>📐 Percentage Calculator</b>\n\n"
            "Send: <code>value percentage</code>\nExample: <code>2500 1.5</code>",
            reply_markup=calculator_menu(),
        )
    elif current == CalcState.risk_reward.state:
        await callback.message.edit_text(
            "<b>📏 Risk / Reward Calculator</b>\n\n"
            "Send: <code>risk reward</code>\nExample: <code>50 100</code>",
            reply_markup=calculator_menu(),
        )
    elif current == CalcState.position.state:
        await callback.message.edit_text(
            "<b>💰 Position Size Calculator</b>\n\n"
            "Send: <code>account risk_percent stop_distance</code>\nExample: <code>1000 1 50</code>",
            reply_markup=calculator_menu(),
        )
    else:
        await callback.message.edit_text(CALCULATOR_TEXT, reply_markup=calculator_menu())


def parse_numbers(text: str | None, count: int) -> list[float]:
    parts = (text or "").replace(",", ".").split()
    if len(parts) != count:
        raise ValueError
    values = [float(part) for part in parts]
    if not all(value == value and abs(value) != float("inf") for value in values):
        raise ValueError
    return values


@router.message(CalcState.percentage)
async def percentage_calculation(message: Message, state: FSMContext):
    try:
        value, pct = parse_numbers(message.text, 2)
        result = value * pct / 100
        await state.clear()
        await message.answer(f"<b>Result:</b> {result:.2f}", reply_markup=input_menu())
    except (ValueError, TypeError):
        await message.answer(
            "That input isn't valid. Please send exactly two numbers, for example: <code>2500 1.5</code>.",
            reply_markup=calculator_menu(),
        )


@router.message(CalcState.risk_reward)
async def rr_calculation(message: Message, state: FSMContext):
    try:
        risk, reward = parse_numbers(message.text, 2)
        if risk <= 0 or reward <= 0:
            raise ValueError
        await state.clear()
        await message.answer(
            f"<b>Risk / Reward:</b> {reward / risk:.2f}R",
            reply_markup=input_menu(),
        )
    except (ValueError, TypeError):
        await message.answer(
            "That input isn't valid. Send two positive numbers, for example: <code>50 100</code>.",
            reply_markup=calculator_menu(),
        )


@router.message(CalcState.position)
async def position_calculation(message: Message, state: FSMContext):
    try:
        account, risk_pct, stop_distance = parse_numbers(message.text, 3)
        if account <= 0 or risk_pct <= 0 or stop_distance <= 0:
            raise ValueError
        risk_cash = account * risk_pct / 100
        units = risk_cash / stop_distance
        await state.clear()
        await message.answer(
            f"<b>Risk amount:</b> {risk_cash:.2f}\n"
            f"<b>Simplified units:</b> {units:.4f}\n\n"
            "This is an educational calculation and not a broker-specific lot calculation.",
            reply_markup=input_menu(),
        )
    except (ValueError, TypeError):
        await message.answer(
            "That input isn't valid. Send three positive numbers, for example: <code>1000 1 50</code>.",
            reply_markup=calculator_menu(),
        )


@router.message()
async def fallback_handler(message: Message, state: FSMContext):
    current = await state.get_state()
    if current:
        await message.answer(
            "I couldn't use that input. Please follow the format shown above or choose a calculator from the menu.",
            reply_markup=calculator_menu(),
        )
        return
    await message.answer("Please choose an option from the main menu.", reply_markup=main_menu())


@router.errors()
async def global_error_handler(event: ErrorEvent):
    logger.exception("Unhandled update error", exc_info=event.exception)
    try:
        if event.update.callback_query:
            await event.update.callback_query.answer(
                "Something went wrong. Please try again.", show_alert=True
            )
        elif event.update.message:
            await event.update.message.answer(
                "Something went wrong. Please send /start and try again."
            )
    except TelegramAPIError:
        logger.exception("Failed to send error response to user")


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health"):
            body = b"Forex Academy Trader is running"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        return


def start_health_server(port: int):
    server = ThreadingHTTPServer(("0.0.0.0", port), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True, name="health-server").start()
    logger.info("Health server listening on port %s", port)


async def configure_bot(bot: Bot):
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Open the main menu"),
            BotCommand(command="help", description="How to use the bot"),
        ]
    )
    await bot.set_my_short_description(
        "Learn forex concepts, analysis basics, and use simple trading calculators."
    )
    await bot.set_my_description(
        "Forex Academy Trader is a Telegram-native educational tool for learning forex concepts, "
        "understanding analysis basics, and running simple trading calculations. "
        "Educational information only; no profit guarantees or personalized investment advice."
    )


async def main():
    config = load_config()
    start_health_server(config.port)

    bot = Bot(
        token=config.token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
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
