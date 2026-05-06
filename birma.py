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
# 1. إعدادات الصفحة - خلفية بيضاء بالكامل
# ============================================================================
st.set_page_config(page_title="BIRMA Integrated System", page_icon="🏭", layout="wide")

st.markdown("""
<style>
    /* خلفية النظام بيضاء بالكامل */
    .stApp {
        background: #ffffff;
    }
    
    /* تنسيق الكروت - بدون خلفيات ملونة، فقط ظل خفيف */
    .data-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
        transition: all 0.2s ease;
    }
    .data-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* كروت الميتريك - خلفية بيضاء */
    .metric-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        border: 1px solid #e2e8f0;
        transition: all 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .metric-card h3 {
        margin: 0;
        font-size: 14px;
        color: #64748b;
        font-weight: normal;
    }
    .metric-card .value {
        font-size: 32px;
        font-weight: bold;
        margin: 10px 0;
        color: #1e293b;
    }
    
    /* كرت الإنتاج */
    .production-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    
    /* بطاقات المواد - خلفية بيضاء */
    .material-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 12px 15px;
        margin: 8px 0;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        transition: all 0.2s ease;
    }
    .material-card:hover {
        transform: translateX(3px);
        border-color: #cbd5e1;
    }
    
    /* شريط التوصيات */
    .marquee {
        background: #f8fafc;
        border-radius: 30px;
        padding: 10px 20px;
        margin: 20px 0;
        overflow: hidden;
        white-space: nowrap;
        border: 1px solid #e2e8f0;
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
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .marquee-content span {
        margin-right: 50px;
        padding: 5px 15px;
        border-radius: 20px;
        display: inline-block;
        font-size: 13px;
    }
    .critical { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
    .warning { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }
    .info { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
    .success { background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; }
    
    /* مربعات البيانات - خلفية بيضاء مع حدود ملونة خفيفة */
    .info-box {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px;
        border: 1px solid #e2e8f0;
        margin: 10px 0;
    }
    .warning-box {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px;
        border: 1px solid #e2e8f0;
        margin: 10px 0;
    }
    .danger-box {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px;
        border: 1px solid #e2e8f0;
        margin: 10px 0;
    }
    .success-box {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px;
        border: 1px solid #e2e8f0;
        margin: 10px 0;
    }
    
    /* عناصر داخل المربعات */
    .stock-item-low {
        background: #fef2f2;
        border-radius: 10px;
        padding: 10px;
        margin: 8px 0;
        border-left: 3px solid #dc2626;
    }
    .stock-item-warning {
        background: #fffbeb;
        border-radius: 10px;
        padding: 10px;
        margin: 8px 0;
        border-left: 3px solid #d97706;
    }
    .stock-item-safe {
        background: #f8fafc;
        border-radius: 10px;
        padding: 10px;
        margin: 8px 0;
        border-left: 3px solid #22c55e;
    }
    
    /* تنسيق الأزرار */
    .stButton button {
        background: #ffffff;
        color: #1e293b;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        padding: 8px 20px;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        background: #f8fafc;
        border-color: #94a3b8;
        transform: translateY(-1px);
    }
    
    /* تنسيق التبويبات */
    .stTabs [data-baseweb="tab"] {
        background: #f8fafc;
        border-radius: 12px;
        margin: 0 5px;
        transition: all 0.2s;
        border: 1px solid #e2e8f0;
    }
    .stTabs [aria-selected="true"] {
        background: #1e293b;
        color: white !important;
        border-color: #1e293b;
    }
    
    /* شريط جانبي */
    [data-testid="stSidebar"] {
        background: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    [data-testid="stSidebar"] * {
        color: #1e293b !important;
    }
    
    /* عنوان الصفحة */
    .page-title {
        text-align: center;
        margin-bottom: 30px;
    }
    .page-title h1 {
        color: #1e293b;
        font-size: 2rem;
        font-weight: bold;
    }
    
    /* تنسيق الجداول */
    .stDataFrame {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
    }
    
    /* مؤشرات الكفاءة */
    .efficiency-label {
        text-align: center;
        margin-top: 10px;
        font-size: 13px;
        color: #64748b;
    }
    
    hr {
        margin: 20px 0;
        border-color: #e2e8f0;
    }
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
    st.markdown(f"<div style='text-align: left; font-size: 14px; padding: 5px; color: #64748b;'>📅 {date_str}</div>", unsafe_allow_html=True)

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
if 'chart_animation_counter' not in st.session_state:
    st.session_state.chart_animation_counter = 0

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
# 6. نظام اللغات (محفوظ بالكامل)
# ============================================================================
LANG = {
    "ar": {
        "designer": "م/ السيد عون", "login_title": "تسجيل الدخول", "username": "اسم المستخدم",
        "password": "كلمة المرور", "login_btn": "دخول", "login_error": "خطأ",
        "logout": "تسجيل خروج", "welcome": "مرحباً", "role": "الدور",
        "dark_mode": "الوضع الليلي", "dashboard": "🏠 لوحة القيادة",
        "production": "📈 إدارة الإنتاج", "maintenance": "🔧 مركز الصيانة",
        "records": "📊 السجلات", "raw_materials": "📦 المخازن (مواد خام)",
        "finished_goods": "🏭 مخزن الإنتاج التام",
        "users": "👥 المستخدمين", "settings": "⚙️ الإعدادات", "line_label": "خط العمل", "sup_label": "المشرف",
        "prod_label": "المنتج", "target_label": "الكمية", "preform_label": "البريفورم",
        "raw_label": "خامة التغليف", "date_label": "التاريخ", "maint_header": "مركز الصيانة",
        "maint_types": ["صيانة دورية", "بلاغ عطل"], "tech_label": "الفني",
        "issue_label": "وصف العطل", "start_t": "بداية التوقف", "end_t": "نهاية الإصلاح",
        "note_label": "ملاحظات", "save_btn": "حفظ", "success_msg": "تم الحفظ",
        "eff_title": "مؤشر الكفاءة", "waste_title": "تحليل الهالك",
        "history_p": "سجل الإنتاج", "history_m": "سجل الصيانة", "history_delivery": "سجل التحميل",
        "admin_title": "لوحة التحكم - حذف السجل", "delete_btn": "حذف السجل",
        "del_success": "تم الحذف", "tools_label": "الأدوات:", "proc_label": "الإجراءات:",
        "weekend_msg": "الجمعة عطلة", "inventory_header": "إدارة المخازن",
        "current_stock": "المخزون الحالي", "receipt": "استلام مشتريات",
        "material": "المادة", "quantity": "الكمية", "invoice": "رقم الفاتورة",
        "receipt_date": "تاريخ الاستلام", "register_receipt": "تسجيل الاستلام",
        "low_stock_alert": "مواد منخفضة", "all_good": "جميع المواد آمنة",
        "edit_stock": "تعديل الرصيد", "new_stock": "الرصيد الجديد",
        "update": "تحديث", "stock_updated": "تم التحديث", "export_btn": "تصدير",
        "dashboard_title": "لوحة القيادة", "total_production": "إجمالي الإنتاج",
        "monthly_production": "إنتاج الشهر", "line1_efficiency": "كفاءة الخط الأول",
        "line2_efficiency": "كفاءة الخط الثاني", "smart_recommendations": "التوصيات الذكية",
        "users_title": "إدارة المستخدمين", "settings_title": "إعدادات النظام",
        "backup_data": "نسخ احتياطي", "clear_cache": "مسح الذاكرة",
        "machine_select": "اختر الماكينة", "task_name": "المهمة", "done": "تم التنفيذ",
        "no_data": "لا توجد بيانات", "no_production": "لا توجد سجلات إنتاج",
        "no_maintenance": "لا توجد سجلات صيانة", "no_delivery": "لا توجد سجلات تحميل",
        "add_new_item": "إضافة صنف جديد", "item_id": "الرقم", "item_name": "اسم المادة",
        "item_unit": "الوحدة", "min_stock": "الحد الأدنى", "info_title": "معلومات",
        "info_text": "حفظ البيانات على هذا الجهاز فقط", "shipping": "شحن منتجات",
        "customer": "اسم العميل", "register_shipping": "تسجيل الشحن",
        "balance": "الرصيد", "in": "وارد", "out": "صادر",
        "pallet_count": "عدد الباليتات", "last_10_days": "آخر 10 أيام",
        "remember_me": "تذكرني", "clear_saved": "مسح المحفوظات",
        "auto_reorder": "إعادة الطلب", "stock_prediction": "توقع النفاذ",
        "raw_balance": "المواد الخام", "fg_balance": "المنتج التام",
        "delivery": "تسليم بضاعة", "product": "المنتج", "quantity_to_deliver": "كمية التسليم",
        "manual_adjust": "تعديل يدوي", "waste_bottles": "هالك العبوات"
    },
    "en": {
        "designer": "Eng. Elsayed Aoun", "login_title": "Login", "username": "Username",
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
        "eff_title": "Efficiency", "waste_title": "Waste", "history_p": "Production Logs",
        "history_m": "Maintenance Logs", "history_delivery": "Delivery Logs",
        "admin_title": "Admin - Delete", "delete_btn": "Delete", "del_success": "Deleted",
        "tools_label": "Tools:", "proc_label": "Procedure:", "weekend_msg": "Friday off",
        "inventory_header": "Inventory", "current_stock": "Current Stock", "receipt": "Receive",
        "material": "Material", "quantity": "Quantity", "invoice": "Invoice", "receipt_date": "Date",
        "register_receipt": "Register", "low_stock_alert": "Low Stock", "all_good": "All Good",
        "edit_stock": "Edit Stock", "new_stock": "New Stock", "update": "Update",
        "stock_updated": "Updated", "export_btn": "Export", "dashboard_title": "Dashboard",
        "total_production": "Total Production", "monthly_production": "Monthly Production",
        "line1_efficiency": "Line 1 Efficiency", "line2_efficiency": "Line 2 Efficiency",
        "smart_recommendations": "Smart Recommendations", "users_title": "Users",
        "settings_title": "Settings", "backup_data": "Backup", "clear_cache": "Clear Cache",
        "machine_select": "Select Machine", "task_name": "Task", "done": "Done",
        "no_data": "No data", "no_production": "No production", "no_maintenance": "No maintenance",
        "no_delivery": "No delivery", "add_new_item": "Add Item", "item_id": "ID",
        "item_name": "Name", "item_unit": "Unit", "min_stock": "Min Stock", "info_title": "Info",
        "info_text": "Data saved locally", "shipping": "Shipping", "customer": "Customer",
        "register_shipping": "Register", "balance": "Balance", "in": "In", "out": "Out",
        "pallet_count": "Pallets", "last_10_days": "Last 10 Days", "remember_me": "Remember",
        "clear_saved": "Clear saved", "auto_reorder": "Auto Reorder", "stock_prediction": "Stock Prediction",
        "raw_balance": "Raw Materials", "fg_balance": "Finished Goods", "delivery": "Delivery",
        "product": "Product", "quantity_to_deliver": "Delivery Qty", "manual_adjust": "Manual Adjust",
        "waste_bottles": "Waste Bottles"
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
# 8. تحميل وحفظ المواد الخام (raw.xlsx)
# ============================================================================
RAW_MATERIALS_FILE = "raw.xlsx"
FINISHED_GOODS_FILE = "finished_goods.xlsx"

def load_raw_materials():
    if os.path.exists(RAW_MATERIALS_FILE):
        try:
            df_raw = pd.read_excel(RAW_MATERIALS_FILE)
            required_cols = ["Material_ID", "Material_Name_AR", "Current_Stock", "Min_Stock", "Unit", "Last_Updated"]
            for col in required_cols:
                if col not in df_raw.columns:
                    df_raw[col] = 0 if col in ["Current_Stock", "Min_Stock"] else ""
            for col in ["Current_Stock", "Min_Stock"]:
                if col in df_raw.columns:
                    df_raw[col] = pd.to_numeric(df_raw[col], errors='coerce').fillna(0)
            return df_raw
        except Exception as e:
            st.error(f"خطأ في تحميل المواد الخام: {e}")
            return None
    else:
        st.error(f"❌ ملف {RAW_MATERIALS_FILE} غير موجود!")
        return None

def update_raw_materials(df_raw):
    try:
        if df_raw is not None:
            df_raw.to_excel(RAW_MATERIALS_FILE, index=False)
            return True
        return False
    except Exception as e:
        st.error(f"خطأ في حفظ المواد الخام: {e}")
        return False

def load_finished_goods():
    if os.path.exists(FINISHED_GOODS_FILE):
        try:
            df_fg = pd.read_excel(FINISHED_GOODS_FILE)
            required_cols = ["Code", "Name", "In", "Out", "Balance", "Unit", "Last_Updated"]
            for col in required_cols:
                if col not in df_fg.columns:
                    df_fg[col] = 0 if col != "Name" and col != "Unit" else ""
            for col in ["In", "Out", "Balance"]:
                if col in df_fg.columns:
                    df_fg[col] = pd.to_numeric(df_fg[col], errors='coerce').fillna(0)
            return df_fg
        except Exception as e:
            st.error(f"خطأ في تحميل المنتج التام: {e}")
            return None
    else:
        st.error(f"❌ ملف {FINISHED_GOODS_FILE} غير موجود!")
        return None

def update_finished_goods(df_fg):
    try:
        if df_fg is not None:
            df_fg.to_excel(FINISHED_GOODS_FILE, index=False)
            return True
        return False
    except Exception as e:
        st.error(f"خطأ في حفظ المنتج التام: {e}")
        return False

# ============================================================================
# 9. BOM وبيانات الإنتاج (الثوابت محفوظة بالكامل)
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
    "200 ml Carton": {"بريفورم 200 مل": 48, "غطاء": 48, "ليبل 200 مل": 48, "كرتون": 1},
    "200 ml Shrink": {"بريفورم 200 مل": 20, "غطاء": 20, "ليبل 200 مل": 20, "شرنك": 0.0005},
    "600 ml Carton": {"بريفورم 600 مل": 30, "غطاء": 30, "ليبل 200 مل": 30, "كرتون": 1},
    "1.5 L Shrink": {"بريفورم 1.5 لتر": 6, "غطاء": 6, "ليبل 200 مل": 6, "شرنك": 0.000625},
    "330 ml Carton": {"بريفورم 330 مل": 40, "غطاء": 40, "ليبل 330 مل": 40, "كرتون": 1},
    "330 ml Shrink": {"بريفورم 330 مل": 20, "غطاء": 20, "ليبل 330 مل": 20, "شرنك": 0.0005},
}

FIXED_CAP_CONSUMPTION = 900000

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
    """صرف المواد من المخزون"""
    if product not in BOM:
        return df_raw, False, f"⚠️ المنتج {product} غير موجود في BOM"
    
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
                shortages.append(f"{mat_name} (مطلوب {req:,.0f}، متوفر {current:,.0f})")
            else:
                new_df.at[idx, "Current_Stock"] = current - req
                new_df.at[idx, "Last_Updated"] = datetime.now().strftime("%Y-%m-%d")
    
    if shortages:
        return df_raw, False, f"⚠️ عجز في المواد: {', '.join(shortages[:5])}"
    
    details = []
    for mat, qty in required.items():
        details.append(f"{mat}: {qty:,.0f}")
    
    return new_df, True, f"✅ تم صرف: {', '.join(details)}"

def add_to_finished_goods(product_name, quantity, df_fg):
    fg_name = get_finished_goods_name(product_name)
    idx = df_fg[df_fg["Name"] == fg_name].index
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
    
    return df_fg, True, f"✅ تم إضافة {quantity:,.0f} وحدة إلى المخزن"

def get_finished_goods_name(product_name):
    mapping = {
        "200 ml Carton": "Cartoon 200 ml",
        "200 ml Shrink": "Shrink 200 ml",
        "600 ml Carton": "Cartoon 600 ml",
        "1.5 L Shrink": "1.5 Ltr",
        "330 ml Carton": "Cartoon 330 ml",
        "330 ml Shrink": "Shrink 330 ml",
    }
    return mapping.get(product_name, product_name)

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
            new_df.at[idx, "Last_Updated"] = datetime.now().strftime("%Y-%m-%d")
    return new_df, True, f"✅ تم إعادة المواد لـ {quantity:,.0f} وحدة"

# ============================================================================
# 10. دوال الصيانة
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
    
    freq_col = 'Freq' if 'Freq' in df_tasks.columns else 'Frequency' if 'Frequency' in df_tasks.columns else None
    if freq_col is None:
        return pd.DataFrame()
    
    if day_name == 'Friday':
        return pd.DataFrame()
    
    allowed_freqs = ['Daily']
    if day_name == 'Saturday':
        allowed_freqs.append('Weekly')
    if is_first_of_month:
        allowed_freqs.append('Monthly')
        allowed_freqs.append('1000h')
        allowed_freqs.append('Yearly')
    
    df_tasks[freq_col] = df_tasks[freq_col].astype(str).replace('4 months', 'Monthly')
    df_tasks_filtered = df_tasks[df_tasks[freq_col].notna()]
    result = df_tasks_filtered[df_tasks_filtered[freq_col].isin(allowed_freqs)]
    return result.reset_index(drop=True)

# ============================================================================
# 11. التوصيات الذكية
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

def calculate_daily_consumption_for_material(df_main, material_name):
    if df_main is None or df_main.empty:
        return 0
    
    prod_df = df_main[df_main['Type'] == 'Production'].copy()
    if prod_df.empty or 'Date' not in prod_df.columns or 'Output_Units' not in prod_df.columns:
        return 0
    
    prod_df['Date'] = pd.to_datetime(prod_df['Date'])
    last_30_days = prod_df[prod_df['Date'] >= datetime.now() - timedelta(days=30)]
    
    if last_30_days.empty:
        return 0
    
    total_consumption = 0
    
    for _, row in last_30_days.iterrows():
        product = row['Product']
        quantity = row['Output_Units']
        
        required, _ = get_materials_required(product, quantity)
        if required and material_name in required:
            total_consumption += required[material_name]
    
    daily_avg = total_consumption / 30 if total_consumption > 0 else 0
    return daily_avg

def get_stock_prediction_calculated(df_raw, df_main, selected_line):
    predictions = []
    
    if df_main is None or df_main.empty or df_raw is None or df_raw.empty:
        return predictions
    
    line_data = CONFIG.get(selected_line, CONFIG["الخط الأول(smi)"])
    products = line_data["products"]
    speeds = [line_data["speed"][p] for p in products]
    
    if not speeds:
        return predictions
    
    avg_speed = sum(speeds) / len(speeds)
    daily_units = avg_speed * 15
    
    material_consumption = {}
    
    material_consumption["غطاء"] = FIXED_CAP_CONSUMPTION
    
    for product in products:
        product_ratio = 1 / len(products)
        product_daily_units = daily_units * product_ratio
        
        if product in BOM:
            for material, qty in BOM[product].items():
                if material == "غطاء":
                    continue
                elif qty < 1:
                    consumption = math.ceil(product_daily_units * qty)
                else:
                    consumption = product_daily_units * qty
                material_consumption[material] = material_consumption.get(material, 0) + consumption
    
    for _, row in df_raw.iterrows():
        material_name = row['Material_Name_AR']
        current_stock = float(row['Current_Stock']) if pd.notna(row['Current_Stock']) else 0
        
        if current_stock <= 0:
            days_left = 0
        else:
            daily_consumption = material_consumption.get(material_name, 0)
            if daily_consumption == 0:
                daily_consumption = calculate_daily_consumption_for_material(df_main, material_name)
            
            if daily_consumption > 0:
                days_left = current_stock / daily_consumption
            else:
                days_left = 999
        
        if days_left < 60:
            if days_left < 7:
                status = "critical"
            elif days_left < 14:
                status = "warning"
            else:
                status = "info"
            
            predictions.append({
                "material": material_name,
                "current": int(current_stock),
                "days_left": round(days_left, 1),
                "daily_consumption": int(daily_consumption),
                "status": status
            })
    
    predictions.sort(key=lambda x: x["days_left"])
    return predictions

def get_marquee_recommendations(df_raw, df_main, df_fg, t, lang, selected_line):
    recommendations = []
    
    reorder = get_auto_reorder_suggestions(df_raw, df_main)
    for rec in reorder[:3]:
        if rec["urgency"] == "high":
            recommendations.append(f"🔴 {t['auto_reorder']}: {rec['material']} - الرصيد {rec['current']:,}")
        else:
            recommendations.append(f"🟡 {t['auto_reorder']}: {rec['material']} - الكمية المقترحة {rec['suggested_qty']:,}")
    
    stock_pred = get_stock_prediction_calculated(df_raw, df_main, selected_line)
    for pred in stock_pred[:3]:
        if pred["status"] == "critical":
            recommendations.append(f"⚠️ {t['stock_prediction']}: {pred['material']} سينفذ خلال {pred['days_left']} يوم")
        elif pred["status"] == "warning":
            recommendations.append(f"📦 {t['stock_prediction']}: {pred['material']} سينفذ خلال {pred['days_left']} يوم")
        else:
            recommendations.append(f"ℹ️ {t['stock_prediction']}: {pred['material']} سينفذ خلال {pred['days_left']} يوم")
    
    if df_fg is not None and not df_fg.empty and "Balance" in df_fg.columns:
        fg_balance = df_fg["Balance"].sum()
        if fg_balance <= 0:
            recommendations.append(f"🏭 {t['fg_balance']}: فارغ - يرجى زيادة الإنتاج")
        elif fg_balance < 10000:
            recommendations.append(f"📦 {t['fg_balance']}: {fg_balance:,.0f} وحدة")
    
    if not recommendations:
        recommendations.append(f"✅ {t['all_good']} ✅")
    
    return recommendations

def show_marquee(df_raw, df_main, df_fg, t, lang, selected_line):
    recommendations = get_marquee_recommendations(df_raw, df_main, df_fg, t, lang, selected_line)
    
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
# 12. دوال مخزن الإنتاج التام
# ============================================================================
def add_delivery_record(product_name, quantity, customer, notes, df_main):
    new_record = pd.DataFrame([{
        "Type": "Delivery",
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Product": product_name,
        "Quantity": quantity,
        "Customer": customer,
        "Notes": notes,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    
    if df_main is None or df_main.empty:
        return new_record
    else:
        return pd.concat([df_main, new_record], ignore_index=True)

def remove_from_finished_goods_delivery(product_name, quantity, df_fg):
    idx = df_fg[df_fg["Name"] == product_name].index
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
    
    return df_fg, True, f"✅ تم تسليم {quantity:,.0f} وحدة من {product_name}"

def update_finished_goods_manual_balance(product_name, new_balance, df_fg):
    idx = df_fg[df_fg["Name"] == product_name].index
    if len(idx) == 0:
        return df_fg, False, f"⚠️ المنتج {product_name} غير موجود"
    
    idx = idx[0]
    old_balance = df_fg.at[idx, "Balance"] if pd.notna(df_fg.at[idx, "Balance"]) else 0
    old_in = df_fg.at[idx, "In"] if pd.notna(df_fg.at[idx, "In"]) else 0
    
    diff = new_balance - old_balance
    
    df_fg.at[idx, "Balance"] = new_balance
    if diff > 0:
        df_fg.at[idx, "In"] = old_in + diff
    df_fg.at[idx, "Last_Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return df_fg, True, f"✅ تم تعديل رصيد {product_name} من {old_balance:,.0f} إلى {new_balance:,.0f}"

# ============================================================================
# 13. لوحة القيادة - مخططات دائرية جذابة
# ============================================================================
def show_dashboard(df_main, df_raw, df_fg, t, selected_line):
    lang = st.session_state.get('lang', 'ar')
    
    # زيادة عداد الأنيميشن
    st.session_state.chart_animation_counter += 1
    
    st.markdown(f"""
    <div class="page-title">
        <h1>🏭 BIRMA - {t['dashboard_title']}</h1>
    </div>
    """, unsafe_allow_html=True)
    
    if df_raw is not None and df_fg is not None:
        show_marquee(df_raw, df_main, df_fg, t, lang, selected_line)
    
    total_prod = 0
    monthly_prod = 0
    line1_efficiency = 0
    line2_efficiency = 0
    line1_count = 0
    line2_count = 0
    line1_color = "#22c55e"
    line2_color = "#22c55e"
    
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
    
    line1_color = "#22c55e" if line1_efficiency >= 80 else "#eab308" if line1_efficiency >= 60 else "#ef4444"
    line2_color = "#22c55e" if line2_efficiency >= 80 else "#eab308" if line2_efficiency >= 60 else "#ef4444"
    
    fg_balance = int(df_fg["Balance"].sum()) if df_fg is not None and not df_fg.empty and "Balance" in df_fg.columns else 0
    
    # كروت الميتريك
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📦 {t['total_production']}</h3>
            <div class="value">{total_prod:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📅 {t['monthly_production']}</h3>
            <div class="value">{monthly_prod:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🏭 {t['fg_balance']}</h3>
            <div class="value">{fg_balance:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        avg_eff = (line1_efficiency + line2_efficiency) / 2 if (line1_efficiency > 0 or line2_efficiency > 0) else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>⚡ {t['eff_title']}</h3>
            <div class="value">{avg_eff:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # مخططات الكفاءة الدائرية
    st.markdown(f'<h2 style="text-align: center; margin: 20px 0;">⚡ {t["eff_title"]}</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # مخطط دائري للخط الأول
        fig1 = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=line1_efficiency,
            title={"text": f"{t['line1_efficiency']}<br><span style='font-size:14px'>📊 {line1_count} {t['history_p']}</span>", 
                   "font": {"size": 18, "color": "#1e293b"}},
            domain={"x": [0, 1], "y": [0, 1]},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94a3b8", 
                        "tickfont": {"size": 11, "color": "#64748b"}},
                "bar": {"color": line1_color, "thickness": 0.3},
                "bgcolor": "#ffffff",
                "borderwidth": 1,
                "bordercolor": "#e2e8f0",
                "steps": [
                    {"range": [0, 60], "color": "#fef2f2"},
                    {"range": [60, 80], "color": "#fffbeb"},
                    {"range": [80, 100], "color": "#f0fdf4"}
                ],
                "threshold": {
                    "line": {"color": "#dc2626", "width": 3},
                    "thickness": 0.75,
                    "value": 85
                }
            },
            number={"font": {"size": 44, "color": line1_color}, "suffix": "%"},
            delta={"reference": 80, "increasing": {"color": "#16a34a"}, "decreasing": {"color": "#dc2626"}}
        ))
        fig1.update_layout(
            height=350, 
            margin=dict(l=20, r=20, t=60, b=20), 
            paper_bgcolor="#ffffff",
            font={"color": "#1e293b"}
        )
        st.plotly_chart(fig1, use_container_width=True, key=f"gauge1_{st.session_state.chart_animation_counter}")
    
    with col2:
        # مخطط دائري للخط الثاني
        fig2 = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=line2_efficiency,
            title={"text": f"{t['line2_efficiency']}<br><span style='font-size:14px'>📊 {line2_count} {t['history_p']}</span>", 
                   "font": {"size": 18, "color": "#1e293b"}},
            domain={"x": [0, 1], "y": [0, 1]},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94a3b8", 
                        "tickfont": {"size": 11, "color": "#64748b"}},
                "bar": {"color": line2_color, "thickness": 0.3},
                "bgcolor": "#ffffff",
                "borderwidth": 1,
                "bordercolor": "#e2e8f0",
                "steps": [
                    {"range": [0, 60], "color": "#fef2f2"},
                    {"range": [60, 80], "color": "#fffbeb"},
                    {"range": [80, 100], "color": "#f0fdf4"}
                ],
                "threshold": {
                    "line": {"color": "#dc2626", "width": 3},
                    "thickness": 0.75,
                    "value": 85
                }
            },
            number={"font": {"size": 44, "color": line2_color}, "suffix": "%"},
            delta={"reference": 80, "increasing": {"color": "#16a34a"}, "decreasing": {"color": "#dc2626"}}
        ))
        fig2.update_layout(
            height=350, 
            margin=dict(l=20, r=20, t=60, b=20), 
            paper_bgcolor="#ffffff",
            font={"color": "#1e293b"}
        )
        st.plotly_chart(fig2, use_container_width=True, key=f"gauge2_{st.session_state.chart_animation_counter}")
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # عرض الأرصدة
    st.markdown('<h2 style="margin: 20px 0;">📊 نظرة عامة على المخزون</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f'<div class="info-box"><h3>📦 {t["raw_balance"]}</h3>', unsafe_allow_html=True)
        if df_raw is not None and not df_raw.empty:
            for _, row in df_raw.head(10).iterrows():
                stock = row['Current_Stock']
                min_stock = row['Min_Stock']
                if stock <= min_stock:
                    item_class = "stock-item-low"
                elif stock <= min_stock * 1.5:
                    item_class = "stock-item-warning"
                else:
                    item_class = "stock-item-safe"
                st.markdown(f"""
                <div class="{item_class}" style="display: flex; justify-content: space-between; align-items: center;">
                    <span>🔹 <strong>{row['Material_Name_AR']}</strong></span>
                    <span style="font-weight: bold;">{stock:,.0f} {row['Unit']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("لا توجد بيانات")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'<div class="info-box"><h3>🏭 {t["fg_balance"]}</h3>', unsafe_allow_html=True)
        if df_fg is not None and not df_fg.empty:
            for _, row in df_fg.iterrows():
                balance = row['Balance']
                if balance <= 5000:
                    item_class = "stock-item-low"
                elif balance <= 20000:
                    item_class = "stock-item-warning"
                else:
                    item_class = "stock-item-safe"
                st.markdown(f"""
                <div class="{item_class}" style="display: flex; justify-content: space-between; align-items: center;">
                    <span>🔹 <strong>{row['Name']}</strong></span>
                    <span style="font-weight: bold;">{balance:,.0f} {row['Unit']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("لا توجد بيانات")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # التوصيات الذكية
    st.markdown(f'<h2 style="text-align: center; margin: 20px 0;">🤖 {t["smart_recommendations"]}</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if df_raw is not None:
            reorder = get_auto_reorder_suggestions(df_raw, df_main)
            if reorder:
                st.markdown(f'<div class="warning-box"><h4>📦 {t["auto_reorder"]}</h4>', unsafe_allow_html=True)
                for rec in reorder[:3]:
                    if rec["urgency"] == "high":
                        st.error(f"🔴 **{rec['material']}** : الرصيد {rec['current']:,} (الحد الأدنى {rec['min_stock']:,})")
                        st.warning(f"   ➕ اقتراح إعادة طلب: {rec['suggested_qty']:,}")
                    else:
                        st.warning(f"🟡 **{rec['material']}** : الرصيد {rec['current']:,} (الحد الأدنى {rec['min_stock']:,})")
                        st.info(f"   ➕ اقتراح إعادة طلب: {rec['suggested_qty']:,}")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="success-box"><h4>✅ {t["all_good"]}</h4></div>', unsafe_allow_html=True)
    
    with col2:
        if df_raw is not None:
            stock_pred = get_stock_prediction_calculated(df_raw, df_main, selected_line)
            if stock_pred:
                st.markdown(f'<div class="info-box"><h4>⏰ {t["stock_prediction"]}</h4>', unsafe_allow_html=True)
                for pred in stock_pred[:5]:
                    if pred["status"] == "critical":
                        st.error(f"🔴 **{pred['material']}** : رصيد {pred['current']:,} - سينفذ خلال {pred['days_left']} يوم")
                    elif pred["status"] == "warning":
                        st.warning(f"🟡 **{pred['material']}** : رصيد {pred['current']:,} - سينفذ خلال {pred['days_left']} يوم")
                    else:
                        st.info(f"ℹ️ **{pred['material']}** : رصيد {pred['current']:,} - سينفذ خلال {pred['days_left']} يوم")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="success-box"><h4>✅ {t["all_good"]}</h4></div>', unsafe_allow_html=True)

# ============================================================================
# 14. واجهة تسجيل الدخول
# ============================================================================
def login_screen(t):
    saved_user, saved_pass, _ = load_credentials_local()
    
    if saved_user and saved_pass:
        if saved_user in USERS and USERS[saved_user]["password"] == saved_pass:
            st.session_state.authenticated = True
            st.session_state.user_role = USERS[saved_user]["role"]
            st.session_state.user_name = USERS[saved_user]["name"]
            st.rerun()
    
    # شاشة دخول بسيطة
    st.markdown("""
    <div style="text-align: center; padding: 40px 0;">
        <div style="background: #f8fafc; border-radius: 50%; width: 100px; height: 100px; margin: 0 auto; display: flex; align-items: center; justify-content: center; border: 1px solid #e2e8f0;">
            <span style="font-size: 50px;">🏭</span>
        </div>
        <h1 style="color: #1e293b; margin-top: 20px;">BIRMA System</h1>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input(t["username"], placeholder="أدخل اسم المستخدم")
            password = st.text_input(t["password"], type="password", placeholder="أدخل كلمة المرور")
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
# 15. الواجهة الرئيسية
# ============================================================================
def main():
    if not st.session_state.authenticated:
        login_screen(LANG["ar"])
        return
    
    show_current_date()
    
    # الوضع الليلي (اختياري)
    dark_mode = st.sidebar.toggle(LANG[st.session_state.lang]["dark_mode"], value=st.session_state.dark_mode)
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.rerun()
    
    # تطبيق الوضع الليلي إذا تم اختياره
    if st.session_state.dark_mode:
        st.markdown("""
            <style>
            .stApp { background-color: #0f172a; }
            .data-card, .metric-card, .production-card, .info-box, .warning-box, .danger-box, .success-box,
            .stock-item-low, .stock-item-warning, .stock-item-safe {
                background: #1e293b;
                border-color: #334155;
                color: #e2e8f0;
            }
            .metric-card .value { color: #f1f5f9; }
            .metric-card h3 { color: #94a3b8; }
            .page-title h1 { color: #f1f5f9; }
            .stTabs [data-baseweb="tab"] { background: #1e293b; color: #e2e8f0; }
            .stTabs [aria-selected="true"] { background: #3b82f6; }
            [data-testid="stSidebar"] { background: #0f172a; }
            [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
            </style>
        """, unsafe_allow_html=True)
    
    st.sidebar.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    if os.path.exists("birma mark.png"):
        st.sidebar.image("birma mark.png", use_container_width=True)
    else:
        st.sidebar.markdown("<h1 style='color: #1e293b; text-align: center;'>🏭 BIRMA</h1>", unsafe_allow_html=True)
    st.sidebar.markdown("</div>", unsafe_allow_html=True)
    
    st.sidebar.divider()
    
    st.sidebar.markdown(f"<p style='text-align: center; font-size: 12px; color: #64748b; margin-bottom: 0;'>Designed by:</p>", unsafe_allow_html=True)
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
    
    if df_raw is None or df_fg is None:
        st.error("❌ لا يمكن تحميل بيانات المخزون. يرجى التأكد من وجود الملفات المطلوبة.")
        st.stop()
    
    # ========== Dashboard ==========
    if selected_raw == "🏠 Dashboard":
        show_dashboard(df_main, df_raw, df_fg, t, selected_line if selected_line else "الخط الأول(smi)")
    
    # ========== Production ==========
    elif selected_raw == "📈 Production" and selected_line:
        st.markdown(f"""
        <div class="production-card">
            <h2 style="color: #1e293b;">📈 {t['production']} - {selected_line}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("prod_form"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input(t["sup_label"], placeholder="أدخل اسم المشرف")
                product = st.selectbox(t["prod_label"], CONFIG[selected_line]["products"])
                target = st.number_input(t["target_label"], min_value=0, step=100)
            with c2:
                preforms = st.number_input(t["preform_label"], min_value=0, step=100)
                raw_val = st.number_input(t["raw_label"], min_value=0, step=100)
                p_date = st.date_input(t["date_label"])
            
            if st.form_submit_button(t["save_btn"], use_container_width=True):
                if target <= 0:
                    st.error("⚠️ الكمية يجب أن تكون أكبر من صفر")
                elif not name:
                    st.error("⚠️ يرجى إدخال اسم المشرف")
                else:
                    packs = CONFIG[selected_line]["pack_per_unit"][product]
                    speed = CONFIG[selected_line]["speed"][product]
                    eff = round((target * packs / (speed * 15)) * 100, 1) if speed > 0 else 0
                    waste_bottles = preforms - (target * packs) if preforms > 0 else 0
                    
                    # 1. صرف المواد الخام تلقائياً
                    new_raw, raw_ok, raw_msg = consume_materials(product, target, df_raw)
                    
                    if not raw_ok:
                        st.error(f"❌ فشل صرف المواد: {raw_msg}")
                    else:
                        if update_raw_materials(new_raw):
                            st.success(f"✅ {raw_msg}")
                            
                            # 2. حفظ سجل الإنتاج
                            new_row = pd.DataFrame([{
                                "Type": "Production", "Date": str(p_date), "Line": selected_line,
                                "Supervisor": name, "Product": product, "Output_Units": int(target),
                                "Preforms_Used": int(preforms), "Waste_Bottles": int(waste_bottles),
                                "Efficiency_%": float(eff),
                                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }])
                            if conn:
                                if df_main.empty:
                                    save_to_sheet(conn, new_row)
                                else:
                                    save_to_sheet(conn, pd.concat([df_main, new_row], ignore_index=True))
                            
                            # 3. إضافة المنتج التام تلقائياً
                            new_fg, fg_ok, fg_msg = add_to_finished_goods(product, target, df_fg)
                            
                            if fg_ok:
                                update_finished_goods(new_fg)
                                st.success(fg_msg)
                            else:
                                st.warning(fg_msg)
                            
                            send_telegram(f"🚀 Production: {product} - {target} units - {eff}%")
                            st.success(f"✅ تم تسجيل الإنتاج بنجاح")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ فشل في حفظ تحديثات المواد الخام")
    
    # ========== Maintenance ==========
    elif selected_raw == "🔧 Maintenance" and selected_line:
        st.header(t["maint_header"])
        m_type = st.radio("Type", t["maint_types"], horizontal=True)
        machine = st.sidebar.selectbox(t["machine_select"], list(MACHINE_MAP.keys()))
        
        if m_type == t["maint_types"][0]:
            path = MACHINE_MAP[machine]
            if not os.path.exists(path):
                create_machine_file(path)
            
            if "Compressor" in path or "AF_Compressor" in path:
                try:
                    df_tasks = pd.read_excel(path, header=2)
                    column_mapping = {
                        'cat': 'Cat', 'no': 'No', 'name': 'Name', 'photo': 'Photo',
                        'tools': 'Tools', 'proc': 'Proc', 'freq': 'Freq',
                        'stat': 'Stat', 'note': 'Note', 'staff': 'Staff'
                    }
                    for old, new in column_mapping.items():
                        if old in df_tasks.columns:
                            df_tasks = df_tasks.rename(columns={old: new})
                    
                    required_cols = ['Cat', 'No', 'Name', 'Photo', 'Tools', 'Proc', 'Freq', 'Stat', 'Note', 'Staff']
                    for col in required_cols:
                        if col not in df_tasks.columns:
                            df_tasks[col] = ''
                    
                    df_tasks = df_tasks.dropna(subset=['Name'], how='all')
                    df_tasks = df_tasks[df_tasks['Name'].notna()]
                    df_tasks = df_tasks.reset_index(drop=True)
                except Exception as e:
                    st.error(f"خطأ في قراءة ملف الكمبروسر: {e}")
                    df_tasks = pd.DataFrame()
            else:
                try:
                    df_tasks = pd.read_excel(path, skiprows=2)
                    df_tasks.columns = ['Cat', 'No', 'Name', 'Photo', 'Tools', 'Proc', 'Freq', 'Stat', 'Note', 'Staff']
                except:
                    df_tasks = pd.read_excel(path)
                    if 'Freq' not in df_tasks.columns and 'Frequency' in df_tasks.columns:
                        df_tasks = df_tasks.rename(columns={'Frequency': 'Freq'})
                    if 'Name' not in df_tasks.columns and 'Task' in df_tasks.columns:
                        df_tasks = df_tasks.rename(columns={'Task': 'Name'})
            
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
                                done = st.checkbox(t["done"], key=f"done_{i}")
                            if done:
                                recs.append({
                                    "Type": "Maintenance_Planned", "Line": selected_line,
                                    "Date": str(datetime.now().date()), "Machine": machine,
                                    "Task": task_name, "Technician": tech, "Notes": note,
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
            with st.form("break_form"):
                tech = st.text_input(t["tech_label"])
                issue = st.text_area(t["issue_label"])
                t1 = st.time_input(t["start_t"])
                t2 = st.time_input(t["end_t"])
                notes = st.text_area(t["note_label"])
                if st.form_submit_button(t["save_btn"]):
                    new_b = pd.DataFrame([{
                        "Type": "Maintenance_Breakdown", "Line": selected_line,
                        "Date": str(datetime.now().date()), "Machine": machine,
                        "Technician": tech, "Issue": issue,
                        "Start_Time": t1.strftime("%H:%M"), "End_Time": t2.strftime("%H:%M"),
                        "Notes": notes, "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
            
            tab1, tab2, tab3 = st.tabs([t["history_p"], t["history_m"], t["history_delivery"]])
            
            with tab1:
                prod_logs = df_main[df_main['Type'] == 'Production'] if 'Type' in df_main.columns else pd.DataFrame()
                if not prod_logs.empty:
                    prod_logs = prod_logs.reset_index(drop=True)
                    if 'Waste_Bottles' not in prod_logs.columns:
                        prod_logs['Waste_Bottles'] = 0
                    
                    display_cols = ['Date', 'Line', 'Supervisor', 'Product', 'Output_Units', 'Preforms_Used', 'Waste_Bottles', 'Efficiency_%']
                    available_cols = [col for col in display_cols if col in prod_logs.columns]
                    display_df = prod_logs[available_cols].copy()
                    
                    if lang == "ar":
                        display_df = display_df.rename(columns={
                            'Date': 'التاريخ', 'Line': 'الخط', 'Supervisor': 'المشرف',
                            'Product': 'المنتج', 'Output_Units': 'الكمية', 'Preforms_Used': 'البريفورم',
                            'Waste_Bottles': t['waste_bottles'], 'Efficiency_%': 'الكفاءة'
                        })
                    else:
                        display_df = display_df.rename(columns={
                            'Date': 'Date', 'Line': 'Line', 'Supervisor': 'Supervisor',
                            'Product': 'Product', 'Output_Units': 'Qty', 'Preforms_Used': 'Preforms',
                            'Waste_Bottles': 'Waste', 'Efficiency_%': 'Efficiency'
                        })
                    
                    if 'التاريخ' in display_df.columns or 'Date' in display_df.columns:
                        date_col = 'التاريخ' if 'التاريخ' in display_df.columns else 'Date'
                        display_df[date_col] = pd.to_datetime(display_df[date_col])
                        display_df = display_df[display_df[date_col] >= ten_days_ago]
                        display_df = display_df.sort_values(date_col, ascending=False)
                    
                    if not display_df.empty:
                        st.dataframe(display_df, use_container_width=True)
                        st.caption(f"📊 {t['last_10_days']} - {len(display_df)} {t['history_p']}")
                    else:
                        st.info(t["no_production"])
                else:
                    st.info(t["no_production"])
            
            with tab2:
                maint_logs = df_main[df_main['Type'].str.contains('Maintenance', na=False)] if 'Type' in df_main.columns else pd.DataFrame()
                if not maint_logs.empty:
                    maint_logs = maint_logs.reset_index(drop=True)
                    if lang == "ar":
                        display_df = maint_logs[['Date', 'Type', 'Machine', 'Technician', 'Task', 'Notes']].copy()
                        display_df = display_df.rename(columns={
                            'Date': 'التاريخ', 'Type': 'النوع', 'Machine': 'الماكينة',
                            'Technician': 'الفني', 'Task': 'المهمة', 'Notes': 'ملاحظات'
                        })
                    else:
                        display_df = maint_logs[['Date', 'Type', 'Machine', 'Technician', 'Task', 'Notes']].copy()
                        display_df = display_df.rename(columns={
                            'Date': 'Date', 'Type': 'Type', 'Machine': 'Machine',
                            'Technician': 'Tech', 'Task': 'Task', 'Notes': 'Notes'
                        })
                    
                    if 'Date' in display_df.columns:
                        display_df['Date'] = pd.to_datetime(display_df['Date'])
                        display_df = display_df[display_df['Date'] >= ten_days_ago]
                        display_df = display_df.sort_values('Date', ascending=False)
                    
                    if not display_df.empty:
                        st.dataframe(display_df, use_container_width=True)
                        st.caption(f"📊 {t['last_10_days']} - {len(display_df)} {t['history_m']}")
                    else:
                        st.info(t["no_maintenance"])
                else:
                    st.info(t["no_maintenance"])
            
            with tab3:
                delivery_logs = df_main[df_main['Type'] == 'Delivery'] if 'Type' in df_main.columns else pd.DataFrame()
                if not delivery_logs.empty:
                    delivery_logs = delivery_logs.reset_index(drop=True)
                    if lang == "ar":
                        display_df = delivery_logs[['Date', 'Product', 'Quantity', 'Customer', 'Notes', 'Timestamp']].copy()
                        display_df = display_df.rename(columns={
                            'Date': 'التاريخ', 'Product': 'المنتج', 'Quantity': 'الكمية',
                            'Customer': 'العميل', 'Notes': 'ملاحظات', 'Timestamp': 'الوقت'
                        })
                    else:
                        display_df = delivery_logs[['Date', 'Product', 'Quantity', 'Customer', 'Notes', 'Timestamp']].copy()
                        display_df = display_df.rename(columns={
                            'Date': 'Date', 'Product': 'Product', 'Quantity': 'Qty',
                            'Customer': 'Customer', 'Notes': 'Notes', 'Timestamp': 'Time'
                        })
                    
                    if 'Date' in display_df.columns:
                        display_df['Date'] = pd.to_datetime(display_df['Date'])
                        display_df = display_df[display_df['Date'] >= ten_days_ago]
                        display_df = display_df.sort_values('Date', ascending=False)
                    
                    if not display_df.empty:
                        st.dataframe(display_df, use_container_width=True)
                        st.caption(f"📊 {t['last_10_days']} - {len(display_df)} {t['history_delivery']}")
                    else:
                        st.info(t["no_delivery"])
                else:
                    st.info(t["no_delivery"])
        else:
            st.info(t["no_data"])
    
    # ========== Raw Materials ==========
    elif selected_raw == "📦 Raw Materials":
        st.header(t["raw_materials"])
        
        if df_raw is not None and not df_raw.empty:
            tab1, tab2 = st.tabs([t["current_stock"], t["receipt"]])
            with tab1:
                st.dataframe(df_raw, use_container_width=True)
                with st.expander(t["edit_stock"]):
                    if st.text_input(t["password"], type="password") in ["admin123", "100"]:
                        material = st.selectbox(t["material"], df_raw["Material_Name_AR"])
                        new_qty = st.number_input(t["new_stock"], min_value=0)
                        if st.button(t["update"]):
                            idx = df_raw[df_raw["Material_Name_AR"] == material].index[0]
                            old_qty = df_raw.at[idx, "Current_Stock"]
                            df_raw.at[idx, "Current_Stock"] = new_qty
                            df_raw.at[idx, "Last_Updated"] = datetime.now().strftime("%Y-%m-%d")
                            update_raw_materials(df_raw)
                            st.success(f"{t['stock_updated']}: {material} من {old_qty:,.0f} إلى {new_qty:,.0f}")
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
        
        if df_fg is not None and not df_fg.empty:
            if lang == "ar":
                display_df = df_fg[['Name', 'In', 'Out', 'Balance', 'Unit']].copy()
                display_df = display_df.rename(columns={'Name': 'المنتج', 'In': t['in'], 'Out': t['out'], 'Balance': t['balance'], 'Unit': 'الوحدة'})
            else:
                display_df = df_fg[['Name', 'In', 'Out', 'Balance', 'Unit']].copy()
                display_df = display_df.rename(columns={'Name': 'Product', 'In': t['in'], 'Out': t['out'], 'Balance': t['balance'], 'Unit': 'Unit'})
            
            st.dataframe(display_df, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(t['in'], f"{df_fg['In'].sum():,.0f}")
            with col2:
                st.metric(t['out'], f"{df_fg['Out'].sum():,.0f}")
            with col3:
                st.metric(t['balance'], f"{df_fg['Balance'].sum():,.0f}")
            
            st.markdown("---")
            
            tab_delivery, tab_manual = st.tabs([t["delivery"], t["manual_adjust"]])
            
            with tab_delivery:
                st.subheader(f"🚚 {t['delivery']}")
                with st.form("delivery_form"):
                    product = st.selectbox(t["product"], df_fg["Name"])
                    qty = st.number_input(t["quantity_to_deliver"], min_value=0, step=100, key="delivery_qty")
                    customer = st.text_input(t["customer"])
                    notes = st.text_area(t["note_label"])
                    
                    if st.form_submit_button(t["register_shipping"], use_container_width=True):
                        if qty <= 0:
                            st.error("⚠️ الكمية يجب أن تكون أكبر من صفر")
                        else:
                            new_fg, ok, msg = remove_from_finished_goods_delivery(product, qty, df_fg)
                            if ok:
                                update_finished_goods(new_fg)
                                
                                updated_main = add_delivery_record(product, qty, customer, notes, df_main)
                                if conn:
                                    save_to_sheet(conn, updated_main)
                                
                                send_telegram(f"🚚 تسليم: {product} - {qty:,.0f} وحدة - {customer}")
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
            
            with tab_manual:
                st.subheader(f"✏️ {t['manual_adjust']}")
                if st.text_input(t["password"], type="password", key="fg_manual_pw") in ["admin123", "100"]:
                    product = st.selectbox(t["product"], df_fg["Name"], key="manual_product")
                    current = df_fg[df_fg["Name"] == product]["Balance"].values[0]
                    new_balance = st.number_input(t["new_stock"], min_value=0, value=int(current), key="manual_balance")
                    if st.button(t["update"]):
                        new_fg, ok, msg = update_finished_goods_manual_balance(product, new_balance, df_fg)
                        if ok:
                            update_finished_goods(new_fg)
                            st.success(msg)
                            st.rerun()
                else:
                    st.warning("🔒 يرجى إدخال كلمة مرور المشرف")
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
        pw = st.text_input(t["password"], type="password", key="del_pw")
        if pw in ["admin123", "100"]:
            if df_main is not None and not df_main.empty:
                df_display = df_main.copy()
                if 'Type' in df_display.columns and 'Date' in df_display.columns:
                    def fmt(row):
                        if row['Type'] == 'Production':
                            return f"📦 {t['production']} | {row['Date']} | {row.get('Product', 'N/A')} | {row.get('Output_Units', 0)} {t['quantity']}"
                        elif row['Type'] == 'Delivery':
                            return f"🚚 {t['delivery']} | {row['Date']} | {row.get('Product', 'N/A')} | {row.get('Customer', 'N/A')}"
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
                            
                            if df_fg is not None and not df_fg.empty:
                                fg_name = get_finished_goods_name(product_name)
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
    st.sidebar.markdown(f"<center><small>BIRMA v24.0<br>{t['designer']}</small></center>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()