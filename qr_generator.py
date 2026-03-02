import asyncio
import base64
import qrcode
from io import BytesIO

from pyrogram import Client
from pyrogram.raw.functions.auth import ExportLoginToken, ImportLoginToken
from pyrogram.raw.types.auth import LoginTokenSuccess, LoginTokenMigrateTo
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

    # Export Login Token
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

    qr_message = await bot.send_photo(
        user_id,
        bio,
        caption=(
            "🚀 **Scan QR To Login**\n\n"
            "Telegram → Settings → Devices → Link Desktop Device\n\n"
            "⏳ Expires in 30 seconds."
        )
    )

    # Wait for Scan
    success = False

    for _ in range(20):  # ~60 seconds
        await asyncio.sleep(3)
        try:
            result = await app.invoke(
                ImportLoginToken(token=login_token)
            )

            if isinstance(result, LoginTokenSuccess):
                success = True
                break

            elif isinstance(result, LoginTokenMigrateTo):
                await app.disconnect()
                app = Client(
                    name="qr_temp",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    in_memory=True,
                    dc_id=result.dc_id
                )
                await app.connect()

        except Exception:
            continue

    # If QR Expired
    if not success:
        await qr_message.delete()
        await app.disconnect()
        return "EXPIRED"

    # 2FA Handling
    try:
        me = await app.get_me()
    except SessionPasswordNeeded:
        return "PASSWORD_REQUIRED", app, qr_message

    # Export Session
    session_string = await app.export_session_string()

    # Save Session To Saved Messages
    await app.send_message(
        "me",
        f"🔐 **Your Pyrogram String Session**\n\n"
        f"`{session_string}`\n\n"
        f"⚠️ Keep this safe."
    )

    await qr_message.delete()
    await app.disconnect()

    return "SUCCESS", me
