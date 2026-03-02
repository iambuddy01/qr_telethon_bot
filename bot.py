import asyncio
import logging
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import API_ID, API_HASH, BOT_TOKEN
from qr_generator import generate_pyrogram_session


# -------------------------------------------------
# Logging Setup
# -------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def startup_banner():
    banner = f"""
╔══════════════════════════════════════════════════╗
║                                                  ║
║        🚀 QR SESSION GENERATOR BOT              ║
║                                                  ║
╠══════════════════════════════════════════════════╣
║  ✅ Status      : ONLINE                        ║
║  🤖 Framework   : Pyrogram v2                   ║
║  🔐 Mode        : QR Login (User Session)       ║
║  🕒 Started At  : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC   ║
║                                                  ║
╚══════════════════════════════════════════════════╝
"""
    logger.info(banner)


# -------------------------------------------------
# Bot Initialization
# -------------------------------------------------

bot = Client(
    "qr_session_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Store pending 2FA sessions
pending_password = {}


# -------------------------------------------------
# /start Command
# -------------------------------------------------

@bot.on_message(filters.command("start"))
async def start_handler(client, message):
    text = (
        "🚀 **Welcome to QR Session Generator**\n\n"
        "Generate your Telegram **Pyrogram String Session** "
        "instantly using secure QR login.\n\n"
        "✨ No phone number typing\n"
        "✨ No OTP entering\n"
        "✨ Fast & Secure\n\n"
        "Click below to begin."
    )

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⚡ Generate Pyrogram Session", callback_data="gen_pyro")]
        ]
    )

    await message.reply_text(text, reply_markup=keyboard)


# -------------------------------------------------
# QR Generate Callback
# -------------------------------------------------

@bot.on_callback_query(filters.regex("gen_pyro"))
async def generate_callback(client, callback_query):
    user_id = callback_query.from_user.id

    await callback_query.message.edit_text(
        "⏳ **Generating QR Code...**\n\nPlease wait..."
    )

    result = await generate_pyrogram_session(bot, user_id)

    # ❌ QR Expired
    if result == "EXPIRED":
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔄 Regenerate QR", callback_data="gen_pyro")]]
        )

        await bot.send_message(
            user_id,
            "❌ **QR Expired!**\n\n"
            "Please generate a new QR and try again.",
            reply_markup=keyboard
        )
        return

    # 🔐 2FA Required
    if isinstance(result, tuple) and result[0] == "PASSWORD_REQUIRED":
        app = result[1]
        qr_msg = result[2]

        pending_password[user_id] = (app, qr_msg)

        await bot.send_message(
            user_id,
            "🔐 **Two-Step Verification Enabled**\n\n"
            "Please send your Telegram account password."
        )
        return

    # ✅ SUCCESS
    if isinstance(result, tuple) and result[0] == "SUCCESS":
        me = result[1]

        await bot.send_message(
            user_id,
            f"""
🎉 **Login Successful!**

👤 **Name:** {me.first_name}
🆔 **User ID:** `{me.id}`

✅ Your session has been securely saved
inside your **Saved Messages**.

📂 Open Telegram → Saved Messages
🔐 Keep your session private.
"""
        )


# -------------------------------------------------
# Handle 2FA Password
# -------------------------------------------------

@bot.on_message(filters.private & ~filters.command("start"))
async def password_handler(client, message):
    user_id = message.from_user.id

    if user_id not in pending_password:
        return

    app, qr_msg = pending_password[user_id]

    try:
        await app.check_password(message.text)

        me = await app.get_me()
        session_string = await app.export_session_string()

        # Save to Saved Messages
        await app.send_message(
            "me",
            f"🔐 **Your Pyrogram String Session**\n\n`{session_string}`"
        )

        await qr_msg.delete()
        await app.disconnect()

        await message.reply(
            f"""
🎉 **Login Successful!**

👤 **Name:** {me.first_name}
🆔 **User ID:** `{me.id}`

✅ Your session has been saved in Saved Messages.
"""
        )

        del pending_password[user_id]

    except Exception:
        await message.reply("❌ Incorrect password. Try again.")


# -------------------------------------------------
# Run Bot
# -------------------------------------------------

if __name__ == "__main__":
    startup_banner()
    bot.run()
