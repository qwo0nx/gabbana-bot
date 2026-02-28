import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from datetime import datetime
import json
import os

# ========== НАСТРОЙКИ ==========
TOKEN = "8761306495:AAFWICUB62qgO2h-1va3Y50DHZPGvCGakjw"
DATA_FILE = "gabbana_data.json"
ALLOWED_IDS = [6578266978, 5029738209, 7950080109]
EMPLOYEES = ["Матвей", "Дима", "Никита"]

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== КЛАВИАТУРЫ ==========
main_keyboard = ReplyKeyboardMarkup([
    ['💰 Доход', '💸 Расход'],
    ['📊 Статистика', '📋 Таблица парфюмов'],
    ['👥 Статистика коллег', '✏️ Редактировать/Удалить']
], resize_keyboard=True)

cancel_keyboard = ReplyKeyboardMarkup([['🔙 Отмена']], resize_keyboard=True)

volume_keyboard = ReplyKeyboardMarkup([
    ['6ml', '10ml'],
    ['🔙 Отмена']
], resize_keyboard=True)

payment_keyboard = ReplyKeyboardMarkup([
    ['💳 Перевод', '💵 Наличка'],
    ['🔙 Отмена']
], resize_keyboard=True)

bank_keyboard = ReplyKeyboardMarkup([
    ['🏦 Сбер', '🏦 Тинькофф', '🏦 ВТБ'],
    ['🏦 Альфа', '🏦 Райффайзен', '🏦 Другой'],
    ['🔙 Отмена']
], resize_keyboard=True)

employee_keyboard = ReplyKeyboardMarkup([
    ['👤 Матвей', '👤 Дима', '👤 Никита'],
    ['🔙 Отмена']
], resize_keyboard=True)

# ========== СОСТОЯНИЯ ==========
INCOME_STATES = {
    'NAME': 1, 'VOLUME': 2, 'QUANTITY': 3,
    'EMPLOYEE': 4, 'PAYMENT': 5, 'BANK': 6, 'AMOUNT': 7
}

EXPENSE_STATES = {
    'AMOUNT': 1, 'DESCRIPTION': 2, 'EMPLOYEE': 3
}

user_data = {}

# ========== РАБОТА С ДАННЫМИ ==========
def check_access(update):
    return update.effective_user.id in ALLOWED_IDS

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'operations': [], 'next_id': 1}
    return {'operations': [], 'next_id': 1}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_next_id():
    data = load_data()
    next_id = data.get('next_id', 1)
    data['next_id'] = next_id + 1
    save_data(data)
    return next_id

def add_operation(operation):
    data = load_data()
    if 'operations' not in data:
        data['operations'] = []
    data['operations'].append(operation)
    save_data(data)

def get_all_operations():
    return load_data().get('operations', [])

def delete_operation(op_id):
    data = load_data()
    data['operations'] = [op for op in data['operations'] if op['id'] != op_id]
    save_data(data)

def update_operation(op_id, updated_op):
    data = load_data()
    for i, op in enumerate(data['operations']):
        if op['id'] == op_id:
            data['operations'][i] = updated_op
            break
    save_data(data)

# ========== СТАРТ ==========
def start(update, context):
    if not check_access(update):
        update.message.reply_text("❌ У вас нет доступа к этому боту")
        return
    
    user = update.effective_user
    
    welcome_text = (
        f"✨ *Gabbana&Home Parfum* ✨\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👋 *Добро пожаловать, {user.first_name}!*\n\n"
        f"📊 *Парфюмерный учет*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"✅ *Основные функции:*\n"
        f"• 💰 Доход - продажа парфюма (6ml/10ml)\n"
        f"• 💸 Расход - закупки, аренда, реклама\n"
        f"• 📊 Статистика - общая статистика\n"
        f"• 📋 Таблица парфюмов - все продажи по парфюмам\n"
        f"• 👥 Статистика коллег - по сотрудникам\n"
        f"• ✏️ Редактировать/Удалить - изменить или удалить запись\n\n"
        f"📝 *Как добавлять доход:*\n"
        f"1️⃣ Название парфюма\n"
        f"2️⃣ Объем (6ml или 10ml)\n"
        f"3️⃣ Количество флаконов\n"
        f"4️⃣ Выбор сотрудника\n"
        f"5️⃣ Способ оплаты\n"
        f"6️⃣ Банк (если перевод)\n"
        f"7️⃣ Сумма\n\n"
        f"✨ *Все данные сохраняются автоматически!*"
    )
    
    update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=main_keyboard)

# ========== ДОХОД ==========
def income_start(update, context):
    chat_id = update.effective_chat.id
    
    user_data[chat_id] = {
        'type': 'income',
        'state': INCOME_STATES['NAME'],
        'added_by': update.effective_user.first_name
    }
    
    text = (
        "💵 *ДОХОД (Продажа парфюма)*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 *Шаг 1 из 7*\n\n"
        "✏️ *Введите название парфюма:*\n\n"
        "💡 *Примеры:*\n"
        "• Creed Aventus\n"
        "• Baccarat Rouge 540\n"
        "• Tom Ford Tobacco Vanille\n"
        "• Maison Francis Kurkdjian\n\n"
        "🔹 *Для отмены нажмите кнопку ниже*"
    )
    
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=cancel_keyboard)

def income_name(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    user_data[chat_id]['parfum_name'] = text
    user_data[chat_id]['state'] = INCOME_STATES['VOLUME']
    
    text = (
        f"✅ *Название:* {text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 *Шаг 2 из 7*\n\n"
        f"🔢 *Выберите объем:*\n\n"
        f"📦 *Доступные объемы:*\n"
        f"• 6ml - пробники\n"
        f"• 10ml - миниатюры\n\n"
        f"🔹 *Нажмите на кнопку с нужным объемом*"
    )
    
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=volume_keyboard)

def income_volume(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    if text not in ['6ml', '10ml']:
        update.message.reply_text(
            "❌ *Ошибка!*\n"
            "Пожалуйста, выберите объем из кнопок ниже:",
            parse_mode='Markdown',
            reply_markup=volume_keyboard
        )
        return
    
    user_data[chat_id]['volume'] = text
    user_data[chat_id]['state'] = INCOME_STATES['QUANTITY']
    
    text = (
        f"✅ *Объем:* {text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 *Шаг 3 из 7*\n\n"
        f"🔢 *Введите количество флаконов:*\n\n"
        f"💡 *Примеры:*\n"
        f"• 1 (один флакон)\n"
        f"• 2 (два флакона)\n"
        f"• 3 (три флакона)\n\n"
        f"🔹 *Для отмены нажмите кнопку ниже*"
    )
    
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=cancel_keyboard)

def income_quantity(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    try:
        quantity = int(text)
        if quantity <= 0:
            raise ValueError
        
        user_data[chat_id]['quantity'] = quantity
        user_data[chat_id]['state'] = INCOME_STATES['EMPLOYEE']
        
        text = (
            f"✅ *Количество:* {quantity} шт\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 4 из 7*\n\n"
            f"👤 *Выберите сотрудника, который продал:*\n\n"
            f"💡 *Нажмите на имя сотрудника:*"
        )
        
        update.message.reply_text(text, parse_mode='Markdown', reply_markup=employee_keyboard)
        
    except ValueError:
        update.message.reply_text(
            "❌ *Ошибка!*\n"
            "Введите корректное число (например: 1, 2, 3)\n\n"
            "🔹 *Для отмены нажмите кнопку ниже*",
            parse_mode='Markdown',
            reply_markup=cancel_keyboard
        )

def income_employee(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    employee = text.replace('👤 ', '')
    
    if employee not in EMPLOYEES:
        update.message.reply_text(
            "❌ *Ошибка!*\n"
            "Пожалуйста, выберите сотрудника из кнопок:",
            parse_mode='Markdown',
            reply_markup=employee_keyboard
        )
        return
    
    user_data[chat_id]['employee'] = employee
    user_data[chat_id]['state'] = INCOME_STATES['PAYMENT']
    
    text = (
        f"✅ *Сотрудник:* {employee}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 *Шаг 5 из 7*\n\n"
        f"💳 *Выберите способ оплаты:*\n\n"
        f"• 💳 Перевод - безналичная оплата\n"
        f"• 💵 Наличка - оплата наличными"
    )
    
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=payment_keyboard)

def income_payment(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    if 'Перевод' in text:
        user_data[chat_id]['payment'] = 'Перевод'
        user_data[chat_id]['state'] = INCOME_STATES['BANK']
        
        text = (
            f"✅ *Способ оплаты:* {text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 6 из 7*\n\n"
            f"🏦 *Выберите банк:*\n\n"
            f"• Сбер\n"
            f"• Тинькофф\n"
            f"• ВТБ\n"
            f"• Альфа\n"
            f"• Райффайзен\n"
            f"• Другой"
        )
        
        update.message.reply_text(text, parse_mode='Markdown', reply_markup=bank_keyboard)
        
    elif 'Наличка' in text:
        user_data[chat_id]['payment'] = 'Наличка'
        user_data[chat_id]['bank'] = '-'
        user_data[chat_id]['state'] = INCOME_STATES['AMOUNT']
        
        text = (
            f"✅ *Способ оплаты:* {text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 7 из 7*\n\n"
            f"💰 *Введите сумму дохода:*\n\n"
            f"📝 *Форматы ввода:*\n"
            f"• `1300` → 1 300 ₽\n"
            f"• `2 500` → 2 500 ₽\n"
            f"• `3 000.50` → 3 000.50 ₽\n\n"
            f"💡 *Пример:* `15000` или `15 000`\n\n"
            f"🔹 *Для отмены нажмите кнопку ниже*"
        )
        
        update.message.reply_text(text, parse_mode='Markdown', reply_markup=cancel_keyboard)
    else:
        update.message.reply_text(
            "❌ *Ошибка!*\n"
            "Пожалуйста, выберите способ оплаты из кнопок:",
            parse_mode='Markdown',
            reply_markup=payment_keyboard
        )

def income_bank(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    bank = text.replace('🏦 ', '') if '🏦' in text else text
    bank = bank.replace('Другой', 'Другой банк')
    
    user_data[chat_id]['bank'] = bank
    user_data[chat_id]['state'] = INCOME_STATES['AMOUNT']
    
    text = (
        f"✅ *Банк:* {bank}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 *Шаг 7 из 7*\n\n"
        f"💰 *Введите сумму дохода:*\n\n"
        f"📝 *Форматы ввода:*\n"
        f"• `1300` → 1 300 ₽\n"
        f"• `2 500` → 2 500 ₽\n"
        f"• `3 000.50` → 3 000.50 ₽\n\n"
        f"💡 *Пример:* `15000` или `15 000`\n\n"
        f"🔹 *Для отмены нажмите кнопку ниже*"
    )
    
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=cancel_keyboard)

def income_amount(update, context):
    chat_id = update.effective_chat.id
    user = update.effective_user
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    try:
        amount = float(text.replace(' ', '').replace(',', '.'))
        
        data = user_data.pop(chat_id)
        
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
        
        add_operation(operation)
        
        # Форматируем сумму
        formatted_amount = f"{amount:,.0f} ₽".replace(',', ' ')
        if amount != int(amount):
            formatted_amount = f"{amount:,.2f} ₽".replace(',', ' ')
        
        # Формируем отчет
        report = (
            f"✅ *ПРОДАЖА #{operation['id']} ЗАПИСАНА!*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *Парфюм:* {data['parfum_name']}\n"
            f"📌 *Объем:* {data['volume']}\n"
            f"📌 *Кол-во:* {data['quantity']} шт\n"
            f"👤 *Продавец:* {data['employee']}\n"
            f"💳 *Оплата:* {data['payment']}\n"
        )
        
        if data['payment'] == 'Перевод':
            report += f"🏦 *Банк:* {data.get('bank', '-')}\n"
        
        report += f"💰 *Сумма:* {formatted_amount}\n"
        report += f"📝 *Запись добавил:* {data['added_by']}\n\n"
        report += f"✨ *Спасибо за продажу!*"
        
        update.message.reply_text(report, parse_mode='Markdown', reply_markup=main_keyboard)
        
    except ValueError:
        update.message.reply_text(
            "❌ *Ошибка!*\n"
            "Введите корректную сумму\n\n"
            "📝 *Форматы ввода:*\n"
            "• `1300` → 1 300 ₽\n"
            "• `2 500` → 2 500 ₽\n"
            "• `3 000.50` → 3 000.50 ₽\n\n"
            "🔹 *Для отмены нажмите кнопку ниже*",
            parse_mode='Markdown',
            reply_markup=cancel_keyboard
        )

# ========== РАСХОД ==========
def expense_start(update, context):
    chat_id = update.effective_chat.id
    
    user_data[chat_id] = {
        'type': 'expense',
        'state': EXPENSE_STATES['AMOUNT'],
        'added_by': update.effective_user.first_name
    }
    
    text = (
        "💳 *РАСХОД*\n"
        "━━━━━━━━━━━━━━\n\n"
        "📝 *Шаг 1 из 3*\n\n"
        "✏️ *Введите сумму расхода:*\n\n"
        "📝 *Форматы ввода:*\n"
        "• `1300` → 1 300 ₽\n"
        "• `2 500` → 2 500 ₽\n"
        "• `3 000.50` → 3 000.50 ₽\n\n"
        "💡 *Примеры расходов:*\n"
        "• Закупка парфюма\n"
        "• Аренда\n"
        "• Реклама\n"
        "• Упаковка\n\n"
        "🔹 *Для отмены нажмите кнопку ниже*"
    )
    
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=cancel_keyboard)

def expense_amount(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    try:
        amount = float(text.replace(' ', '').replace(',', '.'))
        user_data[chat_id]['amount'] = amount
        user_data[chat_id]['state'] = EXPENSE_STATES['DESCRIPTION']
        
        formatted_amount = f"{amount:,.0f} ₽".replace(',', ' ')
        if amount != int(amount):
            formatted_amount = f"{amount:,.2f} ₽".replace(',', ' ')
        
        text = (
            f"✅ *Сумма:* {formatted_amount}\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 2 из 3*\n\n"
            f"✏️ *Введите описание расхода:*\n\n"
            f"💡 *Примеры:*\n"
            f"• Закупка Creed Aventus\n"
            f"• Аренда за февраль\n"
            f"• Реклама в Instagram\n"
            f"• Упаковка (коробки, пакеты)\n\n"
            f"🔹 *Для отмены нажмите кнопку ниже*"
        )
        
        update.message.reply_text(text, parse_mode='Markdown', reply_markup=cancel_keyboard)
    except ValueError:
        update.message.reply_text(
            "❌ *Ошибка!*\n"
            "Введите корректную сумму\n\n"
            "🔹 *Для отмены нажмите кнопку ниже*",
            parse_mode='Markdown',
            reply_markup=cancel_keyboard
        )

def expense_description(update, context):
    chat_id = update.effective_chat.id
    description = update.message.text
    
    if description == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    user_data[chat_id]['description'] = description
    user_data[chat_id]['state'] = EXPENSE_STATES['EMPLOYEE']
    
    text = (
        f"✅ *Описание:* {description}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 *Шаг 3 из 3*\n\n"
        f"👤 *Выберите сотрудника:*\n\n"
        f"💡 *Нажмите на имя сотрудника:*"
    )
    
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=employee_keyboard)

def expense_employee(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    employee = text.replace('👤 ', '')
    
    if employee not in EMPLOYEES:
        update.message.reply_text(
            "❌ *Ошибка!*\n"
            "Пожалуйста, выберите сотрудника из кнопок:",
            parse_mode='Markdown',
            reply_markup=employee_keyboard
        )
        return
    
    data = user_data.pop(chat_id)
    
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
    
    add_operation(operation)
    
    formatted_amount = f"{data['amount']:,.0f} ₽".replace(',', ' ')
    if data['amount'] != int(data['amount']):
        formatted_amount = f"{data['amount']:,.2f} ₽".replace(',', ' ')
    
    report = (
        f"✅ *РАСХОД #{operation['id']} ЗАПИСАН!*\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"💰 *Сумма:* {formatted_amount}\n"
        f"📋 *Описание:* {data['description']}\n"
        f"👤 *Сотрудник:* {employee}\n"
        f"📝 *Запись добавил:* {data['added_by']}"
    )
    
    update.message.reply_text(report, parse_mode='Markdown', reply_markup=main_keyboard)

# ========== СТАТИСТИКА ==========
def show_all_statistics(update, context):
    if not check_access(update):
        return
    
    operations = get_all_operations()
    
    if not operations:
        update.message.reply_text("📭 Нет данных", reply_markup=main_keyboard)
        return
    
    # Общая статистика
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
    
    ml6_formatted = f"{ml6_total:,.0f} ₽".replace(',', ' ')
    ml10_formatted = f"{ml10_total:,.0f} ₽".replace(',', ' ')
    
    # Топ парфюмы
    parfums = {}
    for op in operations:
        if op['type'] == 'income':
            key = op['parfum_name']
            if key not in parfums:
                parfums[key] = {
                    'amount': 0,
                    'quantity': 0,
                    'volume': {}
                }
            parfums[key]['amount'] += op['amount']
            parfums[key]['quantity'] += op['quantity']
            
            vol = op.get('volume', 'unknown')
            if vol not in parfums[key]['volume']:
                parfums[key]['volume'][vol] = 0
            parfums[key]['volume'][vol] += op['quantity']
    
    report = (
        f"📊 *ОБЩАЯ СТАТИСТИКА*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📈 *ДОХОДЫ:*\n"
        f"   • Всего: `{income_formatted}`\n"
        f"   • Продаж: {income_count}\n\n"
        f"📉 *РАСХОДЫ:*\n"
        f"   • Всего: `{expense_formatted}`\n"
        f"   • Операций: {expense_count}\n\n"
        f"💎 *ИТОГ:* `{profit_formatted}`\n\n"
        f"📦 *ПО ОБЪЕМУ:*\n"
        f"   • 6ml: `{ml6_formatted}`\n"
        f"   • 10ml: `{ml10_formatted}`\n"
    )
    
    if parfums:
        report += f"\n🏆 *ТОП ПАРФЮМОВ:*\n"
        top_parfums = sorted(parfums.items(), key=lambda x: x[1]['amount'], reverse=True)[:5]
        for parfum, data in top_parfums:
            pamount = f"{data['amount']:,.0f} ₽".replace(',', ' ')
            
            # Детали по объемам
            vol_details = []
            for vol, qty in data['volume'].items():
                vol_details.append(f"{vol}: {qty} шт")
            vol_str = ", ".join(vol_details)
            
            report += f"   • *{parfum}*: {data['quantity']} шт ({pamount})\n"
            report += f"     └─ {vol_str}\n"
    
    update.message.reply_text(report, parse_mode='Markdown', reply_markup=main_keyboard)

def show_parfum_table(update, context):
    if not check_access(update):
        return
    
    operations = get_all_operations()
    
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
                    'sales': [],
                    'employees': {}
                }
            parfums[key]['total_quantity'] += op['quantity']
            parfums[key]['total_amount'] += op['amount']
            parfums[key]['sales'].append(op)
            
            emp = op['employee']
            if emp not in parfums[key]['employees']:
                parfums[key]['employees'][emp] = 0
            parfums[key]['employees'][emp] += op['quantity']
    
    if not parfums:
        update.message.reply_text("📭 Нет данных о парфюмах", reply_markup=main_keyboard)
        return
    
    sorted_parfums = sorted(parfums.items(), key=lambda x: x[1]['total_amount'], reverse=True)
    
    report = "📋 *ТАБЛИЦА ПАРФЮМОВ*\n"
    report += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for idx, (key, data) in enumerate(sorted_parfums, 1):
        formatted_amount = f"{data['total_amount']:,.0f} ₽".replace(',', ' ')
        
        report += f"{idx}. *{data['name']}*\n"
        report += f"   ├─ Объем: {data['volume']}\n"
        report += f"   ├─ Продано: {data['total_quantity']} шт\n"
        report += f"   ├─ На сумму: `{formatted_amount}`\n"
        report += f"   ├─ Продаж: {len(data['sales'])}\n"
        
        # Кто продавал
        if data['employees']:
            emp_list = []
            for emp, qty in data['employees'].items():
                emp_list.append(f"{emp}: {qty} шт")
            report += f"   └─ Продавцы: {', '.join(emp_list)}\n"
        report += "\n"
    
    # Статистика по объемам
    ml6_total = sum(data['total_amount'] for key, data in parfums.items() if '6ml' in key)
    ml10_total = sum(data['total_amount'] for key, data in parfums.items() if '10ml' in key)
    
    ml6_formatted = f"{ml6_total:,.0f} ₽".replace(',', ' ')
    ml10_formatted = f"{ml10_total:,.0f} ₽".replace(',', ' ')
    
    report += "━━━━━━━━━━━━━━━━━━━━\n"
    report += f"📊 *6ml:* {ml6_formatted}\n"
    report += f"📊 *10ml:* {ml10_formatted}\n"
    
    update.message.reply_text(report, parse_mode='Markdown', reply_markup=main_keyboard)

def show_employee_stats(update, context):
    if not check_access(update):
        return
    
    operations = get_all_operations()
    
    if not operations:
        update.message.reply_text("📭 Нет данных", reply_markup=main_keyboard)
        return
    
    stats = {}
    for employee in EMPLOYEES:
        stats[employee] = {
            'income': 0,
            'income_count': 0,
            'expense': 0,
            'expense_count': 0,
            'parfums': {},
            'volume': {'6ml': 0, '10ml': 0}
        }
    
    for op in operations:
        employee = op.get('employee')
        if employee and employee in stats:
            if op['type'] == 'income':
                stats[employee]['income'] += op['amount']
                stats[employee]['income_count'] += 1
                
                # Парфюмы
                key = f"{op['parfum_name']} {op['volume']}"
                if key not in stats[employee]['parfums']:
                    stats[employee]['parfums'][key] = {
                        'quantity': 0,
                        'amount': 0
                    }
                stats[employee]['parfums'][key]['quantity'] += op['quantity']
                stats[employee]['parfums'][key]['amount'] += op['amount']
                
                # Объемы
                vol = op.get('volume')
                if vol in stats[employee]['volume']:
                    stats[employee]['volume'][vol] += op['quantity']
                
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
        report += f"   📈 Доходы: `{income_formatted}` ({data['income_count']} продаж)\n"
        report += f"   📉 Расходы: `{expense_formatted}` ({data['expense_count']} операций)\n"
        report += f"   💎 Итог: `{profit_formatted}`\n"
        
        # Статистика по объемам
        if data['volume']['6ml'] > 0 or data['volume']['10ml'] > 0:
            report += f"   📦 Продажи по объемам:\n"
            if data['volume']['6ml'] > 0:
                report += f"      • 6ml: {data['volume']['6ml']} шт\n"
            if data['volume']['10ml'] > 0:
                report += f"      • 10ml: {data['volume']['10ml']} шт\n"
        
        # Топ парфюмов сотрудника
        if data['parfums']:
            report += f"   🏆 Топ продаж:\n"
            top_parfums = sorted(data['parfums'].items(), key=lambda x: x[1]['amount'], reverse=True)[:3]
            for parfum, pdata in top_parfums:
                pamount = f"{pdata['amount']:,.0f} ₽".replace(',', ' ')
                report += f"      • {parfum}: {pdata['quantity']} шт ({pamount})\n"
        report += "\n"
    
    update.message.reply_text(report, parse_mode='Markdown', reply_markup=main_keyboard)

# ========== РЕДАКТИРОВАНИЕ ==========
def show_operations_for_edit(update, context):
    if not check_access(update):
        return
    
    if update.message.text == '🔙 Отмена':
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    operations = get_all_operations()
    
    if not operations:
        update.message.reply_text("📭 Нет операций", reply_markup=main_keyboard)
        return
    
    # Сортируем по убыванию ID (новые сверху)
    operations.sort(key=lambda x: x['id'], reverse=True)
    operations = operations[:15]  # Последние 15
    
    keyboard = []
    for op in operations:
        amount = op['amount']
        formatted_amount = f"{amount:,.0f} ₽".replace(',', ' ')
        if amount != int(amount):
            formatted_amount = f"{amount:,.2f} ₽".replace(',', ' ')
        
        if op['type'] == 'income':
            desc = f"{op['parfum_name']} {op['volume']} x{op['quantity']} - {op['employee']}"
        else:
            desc = op['description']
            if len(desc) > 25:
                desc = desc[:22] + "..."
        
        button_text = f"#{op['id']} {op['type_display']} {formatted_amount} - {desc}"
        # Обрезаем если слишком длинное
        if len(button_text) > 50:
            button_text = button_text[:47] + "..."
        
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"edit_op_{op['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Отмена", callback_data="edit_cancel")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "✏️ *ВЫБЕРИТЕ ОПЕРАЦИЮ ДЛЯ РЕДАКТИРОВАНИЯ:*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔹 *Последние 15 операций:*\n"
        "(нажмите на нужную)",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

def edit_callback(update, context):
    query = update.callback_query
    query.answer()
    
    if not check_access(update):
        query.edit_message_text("❌ Нет доступа")
        return
    
    data = query.data
    
    if data == "edit_cancel":
        query.edit_message_text("🔙 Отменено")
        query.message.reply_text("Главное меню:", reply_markup=main_keyboard)
        return
    
    if data.startswith("edit_op_"):
        op_id = int(data.split('_')[2])
        
        operations = get_all_operations()
        op = next((o for o in operations if o['id'] == op_id), None)
        
        if not op:
            query.edit_message_text("❌ Операция не найдена")
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
            [InlineKeyboardButton("❌ Удалить операцию", callback_data=f"edit_del_{op_id}")]
        ]
        
        if op['type'] == 'income':
            keyboard.insert(1, [InlineKeyboardButton("👤 Изменить сотрудника", callback_data=f"edit_employee_{op_id}")])
        
        keyboard.append([InlineKeyboardButton("🔙 Назад к списку", callback_data="edit_back")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(op_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    elif data.startswith("edit_sum_"):
        op_id = int(data.split('_')[2])
        context.user_data['edit_op_id'] = op_id
        context.user_data['edit_action'] = 'sum'
        query.edit_message_text(
            f"✏️ *Введите новую сумму для операции #{op_id}:*\n\n"
            f"📝 *Форматы:*\n"
            f"• 15000\n"
            f"• 15 000\n"
            f"• 15000.50\n\n"
            f"🔹 *Для отмены отправьте /cancel*"
        )
    
    elif data.startswith("edit_employee_"):
        op_id = int(data.split('_')[2])
        
        keyboard = []
        for emp in EMPLOYEES:
            keyboard.append([InlineKeyboardButton(f"👤 {emp}", callback_data=f"edit_set_employee_{op_id}_{emp}")])
        keyboard.append([InlineKeyboardButton("🔙 Отмена", callback_data=f"edit_op_{op_id}")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            f"✏️ *Выберите нового сотрудника для операции #{op_id}:*",
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
        
        query.edit_message_text(f"✅ Сотрудник операции #{op_id} изменен на {new_employee}")
        
        # Уведомление
        notification = f"✏️ *Операция #{op_id} изменена*\n👤 {update.effective_user.first_name}\n👤 Новый сотрудник: {new_employee}"
        for admin_id in ALLOWED_IDS:
            try:
                context.bot.send_message(chat_id=admin_id, text=notification, parse_mode='Markdown')
            except:
                pass
        
        query.message.reply_text("Главное меню:", reply_markup=main_keyboard)
    
    elif data.startswith("edit_del_"):
        op_id = int(data.split('_')[2])
        
        keyboard = [
            [InlineKeyboardButton("✅ Да, удалить", callback_data=f"edit_confirm_del_{op_id}")],
            [InlineKeyboardButton("❌ Нет, отмена", callback_data=f"edit_op_{op_id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(
            f"⚠️ *ВЫ УВЕРЕНЫ?*\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"Операция #{op_id} будет удалена безвозвратно!",
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    elif data.startswith("edit_confirm_del_"):
        op_id = int(data.split('_')[3])
        
        delete_operation(op_id)
        
        query.edit_message_text(f"✅ Операция #{op_id} удалена")
        
        # Уведомление
        notification = f"🗑 *Операция #{op_id} удалена*\n👤 {update.effective_user.first_name}"
        for admin_id in ALLOWED_IDS:
            try:
                context.bot.send_message(chat_id=admin_id, text=notification, parse_mode='Markdown')
            except:
                pass
        
        query.message.reply_text("Главное меню:", reply_markup=main_keyboard)
    
    elif data == "edit_back":
        show_operations_for_edit(update, context)

def handle_edit_input(update, context):
    if 'edit_op_id' not in context.user_data:
        return
    
    if update.message.text == '/cancel':
        del context.user_data['edit_op_id']
        del context.user_data['edit_action']
        update.message.reply_text("🔙 Редактирование отменено", reply_markup=main_keyboard)
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
            
            update.message.reply_text(f"✅ Сумма операции #{op_id} изменена на {formatted_sum}", reply_markup=main_keyboard)
            
            # Уведомление
            notification = f"✏️ *Операция #{op_id} изменена*\n👤 {update.effective_user.first_name}\n💰 Новая сумма: {formatted_sum}"
            for admin_id in ALLOWED_IDS:
                try:
                    context.bot.send_message(chat_id=admin_id, text=notification, parse_mode='Markdown')
                except:
                    pass
            
        except ValueError:
            update.message.reply_text(
                "❌ Введите корректную сумму\n\n"
                "🔹 *Для отмены отправьте /cancel*",
                parse_mode='Markdown'
            )
            return
    
    del context.user_data['edit_op_id']
    del context.user_data['edit_action']

# ========== ГЛАВНЫЙ ОБРАБОТЧИК ==========
def handle_message(update, context):
    if not check_access(update):
        update.message.reply_text("❌ Нет доступа")
        return
    
    chat_id = update.effective_chat.id
    text = update.message.text
    
    # Отмена
    if text == '🔙 Отмена':
        if chat_id in user_data:
            del user_data[chat_id]
        context.user_data.clear()
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    # Редактирование
    if 'edit_op_id' in context.user_data:
        handle_edit_input(update, context)
        return
    
    # Состояния
    if chat_id in user_data:
        state_data = user_data[chat_id]
        
        if state_data.get('type') == 'income':
            state = state_data.get('state')
            
            if state == INCOME_STATES['NAME']:
                income_name(update, context)
            elif state == INCOME_STATES['VOLUME']:
                income_volume(update, context)
            elif state == INCOME_STATES['QUANTITY']:
                income_quantity(update, context)
            elif state == INCOME_STATES['EMPLOYEE']:
                income_employee(update, context)
            elif state == INCOME_STATES['PAYMENT']:
                income_payment(update, context)
            elif state == INCOME_STATES['BANK']:
                income_bank(update, context)
            elif state == INCOME_STATES['AMOUNT']:
                income_amount(update, context)
            else:
                del user_data[chat_id]
                update.message.reply_text("⚠️ Что-то пошло не так. Начните заново.", reply_markup=main_keyboard)
        
        elif state_data.get('type') == 'expense':
            state = state_data.get('state')
            
            if state == EXPENSE_STATES['AMOUNT']:
                expense_amount(update, context)
            elif state == EXPENSE_STATES['DESCRIPTION']:
                expense_description(update, context)
            elif state == EXPENSE_STATES['EMPLOYEE']:
                expense_employee(update, context)
            else:
                del user_data[chat_id]
                update.message.reply_text("⚠️ Что-то пошло не так. Начните заново.", reply_markup=main_keyboard)
        
        return
    
    # Меню
    if text == '💰 Доход':
        income_start(update, context)
    elif text == '💸 Расход':
        expense_start(update, context)
    elif text == '📊 Статистика':
        show_all_statistics(update, context)
    elif text == '📋 Таблица парфюмов':
        show_parfum_table(update, context)
    elif text == '👥 Статистика коллег':
        show_employee_stats(update, context)
    elif text == '✏️ Редактировать/Удалить':
        show_operations_for_edit(update, context)
    else:
        # Игнорируем случайные сообщения
        pass

def cancel_command(update, context):
    chat_id = update.effective_chat.id
    
    if chat_id in user_data:
        del user_data[chat_id]
    context.user_data.clear()
    
    update.message.reply_text("🔙 Действие отменено", reply_markup=main_keyboard)

def main():
    print("🚀 Бот запускается...")
    print("✅ Данные сохраняются в gabbana_data.json")
    
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("cancel", cancel_command))
    dp.add_handler(CallbackQueryHandler(edit_callback, pattern="^(edit_|sum_|del_|yes_|back)"))
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    
    print("✅ Бот готов к работе!")
    print("📊 Статистика, таблицы и отчеты - всё на месте!")
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
