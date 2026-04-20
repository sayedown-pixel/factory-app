import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="BIRMA Factory - Google Sheets Sync", layout="centered")

# --- 2. إعدادات الربط مع Google Sheets ---
# استبدل الرابط أدناه برابط ملف جوجل شيت الخاص بك
SHEET_URL = "ضع_رابط_ملف_جوجل_شيت_هنا"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. إعدادات الملفات المحلية والماكينات ---
IMAGE_FOLDER = 'images'
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
st.sidebar.title("🏭 مصنع بيرما - المزامنة")
target_date = st.sidebar.date_input("تاريخ اليوم", datetime.now())
unit_name = st.sidebar.selectbox("اختر الماكينة", list(MACHINE_MAP.keys()))
unit_file = MACHINE_MAP[unit_name]

# --- 5. تحميل بيانات الماكينة المحلية ---
@st.cache_data
def load_machine_data(path):
    if os.path.exists(path):
        try:
            df = pd.read_excel(path, skiprows=2, engine='openpyxl')
            df.columns = ['Category', 'No', 'Name', 'Photo', 'Tools', 'Procedure', 'Freq', 'Status', 'Note', 'Staff']
            df['Category'] = df['Category'].ffill()
            return df
        except:
            return None
    return None

engine_data = load_machine_data(unit_file)

# --- 6. واجهة الإدخال ---
st.header(f"⚙️ صيانة ومزامنة: {unit_name}")

if engine_data is not None:
    with st.form("maintenance_form", clear_on_submit=True):
        daily_tasks = engine_data[engine_data['Freq'] == 'Daily']
        submission_queue = []

        for i, row in daily_tasks.iterrows():
            st.markdown(f"### {row['Name']}")
            
            # عرض الصورة التوضيحية
            image_name = str(row['Photo']).strip()
            if image_name and image_name != 'nan':
                image_path = os.path.join(os.getcwd(), IMAGE_FOLDER, image_name)
                if os.path.exists(image_path):
                    st.image(image_path, width=250)
            
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

        if st.form_submit_button("إرسال إلى Google Sheets"):
            if not signature:
                st.error("❌ التوقيع مطلوب!")
            elif submission_queue:
                for entry in submission_queue:
                    entry['Technician_Signature'] = signature
                
                try:
                    # 1. قراءة البيانات الحالية من جوجل شيت
                    existing_data = conn.read(spreadsheet=SHEET_URL, usecols=list(range(8)))
                    existing_data = existing_data.dropna(how="all")
                    
                    # 2. دمج البيانات الجديدة
                    new_data = pd.DataFrame(submission_queue)
                    updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                    
                    # 3. تحديث ملف جوجل شيت أونلاين
                    conn.update(spreadsheet=SHEET_URL, data=updated_df)
                    
                    st.success(f"✅ تم إرسال البيانات وحفظها في Google Sheets بنجاح!")
                except Exception as e:
                    st.error(f"حدث خطأ أثناء الربط مع Google Sheets: {e}")
            else:
                st.warning("لم يتم اختيار مهام.")

# --- 7. مراجعة السجل من جوجل شيت ---
if st.sidebar.checkbox("عرض سجل جوجل شيت"):
    try:
        live_data = conn.read(spreadsheet=SHEET_URL)
        st.subheader("📊 البيانات المسجلة أونلاين")
        st.dataframe(live_data.tail(20))
    except:
        st.sidebar.error("لا يمكن الاتصال بالملف حالياً.")