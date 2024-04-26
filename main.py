import asyncio
import datetime
import json
import logging
import re

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums.parse_mode import ParseMode
from aiogram.filters import CommandStart, and_f, or_f
from aiogram.fsm.state import State, StatesGroup
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects

import configs

URL_TO_CHECK = (
    'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'
)


class ClientState(StatesGroup):
    MENU = State()
    CRYPTO = State()
    RATES = State()
    MAX_RATE = State()
    MIN_RATE = State()
    MIN_MAX = State()


bot = Bot(token=configs.TOKEN)
dp = Dispatcher()


class CryptoDataNotFoundError(BaseException):
    def __init__(self, message="Crypto data not found"):
        self.message = message
        super().__init__(self.message)

    @classmethod
    def check_condition(cls, data):

        if not data:
            raise cls("No crypto data available")


def get_response_crypto(crypto):
    parameters = {
        'symbol': crypto,
        'aux': 'num_market_pairs,cmc_rank'
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': configs.API_KEY,
    }
    session = Session()
    session.headers.update(headers)
    try:
        response = session.get(URL_TO_CHECK, params=parameters)
        data = json.loads(response.text)
        price = (
            data.get('data').get(crypto)[0].get('quote')
            .get('USD').get('price')
        )
        CryptoDataNotFoundError.check_condition(data)
    except (
        ConnectionError, Timeout, TooManyRedirects, CryptoDataNotFoundError
    ) as e:
        return e
    return price


def get_on_start_kb():
    porog = types.KeyboardButton(text='Отследить крипту')
    buttons_row_first = [porog]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[buttons_row_first], resize_keyboard=True
    )
    return keyboard


@dp.message(CommandStart())
async def handle_start(message, state):
    await state.set_state(ClientState.MENU)
    await message.answer(
        text=(
            "Приветствую! Я бот который поможет отследить нужный курс крипты!"
        ), reply_markup=get_on_start_kb()
    )


@dp.message(F.text == 'Отследить крипту')
async def handle_crypto(message, state):
    await state.set_state(ClientState.CRYPTO)
    await message.answer(
        text="Введите алфавитный код криптовалюты. Например 'BTC'"
    )


def porog_kb():
    min = types.KeyboardButton(text='Установить минимальный порог')
    max = types.KeyboardButton(text='Установить максимальный порог')
    both = types.KeyboardButton(text='Выбрать оба варианта')
    buttons_row_first = [min, max]
    buttons_row_second = [both]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[buttons_row_first, buttons_row_second], resize_keyboard=True
    )
    return keyboard


@dp.message(ClientState.CRYPTO)
async def handle_alf(message, state):
    url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'
    crypto = message.text
    parameters = {
        'symbol': crypto,
        'aux': 'num_market_pairs,cmc_rank'
    }
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': 'd88ed2c3-4b13-4b61-9b3e-a885f3b36d62',
    }
    session = Session()
    session.headers.update(headers)
    try:
        response = session.get(url, params=parameters)
        result = json.loads(response.text)

        CryptoDataNotFoundError.check_condition(result.get('data').get(crypto))
        price = (
            result.get('data').get(crypto)[0]
            .get('quote').get('USD').get('price')
        )
        info = (
            f"{price}$ текущая цена за одну монету. Теперь установите "
            f"минимальный, максимальный или оба порога для оповещения."
        )
    except (CryptoDataNotFoundError):
        await message.answer(
            text=(
                "Такой криптовалюты либо нет на бирже, "
                "либо неправильно введён код"
            )
        )
    await state.set_state(ClientState.RATES)
    await state.update_data(crypto=message.text)
    await message.answer(text=info, reply_markup=porog_kb())


@dp.message(and_f(F.text == 'Установить минимальный порог', ClientState.RATES))
async def handle_min(message, state):
    await state.set_state(ClientState.MIN_RATE)
    await message.answer(text="Напишите минимальный порог для оповещения")
    await message.answer(
        text="Дробные числа необходимо писать в формате '10.10'"
    )


@dp.message(
        and_f(F.text == 'Установить максимальный порог', ClientState.RATES)
    )
async def handle_max(message, state):
    await state.set_state(ClientState.MAX_RATE)
    await message.answer(text="Напишите максимальный для оповещения")
    await message.answer(
        text="Дробные числа необходимо писать в формате '10.10'"
    )


@dp.message(and_f(F.text == 'Выбрать оба варианта', ClientState.RATES))
async def handle_minmax(message, state):
    await state.set_state(ClientState.MIN_MAX)
    await message.answer(
        text=(
            "Напишите минимальный и максимальный порог "
            "через пробел по возрастанию, например '50000 25000000'"
        )
    )
    await message.answer(
        text="Дробные числа необходимо писать в формате '10.10'"
    )


@dp.message(
        or_f(ClientState.MIN_MAX, ClientState.MAX_RATE, ClientState.MIN_RATE)
    )
async def handle_porog(message, state):
    current_state = await state.get_state()
    if not re.match(
        r'^[0-9]+(?:\.[0-9]+)?$', message.text
    ) and not current_state == ClientState.MIN_MAX:
        await message.answer(
            text="Неправильный ввод. Введите только целые или дробные числа"
        )
    elif not re.match(
        r'^\d+(\.\d+)?\s\d+(\.\d+)?$', message.text
    ) and current_state == ClientState.MIN_MAX:
        await message.answer(
            text=(
                "Неправильный ввод. "
                "Введите только целые или дробные числа через пробел."
            )
        )

    if current_state == ClientState.MIN_RATE:
        min = message.text
        max = None
        await state.update_data(crypto_min=message.text)
    elif current_state == ClientState.MAX_RATE:
        max = message.text
        min = None
    else:
        num = (message.text).split(' ')
        if float(num[0]) > float(num[1]):
            max = num[0]
            min = num[1]
        else:
            max = num[1]
            min = num[0]
    user_id = message.from_user.id
    data = await state.get_data()
    crypto_id = data.get('crypto')
    current_time = datetime.datetime.now()
    check_data = {
        'user_id': user_id,
        'crypto_id': crypto_id,
        'time': current_time,
        'min': min,
        'max': max
    }
    await check_condition_periodically(check_data)


async def check_condition_crypto(crypto, min, max):
    current_price = get_response_crypto(crypto)
    if min:
        if current_price <= float(min):
            return True
    elif max:
        if float(max) <= current_price:
            return True
    return False


async def send_message_to_user(user_id: int, text: str):
    await bot.send_message(user_id, text, parse_mode=ParseMode.HTML)


async def check_condition_periodically(check_data):
    condition_met = False
    user_id = check_data.get('user_id')
    crypto = check_data.get('crypto_id')
    min = check_data.get('min')
    max = check_data.get('max')
    await bot.send_message(user_id, 'Начинаю опрос', parse_mode=ParseMode.HTML)
    while not condition_met:
        if await check_condition_crypto(crypto, min, max):
            condition_met = True
            logging.info("Condition met! Stopping condition checking.")
            if min:
                excepted = min
            else:
                excepted = max
            text = (
                f'Крипта достигла порогового значения {excepted}'
                f'=>{get_response_crypto(crypto)}'
            )
            await send_message_to_user(user_id, text)
            break
        logging.info("Condition not met yet! Continue...")
        await asyncio.sleep(60)


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

asyncio.run(main())
