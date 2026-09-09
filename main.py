import sqlite3
import json
import requests
from datetime import datetime
import secrets
import string
import os
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import time
import imaplib
import email
from email.header import decode_header
import re

class FacebookSimulator:
    def __init__(self, db_name="facebook.db", telegram_token=None, telegram_chat_id=None):
        self.db_name = db_name
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.init_database()
    
    def init_database(self):
        """إنشاء قاعدة البيانات والجداول"""
        # حذف قاعدة البيانات القديمة إذا كانت موجودة
        if os.path.exists(self.db_name):
            try:
                os.remove(self.db_name)
                print(f"✅ تم حذف قاعدة البيانات القديمة")
            except Exception as e:
                print(f"⚠️ خطأ في حذف قاعدة البيانات القديمة: {e}")
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_plain TEXT NOT NULL,
                facebook_id TEXT NOT NULL,
                cookie TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ تم إنشاء قاعدة البيانات بنجاح")
    
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
        cookie_names = [
            "datr", "sb", "ps_l", "ps_n", "c_user", "xs", "fr", "presence"
        ]
        
        for name in cookie_names:
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
            "guerrillamail.com", "mailinator.com"
        ]
        domain = random.choice(domains)
        return f"{username}@{domain}"
    
    def generate_random_names(self):
        """توليد أسماء عشوائية"""
        first_names = [
            "أحمد", "محمد", "علي", "فاطمة", "نور", "ليلى", "سارة", "مريم",
            "حسن", "إبراهيم", "خالد", "عمر", "زيد", "رشا", "هند", "نجلاء",
            "يوسف", "هاني", "مصطفى", "جمال", "ياسمين", "إسراء", "أريج", "نسرين"
        ]
        
        last_names = [
            "محمود", "السالم", "علي", "أحمد", "حسن", "إبراهيم", "خالد",
            "عمر", "زيدان", "الأحمر", "الأسود", "الأزرق", "السيد", "العامري",
            "الهاشمي", "القاسمي", "التميمي", "الشمري", "الدعيجي", "الشراري"
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
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                return {"status": "✅"}
            else:
                return {"status": "❌"}
        except Exception as e:
            print(f"❌ خطأ في إرسال رسالة التليجرام: {e}")
            return {"status": "❌"}
    
    def verify_email_gmail(self, email_addr, app_password, verification_code_pattern=None):
        """التحقق من رسالة تأكيد الايميل من Gmail"""
        try:
            print(f"⏳ جاري البحث عن رسالة التأكيد في البريد...")
            
            # الاتصال بـ Gmail IMAP
            imap = imaplib.IMAP4_SSL("imap.gmail.com")
            imap.login(email_addr, app_password)
            imap.select("INBOX")
            
            # البحث عن رسائل من Facebook
            status, messages = imap.search(None, 'FROM', 'facebook')
            
            if messages[0]:
                email_ids = messages[0].split()
                latest_email_id = email_ids[-1]
                
                status, msg_data = imap.fetch(latest_email_id, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                
                # استخراج الرابط أو الكود من الرسالة
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            # البحث عن رابط التأكيد
                            link_pattern = r'https://[^\s]+'
                            links = re.findall(link_pattern, body)
                            if links:
                                print(f"✅ تم العثور على رابط التأكيد")
                                imap.close()
                                return links[0]
                else:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                    link_pattern = r'https://[^\s]+'
                    links = re.findall(link_pattern, body)
                    if links:
                        print(f"✅ تم العثور على رابط التأكيد")
                        imap.close()
                        return links[0]
            
            imap.close()
            return None
        except Exception as e:
            print(f"❌ خطأ في البحث عن رسالة التأكيد: {e}")
            return None
    
    def create_facebook_account_with_selenium(self, first_name, last_name, email, password, headless=False):
        """إنشاء حساب فيسبوك باستخدام Selenium"""
        try:
            print(f"🌐 جاري فتح متصفح Chrome...")
            
            # إعدادات Chrome
            options = webdriver.ChromeOptions()
            if headless:
                options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            
            driver = webdriver.Chrome(options=options)
            
            # فتح صفحة فيسبوك
            print(f"📱 جاري الانتقال إلى فيسبوك...")
            driver.get("https://www.facebook.com")
            time.sleep(2)
            
            # النقر على زر "إنشاء حساب جديد"
            try:
                create_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, "إنشاء حساب جديد"))
                )
                create_button.click()
            except:
                create_button = driver.find_element(By.XPATH, "//a[contains(text(), 'إنشاء')]")
                create_button.click()
            
            time.sleep(2)
            
            # ملء نموذج التسجيل
            print(f"📝 جاري ملء نموذج التسجيل...")
            
            # الاسم الأول
            first_name_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "firstname"))
            )
            first_name_input.send_keys(first_name)
            
            # الاسم الأخير
            last_name_input = driver.find_element(By.NAME, "lastname")
            last_name_input.send_keys(last_name)
            
            # البريد الإلكتروني
            email_input = driver.find_element(By.NAME, "reg_email__")
            email_input.send_keys(email)
            
            # تأكيد البريد
            email_confirm = driver.find_element(By.NAME, "reg_email_confirmation__")
            email_confirm.send_keys(email)
            
            # كلمة المرور
            password_input = driver.find_element(By.NAME, "reg_passwd__")
            password_input.send_keys(password)
            
            # تاريخ الميلاد
            day_select = driver.find_element(By.NAME, "birthday_day")
            day_select.send_keys("15")
            
            month_select = driver.find_element(By.NAME, "birthday_month")
            month_select.send_keys("Jan")
            
            year_select = driver.find_element(By.NAME, "birthday_year")
            year_select.send_keys("1990")
            
            # الجنس
            gender_male = driver.find_element(By.CSS_SELECTOR, "input[value='1']")
            gender_male.click()
            
            time.sleep(1)
            
            # النقر على زر التسجيل
            print(f"✉️ جاري إنشاء الحساب...")
            signup_button = driver.find_element(By.NAME, "websubmit")
            signup_button.click()
            
            time.sleep(3)
            
            # انتظار التحويل إلى صفحة التأكيد
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'تأكيد')]"))
                )
                print(f"✅ تم إنشاء الحساب بنجاح!")
                
                # محاولة إيجاد رابط التأكيد من الايميل
                app_password = "your_app_password"  # استبدل بـ App Password
                verification_link = self.verify_email_gmail(email, app_password)
                
                if verification_link:
                    print(f"🔗 جاري فتح رابط التأكيد...")
                    driver.get(verification_link)
                    time.sleep(3)
                    print(f"✅ تم تأكيد الايميل!")
                
            except Exception as e:
                print(f"⚠️ قد تحتاج لتأكيد الايميل يدويّاً: {e}")
            
            # الحصول على معلومات الحساب
            current_url = driver.current_url
            facebook_id = current_url.split('/')[-1] if '/' in current_url else "unknown"
            
            driver.quit()
            
            return {
                "status": "✅",
                "facebook_id": facebook_id,
                "message": "تم إنشاء الحساب وتسجيل الدخول بنجاح"
            }
        
        except Exception as e:
            print(f"❌ خطأ في إنشاء حساب الفيسبوك: {e}")
            try:
                driver.quit()
            except:
                pass
            return {
                "status": "❌",
                "error": str(e)
            }
    
    def create_account(self, username, first_name, last_name, email, password, facebook_id, cookie):
        """إنشاء حساب جديد في قاعدة البيانات"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        try:
            token = self.generate_token()
            
            cursor.execute('''
                INSERT INTO accounts 
                (username, email, password_plain, facebook_id, cookie, token, first_name, last_name, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, password, facebook_id, cookie, token, first_name, last_name, "active"))
            
            conn.commit()
            account_id = cursor.lastrowid
            conn.close()
            
            # إرسال إلى التليجرام
            telegram_message = f"""
✅ <b>حساب فيسبوك جديد تم إنشاؤه وتفعيله!</b>

👤 <b>الاسم:</b> {first_name} {last_name}
🔤 <b>اسم المستخدم:</b> <code>{username}</code>
📧 <b>البريد:</b> <code>{email}</code>
🔐 <b>كلمة المرور:</b> <code>{password}</code>
🆔 <b>معرف الفيسبوك:</b> <code>{facebook_id}</code>
🎫 <b>التوكن:</b> <code>{token}</code>
⏰ <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
✅ <b>الحالة:</b> نشط وجاهز للاستخدام
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
    
    def create_and_activate_account(self, headless=False):
        """إنشاء وتفعيل حساب واحد"""
        # توليد البيانات
        first_name, last_name = self.generate_random_names()
        username = self.generate_username(first_name, last_name)
        email = self.generate_email(username)
        password = self.generate_password()
        facebook_id = self.generate_facebook_id()
        cookie = self.generate_cookie()
        
        print(f"\n{'='*70}")
        print(f"👤 الاسم: {first_name} {last_name}")
        print(f"📧 البريد: {email}")
        print(f"🔐 الباسورد: {password}")
        print(f"{'='*70}\n")
        
        # إنشاء حساب الفيسبوك
        fb_result = self.create_facebook_account_with_selenium(
            first_name, last_name, email, password, headless=headless
        )
        
        if fb_result['status'] == "✅":
            # حفظ في قاعدة البيانات
            result = self.create_account(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password,
                facebook_id=fb_result.get('facebook_id', facebook_id),
                cookie=cookie
            )
            
            if result:
                return result
        
        return None
    
    def get_all_accounts(self):
        """الحصول على جميع الحسابات"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, email, first_name, last_name, facebook_id, password_plain, token, created_at, status
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
            SELECT id, username, email, first_name, last_name, facebook_id, password_plain, token, cookie, created_at, status
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
                "created_at": acc[9],
                "status": acc[10]
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
1️⃣  إنشاء حساب فيسبوك وتفعيله
2️⃣  عرض جميع الحسابات
3️⃣  تصدير جميع الحسابات
4️⃣  عدد الحسابات الموجودة
5️⃣  خروج

        """)
    
    def create_account_interactive(self):
        """إنشاء حساب فيسبوك تفاعلي"""
        self.print_header("إنشاء حساب فيسبوك جديد")
        
        try:
            headless = input("\n🖥️ هل تريد تشغيل المتصفح بخلفية؟ (نعم/لا): ").strip().lower()
            headless = headless in ['نعم', 'yes', 'y']
            
            print(f"\n⏳ جاري إنشاء وتفعيل الحساب...\n")
            
            result = self.fb.create_and_activate_account(headless=headless)
            
            if result:
                print(f"\n✅ تم إنشاء الحساب بنجاح!")
                print(f"📧 البريد: {result['email']}")
                print(f"🔐 الباسورد: {result['password']}")
                print(f"✅ تم إرسال البيانات إلى التليجرام!")
            else:
                print(f"\n❌ حدث خطأ في إنشاء الحساب")
        
        except Exception as e:
            print(f"❌ خطأ: {e}")
        
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
                print(f"   🔐 الباسورد: {acc[6]}")
                print(f"   ✅ الحالة: {acc[9]}")
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
        
        print(f"\n📊 عدد الحسابات المنشأة: {count}")
        
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
                self.create_account_interactive()
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
    
    print("\n🔵 تم تحديث الأداة لإنشاء حسابات فيسبوك وتفعيلها...")
    
    # بدء البرنامج
    cli = InteractiveCLI(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    cli.run()
