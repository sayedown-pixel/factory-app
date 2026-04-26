import streamlit as st
import pandas as pd
import os
import requests
import urllib.parse
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import plotly.graph_objects as go
import plotly.express as px
from sklearn.linear_model import LinearRegression

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="BIRMA Integrated System", page_icon="🏭", layout="wide")

# --- 2. نظام اللغات (قاموس النصوص) ---
LANG = {
    "ar": {
        "sidebar_title": "🏭 نظام بيرما الموحد",
        "menu": ["📈 إدارة الإنتاج", "🔧 مركز الصيانة المتكامل", "📊 التقارير الختامية"],
        "line_label": "خط العمل الحالي",
        "pwd_label": "كلمة المرور",
        "pwd_msg": "🔑 يرجى إدخال كلمة المرور للوصول",
        "prod_header": "🚀 تسجيل إنتاج -",
        "maint_header": "🛠 مركز صيانة",
        "maint_type_label": "نوع العملية",
        "maint_types": ["صيانة دورية (Daily Check)", "بلاغ أعطال (Breakdown)"],
        "machine_label": "اختر الماكينة",
        "tech_label": "الفني المسؤول",
        "sup_label": "المشرف المسؤول",
        "product_label": "الصنف المنتج",
        "target_label": "الإنتاج النهائي (وحدة)",
        "preform_label": "البريفورم المستخدم",
        "date_label": "التاريخ",
        "save_btn": "حفظ البيانات",
        "success_msg": "✅ تم الحفظ بنجاح",
        "issue_label": "وصف العطل",
        "action_label": "الإجراء المتخذ",
        "status_label": "حالة المعدة",
        "status_options": ["جاهزة للعمل", "تحت الصيانة", "انتظار قطع غيار"]
    },
    "en": {
        "sidebar_title": "🏭 BIRMA Integrated System",
        "menu": ["📈 Production Management", "🔧 Maintenance Center", "📊 Final Reports"],
        "line_label": "Current Working Line",
        "pwd_label": "Password",
        "pwd_msg": "🔑 Please enter password to access",
        "prod_header": "🚀 Production Entry -",
        "maint_header": "🛠 Maintenance Center",
        "maint_type_label": "Process Type",
        "maint_types": ["Daily Maintenance (Check)", "Breakdown Report"],
        "machine_label": "Select Machine",
        "tech_label": "Responsible Technician",
        "sup_label": "Responsible Supervisor",
        "product_label": "Product Type",
        "target_label": "Final Output (Units)",
        "preform_label": "Preforms Used",
        "date_label": "Date",
        "save_btn": "Save Data",
        "success_msg": "✅ Saved successfully",
        "issue_label": "Issue Description",
        "action_label": "Action Taken",
        "status_label": "Machine Status",
        "status_options": ["Ready for Work", "Under Maintenance", "Waiting for Spare Parts"]
    }
}

# --- 3. اختيار اللغة في القائمة الجانبية ---
ln = st.sidebar.selectbox("🌐 Language / اللغة", ["ar", "en"])

# --- 4. الربط بجوجل شيت ---
try:
    URL_DATA = st.secrets["connections"]["gsheets_testing"]["spreadsheet"]
    conn = st.connection("gsheets_testing", type=GSheetsConnection)
except Exception as e:
    st.error("Connection Error: Check Secrets")
    st.stop()

# --- 5. الإعدادات الفنية (الماكينات والخطوط) ---
CONFIG = {
    "الخط الأول(smi)": {
        "الأصناف": ["200 ml Carton", "200 ml Shrink", "600 ml Carton", "1.5 L Shrink"],
        "العبوات_في_الوحدة": {"200 ml Carton": 48, "200 ml Shrink": 20, "600 ml Carton": 30, "1.5 L Shrink": 6},
        "السرعة": {"200 ml Carton": 35000, "200 ml Shrink": 35000, "600 ml Carton": 20000, "1.5 L Shrink": 12000}
    },
    "الخط الثاني(welbing)": {
        "الأصناف": ["200 ml Carton", "200 ml Shrink", "330 ml Carton", "331 ml Shrink"],
        "العبوات_في_الوحدة": {"200 ml Carton": 48, "200 ml Shrink": 20, "330 ml Carton": 40, "331 ml Shrink": 20},
        "السرعة": {"200 ml Carton": 40000, "200 ml Shrink": 40000, "330 ml Carton": 40000, "331 ml Shrink": 40000}
    }
}

MACHINE_MAP = {
    "النفخ(blowing)": "blowing_machine.xlsx", 
    "الليبل(labelling)": "labeling_machine.xlsx", 
    "السيور(conveyor)": "Conveyor_machine.xlsx", 
    "الكرتون(carton)": "packing_machine.xlsx", 
    "البالتايزر(palitizer)": "paletizer_machine.xlsx", 
    "الشرنك(shrink)": "shrink_machine.xlsx", 
    "التعبئة(filling)": "Filling_machine.xlsx"
}

# --- 6. واجهة المستخدم ---
st.sidebar.title(LANG[ln]["sidebar_title"])
menu = st.sidebar.selectbox(LANG[ln]["menu"][0] if ln=="ar" else "Menu", LANG[ln]["menu"])
selected_line = st.sidebar.radio(LANG[ln]["line_label"], list(CONFIG.keys()))
pwd = st.sidebar.text_input(LANG[ln]["pwd_label"], type="password")

if pwd != "birma2026":
    st.warning(LANG[ln]["pwd_msg"])
    st.stop()

# تحميل البيانات العامة
try:
    df_main = conn.read(spreadsheet=URL_DATA, ttl=0)
except:
    df_main = pd.DataFrame()

# --- 7. قسم الإنتاج ---
if menu in [LANG["ar"]["menu"][0], LANG["en"]["menu"][0]]:
    st.header(f"{LANG[ln]['prod_header']} {selected_line}")
    with st.form("prod_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input(LANG[ln]["sup_label"])
            product = st.selectbox(LANG[ln]["product_label"], CONFIG[selected_line]["الأصناف"])
            target = st.number_input(LANG[ln]["target_label"], min_value=0)
        with c2:
            preforms = st.number_input(LANG[ln]["preform_label"], min_value=0)
            p_date = st.date_input(LANG[ln]["date_label"])
        
        if st.form_submit_button(LANG[ln]["save_btn"]):
            # (عملية الحساب والحفظ هنا...)
            st.success(LANG[ln]["success_msg"])

# --- 8. قسم الصيانة المتكامل (مع الصور واللغات) ---
elif menu in [LANG["ar"]["menu"][1], LANG["en"]["menu"][1]]:
    st.header(f"{LANG[ln]['maint_header']} {selected_line}")
    m_type = st.radio(LANG[ln]["maint_type_label"], LANG[ln]["maint_types"], horizontal=True)
    machine = st.sidebar.selectbox(LANG[ln]["machine_label"], list(MACHINE_MAP.keys()))

    if m_type == LANG[ln]["maint_types"][0]: # دورية
        file_path = MACHINE_MAP[machine]
        if os.path.exists(file_path):
            df_tasks = pd.read_excel(file_path, skiprows=2)
            df_tasks.columns = ['Category', 'No', 'Name', 'Photo', 'Tools', 'Procedure', 'Freq', 'Status', 'Note', 'Staff']
            daily_tasks = df_tasks[df_tasks['Freq'] == 'Daily']
            
            with st.form("maint_daily_form"):
                tech = st.text_input(LANG[ln]["tech_label"])
                records = []
                for i, row in daily_tasks.iterrows():
                    st.divider()
                    col_info, col_img = st.columns([2, 1])
                    with col_info:
                        st.markdown(f"### 🔧 {row['Name']}")
                        st.info(f"📝 {row['Procedure']}")
                        is_done = st.checkbox(f"OK - {row['Name']}", key=f"d_{i}")
                        note = st.text_input(f"Note - {row['Name']}", key=f"n_{i}")
                    with col_img:
                        img_path = os.path.join("images", str(row['Photo']).strip())
                        if os.path.exists(img_path):
                            st.image(img_path, use_container_width=True)
                    
                    if is_done:
                        records.append({"Type": "Maintenance_Daily", "Line": selected_line, "Date": str(datetime.now().date()), 
                                        "Machine": machine, "Task": row['Name'], "Staff": tech, "Notes": note})
                
                if st.form_submit_button(LANG[ln]["save_btn"]):
                    if tech and records:
                        conn.update(spreadsheet=URL_DATA, data=pd.concat([df_main, pd.DataFrame(records)], ignore_index=True))
                        st.success(LANG[ln]["success_msg"])
                        st.rerun()
    
    else: # بلاغ أعطال
        with st.form("breakdown_form"):
            t_name = st.text_input(LANG[ln]["tech_label"])
            issue = st.text_area(LANG[ln]["issue_label"])
            action = st.text_area(LANG[ln]["action_label"])
            status = st.selectbox(LANG[ln]["status_label"], LANG[ln]["status_options"])
            if st.form_submit_button(LANG[ln]["save_btn"]):
                st.success(LANG[ln]["success_msg"])

# --- 9. التقارير ---
elif menu in [LANG["ar"]["menu"][2], LANG["en"]["menu"][2]]:
    st.header(LANG[ln]["menu"][2])
    st.dataframe(df_main.tail(20)[::-1], use_container_width=True)