import os
from dotenv import load_dotenv

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters
)

from handlers import (
    start,
    help_cmd,
    texthistory,
    audiohistory,
    handle_message,
    handle_voice,
    clearlastentry,
    clearhistory,
    delete,
    playlastvoice
)

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("texthistory", texthistory))
    app.add_handler(CommandHandler("audiohistory", audiohistory))
    app.add_handler(CommandHandler("clearlastentry", clearlastentry))
    app.add_handler(CommandHandler("clearhistory", clearhistory))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(CommandHandler("playlastvoice", playlastvoice))

    # media handlers
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()