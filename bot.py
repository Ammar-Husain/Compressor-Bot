import asyncio
import os
import tempfile
from threading import Thread

import dotenv
import requests
from flask import Flask
from pyrogram import Client, filters

from config import *

dotenv.load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SERVICE_URL = os.getenv("SERVICE_URL")


async def main():
    run_flask()
    app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

    @app.on_message(filters.command("start"))
    async def start(_, message):
        await message.reply("Send me video files, I will compress them for you.")

    @app.on_message(filters.video | filters.animation)
    async def handle_media(client, message):
        await message.reply("Compressing file..", quote=True)

        file = await client.download_media(
            message.video.file_id if message.video else message.animation.file_id
        )

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_filename = temp_file.name

        ffmpeg_cmd = (
            f'ffmpeg -i "{file}" -filter_complex "scale={VIDEO_SCALE}" -r {VIDEO_FPS} '
            f"-c:v {VIDEO_CODEC} -pix_fmt {VIDEO_PIXEL_FORMAT} -b:v {VIDEO_BITRATE} "
            f"-crf {VIDEO_CRF} -preset {VIDEO_PRESET} -c:a {VIDEO_AUDIO_CODEC} "
            f"-b:a {VIDEO_AUDIO_BITRATE} -ac {VIDEO_AUDIO_CHANNELS} "
            f'-ar {VIDEO_AUDIO_SAMPLE_RATE} -profile:v {VIDEO_PROFILE} -map_metadata -1 -y "{temp_filename}"'
        )

        process = await asyncio.create_subprocess_shell(ffmpeg_cmd)
        await process.wait()

        if os.path.exists(file):
            os.remove(file)

        await message.reply_video(
            temp_filename,
            caption=message.caption,
            duration=message.video.duration if message.video else None,
            width=message.video.width if message.video else None,
            height=message.video.height if message.video else None,
            quote=True,
        )
        os.remove(temp_filename)

    print("Bot started succefully")
    await keep_up()


def run_flask():
    server = Flask(__name__)

    @server.route("/", methods=["GET"])
    def greet():
        print("Request")
        return "Compressor Bot is UP"

    def flask_thread():
        server.run("0.0.0.0", port=8000)
        print("Server runs succefully")

    thread = Thread(target=flask_thread)
    thread.start()
    return True


async def ping_server():
    if SERVICE_URL:
        res = requests.get(SERVICE_URL)
        print(res.text)
        return res.text
    else:
        print(
            "Warning: $SERVICE_URL is not set, the service can sleep at anytime.",
        )


async def keep_up():
    while True:
        try:
            await asyncio.sleep(60)
            await ping_server()
        except Exception as e:
            print(e)


if __name__ == "__main__":
    run_flask()
    asyncio.get_event_loop().run_until_complete(main())
