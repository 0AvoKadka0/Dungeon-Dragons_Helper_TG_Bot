import telebot
import requests
from bs4 import BeautifulSoup
from telebot import types
import random

# Вставьте сюда ваш токен, который вы получили от BotFather
API_TOKEN = '7558556068:AAHG_o2t_EbV_Pw1xpb53bX03FSQLFUyHuU'  # Замените на ваш токен
bot = telebot.TeleBot(API_TOKEN)

# Хранилище состояния пользователей
user_states = {}

# Функция для извлечения информации с сайта Бестиарий
def search_bestiary(query):
    url = f'https://dnd.su/bestiary/?search={query}'  # Полный URL для поиска
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Извлечение ссылок на результаты поиска
        links = []
        for item in soup.find_all('div', class_='result-item'):
            link = item.find('a')['href']
            if not link.startswith('http'):
                link = f'https://dnd.su{link}'
            links.append(link)

        return links if links else None  # Возвращаем None, если нет результатов

    except Exception as e:
        return [f"Произошла ошибка: {str(e)}"]

# Функция для извлечения информации с сайта Заклинания
def search_spells(query):
    url = f'https://dnd.su/spells/?search={query}'  # Полный URL для поиска
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Извлечение ссылок на результаты поиска
        links = []
        for item in soup.find_all('div', class_='result-item'):
            link = item.find('a')['href']
            if not link.startswith('http'):
                link = f'https://dnd.su{link}'
            links.append(link)

        return links if links else None  # Возвращаем None, если нет результатов

    except Exception as e:
        return [f"Произошла ошибка: {str(e)}"]

# Обработка команды /start
@bot.message_handler(commands=['start'])
def start(message):
    # Приветственное сообщение с инлайн-кнопками "Поиск" и "Кинуть дайсы"

    # Создание инлайн-кнопок "Поиск" и "Кинуть дайсы"
    markup = types.InlineKeyboardMarkup()
    button_search = types.InlineKeyboardButton("Поиск", callback_data="search")
    button_roll_dice = types.InlineKeyboardButton("Кинуть дайсы", callback_data="roll_dice")
    markup.add(button_search, button_roll_dice)

    bot.send_message(message.chat.id, "Привет, я ваш помощник в ДнД, рад стараться ради вас, путник. Выберите, что хотите сделать:", reply_markup=markup)

# Обработка инлайн-кнопки "Поиск"
@bot.callback_query_handler(func=lambda call: call.data == "search")
def callback_search(call):
    # Отправляем сообщение с инлайн-кнопками "Бестиарий" и "Заклинания"
    markup = types.InlineKeyboardMarkup()
    button_bestiary = types.InlineKeyboardButton("Бестиарий", callback_data="bestiary")
    button_spells = types.InlineKeyboardButton("Заклинания", callback_data="spells")
    markup.add(button_bestiary, button_spells)

    # Отправляем сообщение с инлайн-кнопками
    bot.send_message(call.message.chat.id, "Вот что я могу найти: выберите опцию для поиска:", reply_markup=markup)

# Обработка инлайн-кнопки "Кинуть дайсы"
@bot.callback_query_handler(func=lambda call: call.data == "roll_dice")
def callback_roll_dice(call):
    # Отправляем сообщение с вариантами дайсов
    markup = types.InlineKeyboardMarkup()
    button_d4 = types.InlineKeyboardButton("1d4", callback_data="roll_1d4")
    button_d6 = types.InlineKeyboardButton("1d6", callback_data="roll_1d6")
    button_d8 = types.InlineKeyboardButton("1d8", callback_data="roll_1d8")
    button_d10 = types.InlineKeyboardButton("1d10", callback_data="roll_1d10")
    button_d12 = types.InlineKeyboardButton("1d12", callback_data="roll_1d12")
    button_d20 = types.InlineKeyboardButton("1d20", callback_data="roll_1d20")
    
    markup.add(button_d4, button_d6, button_d8, button_d10, button_d12, button_d20)

    bot.send_message(call.message.chat.id, "Какой дайс вы хотите кинуть?", reply_markup=markup)

# Обработка нажатий на кнопки дайсов
@bot.callback_query_handler(func=lambda call: call.data.startswith("roll_"))
def roll_dice(call):
    dice_type = call.data.split("_")[1]  # Получаем тип дайса (например, 1d4, 1d6 и т.д.)
    
    # Определяем максимальное значение в зависимости от типа дайса
    if dice_type == "1d4":
        result = random.randint(1, 4)
    elif dice_type == "1d6":
        result = random.randint(1, 6)
    elif dice_type == "1d8":
        result = random.randint(1, 8)
    elif dice_type == "1d10":
        result = random.randint(1, 10)
    elif dice_type == "1d12":
        result = random.randint(1, 12)
    elif dice_type == "1d20":
        result = random.randint(1, 20)

    # Отправляем сообщение с результатом
    bot.send_message(call.message.chat.id, f"Вы бросили {dice_type}! Результат: {result}")
    
    # Отправляем соответствующий эмодзи отдельно
    if result == 20:
        bot.send_message(call.message.chat.id, "🎉")
    elif result == 1:
        bot.send_message(call.message.chat.id, "💀")
    
    # Сбрасываем состояние для повторного выбора опции
    user_states[call.message.chat.id] = None
    show_dice_options(call.message.chat.id)

def show_dice_options(chat_id):
    """Отправляет пользователю инлайн-кнопки для выбора дайса."""
    markup = types.InlineKeyboardMarkup()
    button_d4 = types.InlineKeyboardButton("1d4", callback_data="roll_1d4")
    button_d6 = types.InlineKeyboardButton("1d6", callback_data="roll_1d6")
    button_d8 = types.InlineKeyboardButton("1d8", callback_data="roll_1d8")
    button_d10 = types.InlineKeyboardButton("1d10", callback_data="roll_1d10")
    button_d12 = types.InlineKeyboardButton("1d12", callback_data="roll_1d12")
    button_d20 = types.InlineKeyboardButton("1d20", callback_data="roll_1d20")
    
    markup.add(button_d4, button_d6, button_d8, button_d10, button_d12, button_d20)

    bot.send_message(chat_id, "Какой дайс вы хотите кинуть?", reply_markup=markup)

# Обработка инлайн-кнопок "Бестиарий" и "Заклинания"
@bot.callback_query_handler(func=lambda call: call.data in ["bestiary", "spells"])
def callback_query(call):
    if call.data == "bestiary":
        user_states[call.message.chat.id] = 'bestiary'  # Сохраняем состояние пользователя
        bot.send_message(call.message.chat.id, "Напишите название существа, которое вас интересует.")
    
    elif call.data == "spells":
        user_states[call.message.chat.id] = 'spells'  # Сохраняем состояние пользователя
        bot.send_message(call.message.chat.id, "Напишите название заклинания, которое вас интересует.")

# Обработка текстовых сообщений
@bot.message_handler(func=lambda message: True)
def search(message):
    query = message.text.strip()
    formatted_query = query.replace(" ", "+")  # Заменяем пробелы на знак "+"

    state = user_states.get(message.chat.id)  # Получаем состояние пользователя

    if state == 'bestiary':
        search_url = f'https://dnd.su/bestiary/?search={formatted_query}'  # Ссылка на поиск
        results = search_bestiary(formatted_query)  # Используем отформатированный запрос
        
        bot.send_message(message.chat.id, f"[Ссылка на результаты]({search_url})", parse_mode='Markdown')  # Отправляем ссылку на поиск
        if results:  # Отправляем результаты, только если они есть
            bot.send_message(message.chat.id, "\n".join(results))  # Отправляем найденные ссылки
        
        # Сбрасываем состояние для повторного выбора опции
        user_states[message.chat.id] = None
        return show_options(message.chat.id)

    elif state == 'spells':
        search_url = f'https://dnd.su/spells/?search={formatted_query}'  # Ссылка на поиск
        results = search_spells(formatted_query)  # Используем отформатированный запрос
        
        bot.send_message(message.chat.id, f"[Ссылка на результаты]({search_url})", parse_mode='Markdown')  # Отправляем ссылку на поиск
        if results:  # Отправляем результаты, только если они есть
            bot.send_message(message.chat.id, "\n".join(results))  # Отправляем найденные ссылки
        
        # Сбрасываем состояние для повторного выбора опции
        user_states[message.chat.id] = None
        return show_options(message.chat.id)

    # Если состояние не установлено (пользователь не выбрал опцию)
    bot.send_message(message.chat.id, "Ошибка: Вы не выбрали опцию. Пожалуйста, используйте кнопку 'Поиск' для начала.")

def show_options(chat_id):
    """Отправляет пользователю инлайн-кнопки для выбора опции."""
    markup = types.InlineKeyboardMarkup()
    button_bestiary = types.InlineKeyboardButton("Бестиарий", callback_data="bestiary")
    button_spells = types.InlineKeyboardButton("Заклинания", callback_data="spells")
    markup.add(button_bestiary, button_spells)
    
    bot.send_message(chat_id, "Вот что я могу найти: выберите опцию:", reply_markup=markup)

# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)
