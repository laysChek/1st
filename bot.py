import json
import logging
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
import asyncio

# 🔹 Твой токен бота
TOKEN = "7686931299:AAFRCpb58TuEl75FzmViv70wgBpIFqdjYTw"

# 🔹 Загружаем меню
with open("menu.json", "r", encoding="utf-8") as file:
    dishes = json.load(file)

# 🔹 Настройки бота
bot = Bot(token=TOKEN)
dp = Dispatcher()

# 🔹 Логирование
logging.basicConfig(level=logging.INFO)

# 🔹 Главное меню (клавиатура)
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Карточки")],
        [KeyboardButton(text="Викторина")],
        [KeyboardButton(text="Тесты")]
    ],
    resize_keyboard=True
)

def get_name():
    """Рандомно выбирает обращение"""
    return "Евгения" if random.random() < 0.2 else "Женя"

# 🔹 Остроумные ответы
funny_correct_responses = [
    "🎉 Да ты просто гуру кухни, {name}! 🔥 Это действительно *{correct}*!",
    "🎉 Бинго! Ты знаешь меню лучше, чем официанты. 😎 *{correct}*!",
    "🎉 Верно! А теперь иди заказывай *{correct}* – ты заслужила. 😉",
    "🎉 Ты была бы отличным шефом! 🍳 *{correct}*!"
]

funny_wrong_responses = [
    "❌ Ох, {name}, ты это серьёзно? 😂 Это же *{correct}*! Пора в ресторан!",
    "❌ Ну, ты почти угадала… если бы совсем не угадала. 😆 Это *{correct}*!",
    "❌ Ай-ай, {name}! Кто-то явно не заказывал *{correct}*!",
    "❌ Нет, но за смелость – 10 баллов! 😄 Настоящий ответ: *{correct}*."
]

# 🔹 Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer(f"Привет, {get_name()}! 💕 Выбери режим:", reply_markup=keyboard)

# 🔹 Исправленная кнопка "Закончить"
@dp.callback_query(F.data == "exit")
async def exit_quiz(callback_query: types.CallbackQuery):
    """Выход из текущего режима в главное меню"""
    
    # Создаём новое сообщение с ReplyKeyboardMarkup
    await callback_query.message.answer("🏠 Ты вернулась в главное меню.", reply_markup=keyboard)
    
    # Удаляем старое сообщение с inline-кнопками
    await callback_query.message.delete()

# 🔹 Викторина
@dp.message(F.text == "Викторина")
async def send_quiz(message: types.Message):
    """Отправляет вопрос викторины"""
    question_index = random.randint(0, len(dishes) - 1)
    correct_dish = dishes[question_index]

    wrong_answers = random.sample(
        [d for d in dishes if d["name"] != correct_dish["name"]], 3
    )

    options = [correct_dish] + wrong_answers
    random.shuffle(options)

    buttons = [
        [InlineKeyboardButton(text=option["name"], callback_data=f"quiz_{dishes.index(option)}")]
        for option in options
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(f"❓ {get_name()}, какое блюдо состоит из:\n{', '.join(correct_dish['ingredients'])}?", reply_markup=keyboard)

@dp.callback_query(F.data.startswith("quiz_"))
async def check_quiz_answer(callback_query: types.CallbackQuery):
    """Проверяет ответ пользователя"""
    selected_index = int(callback_query.data.replace("quiz_", ""))
    selected_dish = dishes[selected_index]

    question_text = callback_query.message.text.split("\n")[0]
    correct_dish = next((d for d in dishes if ', '.join(d["ingredients"]) in callback_query.message.text), None)

    if correct_dish and selected_dish["name"] == correct_dish["name"]:
        response = random.choice(funny_correct_responses).format(name=get_name(), correct=correct_dish["name"])
    else:
        response = random.choice(funny_wrong_responses).format(name=get_name(), correct=correct_dish["name"])

    buttons = [
        [InlineKeyboardButton(text="Следующий вопрос", callback_data="next_quiz")],
        [InlineKeyboardButton(text="Закончить", callback_data="exit")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback_query.message.edit_text(response, parse_mode="Markdown", reply_markup=keyboard)

@dp.callback_query(F.data == "next_quiz")
async def next_quiz(callback_query: types.CallbackQuery):
    await send_quiz(callback_query.message)

# 🔹 Режим "Тесты" с кнопкой "Следующий вопрос"
user_tests = {}

@dp.message(F.text == "Тесты")
async def send_test(message: types.Message):
    """Отправляет вопрос теста"""
    index = random.randint(0, len(dishes) - 1)
    dish = dishes[index]

    await message.answer(f"📝 {get_name()}, введи состав блюда: *{dish['name']}*.\nНапиши ингредиенты через запятую.")
    user_tests[message.chat.id] = dish

@dp.message(F.text)
async def check_test_answer(message: types.Message):
    """Проверяет введённый пользователем состав"""
    if message.chat.id not in user_tests:
        return

    dish = user_tests.pop(message.chat.id)
    correct_ingredients = set(map(str.lower, dish["ingredients"]))
    user_ingredients = set(map(str.lower, map(str.strip, message.text.split(","))))

    if user_ingredients == correct_ingredients:
        response = random.choice(funny_correct_responses).format(name=get_name(), correct=dish["name"])
    else:
        response = random.choice(funny_wrong_responses).format(name=get_name(), correct=dish["name"])

    buttons = [
        [InlineKeyboardButton(text="Следующий вопрос", callback_data="next_test")],
        [InlineKeyboardButton(text="Закончить", callback_data="exit")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(response, parse_mode="Markdown", reply_markup=keyboard)

@dp.callback_query(F.data == "next_test")
async def next_test(callback_query: types.CallbackQuery):
    await send_test(callback_query.message)

# 🔹 Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
