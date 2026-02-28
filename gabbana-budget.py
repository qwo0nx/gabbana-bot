import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from datetime import datetime
import json
import os

# ========== НАСТРОЙКИ ==========
TOKEN = "8761306495:AAFWICUB62qgO2h-1va3Y50DHZPGvCGakjw"
DATA_FILE = "gabbana_data.json"
ALLOWED_IDS = [6578266978, 5029738209, 7950080109]

# Список сотрудников
EMPLOYEES = ["Матвей", "Дима", "Никита"]

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Клавиатуры
main_keyboard = ReplyKeyboardMarkup([
    ['💰 Доход', '💸 Расход'],
    ['📊 Статистика', '📋 Таблица парфюмов'],
    ['👥 Статистика коллег', '✏️ Редактировать/Удалить']
], resize_keyboard=True)

# Клавиатура с кнопкой отмены
cancel_keyboard = ReplyKeyboardMarkup([['🔙 Отмена']], resize_keyboard=True)

# Клавиатура для объема
volume_keyboard = ReplyKeyboardMarkup([
    ['6ml', '10ml'],
    ['🔙 Отмена']
], resize_keyboard=True)

# Клавиатура для способа оплаты
payment_keyboard = ReplyKeyboardMarkup([
    ['💳 Перевод', '💵 Наличка'],
    ['🔙 Отмена']
], resize_keyboard=True)

# Клавиатура для банков
bank_keyboard = ReplyKeyboardMarkup([
    ['🏦 Сбер', '🏦 Тинькофф', '🏦 ВТБ'],
    ['🏦 Альфа', '🏦 Райффайзен', '🏦 Другой'],
    ['🔙 Отмена']
], resize_keyboard=True)

# Клавиатура для выбора сотрудника
employee_keyboard = ReplyKeyboardMarkup([
    ['👤 Матвей', '👤 Дима', '👤 Никита'],
    ['🔙 Отмена']
], resize_keyboard=True)

# Состояния для дохода
INCOME_STATES = {
    'NAME': 1,        # Ввод названия парфюма
    'VOLUME': 2,      # Ввод объема
    'QUANTITY': 3,    # Ввод количества
    'EMPLOYEE': 4,    # Выбор сотрудника
    'PAYMENT': 5,     # Выбор способа оплаты
    'BANK': 6,        # Выбор банка (если перевод)
    'AMOUNT': 7       # Ввод суммы
}

# Состояния для расхода
EXPENSE_STATES = {
    'AMOUNT': 1,
    'DESCRIPTION': 2,
    'EMPLOYEE': 3
}

# Состояния пользователей
user_data = {}  # Для временного хранения данных

def check_access(update):
    user_id = update.effective_user.id
    return user_id in ALLOWED_IDS

def load_data():
    """Загружает данные из JSON файла"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'operations': [], 'next_id': 1}
    return {'operations': [], 'next_id': 1}

def save_data(data):
    """Сохраняет данные в JSON файл"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_next_id():
    """Получает следующий свободный ID"""
    data = load_data()
    next_id = data.get('next_id', 1)
    # Увеличиваем next_id для следующей операции
    data['next_id'] = next_id + 1
    save_data(data)
    return next_id

def add_operation(operation):
    """Добавляет операцию в хранилище"""
    data = load_data()
    if 'operations' not in data:
        data['operations'] = []
    data['operations'].append(operation)
    save_data(data)

def get_all_operations():
    """Получает все операции"""
    data = load_data()
    return data.get('operations', [])

def delete_operation(op_id):
    """Удаляет операцию по ID"""
    data = load_data()
    data['operations'] = [op for op in data['operations'] if op['id'] != op_id]
    save_data(data)

def update_operation(op_id, updated_op):
    """Обновляет операцию"""
    data = load_data()
    for i, op in enumerate(data['operations']):
        if op['id'] == op_id:
            data['operations'][i] = updated_op
            break
    save_data(data)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_access(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту")
        return
    
    user = update.effective_user
    
    welcome_text = (
        f"✨ *Gabbana&Home Parfum* ✨\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👋 *Добро пожаловать, {user.first_name}!*\n\n"
        f"📊 *Парфюмерный учет*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ *Основные функции:*\n"
        f"• 💰 Доход - продажа парфюма\n"
        f"• 💸 Расход - закупка/расходы\n"
        f"• 📊 Статистика - общая статистика\n"
        f"• 📋 Таблица парфюмов - все парфюмы\n"
        f"• 👥 Статистика коллег - по сотрудникам\n"
        f"• ✏️ Редактировать/Удалить\n\n"
        f"✨ *Все данные сохраняются в JSON*"
    )
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=main_keyboard)

async def handle_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления дохода"""
    if not check_access(update):
        return
    
    chat_id = update.effective_chat.id
    
    user_data[chat_id] = {
        'type': 'income',
        'state': INCOME_STATES['NAME'],
        'added_by': update.effective_user.first_name
    }
    
    await update.message.reply_text(
        "💵 *ДОХОД (Продажа парфюма)*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 *Шаг 1 из 7*\n\n"
        "✏️ *Введите название парфюма:*\n\n"
        "💡 *Примеры:*\n"
        "• Creed Aventus\n"
        "• Baccarat Rouge 540\n"
        "• Tom Ford Tobacco Vanille\n\n"
        "🔹 *Для отмены нажмите кнопку ниже*",
        parse_mode='Markdown',
        reply_markup=cancel_keyboard
    )

async def handle_income_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка названия парфюма"""
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        await update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    user_data[chat_id]['parfum_name'] = text
    user_data[chat_id]['state'] = INCOME_STATES['VOLUME']
    
    await update.message.reply_text(
        f"✅ Название: *{text}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 *Шаг 2 из 7*\n\n"
        f"🔢 *Выберите объем:*\n\n"
        f"💡 *Доступные объемы:* 6ml, 10ml",
        parse_mode='Markdown',
        reply_markup=volume_keyboard
    )

async def handle_income_volume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора объема"""
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        await update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    if text not in ['6ml', '10ml']:
        await update.message.reply_text(
            "❌ Пожалуйста, выберите объем из кнопок:",
            reply_markup=volume_keyboard
        )
        return
    
    user_data[chat_id]['volume'] = text
    user_data[chat_id]['state'] = INCOME_STATES['QUANTITY']
    
    await update.message.reply_text(
        f"✅ Объем: *{text}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 *Шаг 3 из 7*\n\n"
        f"🔢 *Введите количество флаконов:*\n\n"
        f"💡 *Примеры:* 1, 2, 3\n\n"
        f"🔹 *Для отмены нажмите кнопку ниже*",
        parse_mode='Markdown',
        reply_markup=cancel_keyboard
    )

async def handle_income_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода количества"""
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        await update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    try:
        quantity = int(text)
        if quantity <= 0:
            raise ValueError
        
        user_data[chat_id]['quantity'] = quantity
        user_data[chat_id]['state'] = INCOME_STATES['EMPLOYEE']
        
        await update.message.reply_text(
            f"✅ Количество: *{quantity} шт*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 4 из 7*\n\n"
            f"👤 *Выберите сотрудника:*",
            parse_mode='Markdown',
            reply_markup=employee_keyboard
        )
        
    except ValueError:
        await update.message.reply_text(
            "❌ Введите корректное число\n\n🔹 *Для отмены нажмите кнопку ниже*",
            parse_mode='Markdown',
            reply_markup=cancel_keyboard
        )

async def handle_income_employee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора сотрудника"""
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        await update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    # Извлекаем имя сотрудника
    employee = text.replace('👤 ', '')
    
    if employee not in EMPLOYEES:
        await update.message.reply_text(
            "❌ Пожалуйста, выберите сотрудника из кнопок:",
            reply_markup=employee_keyboard
        )
        return
    
    user_data[chat_id]['employee'] = employee
    user_data[chat_id]['state'] = INCOME_STATES['PAYMENT']
    
    await update.message.reply_text(
        f"✅ Сотрудник: *{employee}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 *Шаг 5 из 7*\n\n"
        f"💳 *Выберите способ оплаты:*",
        parse_mode='Markdown',
        reply_markup=payment_keyboard
    )

async def handle_income_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора способа оплаты"""
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        await update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    if 'Перевод' in text:
        user_data[chat_id]['payment'] = 'Перевод'
        user_data[chat_id]['state'] = INCOME_STATES['BANK']
        
        await update.message.reply_text(
            f"✅ Способ оплаты: *{text}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 6 из 7*\n\n"
            f"🏦 *Выберите банк:*",
            parse_mode='Markdown',
            reply_markup=bank_keyboard
        )
        
    elif 'Наличка' in text:
        user_data[chat_id]['payment'] = 'Наличка'
        user_data[chat_id]['bank'] = '-'
        user_data[chat_id]['state'] = INCOME_STATES['AMOUNT']
        
        await update.message.reply_text(
            f"✅ Способ оплаты: *{text}*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 7 из 7*\n\n"
            f"💰 *Введите сумму дохода:*\n\n"
            f"📝 *Форматы:* 1300, 2 500, 3 000.50\n\n"
            f"🔹 *Для отмены нажмите кнопку ниже*",
            parse_mode='Markdown',
            reply_markup=cancel_keyboard
        )
    else:
        await update.message.reply_text(
            "❌ Пожалуйста, выберите способ оплаты из кнопок:",
            reply_markup=payment_keyboard
        )

async def handle_income_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора банка"""
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        await update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    bank = text.replace('🏦 ', '') if '🏦' in text else text
    
    user_data[chat_id]['bank'] = bank
    user_data[chat_id]['state'] = INCOME_STATES['AMOUNT']
    
    await update.message.reply_text(
        f"✅ Банк: *{bank}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 *Шаг 7 из 7*\n\n"
        f"💰 *Введите сумму дохода:*\n\n"
        f"📝 *Форматы:* 1300, 2 500, 3 000.50\n\n"
        f"🔹 *Для отмены нажмите кнопку ниже*",
        parse_mode='Markdown',
        reply_markup=cancel_keyboard
    )

async def handle_income_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода суммы и сохранение"""
    chat_id = update.effective_chat.id
    user = update.effective_user
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        await update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    try:
        amount = float(text.replace(' ', '').replace(',', '.'))
        
        data = user_data.pop(chat_id)
        
        # Создаем операцию
        operation = {
            'id': get_next_id(),
            'date': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'type': 'income',
            'type_display': '💰 Доход',
            'parfum_name': data['parfum_name'],
            'volume': data['volume'],
            'quantity': data['quantity'],
            'employee': data['employee'],
            'payment': data['payment'],
            'bank': data.get('bank', '-'),
            'amount': amount,
            'description': f"{data['parfum_name']} {data['volume']} x{data['quantity']}",
            'added_by': data['added_by']
        }
        
        # Сохраняем
        add_operation(operation)
        
        # Форматируем сумму
        formatted_amount = f"{amount:,.0f} ₽".replace(',', ' ')
        if amount != int(amount):
            formatted_amount = f"{amount:,.2f} ₽".replace(',', ' ')
        
        report = (
            f"✅ *ПРОДАЖА #{operation['id']} ЗАПИСАНА!*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *Парфюм:* {data['parfum_name']}\n"
            f"📌 *Объем:* {data['volume']}\n"
            f"📌 *Кол-во:* {data['quantity']} шт\n"
            f"👤 *Сотрудник:* {data['employee']}\n"
            f"💳 *Оплата:* {data['payment']}\n"
        )
        
        if data['payment'] == 'Перевод':
            report += f"🏦 *Банк:* {data.get('bank', '-')}\n"
        
        report += f"💰 *Сумма:* {formatted_amount}\n"
        report += f"📝 *Запись добавил:* {data['added_by']}\n\n"
        report += f"✨ *Спасибо за продажу!*"
        
        await update.message.reply_text(report, parse_mode='Markdown', reply_markup=main_keyboard)
        
        # Уведомление всем
        notification = (
            f"🔔 *НОВАЯ ПРОДАЖА #{operation['id']}*\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"👤 *Сотрудник:* {data['employee']}\n"
            f"📦 {data['parfum_name']} {data['volume']} x{data['quantity']}\n"
            f"💰 {formatted_amount}\n"
            f"💳 {data['payment']}"
        )
        
        for admin_id in ALLOWED_IDS:
            try:
                await context.bot.send_message(chat_id=admin_id, text=notification, parse_mode='Markdown')
            except:
                pass
        
    except ValueError:
        await update.message.reply_text(
            "❌ Введите корректную сумму\n\n🔹 *Для отмены нажмите кнопку ниже*",
            parse_mode='Markdown',
            reply_markup=cancel_keyboard
        )

async def handle_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления расхода"""
    if not check_access(update):
        return
    
    chat_id = update.effective_chat.id
    
    if update.message.text == '🔙 Отмена':
        await update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    user_data[chat_id] = {
        'type': 'expense',
        'state': EXPENSE_STATES['AMOUNT'],
        'added_by': update.effective_user.first_name
    }
    
    await update.message.reply_text(
        "💳 *РАСХОД*\n"
        "━━━━━━━━━━━━━━\n\n"
        "✏️ *Введите сумму расхода:*\n\n"
        "📝 *Форматы:* 1300, 2 500, 3 000.50\n\n"
        "🔹 *Для отмены нажмите кнопку ниже*",
        parse_mode='Markdown',
        reply_markup=cancel_keyboard
    )

async def handle_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода суммы расхода"""
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        await update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    try:
        amount = float(text.replace(' ', '').replace(',', '.'))
        user_data[chat_id]['amount'] = amount
        user_data[chat_id]['state'] = EXPENSE_STATES['DESCRIPTION']
        
        formatted_amount = f"{amount:,.0f} ₽".replace(',', ' ')
        if amount != int(amount):
            formatted_amount = f"{amount:,.2f} ₽".replace(',', ' ')
        
        await update.message.reply_text(
            f"✅ *Сумма:* {formatted_amount}\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"📝 *Введите описание расхода:*\n\n"
            f"💡 Например: Закупка парфюма, Аренда, Реклама\n\n"
            f"🔹 *Для отмены нажмите кнопку ниже*",
            parse_mode='Markdown',
            reply_markup=cancel_keyboard
        )
    except ValueError:
        await update.message.reply_text(
            "❌ Введите корректную сумму\n\n🔹 *Для отмены нажмите кнопку ниже*",
            parse_mode='Markdown',
            reply_markup=cancel_keyboard
        )

async def handle_expense_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода описания расхода"""
    chat_id = update.effective_chat.id
    description = update.message.text
    
    if description == '🔙 Отмена':
        del user_data[chat_id]
        await update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    user_data[chat_id]['description'] = description
    user_data[chat_id]['state'] = EXPENSE_STATES['EMPLOYEE']
    
    await update.message.reply_text(
        f"✅ Описание: *{description}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 *Выберите сотрудника:*",
        parse_mode='Markdown',
        reply_markup=employee_keyboard
    )

async def handle_expense_employee(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора сотрудника для расхода и сохранение"""
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        await update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    employee = text.replace('👤 ', '')
    
    if employee not in EMPLOYEES:
        await update.message.reply_text(
            "❌ Пожалуйста, выберите сотрудника из кнопок:",
            reply_markup=employee_keyboard
        )
        return
    
    data = user_data.pop(chat_id)
    
    # Создаем операцию
    operation = {
        'id': get_next_id(),
        'date': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'type': 'expense',
        'type_display': '💸 Расход',
        'amount': data['amount'],
        'description': data['description'],
        'employee': employee,
        'added_by': data['added_by']
    }
    
    # Сохраняем
    add_operation(operation)
    
    formatted_amount = f"{data['amount']:,.0f} ₽".replace(',', ' ')
    if data['amount'] != int(data['amount']):
        formatted_amount = f"{data['amount']:,.2f} ₽".replace(',', ' ')
    
    await update.message.reply_text(
        f"✅ *РАСХОД #{operation['id']} ЗАПИСАН!*\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"💰 *Сумма:* {formatted_amount}\n"
        f"📋 *Описание:* {data['description']}\n"
        f"👤 *Сотрудник:* {employee}\n"
        f"📝 *Запись добавил:* {data['added_by']}",
        parse_mode='Markdown',
        reply_markup=main_keyboard
    )
    
    # Уведомление всем
    notification = (
        f"🔔 *НОВЫЙ РАСХОД #{operation['id']}*\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"👤 *Сотрудник:* {employee}\n"
        f"💰 {formatted_amount}\n"
        f"📋 {data['description']}"
    )
    
    for admin_id in ALLOWED_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=notification, parse_mode='Markdown')
        except:
            pass

async def show_parfum_table(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает таблицу всех парфюмов"""
    if not check_access(update):
        return
    
    operations = get_all_operations()
    
    # Собираем все доходы по парфюмам
    parfums = {}
    for op in operations:
        if op['type'] == 'income':
            key = f"{op['parfum_name']} ({op['volume']})"
            if key not in parfums:
                parfums[key] = {
                    'name': op['parfum_name'],
                    'volume': op['volume'],
                    'total_quantity': 0,
                    'total_amount': 0,
                    'sales': []
                }
            parfums[key]['total_quantity'] += op['quantity']
            parfums[key]['total_amount'] += op['amount']
            parfums[key]['sales'].append(op)
    
    if not parfums:
        await update.message.reply_text("📭 Нет данных о парфюмах", reply_markup=main_keyboard)
        return
    
    # Сортируем по сумме продаж
    sorted_parfums = sorted(parfums.items(), key=lambda x: x[1]['total_amount'], reverse=True)
    
    report = "📋 *ТАБЛИЦА ПАРФЮМОВ*\n"
    report += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for key, data in sorted_parfums:
        formatted_amount = f"{data['total_amount']:,.0f} ₽".replace(',', ' ')
        report += (
            f"📌 *{data['name']}*\n"
            f"   • Объем: {data['volume']}\n"
            f"   • Продано: {data['total_quantity']} шт\n"
            f"   • На сумму: `{formatted_amount}`\n"
            f"   • Продаж: {len(data['sales'])}\n\n"
        )
    
    # Статистика по объемам
    ml6_total = sum(data['total_amount'] for key, data in parfums.items() if '6ml' in key)
    ml10_total = sum(data['total_amount'] for key, data in parfums.items() if '10ml' in key)
    
    report += "━━━━━━━━━━━━━━━━━━━━\n"
    report += f"📊 *6ml:* {ml6_total:,.0f} ₽\n".replace(',', ' ')
    report += f"📊 *10ml:* {ml10_total:,.0f} ₽\n".replace(',', ' ')
    
    await update.message.reply_text(report, parse_mode='Markdown', reply_markup=main_keyboard)

async def show_employee_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает статистику по сотрудникам"""
    if not check_access(update):
        return
    
    operations = get_all_operations()
    
    if not operations:
        await update.message.reply_text("📭 Нет данных", reply_markup=main_keyboard)
        return
    
    stats = {}
    for employee in EMPLOYEES:
        stats[employee] = {
            'income': 0,
            'income_count': 0,
            'expense': 0,
            'expense_count': 0,
            'parfums': {}
        }
    
    for op in operations:
        employee = op.get('employee', 'Не указан')
        if employee in stats:
            if op['type'] == 'income':
                stats[employee]['income'] += op['amount']
                stats[employee]['income_count'] += 1
                
                # Собираем парфюмы
                key = f"{op['parfum_name']} {op['volume']}"
                if key not in stats[employee]['parfums']:
                    stats[employee]['parfums'][key] = {
                        'quantity': 0,
                        'amount': 0
                    }
                stats[employee]['parfums'][key]['quantity'] += op['quantity']
                stats[employee]['parfums'][key]['amount'] += op['amount']
                
            elif op['type'] == 'expense':
                stats[employee]['expense'] += op['amount']
                stats[employee]['expense_count'] += 1
    
    report = "👥 *СТАТИСТИКА ПО СОТРУДНИКАМ*\n"
    report += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for employee in EMPLOYEES:
        data = stats[employee]
        income_formatted = f"{data['income']:,.0f} ₽".replace(',', ' ')
        expense_formatted = f"{data['expense']:,.0f} ₽".replace(',', ' ')
        profit_formatted = f"{data['income'] - data['expense']:,.0f} ₽".replace(',', ' ')
        
        report += f"👤 *{employee}*\n"
        report += f"   📈 Доходы: `{income_formatted}` ({data['income_count']} шт)\n"
        report += f"   📉 Расходы: `{expense_formatted}` ({data['expense_count']} шт)\n"
        report += f"   💎 Итог: `{profit_formatted}`\n"
        
        if data['parfums']:
            report += f"   📦 Продажи:\n"
            # Топ 3 парфюма
            top_parfums = sorted(data['parfums'].items(), key=lambda x: x[1]['amount'], reverse=True)[:3]
            for parfum, pdata in top_parfums:
                pamount = f"{pdata['amount']:,.0f} ₽".replace(',', ' ')
                report += f"      • {parfum}: {pdata['quantity']} шт ({pamount})\n"
        report += "\n"
    
    await update.message.reply_text(report, parse_mode='Markdown', reply_markup=main_keyboard)

async def show_all_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает общую статистику"""
    if not check_access(update):
        return
    
    operations = get_all_operations()
    
    if not operations:
        await update.message.reply_text("📭 Нет данных", reply_markup=main_keyboard)
        return
    
    income_total = sum(op['amount'] for op in operations if op['type'] == 'income')
    expense_total = sum(op['amount'] for op in operations if op['type'] == 'expense')
    income_count = len([op for op in operations if op['type'] == 'income'])
    expense_count = len([op for op in operations if op['type'] == 'expense'])
    
    income_formatted = f"{income_total:,.0f} ₽".replace(',', ' ')
    expense_formatted = f"{expense_total:,.0f} ₽".replace(',', ' ')
    profit_formatted = f"{income_total - expense_total:,.0f} ₽".replace(',', ' ')
    
    # Статистика по объему
    ml6_total = sum(op['amount'] for op in operations if op['type'] == 'income' and op.get('volume') == '6ml')
    ml10_total = sum(op['amount'] for op in operations if op['type'] == 'income' and op.get('volume') == '10ml')
    
    # Топ парфюмы
    parfums = {}
    for op in operations:
        if op['type'] == 'income':
            key = op['parfum_name']
            if key not in parfums:
                parfums[key] = {
                    'amount': 0,
                    'quantity': 0
                }
            parfums[key]['amount'] += op['amount']
            parfums[key]['quantity'] += op['quantity']
    
    # Формируем отчет (исправлено!)
    report = "📊 *ОБЩАЯ СТАТИСТИКА*\n"
    report += "━━━━━━━━━━━━━━━━━━━━\n\n"
    report += f"📈 *Доходы:* `{income_formatted}` ({income_count} шт)\n"
    report += f"📉 *Расходы:* `{expense_formatted}` ({expense_count} шт)\n"
    report += f"💎 *Итог:* `{profit_formatted}`\n\n"
    report += f"📦 *По объему:*\n"
    report += f"   • 6ml: {ml6_total:,.0f} ₽\n".replace(',', ' ')
    report += f"   • 10ml: {ml10_total:,.0f} ₽\n".replace(',', ' ')
    
    if parfums:
        report += f"\n🏆 *Топ парфюмов:*\n"
        top_parfums = sorted(parfums.items(), key=lambda x: x[1]['amount'], reverse=True)[:5]
        for parfum, data in top_parfums:
            pamount = f"{data['amount']:,.0f} ₽".replace(',', ' ')
            report += f"   • {parfum}: {data['quantity']} шт ({pamount})\n"
    
    await update.message.reply_text(report, parse_mode='Markdown', reply_markup=main_keyboard)

async def show_operations_for_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает последние операции для редактирования"""
    if not check_access(update):
        return
    
    if update.message.text == '🔙 Отмена':
        await update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    operations = get_all_operations()
    
    if not operations:
        await update.message.reply_text("📭 Нет операций", reply_markup=main_keyboard)
        return
    
    # Сортируем по дате (новые сверху) и берем последние 15
    operations.sort(key=lambda x: x['id'], reverse=True)
    operations = operations[:15]
    
    keyboard = []
    for op in operations:
        amount = op['amount']
        formatted_amount = f"{amount:,.0f} ₽".replace(',', ' ')
        if amount != int(amount):
            formatted_amount = f"{amount:,.2f} ₽".replace(',', ' ')
        
        if op['type'] == 'income':
            desc = f"{op['parfum_name']} {op['volume']} x{op['quantity']} - {op['employee']}"
        else:
            desc = op['description'][:20] + "..." if len(op['description']) > 20 else op['description']
        
        button_text = f"#{op['id']} {op['type_display']} {formatted_amount} - {desc}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"edit_op_{op['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Отмена", callback_data="edit_cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "✏️ *ВЫБЕРИТЕ ОПЕРАЦИЮ:*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔹 *Последние 15 операций:*",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def edit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка редактирования"""
    query = update.callback_query
    await query.answer()
    
    if not check_access(update):
        await query.edit_message_text("❌ Нет доступа")
        return
    
    data = query.data
    
    if data == "edit_cancel":
        await query.edit_message_text("🔙 Отменено")
        await query.message.reply_text("Главное меню:", reply_markup=main_keyboard)
        return
    
    if data.startswith("edit_op_"):
        op_id = int(data.split('_')[2])
        
        operations = get_all_operations()
        op = next((o for o in operations if o['id'] == op_id), None)
        
        if not op:
            await query.edit_message_text("❌ Операция не найдена")
            return
        
        amount = op['amount']
        formatted_amount = f"{amount:,.0f} ₽".replace(',', ' ')
        if amount != int(amount):
            formatted_amount = f"{amount:,.2f} ₽".replace(',', ' ')
        
        if op['type'] == 'income':
            op_text = (
                f"📌 *ПРОДАЖА #{op_id}*\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📅 Дата: {op['date']}\n"
                f"📦 Парфюм: {op['parfum_name']}\n"
                f"🔢 Объем: {op['volume']}\n"
                f"📊 Кол-во: {op['quantity']} шт\n"
                f"👤 Сотрудник: {op['employee']}\n"
                f"💳 Оплата: {op['payment']}\n"
                f"🏦 Банк: {op.get('bank', '-')}\n"
                f"💰 Сумма: {formatted_amount}\n"
                f"📝 Добавил: {op['added_by']}"
            )
        else:
            op_text = (
                f"📌 *РАСХОД #{op_id}*\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📅 Дата: {op['date']}\n"
                f"💰 Сумма: {formatted_amount}\n"
                f"📋 Описание: {op['description']}\n"
                f"👤 Сотрудник: {op['employee']}\n"
                f"📝 Добавил: {op['added_by']}"
            )
        
        keyboard = [
            [InlineKeyboardButton("💰 Изменить сумму", callback_data=f"edit_sum_{op_id}")],
            [InlineKeyboardButton("❌ Удалить операцию", callback_data=f"edit_del_{op_id}")],
            [InlineKeyboardButton("🔙 Назад к списку", callback_data="edit_back_to_list")]
        ]
        
        if op['type'] == 'income':
            keyboard.insert(1, [InlineKeyboardButton("👤 Изменить сотрудника", callback_data=f"edit_employee_{op_id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(op_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif data.startswith("edit_sum_"):
        op_id = int(data.split('_')[2])
        context.user_data['edit_op_id'] = op_id
        context.user_data['edit_action'] = 'sum'
        await query.edit_message_text(
            f"✏️ Введите новую сумму для операции #{op_id}:\n\n"
            f"📝 Пример: 15000 или 15 000\n\n"
            f"🔹 *Для отмены нажмите /cancel*"
        )
    
    elif data.startswith("edit_employee_"):
        op_id = int(data.split('_')[2])
        context.user_data['edit_op_id'] = op_id
        context.user_data['edit_action'] = 'employee'
        
        # Создаем клавиатуру с сотрудниками
        keyboard = []
        for emp in EMPLOYEES:
            keyboard.append([InlineKeyboardButton(f"👤 {emp}", callback_data=f"edit_set_employee_{op_id}_{emp}")])
        keyboard.append([InlineKeyboardButton("🔙 Отмена", callback_data=f"edit_op_{op_id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"✏️ Выберите нового сотрудника для операции #{op_id}:",
            reply_markup=reply_markup
        )
    
    elif data.startswith("edit_set_employee_"):
        parts = data.split('_')
        op_id = int(parts[3])
        new_employee = parts[4]
        
        operations = get_all_operations()
        for i, op in enumerate(operations):
            if op['id'] == op_id:
                op['employee'] = new_employee
                update_operation(op_id, op)
                break
        
        await query.edit_message_text(f"✅ Сотрудник операции #{op_id} изменен на {new_employee}")
        
        # Уведомление
        notification = f"✏️ *Операция #{op_id} изменена*\n👤 {update.effective_user.first_name}\n👤 Новый сотрудник: {new_employee}"
        for admin_id in ALLOWED_IDS:
            try:
                await context.bot.send_message(chat_id=admin_id, text=notification, parse_mode='Markdown')
            except:
                pass
        
        await query.message.reply_text("Главное меню:", reply_markup=main_keyboard)
    
    elif data.startswith("edit_del_"):
        op_id = int(data.split('_')[2])
        
        keyboard = [
            [InlineKeyboardButton("✅ Да, удалить", callback_data=f"edit_confirm_del_{op_id}")],
            [InlineKeyboardButton("❌ Нет, отмена", callback_data=f"edit_op_{op_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"⚠️ *Вы уверены, что хотите удалить операцию #{op_id}?*",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif data.startswith("edit_confirm_del_"):
        op_id = int(data.split('_')[3])
        
        delete_operation(op_id)
        
        await query.edit_message_text(f"✅ Операция #{op_id} удалена")
        
        notification = f"🗑 *Операция #{op_id} удалена*\n👤 {update.effective_user.first_name}"
        for admin_id in ALLOWED_IDS:
            try:
                await context.bot.send_message(chat_id=admin_id, text=notification, parse_mode='Markdown')
            except:
                pass
        
        await query.message.reply_text("Главное меню:", reply_markup=main_keyboard)
    
    elif data == "edit_back_to_list":
        await show_operations_for_edit(update, context)

async def handle_edit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода новых данных при редактировании"""
    if 'edit_op_id' not in context.user_data:
        return
    
    if update.message.text == '/cancel':
        del context.user_data['edit_op_id']
        del context.user_data['edit_action']
        await update.message.reply_text("🔙 Редактирование отменено", reply_markup=main_keyboard)
        return
    
    op_id = context.user_data['edit_op_id']
    action = context.user_data['edit_action']
    text = update.message.text
    
    if action == 'sum':
        try:
            new_sum = float(text.replace(' ', '').replace(',', '.'))
            
            operations = get_all_operations()
            for op in operations:
                if op['id'] == op_id:
                    op['amount'] = new_sum
                    update_operation(op_id, op)
                    break
            
            formatted_sum = f"{new_sum:,.0f} ₽".replace(',', ' ')
            if new_sum != int(new_sum):
                formatted_sum = f"{new_sum:,.2f} ₽".replace(',', ' ')
            
            await update.message.reply_text(f"✅ Сумма операции #{op_id} изменена на {formatted_sum}", reply_markup=main_keyboard)
            
            notification = f"✏️ *Операция #{op_id} изменена*\n👤 {update.effective_user.first_name}\n💰 Новая сумма: {formatted_sum}"
            for admin_id in ALLOWED_IDS:
                try:
                    await context.bot.send_message(chat_id=admin_id, text=notification, parse_mode='Markdown')
                except:
                    pass
            
        except ValueError:
            await update.message.reply_text(
                "❌ Введите корректную сумму\n\n🔹 Для отмены нажмите /cancel"
            )
            return
    
    del context.user_data['edit_op_id']
    del context.user_data['edit_action']

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Основной обработчик"""
    if not check_access(update):
        await update.message.reply_text("❌ У вас нет доступа к этому боту")
        return
    
    chat_id = update.effective_chat.id
    text = update.message.text
    
    # Глобальная отмена
    if text == '🔙 Отмена':
        if chat_id in user_data:
            del user_data[chat_id]
        context.user_data.clear()
        await update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    # Проверяем ожидание ввода при редактировании
    if 'edit_op_id' in context.user_data:
        await handle_edit_input(update, context)
        return
    
    # Обработка состояний
    if chat_id in user_data:
        state_data = user_data[chat_id]
        
        if state_data.get('type') == 'income':
            state = state_data.get('state')
            
            if state == INCOME_STATES['NAME']:
                await handle_income_name(update, context)
            elif state == INCOME_STATES['VOLUME']:
                await handle_income_volume(update, context)
            elif state == INCOME_STATES['QUANTITY']:
                await handle_income_quantity(update, context)
            elif state == INCOME_STATES['EMPLOYEE']:
                await handle_income_employee(update, context)
            elif state == INCOME_STATES['PAYMENT']:
                await handle_income_payment(update, context)
            elif state == INCOME_STATES['BANK']:
                await handle_income_bank(update, context)
            elif state == INCOME_STATES['AMOUNT']:
                await handle_income_amount(update, context)
        
        elif state_data.get('type') == 'expense':
            state = state_data.get('state')
            
            if state == EXPENSE_STATES['AMOUNT']:
                await handle_expense_amount(update, context)
            elif state == EXPENSE_STATES['DESCRIPTION']:
                await handle_expense_description(update, context)
            elif state == EXPENSE_STATES['EMPLOYEE']:
                await handle_expense_employee(update, context)
    
    # Основное меню
    elif text == '💰 Доход':
        await handle_income(update, context)
    elif text == '💸 Расход':
        await handle_expense(update, context)
    elif text == '📊 Статистика':
        await show_all_statistics(update, context)
    elif text == '📋 Таблица парфюмов':
        await show_parfum_table(update, context)
    elif text == '👥 Статистика коллег':
        await show_employee_stats(update, context)
    elif text == '✏️ Редактировать/Удалить':
        await show_operations_for_edit(update, context)
    else:
        await update.message.reply_text("Используйте кнопки 👇", reply_markup=main_keyboard)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /cancel"""
    chat_id = update.effective_chat.id
    
    if chat_id in user_data:
        del user_data[chat_id]
    context.user_data.clear()
    
    await update.message.reply_text("🔙 Действие отменено", reply_markup=main_keyboard)

def main():
    print("🚀 Бот запускается...")
    print("✅ Данные будут сохраняться в gabbana_data.json")
    
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(edit_callback, pattern="^edit_"))
    
    print("✅ Бот готов к работе!")
    app.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Бот остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")