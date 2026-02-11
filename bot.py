import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import pandas as pd
from datetime import datetime, timedelta
import os

TOKEN = os.getenv("BOT_TOKEN", "8063272905:AAF7gGyOsHr0x8tLDrolaFQpP6xJVdrxUWM")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

class GeneratorForm(StatesGroup):
    start_date = State()
    end_date = State()
    work_days = State()
    work_hours = State()
    num_entries = State()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я генератор временных меток для Avito.\n\n"
        "✨ Возможности:\n"
        "• Выбор периода публикаций\n"
        "• Настройка рабочих дней\n"
        "• Настройка рабочих часов\n"
        "• Генерация Excel-файла\n\n"
        "📝 Отправь /generate чтобы начать"
    )

@router.message(Command("generate"))
async def start_generation(message: Message, state: FSMContext):
    await message.answer(
        "📅 Введите дату и время начала\n"
        "Формат: ГГГГ-ММ-ДД ЧЧ:ММ\n\n"
        "Пример: 2026-02-12 09:00"
    )
    await state.set_state(GeneratorForm.start_date)

@router.message(GeneratorForm.start_date)
async def process_start_date(message: Message, state: FSMContext):
    try:
        start_dt = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
        await state.update_data(start_date=start_dt)
        await message.answer(
            "📅 Теперь дату и время окончания\n"
            "Формат: ГГГГ-ММ-ДД ЧЧ:ММ\n\n"
            "Пример: 2026-02-20 18:00"
        )
        await state.set_state(GeneratorForm.end_date)
    except:
        await message.answer("❌ Неверный формат даты.\nПопробуйте снова: 2026-02-12 09:00")

@router.message(GeneratorForm.end_date)
async def process_end_date(message: Message, state: FSMContext):
    try:
        end_dt = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
        data = await state.get_data()
        
        if end_dt <= data['start_date']:
            await message.answer("❌ Дата окончания должна быть позже начала. Попробуйте снова:")
            return
            
        await state.update_data(end_date=end_dt, selected_days=set())
        
        # Клавиатура для выбора дней недели
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Пн", callback_data="day_0"),
                InlineKeyboardButton(text="Вт", callback_data="day_1"),
                InlineKeyboardButton(text="Ср", callback_data="day_2"),
                InlineKeyboardButton(text="Чт", callback_data="day_3")
            ],
            [
                InlineKeyboardButton(text="Пт", callback_data="day_4"),
                InlineKeyboardButton(text="Сб", callback_data="day_5"),
                InlineKeyboardButton(text="Вс", callback_data="day_6")
            ],
            [
                InlineKeyboardButton(text="✅ Все дни", callback_data="all_days")
            ],
            [
                InlineKeyboardButton(text="➡️ Далее", callback_data="days_done")
            ]
        ])
        
        await message.answer(
            "📆 Выберите рабочие дни недели:\n"
            "Нажимайте на кнопки, чтобы выбрать/убрать дни\n\n"
            "Выбрано: нет",
            reply_markup=keyboard
        )
        await state.set_state(GeneratorForm.work_days)
    except:
        await message.answer("❌ Неверный формат даты.\nПопробуйте снова: 2026-02-20 18:00")

@router.callback_query(F.data.startswith("day_"), GeneratorForm.work_days)
async def toggle_day(callback: CallbackQuery, state: FSMContext):
    day = int(callback.data.split("_")[1])
    data = await state.get_data()
    selected_days = data.get("selected_days", set())
    
    if day in selected_days:
        selected_days.remove(day)
    else:
        selected_days.add(day)
    
    await state.update_data(selected_days=selected_days)
    
    # Обновляем текст сообщения
    days_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    selected_names = [days_names[d] for d in sorted(selected_days)]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"{'✅' if 0 in selected_days else ''}Пн", callback_data="day_0"),
            InlineKeyboardButton(text=f"{'✅' if 1 in selected_days else ''}Вт", callback_data="day_1"),
            InlineKeyboardButton(text=f"{'✅' if 2 in selected_days else ''}Ср", callback_data="day_2"),
            InlineKeyboardButton(text=f"{'✅' if 3 in selected_days else ''}Чт", callback_data="day_3")
        
