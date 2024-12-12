import telebot
import requests
from bs4 import BeautifulSoup
from telebot import types
import random
import logging
import json
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_TOKEN = '7558556068:AAHG_o2t_EbV_Pw1xpb53bX03FSQLFUyHuU'  # Замените на ваш токен
bot = telebot.TeleBot(API_TOKEN)

# Словарь для хранения состояний пользователей
user_states = {}
# Словарь для хранения персонажей пользователей
user_characters = {}

# Файл для хранения персонажей
CHARACTER_FILE = 'characters.json'


def load_characters():
    """Загружает персонажей из файла, если он существует."""
    if os.path.exists(CHARACTER_FILE):
        with open(CHARACTER_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}


def save_characters():
    """Сохраняет персонажей в файл."""
    with open(CHARACTER_FILE, 'w', encoding='utf-8') as file:
        json.dump(user_characters, file)


# Загрузка персонажей при старте бота
user_characters = load_characters()


def fetch_data(url):
    """Получает данные с указанного URL и возвращает ссылки."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        return [
            f'https://dnd.su{item.find("a")["href"]}'
            for item in soup.find_all('div', class_='result-item')
        ]
    except Exception as e:
        logger.error(f"Ошибка: {str(e)}")
        return []  # Возвращаем пустой список при ошибке


def search_bestiary(query):
    url = f'https://dnd.su/bestiary/?search={query}'
    return fetch_data(url)


def search_spells(query):
    url = f'https://dnd.su/spells/?search={query}'
    return fetch_data(url)


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Поиск", callback_data="search"),
        types.InlineKeyboardButton("Кинуть дайсы", callback_data="roll_dice"),
        types.InlineKeyboardButton("Персонаж",
                                   callback_data="manage_character"))

    bot.send_message(message.chat.id,
                     "Привет, я ваш помощник в ДнД. Выберите действие:",
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "manage_character")
def manage_character(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Создать персонажа",
                                   callback_data="create_character"),
        types.InlineKeyboardButton("Изменить параметры",
                                   callback_data="edit_character"),
        types.InlineKeyboardButton("Посмотреть персонажа",
                                   callback_data="view_character"),
        types.InlineKeyboardButton("Удалить персонажа",
                                   callback_data="delete_character"),
        types.InlineKeyboardButton("Сохранить персонажа",
                                   callback_data="save_character"))

    bot.send_message(call.message.chat.id,
                     "Что вы хотите сделать с вашим персонажем?",
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "search")
def handle_search(call):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Бестиарий",
                                   callback_data="search_bestiary"),
        types.InlineKeyboardButton("Заклинания",
                                   callback_data="search_spells"))

    bot.send_message(call.message.chat.id,
                     "Что вы хотите искать?",
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "search_bestiary")
def search_bestiary_handler(call):
    bot.send_message(call.message.chat.id,
                     "Введите название существа для поиска:")
    user_states[call.message.chat.id] = 'searching_bestiary'


@bot.callback_query_handler(func=lambda call: call.data == "search_spells")
def search_spells_handler(call):
    bot.send_message(call.message.chat.id,
                     "Введите название заклинания для поиска:")
    user_states[call.message.chat.id] = 'searching_spells'


@bot.callback_query_handler(func=lambda call: call.data == "create_character")
def create_character_handler(call):
    bot.send_message(
        call.message.chat.id,
        "Давайте создадим вашего персонажа! Введите имя персонажа:")
    user_states[call.message.chat.id] = 'creating_character'


@bot.message_handler(func=lambda message: True)
def handle_input(message):
    state = user_states.get(message.chat.id)

    if state == 'searching_bestiary':
        query = message.text.strip().replace(" ", "+")
        results = search_bestiary(query)

        search_url = f'https://dnd.su/bestiary/?search={query}'

        if results:
            response_message = f"Вот что удалось найти:\n{results[0]}"
        else:
            response_message = f"К сожалению, ничего не найдено. Вы можете посмотреть по следующей ссылке:\n{search_url}"

        bot.send_message(message.chat.id, response_message)
        user_states[message.chat.id] = None  # Сбрасываем состояние
        handle_search_options(message.chat.id)

    elif state == 'searching_spells':
        query = message.text.strip().replace(" ", "+")
        results = search_spells(query)

        search_url = f'https://dnd.su/spells/?search={query}'

        if results:
            response_message = f"Вот что удалось найти:\n{results[0]}"
        else:
            response_message = f"К сожалению, ничего не найдено. Вы можете посмотреть по следующей ссылке:\n{search_url}"

        bot.send_message(message.chat.id, response_message)
        user_states[message.chat.id] = None  # Сбрасываем состояние
        handle_search_options(message.chat.id)

    elif state == 'creating_character':
        # Создание персонажа
        name = message.text.strip()
        user_characters[message.chat.id] = {
            "name": name,
            "Strength": 0,
            "Dexterity": 0,
            "Constitution": 0,
            "Intelligence": 0,
            "Wisdom": 0,
            "Charisma": 0
        }
        bot.send_message(
            message.chat.id,
            f"Персонаж '{name}' успешно создан! Теперь задайте параметры персонажа:\n"
            "Введите силу (Strength) (значение от 1 до 20):")
        user_states[message.chat.id] = 'setting_strength'

    elif state == 'setting_strength':
        try:
            strength = int(message.text)
            if 1 <= strength <= 20:
                user_characters[message.chat.id]["Strength"] = strength
                bot.send_message(
                    message.chat.id,
                    "Сила установлена. Введите ловкость (Dexterity) (значение от 1 до 20):"
                )
                user_states[message.chat.id] = 'setting_dexterity'
            else:
                bot.send_message(
                    message.chat.id,
                    "Ошибка: Пожалуйста, введите значение от 1 до 20.")
        except ValueError:
            bot.send_message(
                message.chat.id,
                "Ошибка: Пожалуйста, введите корректное числовое значение.")

    elif state == 'setting_dexterity':
        try:
            dexterity = int(message.text)
            if 1 <= dexterity <= 20:
                user_characters[message.chat.id]["Dexterity"] = dexterity
                bot.send_message(
                    message.chat.id,
                    "Ловкость установлена. Введите выносливость (Constitution) (значение от 1 до 20):"
                )
                user_states[message.chat.id] = 'setting_constitution'
            else:
                bot.send_message(
                    message.chat.id,
                    "Ошибка: Пожалуйста, введите значение от 1 до 20.")
        except ValueError:
            bot.send_message(
                message.chat.id,
                "Ошибка: Пожалуйста, введите корректное числовое значение.")

    elif state == 'setting_constitution':
        try:
            constitution = int(message.text)
            if 1 <= constitution <= 20:
                user_characters[message.chat.id]["Constitution"] = constitution
                bot.send_message(
                    message.chat.id,
                    "Выносливость установлена. Введите интеллект (Intelligence) (значение от 1 до 20):"
                )
                user_states[message.chat.id] = 'setting_intelligence'
            else:
                bot.send_message(
                    message.chat.id,
                    "Ошибка: Пожалуйста, введите значение от 1 до 20.")
        except ValueError:
            bot.send_message(
                message.chat.id,
                "Ошибка: Пожалуйста, введите корректное числовое значение.")

    elif state == 'setting_intelligence':
        try:
            intelligence = int(message.text)
            if 1 <= intelligence <= 20:
                user_characters[message.chat.id]["Intelligence"] = intelligence
                bot.send_message(
                    message.chat.id,
                    "Интеллект установлен. Введите мудрость (Wisdom) (значение от 1 до 20):"
                )
                user_states[message.chat.id] = 'setting_wisdom'
            else:
                bot.send_message(
                    message.chat.id,
                    "Ошибка: Пожалуйста, введите значение от 1 до 20.")
        except ValueError:
            bot.send_message(
                message.chat.id,
                "Ошибка: Пожалуйста, введите корректное числовое значение.")

    elif state == 'setting_wisdom':
        try:
            wisdom = int(message.text)
            if 1 <= wisdom <= 20:
                user_characters[message.chat.id]["Wisdom"] = wisdom
                bot.send_message(
                    message.chat.id,
                    "Мудрость установлена. Введите обаяние (Charisma) (значение от 1 до 20):"
                )
                user_states[message.chat.id] = 'setting_charisma'
            else:
                bot.send_message(
                    message.chat.id,
                    "Ошибка: Пожалуйста, введите значение от 1 до 20.")
        except ValueError:
            bot.send_message(
                message.chat.id,
                "Ошибка: Пожалуйста, введите корректное числовое значение.")

    elif state == 'setting_charisma':
        try:
            charisma = int(message.text)
            if 1 <= charisma <= 20:
                user_characters[message.chat.id]["Charisma"] = charisma
                character = user_characters[message.chat.id]
                bot.send_message(
                    message.chat.id,
                    f"Персонаж '{character['name']}' успешно создан с параметрами:\n"
                    f"Сила: {character['Strength']}\n"
                    f"Ловкость: {character['Dexterity']}\n"
                    f"Выносливость: {character['Constitution']}\n"
                    f"Интеллект: {character['Intelligence']}\n"
                    f"Мудрость: {character['Wisdom']}\n"
                    f"Обаяние: {character['Charisma']}")
                user_states[message.chat.id] = None  # Сбрасываем состояние
                handle_character_options(message.chat.id)
            else:
                bot.send_message(
                    message.chat.id,
                    "Ошибка: Пожалуйста, введите значение от 1 до 20.")
        except ValueError:
            bot.send_message(
                message.chat.id,
                "Ошибка: Пожалуйста, введите корректное числовое значение.")


def handle_character_options(chat_id):
    """Отправляет пользователю инлайн-кнопки для управления персонажем."""
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Посмотреть персонажа",
                                   callback_data="view_character"),
        types.InlineKeyboardButton("Изменить параметры",
                                   callback_data="edit_character"),
        types.InlineKeyboardButton("Удалить персонажа",
                                   callback_data="delete_character"),
        types.InlineKeyboardButton("Сохранить персонажа",
                                   callback_data="save_character"))

    bot.send_message(chat_id,
                     "Что вы хотите сделать с вашим персонажем?",
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "view_character")
def view_character(call):
    character = user_characters.get(call.message.chat.id)
    if character:
        response = (f"Персонаж: {character['name']}\n"
                    f"Сила: {character['Strength']}\n"
                    f"Ловкость: {character['Dexterity']}\n"
                    f"Выносливость: {character['Constitution']}\n"
                    f"Интеллект: {character['Intelligence']}\n"
                    f"Мудрость: {character['Wisdom']}\n"
                    f"Обаяние: {character['Charisma']}")
        bot.send_message(call.message.chat.id, response)
    else:
        bot.send_message(call.message.chat.id,
                         "У вас нет созданного персонажа.")


@bot.callback_query_handler(func=lambda call: call.data == "edit_character")
def edit_character_handler(call):
    character = user_characters.get(call.message.chat.id)
    if character:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Изменить Силу",
                                       callback_data="edit_strength"),
            types.InlineKeyboardButton("Изменить Ловкость",
                                       callback_data="edit_dexterity"),
            types.InlineKeyboardButton("Изменить Выносливость",
                                       callback_data="edit_constitution"),
            types.InlineKeyboardButton("Изменить Интеллект",
                                       callback_data="edit_intelligence"),
            types.InlineKeyboardButton("Изменить Мудрость",
                                       callback_data="edit_wisdom"),
            types.InlineKeyboardButton("Изменить Обаяние",
                                       callback_data="edit_charisma"))
        bot.send_message(call.message.chat.id,
                         "Какой параметр вы хотите изменить?",
                         reply_markup=markup)
    else:
        bot.send_message(call.message.chat.id,
                         "У вас нет созданного персонажа.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_"))
def edit_character_parameter(call):
    parameter = call.data.split("_")[1]
    bot.send_message(
        call.message.chat.id,
        f"Введите новое значение для {parameter.capitalize()} (от 1 до 20):")
    user_states[call.message.chat.id] = f'editing_{parameter}'


@bot.callback_query_handler(func=lambda call: call.data == "delete_character")
def delete_character(call):
    if call.message.chat.id in user_characters:
        del user_characters[call.message.chat.id]
        bot.send_message(call.message.chat.id,
                         "Ваш персонаж был успешно удален.")
    else:
        bot.send_message(call.message.chat.id,
                         "У вас нет созданного персонажа.")


@bot.callback_query_handler(func=lambda call: call.data == "save_character")
def save_character(call):
    save_characters()
    bot.send_message(call.message.chat.id,
                     "Ваш персонаж был успешно сохранен.")


@bot.message_handler(func=lambda message: True)
def handle_editing(message):
    state = user_states.get(message.chat.id)

    if state.startswith("editing_"):
        parameter = state.split("_")[1]
        try:
            value = int(message.text)
            if 1 <= value <= 20:
                user_characters[message.chat.id][
                    parameter.capitalize()] = value
                bot.send_message(
                    message.chat.id,
                    f"{parameter.capitalize()} успешно обновлен на {value}.")
                user_states[message.chat.id] = None  # Сбрасываем состояние
                handle_character_options(message.chat.id)
            else:
                bot.send_message(
                    message.chat.id,
                    "Ошибка: Пожалуйста, введите значение от 1 до 20.")
        except ValueError:
            bot.send_message(
                message.chat.id,
                "Ошибка: Пожалуйста, введите корректное числовое значение.")


def handle_search_options(chat_id):
    """Отправляет пользователю инлайн-кнопки для выбора опции поиска."""
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Бестиарий",
                                   callback_data="search_bestiary"),
        types.InlineKeyboardButton("Заклинания",
                                   callback_data="search_spells"))

    bot.send_message(chat_id, "Что вы хотите искать?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "roll_dice")
def callback_roll_dice(call):
    show_dice_options(call.message.chat.id)


def show_dice_options(chat_id):
    """Отправляет пользователю инлайн-кнопки для выбора дайсов."""
    markup = types.InlineKeyboardMarkup()
    for dice in ["1d4", "1d6", "1d8", "1d10", "1d12", "1d20"]:
        markup.add(
            types.InlineKeyboardButton(dice, callback_data=f"roll_{dice}"))
    bot.send_message(chat_id,
                     "Какой дайс вы хотите кинуть?",
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("roll_"))
def roll_dice(call):
    dice_type = call.data.split("_")[1]  # Определяем тип дайса

    # Распознаем количество дайсов и их тип
    try:
        num_dice, max_value = map(int, dice_type.split('d'))
    except ValueError:
        bot.send_message(
            call.message.chat.id,
            "Ошибка: Неверный формат дайса. Пожалуйста, используйте формат 'XdY', например, '2d6'."
        )
        return

    results = [random.randint(1, max_value) for _ in range(num_dice)]

    # Создаем сообщение с результатами броска без суммы
    response = f"Вы бросили {dice_type}! Результаты: {', '.join(map(str, results))}"
    bot.send_message(call.message.chat.id, response)

    # Возвращаем пользователя к выбору дайсов
    show_dice_options(call.message.chat.id)


# Запуск бота и сохранение данных при завершении работы
if __name__ == '__main__':
    try:
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        pass  # Здесь можно добавить обработку завершения работы бота, если нужно.
