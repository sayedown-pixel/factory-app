import streamlit as st
import pandas as pd
import os
import requests
import urllib.parse
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import plotly.graph_objects as go
import plotly.express as px
import math
import time

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="BIRMA Integrated System", page_icon="🏭", layout="wide")

# --- 2. دالة عرض التاريخ ---
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

# --- 3. تهيئة حالة الجلسة ---
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

# --- 4. نظام المستخدمين والأدوار ---
USERS = {
    "admin": {"password": "admin123", "role": "admin", "name": "مدير النظام", "icon": "👑"},
    "supervisor": {"password": "sup456", "role": "supervisor", "name": "مشرف إنتاج", "icon": "👔"},
    "technician": {"password": "tech789", "role": "technician", "name": "فني صيانة", "icon": "🔧"},
    "storekeeper": {"password": "store001", "role": "storekeeper", "name": "أمين مخزن", "icon": "📦"},
    "quality": {"password": "quality123", "role": "quality", "name": "مراقب جودة", "icon": "🔍"}
}

ROLE_PERMISSIONS = {
    "admin": ["🏠 Dashboard", "📈 Production", "🔧 Maintenance", "📊 Records", "📦 Inventory", "👥 Users", "⚙️ Settings"],
    "supervisor": ["🏠 Dashboard", "📈 Production", "🔧 Maintenance", "📊 Records", "📦 Inventory"],
    "technician": ["🏠 Dashboard", "🔧 Maintenance", "📊 Records"],
    "storekeeper": ["🏠 Dashboard", "📦 Inventory", "📊 Records"],
    "quality": ["🏠 Dashboard", "📊 Records", "📈 Production"]
}

# --- 5. نظام اللغات ---
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
        "dashboard": "لوحة القيادة",
        "production": "إدارة الإنتاج",
        "maintenance": "مركز الصيانة",
        "records": "السجلات",
        "inventory": "المخازن",
        "users": "المستخدمين",
        "settings": "الإعدادات",
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
        "low_stock_count": "مواد منخفضة",
        "weekly_trend": "اتجاه الإنتاج",
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
        "min_stock": "الحد الأدنى"
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
        "dashboard": "Dashboard",
        "production": "Production",
        "maintenance": "Maintenance",
        "records": "Records",
        "inventory": "Inventory",
        "users": "Users",
        "settings": "Settings",
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
        "avg_efficiency": "Avg Efficiency",
        "total_waste": "Total Waste",
        "low_stock_count": "Low Stock Items",
        "weekly_trend": "Weekly Trend",
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
        "min_stock": "Min Stock"
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
        "dashboard": "ড্যাশবোর্ড",
        "production": "উৎপাদন",
        "maintenance": "রক্ষণাবেক্ষণ",
        "records": "রেকর্ড",
        "inventory": "ইনভেন্টরি",
        "users": "ব্যবহারকারী",
        "settings": "সেটিংস",
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
        "invoice": "ইনভয়েস",
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
        "low_stock_count": "স্বল্প স্টক",
        "weekly_trend": "সাপ্তাহিক প্রবণতা",
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
        "min_stock": "ন্যূনতম স্টক"
    }
}

# --- 6. الهوية والشعار ---
st.sidebar.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
if os.path.exists("birma mark.png"):
    st.sidebar.image("birma mark.png", use_container_width=True)
else:
    st.sidebar.markdown("<h1 style='color: #0047AB;'>BIRMA</h1>", unsafe_allow_html=True)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.markdown(f"<p style='text-align: center; font-size: 12px; color: gray; margin-bottom:0;'>Designed by:</p>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='text-align: center; color: #2E8B57; margin-top:0;'>{LANG['ar']['designer']}</h3>", unsafe_allow_html=True)
st.sidebar.divider()

# --- 7. الربط والخدمات ---
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

# --- 8. تحميل بيانات المخزون ---
def load_inventory():
    if os.path.exists("raw.xlsx"):
        df_inv = pd.read_excel("raw.xlsx")
        required_cols = ["Material_ID", "Material_Name_AR", "Material_Name_EN", "Unit", "Current_Stock", "Min_Stock", "Last_Updated"]
        for col in required_cols:
            if col not in df_inv.columns:
                df_inv[col] = None
        if 'Last_Updated' in df_inv.columns:
            df_inv['Last_Updated'] = df_inv['Last_Updated'].astype(str)
        for col in ["Current_Stock", "Min_Stock"]:
            if col in df_inv.columns:
                df_inv[col] = pd.to_numeric(df_inv[col], errors='coerce').fillna(0)
        return df_inv
    else:
        return pd.DataFrame(columns=["Material_ID", "Material_Name_AR", "Material_Name_EN", "Unit", "Current_Stock", "Min_Stock", "Last_Updated"])

def update_inventory(df_inv):
    df_inv = df_inv.copy()
    if 'Last_Updated' in df_inv.columns:
        df_inv['Last_Updated'] = df_inv['Last_Updated'].astype(str)
    df_inv.to_excel("raw.xlsx", index=False)
    return True

def check_low_stock(df_inv):
    low_stock = df_inv[df_inv["Current_Stock"] <= df_inv["Min_Stock"]]
    if not low_stock.empty:
        msg = "🚨 *تنبيه مخزون منخفض*\n"
        for _, row in low_stock.iterrows():
            unit = row.get("Unit", "")
            msg += f"- {row['Material_Name_AR']}: {row['Current_Stock']} {unit}\n"
        send_telegram(msg)
    return low_stock

# --- 9. بيانات خطوط الإنتاج و BOM ---
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

# BOM الأساسية
BOM = {
    "200 ml Carton": {"بريفورم200": 48, "غطاء": 48, "ليبل 200": 48, "كرتون200": 1},
    "200 ml Shrink": {"بريفورم200": 20, "غطاء": 20, "ليبل 200": 20, "شرنك200": 0.0005},
    "600 ml Carton": {"بريفورم600": 30, "غطاء": 30, "ليبل 600": 30, "كرتون600": 1},
    "1.5 L Shrink": {"بريفورم لتر ونص": 6, "غطاء": 6, "ليبل لتر ونص": 6, "شرنك لتر ونص": 0.000625},
    "330 ml Carton": {"بريفورم330": 40, "غطاء": 40, "ليبل 330": 40, "كرتون330": 1},
    "331 ml Shrink": {"بريفورم330": 20, "غطاء": 20, "ليبل 330": 20, "شرنك330": 0.0005},
}

# معاملات فواصل الشرنك (حسب الباليت)
SHRINK_PALLET_CONFIG = {
    "200 ml Shrink": {"units_per_pallet": 180, "spacers_per_pallet": 7},
    "331 ml Shrink": {"units_per_pallet": 144, "spacers_per_pallet": 5},
    "1.5 L Shrink": {"units_per_pallet": 80, "spacers_per_pallet": 5},
}

# معاملات استهلاك غراء الليبل (جرام لكل عبوة)
ADHESIVE_CONSUMPTION = {
    "200 ml Carton": 0.3,
    "200 ml Shrink": 0.3,
    "600 ml Carton": 0.4,
    "1.5 L Shrink": 0.35,
    "330 ml Carton": 0.35,
    "331 ml Shrink": 0.35,
}

# معاملات استهلاك غراء الكرتون (جرام لكل كرتونة)
HOTMELT_CONSUMPTION = {
    "200 ml Carton": 2.0,
    "600 ml Carton": 2.5,
    "330 ml Carton": 2.0,
}

def calculate_spacers_needed(product, quantity_produced):
    """حساب عدد فواصل الشرنك المطلوبة"""
    if product not in SHRINK_PALLET_CONFIG:
        return 0
    
    config = SHRINK_PALLET_CONFIG[product]
    units_per_pallet = config["units_per_pallet"]
    spacers_per_pallet = config["spacers_per_pallet"]
    
    num_pallets = math.ceil(quantity_produced / units_per_pallet)
    spacers_needed = num_pallets * spacers_per_pallet
    
    return spacers_needed

def calculate_adhesive_needed(product, quantity_produced):
    """حساب كمية غراء الليبل المطلوبة بالكيلوجرام"""
    if product not in ADHESIVE_CONSUMPTION:
        return 0
    
    grams_per_unit = ADHESIVE_CONSUMPTION[product]
    total_grams = grams_per_unit * quantity_produced
    total_kg = total_grams / 1000
    
    return math.ceil(total_kg * 100) / 100

def calculate_hotmelt_needed(product, quantity_produced):
    """حساب كمية غراء الكرتون المطلوبة بالكيلوجرام"""
    if product not in HOTMELT_CONSUMPTION:
        return 0
    
    grams_per_carton = HOTMELT_CONSUMPTION[product]
    # عدد الكرتونات = عدد الوحدات المنتجة (لأن كل وحدة = كرتونة واحدة في منتجات الكرتون)
    num_cartons = quantity_produced
    total_grams = grams_per_carton * num_cartons
    total_kg = total_grams / 1000
    
    return math.ceil(total_kg * 100) / 100

def consume_materials(product, quantity, df_inv):
    """صرف المواد من المخزون (مع دعم فواصل الشرنك والغراء)"""
    if product not in BOM:
        return df_inv, False, f"المنتج {product} غير موجود"
    
    required = {}
    
    # حساب المواد الأساسية من BOM
    for material, qty in BOM[product].items():
        if qty < 1:
            required[material] = math.ceil(quantity * qty)
        else:
            required[material] = qty * quantity
    
    # حساب فواصل الشرنك (للمنتجات من نوع شرنك فقط)
    if "Shrink" in product:
        spacers_needed = calculate_spacers_needed(product, quantity)
        if spacers_needed > 0:
            required["فواصل شرنك"] = spacers_needed
    
    # حساب غراء الليبل (لجميع المنتجات)
    adhesive_kg = calculate_adhesive_needed(product, quantity)
    if adhesive_kg > 0:
        required["غراء الليبل"] = adhesive_kg
    
    # حساب غراء الكرتون (لمنتجات الكرتون فقط)
    if "Carton" in product:
        hotmelt_kg = calculate_hotmelt_needed(product, quantity)
        if hotmelt_kg > 0:
            required["غراء الكرتون"] = hotmelt_kg
    
    shortages = []
    new_df = df_inv.copy()
    
    for idx, row in new_df.iterrows():
        mat_name = row["Material_Name_AR"]
        if mat_name in required:
            req = required[mat_name]
            current = float(row["Current_Stock"]) if pd.notna(row["Current_Stock"]) else 0
            if current < req:
                if "غراء" in mat_name:
                    shortages.append(f"{mat_name} (مطلوب {req:.2f} كجم، متوفر {current:.2f} كجم)")
                else:
                    shortages.append(f"{mat_name} (مطلوب {req:,.0f}، متوفر {current:,.0f})")
            else:
                new_df.at[idx, "Current_Stock"] = current - req
                new_df.at[idx, "Last_Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if shortages:
        return df_inv, False, f"⚠️ عجز: {', '.join(shortages[:3])}"
    
    # رسالة تفصيلية
    details = []
    for k, v in required.items():
        if "غراء" in k:
            details.append(f"{k}: {v:.2f} كجم")
        elif k == "فواصل شرنك":
            details.append(f"{k}: {v}")
        else:
            details.append(f"{k}: {v:,.0f}")
    
    details_str = ", ".join(details)
    
    # إضافة معلومات الباليتات للشرنك
    if "Shrink" in product and product in SHRINK_PALLET_CONFIG:
        config = SHRINK_PALLET_CONFIG[product]
        pallets = math.ceil(quantity / config["units_per_pallet"])
        details_str += f"\n📦 باليتات: {pallets} باليت | فواصل: {required.get('فواصل شرنك', 0)}"
    
    return new_df, True, f"✅ تم صرف المواد لـ {quantity:,.0f} وحدة من {product}\n📦 المواد: {details_str}"

# --- 10. ماكينات الصيانة ---
MACHINE_MAP = {
    "النفخ(blowing)": "blowing_machine.xlsx",
    "الليبل(labeling)": "labeling_machine.xlsx",
    "السيور(Conveyor)": "Conveyor_machine.xlsx",
    "الكرتون(packing)": "packing_machine.xlsx",
    "البالتايزر(paletizer)": "paletizer_machine.xlsx",
    "الشرنك(shrink)": "shrink_machine.xlsx",
    "التعبئة(filling)": "Filling_machine.xlsx"
}

def create_sample_machine_file(filepath):
    sample_data = pd.DataFrame({
        "Cat": ["ميكانيكية", "ميكانيكية", "كهربائية", "ميكانيكية", "كهربائية"],
        "No": [1, 2, 3, 4, 5],
        "Name": ["فحص المحامل", "تنظيف الفلاتر", "معايرة الحساسات", "تشحيم الأجزاء المتحركة", "فحص الأحزمة"],
        "Photo": ["", "", "", "", ""],
        "Tools": ["مفتاح ربط", "فرشاة + هواء", "جهاز معايرة", "شحم", "مفتاح ربط"],
        "Proc": ["فحص الاهتزازات والحرارة", "تنظيف بالهواء المضغوط", "معايرة حسب الدليل", "تشحيم كل 100 ساعة", "فحص الشد والتآكل"],
        "Freq": ["Daily", "Daily", "Weekly", "Weekly", "Monthly"],
        "Stat": ["Active", "Active", "Active", "Active", "Active"],
        "Note": ["", "", "", "", ""],
        "Staff": ["", "", "", "", ""]
    })
    sample_data.to_excel(filepath, index=False)

def get_scheduled_tasks(df_tasks):
    today = datetime.now()
    day_name = today.strftime('%A')
    is_first_of_month = (today.day == 1)
    
    if day_name == 'Friday':
        return pd.DataFrame()
    
    allowed_freqs = ['Daily']
    if day_name == 'Saturday':
        allowed_freqs.append('Weekly')
    if is_first_of_month:
        allowed_freqs.append('Monthly')
    
    if 'Freq' in df_tasks.columns:
        return df_tasks[df_tasks['Freq'].isin(allowed_freqs)]
    return pd.DataFrame()

# --- 11. دوال عرض البيانات ---
def translate_dataframe(df, lang):
    if df is None or df.empty:
        return df
    
    column_translations = {
        "ar": {
            "Date": "التاريخ", "Line": "الخط", "Supervisor": "المشرف", "Product": "المنتج",
            "Quantity": "الكمية", "Output_Units": "الوحدات", "Efficiency": "الكفاءة",
            "Efficiency_%": "الكفاءة %", "Waste_Bottles": "الهالك", "Timestamp": "التوقيت",
            "Type": "النوع", "Machine": "الماكينة", "Technician": "الفني", "Task": "المهمة",
            "Notes": "ملاحظات", "Issue": "العطل", "Start_Time": "البداية", "End_Time": "النهاية",
            "Staff": "الموظف"
        },
        "en": {
            "Date": "Date", "Line": "Line", "Supervisor": "Supervisor", "Product": "Product",
            "Quantity": "Quantity", "Output_Units": "Output", "Efficiency": "Efficiency",
            "Efficiency_%": "Efficiency %", "Waste_Bottles": "Waste", "Timestamp": "Time",
            "Type": "Type", "Machine": "Machine", "Technician": "Technician", "Task": "Task",
            "Notes": "Notes", "Issue": "Issue", "Start_Time": "Start", "End_Time": "End",
            "Staff": "Staff"
        },
        "bn": {
            "Date": "তারিখ", "Line": "লাইন", "Supervisor": "সুপারভাইজার", "Product": "পণ্য",
            "Quantity": "পরিমাণ", "Output_Units": "উৎপাদন", "Efficiency": "দক্ষতা",
            "Efficiency_%": "দক্ষতা", "Waste_Bottles": "বর্জ্য", "Timestamp": "সময়",
            "Type": "ধরন", "Machine": "মেশিন", "Technician": "টেকনিশিয়ান", "Task": "কাজ",
            "Notes": "নোট", "Issue": "সমস্যা", "Start_Time": "শুরু", "End_Time": "শেষ",
            "Staff": "স্টাফ"
        }
    }
    
    trans = column_translations.get(lang, column_translations["ar"])
    rename_dict = {col: trans.get(col, col) for col in df.columns}
    return df.rename(columns=rename_dict)

# --- 12. لوحة القيادة ---
def show_dashboard(df_main, df_inv, t):
    st.title(f"🏠 {t['dashboard_title']}")
    
    total_prod = 0
    avg_eff = 0
    total_waste = 0
    today_prod = 0
    maint_count = 0
    
    if df_main is not None and not df_main.empty:
        prod_df = df_main[df_main['Type'] == 'Production'] if 'Type' in df_main.columns else pd.DataFrame()
        maint_df = df_main[df_main['Type'].str.contains('Maintenance|Maint', na=False, case=False)] if 'Type' in df_main.columns else pd.DataFrame()
        
        if not prod_df.empty:
            total_prod = int(prod_df['Output_Units'].sum()) if 'Output_Units' in prod_df.columns else 0
            avg_eff = round(prod_df['Efficiency_%'].mean(), 1) if 'Efficiency_%' in prod_df.columns else 0
            total_waste = int(prod_df['Waste_Bottles'].sum()) if 'Waste_Bottles' in prod_df.columns else 0
            
            today_str = datetime.now().strftime("%Y-%m-%d")
            today_prod_df = prod_df[prod_df['Date'] == today_str] if 'Date' in prod_df.columns else pd.DataFrame()
            today_prod = int(today_prod_df['Output_Units'].sum()) if not today_prod_df.empty else 0
        
        maint_count = len(maint_df)
    
    low_count = len(df_inv[df_inv["Current_Stock"] <= df_inv["Min_Stock"]]) if not df_inv.empty else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(t["total_production"], f"{total_prod:,}", delta=f"+{today_prod:,} اليوم" if today_prod > 0 else None)
    with col2:
        st.metric(t["avg_efficiency"], f"{avg_eff}%")
    with col3:
        st.metric(t["total_waste"], f"{total_waste:,}")
    with col4:
        st.metric(t["low_stock_count"], low_count, delta="يحتاج مراجعة" if low_count > 0 else None)
    
    st.markdown("---")
    st.subheader(t["smart_recommendations"])
    
    recommendations = []
    if avg_eff < 75 and total_prod > 0:
        recommendations.append("⚠️ الكفاءة منخفضة - راجع سرعة الإنتاج")
    if low_count > 0:
        recommendations.append(f"📦 يوجد {low_count} مواد منخفضة المخزون")
    if today_prod == 0 and datetime.now().hour > 10:
        recommendations.append("📊 لم يتم تسجيل إنتاج اليوم")
    if maint_count > 0:
        recommendations.append(f"🔧 يوجد {maint_count} سجل صيانة - راجع قسم الصيانة")
    if not recommendations:
        recommendations.append("✅ جميع المؤشرات جيدة")
    
    for rec in recommendations:
        if "⚠️" in rec:
            st.warning(rec)
        elif "📦" in rec or "🔧" in rec:
            st.info(rec)
        else:
            st.success(rec)

# --- 13. واجهة تسجيل الدخول ---
def login_screen(t):
    if os.path.exists("birma mark.png"):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("birma mark.png", use_container_width=True)
    else:
        st.markdown("<h1 style='text-align: center; color: #0047AB;'>🏭 BIRMA</h1>", unsafe_allow_html=True)
    
    st.markdown("<h3 style='text-align: center; color: gray;'>نظام إدارة مصنع المياه المتكامل</h3>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input(t["username"])
            password = st.text_input(t["password"], type="password")
            if st.form_submit_button(t["login_btn"], use_container_width=True):
                if username in USERS and USERS[username]["password"] == password:
                    st.session_state.authenticated = True
                    st.session_state.user_role = USERS[username]["role"]
                    st.session_state.user_name = USERS[username]["name"]
                    st.rerun()
                else:
                    st.error(t["login_error"])

# --- 14. الواجهة الرئيسية ---
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
        st.sidebar.markdown("<h2 style='color: #0047AB; text-align: center;'>🏭 BIRMA</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
    st.sidebar.divider()
    
    lang = st.sidebar.selectbox("🌐 Language", ["ar", "en", "bn"], index=["ar", "en", "bn"].index(st.session_state.lang))
    st.session_state.lang = lang
    t = LANG[lang]
    
    user_icon = "👤"
    for u in USERS.values():
        if u["name"] == st.session_state.user_name:
            user_icon = u["icon"]
            break
    
    st.sidebar.markdown(f"### {user_icon} {st.session_state.user_name}")
    st.sidebar.markdown(f"📌 {t['role']}: {st.session_state.user_role}")
    
    if st.sidebar.button(t["logout"], use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.user_name = None
        st.rerun()
    
    st.sidebar.divider()
    
    available_menus_raw = ROLE_PERMISSIONS.get(st.session_state.user_role, ROLE_PERMISSIONS["admin"])
    menu_translation = {
        "🏠 Dashboard": t["dashboard"],
        "📈 Production": t["production"],
        "🔧 Maintenance": t["maintenance"],
        "📊 Records": t["records"],
        "📦 Inventory": t["inventory"],
        "👥 Users": t["users"],
        "⚙️ Settings": t["settings"]
    }
    available_menus = [menu_translation.get(menu, menu) for menu in available_menus_raw]
    selected_menu_display = st.sidebar.radio("📋", available_menus)
    
    reverse_translation = {v: k for k, v in menu_translation.items()}
    selected_menu_raw = reverse_translation.get(selected_menu_display, selected_menu_display)
    
    if selected_menu_raw in ["📈 Production", "🔧 Maintenance"]:
        selected_line = st.sidebar.radio(t["line_label"], list(CONFIG.keys()))
    else:
        selected_line = None
    
    df_inv = load_inventory()
    
    # ========== Dashboard ==========
    if selected_menu_raw == "🏠 Dashboard":
        show_dashboard(df_main, df_inv, t)
    
    # ========== Production ==========
    elif selected_menu_raw == "📈 Production" and selected_line:
        st.header(f"{t['production']} - {selected_line}")
        
        with st.form("prod_form"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input(t["sup_label"])
                product = st.selectbox(t["prod_label"], CONFIG[selected_line]["products"])
                target = st.number_input(t["target_label"], min_value=0)
            with c2:
                preforms = st.number_input(t["preform_label"], min_value=0)
                raw_type = "Carton" if "Carton" in product else "Shrink"
                raw_val = st.number_input(f"{t['raw_label']} ({raw_type})", min_value=0)
                p_date = st.date_input(t["date_label"])
            
            if st.form_submit_button(t["save_btn"]):
                if target <= 0:
                    st.error("⚠️ الكمية يجب أن تكون أكبر من صفر")
                elif not name:
                    st.error("⚠️ يرجى إدخال اسم المشرف")
                else:
                    b_per_u = CONFIG[selected_line]["pack_per_unit"][product]
                    total_b = target * b_per_u
                    speed = CONFIG[selected_line]["speed"][product]
                    eff = round((total_b / (speed * 15)) * 100, 1) if speed > 0 else 0
                    
                    df_inv_updated, success, msg = consume_materials(product, target, df_inv)
                    
                    if not success:
                        st.error(msg)
                    else:
                        if update_inventory(df_inv_updated):
                            new_row = pd.DataFrame([{
                                "Type": "Production", 
                                "Line": selected_line, 
                                "Date": str(p_date), 
                                "Supervisor": name, 
                                "Product": product, 
                                "Output_Units": int(target),
                                "Waste_Bottles": int(preforms - total_b) if preforms > 0 else 0,
                                "Waste_Raw": int(raw_val - target) if raw_val > 0 else 0,
                                "Efficiency_%": float(eff),
                                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }])
                            
                            if conn is not None and not df_main.empty:
                                save_to_sheet(conn, pd.concat([df_main, new_row], ignore_index=True))
                            elif conn is not None:
                                save_to_sheet(conn, new_row)
                            
                            check_low_stock(df_inv_updated)
                            send_telegram(f"🚀 Production: {selected_line} - {product} - {target} units - {eff}%")
                            
                            st.success(f"{t['success_msg']}\n{msg}")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("فشل في تحديث المخزون")
    
    # ========== Maintenance ==========
    elif selected_menu_raw == "🔧 Maintenance" and selected_line:
        st.header(t["maint_header"])
        m_type = st.radio("Type", t["maint_types"], horizontal=True)
        machine = st.sidebar.selectbox(t["machine_select"], list(MACHINE_MAP.keys()))
        
        if m_type == t["maint_types"][0]:
            path = MACHINE_MAP[machine]
            if not os.path.exists(path):
                create_sample_machine_file(path)
            
            df_raw = pd.read_excel(path, skiprows=2)
            df_raw.columns = ['Cat', 'No', 'Name', 'Photo', 'Tools', 'Proc', 'Freq', 'Stat', 'Note', 'Staff']
            scheduled_tasks = get_scheduled_tasks(df_raw)
            
            if scheduled_tasks.empty:
                st.warning(t["weekend_msg"])
            else:
                with st.form("m_form"):
                    tech = st.text_input(t["tech_label"])
                    recs = []
                    for i, r in scheduled_tasks.iterrows():
                        st.divider()
                        c_i, c_p = st.columns([2,1])
                        with c_i:
                            st.markdown(f"### 🔧 {r['Name']} ({r['Freq']})")
                            st.markdown(f"**{t['tools_label']}** `{r['Tools'] if pd.notna(r['Tools']) else 'N/A'}`")
                            st.info(f"**{t['proc_label']}**\n{r['Proc'] if pd.notna(r['Proc']) else 'N/A'}")
                            ok = st.checkbox(f"{t['done']} - {r['Name']}", key=f"k{i}")
                            note = st.text_input(t["note_label"], key=f"n{i}")
                        with c_p:
                            img = os.path.join("images", str(r['Photo']).strip())
                            if os.path.exists(img):
                                st.image(img, use_container_width=True)
                        if ok:
                            recs.append({
                                "Type": "Maintenance_Planned",
                                "Line": selected_line,
                                "Date": str(datetime.now().date()),
                                "Machine": machine,
                                "Task": r['Name'],
                                "Technician": tech,
                                "Staff": tech,
                                "Notes": note,
                                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })
                    
                    if st.form_submit_button(t["save_btn"]):
                        if not tech:
                            st.error("⚠️ يرجى إدخال اسم الفني")
                        elif not recs:
                            st.error("⚠️ يرجى اختيار المهام المنفذة")
                        else:
                            new_df = pd.DataFrame(recs)
                            if conn is not None:
                                if not df_main.empty:
                                    save_to_sheet(conn, pd.concat([df_main, new_df], ignore_index=True))
                                else:
                                    save_to_sheet(conn, new_df)
                            st.success(t["success_msg"])
                            st.rerun()
        else:
            with st.form("break_form"):
                t_name = st.text_input(t["tech_label"])
                issue = st.text_area(t["issue_label"])
                col1, col2 = st.columns(2)
                t1 = col1.time_input(t["start_t"])
                t2 = col2.time_input(t["end_t"])
                m_note = st.text_area(t["note_label"])
                
                if st.form_submit_button(t["save_btn"]):
                    if not t_name:
                        st.error("⚠️ يرجى إدخال اسم الفني")
                    elif not issue:
                        st.error("⚠️ يرجى إدخال وصف العطل")
                    else:
                        new_b = pd.DataFrame([{
                            "Type": "Maintenance_Breakdown",
                            "Line": selected_line,
                            "Date": str(datetime.now().date()),
                            "Machine": machine,
                            "Technician": t_name,
                            "Staff": t_name,
                            "Issue": issue,
                            "Start_Time": t1.strftime("%H:%M"),
                            "End_Time": t2.strftime("%H:%M"),
                            "Notes": m_note,
                            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }])
                        if conn is not None:
                            if not df_main.empty:
                                save_to_sheet(conn, pd.concat([df_main, new_b], ignore_index=True))
                            else:
                                save_to_sheet(conn, new_b)
                        send_telegram(f"⚠️ Breakdown: {machine} - {t_name} - {issue[:50]}")
                        st.success(t["success_msg"])
                        st.rerun()
    
    # ========== Records ==========
    elif selected_menu_raw == "📊 Records":
        st.header(t["records"])
        
        if df_main is not None and not df_main.empty:
            tab1, tab2 = st.tabs([t["history_p"], t["history_m"]])
            
            with tab1:
                prod_logs = df_main[df_main['Type'] == 'Production'] if 'Type' in df_main.columns else pd.DataFrame()
                if not prod_logs.empty:
                    st.dataframe(translate_dataframe(prod_logs.tail(50)[::-1], lang), use_container_width=True)
                else:
                    st.info(t["no_production"])
            
            with tab2:
                maint_logs = df_main[df_main['Type'].str.contains('Maintenance|Maint', na=False, case=False)] if 'Type' in df_main.columns else pd.DataFrame()
                if not maint_logs.empty:
                    st.dataframe(translate_dataframe(maint_logs.tail(50)[::-1], lang), use_container_width=True)
                else:
                    st.info(t["no_maintenance"])
        else:
            st.info(t["no_data"])
    
    # ========== Inventory ==========
    elif selected_menu_raw == "📦 Inventory":
        st.header(t["inventory_header"])
        
        if not df_inv.empty:
            tab1, tab2, tab3 = st.tabs([t["current_stock"], t["receipt"], t["edit_stock"]])
            
            with tab1:
                st.dataframe(df_inv[["Material_ID", "Material_Name_AR", "Current_Stock", "Min_Stock", "Unit", "Last_Updated"]], use_container_width=True)
            
            with tab2:
                with st.form("receipt_form"):
                    material = st.selectbox(t["material"], df_inv["Material_Name_AR"])
                    qty = st.number_input(t["quantity"], min_value=0, step=1000)
                    invoice_no = st.text_input(t["invoice"])
                    receipt_date = st.date_input(t["receipt_date"])
                    notes = st.text_area("ملاحظات")
                    
                    if st.form_submit_button(t["register_receipt"]):
                        idx = df_inv[df_inv["Material_Name_AR"] == material].index[0]
                        df_inv.at[idx, "Current_Stock"] += qty
                        df_inv.at[idx, "Last_Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        update_inventory(df_inv)
                        st.success(f"تم استلام {qty:,.0f} من {material}")
                        st.rerun()
            
            with tab3:
                st.subheader(t["edit_stock"])
                admin_pw = st.text_input(t["password"], type="password", key="edit_pw")
                if admin_pw == "admin123":
                    # تعديل رصيد موجود
                    material = st.selectbox(t["material"], df_inv["Material_Name_AR"])
                    new_qty = st.number_input(t["new_stock"], min_value=0, step=1000)
                    if st.button(t["update"]):
                        idx = df_inv[df_inv["Material_Name_AR"] == material].index[0]
                        df_inv.at[idx, "Current_Stock"] = new_qty
                        df_inv.at[idx, "Last_Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        update_inventory(df_inv)
                        st.success(t["stock_updated"])
                        st.rerun()
                    
                    st.markdown("---")
                    st.subheader(f"➕ {t['add_new_item']}")
                    
                    with st.expander(t['add_new_item']):
                        col1, col2 = st.columns(2)
                        with col1:
                            new_id = st.number_input(t["item_id"], min_value=1000, step=1, value=2000)
                            new_name_ar = st.text_input(f"{t['item_name']} (عربي)")
                            new_unit = st.selectbox(t["item_unit"], ["قطعة", "كجم", "لتر", "رول"])
                        with col2:
                            new_name_en = st.text_input(f"{t['item_name']} (English)", help="اختياري")
                            new_min_stock = st.number_input(t["min_stock"], min_value=0, step=1000, value=1000)
                        
                        if st.button("➕ إضافة المادة", use_container_width=True):
                            if new_id in df_inv['Material_ID'].values:
                                st.error("⚠️ هذا الرقم التعريفي موجود بالفعل")
                            elif not new_name_ar:
                                st.error("⚠️ يرجى إدخال اسم المادة")
                            else:
                                new_row = pd.DataFrame([{
                                    "Material_ID": new_id,
                                    "Material_Name_AR": new_name_ar,
                                    "Material_Name_EN": new_name_en if new_name_en else new_name_ar,
                                    "Unit": new_unit,
                                    "Current_Stock": 0,
                                    "Min_Stock": new_min_stock,
                                    "Last_Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }])
                                df_inv_updated = pd.concat([df_inv, new_row], ignore_index=True)
                                if update_inventory(df_inv_updated):
                                    st.success(f"✅ تم إضافة المادة {new_name_ar} بنجاح")
                                    st.rerun()
                                else:
                                    st.error("❌ فشل في إضافة المادة")
                else:
                    if admin_pw:
                        st.warning("🔒 يرجى إدخال كلمة مرور المشرف لتعديل الرصيد أو إضافة صنف جديد")
        else:
            st.warning("لا توجد بيانات مخزون")
    
    # ========== Users ==========
    elif selected_menu_raw == "👥 Users" and st.session_state.user_role == "admin":
        st.header(t["users_title"])
        users_df = pd.DataFrame([{"Username": k, "Name": v["name"], "Role": v["role"]} for k, v in USERS.items()])
        st.dataframe(users_df, use_container_width=True)
    
    # ========== Settings ==========
    elif selected_menu_raw == "⚙️ Settings" and st.session_state.user_role == "admin":
        st.header(t["settings_title"])
        col1, col2 = st.columns(2)
        with col1:
            if st.button(t["backup_data"], use_container_width=True):
                if df_main is not None and not df_main.empty:
                    backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    df_main.to_excel(backup_file, index=False)
                    st.success(f"تم إنشاء نسخة احتياطية: {backup_file}")
        with col2:
            if st.button(t["clear_cache"], use_container_width=True):
                st.cache_data.clear()
                st.success("تم مسح الذاكرة المؤقتة")
    
    # ========== حذف السجل ==========
    st.sidebar.divider()
    with st.sidebar.expander("🔒 " + t["admin_title"]):
        admin_pw = st.text_input(t["password"], type="password", key="admin_delete_pw")
        if admin_pw == "admin123":
            if df_main is not None and not df_main.empty:
                df_display = df_main.copy()
                if 'Type' in df_display.columns and 'Date' in df_display.columns:
                    def format_record(row):
                        if row['Type'] == 'Production':
                            product = row.get('Product', 'N/A')
                            qty = row.get('Output_Units', 0)
                            return f"📦 إنتاج | {row['Date']} | {product} | {qty} وحدة"
                        elif 'Maintenance' in str(row['Type']):
                            machine = row.get('Machine', 'N/A')
                            tech = row.get('Technician', row.get('Staff', 'N/A'))
                            return f"🔧 صيانة | {row['Date']} | {machine} | {tech}"
                        else:
                            return f"📄 {row['Type']} | {row['Date']}"
                    
                    df_display['description'] = df_display.apply(format_record, axis=1)
                    
                    selected_index = st.selectbox(
                        "اختر السجل المراد حذفه",
                        options=df_display.index,
                        format_func=lambda x: df_display.loc[x, 'description']
                    )
                    
                    if st.button("🗑️ " + t["delete_btn"], use_container_width=True):
                        df_updated = df_main.drop(selected_index)
                        if conn is not None:
                            if save_to_sheet(conn, df_updated):
                                st.success(t["del_success"])
                                st.rerun()
                            else:
                                st.error("فشل في حفظ التعديلات")
                        else:
                            st.error("لا يوجد اتصال بـ Google Sheets")
                else:
                    st.info("لا توجد أعمدة كافية لعرض السجلات")
            else:
                st.info("لا توجد سجلات لعرضها")
        else:
            if admin_pw:
                st.warning("🔒 كلمة المرور غير صحيحة")
    
    st.sidebar.divider()
    st.sidebar.markdown(f"<center><small>BIRMA v10.5<br>{t['designer']}</small></center>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()