import os
from dotenv import load_dotenv

# .env file ဖတ်ခြင်း
load_dotenv()

"""
IT Helpdesk Telegram Bot (Groq အခမဲ့ AI ဖြင့်)
မြန်မာလို ဖြေကြားပေးသည်
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from telegram.request import HTTPXRequest
from openai import OpenAI

# ============================================
# 🔑 API Keys များကို .env မှ ဖတ်ခြင်း
# ============================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Key များ ရှိမရှိ စစ်ဆေးခြင်း
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN မရှိပါ။ .env file ကို စစ်ပါ။")
if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY မရှိပါ။ .env file ကို စစ်ပါ။")

# ============================================
# 📞 Admin ဆက်သွယ်ရန် အချက်အလက်
# ဒီနေရာမှာ သင့် Admin အချက်အလက်ကို ပြင်ပါ
# ============================================
ADMIN_CONTACT = """

━━━━━━━━━━━━━━━━━━
📞 **ထပ်ဆောင်း အကူအညီ လိုအပ်ပါက**

👤 Admin:name
📱 Phone: 09-xxxxxxxxx
💬 Telegram: @xxxxx
📧 Email: xxxxx
🕐 အချိန်: ၉:၀၀ နာရီ - ၁၇:၀၀ နာရီ အတွင်း
━━━━━━━━━━━━━━━━━━"""
# ============================================

# Groq Client - OpenAI SDK ကို base_url ပြောင်းပြီး အသုံးပြုသည်
client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

# အသုံးပြုမည့် Model
MODEL_NAME = "openai/gpt-oss-120b"

# System Prompt - မြန်မာလို IT Helpdesk
SYSTEM_PROMPT = """သင်သည် ကျွမ်းကျင်သော IT Helpdesk Assistant တစ်ဦးဖြစ်သည်။
အသုံးပြုသူများ၏ IT ပြဿနာများကို မြန်မာဘာသာဖြင့် ကူညီဖြေရှင်းပေးပါ။

ဖြေကြားရာတွင် လိုက်နာရမည့် အချက်များ:
1. အမြဲတမ်း မြန်မာလိုဖြေပါ။
2. တိုတိုနှင့်လိုရင်းနှင့်တိတိကျကျဖြေပေးပါ
3. နည်းပညာဝေါဟာရများကို မြန်မာလို ရှင်းပြပါ။
4. ဖော်ရွေစွာ၊ ကူညီလိုစိတ်ဖြင့် ဖြေပါ။
5. Command များကို code block ဖြင့် ပြပါ။
6. မသေချာရင် ထပ်မေးပါ။
7. အဖြေမပေးနိုင်ရင် အကြံပြုချက်ပေးပါ။

ကူညီနိုင်သော အကြောင်းအရာများ:
- ကွန်ပျူတာ၊ Laptop ပြဿနာများ
- WiFi၊ Internet ပြဿနာများ
- Printer၊ Scanner ချိတ်ဆက်ခြင်း
- Email၊ Password၊ Account ပြဿနာများ
- Software Install / Error ဖြေရှင်းခြင်း
- Virus၊ Malware ကာကွယ်ခြင်း
"""

# User တစ်ဦးချင်းစီ၏ စကားပြောမှတ်တမ်း
chat_history = {}


def get_ai_reply(user_id, message):
    """Groq မှ ဖြေကြားချက်ရယူခြင်း + Admin info ပေါင်းထည့်ခြင်း"""
    # History စတင်ခြင်း
    if user_id not in chat_history:
        chat_history[user_id] = []

    # User message ထည့်ခြင်း
    chat_history[user_id].append({"role": "user", "content": message})

    # နောက်ဆုံး 20 ခုသာ သိမ်းခြင်း
    if len(chat_history[user_id]) > 20:
        chat_history[user_id] = chat_history[user_id][-20:]

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}]
            + chat_history[user_id],
            temperature=0.7,
            max_tokens=1500,
        )
        ai_reply = response.choices[0].message.content

        # ✅ AI reply (Admin info မပါ) ကို history ထဲ သိမ်းခြင်း
        # ဒါမှ နောက်တစ်ခါ AI က Admin info ကို ထပ်မထည့်မိမှာ
        chat_history[user_id].append({"role": "assistant", "content": ai_reply})

        # ✅ User ကို ပြသရာမှာ Admin info ပေါင်းထည့်ခြင်း
        final_reply = ai_reply + ADMIN_CONTACT
        return final_reply

    except Exception as e:
        error_msg = str(e)
        # Rate limit error ဖြစ်ရင် သတိပေးချက်
        if "429" in error_msg or "rate" in error_msg.lower():
            return (
                "⚠️ အခမဲ့ အသုံးပြုမှု ကန့်သတ်ချက် ပြည့်သွားပါပြီ။\n"
                "ခဏနေမှ ထပ်မံ ကြိုးစားပါ။"
                + ADMIN_CONTACT
            )
        return (
            f"⚠️ Error ဖြစ်သွားပါသည်:\n{error_msg}\n\nခဏနေမှ ထပ်ကြိုးစားပါ။"
            + ADMIN_CONTACT
        )


# ============================================
# Command Handlers
# ============================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """'/start' command"""
    name = update.effective_user.first_name or "သူငယ်ချင်း"

    text = f"""👋 မင်္ဂလာပါ {name}！

🤖 ကျွန်တော်က IT Helpdesk AI Assistant ပါ။
IT ပြဿနာတွေကို ကူညီဖြေရှင်းပေးပါမယ်ခင်ဗျ

📌 **ကူညီနိုင်တဲ့ အကြောင်းအရာများ:**
• 💻 ကွန်ပျူတာ / Laptop ပြဿနာ
• 🌐 WiFi / Internet ပြဿနာ
• 🖨️ Printer / Scanner
• 📧 Email / Password
• 🛠️ Software Install / Error

💬 သင့်ပြဿနာကို ရေးပို့လိုက်ရုံပါပဲ။

**Commands:**
/start - ပြန်စတင်ရန်
/help - အကူအညီ
/clear - မှတ်တမ်းရှင်းရန်"""

    keyboard = [
        [InlineKeyboardButton("💻 ကွန်ပျူတာ ပြဿနာ", callback_data="pc")],
        [InlineKeyboardButton("🌐 WiFi ပြဿနာ", callback_data="wifi")],
        [InlineKeyboardButton("🖨️ Printer ပြဿနာ", callback_data="printer")],
        [InlineKeyboardButton("📧 Email ပြဿနာ", callback_data="email")],
    ]
    markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """'/help' command"""
    text = """📖 **အကူအညီ**

သင့်ပြဿနာကို ရိုးရိုးရှင်းရှင်း ရေးပို့ပါ။ ဥပမာ:

• "WiFi မချိတ်ဘူး ဘယ်လိုလုပ်ရမလဲ?"
• "Printer က စာမထုတ်ဘူး"
• "Email password မေ့သွားတယ်"
• "ကွန်ပျူတာ နှေးနေတယ်"

**Commands:**
/start - ပြန်စတင်ရန်
/help - ဒီအကူအညီ
/clear - စကားပြောမှတ်တမ်း ရှင်းရန်"""

    await update.message.reply_text(text, parse_mode="Markdown")


async def clear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """'/clear' command"""
    user_id = update.effective_user.id
    if user_id in chat_history:
        del chat_history[user_id]
    await update.message.reply_text("✅ မှတ်တမ်း ရှင်းလင်းပြီးပါပြီ။ အသစ်ပြန်စနိုင်ပါပြီ။")


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline button နှိပ်ခြင်း"""
    query = update.callback_query
    await query.answer()

    messages = {
        "pc": "💻 ကွန်ပျူတာ ပြဿနာအကြောင်း ရေးပို့ပါ။\nဥပမာ - ကွန်ပျူတာနှေးတယ်၊ Blue Screen တက်တယ်",
        "wifi": "🌐 WiFi ပြဿနာအကြောင်း ရေးပို့ပါ။\nဥပမာ - WiFi မချိတ်ဘူး၊ Internet မရဘူး",
        "printer": "🖨️ Printer ပြဿနာအကြောင်း ရေးပို့ပါ။\nဥပမာ - စာမထုတ်ဘူး၊ Offline ဖြစ်နေတယ်",
        "email": "📧 Email ပြဿနာအကြောင်း ရေးပို့ပါ။\nဥပမာ - Login မဝင်နိုင်ဘူး၊ Password မေ့သွားတယ်",
    }
    await query.message.reply_text(messages.get(query.data, "သင့်ပြဿနာကို ရေးပို့ပါ။"))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """စာသား လက်ခံခြင်း"""
    user_id = update.effective_user.id
    message = update.message.text

    # Typing ပြခြင်း
    await update.message.chat.send_action(action="typing")

    # စဉ်းစားနေသည် ဆိုတဲ့ message ပြခြင်း
    wait_msg = await update.message.reply_text("🤔 စဉ်းစားနေပါသည်...")

    # AI မှ ဖြေကြားချက်ရယူခြင်း (Admin info ပါပြီးသား)
    reply = get_ai_reply(user_id, message)

    # ဖြေကြားချက် ပြသခြင်း
    try:
        await wait_msg.edit_text(reply, parse_mode="Markdown")
    except Exception:
        # Markdown error ဖြစ်ရင် plain text နဲ့ ပြန်ပို့
        await wait_msg.edit_text(reply)


# ============================================
# Main - Bot စတင်ခြင်း
# ============================================

def main():
    print("🤖 IT Helpdesk Bot (Groq) စတင်နေပါသည်...")

    # Token စစ်ဆေးခြင်း
    if "သင့်_" in TELEGRAM_BOT_TOKEN:
        print("❌ ERROR: Telegram Bot Token ကို ထည့်ပါဦး။")
        return
    if "gsk_သင့်_" in GROQ_API_KEY:
        print("❌ ERROR: Groq API Key ကို ထည့်ပါဦး။")
        return

    # ==== Telegram connection ပြတ်တောက်မှု ကာကွယ်ရန် ====
    # Polling အတွက် သီးသန့် request object
    get_updates_request = HTTPXRequest(
        connection_pool_size=1,
        read_timeout=60.0,
        connect_timeout=15.0,
    )

    # API call များအတွက် သီးသန့် request object
    api_request = HTTPXRequest(
        connection_pool_size=8,
        read_timeout=30.0,
        connect_timeout=10.0,
    )

    # Bot Application ဖန်တီးခြင်း
    app = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .request(api_request)
        .get_updates_request(get_updates_request)
        .build()
    )
    # =====================================================

    # Handlers များ ထည့်ခြင်း
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("clear", clear_cmd))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot အဆင်သင့်ဖြစ်ပါပြီ！")
    print("📱 Telegram မှာ သင့် Bot ကို /start ပို့ကြည့်ပါ။")
    print("⏹️ ရပ်ရန် Ctrl+C ကို နှိပ်ပါ။\n")

    # Bot စတင်ခြင်း
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()