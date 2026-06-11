import os
import httpx
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from storage import history, save_history
from sound_to_text import transcribe

FLASK_URL = "http://132.68.34.90:5000/api/ask"


# ---------------------------
# TEXT + VOICE STORAGE + AI
# ---------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    user_id = str(msg.from_user.id)

    # 1. Save history locally
    entry = {
        "type": "text",
        "text": msg.text,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    history.setdefault(user_id, []).append(entry)
    save_history(history)

    # 2. Send to Flask AI backend
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                FLASK_URL,
                json={"message": msg.text}
            )

        if response.status_code != 200:
            await msg.reply_text("Server error. Please try again later.")
            return

        data = response.json()
        answer = data.get("response", "No response from server.")

    except Exception as e:
        await msg.reply_text(f"Connection error: {str(e)}")
        return

    # 3. Reply to user
    await msg.reply_text(answer)


# ---------------------------
# VOICE STORAGE (unchanged)
# ---------------------------

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.voice:
        return

    user_id = str(msg.from_user.id)

    file = await msg.voice.get_file()

    os.makedirs("audio", exist_ok=True)

    filename = f"audio/{user_id}_{len(history.get(user_id, []))}.ogg"
    await file.download_to_drive(filename)

    entry = {
        "type": "voice",
        "file_id": msg.voice.file_id,
        "file_path": filename,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    history.setdefault(user_id, []).append(entry)
    save_history(history)

    await msg.reply_text("Voice saved.")

    transcribed_voice_message = transcribe(filename)
    await msg.reply_text(transcribed_voice_message["text"])


# ---------------------------
# BASIC COMMANDS (unchanged)
# ---------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "FindMyPatient Bot helps hospital staff quickly locate patients and manage information "
        "during emergency situations involving multiple casualties.\n\n"
        "Start typing or send a voice message to get started."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start /help /menu /texthistory /audiohistory")


# ---------------------------
# HISTORY (unchanged)
# ---------------------------

async def texthistory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    msgs = history.get(user_id, [])

    if not msgs:
        await update.message.reply_text("No history.")
        return

    text_msgs = []
    voice_msgs = []

    for i, m in enumerate(msgs, 1):
        mtype = m.get("type", "text")

        if mtype == "text":
            text_msgs.append(f"{i}. {m.get('text', '')}")
        elif mtype == "voice":
            voice_msgs.append(f"{i}. 🎤 voice")

    output = []

    if text_msgs:
        output.append("TEXT:\n" + "\n".join(text_msgs[-20:]))

    if voice_msgs:
        output.append("\nVOICE:\n" + "\n".join(voice_msgs[-10:]))

    await update.message.reply_text("\n".join(output))


async def audiohistory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    msgs = history.get(user_id, [])

    voices = [m for m in msgs if m.get("type") == "voice"]

    if not voices:
        await update.message.reply_text("No voice history.")
        return

    await update.message.reply_text(f"Sending {len(voices)} voice messages...")

    for v in voices:
        file_path = v.get("file_path")
        if file_path and os.path.exists(file_path):
            await update.message.reply_voice(voice=open(file_path, "rb"))


# ---------------------------
# DELETE SYSTEM (unchanged)
# ---------------------------

async def clearlastentry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    if not history.get(user_id):
        await update.message.reply_text("Nothing to delete.")
        return

    removed = history[user_id].pop()
    save_history(history)

    await update.message.reply_text(f"Deleted: {removed['type']}")


async def clearhistory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    history[user_id] = []
    save_history(history)

    await update.message.reply_text("History cleared.")


async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    if not context.args:
        await update.message.reply_text("Usage: /delete 3")
        return

    try:
        index = int(context.args[0]) - 1
    except:
        await update.message.reply_text("Invalid number")
        return

    if index < 0 or index >= len(history.get(user_id, [])):
        await update.message.reply_text("Out of range")
        return

    removed = history[user_id].pop(index)
    save_history(history)

    await update.message.reply_text(f"Deleted: {removed['type']}")


# ---------------------------
# VOICE PLAYBACK (unchanged)
# ---------------------------

def get_last_voice(user_id: str):
    msgs = history.get(user_id, [])
    for m in reversed(msgs):
        if m.get("type") == "voice":
            return m
    return None


async def playlastvoice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)

    voice = get_last_voice(user_id)

    if not voice:
        await update.message.reply_text("No voice found.")
        return

    await update.message.reply_voice(open(voice["file_path"], "rb"))
