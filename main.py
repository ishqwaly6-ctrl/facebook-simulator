import sqlite3
import hashlib
import json
import requests
from datetime import datetime
import secrets
import string
import os
from pathlib import Path
import random

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
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_plain TEXT NOT NULL,
                facebook_id TEXT,
                cookie TEXT,
                token TEXT UNIQUE,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_token(self, length=32):
        """توليد توكن عشوائي"""
        characters = string.ascii_letters + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    def generate_password(self, length=12):
        """توليد كلمة مرور عشوائية قوية"""
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(characters) for _ in range(length))
    
    def generate_facebook_id(self):
        """توليد معرف فيسبوك عشوائي"""
        return str(random.randint(100000000000000, 999999999999999))
    
    def generate_cookie(self):
        """توليد كوكي عشوائي محاكاة"""
        parts = []
        
        # داتا تشبه الواقع
        cookie_names = [
            "datr", "sb", "ps_l", "ps_n", "c_user", "xs", "fr", "presence"
        ]
        
        for name in cookie_names:
            # توليد قيمة عشوائية
            value = ''.join(secrets.choice(string.ascii_letters + string.digits + "-_.") for _ in range(random.randint(20, 40)))
            parts.append(f"{name}={value}")
        
        return "; ".join(parts)
    
    def generate_username(self, first_name, last_name):
        """توليد اسم مستخدم من الاسم"""
        base = f"{first_name.lower()}_{last_name.lower()}"
        suffix = random.randint(100, 9999)
        return f"{base}_{suffix}"
    
    def generate_email(self, username):
        """توليد بريد إلكتروني"""
        domains = [
            "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
            "guerrillamail.com", "mailinator.com", "temp-mail.org"
        ]
        domain = random.choice(domains)
        return f"{username}@{domain}"
    
    def generate_random_names(self):
        """توليد أسماء عشوائية"""
        first_names = [
            "أحمد", "محمد", "علي", "فاطمة", "نور", "ليلى", "سارة", "مريم",
            "حسن", "إبراهيم", "خالد", "عمر", "زيد", "رشا", "هند", "نجلاء"
        ]
        
        last_names = [
            "محمود", "السالم", "علي", "أحمد", "حسن", "إبراهيم", "خالد",
            "عمر", "زيدان", "الأحمر", "الأسود", "الأزرق", "السيد", "العامري"
        ]
        
        return random.choice(first_names), random.choice(last_names)
    
    def send_to_telegram(self, message):
        """إرسال رسالة إلى بوت التليجرام"""
        if not self.telegram_token or not self.telegram_chat_id:
            return {"status": "⚠️"}
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, data=data, timeout=5)
            
            if response.status_code == 200:
                return {"status": "✅"}
            else:
                return {"status": "❌"}
        except Exception as e:
            return {"status": "❌"}
    
    def create_account(self, username, first_name, last_name, email, password, facebook_id, cookie):
        """إنشاء حساب جديد"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            token = self.generate_token()
            
            cursor.execute('''
                INSERT INTO accounts 
                (username, email, password_plain, facebook_id, cookie, token, first_name, last_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, password, facebook_id, cookie, token, first_name, last_name))
            
            conn.commit()
            account_id = cursor.lastrowid
            conn.close()
            
            # إرسال إلى التليجرام
            telegram_message = f"""
✅ <b>حساب فيسبوك جديد تم إنشاؤه!</b>

👤 <b>الاسم:</b> {first_name} {last_name}
🔤 <b>اسم المستخدم:</b> <code>{username}</code>
📧 <b>البريد:</b> <code>{email}</code>
🔐 <b>كلمة المرور:</b> <code>{password}</code>
🆔 <b>معرف الفيسبوك:</b> <code>{facebook_id}</code>
🎫 <b>التوكن:</b> <code>{token}</code>
⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            self.send_to_telegram(telegram_message)
            
            return {
                "status": "✅",
                "account_id": account_id,
                "username": username,
                "email": email,
                "password": password,
                "facebook_id": facebook_id,
                "token": token,
                "first_name": first_name,
                "last_name": last_name
            }
        
        except sqlite3.IntegrityError as e:
            conn.close()
            return None
    
    def create_multiple_accounts(self, count):
        """إنشاء عدة حسابات تلقائياً"""
        accounts = []
        
        for i in range(count):
            # توليد البيانات
            first_name, last_name = self.generate_random_names()
            username = self.generate_username(first_name, last_name)
            email = self.generate_email(username)
            password = self.generate_password()
            facebook_id = self.generate_facebook_id()
            cookie = self.generate_cookie()
            
            # إنشاء الحساب
            result = self.create_account(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password,
                facebook_id=facebook_id,
                cookie=cookie
            )
            
            if result:
                accounts.append(result)
        
        return accounts
    
    def get_all_accounts(self):
        """الحصول على جميع الحسابات"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, first_name, last_name, facebook_id, password_plain, token, created_at
            FROM accounts ORDER BY created_at DESC
        ''')
        
        accounts = cursor.fetchall()
        conn.close()
        
        return accounts
    
    def export_accounts(self, filename="accounts_export.json"):
        """تصدير جميع الحسابات"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, first_name, last_name, facebook_id, password_plain, token, cookie, created_at
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
                "first_name": acc[3],
                "last_name": acc[4],
                "facebook_id": acc[5],
                "password": acc[6],
                "token": acc[7],
                "cookie": acc[8],
                "created_at": acc[9]
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "✅",
            "file": filename,
            "count": len(data)
        }


class InteractiveCLI:
    def __init__(self, telegram_token, telegram_chat_id):
        self.fb = FacebookSimulator(telegram_token=telegram_token, telegram_chat_id=telegram_chat_id)
    
    def clear_screen(self):
        """مسح شاشة الكونسول"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def print_header(self, title):
        """طباعة رأس الصفحة"""
        print("\n" + "=" * 70)
        print(f"🔵 {title}".center(70))
        print("=" * 70)
    
    def print_menu(self):
        """طباعة القائمة الرئيسية"""
        self.print_header("القائمة الرئيسية")
        print("""
1️⃣  إنشاء حسابات تلقائياً
2️⃣  عرض جميع الحسابات
3️⃣  تصدير جميع الحسابات
4️⃣  عدد الحسابات الموجودة
5️⃣  خروج

        """)
    
    def create_accounts_auto(self):
        """إنشاء حسابات تلقائياً"""
        self.print_header("إنشاء حسابات تلقائياً")
        
        try:
            count = int(input("\n📱 كم حساب تريد إنشاء؟ (أدخل رقم): ").strip())
            
            if count <= 0:
                print("❌ يج�� إدخال رقم أكبر من صفر!")
                input("اضغط Enter للمتابعة...")
                return
            
            if count > 100:
                confirm = input(f"⚠️  أنت تحاول إنشاء {count} حساب! هل أنت متأكد؟ (نعم/لا): ").strip().lower()
                if confirm not in ['نعم', 'yes', 'y']:
                    print("❌ تم الإلغاء")
                    input("اضغط Enter للمتابعة...")
                    return
            
            print(f"\n⏳ جاري إنشاء {count} حساب...")
            
            accounts = self.fb.create_multiple_accounts(count)
            
            print(f"\n✅ تم إنشاء {len(accounts)} حساب بنجاح!\n")
            
            # عرض الحسابات المنشأة
            for i, acc in enumerate(accounts, 1):
                print(f"{i}. 👤 {acc['first_name']} {acc['last_name']}")
                print(f"   🔤 المستخدم: {acc['username']}")
                print(f"   📧 البريد: {acc['email']}")
                print(f"   🔐 الباسورد: {acc['password']}")
                print()
            
            print("✅ تم إرسال جميع البيانات إلى التليجرام!")
        
        except ValueError:
            print("❌ يجب إدخال رقم صحيح!")
        
        input("اضغط Enter للمتابعة...")
    
    def show_all_accounts(self):
        """عرض جميع الحسابات"""
        self.print_header("جميع الحسابات")
        
        accounts = self.fb.get_all_accounts()
        
        if not accounts:
            print("\n⚠️ لا توجد حسابات بعد!")
        else:
            print(f"\n📊 إجمالي الحسابات: {len(accounts)}\n")
            
            for i, acc in enumerate(accounts, 1):
                print(f"{i}. 🆔 {acc[0]}")
                print(f"   👤 الاسم: {acc[3]} {acc[4]}")
                print(f"   🔤 المستخدم: {acc[1]}")
                print(f"   📧 البريد: {acc[2]}")
                print(f"   📱 معرف الفيسبوك: {acc[5]}")
                print(f"   🔐 الباسورد: {acc[6]}")
                print(f"   🎫 التوكن: {acc[7][:20]}...")
                print()
        
        input("اضغط Enter للمتابعة...")
    
    def export_accounts_interactive(self):
        """تصدير الحسابات"""
        self.print_header("تصدير جميع الحسابات")
        
        print("\n⏳ جاري تصدير البيانات...")
        result = self.fb.export_accounts()
        
        if result['status'] == "✅":
            print(f"\n✅ تم التصدير بنجاح!")
            print(f"📁 الملف: {result['file']}")
            print(f"📊 عدد الحسابات: {result['count']}")
        else:
            print(f"\n❌ خطأ في التصدير")
        
        input("\nاضغط Enter للمتابعة...")
    
    def show_account_count(self):
        """عرض عدد الحسابات"""
        self.print_header("عدد الحسابات")
        
        accounts = self.fb.get_all_accounts()
        count = len(accounts)
        
        print(f"\n📊 عدد الحسابات المنشأة: <b>{count}</b>")
        
        if count > 0:
            print(f"\n📅 أحدث حساب: {accounts[0][8]}")
        
        input("\nاضغط Enter للمتابعة...")
    
    def run(self):
        """تشغيل البرنامج التفاعلي"""
        while True:
            self.clear_screen()
            self.print_menu()
            
            choice = input("اختر رقم الخيار: ").strip()
            
            if choice == '1':
                self.create_accounts_auto()
            elif choice == '2':
                self.show_all_accounts()
            elif choice == '3':
                self.export_accounts_interactive()
            elif choice == '4':
                self.show_account_count()
            elif choice == '5':
                print("\n👋 شكراً لاستخدام البرنامج! وداعاً...")
                break
            else:
                print("❌ اختيار غير صحيح! حاول مرة أخرى")
                input("اضغط Enter للمتابعة...")


if __name__ == "__main__":
    # بيانات التليجرام
    TELEGRAM_TOKEN = "8321731547:AAEOGHm4fLgb7vkTzF6EBJ2Yy-SLYsKceas"
    TELEGRAM_CHAT_ID = "5749281880"
    
    # بدء البرنامج
    cli = InteractiveCLI(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    cli.run()
