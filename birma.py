import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# --- 1. إعدادات الصفحة / Page Settings ---
st.set_page_config(page_title="BIRMA Integrated System", page_icon="🏭", layout="wide")

# الربط مع جوجل شيت
conn = st.connection("gsheets_secured", type=GSheetsConnection)

# --- 2. نظام اللغات الموحد / Localization System ---
LANG = {
    "ar": {
        "main_mode": "القائمة الرئيسية",
        "mode_prod": "📈 سجل الإنتاج اليومي",
        "mode_maint": "🔧 سجل الصيانة الفني",
        "line_label": "اختر خط الإنتاج",
        "date_label": "تاريخ يوم الإنتاج",
        "supervisor": "اسم المشرف المسؤول",
        "product": "الصنف المنتج",
        "preform": "البريفورم المستخدم (قطعة)",
        "raw_packaging": "الكرتون أو الشرنك الخام (عدد)",
        "output": "الإنتاج النهائي (كرتون/شرنك)",
        "submit": "إرسال التقرير والمزامنة",
        "waste_bottles": "هالك العبوات",
        "waste_pack": "هالك التغليف",
        "eff_label": "كفاءة التشغيل",
        "downtime_label": "وقت التوقف المحسوب",
        "success": "✅ تم الحفظ والمزامنة بنجاح!",
        "error": "❌ يرجى إدخال كافة البيانات الأساسية",
        "maint_staff": "توقيع الفني المسؤول",
        "unit_bottles": "عبوة",
        "hours": "ساعة",
        "maint_machine": "اختر الماكينة",
        "history_title": "📋 سجل التقارير السابقة (آخر 10 تقارير)",
        "empty_history": "لا توجد بيانات مسجلة حالياً."
    },
    "en": {
        "main_mode": "Main Menu",
        "mode_prod": "📈 Daily Production Report",
        "mode_maint": "🔧 Technical Maintenance Log",
        "line_label": "Select Production Line",
        "date_label": "Production Date",
        "supervisor": "Responsible Supervisor",
        "product": "Product Type",
        "preform": "Preforms Used (Pcs)",
        "raw_packaging": "Raw Packaging (Carton/Shrink)",
        "output": "Final Output (Carton/Shrink)",
        "submit": "Submit & Sync Report",
        "waste_bottles": "Bottle Waste",
        "waste_pack": "Packaging Waste",
        "eff_label": "Efficiency",
        "downtime_label": "Calculated Downtime",
        "success": "✅ Saved & Synced Successfully!",
        "error": "❌ Please fill all required fields",
        "maint_staff": "Technician Signature",
        "unit_bottles": "Pcs",
        "hours": "Hrs",
        "maint_machine": "Select Machine",
        "history_title": "📋 Production History (Last 10 Records)",
        "empty_history": "No records found."
    }
}

# --- 3. اختيار اللغة والخط ---
selected_lang = st.sidebar.selectbox("Language / اللغة", ["Arabic", "English"])
ln = "ar" if selected_lang == "Arabic" else "en"

st.sidebar.divider()
app_mode = st.sidebar.selectbox(LANG[ln]["main_mode"], [LANG[ln]["mode_prod"], LANG[ln]["mode_maint"]])
line_choice = st.sidebar.radio(LANG[ln]["line_label"], ["Line 1", "Line 2"])
line_key = "الخط الأول(smi)" if line_choice == "Line 1" else "الخط الثاني(welbing)"

# --- 4. بيانات الأصناف والماكينات ---
PRODUCTION_CONFIG = {
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

IMAGE_FOLDER = 'images'
MACHINE_MAP = {"النفخ(blowing)": "blowing_machine.xlsx", "الليبل(labelling)": "labeling_machine.xlsx", "السيور(conveyor)": "Conveyor_machine.xlsx", 
               "الكرتون(carton)": "packing_machine.xlsx", "البالتايزر(palitizer)": "paletizer_machine.xlsx", 
               "الشرنك(shrink)": "shrink_machine.xlsx", "التعبئة(filling)": "Filling_machine.xlsx"}

# --- 5. قسم الإنتاج ---
if app_mode == LANG[ln]["mode_prod"]:
    st.header(LANG[ln]["mode_prod"])
    yesterday_date = datetime.now() - timedelta(days=1)
    report_date = st.sidebar.date_input(LANG[ln]["date_label"], value=yesterday_date)

    with st.form("prod_form"):
        sup_name = st.text_input(LANG[ln]["supervisor"])
        c1, c2 = st.columns(2)
        with c1:
            prod_type = st.selectbox(LANG[ln]["product"], PRODUCTION_CONFIG[line_key]["الأصناف"])
            pre_count = st.number_input(LANG[ln]["preform"], min_value=0, step=1)
        with c2:
            raw_pack = st.number_input(LANG[ln]["raw_packaging"], min_value=0, step=1)
            out_units = st.number_input(LANG[ln]["output"], min_value=0, step=1)

        if st.form_submit_button(LANG[ln]["submit"], use_container_width=True):
            if not sup_name or out_units == 0:
                st.error(LANG[ln]["error"])
            else:
                b_per_u = PRODUCTION_CONFIG[line_key]["العبوات_في_الوحدة"][prod_type]
                line_speed = PRODUCTION_CONFIG[line_key]["السرعة"][prod_type]
                total_bottles = out_units * b_per_u
                waste_b = pre_count - total_bottles
                waste_p = raw_pack - out_units
                actual_prod_hours = total_bottles / line_speed
                calc_downtime = 15 - actual_prod_hours
                efficiency = (total_bottles / (line_speed * 15)) * 100

                res1, res2, res3 = st.columns(3)
                res1.metric(LANG[ln]["eff_label"], f"{round(efficiency, 1)}%")
                res2.metric(LANG[ln]["downtime_label"], f"{round(max(0, calc_downtime), 2)} {LANG[ln]['hours']}")
                res3.metric(LANG[ln]["waste_bottles"], f"{waste_b} {LANG[ln]['unit_bottles']}")

                try:
                    url = st.secrets["connections"]["gsheets_secured"]["spreadsheet"]
                    new_data = pd.DataFrame([{
                        "Type": "Production", "Line": line_choice, "Date": str(report_date), "Staff": sup_name,
                        "Product": prod_type, "Output_Units": out_units, "Waste_Bottles": waste_b,
                        "Waste_Packaging": waste_p, "Downtime_Hrs": round(max(0, calc_downtime), 2),
                        "Efficiency_%": round(efficiency, 1), "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }])
                    df = conn.read(spreadsheet=url, ttl=0)
                    conn.update(spreadsheet=url, data=pd.concat([df, new_data], ignore_index=True))
                    st.success(LANG[ln]["success"])
                    st.balloons()
                except Exception as e: st.error(f"Error: {e}")

    # --- عرض السجل (تحديث تلقائي) ---
    st.divider()
    st.subheader(LANG[ln]["history_title"])
    try:
        url = st.secrets["connections"]["gsheets_secured"]["spreadsheet"]
        history_df = conn.read(spreadsheet=url, ttl=5) # تحديث كل 5 ثواني
        if not history_df.empty:
            # تصفية لعرض بيانات الإنتاج فقط للخط المختار وترتيبها بالأحدث
            prod_history = history_df[history_df['Type'] == 'Production'].tail(10)[::-1]
            st.dataframe(prod_history, use_container_width=True)
        else:
            st.info(LANG[ln]["empty_history"])
    except:
        st.info(LANG[ln]["empty_history"])

# --- 6. قسم الصيانة ---
else:
    st.header(LANG[ln]["mode_maint"])
    unit_name = st.sidebar.selectbox(LANG[ln]["maint_machine"], list(MACHINE_MAP.keys()))
    file_path = MACHINE_MAP[unit_name]
    
    if os.path.exists(file_path):
        df_tasks = pd.read_excel(file_path, skiprows=2)
        df_tasks.columns = ['Category', 'No', 'Name', 'Photo', 'Tools', 'Procedure', 'Freq', 'Status', 'Note', 'Staff']
        daily = df_tasks[df_tasks['Freq'] == 'Daily']

        with st.form("maint_form"):
            m_staff = st.text_input(LANG[ln]["maint_staff"])
            maint_records = []
            for i, row in daily.iterrows():
                st.markdown(f"### {row['Name']}")
                img = str(row['Photo']).strip()
                if img and img.lower() != 'nan':
                    p = os.path.join(os.path.dirname(__file__), IMAGE_FOLDER, img)
                    if os.path.exists(p): st.image(p, use_container_width=True)
                
                st.info(f"🛠 {row['Procedure']}")
                c_chk, c_note = st.columns([1, 2])
                with c_chk: done = st.checkbox("OK", key=f"c_{i}_{line_choice}")
                with c_note: note = st.text_input("Note", key=f"n_{i}_{line_choice}")
                
                if done:
                    maint_records.append({
                        "Type": "Maintenance", "Line": line_choice, "Date": str(datetime.now().date()),
                        "Machine": unit_name, "Task": row['Name'], "Staff": m_staff, "Notes": note
                    })
            
            if st.form_submit_button(LANG[ln]["submit"], use_container_width=True):
                if maint_records and m_staff:
                    try:
                        url = st.secrets["connections"]["gsheets_secured"]["spreadsheet"]
                        df = conn.read(spreadsheet=url, ttl=0)
                        conn.update(spreadsheet=url, data=pd.concat([df, pd.DataFrame(maint_records)], ignore_index=True))
                        st.success(LANG[ln]["success"])
                    except Exception as e: st.error(f"Error: {e}")
                else: st.error(LANG[ln]["error"])