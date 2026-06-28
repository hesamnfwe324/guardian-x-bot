from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
import structlog

logger = structlog.get_logger()
router = Router()


HELP_TEXT = """
📖 <b>راهنمای دستورات ربات</b>
━━━━━━━━━━━━━━━━━━━━━━

💰 <b>اقتصاد</b>
/wallet — موجودی کیف‌پول و بانک
/daily — دریافت جایزه روزانه
/weekly — دریافت جایزه هفتگی
/monthly — دریافت جایزه ماهانه
/deposit — واریز به بانک
/withdraw — برداشت از بانک
/transfer — انتقال سکه به کاربر دیگر
/referral — لینک دعوت
/achievements — دستاوردهای من

🎮 <b>بازی‌ها</b>
/dice — بازی تاس
/rps — سنگ کاغذ قیچی
/quiz — سوال چهارگزینه‌ای
/wheel — چرخ شانس
/numwar — نبرد اعداد
/cards — نبرد کارت
/treasure — شکار گنج
/mines — مین‌یاب
/roulette — رولت

🛡️ <b>امنیت گروه (ادمین)</b>
/security — تنظیمات امنیتی گروه
/lock — قفل کردن نوع پیام
/unlock — باز کردن قفل

🔨 <b>مدیریت گروه (ادمین)</b>
/ban — مسدود کردن کاربر
/unban — رفع مسدودی
/kick — اخراج از گروه
/mute — بی‌صدا کردن
/unmute — رفع بی‌صدایی
/warn — اخطار به کاربر
/unwarn — لغو اخطار
/warns — مشاهده اخطارها
/history — تاریخچه اقدامات

⚙️ <b>تنظیمات گروه (ادمین)</b>
/settings — تنظیمات پیشرفته گروه

ℹ️ <b>سایر</b>
/language — تغییر زبان
/stats — آمار کاربر
/help — نمایش این راهنما
━━━━━━━━━━━━━━━━━━━━━━
"""


@router.message(Command('help'))
async def cmd_help(message: Message, _: callable, **kwargs):
    await message.answer(HELP_TEXT, parse_mode='HTML')
