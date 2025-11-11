"""
Donation handler - Allow users to support development
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import os
from config import BOT_TOKEN

router = Router()

# Get donation settings from environment
DONATION_WALLET_USDT = os.getenv('DONATION_WALLET_USDT', '')
DONATION_WALLET_NETWORK = os.getenv('DONATION_WALLET_NETWORK', 'TRC20')
SHOW_DONATION_MESSAGE = os.getenv('SHOW_DONATION_MESSAGE', 'true').lower() == 'true'
DONATION_MESSAGE = os.getenv('DONATION_MESSAGE', 'Support free crypto tools! Donate USDT to help us build more. 💙')


def get_donation_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for donation options"""
    keyboard = [
        [InlineKeyboardButton(text="💰 View Wallet Address", callback_data="show_wallet")],
        [InlineKeyboardButton(text="❤️ Why Donate?", callback_data="why_donate")],
        [InlineKeyboardButton(text="🔙 Back to Settings", callback_data="settings_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.message(F.text == "💙 Support Us")
async def donation_info(message: Message):
    """Show donation information"""
    if not SHOW_DONATION_MESSAGE or not DONATION_WALLET_USDT:
        await message.answer(
            "💙 Thank you for your support!\n\n"
            "This bot is 100% free and will always be free.\n\n"
            "Spread the word to help other traders! 🚀",
            parse_mode="Markdown"
        )
        return
    
    msg = (
        "💙 Support Free Crypto Tools\n\n"
        f"{DONATION_MESSAGE}\n\n"
        "Why donate?\n"
        "• Keep this bot 100% free forever\n"
        "• Help us add more features\n"
        "• Support new free tools development\n"
        "• Server & API costs\n\n"
        "Your donation helps:\n"
        "✅ More AI features\n"
        "✅ Better meme coin detection\n"
        "✅ Real-time DEX data\n"
        "✅ New free bots for the community\n\n"
        "Every USDT counts! 💪"
    )
    
    await message.answer(
        msg,
        reply_markup=get_donation_keyboard(),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "show_wallet")
async def show_wallet_address(callback: CallbackQuery):
    """Show USDT wallet address"""
    if not DONATION_WALLET_USDT:
        await callback.answer("❌ Donation wallet not configured", show_alert=True)
        return
    
    msg = (
        "💰 Donation Wallet Address\n\n"
        f"Network: {DONATION_WALLET_NETWORK}\n"
        f"Token: USDT\n\n"
        f"Address:\n"
        f"`{DONATION_WALLET_USDT}`\n\n"
        "How to donate:\n"
        "1. Copy the address above\n"
        "2. Open your crypto wallet\n"
        "3. Send USDT to this address\n"
        f"4. Make sure you select {DONATION_WALLET_NETWORK} network!\n\n"
        "⚠️ Important:\n"
        f"• Only send USDT on {DONATION_WALLET_NETWORK}\n"
        "• Double-check the address before sending\n"
        "• Any amount is appreciated!\n\n"
        "Thank you for supporting free tools! 🙏"
    )
    
    await callback.message.edit_text(
        msg,
        reply_markup=get_donation_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "why_donate")
async def why_donate_info(callback: CallbackQuery):
    """Explain why donations help"""
    msg = (
        "❤️ Why Your Donation Matters\n\n"
        "This bot is 100% FREE because:\n"
        "We believe crypto tools should be accessible to everyone, "
        "not just those who can afford expensive subscriptions.\n\n"
        "But running it costs money:\n"
        "💸 Server hosting ($7-25/month)\n"
        "💸 API calls (CoinGecko, DexScreener)\n"
        "💸 Database storage\n"
        "💸 Development time\n\n"
        "Your donation helps us:\n"
        "✅ Keep this bot free forever\n"
        "✅ Add more features (rug pull AI, whale tracking)\n"
        "✅ Build NEW free tools for the community\n"
        "✅ Support other developers building free tools\n\n"
        "Our Promise:\n"
        "• This bot will NEVER have paid features\n"
        "• 100% of donations go to development\n"
        "• We're building a suite of free crypto tools\n\n"
        "Even $1 helps keep the servers running! 💙\n\n"
        "No donation? No problem!\n"
        "Share the bot with friends - that helps too! 🚀"
    )
    
    await callback.message.edit_text(
        msg,
        reply_markup=get_donation_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "donate_menu")
async def donate_menu_callback(callback: CallbackQuery):
    """Return to donation menu"""
    await donation_info(callback.message)
    await callback.answer()


# Add donation reminder to certain bot responses
def get_donation_footer() -> str:
    """Get donation footer text for messages"""
    if not SHOW_DONATION_MESSAGE or not DONATION_WALLET_USDT:
        return ""
    
    return "\n\n💙 _Enjoying the bot? Consider donating to support free crypto tools!_"


# Helper function to check if donations are enabled
def donations_enabled() -> bool:
    """Check if donation feature is enabled"""
    return SHOW_DONATION_MESSAGE and bool(DONATION_WALLET_USDT)