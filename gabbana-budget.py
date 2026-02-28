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

# ========== КРАСИВЫЕ КЛАВИАТУРЫ ==========
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
user_states = {}

# ========== РАБОТА С JSON ==========
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

def add_operation(op):
    data = load_data()
    data['operations'].append(op)
    save_data(data)

def get_all_operations():
    return load_data().get('operations', [])

def delete_operation(op_id):
    data = load_data()
    data['operations'] = [o for o in data['operations'] if o['id'] != op_id]
    save_data(data)

def update_operation(op_id, new_data):
    data = load_data()
    for i, o in enumerate(data['operations']):
        if o['id'] == op_id:
            data['operations'][i].update(new_data)
            break
    save_data(data)

# ========== ПРОВЕРКА ДОСТУПА ==========
def check_access(update):
    return update.effective_user.id in ALLOWED_IDS

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
        f"✅ *Основные функции:*\n\n"
        f"💰 *Доход* – продажа парфюма (6ml/10ml)\n"
        f"   • Подробный ввод: название → объем → количество\n"
        f"   • Выбор сотрудника и способ оплаты\n"
        f"   • Учет банков при переводе\n\n"
        f"💸 *Расход* – закупки, аренда, реклама\n"
        f"   • Сумма → описание → сотрудник\n\n"
        f"📊 *Статистика* – общие цифры по всем операциям\n"
        f"   • Доходы/расходы/итог\n"
        f"   • Разбивка по объемам (6ml/10ml)\n"
        f"   • Топ парфюмов\n\n"
        f"📋 *Таблица парфюмов* – детально по каждому\n"
        f"   • Количество продаж и сумма\n"
        f"   • Сортировка по популярности\n\n"
        f"👥 *Статистика коллег* – по сотрудникам\n"
        f"   • Доходы и расходы каждого\n"
        f"   • Личный результат\n\n"
        f"✏️ *Редактировать/Удалить* – изменить или удалить запись\n\n"
        f"✨ *Все данные сохраняются автоматически!*"
    )
    
    update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=main_keyboard)

# ========== ДОХОД ==========
def income_start(update, context):
    chat_id = update.effective_chat.id
    user_states[chat_id] = {'type': 'income', 'step': 'name', 'data': {}}
    
    text = (
        "💵 *ДОХОД (Продажа парфюма)*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 *Шаг 1 из 7*\n\n"
        "✏️ *Введите название парфюма:*\n\n"
        "💡 *Примеры:*\n"
        "• Creed Aventus\n"
        "• Baccarat Rouge 540\n"
        "• Tom Ford Tobacco Vanille\n"
        "• Maison Francis Kurkdjian\n"
        "• Xerjoff\n\n"
        "🔹 *Для отмены нажмите кнопку ниже*"
    )
    
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=cancel_keyboard)

def handle_income_step(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    state = user_states[chat_id]
    step = state['step']
    
    if text == '🔙 Отмена':
        del user_states[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    if step == 'name':
        state['data']['name'] = text
        state['step'] = 'volume'
        
        text = (
            f"✅ *Название:* {text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 2 из 7*\n\n"
            f"🔢 *Выберите объем:*\n\n"
            f"📦 *Доступные объемы:*\n"
            f"• 6ml – пробники, тестеры\n"
            f"• 10ml – миниатюры, дорогие ароматы\n\n"
            f"🔹 *Нажмите на кнопку с нужным объемом*"
        )
        
        update.message.reply_text(text, parse_mode='Markdown', reply_markup=volume_keyboard)
    
    elif step == 'volume':
        if text not in ['6ml', '10ml']:
            update.message.reply_text(
                "❌ *Ошибка!*\n"
                "Пожалуйста, выберите объем из кнопок ниже:",
                parse_mode='Markdown', reply_markup=volume_keyboard
            )
            return
        
        state['data']['volume'] = text
        state['step'] = 'quantity'
        
        text = (
            f"✅ *Объем:* {text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 3 из 7*\n\n"
            f"🔢 *Введите количество флаконов:*\n\n"
            f"💡 *Примеры:*\n"
            f"• 1 – один флакон\n"
            f"• 2 – два флакона\n"
            f"• 3 – три флакона\n"
            f"• 5 – пять флаконов\n\n"
            f"🔹 *Для отмены нажмите кнопку ниже*"
        )
        
        update.message.reply_text(text, parse_mode='Markdown', reply_markup=cancel_keyboard)
    
    elif step == 'quantity':
        try:
            qty = int(text)
            if qty <= 0:
                raise ValueError
            
            state['data']['quantity'] = qty
            state['step'] = 'employee'
            
            text = (
                f"✅ *Количество:* {qty} шт\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📝 *Шаг 4 из 7*\n\n"
                f"👤 *Выберите сотрудника, который продал:*\n\n"
                f"💡 *Нажмите на имя сотрудника:*\n"
                f"• Матвей\n"
                f"• Дима\n"
                f"• Никита"
            )
            
            update.message.reply_text(text, parse_mode='Markdown', reply_markup=employee_keyboard)
            
        except ValueError:
            update.message.reply_text(
                "❌ *Ошибка!*\n"
                "Введите целое число (1, 2, 3...)\n\n"
                "🔹 *Для отмены нажмите кнопку ниже*",
                parse_mode='Markdown', reply_markup=cancel_keyboard
            )
    
    elif step == 'employee':
        emp = text.replace('👤 ', '')
        if emp not in EMPLOYEES:
            update.message.reply_text(
                "❌ *Ошибка!*\n"
                "Пожалуйста, выберите сотрудника из кнопок:",
                parse_mode='Markdown', reply_markup=employee_keyboard
            )
            return
        
        state['data']['employee'] = emp
        state['step'] = 'payment'
        
        text = (
            f"✅ *Сотрудник:* {emp}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 5 из 7*\n\n"
            f"💳 *Выберите способ оплаты:*\n\n"
            f"• 💳 Перевод – безналичный расчет (Сбер, Тинькофф и т.д.)\n"
            f"• 💵 Наличка – оплата наличными"
        )
        
        update.message.reply_text(text, parse_mode='Markdown', reply_markup=payment_keyboard)
    
    elif step == 'payment':
        if 'Перевод' in text:
            state['data']['payment'] = 'Перевод'
            state['step'] = 'bank'
            
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
                f"• Другой (впишите название)"
            )
            
            update.message.reply_text(text, parse_mode='Markdown', reply_markup=bank_keyboard)
            
        elif 'Наличка' in text:
            state['data']['payment'] = 'Наличка'
            state['data']['bank'] = '-'
            state['step'] = 'amount'
            
            text = (
                f"✅ *Способ оплаты:* {text}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📝 *Шаг 7 из 7*\n\n"
                f"💰 *Введите сумму дохода:*\n\n"
                f"📝 *Форматы ввода:*\n"
                f"• `1300` → 1 300 ₽\n"
                f"• `2 500` → 2 500 ₽\n"
                f"• `3 000.50` → 3 000.50 ₽\n\n"
                f"💡 *Примеры:*\n"
                f"• 1500 – полторы тысячи\n"
                f"• 15 000 – пятнадцать тысяч\n"
                f"• 12500.50 – двенадцать тысяч пятьсот рублей 50 копеек\n\n"
                f"🔹 *Для отмены нажмите кнопку ниже*"
            )
            
            update.message.reply_text(text, parse_mode='Markdown', reply_markup=cancel_keyboard)
        else:
            update.message.reply_text(
                "❌ *Ошибка!*\n"
                "Пожалуйста, выберите способ оплаты из кнопок:",
                parse_mode='Markdown', reply_markup=payment_keyboard
            )
    
    elif step == 'bank':
        bank = text.replace('🏦 ', '') if '🏦' in text else text
        state['data']['bank'] = bank
        state['step'] = 'amount'
        
        text = (
            f"✅ *Банк:* {bank}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 7 из 7*\n\n"
            f"💰 *Введите сумму дохода:*\n\n"
            f"📝 *Форматы ввода:*\n"
            f"• `1300` → 1 300 ₽\n"
            f"• `2 500` → 2 500 ₽\n"
            f"• `3 000.50` → 3 000.50 ₽\n\n"
            f"💡 *Примеры:*\n"
            f"• 1500 – полторы тысячи\n"
            f"• 15 000 – пятнадцать тысяч\n"
            f"• 12500.50 – двенадцать тысяч пятьсот рублей 50 копеек\n\n"
            f"🔹 *Для отмены нажмите кнопку ниже*"
        )
        
        update.message.reply_text(text, parse_mode='Markdown', reply_markup=cancel_keyboard)
    
    elif step == 'amount':
        try:
            amount = float(text.replace(' ', '').replace(',', '.'))
            data = state['data']
            
            op = {
                'id': get_next_id(),
                'date': datetime.now().strftime('%d.%m.%Y %H:%M'),
                'type': 'income',
                'type_display': '💰 Доход',
                'name': data['name'],
                'volume': data['volume'],
                'quantity': data['quantity'],
                'employee': data['employee'],
                'payment': data['payment'],
                'bank': data.get('bank', '-'),
                'amount': amount,
                'added_by': update.effective_user.first_name
            }
            add_operation(op)
            
            del user_states[chat_id]
            
            formatted = f"{amount:,.0f} ₽".replace(',', ' ')
            if amount != int(amount):
                formatted = f"{amount:,.2f} ₽".replace(',', ' ')
            
            result_text = (
                f"✅ *ПРОДАЖА #{op['id']} ЗАПИСАНА!*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📌 *Парфюм:* {data['name']}\n"
                f"📌 *Объем:* {data['volume']}\n"
                f"📌 *Количество:* {data['quantity']} шт\n"
                f"👤 *Сотрудник:* {data['employee']}\n"
                f"💳 *Оплата:* {data['payment']}\n"
            )
            
            if data['payment'] == 'Перевод':
                result_text += f"🏦 *Банк:* {data.get('bank', '-')}\n"
            
            result_text += f"💰 *Сумма:* {formatted}\n"
            result_text += f"📝 *Запись добавил:* {update.effective_user.first_name}\n\n"
            result_text += f"✨ *Спасибо за продажу!*"
            
            update.message.reply_text(result_text, parse_mode='Markdown', reply_markup=main_keyboard)
            
        except ValueError:
            update.message.reply_text(
                "❌ *Ошибка!*\n"
                "Введите корректную сумму (например: 1500, 2 500, 3000.50)\n\n"
                "🔹 *Для отмены нажмите кнопку ниже*",
                parse_mode='Markdown', reply_markup=cancel_keyboard
            )

# ========== РАСХОД ==========
def expense_start(update, context):
    chat_id = update.effective_chat.id
    user_states[chat_id] = {'type': 'expense', 'step': 'amount', 'data': {}}
    
    text = (
        "💳 *РАСХОД*\n"
        "━━━━━━━━━━━━━━\n\n"
        "📝 *Шаг 1 из 3*\n\n"
        "💰 *Введите сумму расхода:*\n\n"
        "📝 *Форматы ввода:*\n"
        "• `1300` → 1 300 ₽\n"
        "• `2 500` → 2 500 ₽\n"
        "• `3 000.50` → 3 000.50 ₽\n\n"
        "💡 *Примеры расходов:*\n"
        "• Закупка парфюма\n"
        "• Аренда помещения\n"
        "• Реклама\n"
        "• Упаковка\n"
        "• Транспорт\n\n"
        "🔹 *Для отмены нажмите кнопку ниже*"
    )
    
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=cancel_keyboard)

def handle_expense_step(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    state = user_states[chat_id]
    step = state['step']
    
    if text == '🔙 Отмена':
        del user_states[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    if step == 'amount':
        try:
            amount = float(text.replace(' ', '').replace(',', '.'))
            state['data']['amount'] = amount
            state['step'] = 'description'
            
            formatted = f"{amount:,.0f} ₽".replace(',', ' ')
            if amount != int(amount):
                formatted = f"{amount:,.2f} ₽".replace(',', ' ')
            
            text = (
                f"✅ *Сумма:* {formatted}\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📝 *Шаг 2 из 3*\n\n"
                f"✏️ *Введите описание расхода:*\n\n"
                f"💡 *Примеры:*\n"
                f"• Закупка Creed Aventus (3 флакона)\n"
                f"• Аренда за февраль 2024\n"
                f"• Реклама в Instagram\n"
                f"• Упаковка (коробки, пакеты)\n"
                f"• Доставка\n\n"
                f"🔹 *Для отмены нажмите кнопку ниже*"
            )
            
            update.message.reply_text(text, parse_mode='Markdown', reply_markup=cancel_keyboard)
            
        except ValueError:
            update.message.reply_text(
                "❌ *Ошибка!*\n"
                "Введите корректную сумму\n\n"
                "🔹 *Для отмены нажмите кнопку ниже*",
                parse_mode='Markdown', reply_markup=cancel_keyboard
            )
    
    elif step == 'description':
        state['data']['description'] = text
        state['step'] = 'employee'
        
        text = (
            f"✅ *Описание:* {text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 3 из 3*\n\n"
            f"👤 *Выберите сотрудника:*\n\n"
            f"💡 *Нажмите на имя сотрудника:*\n"
            f"• Матвей\n"
            f"• Дима\n"
            f"• Никита"
        )
        
        update.message.reply_text(text, parse_mode='Markdown', reply_markup=employee_keyboard)
    
    elif step == 'employee':
        emp = text.replace('👤 ', '')
        if emp not in EMPLOYEES:
            update.message.reply_text(
                "❌ *Ошибка!*\n"
                "Пожалуйста, выберите сотрудника из кнопок:",
                parse_mode='Markdown', reply_markup=employee_keyboard
            )
            return
        
        data = state['data']
        op = {
            'id': get_next_id(),
            'date': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'type': 'expense',
            'type_display': '💸 Расход',
            'amount': data['amount'],
            'description': data['description'],
            'employee': emp,
            'added_by': update.effective_user.first_name
        }
        add_operation(op)
        
        del user_states[chat_id]
        
        formatted = f"{data['amount']:,.0f} ₽".replace(',', ' ')
        if data['amount'] != int(data['amount']):
            formatted = f"{data['amount']:,.2f} ₽".replace(',', ' ')
        
        result_text = (
            f"✅ *РАСХОД #{op['id']} ЗАПИСАН!*\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"💰 *Сумма:* {formatted}\n"
            f"📋 *Описание:* {data['description']}\n"
            f"👤 *Сотрудник:* {emp}\n"
            f"📝 *Запись добавил:* {update.effective_user.first_name}"
        )
        
        update.message.reply_text(result_text, parse_mode='Markdown', reply_markup=main_keyboard)

# ========== СТАТИСТИКА ==========
def show_stats(update, context):
    ops = get_all_operations()
    
    if not ops:
        update.message.reply_text("📭 *Нет данных*\n\nДобавьте первую операцию через меню Доход или Расход", parse_mode='Markdown', reply_markup=main_keyboard)
        return
    
    income = sum(o['amount'] for o in ops if o['type'] == 'income')
    expense = sum(o['amount'] for o in ops if o['type'] == 'expense')
    inc_count = len([o for o in ops if o['type'] == 'income'])
    exp_count = len([o for o in ops if o['type'] == 'expense'])
    
    ml6 = sum(o['amount'] for o in ops if o['type'] == 'income' and o.get('volume') == '6ml')
    ml10 = sum(o['amount'] for o in ops if o['type'] == 'income' and o.get('volume') == '10ml')
    
    # Топ парфюмов
    parfums = {}
    for o in ops:
        if o['type'] == 'income':
            name = o['name']
            if name not in parfums:
                parfums[name] = {'qty': 0, 'sum': 0}
            parfums[name]['qty'] += o['quantity']
            parfums[name]['sum'] += o['amount']
    
    text = (
        f"📊 *ОБЩАЯ СТАТИСТИКА*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📈 *ДОХОДЫ:*\n"
        f"   • Всего: `{income:,.0f} ₽`\n"
        f"   • Продаж: {inc_count}\n\n"
        f"📉 *РАСХОДЫ:*\n"
        f"   • Всего: `{expense:,.0f} ₽`\n"
        f"   • Операций: {exp_count}\n\n"
        f"💎 *ИТОГ:* `{income - expense:,.0f} ₽`\n\n"
        f"📦 *ПО ОБЪЕМУ:*\n"
        f"   • 6ml: `{ml6:,.0f} ₽`\n"
        f"   • 10ml: `{ml10:,.0f} ₽`\n"
    ).replace(',', ' ')
    
    if parfums:
        text += f"\n🏆 *ТОП ПАРФЮМОВ:*\n"
        sorted_parfums = sorted(parfums.items(), key=lambda x: -x[1]['sum'])[:5]
        for name, data in sorted_parfums:
            text += f"   • *{name}*: {data['qty']} шт – {data['sum']:,.0f} ₽\n".replace(',', ' ')
    
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=main_keyboard)

def show_parfums(update, context):
    ops = get_all_operations()
    
    parfums = {}
    for o in ops:
        if o['type'] == 'income':
            key = f"{o['name']} ({o['volume']})"
            if key not in parfums:
                parfums[key] = {
                    'name': o['name'],
                    'volume': o['volume'],
                    'qty': 0,
                    'sum': 0,
                    'count': 0
                }
            parfums[key]['qty'] += o['quantity']
            parfums[key]['sum'] += o['amount']
            parfums[key]['count'] += 1
    
    if not parfums:
        update.message.reply_text("📭 *Нет данных о парфюмах*\n\nДобавьте продажи через меню Доход", parse_mode='Markdown', reply_markup=main_keyboard)
        return
    
    text = "📋 *ТАБЛИЦА ПАРФЮМОВ*\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    sorted_parfums = sorted(parfums.items(), key=lambda x: -x[1]['sum'])
    for idx, (key, data) in enumerate(sorted_parfums, 1):
        text += f"{idx}. *{data['name']}* ({data['volume']})\n"
        text += f"   ├─ Продано: {data['qty']} шт\n"
        text += f"   ├─ Сумма: {data['sum']:,.0f} ₽\n"
        text += f"   └─ Продаж: {data['count']}\n\n".replace(',', ' ')
    
    ml6 = sum(d['sum'] for k, d in parfums.items() if '6ml' in k)
    ml10 = sum(d['sum'] for k, d in parfums.items() if '10ml' in k)
    
    text += "━━━━━━━━━━━━━━━━━━━━\n"
    text += f"📊 *6ml:* {ml6:,.0f} ₽\n".replace(',', ' ')
    text += f"📊 *10ml:* {ml10:,.0f} ₽".replace(',', ' ')
    
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=main_keyboard)

def show_employees(update, context):
    ops = get_all_operations()
    
    stats = {}
    for emp in EMPLOYEES:
        stats[emp] = {
            'inc': 0, 'exp': 0,
            'inc_count': 0, 'exp_count': 0,
            'parfums': {}
        }
    
    for o in ops:
        emp = o.get('employee')
        if emp and emp in stats:
            if o['type'] == 'income':
                stats[emp]['inc'] += o['amount']
                stats[emp]['inc_count'] += 1
                
                key = f"{o['name']} {o['volume']}"
                if key not in stats[emp]['parfums']:
                    stats[emp]['parfums'][key] = 0
                stats[emp]['parfums'][key] += o['quantity']
            else:
                stats[emp]['exp'] += o['amount']
                stats[emp]['exp_count'] += 1
    
    text = "👥 *СТАТИСТИКА ПО СОТРУДНИКАМ*\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for emp in EMPLOYEES:
        d = stats[emp]
        profit = d['inc'] - d['exp']
        
        text += f"👤 *{emp}*\n"
        text += f"   📈 Доходы: `{d['inc']:,.0f} ₽` ({d['inc_count']} продаж)\n"
        text += f"   📉 Расходы: `{d['exp']:,.0f} ₽` ({d['exp_count']} операций)\n"
        text += f"   💎 Итог: `{profit:,.0f} ₽`\n".replace(',', ' ')
        
        if d['parfums']:
            text += f"   📦 Продажи:\n"
            sorted_parfums = sorted(d['parfums'].items(), key=lambda x: -x[1])[:3]
            for p, q in sorted_parfums:
                text += f"      • {p}: {q} шт\n"
        text += "\n"
    
    if all(d['inc'] == 0 and d['exp'] == 0 for d in stats.values()):
        text += "📭 *Пока нет операций*\nДобавьте доходы или расходы"
    
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=main_keyboard)

# ========== РЕДАКТИРОВАНИЕ ==========
def edit_start(update, context):
    ops = get_all_operations()
    
    if not ops:
        update.message.reply_text("📭 *Нет операций для редактирования*", parse_mode='Markdown', reply_markup=main_keyboard)
        return
    
    ops.sort(key=lambda x: x['id'], reverse=True)
    kb = []
    
    for o in ops[:10]:
        amount = f"{o['amount']:,.0f} ₽".replace(',', ' ')
        if o['type'] == 'income':
            desc = f"{o['name']} {o['volume']} x{o['quantity']}"
        else:
            desc = o['description'][:25]
        
        btn = f"#{o['id']} {o['type_display']} {amount}"
        kb.append([InlineKeyboardButton(btn, callback_data=f"edit_{o['id']}")])
    
    kb.append([InlineKeyboardButton("🔙 Отмена", callback_data="cancel")])
    
    text = (
        "✏️ *РЕДАКТИРОВАНИЕ ОПЕРАЦИЙ*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔹 *Последние 10 операций:*\n"
        "(нажмите на нужную)"
    )
    
    update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

def edit_callback(update, context):
    query = update.callback_query
    query.answer()
    data = query.data
    
    if data == "cancel":
        query.edit_message_text("🔙 *Отменено*", parse_mode='Markdown')
        query.message.reply_text("Главное меню:", reply_markup=main_keyboard)
        return
    
    if data.startswith("edit_"):
        op_id = int(data.split('_')[1])
        ops = get_all_operations()
        op = next((o for o in ops if o['id'] == op_id), None)
        
        if not op:
            query.edit_message_text("❌ *Операция не найдена*", parse_mode='Markdown')
            return
        
        amount = f"{op['amount']:,.0f} ₽".replace(',', ' ')
        
        if op['type'] == 'income':
            text = (
                f"📌 *ПРОДАЖА #{op_id}*\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📅 *Дата:* {op['date']}\n"
                f"📦 *Парфюм:* {op['name']}\n"
                f"🔢 *Объем:* {op['volume']}\n"
                f"📊 *Количество:* {op['quantity']} шт\n"
                f"👤 *Сотрудник:* {op['employee']}\n"
                f"💳 *Оплата:* {op['payment']}\n"
                f"🏦 *Банк:* {op.get('bank', '-')}\n"
                f"💰 *Сумма:* {amount}\n"
                f"📝 *Добавил:* {op['added_by']}"
            )
        else:
            text = (
                f"📌 *РАСХОД #{op_id}*\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📅 *Дата:* {op['date']}\n"
                f"💰 *Сумма:* {amount}\n"
                f"📋 *Описание:* {op['description']}\n"
                f"👤 *Сотрудник:* {op['employee']}\n"
                f"📝 *Добавил:* {op['added_by']}"
            )
        
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Изменить сумму", callback_data=f"sum_{op_id}")],
            [InlineKeyboardButton("❌ Удалить операцию", callback_data=f"del_{op_id}")],
            [InlineKeyboardButton("🔙 Назад к списку", callback_data="back")]
        ])
        
        query.edit_message_text(text, parse_mode='Markdown', reply_markup=kb)
    
    elif data.startswith("sum_"):
        op_id = int(data.split('_')[1])
        context.user_data['edit_id'] = op_id
        query.edit_message_text(
            f"✏️ *Введите новую сумму для операции #{op_id}:*\n\n"
            f"📝 *Форматы:*\n"
            f"• 1500\n"
            f"• 2 500\n"
            f"• 3000.50\n\n"
            f"🔹 *Для отмены отправьте /cancel*",
            parse_mode='Markdown'
        )
    
    elif data.startswith("del_"):
        op_id = int(data.split('_')[1])
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Да, удалить", callback_data=f"yes_{op_id}")],
            [InlineKeyboardButton("❌ Нет, отмена", callback_data="back")]
        ])
        query.edit_message_text(
            f"⚠️ *ВЫ УВЕРЕНЫ?*\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"Операция #{op_id} будет удалена безвозвратно!",
            parse_mode='Markdown', reply_markup=kb
        )
    
    elif data.startswith("yes_"):
        op_id = int(data.split('_')[1])
        delete_operation(op_id)
        query.edit_message_text(f"✅ *Операция #{op_id} удалена*", parse_mode='Markdown')
        query.message.reply_text("Главное меню:", reply_markup=main_keyboard)
    
    elif data == "back":
        edit_start(update, context)

def handle_edit_input(update, context):
    if 'edit_id' not in context.user_data:
        return
    
    if update.message.text == '/cancel':
        del context.user_data['edit_id']
        update.message.reply_text("🔙 *Редактирование отменено*", parse_mode='Markdown', reply_markup=main_keyboard)
        return
    
    try:
        new_sum = float(update.message.text.replace(' ', '').replace(',', '.'))
        op_id = context.user_data['edit_id']
        update_operation(op_id, {'amount': new_sum})
        
        formatted = f"{new_sum:,.0f} ₽".replace(',', ' ')
        if new_sum != int(new_sum):
            formatted = f"{new_sum:,.2f} ₽".replace(',', ' ')
        
        update.message.reply_text(f"✅ *Сумма изменена на {formatted}*", parse_mode='Markdown', reply_markup=main_keyboard)
        
    except ValueError:
        update.message.reply_text(
            "❌ *Ошибка!*\nВведите корректную сумму\n\n🔹 *Для отмены отправьте /cancel*",
            parse_mode='Markdown'
        )
        return
    
    del context.user_data['edit_id']

# ========== ГЛАВНЫЙ ОБРАБОТЧИК ==========
def handle_message(update, context):
    if not check_access(update):
        update.message.reply_text("❌ У вас нет доступа к этому боту")
        return
    
    chat_id = update.effective_chat.id
    text = update.message.text
    
    # Отмена
    if text == '🔙 Отмена':
        if chat_id in user_states:
            del user_states[chat_id]
        context.user_data.clear()
        update.message.reply_text("🔙 *Возврат в главное меню*", parse_mode='Markdown', reply_markup=main_keyboard)
        return
    
    # Редактирование
    if 'edit_id' in context.user_data:
        handle_edit_input(update, context)
        return
    
    # Состояния
    if chat_id in user_states:
        if user_states[chat_id]['type'] == 'income':
            handle_income_step(update, context)
        else:
            handle_expense_step(update, context)
        return
    
    # Меню
    if text == '💰 Доход':
        income_start(update, context)
    elif text == '💸 Расход':
        expense_start(update, context)
    elif text == '📊 Статистика':
        show_stats(update, context)
    elif text == '📋 Таблица парфюмов':
        show_parfums(update, context)
    elif text == '👥 Статистика коллег':
        show_employees(update, context)
    elif text == '✏️ Редактировать/Удалить':
        edit_start(update, context)

def cancel_command(update, context):
    chat_id = update.effective_chat.id
    
    if chat_id in user_states:
        del user_states[chat_id]
    context.user_data.clear()
    
    update.message.reply_text("🔙 *Действие отменено*", parse_mode='Markdown', reply_markup=main_keyboard)

def main():
    print("🚀 Бот запускается...")
    print("✅ Данные сохраняются в gabbana_data.json")
    
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("cancel", cancel_command))
    dp.add_handler(CallbackQueryHandler(edit_callback))
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    
    print("✅ Бот готов к работе!")
    print("📊 Красивые отчеты и стабильная работа!")
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
