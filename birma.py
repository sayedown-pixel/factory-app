import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="BIRMA Maintenance System", layout="centered")

# --- 2. إنشاء الاتصال (استخدام اسم فريد لتجنب التخزين المؤقت القديم) ---
conn = st.connection("gsheets_secured", type=GSheetsConnection)

# --- 3. خريطة الملفات المحلية (Excel) ---
MACHINE_MAP = {
    "النفخ": "blowing_machine.xlsx",
    "الليبل": "labeling_machine.xlsx",
    "السيور": "Conveyor_machine.xlsx",
    "الكرتون": "packing_machine.xlsx",
    "البالتايزر": "paletizer_machine.xlsx",
    "الشرنك": "shrink_machine.xlsx",
    "التعبئة": "Filling_machine.xlsx",
}

# --- 4. القائمة الجانبية ---
st.sidebar.title("🏭 مصنع بيرما")
target_date = st.sidebar.date_input("تاريخ التقرير", datetime.now())
unit_name = st.sidebar.selectbox("اختر الماكينة", list(MACHINE_MAP.keys()))
unit_file = MACHINE_MAP[unit_name]

# --- 5. تحميل بيانات الماكينة من الإكسيل المحلي ---
@st.cache_data
def load_local_data(path):
    if os.path.exists(path):
        try:
            df = pd.read_excel(path, skiprows=2, engine='openpyxl')
            df.columns = ['Category', 'No', 'Name', 'Photo', 'Tools', 'Procedure', 'Freq', 'Status', 'Note', 'Staff']
            df['Category'] = df['Category'].ffill()
            return df
        except: return None
    return None

engine_data = load_local_data(unit_file)

# --- 6. واجهة الإدخال ---
st.header(f"🔧 سجل صيانة: {unit_name}")

if engine_data is not None:
    with st.form("main_form", clear_on_submit=True):
        daily_tasks = engine_data[engine_data['Freq'] == 'Daily']
        submission_queue = []

        for i, row in daily_tasks.iterrows():
            st.markdown(f"### {row['Name']}")
            st.info(f"📋 **الإجراء:** {row['Procedure']}")
            
            c1, c2 = st.columns([1, 2])
            with c1:
                is_done = st.checkbox("تم الفحص", key=f"chk_{i}")
            with c2:
                comment = st.text_input("ملاحظات", key=f"txt_{i}")

            if is_done:
                submission_queue.append({
                    'Date': str(target_date),
                    'Time': datetime.now().strftime("%H:%M:%S"),
                    'Machine': unit_name,
                    'Task': row['Name'],
                    'Procedure': row['Procedure'],
                    'Status': 'Completed',
                    'Notes': comment
                })
            st.divider()

        signature = st.text_input("توقيع الفني:")

        if st.form_submit_button("إرسال التقرير"):
            if not signature:
                st.error("❌ التوقيع مطلوب!")
            elif submission_queue:
                try:
                    # جلب الرابط من Secrets (هنا نستخدم الاسم الجديد gsheets_secured)
                    url = st.secrets["connections"]["gsheets_secured"]["spreadsheet"]
                    
                    for entry in submission_queue:
                        entry['Technician_Signature'] = signature
                    new_df = pd.DataFrame(submission_queue)

                    # القراءة والكتابة باستخدام الصلاحيات المؤمنة
                    try:
                        existing_df = conn.read(spreadsheet=url, ttl=0)
                        final_df = pd.concat([existing_df, new_df], ignore_index=True)
                    except:
                        final_df = new_df
                    
                    conn.update(spreadsheet=url, data=final_df)
                    st.success("✅ تم التحديث بنجاح!")
                eimport traceback

                   except Exception as e:
                  st.error("حدث خطأ أثناء المزامنة:")
                  st.code(str(e))
                  st.code(traceback.format_exc())
            else:
                st.warning("يرجى اختيار مهام.")
