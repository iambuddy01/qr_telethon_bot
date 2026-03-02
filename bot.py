import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import API_ID, API_HASH, BOT_TOKEN
from qr_generator import generate_pyrogram_session
from pyrogram.errors import SessionPasswordNeeded

bot = Client(
    "qr_session_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

user_sessions = {}  # temporary storage for 2FA


@bot.on_message(filters.command("start"))
async def start(client, message):
    text = (
        "🚀 **QR Session Generator Bot**\n\n"
        "Generate Telegram user session using QR scan.\n\n"
        "✨ No OTP\n"
        "✨ No phone number typing\n"
        "✨ Instant login\n\n"
        "Click below to generate Pyrogram session."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ Generate Pyrogram Session", callback_data="gen_pyro")]
    ])

    await message.reply(text, reply_markup=keyboard)


@bot.on_callback_query(filters.regex("gen_pyro"))
async def generate_session_callback(client, callback_query):
    await callback_query.message.edit("⏳ Generating QR Code...")

    result = await generate_pyrogram_session(bot, callback_query.from_user.id)

    if isinstance(result, tuple):
        if result[0] == "PASSWORD_REQUIRED":
            user_sessions[callback_query.from_user.id] = result[1]
            return
        else:
            session_string, me = result

            await bot.send_message(
                callback_query.from_user.id,
                f"✅ **Session Generated Successfully!**\n\n"
                f"👤 Name: {me.first_name}\n"
                f"🆔 ID: `{me.id}`\n\n"
                f"🔑 **String Session:**\n`{session_string}`"
            )


@bot.on_message(filters.private & ~filters.command("start"))
async def handle_password(client, message):
    user_id = message.from_user.id

    if user_id in user_sessions:
        app = user_sessions[user_id]
        try:
            await app.check_password(message.text)
            me = await app.get_me()
            session_string = await app.export_session_string()
            await app.disconnect()

            await message.reply(
                f"✅ **Session Generated Successfully!**\n\n"
                f"👤 Name: {me.first_name}\n"
                f"🆔 ID: `{me.id}`\n\n"
                f"🔑 **String Session:**\n`{session_string}`"
            )

            del user_sessions[user_id]

        except Exception:
            await message.reply("❌ Wrong Password. Try again.")


bot.run()
