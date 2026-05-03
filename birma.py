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
import base64
from calendar import monthrange

# ============================================================================
# 1. إعدادات الصفحة مع CSS محسن
# ============================================================================
st.set_page_config(page_title="BIRMA Integrated System", page_icon="🏭", layout="wide")

# CSS محسن
st.markdown("""
<style>
    .stApp { background: #ffffff; }
    
    .glass-card {
        background: #ffffff;
        border-radius: 25px;
        padding: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
        border: 1px solid rgba(0,0,0,0.05);
    }
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
    }
    
    .gradient-title {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: bold;
        text-align: center;
        text-shadow: none;
    }
    
    .marquee {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border-radius: 50px;
        padding: 12px 20px;
        margin: 20px 0;
        overflow: hidden;
        white-space: nowrap;
        color: #ffffff;
        font-weight: bold;
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .marquee-content {
        display: inline-block;
        animation: marquee 25s linear infinite;
        padding-left: 100%;
    }
    @keyframes marquee {
        0% { transform: translateX(0); }
        100% { transform: translateX(-100%); }
    }
    .marquee-content span {
        margin-right: 50px;
        padding: 8px 20px;
        border-radius: 30px;
        display: inline-block;
        font-weight: bold;
    }
    .critical { background-color: #dc2626; color: white; }
    .warning { background-color: #f59e0b; color: white; }
    .info { background-color: #3b82f6; color: white; }
    .success { background-color: #10b981; color: white; }
    
    .gauge-container {
        text-align: center;
        padding: 20px;
        border-radius: 20px;
        background: #ffffff;
        box-shadow: 0 5px 20px rgba(0,0,0,0.08);
    }
    .gauge-container h3 { color: #1a1a2e; }
    .gauge-container small { color: #666; }
    
    .stButton button {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        color: white;
        border: none;
        border-radius: 30px;
        padding: 10px 25px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: scale(1.05);
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] .stSelectbox label { color: #ffffff !important; }
    
    .stMarkdown, .stText, .stDataFrame { color: #1a1a2e; }
    .stMetric label { color: #1a1a2e !important; font-weight: bold; }
    .stMetric .stMetric-value { color: #1a1a2e !important; }
    
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background: #ffffff;
        border-radius: 20px;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        color: white !important;
    }
    
    .streamlit-expanderHeader {
        background: #ffffff;
        border-radius: 15px;
        font-weight: bold;
    }
    .stAlert { border-radius: 15px; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 2. نظام حفظ الدخول
# ============================================================================
def save_credentials_local(username, password, remember=True):
    if remember:
        data = {"u": username, "p": password, "t": datetime.now().isoformat()}
        encoded = base64.b64encode(json.dumps(data).encode()).decode()
        st.markdown(f"<script>localStorage.setItem('birma_creds', '{encoded}');</script>", unsafe_allow_html=True)
        return True
    return False

def load_credentials_local():
    st.markdown("""
        <script>
            var creds = localStorage.getItem('birma_creds');
            if (creds && !window.location.search.includes('creds')) {
                window.location.href = window.location.pathname + '?creds=' + encodeURIComponent(creds);
            }
        </script>
    """, unsafe_allow_html=True)
    if 'creds' in st.query_params:
        try:
            decoded = base64.b64decode(st.query_params['creds']).decode()
            data = json.loads(decoded)
            return data.get('u'), data.get('p'), True
        except:
            return None, None, False
    return None, None, False

def clear_credentials_local():
    st.markdown("<script>localStorage.removeItem('birma_creds');</script>", unsafe_allow_html=True)
    st.query_params.clear()

# ============================================================================
# 3. دالة عرض التاريخ
# ============================================================================
def show_current_date():
    today = datetime.now()
    lang = st.session_state.get('lang', 'ar')
    if lang == "ar":
        days = {"Monday": "الإثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء",
                "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"}
        months = {"January": "يناير", "February": "فبراير", "March": "مارس", "April": "أبريل",
                  "May": "مايو", "June": "يونيو", "July": "يوليو", "August": "أغسطس",
                  "September": "سبتمبر", "October": "أكتوبر", "November": "نوفمبر", "December": "ديسمبر"}
        date_str = f"{days.get(today.strftime('%A'), today.strftime('%A'))}، {today.day} {months.get(today.strftime('%B'), today.strftime('%B'))} {today.year}"
    else:
        date_str = today.strftime("%A, %B %d, %Y")
    st.markdown(f"<div style='text-align: left; font-size: 14px; background: #ffffff; padding: 10px; border-radius: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);'>📅 {date_str}</div>", unsafe_allow_html=True)

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
    "admin": {"password": "100", "role": "admin", "name": "مدير النظام", "icon": "👑"},
    "pro": {"password": "400", "role": "supervisor", "name": "مشرف إنتاج", "icon": "👔"},
    "tec": {"password": "300", "role": "technician", "name": "فني صيانة", "icon": "🔧"},
    "sto": {"password": "200", "role": "storekeeper", "name": "أمين مخزن", "icon": "📦"},
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
# 6. نظام اللغات الكامل
# ============================================================================
LANG = {
    "ar": {
        "designer": "م/ السيد عون", "login_title": "تسجيل الدخول", "username": "اسم المستخدم",
        "password": "كلمة المرور", "login_btn": "دخول", "login_error": "خطأ",
        "logout": "تسجيل خروج", "welcome": "مرحباً", "role": "الدور",
        "dark_mode": "الوضع الليلي", "dashboard": "🏠 لوحة القيادة",
        "production": "📈 إدارة الإنتاج", "maintenance": "🔧 مركز الصيانة",
        "records": "📊 السجلات", "raw_materials": "📦 المخازن (مواد خام)",
        "finished_goods": "🏭 مخزن الإنتاج التام", "users": "👥 المستخدمين",
        "settings": "⚙️ الإعدادات", "line_label": "خط العمل", "sup_label": "المشرف",
        "prod_label": "المنتج", "target_label": "الكمية", "preform_label": "البريفورم",
        "raw_label": "خامة التغليف", "date_label": "التاريخ", "maint_header": "مركز الصيانة",
        "maint_types": ["صيانة دورية", "بلاغ عطل"], "tech_label": "الفني",
        "issue_label": "وصف العطل", "start_t": "بداية التوقف", "end_t": "نهاية الإصلاح",
        "note_label": "ملاحظات", "save_btn": "حفظ", "success_msg": "تم الحفظ",
        "eff_title": "مؤشر الكفاءة", "waste_title": "تحليل الهالك",
        "history_p": "سجل الإنتاج", "history_m": "سجل الصيانة",
        "admin_title": "لوحة التحكم - حذف السجل", "delete_btn": "حذف السجل",
        "del_success": "تم الحذف", "tools_label": "الأدوات:", "proc_label": "الإجراءات:",
        "weekend_msg": "الجمعة عطلة - لا توجد صيانات دورية", "inventory_header": "إدارة المخازن",
        "current_stock": "المخزون الحالي", "receipt": "استلام مشتريات",
        "material": "المادة", "quantity": "الكمية", "invoice": "رقم الفاتورة",
        "receipt_date": "تاريخ الاستلام", "register_receipt": "تسجيل الاستلام",
        "low_stock_alert": "مواد منخفضة", "all_good": "جميع المواد آمنة",
        "edit_stock": "تعديل الرصيد", "new_stock": "الرصيد الجديد",
        "update": "تحديث", "stock_updated": "تم التحديث", "export_btn": "تصدير",
        "dashboard_title": "لوحة القيادة الذكية", "total_production": "إجمالي الإنتاج",
        "monthly_production": "إنتاج الشهر الحالي", "line1_efficiency": "كفاءة الخط الأول",
        "line2_efficiency": "كفاءة الخط الثاني", "smart_recommendations": "التوصيات الذكية",
        "users_title": "إدارة المستخدمين", "settings_title": "إعدادات النظام",
        "backup_data": "نسخ احتياطي", "clear_cache": "مسح الذاكرة",
        "machine_select": "اختر الماكينة", "task_name": "المهمة", "done": "تم التنفيذ",
        "no_data": "لا توجد بيانات", "no_production": "لا توجد سجلات إنتاج",
        "no_maintenance": "لا توجد سجلات صيانة", "add_new_item": "إضافة صنف جديد",
        "item_id": "الرقم", "item_name": "اسم المادة", "item_unit": "الوحدة",
        "min_stock": "الحد الأدنى", "info_title": "معلومات",
        "info_text": "حفظ البيانات على هذا الجهاز فقط", "shipping": "شحن منتجات",
        "customer": "اسم العميل", "register_shipping": "تسجيل الشحن",
        "balance": "الرصيد", "in": "وارد", "out": "صادر",
        "pallet_count": "عدد الباليتات", "last_10_days": "آخر 10 أيام",
        "remember_me": "تذكرني", "clear_saved": "مسح المحفوظات",
        "auto_reorder": "توصيات إعادة الطلب التلقائي",
        "stock_prediction": "توقع نفاذ المخزون",
        "raw_balance": "رصيد المواد الخام", "fg_balance": "رصيد المنتج التام"
    },
    "en": {
        "designer": "Eng. Elsayed Oun", "login_title": "Login", "username": "Username",
        "password": "Password", "login_btn": "Login", "login_error": "Error",
        "logout": "Logout", "welcome": "Welcome", "role": "Role", "dark_mode": "Dark Mode",
        "dashboard": "🏠 Dashboard", "production": "📈 Production", "maintenance": "🔧 Maintenance",
        "records": "📊 Records", "raw_materials": "📦 Raw Materials", "finished_goods": "🏭 Finished Goods",
        "users": "👥 Users", "settings": "⚙️ Settings", "line_label": "Line",
        "sup_label": "Supervisor", "prod_label": "Product", "target_label": "Quantity",
        "preform_label": "Preforms", "raw_label": "Packaging", "date_label": "Date",
        "maint_header": "Maintenance", "maint_types": ["Planned", "Breakdown"],
        "tech_label": "Technician", "issue_label": "Issue", "start_t": "Start", "end_t": "End",
        "note_label": "Notes", "save_btn": "Save", "success_msg": "Saved",
        "eff_title": "Efficiency Indicator", "waste_title": "Waste", "history_p": "Production Logs",
        "history_m": "Maintenance Logs", "admin_title": "Admin - Delete", "delete_btn": "Delete",
        "del_success": "Deleted", "tools_label": "Tools:", "proc_label": "Procedure:",
        "weekend_msg": "Friday is weekend - No scheduled maintenance", "inventory_header": "Inventory",
        "current_stock": "Current Stock", "receipt": "Receive", "material": "Material",
        "quantity": "Quantity", "invoice": "Invoice", "receipt_date": "Date", "register_receipt": "Register",
        "low_stock_alert": "Low Stock", "all_good": "All Good", "edit_stock": "Edit Stock",
        "new_stock": "New Stock", "update": "Update", "stock_updated": "Updated", "export_btn": "Export",
        "dashboard_title": "Smart Dashboard", "total_production": "Total Production",
        "monthly_production": "Current Month Production", "line1_efficiency": "Line 1 Efficiency",
        "line2_efficiency": "Line 2 Efficiency", "smart_recommendations": "Smart Recommendations",
        "users_title": "Users", "settings_title": "Settings", "backup_data": "Backup",
        "clear_cache": "Clear Cache", "machine_select": "Select Machine", "task_name": "Task",
        "done": "Done", "no_data": "No data", "no_production": "No production records",
        "no_maintenance": "No maintenance records", "add_new_item": "Add New Item", "item_id": "ID",
        "item_name": "Name", "item_unit": "Unit", "min_stock": "Min Stock", "info_title": "Info",
        "info_text": "Data saved on this device only", "shipping": "Shipping", "customer": "Customer",
        "register_shipping": "Register Shipping", "balance": "Balance", "in": "In", "out": "Out",
        "pallet_count": "Pallets", "last_10_days": "Last 10 Days", "remember_me": "Remember me",
        "clear_saved": "Clear saved", "auto_reorder": "Auto Reorder Suggestions",
        "stock_prediction": "Stock Depletion Prediction",
        "raw_balance": "Raw Materials Balance", "fg_balance": "Finished Goods Balance"
    },
    "bn": {
        "designer": "ইঞ্জি. সাঈদ আউন", "login_title": "লগইন", "username": "ব্যবহারকারীর নাম",
        "password": "পাসওয়ার্ড", "login_btn": "লগইন", "login_error": "ভুল",
        "logout": "লগআউট", "welcome": "স্বাগতম", "role": "ভূমিকা", "dark_mode": "ডার্ক মোড",
        "dashboard": "🏠 ড্যাশবোর্ড", "production": "📈 উৎপাদন", "maintenance": "🔧 রক্ষণাবেক্ষণ",
        "records": "📊 রেকর্ড", "raw_materials": "📦 কাঁচামাল", "finished_goods": "🏭 সমাপ্ত পণ্য",
        "users": "👥 ব্যবহারকারী", "settings": "⚙️ সেটিংস", "line_label": "লাইন",
        "sup_label": "সুপারভাইজার", "prod_label": "পণ্য", "target_label": "পরিমাণ",
        "preform_label": "প্রিফর্ম", "raw_label": "প্যাকেজিং", "date_label": "তারিখ",
        "maint_header": "রক্ষণাবেক্ষণ", "maint_types": ["পরিকল্পিত", "ব্রেকডাউন"],
        "tech_label": "টেকনিশিয়ান", "issue_label": "সমস্যা", "start_t": "শুরু", "end_t": "শেষ",
        "note_label": "নোট", "save_btn": "সংরক্ষণ", "success_msg": "সংরক্ষিত",
        "eff_title": "দক্ষতা নির্দেশক", "waste_title": "বর্জ্য", "history_p": "উৎপাদন লগ",
        "history_m": "রক্ষণাবেক্ষণ লগ", "admin_title": "অ্যাডমিন - মুছুন", "delete_btn": "মুছুন",
        "del_success": "মুছে ফেলা হয়েছে", "tools_label": "সরঞ্জাম:", "proc_label": "পদ্ধতি:",
        "weekend_msg": "শুক্রবার সাপ্তাহিক ছুটি - কোন পরিকল্পিত রক্ষণাবেক্ষণ নেই", "inventory_header": "ইনভেন্টরি",
        "current_stock": "বর্তমান স্টক", "receipt": "গ্রহণ", "material": "উপাদান",
        "quantity": "পরিমাণ", "invoice": "ইনভয়েস", "receipt_date": "তারিখ", "register_receipt": "নিবন্ধন",
        "low_stock_alert": "স্বল্প স্টক", "all_good": "সব ঠিক", "edit_stock": "স্টক সম্পাদনা",
        "new_stock": "নতুন স্টক", "update": "আপডেট", "stock_updated": "আপডেট হয়েছে", "export_btn": "এক্সপোর্ট",
        "dashboard_title": "স্মার্ট ড্যাশবোর্ড", "total_production": "মোট উৎপাদন",
        "monthly_production": "বর্তমান মাসের উৎপাদন", "line1_efficiency": "লাইন ১ দক্ষতা",
        "line2_efficiency": "লাইন ২ দক্ষতা", "smart_recommendations": "স্মার্ট সুপারিশ",
        "users_title": "ব্যবহারকারী", "settings_title": "সেটিংস", "backup_data": "ব্যাকআপ",
        "clear_cache": "ক্যাশ সাফ", "machine_select": "মেশিন নির্বাচন", "task_name": "কাজ",
        "done": "সম্পন্ন", "no_data": "তথ্য নেই", "no_production": "উৎপাদন রেকর্ড নেই",
        "no_maintenance": "রক্ষণাবেক্ষণ রেকর্ড নেই", "add_new_item": "নতুন আইটেম যোগ করুন",
        "item_id": "আইডি", "item_name": "নাম", "item_unit": "ইউনিট", "min_stock": "ন্যূনতম স্টক",
        "info_title": "তথ্য", "info_text": "ডেটা শুধুমাত্র এই ডিভাইসে সংরক্ষিত",
        "shipping": "প্রেরণ", "customer": "গ্রাহক", "register_shipping": "প্রেরণ নিবন্ধন",
        "balance": "ব্যালেন্স", "in": "ইন", "out": "আউট", "pallet_count": "প্যালেট",
        "last_10_days": "শেষ ১০ দিন", "remember_me": "মনে রাখুন", "clear_saved": "সংরক্ষিত ডেটা মুছুন",
        "auto_reorder": "স্বয়ংক্রিয় অর্ডার সুপারিশ",
        "stock_prediction": "স্টক শেষ হওয়ার পূর্বাভাস",
        "raw_balance": "কাঁচামালের ব্যালেন্স", "fg_balance": "সমাপ্ত পণ্যের ব্যালেন্স"
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
# 8. تحميل البيانات
# ============================================================================
RAW_MATERIALS_FILE = "raw.xlsx"
FINISHED_GOODS_FILE = "finished_goods.xlsx"

def load_raw_materials():
    if os.path.exists(RAW_MATERIALS_FILE):
        df_raw = pd.read_excel(RAW_MATERIALS_FILE)
        for col in ["Current_Stock", "Min_Stock"]:
            if col in df_raw.columns:
                df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce').fillna(0)
        return df_raw
    return pd.DataFrame()

def update_raw_materials(df_raw):
    df_raw.to_excel(RAW_MATERIALS_FILE, index=False)
    return True

def load_finished_goods():
    if os.path.exists(FINISHED_GOODS_FILE):
        df_fg = pd.read_excel(FINISHED_GOODS_FILE)
        for col in ["In", "Out", "Balance"]:
            if col in df_fg.columns:
                df_fg[col] = pd.to_numeric(df_fg[col], errors='coerce').fillna(0)
        return df_fg
    return pd.DataFrame()

def update_finished_goods(df_fg):
    df_fg.to_excel(FINISHED_GOODS_FILE, index=False)
    return True

# ============================================================================
# 9. BOM
# ============================================================================
CONFIG = {
    "الخط الأول(smi)": {
        "products": ["200 ml Carton", "200 ml Shrink", "600 ml Carton", "1.5 L Shrink"],
        "pack_per_unit": {"200 ml Carton": 48, "200 ml Shrink": 20, "600 ml Carton": 30, "1.5 L Shrink": 6},
        "speed": {"200 ml Carton": 35000, "200 ml Shrink": 35000, "600 ml Carton": 20000, "1.5 L Shrink": 12000}
    },
    "الخط الثاني(welbing)": {
        "products": ["200 ml Carton", "200 ml Shrink", "330 ml Carton", "330 ml Shrink"],
        "pack_per_unit": {"200 ml Carton": 48, "200 ml Shrink": 20, "330 ml Carton": 40, "330 ml Shrink": 20},
        "speed": {"200 ml Carton": 40000, "200 ml Shrink": 40000, "330 ml Carton": 40000, "330 ml Shrink": 40000}
    }
}

BOM = {
    "200 ml Carton": {"بريفورم200": 48, "غطاء": 48, "ليبل 200": 48, "كرتون200": 1},
    "200 ml Shrink": {"بريفورم200": 20, "غطاء": 20, "ليبل 200": 20, "شرنك200": 0.0005},
    "600 ml Carton": {"بريفورم600": 30, "غطاء": 30, "ليبل 600": 30, "كرتون600": 1},
    "1.5 L Shrink": {"بريفورم لتر ونص": 6, "غطاء": 6, "ليبل لتر ونص": 6, "شرنك لتر ونص": 0.000625},
    "330 ml Carton": {"بريفورم330": 40, "غطاء": 40, "ليبل 330": 40, "كرتون330": 1},
    "330 ml Shrink": {"بريفورم330": 20, "غطاء": 20, "ليبل 330": 20, "شرنك330": 0.0005},
}

SHRINK_PALLET_CONFIG = {
    "200 ml Shrink": {"units_per_pallet": 180, "spacers_per_pallet": 7},
    "330 ml Shrink": {"units_per_pallet": 144, "spacers_per_pallet": 5},
    "1.5 L Shrink": {"units_per_pallet": 88, "spacers_per_pallet": 5},
}

def get_materials_required(product, quantity):
    if product not in BOM:
        return None, f"المنتج {product} غير موجود"
    required = {}
    for material, qty in BOM[product].items():
        if qty < 1:
            required[material] = math.ceil(quantity * qty)
        else:
            required[material] = qty * quantity
    if "Shrink" in product and product in SHRINK_PALLET_CONFIG:
        config = SHRINK_PALLET_CONFIG[product]
        spacers = math.ceil(quantity / config["units_per_pallet"]) * config["spacers_per_pallet"]
        if spacers > 0:
            required["فواصل شرنك"] = spacers
    return required, None

def consume_materials(product, quantity, df_raw):
    required, error = get_materials_required(product, quantity)
    if error:
        return df_raw, False, error
    shortages = []
    new_df = df_raw.copy()
    for idx, row in new_df.iterrows():
        mat_name = row["Material_Name_AR"]
        if mat_name in required:
            req = required[mat_name]
            current = float(row["Current_Stock"]) if pd.notna(row["Current_Stock"]) else 0
            if current < req:
                shortages.append(mat_name)
            else:
                new_df.at[idx, "Current_Stock"] = current - req
    if shortages:
        return df_raw, False, f"⚠️ عجز في المواد: {', '.join(shortages[:3])}"
    return new_df, True, f"✅ تم صرف المواد لـ {quantity:,.0f} وحدة"

def restore_materials(product, quantity, df_raw):
    required, error = get_materials_required(product, quantity)
    if error:
        return df_raw, False, error
    new_df = df_raw.copy()
    for idx, row in new_df.iterrows():
        mat_name = row["Material_Name_AR"]
        if mat_name in required:
            req = required[mat_name]
            current = float(row["Current_Stock"]) if pd.notna(row["Current_Stock"]) else 0
            new_df.at[idx, "Current_Stock"] = current + req
    return new_df, True, f"✅ تم إعادة المواد لـ {quantity:,.0f} وحدة"

# ============================================================================
# 10. دوال الصيانة والماكينات (مع دعم خاص للكمبروسر)
# ============================================================================
MACHINE_MAP = {
    "النفخ(blowing)": "blowing_machine.xlsx",
    "الليبل(labeling)": "labeling_machine.xlsx",
    "السيور(Conveyor)": "Conveyor_machine.xlsx",
    "الكرتون(packing)": "packing_machine.xlsx",
    "البالتايزر(paletizer)": "paletizer_machine.xlsx",
    "الشرنك(shrink)": "shrink_machine.xlsx",
    "التعبئة(filling)": "Filling_machine.xlsx",
    "كمبروسر الهواء (Air Compressor)": "AF_Compressor_Maintenance_LTR.xlsx"
}

def create_machine_file(filepath):
    if "Compressor" in filepath or "AF_Compressor" in filepath:
        # إنشاء ملف الكمبروسر بالشكل الصحيح
        sample_data = pd.DataFrame({
            "Cat": ["فحوصات يومية", "فحص التشغيل", "تنظيف وتشحيم", "تنظيف وتشحيم", 
                    "فحص ميكانيكي", "فحص ميكانيكي", "أنظمة مساعدة", "أنظمة مساعدة", 
                    "كهرباء", "صيانة متقدمة", "صيانة متقدمة", "صيانة متقدمة"],
            "No": [1, 1, 1, 2, 1, 2, 1, 2, 1, 1, 2, 3],
            "Name": ["تعبئة سجل الأداء الأسبوعي", "فحص زر التوقف الطارئ", "فحص مستوى الزيت", 
                    "استبدال أو تنظيف فلتر الزيت", "فحص شد ومحاذاة السيور", 
                    "تنظيف فلتر هواء السحب", "فحص عمل تصريف Bekomats", "تنظيف مبرد المجفف",
                    "فلتر كابينة الكهرباء", "عزم ربط أغطية الصمامات", 
                    "تشحيم رولمان بلي المحرك", "تنظيف المحرك الرئيسي"],
            "Photo": ["", "", "", "", "", "", "", "", "", "", "", ""],
            "Tools": ["قلم", "يدوي", "مقياس زيت", "مفتاح فلاتر", "مقياس شد", "هواء مضغوط", 
                     "فحص بصري", "فرشاة ناعمة", "مكنسة/هواء", "مفتاح عزم", "محقن شحم", "هواء مضغوط"],
            "Proc": ["تسجيل البيانات", "اختبار يدوي", "فحص العلامة الصحيحة", "تنظيف أو استبدال",
                     "فحص الشد والمحاذاة", "تنظيف من الأتربة", "فحص عدم الانسداد", "تنظيف الزعانف",
                     "تنظيف للتهوية", "حسب المواصفات", "شحم كافٍ", "خالٍ من العوالق"],
            "Freq": ["Daily", "Daily", "Daily", "Weekly", "Weekly", "Weekly", 
                     "Weekly", "Weekly", "Weekly", "Monthly", "Yearly", "Yearly"],
            "Stat": ["Active"] * 12,
            "Note": [""] * 12,
            "Staff": [""] * 12
        })
        sample_data.to_excel(filepath, index=False)
    else:
        sample = pd.DataFrame({
            "Cat": ["ميكانيكية", "ميكانيكية", "كهربائية", "ميكانيكية", "كهربائية"],
            "No": [1, 2, 3, 4, 5],
            "Name": ["فحص المحامل", "تنظيف الفلاتر", "معايرة الحساسات", "تشحيم الأجزاء", "فحص الأحزمة"],
            "Photo": ["", "", "", "", ""],
            "Tools": ["مفتاح ربط", "فرشاة + هواء", "جهاز معايرة", "شحم", "مفتاح ربط"],
            "Proc": ["فحص الاهتزازات", "تنظيف بالهواء", "معايرة حسب الدليل", "تشحيم كل 100 ساعة", "فحص الشد"],
            "Freq": ["Daily", "Daily", "Weekly", "Weekly", "Monthly"],
            "Stat": ["Active"] * 5, "Note": [""] * 5, "Staff": [""] * 5
        })
        sample.to_excel(filepath, index=False)

def find_image_path(photo_name):
    if not photo_name or pd.isna(photo_name) or photo_name == "":
        return None
    possible_paths = [photo_name, os.path.join("images", photo_name), os.path.join("images", os.path.basename(photo_name))]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def get_scheduled_tasks(df_tasks):
    today = datetime.now()
    day_name = today.strftime('%A')
    is_first_of_month = (today.day == 1)
    
    # تحديد عمود التردد
    freq_col = None
    if 'Freq' in df_tasks.columns:
        freq_col = 'Freq'
    elif 'Frequency' in df_tasks.columns:
        freq_col = 'Frequency'
    else:
        return pd.DataFrame()
    
    # الجمعة: لا مهام
    if day_name == 'Friday':
        return pd.DataFrame()
    
    # تحديد الترددات المطلوبة
    allowed_freqs = ['Daily']
    
    # السبت: نضيف التردد الأسبوعي
    if day_name == 'Saturday':
        allowed_freqs.append('Weekly')
    
    # أول الشهر: نضيف الترددات الشهرية والسنوية
    if is_first_of_month:
        allowed_freqs.append('Monthly')
        allowed_freqs.append('1000h')
        allowed_freqs.append('Yearly')
    
    # تحويل التردد 4 months إلى Monthly
    df_tasks[freq_col] = df_tasks[freq_col].astype(str)
    df_tasks[freq_col] = df_tasks[freq_col].replace('4 months', 'Monthly')
    
    # تصفية المهام (مع معالجة القيم الفارغة)
    df_tasks_filtered = df_tasks[df_tasks[freq_col].notna()]
    result = df_tasks_filtered[df_tasks_filtered[freq_col].isin(allowed_freqs)]
    
    return result.reset_index(drop=True)

# ============================================================================
# 11. التوصيات الذكية وشريط البيانات المتحرك
# ============================================================================
def get_auto_reorder_suggestions(df_raw, df_main):
    suggestions = []
    if df_main is None or df_main.empty:
        return suggestions
    
    prod_df = df_main[df_main['Type'] == 'Production'].copy()
    if not prod_df.empty and 'Date' in prod_df.columns:
        prod_df['Date'] = pd.to_datetime(prod_df['Date'])
        last_30_days = prod_df[prod_df['Date'] >= datetime.now() - timedelta(days=30)]
        if not last_30_days.empty:
            for _, row in df_raw.iterrows():
                current = row['Current_Stock']
                min_stock = row['Min_Stock']
                if current <= min_stock:
                    suggested_qty = int(min_stock * 2 - current) if current < min_stock else int(min_stock)
                    if suggested_qty < 0:
                        suggested_qty = int(min_stock)
                    urgency = "high" if current < min_stock / 2 else "medium"
                    suggestions.append({
                        "material": row['Material_Name_AR'],
                        "current": int(current),
                        "min_stock": int(min_stock),
                        "suggested_qty": suggested_qty,
                        "urgency": urgency
                    })
    return suggestions

def get_stock_prediction(df_raw, df_main):
    predictions = []
    if df_main is None or df_main.empty:
        return predictions
    
    prod_df = df_main[df_main['Type'] == 'Production'].copy()
    if not prod_df.empty and 'Date' in prod_df.columns:
        prod_df['Date'] = pd.to_datetime(prod_df['Date'])
        last_30_days = prod_df[prod_df['Date'] >= datetime.now() - timedelta(days=30)]
        if not last_30_days.empty:
            daily_prod = last_30_days['Output_Units'].mean()
            for _, row in df_raw.iterrows():
                current = row['Current_Stock']
                if current > 0 and daily_prod > 0:
                    days_left = current / (daily_prod * 0.05)
                    if days_left < 30:
                        predictions.append({
                            "material": row['Material_Name_AR'],
                            "current": int(current),
                            "days_left": round(days_left, 1),
                            "status": "critical" if days_left < 7 else "warning" if days_left < 14 else "info"
                        })
    return predictions

def get_marquee_recommendations(df_raw, df_main, df_fg, t, lang):
    recommendations = []
    
    reorder = get_auto_reorder_suggestions(df_raw, df_main)
    for rec in reorder[:3]:
        if rec["urgency"] == "high":
            if lang == "ar":
                recommendations.append(f"🔴 {t['auto_reorder']}: {rec['material']} - الرصيد {rec['current']:,}")
            elif lang == "en":
                recommendations.append(f"🔴 {t['auto_reorder']}: {rec['material']} - Stock {rec['current']:,}")
            else:
                recommendations.append(f"🔴 {t['auto_reorder']}: {rec['material']} - স্টক {rec['current']:,}")
        else:
            if lang == "ar":
                recommendations.append(f"🟡 {t['auto_reorder']}: {rec['material']} - الكمية المقترحة {rec['suggested_qty']:,}")
            elif lang == "en":
                recommendations.append(f"🟡 {t['auto_reorder']}: {rec['material']} - Suggested {rec['suggested_qty']:,}")
            else:
                recommendations.append(f"🟡 {t['auto_reorder']}: {rec['material']} - প্রস্তাবিত {rec['suggested_qty']:,}")
    
    stock_pred = get_stock_prediction(df_raw, df_main)
    for pred in stock_pred[:3]:
        if pred["status"] == "critical":
            if lang == "ar":
                recommendations.append(f"⚠️ {t['stock_prediction']}: {pred['material']} سينفذ خلال {pred['days_left']} يوم")
            elif lang == "en":
                recommendations.append(f"⚠️ {t['stock_prediction']}: {pred['material']} will run out in {pred['days_left']} days")
            else:
                recommendations.append(f"⚠️ {t['stock_prediction']}: {pred['material']} {pred['days_left']} দিনের মধ্যে শেষ হবে")
        elif pred["status"] == "warning":
            if lang == "ar":
                recommendations.append(f"📦 {t['stock_prediction']}: {pred['material']} سينفذ خلال {pred['days_left']} يوم")
            elif lang == "en":
                recommendations.append(f"📦 {t['stock_prediction']}: {pred['material']} will run out in {pred['days_left']} days")
            else:
                recommendations.append(f"📦 {t['stock_prediction']}: {pred['material']} {pred['days_left']} দিনের মধ্যে শেষ হবে")
    
    if not df_fg.empty and "Balance" in df_fg.columns:
        fg_balance = df_fg["Balance"].sum()
        if fg_balance <= 0:
            if lang == "ar":
                recommendations.append(f"🏭 {t['fg_balance']}: فارغ - يرجى زيادة الإنتاج")
            elif lang == "en":
                recommendations.append(f"🏭 {t['fg_balance']}: Empty - Please increase production")
            else:
                recommendations.append(f"🏭 {t['fg_balance']}: খালি - উৎপাদন বাড়ান")
        elif fg_balance < 10000:
            if lang == "ar":
                recommendations.append(f"📦 {t['fg_balance']}: {fg_balance:,.0f} وحدة")
            elif lang == "en":
                recommendations.append(f"📦 {t['fg_balance']}: {fg_balance:,.0f} units")
            else:
                recommendations.append(f"📦 {t['fg_balance']}: {fg_balance:,.0f} ইউনিট")
    
    if not recommendations:
        if lang == "ar":
            recommendations.append(f"✅ {t['all_good']} ✅")
        elif lang == "en":
            recommendations.append(f"✅ {t['all_good']} ✅")
        else:
            recommendations.append(f"✅ {t['all_good']} ✅")
    
    return recommendations

def show_marquee(df_raw, df_main, df_fg, t, lang):
    recommendations = get_marquee_recommendations(df_raw, df_main, df_fg, t, lang)
    
    marquee_content = ""
    for rec in recommendations:
        if "🔴" in rec or "⚠️" in rec:
            marquee_content += f'<span class="critical">{rec}</span>'
        elif "🟡" in rec or "📦" in rec:
            marquee_content += f'<span class="warning">{rec}</span>'
        elif "🏭" in rec:
            marquee_content += f'<span class="info">{rec}</span>'
        else:
            marquee_content += f'<span class="success">{rec}</span>'
    
    st.markdown(f"""
    <div class="marquee">
        <div class="marquee-content">
            {marquee_content}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# 12. لوحة القيادة
# ============================================================================
def show_dashboard(df_main, df_raw, df_fg, t):
    lang = st.session_state.get('lang', 'ar')
    
    st.markdown('<h1 class="gradient-title">🏭 BIRMA - ' + t["dashboard_title"] + '</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    show_marquee(df_raw, df_main, df_fg, t, lang)
    
    total_prod = 0
    monthly_prod = 0
    line1_efficiency = 0
    line2_efficiency = 0
    line1_count = 0
    line2_count = 0
    
    if df_main is not None and not df_main.empty:
        prod_df = df_main[df_main['Type'] == 'Production']
        if not prod_df.empty:
            total_prod = int(prod_df['Output_Units'].sum()) if 'Output_Units' in prod_df.columns else 0
            if 'Date' in prod_df.columns:
                prod_df['Date'] = pd.to_datetime(prod_df['Date'])
                current_year = datetime.now().year
                current_month = datetime.now().month
                monthly_prod_df = prod_df[(prod_df['Date'].dt.year == current_year) & (prod_df['Date'].dt.month == current_month)]
                monthly_prod = int(monthly_prod_df['Output_Units'].sum()) if not monthly_prod_df.empty else 0
            
            if 'Line' in prod_df.columns and 'Efficiency_%' in prod_df.columns:
                line1_data = prod_df[prod_df['Line'] == "الخط الأول(smi)"]
                line2_data = prod_df[prod_df['Line'] == "الخط الثاني(welbing)"]
                if not line1_data.empty:
                    line1_efficiency = round(line1_data['Efficiency_%'].mean(), 1)
                    line1_count = len(line1_data)
                if not line2_data.empty:
                    line2_efficiency = round(line2_data['Efficiency_%'].mean(), 1)
                    line2_count = len(line2_data)
    
    fg_balance = int(df_fg["Balance"].sum()) if not df_fg.empty and "Balance" in df_fg.columns else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size: 1.2rem; opacity: 0.8;">🏭 {t['total_production']}</div>
            <div style="font-size: 3rem; font-weight: bold; color: #667eea;">{total_prod:,}</div>
            <div style="font-size: 0.8rem;">{t['no_data'] if total_prod == 0 else ''}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size: 1.2rem; opacity: 0.8;">📅 {t['monthly_production']}</div>
            <div style="font-size: 3rem; font-weight: bold; color: #f59e0b;">{monthly_prod:,}</div>
            <div style="font-size: 0.8rem;">{datetime.now().strftime('%B %Y')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="glass-card">
            <div style="font-size: 1.2rem; opacity: 0.8;">🏭 {t['fg_balance']}</div>
            <div style="font-size: 3rem; font-weight: bold; color: #10b981;">{fg_balance:,}</div>
            <div style="font-size: 0.8rem;">{t['balance']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.subheader("⚡ " + t["eff_title"])
    col1, col2 = st.columns(2)
    
    with col1:
        color1 = "#22c55e" if line1_efficiency >= 80 else "#eab308" if line1_efficiency >= 60 else "#ef4444"
        st.markdown(f"""
        <div class="gauge-container">
            <h3>{t['line1_efficiency']}</h3>
            <div style="position: relative; width: 180px; height: 180px; margin: auto;">
                <svg width="180" height="180" viewBox="0 0 180 180">
                    <circle cx="90" cy="90" r="78" fill="none" stroke="#e5e7eb" stroke-width="14"/>
                    <circle cx="90" cy="90" r="78" fill="none" stroke="{color1}" stroke-width="14" 
                            stroke-dasharray="{2 * math.pi * 78 * max(0, min(100, line1_efficiency)) / 100} {2 * math.pi * 78}"
                            stroke-dashoffset="{2 * math.pi * 78 * 0.25}" transform="rotate(-90 90 90)"/>
                    <text x="90" y="95" text-anchor="middle" font-size="28" font-weight="bold" fill="{color1}">{line1_efficiency}%</text>
                    <text x="90" y="118" text-anchor="middle" font-size="14">{t['eff_title']}</text>
                </svg>
            </div>
            <small>{t['records']}: {line1_count}</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        color2 = "#22c55e" if line2_efficiency >= 80 else "#eab308" if line2_efficiency >= 60 else "#ef4444"
        st.markdown(f"""
        <div class="gauge-container">
            <h3>{t['line2_efficiency']}</h3>
            <div style="position: relative; width: 180px; height: 180px; margin: auto;">
                <svg width="180" height="180" viewBox="0 0 180 180">
                    <circle cx="90" cy="90" r="78" fill="none" stroke="#e5e7eb" stroke-width="14"/>
                    <circle cx="90" cy="90" r="78" fill="none" stroke="{color2}" stroke-width="14" 
                            stroke-dasharray="{2 * math.pi * 78 * max(0, min(100, line2_efficiency)) / 100} {2 * math.pi * 78}"
                            stroke-dashoffset="{2 * math.pi * 78 * 0.25}" transform="rotate(-90 90 90)"/>
                    <text x="90" y="95" text-anchor="middle" font-size="28" font-weight="bold" fill="{color2}">{line2_efficiency}%</text>
                    <text x="90" y="118" text-anchor="middle" font-size="14">{t['eff_title']}</text>
                </svg>
            </div>
            <small>{t['records']}: {line2_count}</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("📦 " + t["raw_balance"])
        if not df_raw.empty:
            raw_chart = df_raw.nlargest(10, "Current_Stock")[["Material_Name_AR", "Current_Stock"]].copy()
            if lang == "ar":
                raw_chart = raw_chart.rename(columns={"Material_Name_AR": "المادة", "Current_Stock": "الكمية"})
                title_text = "أرصدة المواد الخام"
                x_col = "المادة"
                y_col = "الكمية"
            elif lang == "en":
                raw_chart = raw_chart.rename(columns={"Material_Name_AR": "Material", "Current_Stock": "Quantity"})
                title_text = "Raw Materials Balance"
                x_col = "Material"
                y_col = "Quantity"
            else:
                raw_chart = raw_chart.rename(columns={"Material_Name_AR": "উপাদান", "Current_Stock": "পরিমাণ"})
                title_text = "কাঁচামালের ব্যালেন্স"
                x_col = "উপাদান"
                y_col = "পরিমাণ"
            
            fig_raw = px.bar(raw_chart, x=x_col, y=y_col, title=title_text,
                             color=y_col, color_continuous_scale="Blues", text=y_col)
            fig_raw.update_traces(textposition='outside')
            fig_raw.update_layout(height=450)
            st.plotly_chart(fig_raw, use_container_width=True)
        else:
            st.info(t["no_data"] if lang == "ar" else "No data" if lang == "en" else "তথ্য নেই")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("🏭 " + t["fg_balance"])
        if not df_fg.empty:
            fg_chart = df_fg[["Name", "Balance"]].copy()
            if lang == "ar":
                fg_chart = fg_chart.rename(columns={"Name": "المنتج", "Balance": "الرصيد"})
                title_text = "أرصدة المنتجات التامة"
                x_col = "المنتج"
                y_col = "الرصيد"
            elif lang == "en":
                fg_chart = fg_chart.rename(columns={"Name": "Product", "Balance": "Balance"})
                title_text = "Finished Goods Balance"
                x_col = "Product"
                y_col = "Balance"
            else:
                fg_chart = fg_chart.rename(columns={"Name": "পণ্য", "Balance": "ব্যালেন্স"})
                title_text = "সমাপ্ত পণ্যের ব্যালেন্স"
                x_col = "পণ্য"
                y_col = "ব্যালেন্স"
            
            fig_fg = px.bar(fg_chart, x=x_col, y=y_col, title=title_text,
                            color=y_col, color_continuous_scale="Greens", text=y_col)
            fig_fg.update_traces(textposition='outside')
            fig_fg.update_layout(height=450)
            st.plotly_chart(fig_fg, use_container_width=True)
        else:
            st.info(t["no_data"] if lang == "ar" else "No data" if lang == "en" else "তথ্য নেই")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.subheader("🤖 " + t["smart_recommendations"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        reorder = get_auto_reorder_suggestions(df_raw, df_main)
        if reorder:
            st.markdown("#### 📦 " + t["auto_reorder"])
            for rec in reorder[:3]:
                if rec["urgency"] == "high":
                    if lang == "ar":
                        st.error(f"🔴 **{rec['material']}** : الرصيد {rec['current']:,} (الحد الأدنى {rec['min_stock']:,})")
                        st.warning(f"   ➕ اقتراح إعادة طلب: {rec['suggested_qty']:,}")
                    elif lang == "en":
                        st.error(f"🔴 **{rec['material']}** : Stock {rec['current']:,} (Min {rec['min_stock']:,})")
                        st.warning(f"   ➕ Suggested reorder: {rec['suggested_qty']:,}")
                    else:
                        st.error(f"🔴 **{rec['material']}** : স্টক {rec['current']:,} (ন্যূনতম {rec['min_stock']:,})")
                        st.warning(f"   ➕ প্রস্তাবিত অর্ডার: {rec['suggested_qty']:,}")
                else:
                    if lang == "ar":
                        st.warning(f"🟡 **{rec['material']}** : الرصيد {rec['current']:,} (الحد الأدنى {rec['min_stock']:,})")
                        st.info(f"   ➕ اقتراح إعادة طلب: {rec['suggested_qty']:,}")
                    elif lang == "en":
                        st.warning(f"🟡 **{rec['material']}** : Stock {rec['current']:,} (Min {rec['min_stock']:,})")
                        st.info(f"   ➕ Suggested reorder: {rec['suggested_qty']:,}")
                    else:
                        st.warning(f"🟡 **{rec['material']}** : স্টক {rec['current']:,} (ন্যূনতম {rec['min_stock']:,})")
                        st.info(f"   ➕ প্রস্তাবিত অর্ডার: {rec['suggested_qty']:,}")
        else:
            if lang == "ar":
                st.success("✅ لا توجد مواد تحتاج إعادة طلب حالياً")
            elif lang == "en":
                st.success("✅ No materials need reordering")
            else:
                st.success("✅ কোনো উপাদানের পুনর্বিন্যাস প্রয়োজন নেই")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        stock_pred = get_stock_prediction(df_raw, df_main)
        if stock_pred:
            st.markdown("#### ⏰ " + t["stock_prediction"])
            for pred in stock_pred[:3]:
                if pred["status"] == "critical":
                    if lang == "ar":
                        st.error(f"🔴 **{pred['material']}** : سينفذ خلال {pred['days_left']} يوم")
                    elif lang == "en":
                        st.error(f"🔴 **{pred['material']}** : Will run out in {pred['days_left']} days")
                    else:
                        st.error(f"🔴 **{pred['material']}** : {pred['days_left']} দিনের মধ্যে শেষ হয়ে যাবে")
                elif pred["status"] == "warning":
                    if lang == "ar":
                        st.warning(f"🟡 **{pred['material']}** : سينفذ خلال {pred['days_left']} يوم")
                    elif lang == "en":
                        st.warning(f"🟡 **{pred['material']}** : Will run out in {pred['days_left']} days")
                    else:
                        st.warning(f"🟡 **{pred['material']}** : {pred['days_left']} দিনের মধ্যে শেষ হয়ে যাবে")
                else:
                    if lang == "ar":
                        st.info(f"ℹ️ **{pred['material']}** : سينفذ خلال {pred['days_left']} يوم")
                    elif lang == "en":
                        st.info(f"ℹ️ **{pred['material']}** : Will run out in {pred['days_left']} days")
                    else:
                        st.info(f"ℹ️ **{pred['material']}** : {pred['days_left']} দিনের মধ্যে শেষ হয়ে যাবে")
        else:
            if lang == "ar":
                st.success("✅ جميع المواد فوق الحد الآمن")
            elif lang == "en":
                st.success("✅ All materials above safe level")
            else:
                st.success("✅ সমস্ত উপাদান নিরাপদ সীমার উপরে")
        st.markdown('</div>', unsafe_allow_html=True)

# ============================================================================
# 13. واجهة تسجيل الدخول
# ============================================================================
def login_screen(t):
    saved_user, saved_pass, _ = load_credentials_local()
    
    if saved_user and saved_pass:
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
            username = st.text_input(t["username"])
            password = st.text_input(t["password"], type="password")
            remember = st.checkbox(t["remember_me"])
            
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

# ============================================================================
# 14. الواجهة الرئيسية
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
    
    st.sidebar.markdown(f"<p style='text-align: center; font-size: 12px; color: #aaa; margin-bottom: 0;'>Designed by:</p>", unsafe_allow_html=True)
    st.sidebar.markdown(f"<h4 style='text-align: center; color: #f59e0b; margin-top: 0;'>{LANG[st.session_state.lang]['designer']}</h4>", unsafe_allow_html=True)
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
                            new_row = pd.DataFrame([{
                                "Type": "Production", "Date": str(p_date), "Line": selected_line,
                                "Supervisor": name, "Product": product, "Output_Units": int(target),
                                "Preforms_Used": int(preforms), "Efficiency_%": float(eff),
                                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }])
                            if conn:
                                if df_main.empty:
                                    save_to_sheet(conn, new_row)
                                else:
                                    save_to_sheet(conn, pd.concat([df_main, new_row], ignore_index=True))
                            
                            # إضافة المنتج التام
                            fg_name = "Cartoon 200 ml" if "Carton" in product else "Shrink 200 ml"
                            if "330" in product:
                                fg_name = "Cartoon 330 ml" if "Carton" in product else "Shrink 330 ml"
                            elif "600" in product:
                                fg_name = "Cartoon 600 ml"
                            elif "1.5" in product:
                                fg_name = "1.5 Ltr"
                            
                            idx = df_fg[df_fg["Name"] == fg_name].index
                            if len(idx) > 0:
                                df_fg.at[idx[0], "In"] += target
                                df_fg.at[idx[0], "Balance"] += target
                                update_finished_goods(df_fg)
                            
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
            
            # ========== قراءة ملف الصيانة (مع دعم خاص للكمبروسر) ==========
           
            if "Compressor" in path or "AF_Compressor" in path:
                # ملف الكمبروسر له هيكل خاص
                try:
                    # قراءة الملف مع تحديد الصف الذي يحتوي على أسماء الأعمدة
                    # الصف الثالث (index 2) يحتوي على أسماء الأعمدة
                    df_tasks = pd.read_excel(path, header=2)
        
                    # إعادة تسمية الأعمدة إلى الأسماء المطلوبة
                    column_mapping = {
                       'cat': 'Cat', 'no': 'No', 'name': 'Name', 'photo': 'Photo',
                       'tools': 'Tools', 'proc': 'Proc', 'freq': 'Freq',
                        'stat': 'Stat', 'note': 'Note', 'staff': 'Staff'
                   }
        
                   # إعادة تسمية الأعمدة الموجودة فقط
                    for old, new in column_mapping.items():
                       if old in df_tasks.columns:
                          df_tasks = df_tasks.rename(columns={old: new})
        
                       # حذف أي أعمدة إضافية غير مطلوبة
                    required_cols = ['Cat', 'No', 'Name', 'Photo', 'Tools', 'Proc', 'Freq', 'Stat', 'Note', 'Staff']
                    for col in df_tasks.columns:
                       if col not in required_cols:
                           df_tasks = df_tasks.drop(columns=[col])
        
                    # إضافة الأعمدة المفقودة
                    for col in required_cols:
                        if col not in df_tasks.columns:
                           df_tasks[col] = ''
        
                    # حذف الصفوف الفارغة
                    df_tasks = df_tasks.dropna(subset=['Name'], how='all')
                    df_tasks = df_tasks[df_tasks['Name'].notna()]
                    df_tasks = df_tasks.reset_index(drop=True)
        
                except Exception as e:
                 st.error(f"خطأ في قراءة ملف الكمبروسر: {e}")
                 df_tasks = pd.DataFrame()
            else:
                # الملفات العادية
                try:
                    df_tasks = pd.read_excel(path, skiprows=2)
                    df_tasks.columns = ['Cat', 'No', 'Name', 'Photo', 'Tools', 'Proc', 'Freq', 'Stat', 'Note', 'Staff']
                except:
                    df_tasks = pd.read_excel(path)
                    if 'Freq' not in df_tasks.columns and 'Frequency' in df_tasks.columns:
                        df_tasks = df_tasks.rename(columns={'Frequency': 'Freq'})
                    if 'Name' not in df_tasks.columns and 'Task' in df_tasks.columns:
                        df_tasks = df_tasks.rename(columns={'Task': 'Name'})
            
            # تصفية المهام حسب اليوم
            tasks = get_scheduled_tasks(df_tasks)
            
            if tasks.empty:
                if datetime.now().strftime('%A') == 'Friday':
                    st.warning(t["weekend_msg"])
                else:
                    st.info(f"📋 لا توجد مهام صيانة {t['maint_types'][0].lower()} لهذا اليوم")
            else:
                with st.form("m_form"):
                    tech = st.text_input(t["tech_label"])
                    recs = []
                    for i, r in tasks.iterrows():
                        task_name = r.get('Name', f'مهمة {i+1}')
                        with st.expander(f"🔧 {task_name} ({r.get('Freq', 'N/A')})"):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.markdown(f"**{t['tools_label']}** {r.get('Tools', 'N/A')}")
                                st.info(f"**{t['proc_label']}**\n{r.get('Proc', 'N/A')}")
                                note = st.text_input(t["note_label"], key=f"note_{i}")
                            with col2:
                                photo_name = r.get('Photo', '') if pd.notna(r.get('Photo', '')) else ""
                                img_path = find_image_path(photo_name)
                                if img_path:
                                    st.image(img_path, use_container_width=True)
                                elif photo_name:
                                    st.caption(f"📷 {photo_name}")
                                else:
                                    st.caption("📷 لا توجد صورة")
                                done = st.checkbox(t["done"], key=f"done_{i}")
                            if done:
                                recs.append({
                                    "Type": "Maintenance_Planned",
                                    "Line": selected_line,
                                    "Date": str(datetime.now().date()),
                                    "Machine": machine,
                                    "Task": task_name,
                                    "Technician": tech,
                                    "Notes": note,
                                    "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                })
                    if st.form_submit_button(t["save_btn"]):
                        if recs:
                            new_df = pd.DataFrame(recs)
                            if conn:
                                if df_main.empty:
                                    save_to_sheet(conn, new_df)
                                else:
                                    save_to_sheet(conn, pd.concat([df_main, new_df], ignore_index=True))
                        st.success(t["success_msg"])
                        st.rerun()
        else:
            # بلاغ عطل
            with st.form("break_form"):
                tech = st.text_input(t["tech_label"])
                issue = st.text_area(t["issue_label"])
                t1 = st.time_input(t["start_t"])
                t2 = st.time_input(t["end_t"])
                notes = st.text_area(t["note_label"])
                if st.form_submit_button(t["save_btn"]):
                    new_b = pd.DataFrame([{
                        "Type": "Maintenance_Breakdown",
                        "Line": selected_line,
                        "Date": str(datetime.now().date()),
                        "Machine": machine,
                        "Technician": tech,
                        "Issue": issue,
                        "Start_Time": t1.strftime("%H:%M"),
                        "End_Time": t2.strftime("%H:%M"),
                        "Notes": notes,
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }])
                    if conn:
                        if df_main.empty:
                            save_to_sheet(conn, new_b)
                        else:
                            save_to_sheet(conn, pd.concat([df_main, new_b], ignore_index=True))
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
                        display_cols = ['Date', 'Line', 'Supervisor', 'Product', 'Output_Units', 'Preforms_Used', 'Efficiency_%']
                        available_cols = [col for col in display_cols if col in prod_logs_last10.columns]
                        display_df = prod_logs_last10[available_cols].copy()
                        if lang == "ar":
                            display_df = display_df.rename(columns={
                                'Date': 'التاريخ', 'Line': 'الخط', 'Supervisor': 'المشرف',
                                'Product': 'المنتج', 'Output_Units': 'الكمية', 'Preforms_Used': 'البريفورم المستخدم',
                                'Efficiency_%': 'الكفاءة'
                            })
                        elif lang == "en":
                            display_df = display_df.rename(columns={
                                'Date': 'Date', 'Line': 'Line', 'Supervisor': 'Supervisor',
                                'Product': 'Product', 'Output_Units': 'Quantity', 'Preforms_Used': 'Preforms Used',
                                'Efficiency_%': 'Efficiency'
                            })
                        else:
                            display_df = display_df.rename(columns={
                                'Date': 'তারিখ', 'Line': 'লাইন', 'Supervisor': 'সুপারভাইজার',
                                'Product': 'পণ্য', 'Output_Units': 'পরিমাণ', 'Preforms_Used': 'প্রিফর্ম ব্যবহৃত',
                                'Efficiency_%': 'দক্ষতা'
                            })
                        st.dataframe(display_df, use_container_width=True)
                        if lang == "ar":
                            st.caption(f"📊 عرض {len(prod_logs_last10)} سجل إنتاج من آخر 10 أيام")
                        elif lang == "en":
                            st.caption(f"📊 Showing {len(prod_logs_last10)} production records from last 10 days")
                        else:
                            st.caption(f"📊 শেষ ১০ দিনের {len(prod_logs_last10)}টি উৎপাদন রেকর্ড দেখাচ্ছে")
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
                        if lang == "ar":
                            display_df = maint_logs_last10[['Date', 'Type', 'Machine', 'Technician', 'Task', 'Notes']].copy()
                            display_df = display_df.rename(columns={
                                'Date': 'التاريخ', 'Type': 'النوع', 'Machine': 'الماكينة',
                                'Technician': 'الفني', 'Task': 'المهمة', 'Notes': 'ملاحظات'
                            })
                        elif lang == "en":
                            display_df = maint_logs_last10[['Date', 'Type', 'Machine', 'Technician', 'Task', 'Notes']].copy()
                            display_df = display_df.rename(columns={
                                'Date': 'Date', 'Type': 'Type', 'Machine': 'Machine',
                                'Technician': 'Technician', 'Task': 'Task', 'Notes': 'Notes'
                            })
                        else:
                            display_df = maint_logs_last10[['Date', 'Type', 'Machine', 'Technician', 'Task', 'Notes']].copy()
                            display_df = display_df.rename(columns={
                                'Date': 'তারিখ', 'Type': 'ধরন', 'Machine': 'মেশিন',
                                'Technician': 'টেকনিশিয়ান', 'Task': 'কাজ', 'Notes': 'নোট'
                            })
                        st.dataframe(display_df, use_container_width=True)
                        if lang == "ar":
                            st.caption(f"📊 عرض {len(maint_logs_last10)} سجل صيانة من آخر 10 أيام")
                        elif lang == "en":
                            st.caption(f"📊 Showing {len(maint_logs_last10)} maintenance records from last 10 days")
                        else:
                            st.caption(f"📊 শেষ ১০ দিনের {len(maint_logs_last10)}টি রক্ষণাবেক্ষণ রেকর্ড দেখাচ্ছে")
                    else:
                        st.info(t["no_maintenance"])
                else:
                    st.info(t["no_maintenance"])
        else:
            st.info(t["no_data"])
    
    # ========== Raw Materials ==========
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
                            
                            receipt_record = pd.DataFrame([{
                                "Type": "Raw_Receipt", "Date": str(receipt_date),
                                "Material": material, "Quantity": qty, "Invoice": invoice_no,
                                "Notes": notes, "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }])
                            if conn:
                                if df_main.empty:
                                    save_to_sheet(conn, receipt_record)
                                else:
                                    save_to_sheet(conn, pd.concat([df_main, receipt_record], ignore_index=True))
                            
                            send_telegram(f"📥 استلام مواد خام: {material} - {qty:,.0f} - فاتورة: {invoice_no}")
                            st.success(f"✅ تم استلام {qty:,.0f} من {material}\n📄 رقم الفاتورة: {invoice_no}")
                            st.rerun()
        else:
            st.warning("لا توجد بيانات مخزون")
    
    # ========== Finished Goods ==========
    elif selected_raw == "🏭 Finished Goods":
        st.header(t["finished_goods"])
        
        if not df_fg.empty:
            display_df = df_fg[['Name', 'In', 'Out', 'Balance', 'Unit']].copy()
            if lang == "ar":
                display_df = display_df.rename(columns={'Name': 'المنتج', 'In': t['in'], 'Out': t['out'], 'Balance': t['balance'], 'Unit': 'الوحدة'})
            elif lang == "en":
                display_df = display_df.rename(columns={'Name': 'Product', 'In': t['in'], 'Out': t['out'], 'Balance': t['balance'], 'Unit': 'Unit'})
            else:
                display_df = display_df.rename(columns={'Name': 'পণ্য', 'In': t['in'], 'Out': t['out'], 'Balance': t['balance'], 'Unit': 'ইউনিট'})
            st.dataframe(display_df, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(t['in'], f"{df_fg['In'].sum():,.0f}")
            with col2:
                st.metric(t['out'], f"{df_fg['Out'].sum():,.0f}")
            with col3:
                st.metric(t['balance'], f"{df_fg['Balance'].sum():,.0f}")
        else:
            st.warning("لا توجد بيانات في مخزن الإنتاج التام")
    
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
                            return f"📦 {t['production']} | {row['Date']} | {row.get('Product', 'N/A')} | {row.get('Output_Units', 0)} {t['quantity']}"
                        return f"🔧 {t['maintenance']} | {row['Date']} | {row.get('Machine', 'N/A')}"
                    df_display['desc'] = df_display.apply(fmt, axis=1)
                    selected_idx = st.selectbox("اختر السجل", options=df_display.index, format_func=lambda x: df_display.loc[x, 'desc'])
                    selected_row = df_main.loc[selected_idx]
                    
                    if st.button("🗑️ " + t["delete_btn"], use_container_width=True):
                        if selected_row['Type'] == 'Production':
                            product_name = selected_row['Product']
                            quantity = selected_row['Output_Units']
                            
                            new_raw, raw_ok, raw_msg = restore_materials(product_name, quantity, df_raw)
                            if raw_ok:
                                update_raw_materials(new_raw)
                                st.info(f"🔄 {raw_msg}")
                            
                            if not df_fg.empty:
                                fg_name = "Cartoon 200 ml" if "Carton" in product_name else "Shrink 200 ml"
                                if "330" in product_name:
                                    fg_name = "Cartoon 330 ml" if "Carton" in product_name else "Shrink 330 ml"
                                elif "600" in product_name:
                                    fg_name = "Cartoon 600 ml"
                                elif "1.5" in product_name:
                                    fg_name = "1.5 Ltr"
                                
                                idx = df_fg[df_fg["Name"] == fg_name].index
                                if len(idx) > 0:
                                    df_fg.at[idx[0], "In"] = max(0, df_fg.at[idx[0], "In"] - quantity)
                                    df_fg.at[idx[0], "Balance"] = max(0, df_fg.at[idx[0], "Balance"] - quantity)
                                    update_finished_goods(df_fg)
                                    st.info(f"🔄 تم حذف {quantity:,.0f} وحدة من المنتج التام")
                            
                            df_main_updated = df_main.drop(selected_idx)
                            if conn and save_to_sheet(conn, df_main_updated):
                                st.success(f"✅ تم حذف سجل الإنتاج واستعادة المواد")
                                st.rerun()
                            else:
                                st.error("فشل في حفظ التعديلات")
                        else:
                            df_main_updated = df_main.drop(selected_idx)
                            if conn and save_to_sheet(conn, df_main_updated):
                                st.success(t["del_success"])
                                st.rerun()
                            else:
                                st.error("فشل في حفظ التعديلات")
    
    st.sidebar.divider()
    st.sidebar.markdown(f"<center><small>BIRMA v16.0<br>{t['designer']}</small></center>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()