import asyncio
import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

TOKEN = "8888434497:AAGR6xdBiuCBjajw8BeQgboJ2_PMk90jBCg"
ADMIN_ID = 105635005
GROUP_ID = -1004368091214

bot = Bot(TOKEN)
dp = Dispatcher()

# ⚙️ настройки
settings = {
    "timer": 120,
    "price": 4,
    "prize": "https://t.me/nft/test"
}

# 📊 состояние
event_active = False
last_user = None
end_time = None

# 🚫 игнор-лист
ignore_list = set()

# FSM
class AdminStates(StatesGroup):
    set_timer = State()
    set_prize = State()
    set_price = State()

# ================= КНОПКИ =================

def admin_panel():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Старт", callback_data="start_event")],
        [InlineKeyboardButton(text="⏹ Стоп", callback_data="stop_event")],
        [InlineKeyboardButton(text="⏱ Таймер", callback_data="timer")],
        [InlineKeyboardButton(text="🎁 Приз", callback_data="prize")],
        [InlineKeyboardButton(text="💰 Цена перебива", callback_data="price")],
        [InlineKeyboardButton(text="🔇 Мут (reply)", callback_data="mute_help")]
    ])

# ================= СТАРТ =================

@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("⚙️ Админ панель", reply_markup=admin_panel())

# ================= АДМИН =================

@dp.callback_query(F.data == "start_event")
async def start_event(callback: types.CallbackQuery):
    global event_active, end_time

    if callback.from_user.id != ADMIN_ID:
        return

    event_active = True
    end_time = asyncio.get_event_loop().time() + settings["timer"]

    await bot.send_message(
        GROUP_ID,
        f"🎯 Ивент начался!\n💰 Перебив: {settings['price']}\n⏱ Таймер: {settings['timer']} сек"
    )

    asyncio.create_task(timer_loop(GROUP_ID))


@dp.callback_query(F.data == "stop_event")
async def stop_event(callback: types.CallbackQuery):
    global event_active

    if callback.from_user.id != ADMIN_ID:
        return

    event_active = False
    await bot.send_message(GROUP_ID, "⛔ Ивент остановлен")

# ================= НАСТРОЙКИ =================

@dp.callback_query(F.data == "timer")
async def set_timer(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введи таймер (сек):")
    await state.set_state(AdminStates.set_timer)


@dp.message(AdminStates.set_timer)
async def save_timer(message: types.Message, state: FSMContext):
    global end_time

    settings["timer"] = int(message.text)

    await bot.send_message(
        GROUP_ID,
        f"⚠️ Таймер изменён на {message.text} секунд!"
    )

    if event_active:
        end_time = asyncio.get_event_loop().time() + int(message.text)

    await state.clear()


@dp.callback_query(F.data == "prize")
async def set_prize(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введи ссылку на приз:")
    await state.set_state(AdminStates.set_prize)


@dp.message(AdminStates.set_prize)
async def save_prize(message: types.Message, state: FSMContext):
    settings["prize"] = message.text
    await message.answer("🎁 Приз обновлён!")
    await state.clear()


@dp.callback_query(F.data == "price")
async def set_price(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введи цену перебива:")
    await state.set_state(AdminStates.set_price)


@dp.message(AdminStates.set_price)
async def save_price(message: types.Message, state: FSMContext):
    settings["price"] = int(message.text)
    await message.answer("💰 Цена обновлена!")
    await state.clear()

# ================= МУТ (РЕАЛЬНЫЙ) =================

@dp.callback_query(F.data == "mute_help")
async def mute_help(callback: types.CallbackQuery):
    await callback.message.answer(
        "🔇 Ответь на сообщение пользователя и напиши:\n/mute 10"
    )


@dp.message(Command("mute"))
async def mute_user(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    if not message.reply_to_message:
        await message.answer("❌ Ответь на сообщение пользователя")
        return

    try:
        minutes = int(message.text.split()[1])
    except:
        await message.answer("Пример: /mute 10")
        return

    user = message.reply_to_message.from_user

    until_date = datetime.datetime.now() + datetime.timedelta(minutes=minutes)

    await bot.restrict_chat_member(
        chat_id=GROUP_ID,
        user_id=user.id,
        permissions=types.ChatPermissions(can_send_messages=False),
        until_date=until_date
    )

    await message.answer(f"🔇 {user.full_name} замучен на {minutes} минут")

# ================= ИГНОР ЛИСТ =================

@dp.message(Command("ignore"))
async def add_ignore(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        user_id = int(message.text.split()[1])
    except:
        await message.answer("Пример: /ignore 123456789")
        return

    ignore_list.add(user_id)
    await message.answer(f"🚫 {user_id} добавлен в игнор")


@dp.message(Command("unignore"))
async def remove_ignore(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        user_id = int(message.text.split()[1])
    except:
        await message.answer("Пример: /unignore 123456789")
        return

    ignore_list.discard(user_id)
    await message.answer(f"✅ {user_id} убран из игнора")


@dp.message(Command("ignorelist"))
async def show_ignore(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    if not ignore_list:
        await message.answer("Список игнора пуст")
        return

    text = "🚫 Игнор-лист:\n"
    for uid in ignore_list:
        text += f"{uid}\n"

    await message.answer(text)

# ================= ИВЕНТ =================

@dp.message()
async def messages(message: types.Message):
    global last_user, end_time

    if message.chat.id != GROUP_ID:
        return

    if not event_active:
        return

    if message.from_user.id in ignore_list:
        return

    last_user = message.from_user
    end_time = asyncio.get_event_loop().time() + settings["timer"]


async def timer_loop(chat_id):
    global event_active

    warned30 = False
    warned10 = False

    while event_active:
        remaining = int(end_time - asyncio.get_event_loop().time())

        if remaining <= 0:
            await finish(chat_id)
            return

        if remaining == 30 and not warned30:
            warned30 = True
            await bot.send_message(chat_id, "😱 Осталось 30 секунд!")

        if remaining == 10 and not warned10:
            warned10 = True
            asyncio.create_task(countdown(chat_id))

        await asyncio.sleep(1)


async def countdown(chat_id):
    msg = await bot.send_message(chat_id, "10")

    for i in range(9, -1, -1):
        await asyncio.sleep(1)
        await msg.edit_text(str(i))


async def finish(chat_id):
    global event_active
    event_active = False

    if last_user:
        name = f"@{last_user.username}" if last_user.username else last_user.full_name

        await bot.send_message(
            chat_id,
            f"🏆 Победитель: {name}\n🎁 {settings['prize']}"
        )

# ================= СТАРТ =================

async def main():
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())