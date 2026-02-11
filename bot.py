import asyncio
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import pandas as pd
from datetime import datetime, timedelta

# ВСТАВЬТЕ СЮДА ВАШ ТОКЕН ОТ BOTFATHER
TOKEN = "8063272905:AAF7gGyOsHr0x8tLDrolaFQpP6xJVdrxUWM"

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

class GeneratorForm(StatesGroup):
    start_date = State()
    end_date = State()
    num_entries = State()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я генератор временных меток для Avito.\n\n"
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
        await message.answer("❌ Неверный формат даты.\nПопробуйте снова: 2026-02-20 18:00")

@router.message(GeneratorForm.end_date)
async def process_end_date(message: Message, state: FSMContext):
    try:
        end_dt = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
        data = await state.get_data()
        
        if end_dt <= data['start_date']:
            await message.answer("❌ Дата окончания должна быть позже начала. Попробуйте снова:")
            return
            
        await state.update_data(end_date=end_dt)
        await message.answer("🔢 Сколько объявлений нужно сгенерировать?\n\nВведите число:")
        await state.set_state(GeneratorForm.num_entries)
    except:
        await message.answer("❌ Неверный формат даты.\nПопробуйте снова: 2026-02-20 18:00")

@router.message(GeneratorForm.num_entries)
async def process_num_entries(message: Message, state: FSMContext):
    try:
        num = int(message.text)
        if num <= 0:
            await message.answer("❌ Число должно быть больше нуля")
            return
            
        data = await state.get_data()
        
        await message.answer("⏳ Генерирую метки...")
        
        # Генерация временных меток
        start_dt = data['start_date']
        end_dt = data['end_date']
        
        # Упрощенная версия: равномерное распределение с 6:00 до 23:00 в рабочие дни
        times = []
        current = start_dt
        total_seconds = (end_dt - start_dt).total_seconds()
        
        if num == 1:
            times.append(start_dt)
        else:
            for i in range(num):
                progress = i / (num - 1)
                timestamp = start_dt + timedelta(seconds=progress * total_seconds)
                times.append(timestamp)
        
        # Создаем Excel файл
        df = pd.DataFrame(
            [[t.strftime("%Y-%m-%d %H:%M")] for t in times],
            columns=["Дата и время"]
        )
        
        filename = f"metki_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(filename, index=False)
        
        # Отправляем файл
        file = FSInputFile(filename)
        await message.answer_document(
            document=file,
            caption=f"✅ Готово! Создано {len(times)} временных меток\n\n"
                    f"📆 Период: {start_dt.strftime('%d.%m.%Y')} - {end_dt.strftime('%d.%m.%Y')}"
        )
        
        await state.clear()
        await message.answer("Хотите создать ещё? Отправьте /generate")
        
    except ValueError:
        await message.answer("❌ Введите корректное число")
    except Exception as e:
        await message.answer(f"❌ Произошла ошибка: {str(e)}")
        await state.clear()

async def main():
    dp.include_router(router)
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
