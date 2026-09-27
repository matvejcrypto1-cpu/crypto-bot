from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user_lang, set_user_lang
from texts import TEXTS

router = Router()

def get_lang_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(text="English 🇬🇧", callback_data="lang_en"),
            InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang_ru")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_main_menu_keyboard(lang: str):
    t = TEXTS.get(lang, TEXTS['en'])
    keyboard = [
        [InlineKeyboardButton(text=t['btn_item1'], callback_data="menu_item1")],
        [InlineKeyboardButton(text=t['btn_item2'], callback_data="menu_item2")],
        [InlineKeyboardButton(text=t['btn_about'], callback_data="menu_about")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_back_keyboard(lang: str):
    t = TEXTS.get(lang, TEXTS['en'])
    keyboard = [
        [InlineKeyboardButton(text=t['btn_back'], callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.message(Command("start"))
async def cmd_start(message: Message):
    lang = get_user_lang(message.from_user.id)
    t = TEXTS.get(lang, TEXTS['en'])
    await message.answer(t['choose_lang'], reply_markup=get_lang_keyboard())

@router.callback_query(F.data.startswith("lang_"))
async def process_lang_selection(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    set_user_lang(callback.from_user.id, lang)
    t = TEXTS.get(lang, TEXTS['en'])
    
    await callback.message.edit_text(t['lang_set'])
    await callback.message.answer(t['main_menu'], reply_markup=get_main_menu_keyboard(lang))
    await callback.answer()

@router.callback_query(F.data == "menu_main")
async def process_main_menu(callback: CallbackQuery):
    lang = get_user_lang(callback.from_user.id)
    t = TEXTS.get(lang, TEXTS['en'])
    
    await callback.message.edit_text(t['main_menu'], reply_markup=get_main_menu_keyboard(lang))
    await callback.answer()

@router.callback_query(F.data.startswith("menu_"))
async def process_menu_items(callback: CallbackQuery):
    item = callback.data.split("_")[1]
    lang = get_user_lang(callback.from_user.id)
    t = TEXTS.get(lang, TEXTS['en'])
    
    text_key = f'text_{item}'
    text = t.get(text_key, "Text not found.")
    
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(lang))
    await callback.answer()
