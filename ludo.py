import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ChatType

TOKEN = "8888434497:AAHTgwa8SApty6hSUOJs-yjUPUS3a12JgVo"
ADMIN_ID = 105635005
GROUP_ID = -1004368091214

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ====== НАСТРОЙКИ ======
settings = {
    "timer": 60,
    "price": 1,
    "nft": "https://example.com"
}

# ====== СОСТОЯНИЕ ======
event_active = False
end_time = 0
last_user = None

ignore_list = set()

countdown_task = None
timer_message = None

# ====== UI ======

def progress_bar(seconds):
    total = 10
    filled = seconds
    empty = total - filled
    return "█" * filled + "░" * empty

# ====== СТАРТ ИВЕНТА ======

@dp.message(Command("start_event"))
async def start_event(message: Message):
    global event_active, end_time

    if message.from_user.id != ADMIN_ID:
        return

    if message.chat.id != GROUP_ID:
        return

    event_active = True
    end_time = asyncio.get_event_loop().time() + settings["timer"]

    await message.answer(
        f"🚀 Ивент начался!\n\n"
        f"🎁 Приз: {settings['nft']}\n"
        f"💸 Перебив: {settings['price']}⭐\n"
        f"⏳ Таймер: {settings['timer']} сек"
    )

    asyncio.create_task(timer_loop(message.chat.id))

# ====== ПЕРЕБИВ ======

@dp.message()
async def bid(message: Message):
    global last_user, end_time, countdown_task, timer_message

    if not event_active:
        return

    if message.chat.id != GROUP_ID:
        return

    if message.from_user.id in ignore_list:
        return

    # тут можно добавить оплату stars

    last_user = message.from_user
    end_time = asyncio.get_event_loop().time() + settings["timer"]

    # стопаем countdown
    if countdown_task and not countdown_task.done():
        countdown_task.cancel()
        countdown_task = None

    # удаляем старый таймер
    if timer_message:
        try:
            await timer_message.delete()
        except:
            pass
        timer_message = None

    await message.answer(f"💥 Перебив от @{message.from_user.username}")

# ====== ТАЙМЕР ======

async def timer_loop(chat_id):
    global event_active, countdown_task

    warned30 = False

    while event_active:
        now = asyncio.get_event_loop().time()
        remaining = int(end_time - now)

        if remaining <= 0:
            await finish(chat_id)
            return

        if remaining <= 30 and not warned30:
            warned30 = True
            await bot.send_message(chat_id, "😱 Осталось 30 секунд!")

        if remaining <= 10:
            if countdown_task is None or countdown_task.done():
                countdown_task = asyncio.create_task(countdown(chat_id))

        await asyncio.sleep(1)

# ====== КРАСИВЫЙ COUNTDOWN ======

async def countdown(chat_id):
    global timer_message

    try:
        for i in range(10, -1, -1):
            now = asyncio.get_event_loop().time()

            # если перебили — выходим
            if end_time - now > 10:
                return

            bar = progress_bar(i)
            text = f"⏳ [{bar}] {i}s"

            if timer_message is None:
                timer_message = await bot.send_message(chat_id, text)
            else:
                try:
                    await timer_message.edit_text(text)
                except:
                    return

            await asyncio.sleep(1)

    except:
        pass

# ====== ФИНИШ ======

async def finish(chat_id):
    global event_active, timer_message

    event_active = False

    if timer_message:
        try:
            await timer_message.delete()
        except:
            pass

    if last_user:
        await bot.send_message(
            chat_id,
            f"🏆 Победитель: @{last_user.username}\n🎁 Приз: {settings['nft']}"
        )
    else:
        await bot.send_message(chat_id, "❌ Нет победителя")

# ====== АДМИН КОМАНДЫ ======

@dp.message(Command("set_timer"))
async def set_timer(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    value = int(message.text.split()[1])
    settings["timer"] = value

    await message.answer(f"⏳ Таймер изменён на {value} сек")

@dp.message(Command("set_price"))
async def set_price(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    value = int(message.text.split()[1])
    settings["price"] = value

    await message.answer(f"💸 Цена перебива: {value}⭐")

@dp.message(Command("set_nft"))
async def set_nft(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    link = message.text.split()[1]
    settings["nft"] = link

    await message.answer(f"🎁 Приз обновлён")

@dp.message(Command("ignore"))
async def ignore(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    user_id = int(message.text.split()[1])
    ignore_list.add(user_id)

    await message.answer(f"🚫 {user_id} добавлен в игнор")

# ====== ЗАПУСК ======

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())    asyncio.run(main())