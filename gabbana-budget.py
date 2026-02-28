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
volume_keyboard = ReplyKeyboardMarkup([['6ml', '10ml'], ['🔙 Отмена']], resize_keyboard=True)
payment_keyboard = ReplyKeyboardMarkup([['💳 Перевод', '💵 Наличка'], ['🔙 Отмена']], resize_keyboard=True)
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
user_data = {}

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

# ========== ПРОВЕРКА ДОСТУПА ==========
def check_access(update):
    return update.effective_user.id in ALLOWED_IDS

# ========== СТАРТ ==========
def start(update, context):
    if not check_access(update):
        update.message.reply_text("❌ У вас нет доступа к этому боту")
        return
    
    text = (
        "✨ *Gabbana&Home BUDGET* ✨\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👋 *Добро пожаловать!*\n\n"
        "📊 *Парфюмерный учет*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ *Доступные функции:*\n\n"
        "💰 *Доход* – продажа парфюма (6ml/10ml)\n"
        "💸 *Расход* – закупки, аренда, реклама\n"
        "📊 *Статистика* – общие цифры\n"
        "📋 *Таблица парфюмов* – все продажи\n"
        "👥 *Статистика коллег* – по сотрудникам\n"
        "✏️ *Редактировать/Удалить* – изменить запись\n\n"
        "✨ *Все данные сохраняются автоматически!*"
    )
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=main_keyboard)

# ========== ДОХОД (ПРОДАЖА) ==========
def income_start(update, context):
    chat_id = update.effective_chat.id
    user_data[chat_id] = {'step': 'name'}
    update.message.reply_text(
        "💵 *ДОХОД (Продажа парфюма)*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📝 *Шаг 1 из 7*\n\n"
        "✏️ *Введите название парфюма:*\n\n"
        "💡 *Примеры:*\n"
        "• Creed Aventus\n"
        "• Baccarat Rouge 540\n"
        "• Tom Ford Tobacco Vanille",
        parse_mode='Markdown', reply_markup=cancel_keyboard
    )

def income_name(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    user_data[chat_id]['name'] = text
    user_data[chat_id]['step'] = 'volume'
    update.message.reply_text(
        f"✅ *Название:* {text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 *Шаг 2 из 7*\n\n"
        f"🔢 *Выберите объем:*",
        parse_mode='Markdown', reply_markup=volume_keyboard
    )

def income_volume(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    if text not in ['6ml', '10ml']:
        update.message.reply_text("❌ Выберите объем из кнопок:", reply_markup=volume_keyboard)
        return
    
    user_data[chat_id]['volume'] = text
    user_data[chat_id]['step'] = 'quantity'
    update.message.reply_text(
        f"✅ *Объем:* {text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 *Шаг 3 из 7*\n\n"
        f"🔢 *Введите количество флаконов:*\n\n"
        f"💡 *Пример:* 1, 2, 3",
        parse_mode='Markdown', reply_markup=cancel_keyboard
    )

def income_quantity(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    try:
        qty = int(text)
        if qty <= 0:
            raise ValueError
        
        user_data[chat_id]['quantity'] = qty
        user_data[chat_id]['step'] = 'employee'
        update.message.reply_text(
            f"✅ *Количество:* {qty} шт\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 4 из 7*\n\n"
            f"👤 *Выберите сотрудника:*",
            parse_mode='Markdown', reply_markup=employee_keyboard
        )
    except:
        update.message.reply_text("❌ Введите число (1, 2, 3...)", reply_markup=cancel_keyboard)

def income_employee(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    emp = text.replace('👤 ', '')
    if emp not in EMPLOYEES:
        update.message.reply_text("❌ Выберите из кнопок:", reply_markup=employee_keyboard)
        return
    
    user_data[chat_id]['employee'] = emp
    user_data[chat_id]['step'] = 'payment'
    update.message.reply_text(
        f"✅ *Сотрудник:* {emp}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 *Шаг 5 из 7*\n\n"
        f"💳 *Выберите способ оплаты:*",
        parse_mode='Markdown', reply_markup=payment_keyboard
    )

def income_payment(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    if 'Перевод' in text:
        user_data[chat_id]['payment'] = 'Перевод'
        user_data[chat_id]['step'] = 'bank'
        update.message.reply_text(
            f"✅ *Способ оплаты:* {text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 6 из 7*\n\n"
            f"🏦 *Выберите банк:*",
            parse_mode='Markdown', reply_markup=bank_keyboard
        )
    elif 'Наличка' in text:
        user_data[chat_id]['payment'] = 'Наличка'
        user_data[chat_id]['bank'] = '-'
        user_data[chat_id]['step'] = 'amount'
        update.message.reply_text(
            f"✅ *Способ оплаты:* {text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 7 из 7*\n\n"
            f"💰 *Введите сумму:*\n\n"
            f"📝 *Пример:* 1500, 2 500, 3000.50",
            parse_mode='Markdown', reply_markup=cancel_keyboard
        )
    else:
        update.message.reply_text("❌ Выберите из кнопок:", reply_markup=payment_keyboard)

def income_bank(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    bank = text.replace('🏦 ', '') if '🏦' in text else text
    user_data[chat_id]['bank'] = bank
    user_data[chat_id]['step'] = 'amount'
    update.message.reply_text(
        f"✅ *Банк:* {bank}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 *Шаг 7 из 7*\n\n"
        f"💰 *Введите сумму:*\n\n"
        f"📝 *Пример:* 1500, 2 500, 3000.50",
        parse_mode='Markdown', reply_markup=cancel_keyboard
    )

def income_amount(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    try:
        amount = float(text.replace(' ', '').replace(',', '.'))
        data = user_data.pop(chat_id)
        
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
        
        formatted = f"{amount:,.0f} ₽".replace(',', ' ')
        if amount != int(amount):
            formatted = f"{amount:,.2f} ₽".replace(',', ' ')
        
        update.message.reply_text(
            f"✅ *ПРОДАЖА #{op['id']} ЗАПИСАНА!*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"📌 *Парфюм:* {data['name']} {data['volume']} x{data['quantity']}\n"
            f"👤 *Сотрудник:* {data['employee']}\n"
            f"💳 *Оплата:* {data['payment']}\n"
            f"💰 *Сумма:* {formatted}",
            parse_mode='Markdown', reply_markup=main_keyboard
        )
    except:
        update.message.reply_text("❌ Введите сумму (например: 1500)", reply_markup=cancel_keyboard)

# ========== РАСХОД ==========
def expense_start(update, context):
    chat_id = update.effective_chat.id
    user_data[chat_id] = {'type': 'expense', 'step': 'amount'}
    update.message.reply_text(
        "💳 *РАСХОД*\n"
        "━━━━━━━━━━━━━━\n\n"
        "📝 *Шаг 1 из 3*\n\n"
        "💰 *Введите сумму:*\n\n"
        "📝 *Пример:* 1500, 2 500, 3000.50",
        parse_mode='Markdown', reply_markup=cancel_keyboard
    )

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
        user_data[chat_id]['step'] = 'description'
        
        formatted = f"{amount:,.0f} ₽".replace(',', ' ')
        if amount != int(amount):
            formatted = f"{amount:,.2f} ₽".replace(',', ' ')
        
        update.message.reply_text(
            f"✅ *Сумма:* {formatted}\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 2 из 3*\n\n"
            f"✏️ *Введите описание:*\n\n"
            f"💡 *Примеры:*\n"
            f"• Закупка Creed Aventus\n"
            f"• Аренда за февраль\n"
            f"• Реклама в Instagram",
            parse_mode='Markdown', reply_markup=cancel_keyboard
        )
    except:
        update.message.reply_text("❌ Введите сумму", reply_markup=cancel_keyboard)

def expense_description(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    user_data[chat_id]['description'] = text
    user_data[chat_id]['step'] = 'employee'
    update.message.reply_text(
        f"✅ *Описание:* {text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 *Шаг 3 из 3*\n\n"
        f"👤 *Выберите сотрудника:*",
        parse_mode='Markdown', reply_markup=employee_keyboard
    )

def expense_employee(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Возврат в главное меню", reply_markup=main_keyboard)
        return
    
    emp = text.replace('👤 ', '')
    if emp not in EMPLOYEES:
        update.message.reply_text("❌ Выберите из кнопок:", reply_markup=employee_keyboard)
        return
    
    data = user_data.pop(chat_id)
    
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
    
    formatted = f"{data['amount']:,.0f} ₽".replace(',', ' ')
    if data['amount'] != int(data['amount']):
        formatted = f"{data['amount']:,.2f} ₽".replace(',', ' ')
    
    update.message.reply_text(
        f"✅ *РАСХОД #{op['id']} ЗАПИСАН!*\n"
        f"━━━━━━━━━━━━━━\n\n"
        f"💰 *Сумма:* {formatted}\n"
        f"📋 *Описание:* {data['description']}\n"
        f"👤 *Сотрудник:* {emp}",
        parse_mode='Markdown', reply_markup=main_keyboard
    )

# ========== СТАТИСТИКА ==========
def show_stats(update, context):
    ops = get_all_operations()
    
    if not ops:
        update.message.reply_text("📭 Нет данных", reply_markup=main_keyboard)
        return
    
    income = sum(o['amount'] for o in ops if o['type'] == 'income')
    expense = sum(o['amount'] for o in ops if o['type'] == 'expense')
    inc_count = len([o for o in ops if o['type'] == 'income'])
    exp_count = len([o for o in ops if o['type'] == 'expense'])
    
    # По объемам
    ml6 = sum(o['amount'] for o in ops if o['type'] == 'income' and o.get('volume') == '6ml')
    ml10 = sum(o['amount'] for o in ops if o['type'] == 'income' and o.get('volume') == '10ml')
    
    # Топ парфюмы
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
        top = sorted(parfums.items(), key=lambda x: -x[1]['sum'])[:5]
        for name, data in top:
            text += f"   • {name}: {data['qty']} шт ({data['sum']:,.0f} ₽)\n".replace(',', ' ')
    
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
        update.message.reply_text("📭 Нет данных", reply_markup=main_keyboard)
        return
    
    text = "📋 *ТАБЛИЦА ПАРФЮМОВ*\n"
    text += "━━━━━━━━━━━━━━━━━━━━\n\n"
    
    sorted_items = sorted(parfums.items(), key=lambda x: -x[1]['sum'])
    for idx, (key, data) in enumerate(sorted_items, 1):
        text += f"{idx}. *{data['name']}* ({data['volume']})\n"
        text += f"   ├─ Продано: {data['qty']} шт\n"
        text += f"   ├─ Сумма: {data['sum']:,.0f} ₽\n"
        text += f"   └─ Продаж: {data['count']}\n\n".replace(',', ' ')
    
    # Итоги по объемам
    ml6 = sum(d['sum'] for k, d in parfums.items() if '6ml' in k)
    ml10 = sum(d['sum'] for k, d in parfums.items() if '10ml' in k)
    
    text += "━━━━━━━━━━━━━━━━━━━━\n"
    text += f"📊 *6ml:* {ml6:,.0f} ₽\n".replace(',', ' ')
    text += f"📊 *10ml:* {ml10:,.0f} ₽".replace(',', ' ')
    
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=main_keyboard)

def show_employees(update, context):
    ops = get_all_operations()
    
    stats = {e: {'inc': 0, 'exp': 0, 'inc_count': 0, 'exp_count': 0, 'parfums': {}} for e in EMPLOYEES}
    
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
        text += f"   📈 Доходы: `{d['inc']:,.0f} ₽` ({d['inc_count']} шт)\n"
        text += f"   📉 Расходы: `{d['exp']:,.0f} ₽` ({d['exp_count']} шт)\n"
        text += f"   💎 Итог: `{profit:,.0f} ₽`\n".replace(',', ' ')
        
        if d['parfums']:
            text += f"   📦 Продажи:\n"
            top = sorted(d['parfums'].items(), key=lambda x: -x[1])[:3]
            for p, q in top:
                text += f"      • {p}: {q} шт\n"
        text += "\n"
    
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=main_keyboard)

# ========== РЕДАКТИРОВАНИЕ ==========
def edit_start(update, context):
    ops = get_all_operations()
    
    if not ops:
        update.message.reply_text("📭 Нет операций", reply_markup=main_keyboard)
        return
    
    ops.sort(key=lambda x: x['id'], reverse=True)
    kb = []
    
    for o in ops[:10]:
        amount = f"{o['amount']:,.0f} ₽".replace(',', ' ')
        if o['type'] == 'income':
            desc = f"{o['name']} {o['volume']} x{o['quantity']}"
        else:
            desc = o['description'][:20]
        
        btn = f"#{o['id']} {o['type_display']} {amount} - {desc}"
        if len(btn) > 40:
            btn = btn[:37] + "..."
        kb.append([InlineKeyboardButton(btn, callback_data=f"edit_{o['id']}")])
    
    kb.append([InlineKeyboardButton("🔙 Отмена", callback_data="cancel")])
    
    update.message.reply_text(
        "✏️ *ВЫБЕРИТЕ ОПЕРАЦИЮ:*\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🔹 *Последние 10 операций:*",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode='Markdown'
    )

def edit_callback(update, context):
    query = update.callback_query
    query.answer()
    data = query.data
    
    if data == "cancel":
        query.edit_message_text("🔙 Отменено")
        query.message.reply_text("Главное меню:", reply_markup=main_keyboard)
        return
    
    if data.startswith("edit_"):
        op_id = int(data.split('_')[1])
        ops = get_all_operations()
        op = next((o for o in ops if o['id'] == op_id), None)
        
        if not op:
            query.edit_message_text("❌ Не найдено")
            return
        
        amount = f"{op['amount']:,.0f} ₽".replace(',', ' ')
        if op['type'] == 'income':
            text = (
                f"📌 *ПРОДАЖА #{op_id}*\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📦 {op['name']} {op['volume']} x{op['quantity']}\n"
                f"👤 {op['employee']}\n"
                f"💳 {op['payment']} {op.get('bank', '')}\n"
                f"💰 {amount}\n"
                f"📅 {op['date']}"
            )
        else:
            text = (
                f"📌 *РАСХОД #{op_id}*\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📋 {op['description']}\n"
                f"👤 {op['employee']}\n"
                f"💰 {amount}\n"
                f"📅 {op['date']}"
            )
        
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Изменить сумму", callback_data=f"sum_{op_id}")],
            [InlineKeyboardButton("❌ Удалить", callback_data=f"del_{op_id}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")]
        ])
        query.edit_message_text(text, parse_mode='Markdown', reply_markup=kb)
    
    elif data.startswith("sum_"):
        op_id = int(data.split('_')[1])
        context.user_data['edit_id'] = op_id
        query.edit_message_text(f"✏️ Введите новую сумму для операции #{op_id}:")
    
    elif data.startswith("del_"):
        op_id = int(data.split('_')[1])
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Да, удалить", callback_data=f"yes_{op_id}")],
            [InlineKeyboardButton("❌ Нет", callback_data="back")]
        ])
        query.edit_message_text(f"⚠️ Удалить операцию #{op_id}?", reply_markup=kb)
    
    elif data.startswith("yes_"):
        op_id = int(data.split('_')[1])
        data = load_data()
        data['operations'] = [o for o in data['operations'] if o['id'] != op_id]
        save_data(data)
        query.edit_message_text(f"✅ Операция #{op_id} удалена")
        query.message.reply_text("Главное меню:", reply_markup=main_keyboard)
    
    elif data == "back":
        edit_start(update, context)

def handle_edit_input(update, context):
    if 'edit_id' not in context.user_data:
        return
    
    try:
        new_sum = float(update.message.text.replace(' ', '').replace(',', '.'))
        op_id = context.user_data['edit_id']
        
        data = load_data()
        for o in data['operations']:
            if o['id'] == op_id:
                o['amount'] = new_sum
                break
        save_data(data)
        
        formatted = f"{new_sum:,.0f} ₽".replace(',', ' ')
        update.message.reply_text(f"✅ Сумма изменена на {formatted}", reply_markup=main_keyboard)
    except:
        update.message.reply_text("❌ Введите сумму", reply_markup=main_keyboard)
    
    del context.user_data['edit_id']

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
        update.message.reply_text("🔙 Главное меню", reply_markup=main_keyboard)
        return
    
    # Редактирование
    if 'edit_id' in context.user_data:
        handle_edit_input(update, context)
        return
    
    # Состояния дохода
    if chat_id in user_data and user_data[chat_id].get('type') != 'expense':
        step = user_data[chat_id].get('step')
        if step == 'name': income_name(update, context)
        elif step == 'volume': income_volume(update, context)
        elif step == 'quantity': income_quantity(update, context)
        elif step == 'employee': income_employee(update, context)
        elif step == 'payment': income_payment(update, context)
        elif step == 'bank': income_bank(update, context)
        elif step == 'amount': income_amount(update, context)
        return
    
    # Состояния расхода
    if chat_id in user_data and user_data[chat_id].get('type') == 'expense':
        step = user_data[chat_id].get('step')
        if step == 'amount': expense_amount(update, context)
        elif step == 'description': expense_description(update, context)
        elif step == 'employee': expense_employee(update, context)
        return
    
    # Меню
    if text == '💰 Доход': income_start(update, context)
    elif text == '💸 Расход': expense_start(update, context)
    elif text == '📊 Статистика': show_stats(update, context)
    elif text == '📋 Таблица парфюмов': show_parfums(update, context)
    elif text == '👥 Статистика коллег': show_employees(update, context)
    elif text == '✏️ Редактировать/Удалить': edit_start(update, context)

def main():
    print("🚀 Бот запускается...")
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(edit_callback))
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    
    print("✅ Бот готов к работе!")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
