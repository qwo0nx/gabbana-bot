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

# ========== КЛАВИАТУРЫ ==========
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
user_states = {}  # {chat_id: {'type': 'income', 'step': 'name', 'data': {}}}

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
    
    text = (
        "✨ *Gabbana&Home BUDGET* ✨\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "👋 *Добро пожаловать!*\n\n"
        "📊 *Парфюмерный учет*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "💰 *Доход* – продажа парфюма\n"
        "💸 *Расход* – закупки, аренда, реклама\n"
        "📊 *Статистика* – общие цифры\n"
        "📋 *Таблица парфюмов* – все продажи\n"
        "👥 *Статистика коллег* – по сотрудникам\n"
        "✏️ *Редактировать/Удалить* – изменить запись"
    )
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=main_keyboard)

# ========== ДОХОД ==========
def income_start(update, context):
    chat_id = update.effective_chat.id
    user_states[chat_id] = {'type': 'income', 'step': 'name', 'data': {}}
    update.message.reply_text(
        "💵 *ДОХОД*\n━━━━━━━━━━━━━━\n\n"
        "📝 *Шаг 1 из 7*\n\n"
        "✏️ *Введите название парфюма:*",
        parse_mode='Markdown', reply_markup=cancel_keyboard
    )

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
        update.message.reply_text(
            f"✅ *Название:* {text}\n━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 2 из 7*\n\n"
            f"🔢 *Выберите объем:*",
            parse_mode='Markdown', reply_markup=volume_keyboard
        )
    
    elif step == 'volume':
        if text not in ['6ml', '10ml']:
            update.message.reply_text("❌ Выберите объем из кнопок:", reply_markup=volume_keyboard)
            return
        state['data']['volume'] = text
        state['step'] = 'quantity'
        update.message.reply_text(
            f"✅ *Объем:* {text}\n━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 3 из 7*\n\n"
            f"🔢 *Введите количество флаконов:*",
            parse_mode='Markdown', reply_markup=cancel_keyboard
        )
    
    elif step == 'quantity':
        try:
            qty = int(text)
            if qty <= 0: raise ValueError
            state['data']['quantity'] = qty
            state['step'] = 'employee'
            update.message.reply_text(
                f"✅ *Количество:* {qty} шт\n━━━━━━━━━━━━━━\n\n"
                f"📝 *Шаг 4 из 7*\n\n"
                f"👤 *Выберите сотрудника:*",
                parse_mode='Markdown', reply_markup=employee_keyboard
            )
        except:
            update.message.reply_text("❌ Введите число (1, 2, 3...)", reply_markup=cancel_keyboard)
    
    elif step == 'employee':
        emp = text.replace('👤 ', '')
        if emp not in EMPLOYEES:
            update.message.reply_text("❌ Выберите из кнопок:", reply_markup=employee_keyboard)
            return
        state['data']['employee'] = emp
        state['step'] = 'payment'
        update.message.reply_text(
            f"✅ *Сотрудник:* {emp}\n━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 5 из 7*\n\n"
            f"💳 *Выберите способ оплаты:*",
            parse_mode='Markdown', reply_markup=payment_keyboard
        )
    
    elif step == 'payment':
        if 'Перевод' in text:
            state['data']['payment'] = 'Перевод'
            state['step'] = 'bank'
            update.message.reply_text(
                f"✅ *Способ оплаты:* {text}\n━━━━━━━━━━━━━━\n\n"
                f"📝 *Шаг 6 из 7*\n\n"
                f"🏦 *Выберите банк:*",
                parse_mode='Markdown', reply_markup=bank_keyboard
            )
        elif 'Наличка' in text:
            state['data']['payment'] = 'Наличка'
            state['data']['bank'] = '-'
            state['step'] = 'amount'
            update.message.reply_text(
                f"✅ *Способ оплаты:* {text}\n━━━━━━━━━━━━━━\n\n"
                f"📝 *Шаг 7 из 7*\n\n"
                f"💰 *Введите сумму:*",
                parse_mode='Markdown', reply_markup=cancel_keyboard
            )
        else:
            update.message.reply_text("❌ Выберите из кнопок:", reply_markup=payment_keyboard)
    
    elif step == 'bank':
        bank = text.replace('🏦 ', '') if '🏦' in text else text
        state['data']['bank'] = bank
        state['step'] = 'amount'
        update.message.reply_text(
            f"✅ *Банк:* {bank}\n━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 7 из 7*\n\n"
            f"💰 *Введите сумму:*",
            parse_mode='Markdown', reply_markup=cancel_keyboard
        )
    
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
            update.message.reply_text(
                f"✅ *ПРОДАЖА #{op['id']}*\n━━━━━━━━━━━━━━\n\n"
                f"📌 {data['name']} {data['volume']} x{data['quantity']}\n"
                f"👤 {data['employee']}\n"
                f"💰 {formatted}",
                parse_mode='Markdown', reply_markup=main_keyboard
            )
        except:
            update.message.reply_text("❌ Введите сумму", reply_markup=cancel_keyboard)

# ========== РАСХОД ==========
def expense_start(update, context):
    chat_id = update.effective_chat.id
    user_states[chat_id] = {'type': 'expense', 'step': 'amount', 'data': {}}
    update.message.reply_text(
        "💳 *РАСХОД*\n━━━━━━━━━━━━━━\n\n"
        "📝 *Шаг 1 из 3*\n\n"
        "💰 *Введите сумму:*",
        parse_mode='Markdown', reply_markup=cancel_keyboard
    )

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
            update.message.reply_text(
                f"✅ *Сумма:* {formatted}\n━━━━━━━━━━━━━━\n\n"
                f"📝 *Шаг 2 из 3*\n\n"
                f"✏️ *Введите описание:*",
                parse_mode='Markdown', reply_markup=cancel_keyboard
            )
        except:
            update.message.reply_text("❌ Введите сумму", reply_markup=cancel_keyboard)
    
    elif step == 'description':
        state['data']['description'] = text
        state['step'] = 'employee'
        update.message.reply_text(
            f"✅ *Описание:* {text}\n━━━━━━━━━━━━━━\n\n"
            f"📝 *Шаг 3 из 3*\n\n"
            f"👤 *Выберите сотрудника:*",
            parse_mode='Markdown', reply_markup=employee_keyboard
        )
    
    elif step == 'employee':
        emp = text.replace('👤 ', '')
        if emp not in EMPLOYEES:
            update.message.reply_text("❌ Выберите из кнопок:", reply_markup=employee_keyboard)
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
        update.message.reply_text(
            f"✅ *РАСХОД #{op['id']}*\n━━━━━━━━━━━━━━\n\n"
            f"💰 {formatted}\n"
            f"📋 {data['description']}\n"
            f"👤 {emp}",
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
    
    ml6 = sum(o['amount'] for o in ops if o['type'] == 'income' and o.get('volume') == '6ml')
    ml10 = sum(o['amount'] for o in ops if o['type'] == 'income' and o.get('volume') == '10ml')
    
    text = (
        f"📊 *ОБЩАЯ СТАТИСТИКА*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📈 *Доходы:* {income:,.0f} ₽ ({inc_count})\n"
        f"📉 *Расходы:* {expense:,.0f} ₽ ({exp_count})\n"
        f"💎 *Итог:* {income - expense:,.0f} ₽\n\n"
        f"📦 *По объему:*\n"
        f"   • 6ml: {ml6:,.0f} ₽\n"
        f"   • 10ml: {ml10:,.0f} ₽"
    ).replace(',', ' ')
    
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=main_keyboard)

def show_parfums(update, context):
    ops = get_all_operations()
    parfums = {}
    
    for o in ops:
        if o['type'] == 'income':
            key = f"{o['name']} ({o['volume']})"
            if key not in parfums:
                parfums[key] = {'qty': 0, 'sum': 0, 'count': 0}
            parfums[key]['qty'] += o['quantity']
            parfums[key]['sum'] += o['amount']
            parfums[key]['count'] += 1
    
    if not parfums:
        update.message.reply_text("📭 Нет данных", reply_markup=main_keyboard)
        return
    
    text = "📋 *ТАБЛИЦА ПАРФЮМОВ*\n━━━━━━━━━━━━━━━━\n\n"
    for name, data in sorted(parfums.items(), key=lambda x: -x[1]['sum']):
        text += f"• {name}: {data['qty']} шт - {data['sum']:,.0f} ₽ ({data['count']} продаж)\n".replace(',', ' ')
    
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=main_keyboard)

def show_employees(update, context):
    ops = get_all_operations()
    stats = {e: {'inc': 0, 'exp': 0, 'inc_count': 0, 'exp_count': 0} for e in EMPLOYEES}
    
    for o in ops:
        emp = o.get('employee')
        if emp and emp in stats:
            if o['type'] == 'income':
                stats[emp]['inc'] += o['amount']
                stats[emp]['inc_count'] += 1
            else:
                stats[emp]['exp'] += o['amount']
                stats[emp]['exp_count'] += 1
    
    text = "👥 *СТАТИСТИКА СОТРУДНИКОВ*\n━━━━━━━━━━━━━━━━\n\n"
    for emp in EMPLOYEES:
        d = stats[emp]
        text += f"• *{emp}*:\n"
        text += f"  ├─ Доход: {d['inc']:,.0f} ₽ ({d['inc_count']})\n"
        text += f"  ├─ Расход: {d['exp']:,.0f} ₽ ({d['exp_count']})\n"
        text += f"  └─ Итог: {d['inc'] - d['exp']:,.0f} ₽\n\n".replace(',', ' ')
    
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
        btn = f"#{o['id']} {o['type_display']} {amount}"
        kb.append([InlineKeyboardButton(btn, callback_data=f"edit_{o['id']}")])
    
    kb.append([InlineKeyboardButton("🔙 Отмена", callback_data="cancel")])
    update.message.reply_text(
        "✏️ *ВЫБЕРИТЕ ОПЕРАЦИЮ:*",
        reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown'
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
            text = f"📌 *ПРОДАЖА #{op_id}*\n{op['name']} {op['volume']} x{op['quantity']}\n👤 {op['employee']}\n💰 {amount}"
        else:
            text = f"📌 *РАСХОД #{op_id}*\n📋 {op['description']}\n👤 {op['employee']}\n💰 {amount}"
        
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Изменить сумму", callback_data=f"sum_{op_id}")],
            [InlineKeyboardButton("❌ Удалить", callback_data=f"del_{op_id}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="back")]
        ])
        query.edit_message_text(text, parse_mode='Markdown', reply_markup=kb)
    
    elif data.startswith("sum_"):
        op_id = int(data.split('_')[1])
        context.user_data['edit_id'] = op_id
        query.edit_message_text(f"✏️ Введите новую сумму для #{op_id}:")
    
    elif data.startswith("del_"):
        op_id = int(data.split('_')[1])
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Да", callback_data=f"yes_{op_id}")],
            [InlineKeyboardButton("❌ Нет", callback_data="back")]
        ])
        query.edit_message_text(f"⚠️ Удалить операцию #{op_id}?", reply_markup=kb)
    
    elif data.startswith("yes_"):
        op_id = int(data.split('_')[1])
        delete_operation(op_id)
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
        update_operation(op_id, {'amount': new_sum})
        update.message.reply_text(f"✅ Сумма изменена", reply_markup=main_keyboard)
    except:
        update.message.reply_text("❌ Ошибка", reply_markup=main_keyboard)
    
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
        if chat_id in user_states:
            del user_states[chat_id]
        context.user_data.clear()
        update.message.reply_text("🔙 Главное меню", reply_markup=main_keyboard)
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
