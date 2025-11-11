from aiogram import Dispatcher

from .start import register_handlers as start_register
from .menu import register_handlers as menu_register

def register_all_handlers(dp: Dispatcher):
    start_register(dp)
    menu_register(dp)
