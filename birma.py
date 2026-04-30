import streamlit as st
import pandas as pd
import os
import requests
import urllib.parse
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection
import plotly.graph_objects as go
import plotly.express as px
import math
import time
import json
import glob
import base64

# ============================================================================
# 1. إعدادات الصفحة
# ============================================================================
st.set_page_config(page_title="BIRMA Integrated System", page_icon="🏭", layout="wide")

# ============================================================================
# 2. نظام حفظ الدخول على الجهاز فقط (localStorage)
# ============================================================================
def save_credentials_local(username, password, remember=True):
    """حفظ بيانات الدخول في localStorage (على الجهاز فقط، وليس على السيرفر)"""
    if remember:
        data = {
            "u": username,
            "p": password,
            "t": datetime.now().isoformat()
        }
        encoded = base64.b64encode(json.dumps(data).encode()).decode()
        
        st.markdown(f"""
            <script>
                localStorage.setItem('birma_creds', '{encoded}');
                localStorage.setItem('birma_remember', 'true');
            </script>
        """, unsafe_allow_html=True)
        return True
    return False

def load_credentials_local():
    """تحميل بيانات الدخول من localStorage"""
    st.markdown("""
        <script>
            var creds = localStorage.getItem('birma_creds');
            var url = new URL(window.location.href);
            if (creds && !url.searchParams.has('creds')) {
                url.searchParams.set('creds', encodeURIComponent(creds));
                window.location.href = url.toString();
            }
        </script>
    """, unsafe_allow_html=True)
    
    if 'creds' in st.query_params:
        try:
            encoded = st.query_params['creds']
            decoded = base64.b64decode(encoded).decode()
            data = json.loads(decoded)
            return data.get('u'), data.get('p'), True
        except:
            return None, None, False
    return None, None, False

def clear_credentials_local():
    """مسح بيانات الدخول من localStorage"""
    st.markdown("""
        <script>
            localStorage.removeItem('birma_creds');
            localStorage.removeItem('birma_remember');
            var url = new URL(window.location.href);
            url.searchParams.delete('creds');
            window.location.href = url.toString();
        </script>
    """, unsafe_allow_html=True)

# ============================================================================
# 3. دالة عرض التاريخ
# ============================================================================
def show_current_date():
    today = datetime.now()
    
    arabic_days = {
        "Monday": "الإثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء",
        "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"
    }
    arabic_months = {
        "January": "يناير", "February": "فبراير", "March": "مارس", "April": "أبريل",
        "May": "مايو", "June": "يونيو", "July": "يوليو", "August": "أغسطس",
        "September": "سبتمبر", "October": "أكتوبر", "November": "نوفمبر", "December": "ديسمبر"
    }
    
    bengali_days = {
        "Monday": "সোমবার", "Tuesday": "মঙ্গলবার", "Wednesday": "বুধবার",
        "Thursday": "বৃহস্পতিবার", "Friday": "শুক্রবার", "Saturday": "শনিবার", "Sunday": "রবিবার"
    }
    bengali_months = {
        "January": "জানুয়ারি", "February": "ফেব্রুয়ারি", "March": "মার্চ", "April": "এপ্রিল",
        "May": "মে", "June": "জুন", "July": "জুলাই", "August": "আগস্ট",
        "September": "সেপ্টেম্বর", "October": "অক্টোবর", "November": "নভেম্বর", "December": "ডিসেম্বর"
    }
    
    lang = st.session_state.get('lang', 'ar')
    day_name = today.strftime("%A")
    month_name = today.strftime("%B")
    
    if lang == "ar":
        day = arabic_days.get(day_name, day_name)
        month = arabic_months.get(month_name, month_name)
        date_str = f"{day}، {today.day} {month} {today.year}"
    elif lang == "bn":
        day = bengali_days.get(day_name, day_name)
        month = bengali_months.get(month_name, month_name)
        date_str = f"{day}, {today.day} {month} {today.year}"
    else:
        date_str = today.strftime("%A, %B %d, %Y")
    
    st.markdown(f"<div style='text-align: left; direction: ltr; font-size: 14px; color: gray; margin-bottom: 10px;'>📅 {date_str}</div>", unsafe_allow_html=True)

# ============================================================================
# 4. تهيئة حالة الجلسة
# ============================================================================
if 'lang' not in st.session_state:
    st.session_state.lang = 'ar'
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

# ============================================================================
# 5. نظام المستخدمين والأدوار
# ============================================================================
USERS = {
    "admin": {"password": "admin123", "role": "admin", "name": "مدير النظام", "icon": "👑"},
    "supervisor": {"password": "sup456", "role": "supervisor", "name": "مشرف إنتاج", "icon": "👔"},
    "technician": {"password": "tech789", "role": "technician", "name": "فني صيانة", "icon": "🔧"},
    "storekeeper": {"password": "store001", "role": "storekeeper", "name": "أمين مخزن", "icon": "📦"},
    "quality": {"password": "quality123", "role": "quality", "name": "مراقب جودة", "icon": "🔍"}
}

ROLE_PERMISSIONS = {
    "admin": ["🏠 Dashboard", "📈 Production", "🔧 Maintenance", "📊 Records", "📦 Raw Materials", "🏭 Finished Goods", "👥 Users", "⚙️ Settings"],
    "supervisor": ["🏠 Dashboard", "📈 Production", "🔧 Maintenance", "📊 Records", "📦 Raw Materials", "🏭 Finished Goods"],
    "technician": ["🏠 Dashboard", "🔧 Maintenance", "📊 Records"],
    "storekeeper": ["🏠 Dashboard", "📦 Raw Materials", "🏭 Finished Goods", "📊 Records"],
    "quality": ["🏠 Dashboard", "📊 Records", "📈 Production"]
}

# ============================================================================
# 6. نظام اللغات
# ============================================================================
LANG = {
    "ar": {
        "designer": "م/ السيد عون",
        "login_title": "تسجيل الدخول",
        "username": "اسم المستخدم",
        "password": "كلمة المرور",
        "login_btn": "دخول",
        "login_error": "خطأ في اسم المستخدم أو كلمة المرور",
        "logout": "تسجيل خروج",
        "welcome": "مرحباً",
        "role": "الدور",
        "dark_mode": "الوضع الليلي",
        "dashboard": "🏠 لوحة القيادة",
        "production": "📈 إدارة الإنتاج",
        "maintenance": "🔧 مركز الصيانة",
        "records": "📊 السجلات",
        "raw_materials": "📦 المخازن (مواد خام)",
        "finished_goods": "🏭 مخزن الإنتاج التام",
        "users": "👥 المستخدمين",
        "settings": "⚙️ الإعدادات",
        "line_label": "خط العمل",
        "sup_label": "المشرف",
        "prod_label": "المنتج",
        "target_label": "الكمية",
        "preform_label": "البريفورم المستخدم",
        "raw_label": "خامة التغليف",
        "date_label": "التاريخ",
        "maint_header": "مركز الصيانة",
        "maint_types": ["صيانة دورية", "بلاغ عطل"],
        "tech_label": "الفني",
        "issue_label": "وصف العطل",
        "start_t": "بداية التوقف",
        "end_t": "نهاية الإصلاح",
        "note_label": "ملاحظات",
        "save_btn": "حفظ",
        "success_msg": "تم الحفظ بنجاح",
        "eff_title": "متوسط الكفاءة",
        "waste_title": "تحليل الهالك",
        "history_p": "سجل الإنتاج",
        "history_m": "سجل الصيانة",
        "admin_title": "لوحة التحكم - حذف السجل",
        "delete_btn": "حذف السجل المختار",
        "del_success": "تم حذف السجل بنجاح",
        "tools_label": "الأدوات:",
        "proc_label": "الإجراءات:",
        "weekend_msg": "الجمعة عطلة - لا صيانات دورية",
        "inventory_header": "إدارة المخازن",
        "current_stock": "المخزون الحالي",
        "receipt": "استلام مشتريات",
        "alerts": "تنبيهات",
        "material": "المادة",
        "quantity": "الكمية",
        "invoice": "رقم الفاتورة",
        "receipt_date": "تاريخ الاستلام",
        "register_receipt": "تسجيل الاستلام",
        "low_stock_alert": "مواد منخفضة المخزون",
        "all_good": "جميع المواد آمنة",
        "edit_stock": "تعديل الرصيد",
        "new_stock": "الرصيد الجديد",
        "update": "تحديث",
        "stock_updated": "تم تحديث الرصيد",
        "export_btn": "تصدير",
        "dashboard_title": "لوحة القيادة",
        "total_production": "إجمالي الإنتاج",
        "avg_efficiency": "متوسط الكفاءة",
        "total_waste": "إجمالي الهالك",
        "low_stock_count": "مواد خام منخفضة",
        "line1_efficiency": "كفاءة الخط الأول",
        "line2_efficiency": "كفاءة الخط الثاني",
        "smart_recommendations": "التوصيات الذكية",
        "users_title": "إدارة المستخدمين",
        "settings_title": "إعدادات النظام",
        "backup_data": "نسخ احتياطي",
        "clear_cache": "مسح الذاكرة",
        "machine_select": "اختر الماكينة",
        "task_name": "المهمة",
        "done": "تم التنفيذ",
        "no_data": "لا توجد بيانات مسجلة حتى الآن",
        "no_production": "لا توجد سجلات إنتاج",
        "no_maintenance": "لا توجد سجلات صيانة",
        "add_new_item": "إضافة صنف جديد",
        "item_id": "الرقم التعريفي",
        "item_name": "اسم المادة",
        "item_unit": "الوحدة",
        "min_stock": "الحد الأدنى",
        "info_title": "ℹ️ معلومات",
        "info_text": "🔐 هذا النظام يستخدم التخزين المحلي للمتصفح فقط.\n\n📱 بيانات الدخول محفوظة على جهازك ولا تنتقل إلى أجهزة أخرى.\n\n🛡️ يمكنك استخدام خيار 'تذكرني' لحفظ بيانات الدخول على هذا الجهاز فقط.",
        "shipping": "شحن منتجات",
        "customer": "اسم العميل",
        "register_shipping": "تسجيل الشحن",
        "balance": "الرصيد",
        "in": "وارد",
        "out": "صادر",
        "pallet_count": "عدد الباليتات",
        "last_10_days": "آخر 10 أيام",
        "remember_me": "تذكرني على هذا الجهاز",
        "clear_saved": "مسح البيانات المحفوظة"
    },
    "en": {
        "designer": "Eng. Elsayed Aoun",
        "login_title": "Login",
        "username": "Username",
        "password": "Password",
        "login_btn": "Login",
        "login_error": "Invalid username or password",
        "logout": "Logout",
        "welcome": "Welcome",
        "role": "Role",
        "dark_mode": "Dark Mode",
        "dashboard": "🏠 Dashboard",
        "production": "📈 Production",
        "maintenance": "🔧 Maintenance",
        "records": "📊 Records",
        "raw_materials": "📦 Raw Materials",
        "finished_goods": "🏭 Finished Goods",
        "users": "👥 Users",
        "settings": "⚙️ Settings",
        "line_label": "Production Line",
        "sup_label": "Supervisor",
        "prod_label": "Product",
        "target_label": "Quantity",
        "preform_label": "Preforms Used",
        "raw_label": "Packaging",
        "date_label": "Date",
        "maint_header": "Maintenance Center",
        "maint_types": ["Planned", "Breakdown"],
        "tech_label": "Technician",
        "issue_label": "Issue Description",
        "start_t": "Start Time",
        "end_t": "End Time",
        "note_label": "Notes",
        "save_btn": "Save",
        "success_msg": "Saved successfully",
        "eff_title": "Average Efficiency",
        "waste_title": "Waste Analysis",
        "history_p": "Production Logs",
        "history_m": "Maintenance Logs",
        "admin_title": "Admin Panel - Delete Record",
        "delete_btn": "Delete Selected Record",
        "del_success": "Record deleted successfully",
        "tools_label": "Tools:",
        "proc_label": "Procedure:",
        "weekend_msg": "Friday is weekend - No scheduled maintenance",
        "inventory_header": "Inventory Management",
        "current_stock": "Current Stock",
        "receipt": "Receive Materials",
        "alerts": "Alerts",
        "material": "Material",
        "quantity": "Quantity",
        "invoice": "Invoice Number",
        "receipt_date": "Receipt Date",
        "register_receipt": "Register Receipt",
        "low_stock_alert": "Low stock materials",
        "all_good": "All materials above minimum",
        "edit_stock": "Edit Stock",
        "new_stock": "New Stock",
        "update": "Update",
        "stock_updated": "Stock updated",
        "export_btn": "Export",
        "dashboard_title": "Dashboard",
        "total_production": "Total Production",
        "avg_efficiency": "Average Efficiency",
        "total_waste": "Total Waste",
        "low_stock_count": "Low Raw Materials",
        "line1_efficiency": "Line 1 Efficiency",
        "line2_efficiency": "Line 2 Efficiency",
        "smart_recommendations": "Smart Recommendations",
        "users_title": "User Management",
        "settings_title": "System Settings",
        "backup_data": "Backup Data",
        "clear_cache": "Clear Cache",
        "machine_select": "Select Machine",
        "task_name": "Task",
        "done": "Completed",
        "no_data": "No data recorded yet",
        "no_production": "No production records",
        "no_maintenance": "No maintenance records",
        "add_new_item": "Add New Item",
        "item_id": "Item ID",
        "item_name": "Item Name",
        "item_unit": "Unit",
        "min_stock": "Min Stock",
        "info_title": "ℹ️ Info",
        "info_text": "🔐 This system uses browser local storage only.\n\n📱 Login data is saved on your device only and does not transfer to other devices.\n\n🛡️ You can use 'Remember me' to save your login data on this device only.",
        "shipping": "Shipping",
        "customer": "Customer Name",
        "register_shipping": "Register Shipping",
        "balance": "Balance",
        "in": "In",
        "out": "Out",
        "pallet_count": "Pallets",
        "last_10_days": "Last 10 Days",
        "remember_me": "Remember me on this device",
        "clear_saved": "Clear saved data"
    },
    "bn": {
        "designer": "ইঞ্জি. সাঈদ আউন",
        "login_title": "লগইন",
        "username": "ব্যবহারকারীর নাম",
        "password": "পাসওয়ার্ড",
        "login_btn": "লগইন",
        "login_error": "ভুল ব্যবহারকারীর নাম বা পাসওয়ার্ড",
        "logout": "লগআউট",
        "welcome": "স্বাগতম",
        "role": "ভূমিকা",
        "dark_mode": "ডার্ক মোড",
        "dashboard": "🏠 ড্যাশবোর্ড",
        "production": "📈 উৎপাদন",
        "maintenance": "🔧 রক্ষণাবেক্ষণ",
        "records": "📊 রেকর্ড",
        "raw_materials": "📦 কাঁচামাল",
        "finished_goods": "🏭 সমাপ্ত পণ্য",
        "users": "👥 ব্যবহারকারী",
        "settings": "⚙️ সেটিংস",
        "line_label": "উৎপাদন লাইন",
        "sup_label": "সুপারভাইজার",
        "prod_label": "পণ্য",
        "target_label": "পরিমাণ",
        "preform_label": "প্রিফর্ম ব্যবহৃত",
        "raw_label": "প্যাকেজিং",
        "date_label": "তারিখ",
        "maint_header": "রক্ষণাবেক্ষণ কেন্দ্র",
        "maint_types": ["পরিকল্পিত", "ব্রেকডাউন"],
        "tech_label": "টেকনিশিয়ান",
        "issue_label": "সমস্যার বিবরণ",
        "start_t": "শুরু",
        "end_t": "শেষ",
        "note_label": "নোট",
        "save_btn": "সংরক্ষণ",
        "success_msg": "সফলভাবে সংরক্ষিত",
        "eff_title": "গড় দক্ষতা",
        "waste_title": "বর্জ্য বিশ্লেষণ",
        "history_p": "উৎপাদন লগ",
        "history_m": "রক্ষণাবেক্ষণ লগ",
        "admin_title": "অ্যাডমিন প্যানেল - রেকর্ড মুছুন",
        "delete_btn": "নির্বাচিত রেকর্ড মুছুন",
        "del_success": "রেকর্ড সফলভাবে মুছে ফেলা হয়েছে",
        "tools_label": "সরঞ্জাম:",
        "proc_label": "পদ্ধতি:",
        "weekend_msg": "শুক্রবার সাপ্তাহিক ছুটি",
        "inventory_header": "ইনভেন্টরি ব্যবস্থাপনা",
        "current_stock": "বর্তমান স্টক",
        "receipt": "উপকরণ গ্রহণ",
        "alerts": "সতর্কতা",
        "material": "উপাদান",
        "quantity": "পরিমাণ",
        "invoice": "ইনভয়েস নম্বর",
        "receipt_date": "গ্রহণের তারিখ",
        "register_receipt": "নিবন্ধন",
        "low_stock_alert": "স্বল্প স্টক",
        "all_good": "সব ঠিক আছে",
        "edit_stock": "স্টক সম্পাদনা",
        "new_stock": "নতুন স্টক",
        "update": "আপডেট",
        "stock_updated": "স্টক আপডেট হয়েছে",
        "export_btn": "এক্সপোর্ট",
        "dashboard_title": "ড্যাশবোর্ড",
        "total_production": "মোট উৎপাদন",
        "avg_efficiency": "গড় দক্ষতা",
        "total_waste": "মোট বর্জ্য",
        "low_stock_count": "স্বল্প কাঁচামাল",
        "line1_efficiency": "লাইন ১ দক্ষতা",
        "line2_efficiency": "লাইন ২ দক্ষতা",
        "smart_recommendations": "স্মার্ট সুপারিশ",
        "users_title": "ব্যবহারকারী ব্যবস্থাপনা",
        "settings_title": "সিস্টেম সেটিংস",
        "backup_data": "ব্যাকআপ",
        "clear_cache": "ক্যাশ সাফ",
        "machine_select": "মেশিন নির্বাচন",
        "task_name": "কাজের নাম",
        "done": "সম্পন্ন",
        "no_data": "এখনো কোন তথ্য রেকর্ড করা হয়নি",
        "no_production": "কোন উৎপাদন রেকর্ড নেই",
        "no_maintenance": "কোন রক্ষণাবেক্ষণ রেকর্ড নেই",
        "add_new_item": "নতুন আইটেম যোগ করুন",
        "item_id": "আইডি",
        "item_name": "আইটেমের নাম",
        "item_unit": "ইউনিট",
        "min_stock": "ন্যূনতম স্টক",
        "info_title": "ℹ️ তথ্য",
        "info_text": "🔐 এই সিস্টেম শুধুমাত্র ব্রাউজার লোকাল স্টোরেজ ব্যবহার করে।\n\n📱 লগইন ডেটা শুধুমাত্র আপনার ডিভাইসে সংরক্ষিত থাকে এবং অন্য ডিভাইসে যায় না।\n\n🛡️ 'আমাকে মনে রাখুন' ব্যবহার করে এই ডিভাইসে ডেটা সংরক্ষণ করতে পারেন।",
        "shipping": "পণ্য প্রেরণ",
        "customer": "গ্রাহকের নাম",
        "register_shipping": "প্রেরণ নিবন্ধন",
        "balance": "ব্যালেন্স",
        "in": "ইন",
        "out": "আউট",
        "pallet_count": "প্যালেট সংখ্যা",
        "last_10_days": "শেষ ১০ দিন",
        "remember_me": "এই ডিভাইসে মনে রাখুন",
        "clear_saved": "সংরক্ষিত ডেটা মুছুন"
    }
}

# ============================================================================
# 7. الاتصال بـ Google Sheets
# ============================================================================
def load_main_data():
    try:
        conn = st.connection("gsheets_testing", type=GSheetsConnection)
        df = conn.read(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], ttl=0)
        return conn, df
    except:
        return None, pd.DataFrame()

def save_to_sheet(conn, df):
    try:
        conn.update(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], data=df)
        return True
    except:
        return False

def send_telegram(msg):
    try:
        token = st.secrets["telegram"]["bot_token"]
        chat_id = st.secrets["telegram"]["chat_id"]
        requests.get(f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={urllib.parse.quote(msg)}&parse_mode=Markdown")
    except:
        pass

conn, df_main = load_main_data()

# ============================================================================
# 8. مخزن المواد الخام (raw.xlsx)
# ============================================================================
def load_raw_materials():
    if os.path.exists("raw.xlsx"):
        df_raw = pd.read_excel("raw.xlsx")
        required_cols = ["Material_ID", "Material_Name_AR", "Current_Stock", "Min_Stock", "Unit", "Last_Updated"]
        for col in required_cols:
            if col not in df_raw.columns:
                df_raw[col] = None
        if 'Last_Updated' in df_raw.columns:
            df_raw['Last_Updated'] = df_raw['Last_Updated'].astype(str)
        for col in ["Current_Stock", "Min_Stock"]:
            if col in df_raw.columns:
                df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce').fillna(0)
        return df_raw
    else:
        return pd.DataFrame()

def update_raw_materials(df_raw):
    df_raw.to_excel("raw.xlsx", index=False)
    return True

# ============================================================================
# 9. BOM والمواد المضافة
# ============================================================================
CONFIG = {
    "الخط الأول(smi)": {
        "products": ["200 ml Carton", "200 ml Shrink", "600 ml Carton", "1.5 L Shrink"],
        "pack_per_unit": {"200 ml Carton": 48, "200 ml Shrink": 20, "600 ml Carton": 30, "1.5 L Shrink": 6},
        "speed": {"200 ml Carton": 35000, "200 ml Shrink": 35000, "600 ml Carton": 20000, "1.5 L Shrink": 12000}
    },
    "الخط الثاني(welbing)": {
        "products": ["200 ml Carton", "200 ml Shrink", "330 ml Carton", "331 ml Shrink"],
        "pack_per_unit": {"200 ml Carton": 48, "200 ml Shrink": 20, "330 ml Carton": 40, "331 ml Shrink": 20},
        "speed": {"200 ml Carton": 40000, "200 ml Shrink": 40000, "330 ml Carton": 40000, "331 ml Shrink": 40000}
    }
}

BOM = {
    "200 ml Carton": {"بريفورم200": 48, "غطاء": 48, "ليبل 200": 48, "كرتون200": 1},
    "200 ml Shrink": {"بريفورم200": 20, "غطاء": 20, "ليبل 200": 20, "شرنك200": 0.0005},
    "600 ml Carton": {"بريفورم600": 30, "غطاء": 30, "ليبل 600": 30, "كرتون600": 1},
    "1.5 L Shrink": {"بريفورم لتر ونص": 6, "غطاء": 6, "ليبل لتر ونص": 6, "شرنك لتر ونص": 0.000625},
    "330 ml Carton": {"بريفورم330": 40, "غطاء": 40, "ليبل 330": 40, "كرتون330": 1},
    "331 ml Shrink": {"بريفورم330": 20, "غطاء": 20, "ليبل 330": 20, "شرنك330": 0.0005},
}

SHRINK_PALLET_CONFIG = {
    "200 ml Shrink": {"units_per_pallet": 180, "spacers_per_pallet": 7},
    "331 ml Shrink": {"units_per_pallet": 144, "spacers_per_pallet": 5},
    "1.5 L Shrink": {"units_per_pallet": 88, "spacers_per_pallet": 5},
}

ADHESIVE_CONSUMPTION = {
    "200 ml Carton": 0.3, "200 ml Shrink": 0.3, "600 ml Carton": 0.4,
    "1.5 L Shrink": 0.35, "330 ml Carton": 0.35, "331 ml Shrink": 0.35,
}

HOTMELT_CONSUMPTION = {
    "200 ml Carton": 2.0, "600 ml Carton": 2.5, "330 ml Carton": 2.0,
}

def calculate_spacers_needed(product, quantity):
    if product not in SHRINK_PALLET_CONFIG:
        return 0
    config = SHRINK_PALLET_CONFIG[product]
    return math.ceil(quantity / config["units_per_pallet"]) * config["spacers_per_pallet"]

def calculate_adhesive_needed(product, quantity):
    if product not in ADHESIVE_CONSUMPTION:
        return 0
    return math.ceil((ADHESIVE_CONSUMPTION[product] * quantity) / 1000 * 100) / 100

def calculate_hotmelt_needed(product, quantity):
    if product not in HOTMELT_CONSUMPTION:
        return 0
    return math.ceil((HOTMELT_CONSUMPTION[product] * quantity) / 1000 * 100) / 100

def consume_materials(product, quantity, df_raw):
    if product not in BOM:
        return df_raw, False, f"المنتج {product} غير موجود"
    
    required = {}
    for material, qty in BOM[product].items():
        if qty < 1:
            required[material] = math.ceil(quantity * qty)
        else:
            required[material] = qty * quantity
    
    if "Shrink" in product:
        spacers = calculate_spacers_needed(product, quantity)
        if spacers > 0:
            required["فواصل شرنك"] = spacers
    
    adhesive = calculate_adhesive_needed(product, quantity)
    if adhesive > 0:
        required["غراء الليبل"] = adhesive
    
    if "Carton" in product:
        hotmelt = calculate_hotmelt_needed(product, quantity)
        if hotmelt > 0:
            required["غراء الكرتون"] = hotmelt
    
    shortages = []
    new_df = df_raw.copy()
    
    for idx, row in new_df.iterrows():
        mat_name = row["Material_Name_AR"]
        if mat_name in required:
            req = required[mat_name]
            current = float(row["Current_Stock"]) if pd.notna(row["Current_Stock"]) else 0
            if current < req:
                shortages.append(f"{mat_name}")
            else:
                new_df.at[idx, "Current_Stock"] = current - req
                new_df.at[idx, "Last_Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if shortages:
        return df_raw, False, f"⚠️ عجز في المواد: {', '.join(shortages[:3])}"
    
    return new_df, True, f"✅ تم صرف المواد لـ {quantity:,.0f} وحدة"

# ============================================================================
# 10. مخزن الإنتاج التام (finished_goods.xlsx)
# ============================================================================
FINISHED_GOODS_FILE = "finished_goods.xlsx"

def calculate_pallet_count(product_name, balance, unit):
    if unit == "Shrink" or unit == "shrink":
        if "200" in str(product_name):
            return round(balance / 180, 2)
        elif "330" in str(product_name):
            return round(balance / 144, 2)
        else:
            return round(balance / 88, 2)
    else:
        if "200" in str(product_name):
            return round(balance / 96, 2)
        elif "330" in str(product_name):
            return round(balance / 81, 2)
        elif "600" in str(product_name):
            return round(balance / 63, 2)
        else:
            return round(balance / 100, 2)

def load_finished_goods():
    if os.path.exists(FINISHED_GOODS_FILE):
        try:
            df = pd.read_excel(FINISHED_GOODS_FILE)
            
            rename_map = {
                'Code': 'Code', 'Name Item': 'Name', 'in': 'In',
                'Out': 'Out', 'balance': 'Balance', 'Unit': 'Unit'
            }
            for old, new in rename_map.items():
                if old in df.columns:
                    df = df.rename(columns={old: new})
            
            required_cols = ["Code", "Name", "In", "Out", "Balance", "Unit"]
            for col in required_cols:
                if col not in df.columns:
                    df[col] = 0
            
            df = df.dropna(subset=["Code"], how="all")
            df = df[df["Code"].notna()]
            df = df[df["Code"] != 0]
            df = df[df["Code"] != ""]
            
            for col in ["Code", "In", "Out", "Balance"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            pallet_counts = []
            for idx, row in df.iterrows():
                product_name = row["Name"] if pd.notna(row["Name"]) else ""
                balance = row["Balance"] if pd.notna(row["Balance"]) else 0
                unit = row["Unit"] if pd.notna(row["Unit"]) else ""
                pallet_count = calculate_pallet_count(product_name, balance, unit)
                pallet_counts.append(pallet_count)
            
            df['Pallet_Count'] = pallet_counts
            
            if 'Last_Updated' not in df.columns:
                df['Last_Updated'] = datetime.now().strftime("%Y-%m-%d")
            else:
                df['Last_Updated'] = df['Last_Updated'].astype(str)
            
            return df
        except Exception as e:
            st.error(f"خطأ في تحميل المخزن: {e}")
            return pd.DataFrame()
    else:
        return pd.DataFrame()

def update_finished_goods(df):
    try:
        save_cols = {
            'Code': 'Code', 'Name': 'Name Item', 'In': 'in',
            'Out': 'Out', 'Balance': 'balance', 'Unit': 'Unit',
            'Pallet_Count': 'number of pallet'
        }
        df_save = df.copy()
        for en, ar in save_cols.items():
            if en in df_save.columns:
                df_save = df_save.rename(columns={en: ar})
        df_save.to_excel(FINISHED_GOODS_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"خطأ في حفظ المخزن: {e}")
        return False

def add_to_finished_goods(product_name, quantity, df_fg):
    mapping = {
        "200 ml Carton": "Cartoon  200 ml",
        "200 ml Shrink": "Shrink  200 ml",
        "600 ml Carton": "Cartoon  600  ml",
        "1.5 L Shrink": "1.5 Ltr",
        "330 ml Carton": "Cartoon  330  m",
        "331 ml Shrink": "Shrink  330 ml",
    }
    fg_name = mapping.get(product_name, product_name)
    
    idx = df_fg[df_fg["Name"].str.strip() == fg_name.strip()].index
    if len(idx) == 0:
        for i, row in df_fg.iterrows():
            if fg_name.strip() in str(row["Name"]):
                idx = [i]
                break
    
    if len(idx) == 0:
        return df_fg, False, f"⚠️ المنتج {product_name} غير موجود في المخزن"
    
    idx = idx[0]
    old_in = df_fg.at[idx, "In"] if pd.notna(df_fg.at[idx, "In"]) else 0
    old_balance = df_fg.at[idx, "Balance"] if pd.notna(df_fg.at[idx, "Balance"]) else 0
    
    new_in = old_in + quantity
    new_balance = old_balance + quantity
    
    df_fg.at[idx, "In"] = new_in
    df_fg.at[idx, "Balance"] = new_balance
    df_fg.at[idx, "Last_Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    product_name_val = df_fg.at[idx, "Name"] if pd.notna(df_fg.at[idx, "Name"]) else ""
    unit = df_fg.at[idx, "Unit"] if pd.notna(df_fg.at[idx, "Unit"]) else ""
    df_fg.at[idx, "Pallet_Count"] = calculate_pallet_count(product_name_val, new_balance, unit)
    
    return df_fg, True, f"✅ تم إضافة {quantity:,.0f} وحدة إلى المخزن"

def remove_from_finished_goods(product_name, quantity, df_fg):
    mapping = {
        "200 ml Carton": "Cartoon  200 ml",
        "200 ml Shrink": "Shrink  200 ml",
        "600 ml Carton": "Cartoon  600  ml",
        "1.5 L Shrink": "1.5 Ltr",
        "330 ml Carton": "Cartoon  330  m",
        "331 ml Shrink": "Shrink  330 ml",
    }
    fg_name = mapping.get(product_name, product_name)
    
    idx = df_fg[df_fg["Name"].str.strip() == fg_name.strip()].index
    if len(idx) == 0:
        for i, row in df_fg.iterrows():
            if fg_name.strip() in str(row["Name"]):
                idx = [i]
                break
    
    if len(idx) == 0:
        return df_fg, False, f"⚠️ المنتج {product_name} غير موجود"
    
    idx = idx[0]
    current = df_fg.at[idx, "Balance"] if pd.notna(df_fg.at[idx, "Balance"]) else 0
    if current < quantity:
        return df_fg, False, f"⚠️ الكمية غير كافية. المتوفر: {current:,.0f}"
    
    old_out = df_fg.at[idx, "Out"] if pd.notna(df_fg.at[idx, "Out"]) else 0
    new_out = old_out + quantity
    new_balance = current - quantity
    
    df_fg.at[idx, "Out"] = new_out
    df_fg.at[idx, "Balance"] = new_balance
    df_fg.at[idx, "Last_Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    product_name_val = df_fg.at[idx, "Name"] if pd.notna(df_fg.at[idx, "Name"]) else ""
    unit = df_fg.at[idx, "Unit"] if pd.notna(df_fg.at[idx, "Unit"]) else ""
    df_fg.at[idx, "Pallet_Count"] = calculate_pallet_count(product_name_val, new_balance, unit)
    
    return df_fg, True, f"✅ تم شحن {quantity:,.0f} وحدة"

def update_finished_goods_manual(df_fg, idx, new_balance):
    df_fg.at[idx, "Balance"] = new_balance
    df_fg.at[idx, "Last_Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    product_name = df_fg.at[idx, "Name"] if pd.notna(df_fg.at[idx, "Name"]) else ""
    unit = df_fg.at[idx, "Unit"] if pd.notna(df_fg.at[idx, "Unit"]) else ""
    df_fg.at[idx, "Pallet_Count"] = calculate_pallet_count(product_name, new_balance, unit)
    
    return df_fg

# ============================================================================
# 11. ماكينات الصيانة (مع دعم الصور)
# ============================================================================
MACHINE_MAP = {
    "النفخ(blowing)": "blowing_machine.xlsx",
    "الليبل(labeling)": "labeling_machine.xlsx",
    "السيور(Conveyor)": "Conveyor_machine.xlsx",
    "الكرتون(packing)": "packing_machine.xlsx",
    "البالتايزر(paletizer)": "paletizer_machine.xlsx",
    "الشرنك(shrink)": "shrink_machine.xlsx",
    "التعبئة(filling)": "Filling_machine.xlsx"
}

def create_machine_file(filepath):
    sample = pd.DataFrame({
        "Cat": ["ميكانيكية", "ميكانيكية", "كهربائية", "ميكانيكية", "كهربائية"],
        "No": [1, 2, 3, 4, 5],
        "Name": ["فحص المحامل", "تنظيف الفلاتر", "معايرة الحساسات", "تشحيم الأجزاء", "فحص الأحزمة"],
        "Photo": ["images/bearing.jpg", "images/filter.jpg", "images/sensor.jpg", "images/lubrication.jpg", "images/belt.jpg"],
        "Tools": ["مفتاح ربط", "فرشاة + هواء", "جهاز معايرة", "شحم", "مفتاح ربط"],
        "Proc": ["فحص الاهتزازات", "تنظيف بالهواء", "معايرة حسب الدليل", "تشحيم كل 100 ساعة", "فحص الشد"],
        "Freq": ["Daily", "Daily", "Weekly", "Weekly", "Monthly"],
        "Stat": ["Active"] * 5, "Note": [""] * 5, "Staff": [""] * 5
    })
    sample.to_excel(filepath, index=False)

def find_image_path(photo_name):
    if not photo_name or pd.isna(photo_name) or photo_name == "":
        return None
    
    possible_paths = [
        photo_name,
        os.path.join("images", photo_name),
        os.path.join("images", os.path.basename(photo_name)),
        f"images/{photo_name}",
        f"./images/{photo_name}",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    if os.path.exists("images"):
        for file in os.listdir("images"):
            if photo_name.lower() in file.lower() or file.lower() in photo_name.lower():
                return os.path.join("images", file)
    
    return None

def get_scheduled_tasks(df_tasks):
    today = datetime.now()
    if today.strftime('%A') == 'Friday':
        return pd.DataFrame()
    allowed = ['Daily']
    if today.strftime('%A') == 'Saturday':
        allowed.append('Weekly')
    if today.day == 1:
        allowed.append('Monthly')
    if 'Freq' in df_tasks.columns:
        return df_tasks[df_tasks['Freq'].isin(allowed)]
    return pd.DataFrame()

# ============================================================================
# 12. دوال عرض البيانات
# ============================================================================
def translate_dataframe(df, lang):
    if df is None or df.empty:
        return df
    trans = {
        "ar": {"Date": "التاريخ", "Line": "الخط", "Supervisor": "المشرف", "Product": "المنتج",
               "Quantity": "الكمية", "Output_Units": "الوحدات", "Efficiency": "الكفاءة",
               "Efficiency_%": "الكفاءة %", "Type": "النوع", "Machine": "الماكينة", "Technician": "الفني"},
        "en": {"Date": "Date", "Line": "Line", "Supervisor": "Supervisor", "Product": "Product",
               "Quantity": "Quantity", "Output_Units": "Output", "Efficiency": "Efficiency",
               "Efficiency_%": "Efficiency %", "Type": "Type", "Machine": "Machine", "Technician": "Technician"},
        "bn": {"Date": "তারিখ", "Line": "লাইন", "Supervisor": "সুপারভাইজার", "Product": "পণ্য",
               "Quantity": "পরিমাণ", "Output_Units": "উৎপাদন", "Efficiency": "দক্ষতা",
               "Efficiency_%": "দক্ষতা", "Type": "ধরন", "Machine": "মেশিন", "Technician": "টেকনিশিয়ান"}
    }
    rename = {col: trans.get(lang, trans["ar"]).get(col, col) for col in df.columns}
    return df.rename(columns=rename)

# ============================================================================
# 13. لوحة القيادة
# ============================================================================
def show_dashboard(df_main, df_raw, df_fg, t):
    st.title(t["dashboard_title"])
    
    total_prod = 0
    total_waste = 0
    today_prod = 0
    
    line1_efficiency = 0
    line2_efficiency = 0
    line1_count = 0
    line2_count = 0
    
    if df_main is not None and not df_main.empty:
        prod_df = df_main[df_main['Type'] == 'Production'] if 'Type' in df_main.columns else pd.DataFrame()
        if not prod_df.empty:
            if 'Output_Units' in prod_df.columns:
                total_prod = int(prod_df['Output_Units'].sum())
            if 'Waste_Bottles' in prod_df.columns:
                total_waste = int(prod_df['Waste_Bottles'].sum())
            if 'Date' in prod_df.columns:
                today_str = datetime.now().strftime("%Y-%m-%d")
                today_prod = int(prod_df[prod_df['Date'] == today_str]['Output_Units'].sum()) if not prod_df[prod_df['Date'] == today_str].empty else 0
            
            if 'Line' in prod_df.columns and 'Efficiency_%' in prod_df.columns:
                line1_data = prod_df[prod_df['Line'] == "الخط الأول(smi)"]
                line2_data = prod_df[prod_df['Line'] == "الخط الثاني(welbing)"]
                
                if not line1_data.empty:
                    line1_efficiency = round(line1_data['Efficiency_%'].mean(), 1)
                    line1_count = len(line1_data)
                if not line2_data.empty:
                    line2_efficiency = round(line2_data['Efficiency_%'].mean(), 1)
                    line2_count = len(line2_data)
    
    low_raw_count = len(df_raw[df_raw["Current_Stock"] <= df_raw["Min_Stock"]]) if not df_raw.empty else 0
    total_raw_value = int(df_raw["Current_Stock"].sum()) if not df_raw.empty else 0
    
    fg_in = int(df_fg["In"].sum()) if not df_fg.empty and "In" in df_fg.columns else 0
    fg_out = int(df_fg["Out"].sum()) if not df_fg.empty and "Out" in df_fg.columns else 0
    fg_balance = int(df_fg["Balance"].sum()) if not df_fg.empty and "Balance" in df_fg.columns else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(t["total_production"], f"{total_prod:,}", f"+{today_prod:,} اليوم" if today_prod > 0 else None)
    with col2:
        avg_eff = (line1_efficiency + line2_efficiency) / 2 if (line1_count > 0 or line2_count > 0) else 0
        st.metric(t["avg_efficiency"], f"{avg_eff:.1f}%")
    with col3:
        st.metric(t["total_waste"], f"{total_waste:,}")
    with col4:
        st.metric("صافي الإنتاج", f"{total_prod - total_waste:,}")
    
    st.markdown("---")
    
    st.subheader("📊 كفاءة خطوط الإنتاج")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(t["line1_efficiency"], f"{line1_efficiency}%", delta="عدد السجلات: " + str(line1_count) if line1_count > 0 else None)
    with col2:
        st.metric(t["line2_efficiency"], f"{line2_efficiency}%", delta="عدد السجلات: " + str(line2_count) if line2_count > 0 else None)
    
    st.markdown("---")
    
    st.subheader("📦 توزيع المواد الخام")
    if not df_raw.empty:
        raw_chart_data = df_raw.nlargest(10, "Current_Stock")[["Material_Name_AR", "Current_Stock"]].copy()
        raw_chart_data = raw_chart_data.rename(columns={"Material_Name_AR": "المادة", "Current_Stock": "الكمية"})
        fig_raw = px.bar(raw_chart_data, x="المادة", y="الكمية", 
                         title="أهم 10 مواد خام",
                         color="الكمية", color_continuous_scale="Blues")
        fig_raw.update_layout(height=450)
        st.plotly_chart(fig_raw, use_container_width=True)
    else:
        st.info("لا توجد بيانات للمواد الخام")
    
    st.markdown("---")
    
    st.subheader("🏭 توزيع المنتج التام")
    if not df_fg.empty:
        fg_chart_data = df_fg[["Name", "Balance"]].copy()
        fg_chart_data = fg_chart_data.rename(columns={"Name": "المنتج", "Balance": "الرصيد"})
        fig_fg = px.bar(fg_chart_data, x="المنتج", y="الرصيد", 
                        title="رصيد المنتجات التامة",
                        color="الرصيد", color_continuous_scale="Greens")
        fig_fg.update_layout(height=450)
        st.plotly_chart(fig_fg, use_container_width=True)
    else:
        st.info("لا توجد بيانات للمنتج التام")
    
    st.markdown("---")
    
    st.subheader(t["smart_recommendations"])
    recs = []
    
    if line1_efficiency < 75 and line1_count > 0:
        recs.append("⚠️ كفاءة الخط الأول منخفضة - راجع سرعة الإنتاج")
    if line2_efficiency < 75 and line2_count > 0:
        recs.append("⚠️ كفاءة الخط الثاني منخفضة - راجع سرعة الإنتاج")
    if low_raw_count > 0:
        recs.append(f"📦 يوجد {low_raw_count} مواد خام منخفضة - يفضل إعادة الطلب")
    if today_prod == 0 and datetime.now().hour > 10:
        recs.append("📊 لم يتم تسجيل إنتاج اليوم - يرجى مراجعة وردية الإنتاج")
    if fg_balance <= 0:
        recs.append("🏭 مخزن المنتج التام فارغ - يرجى زيادة الإنتاج")
    if fg_balance > 50000:
        recs.append("📦 مخزن المنتج التام مكتظ - يفضل زيادة الشحنات")
    if total_waste > total_prod * 0.05 and total_prod > 0:
        recs.append("🗑️ نسبة الهالك مرتفعة (أكثر من 5%) - راجع جودة المواد الخام")
    
    if not recs:
        recs.append("✅ جميع المؤشرات جيدة - استمر بهذا المستوى!")
    
    for rec in recs:
        if "⚠️" in rec:
            st.warning(rec)
        elif "📦" in rec or "🏭" in rec:
            st.info(rec)
        elif "🗑️" in rec:
            st.error(rec)
        else:
            st.success(rec)

# ============================================================================
# 14. واجهة تسجيل الدخول (مع localStorage)
# ============================================================================
def login_screen(t):
    # محاولة تحميل البيانات المحفوظة
    saved_user, saved_pass, has_creds = load_credentials_local()
    
    if has_creds and saved_user and saved_pass:
        if saved_user in USERS and USERS[saved_user]["password"] == saved_pass:
            st.session_state.authenticated = True
            st.session_state.user_role = USERS[saved_user]["role"]
            st.session_state.user_name = USERS[saved_user]["name"]
            st.rerun()
    
    if os.path.exists("birma mark.png"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("birma mark.png", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #0047AB;'>🏭 BIRMA</h1>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input(t["username"], value=saved_user if saved_user else "")
            password = st.text_input(t["password"], type="password", value=saved_pass if saved_pass else "")
            remember = st.checkbox(t["remember_me"], value=has_creds)
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.form_submit_button(t["login_btn"], use_container_width=True):
                    if username in USERS and USERS[username]["password"] == password:
                        st.session_state.authenticated = True
                        st.session_state.user_role = USERS[username]["role"]
                        st.session_state.user_name = USERS[username]["name"]
                        if remember:
                            save_credentials_local(username, password, True)
                        st.rerun()
                    else:
                        st.error(t["login_error"])
            
            with col_btn2:
                if has_creds and st.form_submit_button("🗑️ " + t["clear_saved"], use_container_width=True):
                    clear_credentials_local()
                    st.rerun()
    
    with st.expander(t["info_title"]):
        st.markdown(t["info_text"])

# ============================================================================
# 15. الواجهة الرئيسية
# ============================================================================
def main():
    if not st.session_state.authenticated:
        login_screen(LANG["ar"])
        return
    
    show_current_date()
    
    dark_mode = st.sidebar.toggle(LANG[st.session_state.lang]["dark_mode"], value=st.session_state.dark_mode)
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.rerun()
    
    if st.session_state.dark_mode:
        st.markdown("""
            <style>
            .stApp { background-color: #0e1117; }
            .stMetric { background-color: #1e2130; border-radius: 10px; padding: 10px; }
            .stDataFrame { background-color: #1e2130; }
            </style>
        """, unsafe_allow_html=True)
    
    st.sidebar.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    if os.path.exists("birma mark.png"):
        st.sidebar.image("birma mark.png", use_container_width=True)
    else:
        st.sidebar.markdown("<h1 style='color: #0047AB; text-align: center;'>🏭 BIRMA</h1>", unsafe_allow_html=True)
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
    
    st.sidebar.divider()
    
    st.sidebar.markdown(f"<p style='text-align: center; font-size: 12px; color: gray; margin-bottom: 0;'>Designed by:</p>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<h4 style='text-align: center; color: #2E8B57; margin-top: 0;'>{LANG[st.session_state.lang]['designer']}</h4>", unsafe_allow_html=True)
    st.sidebar.divider()
    
    lang = st.sidebar.selectbox("🌐 Language", ["ar", "en", "bn"], index=["ar", "en", "bn"].index(st.session_state.lang))
    st.session_state.lang = lang
    t = LANG[lang]
    
    user_icon = next((u["icon"] for u in USERS.values() if u["name"] == st.session_state.user_name), "👤")
    st.sidebar.markdown(f"### {user_icon} {st.session_state.user_name}")
    st.sidebar.markdown(f"📌 {t['role']}: {st.session_state.user_role}")
    
    if st.sidebar.button(t["logout"], use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.user_name = None
        st.rerun()
    
    st.sidebar.divider()
    
    available_menus = ROLE_PERMISSIONS.get(st.session_state.user_role, ROLE_PERMISSIONS["admin"])
    menu_map = {
        "🏠 Dashboard": t["dashboard"], "📈 Production": t["production"],
        "🔧 Maintenance": t["maintenance"], "📊 Records": t["records"],
        "📦 Raw Materials": t["raw_materials"], "🏭 Finished Goods": t["finished_goods"],
        "👥 Users": t["users"], "⚙️ Settings": t["settings"]
    }
    selected = st.sidebar.radio("📋", [menu_map.get(m, m) for m in available_menus])
    reverse_map = {v: k for k, v in menu_map.items()}
    selected_raw = reverse_map.get(selected, selected)
    
    if selected_raw in ["📈 Production", "🔧 Maintenance"]:
        selected_line = st.sidebar.radio(t["line_label"], list(CONFIG.keys()))
    else:
        selected_line = None
    
    df_raw = load_raw_materials()
    df_fg = load_finished_goods()
    
    # ========== Dashboard ==========
    if selected_raw == "🏠 Dashboard":
        show_dashboard(df_main, df_raw, df_fg, t)
    
    # ========== Production ==========
    elif selected_raw == "📈 Production" and selected_line:
        st.header(f"{t['production']} - {selected_line}")
        with st.form("prod_form"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input(t["sup_label"])
                product = st.selectbox(t["prod_label"], CONFIG[selected_line]["products"])
                target = st.number_input(t["target_label"], min_value=0)
            with c2:
                preforms = st.number_input(t["preform_label"], min_value=0)
                raw_val = st.number_input(t["raw_label"], min_value=0)
                p_date = st.date_input(t["date_label"])
            
            if st.form_submit_button(t["save_btn"]):
                if target <= 0:
                    st.error("⚠️ الكمية يجب أن تكون أكبر من صفر")
                elif not name:
                    st.error("⚠️ يرجى إدخال اسم المشرف")
                else:
                    packs = CONFIG[selected_line]["pack_per_unit"][product]
                    speed = CONFIG[selected_line]["speed"][product]
                    eff = round((target * packs / (speed * 15)) * 100, 1) if speed > 0 else 0
                    
                    new_raw, raw_ok, raw_msg = consume_materials(product, target, df_raw)
                    if not raw_ok:
                        st.error(raw_msg)
                    else:
                        if update_raw_materials(new_raw):
                            new_row = pd.DataFrame([{"Type": "Production", "Date": str(p_date), "Line": selected_line,
                                                     "Supervisor": name, "Product": product, "Output_Units": int(target),
                                                     "Waste_Bottles": 0, "Waste_Raw": 0, "Efficiency_%": float(eff),
                                                     "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])
                            if conn and not df_main.empty:
                                save_to_sheet(conn, pd.concat([df_main, new_row], ignore_index=True))
                            elif conn:
                                save_to_sheet(conn, new_row)
                            
                            if not df_fg.empty:
                                new_fg, fg_ok, fg_msg = add_to_finished_goods(product, target, df_fg)
                                if fg_ok:
                                    update_finished_goods(new_fg)
                                    st.info(fg_msg)
                                else:
                                    st.warning(fg_msg)
                            
                            send_telegram(f"🚀 Production: {product} - {target} units - {eff}%")
                            st.success(raw_msg)
                            st.balloons()
                            st.rerun()
    
    # ========== Maintenance ==========
    elif selected_raw == "🔧 Maintenance" and selected_line:
        st.header(t["maint_header"])
        m_type = st.radio("Type", t["maint_types"], horizontal=True)
        machine = st.sidebar.selectbox(t["machine_select"], list(MACHINE_MAP.keys()))
        
        if m_type == t["maint_types"][0]:
            path = MACHINE_MAP[machine]
            if not os.path.exists(path):
                create_machine_file(path)
            df_tasks = pd.read_excel(path, skiprows=2)
            df_tasks.columns = ['Cat', 'No', 'Name', 'Photo', 'Tools', 'Proc', 'Freq', 'Stat', 'Note', 'Staff']
            tasks = get_scheduled_tasks(df_tasks)
            
            if tasks.empty:
                st.warning(t["weekend_msg"])
            else:
                with st.form("m_form"):
                    tech = st.text_input(t["tech_label"])
                    recs = []
                    for i, r in tasks.iterrows():
                        with st.expander(f"🔧 {r['Name']} ({r['Freq']})"):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"**{t['tools_label']}** {r['Tools']}")
                                st.info(f"**{t['proc_label']}**\n{r['Proc']}")
                                note = st.text_input(t["note_label"], key=f"note_{i}")
                            with col2:
                                photo_name = r['Photo'] if pd.notna(r['Photo']) else ""
                                img_path = find_image_path(photo_name)
                                if img_path and os.path.exists(img_path):
                                    st.image(img_path, use_container_width=True)
                                elif photo_name:
                                    st.caption(f"📷 غير موجود: {photo_name}")
                                else:
                                    st.caption("📷 لا توجد صورة")
                                done = st.checkbox(t["done"], key=f"done_{i}")
                            if done:
                                recs.append({"Type": "Maintenance_Planned", "Line": selected_line,
                                            "Date": str(datetime.now().date()), "Machine": machine,
                                            "Task": r['Name'], "Technician": tech, "Notes": note,
                                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                    if st.form_submit_button(t["save_btn"]):
                        if recs:
                            new_df = pd.DataFrame(recs)
                            if conn:
                                save_to_sheet(conn, pd.concat([df_main, new_df], ignore_index=True) if not df_main.empty else new_df)
                        st.success(t["success_msg"])
                        st.rerun()
        else:
            with st.form("break_form"):
                tech = st.text_input(t["tech_label"])
                issue = st.text_area(t["issue_label"])
                t1 = st.time_input(t["start_t"])
                t2 = st.time_input(t["end_t"])
                notes = st.text_area(t["note_label"])
                if st.form_submit_button(t["save_btn"]):
                    new_b = pd.DataFrame([{"Type": "Maintenance_Breakdown", "Line": selected_line,
                                           "Date": str(datetime.now().date()), "Machine": machine,
                                           "Technician": tech, "Issue": issue,
                                           "Start_Time": t1.strftime("%H:%M"), "End_Time": t2.strftime("%H:%M"),
                                           "Notes": notes, "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}])
                    if conn:
                        save_to_sheet(conn, pd.concat([df_main, new_b], ignore_index=True) if not df_main.empty else new_b)
                    send_telegram(f"⚠️ Breakdown: {machine} - {issue[:50]}")
                    st.success(t["success_msg"])
                    st.rerun()
    
    # ========== Records ==========
    elif selected_raw == "📊 Records":
        st.header(t["records"])
        
        if df_main is not None and not df_main.empty:
            ten_days_ago = datetime.now() - timedelta(days=10)
            
            tab1, tab2 = st.tabs([t["history_p"], t["history_m"]])
            
            with tab1:
                prod_logs = df_main[df_main['Type'] == 'Production'] if 'Type' in df_main.columns else pd.DataFrame()
                if not prod_logs.empty and 'Date' in prod_logs.columns:
                    prod_logs['Date'] = pd.to_datetime(prod_logs['Date'])
                    prod_logs_last10 = prod_logs[prod_logs['Date'] >= ten_days_ago].copy()
                    prod_logs_last10 = prod_logs_last10.sort_values('Date', ascending=False)
                    
                    if not prod_logs_last10.empty:
                        st.dataframe(translate_dataframe(prod_logs_last10, lang), use_container_width=True)
                        st.caption(f"📊 عرض {len(prod_logs_last10)} سجل إنتاج من آخر 10 أيام")
                    else:
                        st.info(t["no_production"])
                else:
                    st.info(t["no_production"])
            
            with tab2:
                maint_logs = df_main[df_main['Type'].str.contains('Maintenance', na=False)] if 'Type' in df_main.columns else pd.DataFrame()
                if not maint_logs.empty and 'Date' in maint_logs.columns:
                    maint_logs['Date'] = pd.to_datetime(maint_logs['Date'])
                    maint_logs_last10 = maint_logs[maint_logs['Date'] >= ten_days_ago].copy()
                    maint_logs_last10 = maint_logs_last10.sort_values('Date', ascending=False)
                    
                    if not maint_logs_last10.empty:
                        st.dataframe(translate_dataframe(maint_logs_last10, lang), use_container_width=True)
                        st.caption(f"📊 عرض {len(maint_logs_last10)} سجل صيانة من آخر 10 أيام")
                    else:
                        st.info(t["no_maintenance"])
                else:
                    st.info(t["no_maintenance"])
        else:
            st.info(t["no_data"])
    
    # ========== Raw Materials (مع رقم الفاتورة) ==========
    elif selected_raw == "📦 Raw Materials":
        st.header(t["raw_materials"])
        if not df_raw.empty:
            tab1, tab2 = st.tabs([t["current_stock"], t["receipt"]])
            with tab1:
                st.dataframe(df_raw, use_container_width=True)
                with st.expander(t["edit_stock"]):
                    if st.text_input(t["password"], type="password") == "admin123":
                        material = st.selectbox(t["material"], df_raw["Material_Name_AR"])
                        new_qty = st.number_input(t["new_stock"], min_value=0)
                        if st.button(t["update"]):
                            idx = df_raw[df_raw["Material_Name_AR"] == material].index[0]
                            df_raw.at[idx, "Current_Stock"] = new_qty
                            df_raw.at[idx, "Last_Updated"] = datetime.now().strftime("%Y-%m-%d")
                            update_raw_materials(df_raw)
                            st.success(t["stock_updated"])
                            st.rerun()
            
            with tab2:
                with st.form("receipt_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        material = st.selectbox(t["material"], df_raw["Material_Name_AR"])
                        qty = st.number_input(t["quantity"], min_value=0)
                    with col2:
                        invoice_no = st.text_input(t["invoice"])
                        receipt_date = st.date_input(t["receipt_date"])
                    notes = st.text_area("ملاحظات")
                    
                    if st.form_submit_button(t["register_receipt"], use_container_width=True):
                        if qty <= 0:
                            st.error("⚠️ الكمية يجب أن تكون أكبر من صفر")
                        elif not material:
                            st.error("⚠️ يرجى اختيار المادة")
                        else:
                            idx = df_raw[df_raw["Material_Name_AR"] == material].index[0]
                            df_raw.at[idx, "Current_Stock"] += qty
                            df_raw.at[idx, "Last_Updated"] = datetime.now().strftime("%Y-%m-%d")
                            update_raw_materials(df_raw)
                            
                            # تسجيل عملية الاستلام مع رقم الفاتورة
                            receipt_record = pd.DataFrame([{
                                "Type": "Raw_Receipt",
                                "Date": str(receipt_date),
                                "Material": material,
                                "Quantity": qty,
                                "Invoice": invoice_no,
                                "Notes": notes,
                                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }])
                            if conn and not df_main.empty:
                                save_to_sheet(conn, pd.concat([df_main, receipt_record], ignore_index=True))
                            elif conn:
                                save_to_sheet(conn, receipt_record)
                            
                            send_telegram(f"📥 استلام مواد خام: {material} - {qty:,.0f} - فاتورة: {invoice_no}")
                            st.success(f"✅ تم استلام {qty:,.0f} من {material}\n📄 رقم الفاتورة: {invoice_no}")
                            st.rerun()
        else:
            st.warning("لا توجد بيانات مخزون")
            st.info("💡 يرجى التأكد من وجود ملف raw.xlsx في نفس المجلد")
    
    # ========== Finished Goods ==========
    elif selected_raw == "🏭 Finished Goods":
        st.header(t["finished_goods"])
        
        if not df_fg.empty:
            display_cols = {
                'Code': 'الكود', 'Name': 'الصنف', 'In': t['in'],
                'Out': t['out'], 'Balance': t['balance'], 'Unit': 'الوحدة',
                'Pallet_Count': t['pallet_count'], 'Last_Updated': 'آخر تحديث'
            }
            display = df_fg[[c for c in display_cols.keys() if c in df_fg.columns]].copy()
            display = display.rename(columns={k: v for k, v in display_cols.items() if k in display.columns})
            
            tab1, tab2, tab3 = st.tabs(["📦 المخزون الحالي", "🚚 " + t["shipping"], "✏️ تعديل الرصيد"])
            
            with tab1:
                st.dataframe(display, use_container_width=True)
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(t['in'], f"{df_fg['In'].sum():,.0f}")
                with col2:
                    st.metric(t['out'], f"{df_fg['Out'].sum():,.0f}")
                with col3:
                    st.metric(t['balance'], f"{df_fg['Balance'].sum():,.0f}")
                with col4:
                    st.metric(t['pallet_count'], f"{df_fg['Pallet_Count'].sum():,.0f}")
            
            with tab2:
                with st.form("shipping_form"):
                    product = st.selectbox(t["prod_label"], df_fg["Name"])
                    qty = st.number_input(t["quantity"], min_value=0, step=100)
                    customer = st.text_input(t["customer"])
                    if st.form_submit_button(t["register_shipping"], use_container_width=True):
                        if qty <= 0:
                            st.error("⚠️ الكمية يجب أن تكون أكبر من صفر")
                        else:
                            new_fg, ok, msg = remove_from_finished_goods(product, qty, df_fg)
                            if ok:
                                update_finished_goods(new_fg)
                                send_telegram(f"🚚 شحن: {product} - {qty:,.0f} وحدة - {customer}")
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
            
            with tab3:
                st.subheader("✏️ تعديل الرصيد يدوياً")
                if st.text_input(t["password"], type="password", key="fg_pw") == "admin123":
                    product = st.selectbox(t["prod_label"], df_fg["Name"], key="fg_product")
                    current = df_fg[df_fg["Name"] == product]["Balance"].values[0]
                    new_balance = st.number_input(t["new_stock"], min_value=0, value=int(current))
                    if st.button(t["update"]):
                        idx = df_fg[df_fg["Name"] == product].index[0]
                        df_fg = update_finished_goods_manual(df_fg, idx, new_balance)
                        update_finished_goods(df_fg)
                        st.success(t["stock_updated"])
                        st.rerun()
                else:
                    st.warning("🔒 يرجى إدخال كلمة مرور المشرف")
        else:
            st.warning("لا توجد بيانات في مخزن الإنتاج التام")
            st.info("💡 يرجى التأكد من وجود ملف finished_goods.xlsx في نفس المجلد")
    
    # ========== Users ==========
    elif selected_raw == "👥 Users" and st.session_state.user_role == "admin":
        st.header(t["users_title"])
        users_df = pd.DataFrame([{"Username": k, "Name": v["name"], "Role": v["role"]} for k, v in USERS.items()])
        st.dataframe(users_df, use_container_width=True)
    
    # ========== Settings ==========
    elif selected_raw == "⚙️ Settings" and st.session_state.user_role == "admin":
        st.header(t["settings_title"])
        col1, col2 = st.columns(2)
        with col1:
            if st.button(t["backup_data"], use_container_width=True):
                if df_main is not None and not df_main.empty:
                    df_main.to_excel(f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", index=False)
                    st.success("تم إنشاء نسخة احتياطية")
        with col2:
            if st.button(t["clear_cache"], use_container_width=True):
                st.cache_data.clear()
                st.success("تم مسح الذاكرة المؤقتة")
    
    # ========== Delete Records ==========
    st.sidebar.divider()
    with st.sidebar.expander("🔒 " + t["admin_title"]):
        if st.text_input(t["password"], type="password", key="del_pw") == "admin123":
            if df_main is not None and not df_main.empty:
                df_display = df_main.copy()
                if 'Type' in df_display.columns and 'Date' in df_display.columns:
                    def fmt(row):
                        if row['Type'] == 'Production':
                            return f"📦 إنتاج | {row['Date']} | {row.get('Product', 'N/A')}"
                        return f"🔧 صيانة | {row['Date']} | {row.get('Machine', 'N/A')}"
                    df_display['desc'] = df_display.apply(fmt, axis=1)
                    idx = st.selectbox("اختر السجل", options=df_display.index, format_func=lambda x: df_display.loc[x, 'desc'])
                    if st.button(t["delete_btn"]):
                        df_updated = df_main.drop(idx)
                        if conn and save_to_sheet(conn, df_updated):
                            st.success(t["del_success"])
                            st.rerun()
    
    st.sidebar.divider()
    st.sidebar.markdown(f"<center><small>BIRMA v12.0<br>{t['designer']}</small></center>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()