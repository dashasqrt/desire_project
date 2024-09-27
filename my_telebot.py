import io, os
import requests
import json
import asyncio
import nest_asyncio
nest_asyncio.apply()

from aiogram import Bot, Dispatcher, types, F, html, Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, URLInputFile, BufferedInputFile, KeyboardButton, ReplyKeyboardRemove
from typing import Any, Dict

# токен, полученный у https://t.me/BotFather
TOKEN = ''

# инициализация бота и диспетчера
bot = Bot(TOKEN)


dp = Dispatcher()

class Form(StatesGroup):
    recepient = State() 
    holiday = State() 
    ok = State()

url = "http://localhost:11434/api/generate"

recepients = ['Женщины', "Мужчины", "Коллеги", "Подруги", "Отца", "Мамы"]

holidays = ['C днем рождения', 'C Новым годом', 'C Рождеством', 'C днем матери']

final_text = ''

def edit_final_text(data: str):
    global final_text
    final_text = data


@dp.message(CommandStart())
async def start(message: types.Message, state: FSMContext) -> None:
    kb = []
    for r in recepients:
        kb.append([types.KeyboardButton(text=r)])
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb)
    await state.set_state(Form.recepient)
    await message.answer('Добро пожаловать, для кого пишем поздравления? Выберите из списка или укажите сами.', parse_mode="html", reply_markup=keyboard)


@dp.message(Form.recepient)
async def process_recipient(message: types.Message, state: FSMContext) -> None:
    await state.update_data(recepient=message.text)
    await state.set_state(Form.holiday)
    kb = []
    for h in holidays:
        kb.append([types.KeyboardButton(text=h)])
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb)
    await  message.answer('С чем поздравляем? Выберите из списка или укажите сами.', parse_mode="html", reply_markup=keyboard)


@dp.message(Form.holiday)
async def process_holiday(message: types.Message, state: FSMContext)-> None:
    data = await state.update_data(holiday=message.text)
    await state.set_state(Form.ok)
    await show_summary(message=message, state = FSMContext, data=data)

async def show_summary(message: Message, state: FSMContext, data: Dict[str, Any]) -> None:
    recepient = data["recepient"]
    holiday = data['holiday']
    text = f"Поздравление для {html.quote(recepient.lower())} {html.quote(holiday.lower())}"
    edit_final_text(text)
    kb = [[types.KeyboardButton(text='Да! Все верно!')], [types.KeyboardButton(text='Нет! Не верно!')]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb)
    await message.answer(text=text+ ". Верно?",  parse_mode="html", reply_markup=keyboard)

@dp.message(lambda message: message.text == 'Нет! Не верно!', Form.ok)
async def process_notok(message: types.Message, state: FSMContext)-> None:
    data = await state.update_data(ok=message.text)
    await state.clear()
    await message.answer(text='Введите сообщение в формате: "Поздравление {для кого?} {с чем?}"')


@dp.message(lambda message: message.text == 'Да! Все верно!', Form.ok)
async def process_notok(message: types.Message, state: FSMContext):
    data = await state.update_data(ok=message.text)
    await state.clear()
    await answer_text(message=message, data=final_text)

@dp.message(F.text)
async def save_request(message: types.Message):
    await answer_text(message=message, data=message.text)


async def answer_text(message: Message, data: str) -> None:
    json_data = {
    "model": "qwen2:1.5b",
    "prompt": data,
    "stream": False,
    "options": {"temperature": 0.3},
    }
    response = requests.post(url, json=json_data)
    response.raise_for_status()
    json_response = json.loads(response.text)
    await message.answer(json_response["response"]+"\n\nСпасибо за обращение! Для нового обращения укажите /start")


# функция (корутина) которая запускает бота
async def main() -> None:
    await dp.start_polling(bot, skip_updates=True)

# запуск бота
asyncio.run(main())
