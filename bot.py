import asyncio
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
import pandas as pd
from datetime import datetime, timedelta
import os

TOKEN = "8063272905:AAF7gGyOsHr0x8tLDrolaFQpP6xJVdrxUWM"
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()

class Gen(StatesGroup):
    start = State()
    end = State()
    days = State()
    hours = State()
    count = State()

@router.message(CommandStart())
async def start(m: Message):
    await m.answer("Привет! Отправь /generate")

@router.message(Command("generate"))
async def gen(m: Message, state: FSMContext):
    await m.answer("Введите дату начала (2026-02-12 09:00):")
    await state.set_state(Gen.start)

@router.message(Gen.start)
async def get_start(m: Message, state: FSMContext):
    try:
        dt = datetime.strptime(m.text, "%Y-%m-%d %H:%M")
        await state.update_data(start=dt)
        await m.answer("Введите дату окончания (2026-02-20 18:00):")
        await state.set_state(Gen.end)
    except:
        await m.answer("Ошибка! Пример: 2026-02-12 09:00")

@router.message(Gen.end)
async def get_end(m: Message, state: FSMContext):
    try:
        dt = datetime.strptime(m.text, "%Y-%m-%d %H:%M")
        await state.update_data(end=dt)
        await m.answer("Введите рабочие дни через запятую\nПример: 0,1,2,3,4 (0=Пн, 6=Вс)\nИли 0,1,2,3,4,5,6 для всех дней")
        await state.set_state(Gen.days)
    except:
        await m.answer("Ошибка! Пример: 2026-02-20 18:00")

@router.message(Gen.days)
async def get_days(m: Message, state: FSMContext):
    try:
        days = [int(x.strip()) for x in m.text.split(",")]
        await state.update_data(days=days)
        await m.answer("Введите рабочие часы\nПример: 6-23")
        await state.set_state(Gen.hours)
    except:
        await m.answer("Ошибка! Пример: 0,1,2,3,4")

@router.message(Gen.hours)
async def get_hours(m: Message, state: FSMContext):
    try:
        h = m.text.split("-")
        await state.update_data(h_start=int(h[0]), h_end=int(h[1]))
        await m.answer("Сколько объявлений?")
        await state.set_state(Gen.count)
    except:
        await m.answer("Ошибка! Пример: 6-23")

@router.message(Gen.count)
async def make_file(m: Message, state: FSMContext):
    try:
        num = int(m.text)
        data = await state.get_data()
        await m.answer("Генерирую...")
        
        times = gen_times(data['start'], data['end'], data['days'], 
                         (data['h_start'], data['h_end']), num)
        
        df = pd.DataFrame([[t.strftime("%Y-%m-%d %H:%M")] for t in times], 
                         columns=["Дата и время"])
        
        fname = f"metki_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        df.to_excel(fname, index=False)
        
        file = FSInputFile(fname)
        await m.answer_document(document=file, caption=f"Готово! {len(times)} меток")
        os.remove(fname)
        await state.clear()
    except Exception as e:
        await m.answer(f"Ошибка: {e}")
        await state.clear()

def gen_times(start, end, days, hours, count):
    intervals = []
    cur = start.date()
    
    while cur <= end.date():
        if cur.weekday() in days:
            d_start = datetime.combine(cur, datetime.min.time()) + timedelta(hours=hours[0])
            d_end = datetime.combine(cur, datetime.min.time()) + timedelta(hours=hours[1])
            i_start = max(start, d_start)
            i_end = min(end, d_end)
            if i_start < i_end:
                intervals.append((i_start, i_end))
        cur += timedelta(days=1)
    
    if not intervals:
        return []
    
    total = sum((e - s).total_seconds() for s, e in intervals)
    times = []
    
    if count == 1:
        times.append(start)
    else:
        for i in range(count):
            prog = i / (count - 1)
            target = prog * total
            acc = 0
            for s, e in intervals:
                dur = (e - s).total_seconds()
                if acc + dur >= target:
                    times.append(s + timedelta(seconds=(target - acc)))
                    break
                acc += dur
    
    return times

async def main():
    dp.include_router(router)
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
