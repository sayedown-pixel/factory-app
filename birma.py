import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="BIRMA Maintenance System", layout="wide")

# --- 2. الاتصال (تأكد أن الاسم gsheets_secured يطابق ما في الـ Secrets) ---
conn = st.connection("gsheets_secured", type=GSheetsConnection)

# --- 3. خريطة الماكينات ---
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

# --- 5. تحميل بيانات المهام محلياً ---
@st.cache_data
def load_local_machine_data(path):
    if os.path.exists(path):
        try:
            df = pd.read_excel(path, skiprows=2)
            df.columns = ['Category', 'No', 'Name', 'Photo', 'Tools', 'Procedure', 'Freq', 'Status', 'Note', 'Staff']
            df['Category'] = df['Category'].ffill()
            return df
        except: return None
    return None

engine_data = load_local_machine_data(unit_file)

# --- 6. واجهة العمل ---
st.header(f"⚙️ صيانة ومزامنة: {unit_name}")

if engine_data is not None:
    with st.form("maintenance_form", clear_on_submit=True):
        # تصفية المهام اليومية فقط
        daily_tasks = engine_data[engine_data['Freq'] == 'Daily']
        submission_queue = []

        for i, row in daily_tasks.iterrows():
            st.markdown(f"### {row['Name']}")
            st.info(f"📋 **الإجراء:** {row['Procedure']}")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                is_done = st.checkbox("تم الفحص", key=f"chk_{i}")
            with col2:
                comment = st.text_input("ملاحظات", key=f"txt_{i}")

            if is_done:
                submission_queue.append({
                    'Date': str(target_date),
                    'Time': datetime.now().strftime("%H:%M:%S"),
                    'Machine': unit_name,
                    'Task': row['Name'],
                    'Status': 'Completed',
                    'Notes': comment
                })
            st.divider()

        signature = st.text_input("اسم الفني (التوقيع):")

        if st.form_submit_button("إرسال التقرير إلى Google Sheets"):
            if not signature:
                st.error("❌ يجب كتابة اسم الفني!")
            elif submission_queue:
                try:
                    # جلب الرابط من Secrets لضمان ربطه بحساب الخدمة
                    sheet_url = st.secrets["connections"]["gsheets_secured"]["spreadsheet"]
                    
                    # تجهيز البيانات الجديدة
                    for entry in submission_queue:
                        entry['Technician_Signature'] = signature
                    new_data = pd.DataFrame(submission_queue)

                    # 1. القراءة (تأكد أن الـ API مفعلة لتنجح هذه الخطوة)
                    try:
                        existing_data = conn.read(spreadsheet=sheet_url, ttl=0)
                        updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                    except:
                        updated_df = new_data
                    
                    # 2. الكتابة
                    conn.update(spreadsheet=sheet_url, data=updated_df)
                    st.success("✅ تم التحديث بنجاح! الرابط يعمل الآن.")
                    st.balloons()
                except Exception as e:
                    st.error(f"حدث خطأ أثناء المزامنة: {e}")
            else:
                st.warning("لم يتم اختيار أي مهام.")

# --- 7. عرض السجل ---
if st.sidebar.checkbox("📊 عرض السجل المباشر"):
    try:
        sheet_url = st.secrets["connections"]["gsheets_secured"]["spreadsheet"]
        st.dataframe(conn.read(spreadsheet=sheet_url, ttl=0).tail(15))
    except:
        st.sidebar.error("فشل جلب البيانات أونلاين.")