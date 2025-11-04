from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
import os, sys, threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- Path setup to access external modules ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Operations.LeadManager.lead_manager import lead_manager

# --- Environment setup ---
load_dotenv()
BOT_USERNAME = os.getenv('BOT_NAME')
TOKEN = os.getenv('TOKEN')
print(f"Bot username: {BOT_USERNAME}, Token: {TOKEN}")

# --- Commands ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("👋 Hello! I am your chatbot. How can I assist you today?")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("💡 I can process leads into structured JSON format. Just send me the details!")

async def process_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = update.message.text
    try:
        response = lead_manager(user_input)  # call your external function
        await update.message.reply_text("✅ Processed Successfully!\n\n" + str(response))
    except Exception as e:
        await update.message.reply_text(f"❌ Error while processing: {e}")

# --- General message handling ---
def handle_response(text: str) -> str:
    text = text.lower()
    if 'hello' in text:
        return "Hello there! How can I help you?"
    elif 'help' in text:
        return "Sure! Try using /process followed by your lead details."
    return "I'm not sure I understood that. Can you rephrase?"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_type = update.message.chat.type
    text = update.message.text.strip()
    print(f"User ({update.message.chat.id}) in {message_type} sent: {text}")

    if message_type == 'group' and BOT_USERNAME not in text:
        return  # ignore non-mentions in groups

    response = handle_response(text)
    print("Bot:", response)
    await update.message.reply_text(response)

# --- Error logging ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"⚠️ Update {update} caused error: {context.error}")

# --- Simple keep-alive web server for Render Free Plan ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write("🤖 Telegram bot is running!")

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    print(f"🌐 Keep-alive server running on port {port}")

# --- Entry point ---
if __name__ == "__main__":
    # Start the dummy web server first (for Render)
    keep_alive()

    app = Application.builder().token(TOKEN).build()

    # Command Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("process", process_command))
    
    # Text Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Error Handler
    app.add_error_handler(error_handler)

    print("🤖 Bot is running...")
    app.run_polling(poll_interval=3)
