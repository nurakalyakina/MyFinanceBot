from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def start_server():
    server = HTTPServer(("", 3000), SimpleHandler)
    server.serve_forever()

# Запускаем сервер в отдельном потоке
threading.Thread(target=start_server, daemon=True).start()
import telebot
import json
import os
import datetime
from datetime import datetime as dt

# Токен, который ты предоставила
TOKEN = "7713672785:AAHq_TUNg7yYGVZopncokwIkERHBRkOZb-o"

# Создаем бота
bot = telebot.TeleBot(TOKEN)

# Категории расходов
CATEGORIES = ["Еда", "Аптека", "Проезд", "Квартира", "КУ", "Другое"]

# Файл для хранения данных
DATA_FILE = "finance_data.json"

# Загрузка данных
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    return {}

# Сохранение данных
def save_data(data):
    with open(DATA_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Проверка, активны ли лимиты (по дате)
def are_limits_active(user_data):
    if "limit_start_date" not in user_data or "limit_end_date" not in user_data:
        return False
    start_date = dt.strptime(user_data["limit_start_date"], "%Y-%m-%d")
    end_date = dt.strptime(user_data["limit_end_date"], "%Y-%m-%d")
    current_date = dt.now()
    return start_date <= current_date <= end_date

# Функция для создания текстового прогресс-бара
def create_progress_bar(percentage, bar_length=10):
    filled = int(bar_length * percentage // 100)
    bar = '█' * filled + '-' * (bar_length - filled)
    return f"[{bar}] {percentage}%"

# Создаем клавиатуру
def create_main_menu():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(telebot.types.KeyboardButton("Установить лимиты"), telebot.types.KeyboardButton("Добавить расход"))
    keyboard.add(telebot.types.KeyboardButton("Посмотреть остатки"), telebot.types.KeyboardButton("Сброс лимитов"))
    keyboard.add(telebot.types.KeyboardButton("Посмотреть общий лимит"))
    keyboard.add(telebot.types.KeyboardButton("Установить срок лимита"), telebot.types.KeyboardButton("Сброс срока лимита"))
    keyboard.add(telebot.types.KeyboardButton("Посмотреть историю расходов"))
    keyboard.add(telebot.types.KeyboardButton("Посмотреть графики расходов"))
    return keyboard

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я бот для учета финансов. Начнем?", reply_markup=create_main_menu())

# Обработчик для установки срока лимита
@bot.message_handler(func=lambda message: message.text == "Установить срок лимита")
def start_setting_limit_dates(message):
    bot.reply_to(message, "Введи дату начала действия лимита (в формате ДД.ММ.ГГГГ, например, 15.03.2025):")
    bot.register_next_step_handler(message, process_start_date)

def process_start_date(message):
    user_id = str(message.from_user.id)
    try:
        start_date = dt.strptime(message.text, "%d.%m.%Y")
        data = load_data()
        if user_id not in data:
            data[user_id] = {cat: {"limit": 0, "spent": 0} for cat in CATEGORIES}
            data[user_id]["expenses_history"] = []  # Инициализируем историю расходов
        data[user_id]["limit_start_date"] = start_date.strftime("%Y-%m-%d")
        save_data(data)
        bot.reply_to(message, "Теперь введи дату окончания действия лимита (в формате ДД.ММ.ГГГГ, например, 15.04.2025):")
        bot.register_next_step_handler(message, process_end_date, user_id)
    except ValueError:
        bot.reply_to(message, "Пожалуйста, введи дату в формате ДД.ММ.ГГГГ (например, 15.03.2025).")
        bot.register_next_step_handler(message, process_start_date)

def process_end_date(message, user_id):
    try:
        end_date = dt.strptime(message.text, "%d.%m.%Y")
        data = load_data()
        start_date = dt.strptime(data[user_id]["limit_start_date"], "%Y-%m-%d")
        if end_date <= start_date:
            bot.reply_to(message, "Дата окончания должна быть позже даты начала! Попробуй снова.")
            bot.register_next_step_handler(message, process_end_date, user_id)
            return
        data[user_id]["limit_end_date"] = end_date.strftime("%Y-%m-%d")
        save_data(data)
        bot.reply_to(message, f"Срок действия лимита установлен: с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}.", reply_markup=create_main_menu())
    except ValueError:
        bot.reply_to(message, "Пожалуйста, введи дату в формате ДД.ММ.ГГГГ (например, 15.04.2025).")
        bot.register_next_step_handler(message, process_end_date, user_id)

# Обработчик для сброса срока лимита
@bot.message_handler(func=lambda message: message.text == "Сброс срока лимита")
def reset_limit_dates(message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id not in data:
        bot.reply_to(message, "У тебя еще нет установленных лимитов или срока!", reply_markup=create_main_menu())
        return
    if "limit_start_date" in data[user_id] and "limit_end_date" in data[user_id]:
        del data[user_id]["limit_start_date"]
        del data[user_id]["limit_end_date"]
        save_data(data)
        bot.reply_to(message, "Срок действия лимита сброшен!", reply_markup=create_main_menu())
    else:
        bot.reply_to(message, "Срок действия лимита еще не установлен!", reply_markup=create_main_menu())

# Обработчик для установки лимитов
@bot.message_handler(func=lambda message: message.text == "Установить лимиты")
def start_setting_limits(message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data:
        data[user_id] = {cat: {"limit": 0, "spent": 0} for cat in CATEGORIES}
        data[user_id]["expenses_history"] = []  # Инициализируем историю расходов
    save_data(data)
    bot.reply_to(message, f"Введи лимит для категории '{CATEGORIES[0]}' (в рублях):")
    bot.register_next_step_handler(message, process_limit, 0, user_id)

def process_limit(message, category_index, user_id):
    try:
        limit = float(message.text)
        if limit < 0:
            bot.reply_to(message, "Пожалуйста, введи корректное число (например, 1000).")
            bot.register_next_step_handler(message, process_limit, category_index, user_id)
            return
        data = load_data()
        data[user_id][CATEGORIES[category_index]]["limit"] = limit
        data[user_id][CATEGORIES[category_index]]["spent"] = 0
        save_data(data)

        category_index += 1
        if category_index < len(CATEGORIES):
            bot.reply_to(message, f"Введи лимит для категории '{CATEGORIES[category_index]}':")
            bot.register_next_step_handler(message, process_limit, category_index, user_id)
        else:
            bot.reply_to(message, "Все лимиты установлены!", reply_markup=create_main_menu())
    except ValueError:
        bot.reply_to(message, "Пожалуйста, введи корректное число (например, 1000).")
        bot.register_next_step_handler(message, process_limit, category_index, user_id)

# Обработчик для добавления расхода
@bot.message_handler(func=lambda message: message.text == "Добавить расход")
def start_spending(message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data or data[user_id][CATEGORIES[0]]["limit"] == 0:
        bot.reply_to(message, "Сначала установи лимиты!")
        return
    if not are_limits_active(data[user_id]):
        bot.reply_to(message, "Лимиты неактивны! Установи срок действия лимита или сбрось его.")
        return
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for category in CATEGORIES:
        keyboard.add(telebot.types.KeyboardButton(category))
    bot.reply_to(message, "Выбери категорию:", reply_markup=keyboard)
    bot.register_next_step_handler(message, process_category, user_id)

def process_category(message, user_id):
    if message.text not in CATEGORIES:
        bot.reply_to(message, "Выбери категорию из списка!")
        bot.register_next_step_handler(message, process_category, user_id)
        return
    category = message.text
    bot.reply_to(message, f"Введи сумму для '{category}':")
    bot.register_next_step_handler(message, process_amount, user_id, category)

def process_amount(message, user_id, category):
    try:
        amount = float(message.text)
        if amount < 0:
            bot.reply_to(message, "Пожалуйста, введи корректное число (например, 500).")
            bot.register_next_step_handler(message, process_amount, user_id, category)
            return
        data = load_data()
        current_spent = data[user_id][category]["spent"]
        limit = data[user_id][category]["limit"]
        new_spent = current_spent + amount

        # Сохраняем расход в историю
        if "expenses_history" not in data[user_id]:
            data[user_id]["expenses_history"] = []
        expense = {
            "category": category,
            "amount": amount,
            "date": dt.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        data[user_id]["expenses_history"].append(expense)

        if new_spent > limit:
            bot.reply_to(message, f"Превышен лимит в '{category}'! Остаток: {limit - current_spent}")
        else:
            data[user_id][category]["spent"] = new_spent
            remaining = limit - new_spent
            bot.reply_to(message, f"Расход учтен. В '{category}' осталось {remaining} из {limit}.")
            if remaining / limit <= 0.1:  # 10% или меньше
                bot.reply_to(message, f"⚠️ Внимание! В '{category}' осталось менее 10% лимита ({remaining}).")
        save_data(data)
        bot.reply_to(message, "Выбери действие:", reply_markup=create_main_menu())
    except ValueError:
        bot.reply_to(message, "Пожалуйста, введи корректное число (например, 500).")
        bot.register_next_step_handler(message, process_amount, user_id, category)

# Обработчик для проверки остатков
@bot.message_handler(func=lambda message: message.text == "Посмотреть остатки")
def check_balance(message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data or data[user_id][CATEGORIES[0]]["limit"] == 0:
        bot.reply_to(message, "Сначала установи лимиты!")
        return
    if not are_limits_active(data[user_id]):
        bot.reply_to(message, "Лимиты неактивны! Установи срок действия лимита или сбрось его.")
        return
    response = "Текущие остатки:\n"
    for category in CATEGORIES:
        limit = data[user_id][category]["limit"]
        spent = data[user_id][category]["spent"]
        response += f"{category}: {limit - spent}/{limit}\n"
    # Показываем срок действия лимита, если он установлен
    if "limit_start_date" in data[user_id] and "limit_end_date" in data[user_id]:
        start_date = dt.strptime(data[user_id]["limit_start_date"], "%Y-%m-%d").strftime("%d.%m.%Y")
        end_date = dt.strptime(data[user_id]["limit_end_date"], "%Y-%m-%d").strftime("%d.%m.%Y")
        response += f"\nСрок действия лимита: с {start_date} по {end_date}"
    bot.reply_to(message, response, reply_markup=create_main_menu())

# Обработчик для сброса лимитов
@bot.message_handler(func=lambda message: message.text == "Сброс лимитов")
def reset_limits(message):
    user_id = str(message.from_user.id)
    data = load_data()
    if user_id not in data:
        bot.reply_to(message, "У тебя еще нет установленных лимитов!", reply_markup=create_main_menu())
        return
    # Сохраняем историю расходов и даты, если они есть
    expenses_history = data[user_id].get("expenses_history", [])
    limit_start_date = data[user_id].get("limit_start_date")
    limit_end_date = data[user_id].get("limit_end_date")
    # Сбрасываем лимиты и расходы
    data[user_id] = {cat: {"limit": 0, "spent": 0} for cat in CATEGORIES}
    data[user_id]["expenses_history"] = expenses_history
    if limit_start_date and limit_end_date:
        data[user_id]["limit_start_date"] = limit_start_date
        data[user_id]["limit_end_date"] = limit_end_date
    save_data(data)
    bot.reply_to(message, "Все лимиты и расходы сброшены! История расходов сохранена.", reply_markup=create_main_menu())

# Обработчик для просмотра истории расходов
@bot.message_handler(func=lambda message: message.text == "Посмотреть историю расходов")
def check_expenses_history(message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data or "expenses_history" not in data[user_id] or not data[user_id]["expenses_history"]:
        bot.reply_to(message, "У тебя пока нет записей о расходах!", reply_markup=create_main_menu())
        return
    response = "История расходов:\n"
    for expense in data[user_id]["expenses_history"]:
        response += f"{expense['date']}: {expense['category']} - {expense['amount']} руб.\n"
    bot.reply_to(message, response, reply_markup=create_main_menu())

# Обработчик для просмотра графиков расходов
@bot.message_handler(func=lambda message: message.text == "Посмотреть графики расходов")
def check_expenses_graphs(message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data or data[user_id][CATEGORIES[0]]["limit"] == 0:
        bot.reply_to(message, "Сначала установи лимиты!")
        return
    if not are_limits_active(data[user_id]):
        bot.reply_to(message, "Лимиты неактивны! Установи срок действия лимита или сбрось его.")
        return
    response = "Графики расходов:\n"
    for category in CATEGORIES:
        limit = data[user_id][category]["limit"]
        spent = data[user_id][category]["spent"]
        if limit == 0:  # Избегаем деления на ноль
            percentage = 0
        else:
            percentage = min(int((spent / limit) * 100), 100)  # Ограничиваем 100%
        progress_bar = create_progress_bar(percentage)
        response += f"{category}: {progress_bar} ({spent}/{limit})\n"
    # Показываем срок действия лимита, если он установлен
    if "limit_start_date" in data[user_id] and "limit_end_date" in data[user_id]:
        start_date = dt.strptime(data[user_id]["limit_start_date"], "%Y-%m-%d").strftime("%d.%m.%Y")
        end_date = dt.strptime(data[user_id]["limit_end_date"], "%Y-%m-%d").strftime("%d.%m.%Y")
        response += f"\nСрок действия лимита: с {start_date} по {end_date}"
    bot.reply_to(message, response, reply_markup=create_main_menu())

# Обработчик для просмотра общего лимита
@bot.message_handler(func=lambda message: message.text == "Посмотреть общий лимит")
def check_total_limit(message):
    data = load_data()
    user_id = str(message.from_user.id)
    if user_id not in data or data[user_id][CATEGORIES[0]]["limit"] == 0:
        bot.reply_to(message, "Сначала установи лимиты!")
        return
    if not are_limits_active(data[user_id]):
        bot.reply_to(message, "Лимиты неактивны! Установи срок действия лимита или сбрось его.")
        return
    total_limit = 0
    total_spent = 0
    for category in CATEGORIES:
        total_limit += data[user_id][category]["limit"]
        total_spent += data[user_id][category]["spent"]
    total_remaining = total_limit - total_spent
    percentage = min(int((total_spent / total_limit) * 100), 100) if total_limit > 0 else 0
    progress_bar = create_progress_bar(percentage)
    response = f"Общий лимит по всем категориям: {total_limit} руб.\n"
    response += f"Потрачено: {total_spent} руб.\n"
    response += f"Осталось: {total_remaining} руб.\n"
    response += f"Прогресс: {progress_bar}\n"
    # Показываем срок действия лимита, если он установлен
    if "limit_start_date" in data[user_id] and "limit_end_date" in data[user_id]:
        start_date = dt.strptime(data[user_id]["limit_start_date"], "%Y-%m-%d").strftime("%d.%m.%Y")
        end_date = dt.strptime(data[user_id]["limit_end_date"], "%Y-%m-%d").strftime("%d.%m.%Y")
        response += f"\nСрок действия лимита: с {start_date} по {end_date}"
    bot.reply_to(message, response, reply_markup=create_main_menu())

# Запуск бота
print("Бот запущен!")
bot.polling()