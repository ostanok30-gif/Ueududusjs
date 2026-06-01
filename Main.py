#!/usr/bin/env python3
"""
OxatovAccount Bot v3.0 - Максимальная админ-панель
Запуск: python3 bot.py
"""

import asyncio
import json
import random
import hashlib
import sqlite3
import os
import csv
import io
from datetime import datetime, timedelta
from aiohttp import web

from telethon import TelegramClient, events
from telethon.tl.custom import Button
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError

# ==================== КОНФИГУРАЦИЯ ====================
BOT_TOKEN = "8598355142:AAGQ8LZPeR00mltNKxmjb2bEZtQorV_5pEs"
ADMIN_IDS = [8640180536]
API_ID = 34928216
API_HASH = "29f66350a892e8b69a83b50d7e99bd27"

MINIAPP_URL = "https://oxatovaccount.bothost.tech"
CODE_TIMEOUT_MINUTES = 3
BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

# ==================== БАЗА ДАННЫХ ====================
class Database:
    def __init__(self):
        self.conn = sqlite3.connect("shop.db", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
    
    def _init_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                balance INTEGER DEFAULT 0,
                username TEXT,
                first_name TEXT,
                total_bought INTEGER DEFAULT 0,
                total_spent INTEGER DEFAULT 0,
                last_activity TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_string TEXT,
                phone TEXT,
                country TEXT,
                dc TEXT DEFAULT 'DC1',
                price INTEGER NOT NULL,
                original_price INTEGER,
                status TEXT DEFAULT 'available',
                buyer_id INTEGER,
                sold_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                account_id INTEGER,
                phone TEXT,
                amount INTEGER,
                status TEXT DEFAULT 'completed',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS auth_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT,
                user_id INTEGER,
                phone TEXT,
                code TEXT,
                expires_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS star_deposits (
                gift_id TEXT PRIMARY KEY,
                user_id INTEGER,
                stars_count INTEGER,
                processed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                action TEXT,
                target TEXT,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS mailings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT,
                sent_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('stars_rate', '1')")
        self.conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('markup', '20')")
        self.conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('maintenance', '0')")
        self.conn.commit()
    
    def log_action(self, admin_id, action, target, details=""):
        self.conn.execute("INSERT INTO admin_logs (admin_id, action, target, details) VALUES (?, ?, ?, ?)",
                         (admin_id, action, target, details))
        self.conn.commit()
    
    def add_user(self, user_id, username=None, first_name=None):
        self.conn.execute("INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)", 
                         (user_id, username, first_name))
        self.conn.commit()
    
    def get_user(self, user_id):
        return self.conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    
    def get_balance(self, user_id):
        row = self.conn.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return row['balance'] if row else 0
    
    def add_balance(self, user_id, amount, admin_id=None):
        self.conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        if admin_id:
            self.log_action(admin_id, "add_balance", str(user_id), f"+{amount}")
        self.conn.commit()
        return True
    
    def subtract_balance(self, user_id, amount, admin_id=None):
        current = self.get_balance(user_id)
        if current < amount:
            return False
        self.conn.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
        if admin_id:
            self.log_action(admin_id, "sub_balance", str(user_id), f"-{amount}")
        self.conn.commit()
        return True
    
    def get_all_users(self, limit=100, offset=0):
        return self.conn.execute("SELECT user_id, username, first_name, balance, total_bought, total_spent, created_at FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset)).fetchall()
    
    def get_total_users(self):
        row = self.conn.execute("SELECT COUNT(*) FROM users").fetchone()
        return row[0] if row else 0
    
    def get_top_spenders(self, limit=10):
        return self.conn.execute("SELECT user_id, username, total_spent FROM users ORDER BY total_spent DESC LIMIT ?", (limit,)).fetchall()
    
    def get_available_accounts(self, country=None):
        if country:
            return self.conn.execute("SELECT * FROM accounts WHERE status = 'available' AND country = ? ORDER BY price", (country,)).fetchall()
        return self.conn.execute("SELECT * FROM accounts WHERE status = 'available' ORDER BY price").fetchall()
    
    def get_account_by_id(self, account_id):
        return self.conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    
    def get_all_accounts(self, status=None):
        if status:
            return self.conn.execute("SELECT * FROM accounts WHERE status = ? ORDER BY created_at DESC", (status,)).fetchall()
        return self.conn.execute("SELECT * FROM accounts ORDER BY created_at DESC").fetchall()
    
    def get_total_accounts(self):
        row = self.conn.execute("SELECT COUNT(*) FROM accounts").fetchone()
        return row[0] if row else 0
    
    def get_accounts_by_country(self):
        return self.conn.execute("SELECT country, COUNT(*) as count, MIN(price) as min_price FROM accounts WHERE status = 'available' GROUP BY country").fetchall()
    
    def add_account(self, session_string, phone, country, price, original_price=None, admin_id=None):
        if original_price is None:
            original_price = price
        cursor = self.conn.execute("INSERT INTO accounts (session_string, phone, country, price, original_price) VALUES (?, ?, ?, ?, ?)",
                                   (session_string, phone, country, price, original_price))
        self.conn.commit()
        if admin_id:
            self.log_action(admin_id, "add_account", str(cursor.lastrowid), f"{country}, {price}★")
        return cursor.lastrowid
    
    def delete_account(self, account_id, admin_id=None):
        acc = self.get_account_by_id(account_id)
        if acc:
            self.conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
            self.conn.commit()
            if admin_id:
                self.log_action(admin_id, "delete_account", str(account_id), f"{acc['country']}, {acc['price']}★")
            return True
        return False
    
    def update_account_price(self, account_id, new_price, admin_id=None):
        self.conn.execute("UPDATE accounts SET price = ? WHERE id = ?", (new_price, account_id))
        self.conn.commit()
        if admin_id:
            self.log_action(admin_id, "update_price", str(account_id), f"new price: {new_price}★")
    
    def buy_account(self, account_id, user_id):
        account = self.get_account_by_id(account_id)
        if not account or account['status'] != 'available':
            return None
        
        balance = self.get_balance(user_id)
        if balance < account['price']:
            return None
        
        self.conn.execute("BEGIN TRANSACTION")
        try:
            self.conn.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (account['price'], user_id))
            self.conn.execute("UPDATE users SET total_bought = total_bought + 1, total_spent = total_spent + ? WHERE user_id = ?", (account['price'], user_id))
            self.conn.execute("UPDATE accounts SET status = 'sold', buyer_id = ?, sold_at = ? WHERE id = ?", 
                             (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), account_id))
            
            order_id = hashlib.md5(f"{user_id}{account_id}{datetime.now()}".encode()).hexdigest()[:16]
            code = str(random.randint(10000, 99999))
            expires = (datetime.now() + timedelta(minutes=CODE_TIMEOUT_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
            
            self.conn.execute("INSERT INTO orders (order_id, user_id, account_id, phone, amount) VALUES (?, ?, ?, ?, ?)",
                             (order_id, user_id, account_id, account['phone'], account['price']))
            self.conn.execute("INSERT INTO auth_codes (order_id, user_id, phone, code, expires_at) VALUES (?, ?, ?, ?, ?)",
                             (order_id, user_id, account['phone'], code, expires))
            self.conn.commit()
            
            return {'order_id': order_id, 'code': code, 'session': account['session_string'], 'phone': account['phone']}
        except:
            self.conn.execute("ROLLBACK")
            return None
    
    def get_user_orders(self, user_id, limit=50):
        return self.conn.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit)).fetchall()
    
    def get_all_orders(self, limit=100):
        return self.conn.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    
    def get_total_revenue(self):
        row = self.conn.execute("SELECT SUM(amount) FROM orders").fetchone()
        return row[0] if row[0] else 0
    
    def refresh_code(self, order_id, user_id, phone):
        new_code = str(random.randint(10000, 99999))
        expires = (datetime.now() + timedelta(minutes=CODE_TIMEOUT_MINUTES)).strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute("INSERT INTO auth_codes (order_id, user_id, phone, code, expires_at) VALUES (?, ?, ?, ?, ?)",
                         (order_id, user_id, phone, new_code, expires))
        self.conn.commit()
        return new_code
    
    def get_active_codes(self, user_id):
        return self.conn.execute("SELECT * FROM auth_codes WHERE user_id = ? AND expires_at > datetime('now')", (user_id,)).fetchall()
    
    def star_gift_exists(self, gift_id):
        row = self.conn.execute("SELECT * FROM star_deposits WHERE gift_id = ?", (gift_id,)).fetchone()
        return row is not None
    
    def add_star_deposit(self, gift_id, user_id, stars_count):
        self.conn.execute("INSERT INTO star_deposits (gift_id, user_id, stars_count, processed) VALUES (?, ?, ?, 1)", 
                         (gift_id, user_id, stars_count))
        self.conn.commit()
    
    def get_admin_logs(self, limit=50):
        return self.conn.execute("SELECT * FROM admin_logs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    
    def get_setting(self, key, default=None):
        row = self.conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row['value'] if row else default
    
    def set_setting(self, key, value, admin_id=None):
        self.conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()
        if admin_id:
            self.log_action(admin_id, "setting", key, value)
    
    def add_mailing(self, text):
        cursor = self.conn.execute("INSERT INTO mailings (text, status) VALUES (?, 'pending')", (text,))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_mailing(self, mailing_id, sent_count, failed_count, status):
        self.conn.execute("UPDATE mailings SET sent_count = ?, failed_count = ?, status = ? WHERE id = ?",
                         (sent_count, failed_count, status, mailing_id))
        self.conn.commit()
    
    def get_stats(self):
        users = self.get_total_users()
        accounts = self.get_total_accounts()
        active = self.conn.execute("SELECT COUNT(*) FROM accounts WHERE status = 'available'").fetchone()[0]
        sold = self.conn.execute("SELECT COUNT(*) FROM accounts WHERE status = 'sold'").fetchone()[0]
        revenue = self.get_total_revenue()
        orders = self.conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        today_orders = self.conn.execute("SELECT COUNT(*) FROM orders WHERE date(created_at) = date('now')").fetchone()[0]
        today_revenue = self.conn.execute("SELECT COALESCE(SUM(amount), 0) FROM orders WHERE date(created_at) = date('now')").fetchone()[0]
        
        return {
            'users': users, 'accounts': accounts, 'active': active, 'sold': sold,
            'revenue': revenue, 'orders': orders, 'today_orders': today_orders, 'today_revenue': today_revenue
        }
    
    def export_users_csv(self):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['user_id', 'username', 'first_name', 'balance', 'total_bought', 'total_spent', 'created_at'])
        users = self.conn.execute("SELECT user_id, username, first_name, balance, total_bought, total_spent, created_at FROM users").fetchall()
        for u in users:
            writer.writerow([u['user_id'], u['username'], u['first_name'], u['balance'], u['total_bought'], u['total_spent'], u['created_at']])
        return output.getvalue()
    
    def export_accounts_csv(self):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['id', 'phone', 'country', 'price', 'status', 'created_at'])
        accs = self.conn.execute("SELECT id, phone, country, price, status, created_at FROM accounts").fetchall()
        for a in accs:
            writer.writerow([a['id'], a['phone'], a['country'], a['price'], a['status'], a['created_at']])
        return output.getvalue()

db = Database()

# ==================== API ХЕНДЛЕРЫ ====================
async def handle_balance(request):
    user_id = int(request.query.get('user_id', 0))
    return web.json_response({"balance": db.get_balance(user_id)})

async def handle_catalog(request):
    accounts = db.get_available_accounts()
    items = [{"id": a['id'], "phone": "***", "country": a['country'], "dc": a['dc'], "price": a['price'], "status": a['status']} for a in accounts]
    return web.json_response({"items": items})

async def handle_orders(request):
    user_id = int(request.query.get('user_id', 0))
    orders = db.get_user_orders(user_id)
    orders_list = [{"order_id": o['order_id'], "phone": o['phone'], "amount": o['amount'], "status": o['status'], "date": o['created_at'][:16]} for o in orders]
    return web.json_response({"orders": orders_list})

async def handle_codes(request):
    user_id = int(request.query.get('user_id', 0))
    codes = db.get_active_codes(user_id)
    codes_list = [{"order_id": c['order_id'], "phone": c['phone'], "code": c['code'], "expires": c['expires_at']} for c in codes]
    return web.json_response({"codes": codes_list})

async def handle_buy(request):
    data = await request.json()
    user_id = int(data.get('user_id', 0))
    account_id = int(data.get('account_id', 0))
    result = db.buy_account(account_id, user_id)
    if result:
        return web.json_response({"success": True, "order_id": result['order_id'], "code": result['code']})
    return web.json_response({"success": False})

async def handle_refresh_code(request):
    data = await request.json()
    user_id = int(data.get('user_id', 0))
    order_id = data.get('order_id')
    phone = data.get('phone')
    new_code = db.refresh_code(order_id, user_id, phone)
    return web.json_response({"success": True, "code": new_code})

async def handle_deposit(request):
    data = await request.json()
    user_id = int(data.get('user_id', 0))
    amount = int(data.get('amount', 0))
    return web.json_response({"success": True, "message": f"Для пополнения на {amount} звезд отправьте подарок на аккаунт-приёмник"})

# ==================== ОСНОВНОЙ БОТ ====================
bot_client = None
user_states = {}
temp_clients = {}

async def start_bot():
    global bot_client
    
    bot_client = TelegramClient('bot_session', API_ID, API_HASH)
    await bot_client.start(bot_token=BOT_TOKEN)
    
    # Запуск API сервера
    app = web.Application()
    app.router.add_get('/api/balance', handle_balance)
    app.router.add_get('/api/catalog', handle_catalog)
    app.router.add_get('/api/orders', handle_orders)
    app.router.add_get('/api/codes', handle_codes)
    app.router.add_post('/api/buy', handle_buy)
    app.router.add_post('/api/refresh_code', handle_refresh_code)
    app.router.add_post('/api/deposit', handle_deposit)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    
    print("🚀 API сервер запущен на порту 8000")
    
    # ========== ОСНОВНЫЕ КОМАНДЫ ==========
    @bot_client.on(events.NewMessage(pattern='/start'))
    async def start_handler(event):
        user_id = event.sender_id
        db.add_user(user_id, event.sender.username, event.sender.first_name)
        maintenance = db.get_setting('maintenance', '0')
        if maintenance == '1':
            await event.respond("🔧 Бот на техническом обслуживании. Зайдите позже.")
            return
        
        await event.respond(
            "⚡ <b>OxatovAccount</b>\n\n"
            "Добро пожаловать в магазин Telegram аккаунтов!\n\n"
            "🛒 Нажми на кнопку ниже, чтобы открыть магазин\n"
            "💰 Баланс пополняется через Telegram Stars\n"
            "🔐 Коды приходят в приложение",
            buttons=[[Button.url("🛒 Открыть магазин", MINIAPP_URL)]],
            parse_mode='html'
        )
    
    @bot_client.on(events.NewMessage(pattern='/shop'))
    async def shop_handler(event):
        await event.respond("🛒 Открыть магазин:", buttons=[[Button.url("⭐ OxatovAccount", MINIAPP_URL)]])
    
    @bot_client.on(events.NewMessage(pattern='/balance'))
    async def balance_handler(event):
        balance = db.get_balance(event.sender_id)
        await event.respond(f"💰 Ваш баланс: <b>{balance} звезд</b>", parse_mode='html')
    
    # ========== АДМИН-ПАНЕЛЬ ==========
    @bot_client.on(events.NewMessage(pattern='/admin'))
    async def admin_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        stats = db.get_stats()
        await event.respond(
            "⚙️ <b>АДМИН-ПАНЕЛЬ</b>\n\n"
            f"📊 <b>СТАТИСТИКА</b>\n"
            f"👥 Пользователей: {stats['users']}\n"
            f"📱 Аккаунтов: {stats['accounts']} (🟢{stats['active']} 🔴{stats['sold']})\n"
            f"📦 Заказов: {stats['orders']} (сегодня: {stats['today_orders']})\n"
            f"💰 Выручка: {stats['revenue']} ★ (сегодня: {stats['today_revenue']} ★)\n\n"
            "📋 <b>КОМАНДЫ</b>\n"
            "/stats - детальная статистика\n"
            "/users - список пользователей\n"
            "/user <id> - информация о пользователе\n"
            "/add_balance <id> <sum> - добавить баланс\n"
            "/sub_balance <id> <sum> - списать баланс\n"
            "/accounts - список аккаунтов\n"
            "/account <id> - информация об аккаунте\n"
            "/add_account <session> <phone> <country> <price> - добавить аккаунт\n"
            "/del_account <id> - удалить аккаунт\n"
            "/price <id> <new_price> - изменить цену\n"
            "/orders - все заказы\n"
            "/top - топ пользователей\n"
            "/mailing <текст> - рассылка\n"
            "/set_markup <%> - установить наценку\n"
            "/set_stars_rate <курс> - установить курс Stars\n"
            "/maintenance on/off - техобслуживание\n"
            "/backup - создать бэкап\n"
            "/export_users - выгрузить пользователей CSV\n"
            "/export_accounts - выгрузить аккаунты CSV\n"
            "/logs - логи действий\n"
            "/settings - текущие настройки",
            parse_mode='html'
        )
    
    @bot_client.on(events.NewMessage(pattern='/stats'))
    async def stats_detail_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        stats = db.get_stats()
        await event.respond(
            "📊 <b>ДЕТАЛЬНАЯ СТАТИСТИКА</b>\n\n"
            f"👥 Всего пользователей: {stats['users']}\n"
            f"📱 Аккаунтов в наличии: {stats['active']}\n"
            f"🔴 Продано аккаунтов: {stats['sold']}\n"
            f"📦 Всего заказов: {stats['orders']}\n"
            f"📦 Заказов сегодня: {stats['today_orders']}\n"
            f"💰 Общая выручка: {stats['revenue']} ★\n"
            f"💰 Выручка сегодня: {stats['today_revenue']} ★",
            parse_mode='html'
        )
    
    @bot_client.on(events.NewMessage(pattern='/users'))
    async def users_list_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        users = db.get_all_users(limit=50)
        if not users:
            await event.respond("👥 Нет пользователей")
            return
        text = "👥 <b>ПОЛЬЗОВАТЕЛИ</b>\n\n"
        for u in users:
            text += f"🆔 {u['user_id']} | @{u['username'] or 'нет'} | {u['balance']} ★ | {u['total_bought']} покупок\n"
        await event.respond(text, parse_mode='html')
    
    @bot_client.on(events.NewMessage(pattern='/user (\\d+)'))
    async def user_info_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        user_id = int(event.pattern_match.group(1))
        user = db.get_user(user_id)
        if not user:
            await event.respond(f"❌ Пользователь {user_id} не найден")
            return
        orders = db.get_user_orders(user_id, limit=10)
        orders_text = ""
        for o in orders[:5]:
            orders_text += f"  🆔 {o['order_id']} | {o['amount']} ★ | {o['created_at'][:10]}\n"
        
        await event.respond(
            f"👤 <b>ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ</b>\n\n"
            f"🆔 ID: {user['user_id']}\n"
            f"👤 Username: @{user['username'] or 'нет'}\n"
            f"💰 Баланс: {user['balance']} ★\n"
            f"🛒 Куплено: {user['total_bought']} шт.\n"
            f"💳 Потрачено: {user['total_spent']} ★\n"
            f"📅 Регистрация: {user['created_at'][:16]}\n\n"
            f"📦 <b>Последние заказы:</b>\n{orders_text}",
            parse_mode='html'
        )
    
    @bot_client.on(events.NewMessage(pattern='/add_balance (\\d+) (\\d+)'))
    async def add_balance_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        user_id = int(event.pattern_match.group(1))
        amount = int(event.pattern_match.group(2))
        db.add_balance(user_id, amount, event.sender_id)
        await event.respond(f"✅ Пользователю {user_id} добавлено {amount} ★")
        await bot_client.send_message(user_id, f"💰 Ваш баланс пополнен на {amount} звезд!")
    
    @bot_client.on(events.NewMessage(pattern='/sub_balance (\\d+) (\\d+)'))
    async def sub_balance_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        user_id = int(event.pattern_match.group(1))
        amount = int(event.pattern_match.group(2))
        if db.subtract_balance(user_id, amount, event.sender_id):
            await event.respond(f"✅ С пользователя {user_id} списано {amount} ★")
            await bot_client.send_message(user_id, f"💰 С вашего баланса списано {amount} звезд!")
        else:
            await event.respond(f"❌ Недостаточно средств у пользователя {user_id}")
    
    @bot_client.on(events.NewMessage(pattern='/accounts'))
    async def accounts_list_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        accounts = db.get_all_accounts()
        if not accounts:
            await event.respond("📭 Нет аккаунтов")
            return
        
        by_country = db.get_accounts_by_country()
        text = "📋 <b>АККАУНТЫ ПО СТРАНАМ</b>\n\n"
        for c in by_country:
            text += f"🌍 {c['country']}: {c['count']} шт. от {c['min_price']} ★\n"
        
        text += f"\n📱 <b>Всего аккаунтов:</b> {len(accounts)}\n"
        text += f"🟢 <b>В наличии:</b> {len([a for a in accounts if a['status'] == 'available'])}\n"
        text += f"🔴 <b>Продано:</b> {len([a for a in accounts if a['status'] == 'sold'])}"
        await event.respond(text, parse_mode='html')
    
    @bot_client.on(events.NewMessage(pattern='/account (\\d+)'))
    async def account_info_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        account_id = int(event.pattern_match.group(1))
        acc = db.get_account_by_id(account_id)
        if not acc:
            await event.respond(f"❌ Аккаунт #{account_id} не найден")
            return
        await event.respond(
            f"📱 <b>АККАУНТ #{account_id}</b>\n\n"
            f"📞 Телефон: {acc['phone']}\n"
            f"🌍 Страна: {acc['country']}\n"
            f"⚡ DC: {acc['dc']}\n"
            f"💰 Цена: {acc['price']} ★\n"
            f"📊 Статус: {'🟢 В наличии' if acc['status'] == 'available' else '🔴 Продан'}\n"
            f"📅 Добавлен: {acc['created_at'][:16]}\n"
            f"🆔 Session: <code>{acc['session_string'][:50]}...</code>",
            parse_mode='html'
        )
    
    @bot_client.on(events.NewMessage(pattern='/add_account (.+) (.+) (.+) (\\d+)'))
    async def add_account_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        session = event.pattern_match.group(1)
        phone = event.pattern_match.group(2)
        country = event.pattern_match.group(3)
        price = int(event.pattern_match.group(4))
        account_id = db.add_account(session, phone, country, price, admin_id=event.sender_id)
        await event.respond(f"✅ Аккаунт #{account_id} добавлен ({country}, {price} ★)")
    
    @bot_client.on(events.NewMessage(pattern='/del_account (\\d+)'))
    async def delete_account_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        account_id = int(event.pattern_match.group(1))
        if db.delete_account(account_id, event.sender_id):
            await event.respond(f"✅ Аккаунт #{account_id} удалён")
        else:
            await event.respond(f"❌ Аккаунт #{account_id} не найден")
    
    @bot_client.on(events.NewMessage(pattern='/price (\\d+) (\\d+)'))
    async def update_price_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        account_id = int(event.pattern_match.group(1))
        new_price = int(event.pattern_match.group(2))
        db.update_account_price(account_id, new_price, event.sender_id)
        await event.respond(f"✅ Цена аккаунта #{account_id} изменена на {new_price} ★")
    
    @bot_client.on(events.NewMessage(pattern='/orders'))
    async def all_orders_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        orders = db.get_all_orders(limit=50)
        if not orders:
            await event.respond("📭 Нет заказов")
            return
        text = "📦 <b>ПОСЛЕДНИЕ ЗАКАЗЫ</b>\n\n"
        for o in orders:
            text += f"🆔 {o['order_id'][:12]}... | {o['amount']} ★ | {o['created_at'][:16]}\n"
        await event.respond(text, parse_mode='html')
    
    @bot_client.on(events.NewMessage(pattern='/top'))
    async def top_users_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        tops = db.get_top_spenders(10)
        text = "🏆 <b>ТОП ПОТРАТИЛОВ</b>\n\n"
        for i, u in enumerate(tops, 1):
            text += f"{i}. 🆔 {u['user_id']} | @{u['username'] or 'нет'} | {u['total_spent']} ★\n"
        await event.respond(text, parse_mode='html')
    
    @bot_client.on(events.NewMessage(pattern='/mailing (.+)'))
    async def mailing_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        text = event.pattern_match.group(1)
        await event.respond("⏳ Запуск рассылки...")
        
        users = db.get_all_users(limit=10000)
        sent = 0
        failed = 0
        
        for user in users:
            try:
                await bot_client.send_message(
                    user['user_id'],
                    f"📢 <b>РАССЫЛКА ОТ АДМИНИСТРАЦИИ</b>\n\n{text}",
                    parse_mode='html'
                )
                sent += 1
                await asyncio.sleep(0.05)
            except:
                failed += 1
        
        mailing_id = db.add_mailing(text)
        db.update_mailing(mailing_id, sent, failed, 'completed')
        await event.respond(f"✅ Рассылка завершена!\n📨 Отправлено: {sent}\n❌ Ошибок: {failed}")
    
    @bot_client.on(events.NewMessage(pattern='/set_markup (\\d+)'))
    async def set_markup_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        markup = event.pattern_match.group(1)
        db.set_setting('markup', markup, event.sender_id)
        await event.respond(f"✅ Наценка установлена: {markup}%")
    
    @bot_client.on(events.NewMessage(pattern='/set_stars_rate (\\d+\\.?\\d*)'))
    async def set_stars_rate_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        rate = event.pattern_match.group(1)
        db.set_setting('stars_rate', rate, event.sender_id)
        await event.respond(f"✅ Курс Stars установлен: 1⭐ = {rate} ₽")
    
    @bot_client.on(events.NewMessage(pattern='/maintenance (on|off)'))
    async def maintenance_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        mode = event.pattern_match.group(1)
        db.set_setting('maintenance', '1' if mode == 'on' else '0', event.sender_id)
        await event.respond(f"🔧 Режим техобслуживания: {'ВКЛЮЧЁН' if mode == 'on' else 'ВЫКЛЮЧЕН'}")
    
    @bot_client.on(events.NewMessage(pattern='/backup'))
    async def backup_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        backup_file = os.path.join(BACKUP_DIR, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
        import shutil
        shutil.copy("shop.db", backup_file)
        await event.respond(f"✅ Бэкап создан: {backup_file}")
    
    @bot_client.on(events.NewMessage(pattern='/export_users'))
    async def export_users_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        csv_data = db.export_users_csv()
        await event.respond(file=io.BytesIO(csv_data.encode('utf-8')), force_document=True, file_name="users.csv")
    
    @bot_client.on(events.NewMessage(pattern='/export_accounts'))
    async def export_accounts_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        csv_data = db.export_accounts_csv()
        await event.respond(file=io.BytesIO(csv_data.encode('utf-8')), force_document=True, file_name="accounts.csv")
    
    @bot_client.on(events.NewMessage(pattern='/logs'))
    async def logs_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        logs = db.get_admin_logs(30)
        if not logs:
            await event.respond("📭 Нет логов")
            return
        text = "📋 <b>ПОСЛЕДНИЕ ДЕЙСТВИЯ</b>\n\n"
        for log in logs:
            text += f"👤 Админ: {log['admin_id']}\n📝 {log['action']}: {log['target']}\n📅 {log['created_at'][:16]}\n\n"
        await event.respond(text, parse_mode='html')
    
    @bot_client.on(events.NewMessage(pattern='/settings'))
    async def settings_handler(event):
        if event.sender_id not in ADMIN_IDS:
            return
        markup = db.get_setting('markup', '20')
        stars_rate = db.get_setting('stars_rate', '1')
        maintenance = db.get_setting('maintenance', '0')
        await event.respond(
            f"⚙️ <b>ТЕКУЩИЕ НАСТРОЙКИ</b>\n\n"
            f"💰 Наценка: {markup}%\n"
            f"⭐ Курс Stars: 1★ = {stars_rate} ₽\n"
            f"🔧 Техобслуживание: {'ВКЛ' if maintenance == '1' else 'ВЫКЛ'}",
            parse_mode='html'
        )
    
    print("🤖 Бот запущен!")
    await bot_client.run_until_disconnected()

# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    print("=" * 50)
    print("OxatovAccount Bot v3.0")
    print("=" * 50)
    print(f"Mini App URL: {MINIAPP_URL}")
    print("=" * 50)
    print("АДМИН-КОМАНДЫ:")
    print("  /admin - главная панель")
    print("  /stats - статистика")
    print("  /users - список пользователей")
    print("  /add_balance <id> <sum> - добавить баланс")
    print("  /sub_balance <id> <sum> - списать баланс")
    print("  /accounts - список аккаунтов")
    print("  /add_account <session> <phone> <country> <price> - добавить")
    print("  /del_account <id> - удалить аккаунт")
    print("  /price <id> <new_price> - изменить цену")
    print("  /orders - все заказы")
    print("  /mailing <текст> - рассылка")
    print("  /backup - бэкап БД")
    print("  /export_users - выгрузить пользователей")
    print("  /export_accounts - выгрузить аккаунты")
    print("  /logs - логи действий")
    print("=" * 50)
    
    asyncio.run(start_bot())