"""
Start handler - Welcome new users
NO SUBSCRIPTIONS - 100% FREE
"""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from datetime import datetime
import database
from keyboards import get_main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command - Simple welcome for free bot"""
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Check if user exists
    user = await database.get_user(telegram_id)
    
    if user:
        # Existing user - Simple welcome back
        await message.answer(
            f"👋 Welcome back, {first_name}!\n\n"
            f"🎉 LaunchBot - 100% FREE Forever\n\n"
            f"Your ultimate crypto & meme coin tracker:\n"
            f"✅ Unlimited watchlist\n"
            f"✅ AI-powered analysis\n"
            f"✅ Smart alerts\n"
            f"✅ Portfolio tracking\n"
            f"✅ Real-time DEX data\n\n"
            f"Choose an option below to get started:",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )
    else:
        # New user - Create account and show welcome
        await database.create_user(telegram_id, username)
        
        await message.answer(
            f"🎉 Welcome to LaunchBot, {first_name}!\n\n"
            f"Your FREE crypto intelligence assistant 🚀\n\n"
            f"What You Get:\n"
            f"💎 Track unlimited coins\n"
            f"🔥 Meme coin risk detector\n"
            f"🤖 AI-powered scoring (Hugging Face)\n"
            f"📊 Real-time DEX data\n"
            f"🔔 Smart price alerts\n"
            f"💰 Portfolio tracking\n"
            f"📈 Market sentiment analysis\n\n"
            f"100% Free. No Trials. No Limits.\n\n"
            f"Tap a button below to start:",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="Markdown"
        )