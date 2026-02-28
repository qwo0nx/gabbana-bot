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

# Клавиатуры
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

# Состояния
INCOME_STATES = {'NAME': 1, 'VOLUME': 2, 'QUANTITY': 3, 'EMPLOYEE': 4, 'PAYMENT': 5, 'BANK': 6, 'AMOUNT': 7}
EXPENSE_STATES = {'AMOUNT': 1, 'DESCRIPTION': 2, 'EMPLOYEE': 3}

user_data = {}

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

def start(update, context):
    if not check_access(update):
        update.message.reply_text("❌ У вас нет доступа")
        return
    update.message.reply_text(
        "✨ *Gabbana&Home Budget* ✨\n\n"
        "💰 Доход - продажа парфюма\n"
        "💸 Расход - закупки/расходы\n"
        "📊 Статистика - общая\n"
        "📋 Таблица парфюмов - все парфюмы\n"
        "👥 Статистика коллег - по сотрудникам\n"
        "✏️ Редактировать/Удалить",
        parse_mode='Markdown', reply_markup=main_keyboard
    )

# ========== ДОХОД ==========
def income_start(update, context):
    chat_id = update.effective_chat.id
    user_data[chat_id] = {'type': 'income', 'state': INCOME_STATES['NAME']}
    update.message.reply_text(
        "💵 *ШАГ 1/7*\n\nВведите *название парфюма*:",
        parse_mode='Markdown', reply_markup=cancel_keyboard
    )

def income_name(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Отменено", reply_markup=main_keyboard)
        return
    user_data[chat_id]['parfum_name'] = text
    user_data[chat_id]['state'] = INCOME_STATES['VOLUME']
    update.message.reply_text(
        f"✅ *{text}*\n\n💵 *ШАГ 2/7*\n\nВыберите *объем*:",
        parse_mode='Markdown', reply_markup=volume_keyboard
    )

def income_volume(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Отменено", reply_markup=main_keyboard)
        return
    if text not in ['6ml', '10ml']:
        update.message.reply_text("❌ Выберите из кнопок:", reply_markup=volume_keyboard)
        return
    user_data[chat_id]['volume'] = text
    user_data[chat_id]['state'] = INCOME_STATES['QUANTITY']
    update.message.reply_text(
        f"✅ *{text}*\n\n💵 *ШАГ 3/7*\n\nВведите *количество*:",
        parse_mode='Markdown', reply_markup=cancel_keyboard
    )

def income_quantity(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Отменено", reply_markup=main_keyboard)
        return
    try:
        qty = int(text)
        if qty <= 0: raise ValueError
        user_data[chat_id]['quantity'] = qty
        user_data[chat_id]['state'] = INCOME_STATES['EMPLOYEE']
        update.message.reply_text(
            f"✅ *{qty} шт*\n\n💵 *ШАГ 4/7*\n\nВыберите *сотрудника*:",
            parse_mode='Markdown', reply_markup=employee_keyboard
        )
    except:
        update.message.reply_text("❌ Введите число", reply_markup=cancel_keyboard)

def income_employee(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Отменено", reply_markup=main_keyboard)
        return
    emp = text.replace('👤 ', '')
    if emp not in EMPLOYEES:
        update.message.reply_text("❌ Выберите из кнопок:", reply_markup=employee_keyboard)
        return
    user_data[chat_id]['employee'] = emp
    user_data[chat_id]['state'] = INCOME_STATES['PAYMENT']
    update.message.reply_text(
        f"✅ *{emp}*\n\n💵 *ШАГ 5/7*\n\nВыберите *оплату*:",
        parse_mode='Markdown', reply_markup=payment_keyboard
    )

def income_payment(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Отменено", reply_markup=main_keyboard)
        return
    if 'Перевод' in text:
        user_data[chat_id]['payment'] = 'Перевод'
        user_data[chat_id]['state'] = INCOME_STATES['BANK']
        update.message.reply_text(
            f"✅ *{text}*\n\n💵 *ШАГ 6/7*\n\nВыберите *банк*:",
            parse_mode='Markdown', reply_markup=bank_keyboard
        )
    elif 'Наличка' in text:
        user_data[chat_id]['payment'] = 'Наличка'
        user_data[chat_id]['bank'] = '-'
        user_data[chat_id]['state'] = INCOME_STATES['AMOUNT']
        update.message.reply_text(
            f"✅ *{text}*\n\n💵 *ШАГ 7/7*\n\nВведите *сумму*:",
            parse_mode='Markdown', reply_markup=cancel_keyboard
        )
    else:
        update.message.reply_text("❌ Выберите из кнопок:", reply_markup=payment_keyboard)

def income_bank(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Отменено", reply_markup=main_keyboard)
        return
    bank = text.replace('🏦 ', '') if '🏦' in text else text
    user_data[chat_id]['bank'] = bank
    user_data[chat_id]['state'] = INCOME_STATES['AMOUNT']
    update.message.reply_text(
        f"✅ *{bank}*\n\n💵 *ШАГ 7/7*\n\nВведите *сумму*:",
        parse_mode='Markdown', reply_markup=cancel_keyboard
    )

def income_amount(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Отменено", reply_markup=main_keyboard)
        return
    try:
        amount = float(text.replace(' ', '').replace(',', '.'))
        data = user_data.pop(chat_id)
        op = {
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
            'added_by': update.effective_user.first_name
        }
        add_operation(op)
        formatted = f"{amount:,.0f} ₽".replace(',', ' ')
        update.message.reply_text(
            f"✅ *ПРОДАЖА #{op['id']}*\n\n"
            f"📌 {data['parfum_name']} {data['volume']} x{data['quantity']}\n"
            f"👤 {data['employee']}\n"
            f"💰 {formatted}",
            parse_mode='Markdown', reply_markup=main_keyboard
        )
    except:
        update.message.reply_text("❌ Введите сумму", reply_markup=cancel_keyboard)

# ========== РАСХОД ==========
def expense_start(update, context):
    chat_id = update.effective_chat.id
    user_data[chat_id] = {'type': 'expense', 'state': EXPENSE_STATES['AMOUNT']}
    update.message.reply_text(
        "💳 *ШАГ 1/3*\n\nВведите *сумму*:",
        parse_mode='Markdown', reply_markup=cancel_keyboard
    )

def expense_amount(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Отменено", reply_markup=main_keyboard)
        return
    try:
        amount = float(text.replace(' ', '').replace(',', '.'))
        user_data[chat_id]['amount'] = amount
        user_data[chat_id]['state'] = EXPENSE_STATES['DESCRIPTION']
        formatted = f"{amount:,.0f} ₽".replace(',', ' ')
        update.message.reply_text(
            f"✅ *{formatted}*\n\n💳 *ШАГ 2/3*\n\nВведите *описание*:",
            parse_mode='Markdown', reply_markup=cancel_keyboard
        )
    except:
        update.message.reply_text("❌ Введите сумму", reply_markup=cancel_keyboard)

def expense_description(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Отменено", reply_markup=main_keyboard)
        return
    user_data[chat_id]['description'] = text
    user_data[chat_id]['state'] = EXPENSE_STATES['EMPLOYEE']
    update.message.reply_text(
        f"✅ *{text}*\n\n💳 *ШАГ 3/3*\n\nВыберите *сотрудника*:",
        parse_mode='Markdown', reply_markup=employee_keyboard
    )

def expense_employee(update, context):
    chat_id = update.effective_chat.id
    text = update.message.text
    if text == '🔙 Отмена':
        del user_data[chat_id]
        update.message.reply_text("🔙 Отменено", reply_markup=main_keyboard)
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
    update.message.reply_text(
        f"✅ *РАСХОД #{op['id']}*\n\n"
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
    
    text = (
        f"📊 *ОБЩАЯ СТАТИСТИКА*\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"💰 Доходы: {income:,.0f} ₽ ({inc_count})\n"
        f"💸 Расходы: {expense:,.0f} ₽ ({exp_count})\n"
        f"💎 Итог: {income - expense:,.0f} ₽"
    ).replace(',', ' ')
    
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=main_keyboard)

def show_parfums(update, context):
    ops = get_all_operations()
    parfums = {}
    for o in ops:
        if o['type'] == 'income':
            key = f"{o['parfum_name']} ({o['volume']})"
            if key not in parfums:
                parfums[key] = {'qty': 0, 'sum': 0}
            parfums[key]['qty'] += o['quantity']
            parfums[key]['sum'] += o['amount']
    
    if not parfums:
        update.message.reply_text("📭 Нет данных", reply_markup=main_keyboard)
        return
    
    text = "📋 *ПАРФЮМЫ*\n━━━━━━━━━━\n\n"
    for name, data in sorted(parfums.items(), key=lambda x: -x[1]['sum']):
        text += f"• {name}: {data['qty']} шт - {data['sum']:,.0f} ₽\n".replace(',', ' ')
    
    update.message.reply_text(text, parse_mode='Markdown', reply_markup=main_keyboard)

def show_employees(update, context):
    ops = get_all_operations()
    stats = {e: {'inc': 0, 'exp': 0} for e in EMPLOYEES}
    
    for o in ops:
        if o.get('employee') in stats:
            if o['type'] == 'income':
                stats[o['employee']]['inc'] += o['amount']
            else:
                stats[o['employee']]['exp'] += o['amount']
    
    text = "👥 *СОТРУДНИКИ*\n━━━━━━━━━━\n\n"
    for e in EMPLOYEES:
        inc = stats[e]['inc']
        exp = stats[e]['exp']
        total = inc - exp
        text += f"• {e}: +{inc:,.0f} / -{exp:,.0f} = {total:,.0f} ₽\n".replace(',', ' ')
    
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
        btn = f"#{o['id']} {o['type_display']} {o['amount']:,.0f} ₽".replace(',', ' ')
        if len(btn) > 40:
            btn = btn[:37] + "..."
        kb.append([InlineKeyboardButton(btn, callback_data=f"edit_{o['id']}")])
    kb.append([InlineKeyboardButton("🔙 Отмена", callback_data="cancel")])
    
    update.message.reply_text(
        "✏️ *ВЫБЕРИТЕ ОПЕРАЦИЮ:*",
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
            text = (f"📌 *ПРОДАЖА #{op_id}*\n"
                   f"{op['parfum_name']} {op['volume']} x{op['quantity']}\n"
                   f"👤 {op['employee']}\n"
                   f"💰 {amount}")
        else:
            text = (f"📌 *РАСХОД #{op_id}*\n"
                   f"📋 {op['description']}\n"
                   f"👤 {op['employee']}\n"
                   f"💰 {amount}")
        
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
        ops = get_all_operations()
        for o in ops:
            if o['id'] == op_id:
                o['amount'] = new_sum
                update_operation(op_id, o)
                break
        update.message.reply_text(f"✅ Сумма изменена", reply_markup=main_keyboard)
    except:
        update.message.reply_text("❌ Ошибка", reply_markup=main_keyboard)
    
    del context.user_data['edit_id']

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
    
    # Состояния
    if chat_id in user_data:
        if user_data[chat_id]['type'] == 'income':
            state = user_data[chat_id]['state']
            if state == 1: income_name(update, context)
            elif state == 2: income_volume(update, context)
            elif state == 3: income_quantity(update, context)
            elif state == 4: income_employee(update, context)
            elif state == 5: income_payment(update, context)
            elif state == 6: income_bank(update, context)
            elif state == 7: income_amount(update, context)
        elif user_data[chat_id]['type'] == 'expense':
            state = user_data[chat_id]['state']
            if state == 1: expense_amount(update, context)
            elif state == 2: expense_description(update, context)
            elif state == 3: expense_employee(update, context)
        return
    
    # Меню
    if text == '💰 Доход': income_start(update, context)
    elif text == '💸 Расход': expense_start(update, context)
    elif text == '📊 Статистика': show_stats(update, context)
    elif text == '📋 Таблица парфюмов': show_parfums(update, context)
    elif text == '👥 Статистика коллег': show_employees(update, context)
    elif text == '✏️ Редактировать/Удалить': edit_start(update, context)

def main():
    print("🚀 Запуск...")
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(edit_callback))
    dp.add_handler(MessageHandler(Filters.text, handle_message))
    
    print("✅ Готов!")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
