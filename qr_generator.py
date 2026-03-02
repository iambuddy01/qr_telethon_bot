import asyncio
import base64
import qrcode
from io import BytesIO
from pyrogram import Client
from pyrogram.raw.functions.auth import ExportLoginToken, ImportLoginToken
from pyrogram.errors import SessionPasswordNeeded
from config import API_ID, API_HASH


async def generate_pyrogram_session(bot, user_id):
    app = Client(
        name="qr_temp",
        api_id=API_ID,
        api_hash=API_HASH,
        in_memory=True
    )

    await app.connect()

    token_data = await app.invoke(
        ExportLoginToken(api_id=API_ID, api_hash=API_HASH, except_ids=[])
    )

    login_token = token_data.token
    login_token_b64 = base64.urlsafe_b64encode(login_token).decode()
    qr_url = f"tg://login?token={login_token_b64}"

    # Generate QR Image
    qr = qrcode.make(qr_url)
    bio = BytesIO()
    bio.name = "qr.png"
    qr.save(bio, "PNG")
    bio.seek(0)

    await bot.send_photo(
        user_id,
        bio,
        caption="📲 **Scan this QR using Telegram**\n\n"
                "Go to:\n"
                "`Settings → Devices → Link Desktop Device`\n\n"
                "⏳ QR expires in 30 seconds."
    )

    # Wait for scan
    for _ in range(15):  # ~45 seconds
        await asyncio.sleep(3)
        try:
            await app.invoke(ImportLoginToken(token=login_token))
            break
        except Exception:
            continue
    else:
        await bot.send_message(user_id, "❌ QR Expired. Please try again.")
        await app.disconnect()
        return

    try:
        me = await app.get_me()
    except SessionPasswordNeeded:
        await bot.send_message(user_id, "🔐 2FA Enabled.\nPlease send your password.")
        return "PASSWORD_REQUIRED", app

    session_string = await app.export_session_string()
    await app.disconnect()

    return session_string, me
