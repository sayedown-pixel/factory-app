import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. Master Configuration ---
st.set_page_config(page_title="BIRMA Factory - Maintenance Display", layout="centered")

# --- 2. Database & Paths ---
LOG_FILE = 'maintenance_logs.csv'
IMAGE_FOLDER = 'images'  # المجلد الذي يحتوي على صور الماكينات والقطع
MACHINE_MAP = {
    "النفخ": "blowing_machine.xlsx",
    "الليبل": "labeling_machine.xlsx",
    "السيور": "Conveyor_machine.xlsx",
    "الكرتون": "packing_machine.xlsx",
    "البالتايزر": "paletizer_machine.xlsx",
    "الشرنك": "shrink_machine.xlsx",
    "التعبئة": "Filling_machine.xlsx",
}

if not os.path.exists(LOG_FILE):
    pd.DataFrame(columns=['Date', 'Time', 'Machine', 'Task', 'Procedure', 'Status', 'Notes', 'Technician_Signature']).to_csv(LOG_FILE, index=False)

# --- 3. Sidebar ---
st.sidebar.title("🏭 BIRMA Control")
target_date = st.sidebar.date_input("تاريخ اليوم", datetime.now())
unit_name = st.sidebar.selectbox("اختر الماكينة", list(MACHINE_MAP.keys()))
unit_file = MACHINE_MAP[unit_name]

# --- 4. Data Loading ---
@st.cache_data
def load_data(path):
    if os.path.exists(path):
        try:
            df = pd.read_excel(path, skiprows=2, engine='openpyxl')
            df.columns = ['Category', 'No', 'Name', 'Photo', 'Tools', 'Procedure', 'Freq', 'Status', 'Note', 'Staff']
            df['Category'] = df['Category'].ffill()
            return df
        except:
            return None
    return None

engine_data = load_data(unit_file)

# --- 5. Interface ---
st.header(f"⚙️ وحدة: {unit_name}")

if engine_data is not None:
    with st.form("main_log_form"):
        daily_tasks = engine_data[engine_data['Freq'] == 'Daily']
        submission_queue = []

        for i, row in daily_tasks.iterrows():
            st.markdown(f"### {row['Name']}")
            
            # --- عرض الصورة التوضيحية من مجلد images ---
            image_name = str(row['Photo']).strip()
            if image_name and image_name != 'nan':
                image_path = os.path.join(os.getcwd(), 'images', image_name)
                if os.path.exists(image_path):
                    st.image(image_path, caption=f"صورة توضيحية: {row['Name']}", width=300)
                else:
                    st.error(f"⚠️ السيرفر لم يجد الصورة: images/{image_name}")

            st.warning(f"📋 **طريقة التنفيذ:** {row['Procedure']}")
            
            c1, c2 = st.columns([1, 2])
            with c1:
                is_done = st.checkbox("تم الفحص", key=f"c_{i}")
            with c2:
                comment = st.text_input("ملاحظات الفني", key=f"n_{i}")

            if is_done:
                submission_queue.append({
                    'Date': target_date,
                    'Time': datetime.now().strftime("%H:%M:%S"),
                    'Machine': unit_name,
                    'Task': row['Name'],
                    'Procedure': row['Procedure'],
                    'Status': 'Completed',
                    'Notes': comment
                })
            st.divider()

        st.subheader("✍️ توقيع القائم بالعمل")
        signature = st.text_input("ادخل اسمك هنا لاعتماد التقرير:")

        if st.form_submit_button("إرسال التقرير النهائي"):
            if not signature:
                st.error("❌ لا يمكن الإرسال بدون توقيع!")
            elif submission_queue:
                for entry in submission_queue:
                    entry['Technician_Signature'] = signature
                
                history = pd.read_csv(LOG_FILE)
                pd.concat([history, pd.DataFrame(submission_queue)], ignore_index=True).to_csv(LOG_FILE, index=False)
                st.success(f"✅ تم الحفظ بنجاح. شكراً لك يا {signature}")
            else:
                st.warning("يرجى تعليم المهام التي قمت بإنجازها.")
else:
    st.error(f"ملف {unit_file} غير موجود. يرجى رفعه مع مجلد الصور.")

# --- 6. Review ---
if st.checkbox("عرض السجل الأخير"):
    if os.path.exists(LOG_FILE):
        st.table(pd.read_csv(LOG_FILE).tail(5))