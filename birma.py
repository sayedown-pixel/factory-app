import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. إعدادات الصفحة (تحسين العرض للموبايل) ---
st.set_page_config(
    page_title="نظام صيانة بيرما",
    page_icon="🏭",
    layout="centered",  # أفضل للموبايل من wide
    initial_sidebar_state="collapsed"
)

# --- 2. إنشاء الاتصال بمكتبة جوجل ---
conn = st.connection("gsheets_secured", type=GSheetsConnection)

# --- 3. تعريف المجلدات والملفات ---
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
st.sidebar.header("الإعدادات")
target_date = st.sidebar.date_input("تاريخ التقرير", datetime.now())
unit_name = st.sidebar.selectbox("اختر الماكينة", list(MACHINE_MAP.keys()))
unit_file = MACHINE_MAP[unit_name]

# --- 5. دالة تحميل بيانات الماكينة ---
@st.cache_data
def load_machine_data(path):
    if os.path.exists(path):
        try:
            # قراءة الإكسيل مع تخطي السطور التعريفية
            df = pd.read_excel(path, skiprows=2, engine='openpyxl')
            df.columns = ['Category', 'No', 'Name', 'Photo', 'Tools', 'Procedure', 'Freq', 'Status', 'Note', 'Staff']
            df['Category'] = df['Category'].ffill()
            return df
        except Exception as e:
            st.error(f"خطأ في قراءة ملف {path}: {e}")
            return None
    return None

engine_data = load_machine_data(unit_file)

# --- 6. واجهة المستخدم الرئيسية ---
st.title("📋 سجل الصيانة اليومي")
st.subheader(f"ماكينة: {unit_name}")

if engine_data is not None:
    with st.form("maintenance_form", clear_on_submit=True):
        # نركز فقط على المهام اليومية
        daily_tasks = engine_data[engine_data['Freq'] == 'Daily']
        submission_queue = []

        for i, row in daily_tasks.iterrows():
            with st.container():
                st.markdown(f"#### {row['Name']}")
                
                # --- نظام عرض الصور المطور ---
                image_name = str(row['Photo']).strip()
                if image_name and image_name.lower() != 'nan':
                    # تحديد المسار المطلق للمجلد لضمان الوصول إليه في السيرفر
                    base_path = os.path.dirname(__file__)
                    full_image_path = os.path.join(base_path, IMAGE_FOLDER, image_name)
                    
                    if os.path.exists(full_image_path):
                        st.image(full_image_path, use_container_width=True, caption=f"صورة توضيحية لـ {row['Name']}")
                    else:
                        st.caption(f"⚠️ صورة مفقودة: {image_name}")

                st.info(f"🛠 **الإجراء:** {row['Procedure']}")
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    is_done = st.checkbox("تم الفحص", key=f"chk_{i}")
                with col2:
                    comment = st.text_input("ملاحظات", key=f"txt_{i}", placeholder="اختياري...")

                if is_done:
                    submission_queue.append({
                        'Date': str(target_date),
                        'Time': datetime.now().strftime("%H:%M:%S"),
                        'Machine': unit_name,
                        'Task': row['Name'],
                        'Status': 'Completed',
                        'Notes': comment
                    })
                st.markdown("---")

        signature = st.text_input("✍️ اسم الفني المسئول:")

        # زر الإرسال
        submit_button = st.form_submit_button("إرسال البيانات ومزامنة Google Sheets", use_container_width=True)

        if submit_button:
            if not signature:
                st.error("❌ لا يمكن الإرسال بدون توقيع الفني!")
            elif not submission_queue:
                st.warning("⚠️ يرجى اختيار مهمة واحدة على الأقل تم تنفيذها.")
            else:
                try:
                    # إضافة التوقيع
                    for entry in submission_queue:
                        entry['Technician_Signature'] = signature
                    
                    new_df = pd.DataFrame(submission_queue)
                    sheet_url = st.secrets["connections"]["gsheets_secured"]["spreadsheet"]

                    # القراءة والكتابة
                    try:
                        existing_df = conn.read(spreadsheet=sheet_url, ttl=0)
                        final_df = pd.concat([existing_df, new_df], ignore_index=True)
                    except:
                        final_df = new_df
                    
                    conn.update(spreadsheet=sheet_url, data=final_df)
                    st.success("✅ تم إرسال التقرير ومزامنته بنجاح!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ خطأ في المزامنة: {e}")

# --- 7. عرض السجل في القائمة الجانبية (اختياري) ---
if st.sidebar.checkbox("👁 عرض آخر السجلات أونلاين"):
    try:
        url = st.secrets["connections"]["gsheets_secured"]["spreadsheet"]
        st.write(conn.read(spreadsheet=url, ttl=0).tail(10))
    except:
        st.sidebar.error("لا يمكن الاتصال بـ Google حالياً.")