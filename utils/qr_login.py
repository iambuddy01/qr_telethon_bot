import asyncio
import base64
import qrcode
from io import BytesIO
from pyrogram import Client
from pyrogram.raw.functions.auth import ExportLoginToken, ImportLoginToken
from pyrogram.errors import SessionPasswordNeeded
from config import API_ID, API_HASH


async def generate_qr_session():
    app = Client(
        name="qr_temp",
        api_id=API_ID,
        api_hash=API_HASH,
        in_memory=True
    )

    await app.connect()

    # Step 1: Export login token
    token = await app.invoke(
        ExportLoginToken(api_id=API_ID, api_hash=API_HASH, except_ids=[])
    )

    login_token = token.token
    login_token_b64 = base64.urlsafe_b64encode(login_token).decode()

    qr_url = f"tg://login?token={login_token_b64}"

    # Step 2: Generate QR
    qr = qrcode.make(qr_url)
    qr.show()

    print("\nScan this QR using Telegram → Settings → Devices → Link Desktop Device")
    print("Waiting for scan...\n")

    # Step 3: Wait for scan
    while True:
        await asyncio.sleep(3)
        try:
            result = await app.invoke(
                ImportLoginToken(token=login_token)
            )
            break
        except Exception:
            continue

    # Step 4: Handle 2FA if needed
    try:
        me = await app.get_me()
    except SessionPasswordNeeded:
        password = input("2FA Password: ")
        await app.check_password(password)
        me = await app.get_me()

    # Step 5: Export string session
    string_session = await app.export_session_string()

    print("\n✅ Login Successful!")
    print(f"👤 Name: {me.first_name}")
    print(f"🆔 ID: {me.id}")
    print("\n🔑 STRING SESSION:\n")
    print(string_session)

    await app.disconnect()
