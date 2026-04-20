import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="BIRMA - Secured Sync", layout="centered")

# --- 2. إنشاء الاتصال ---
# هنا سيبحث Streamlit تلقائياً في Secrets عن [connections.gsheets]
# وسيجد الرابط والمفتاح معاً ويربطهما ببعض.
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. إعدادات الماكينات المحلية ---
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
st.sidebar.title("🏭 مصنع بيرما")
target_date = st.sidebar.date_input("تاريخ اليوم", datetime.now())
unit_name = st.sidebar.selectbox("اختر الماكينة", list(MACHINE_MAP.keys()))
unit_file = MACHINE_MAP[unit_name]

# --- 5. تحميل بيانات الماكينة المحلية ---
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
if engine_data is not None:
    with st.form("main_form", clear_on_submit=True):
        daily_tasks = engine_data[engine_data['Freq'] == 'Daily']
        submission_queue = []

        for i, row in daily_tasks.iterrows():
            st.markdown(f"### {row['Name']}")
            
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

        if st.form_submit_button("إرسال التقرير"):
            if not signature:
                st.error("❌ يجب كتابة التوقيع!")
            elif submission_queue:
                try:
                    for entry in submission_queue:
                        entry['Technician_Signature'] = signature
                    
                    new_entries = pd.DataFrame(submission_queue)

                    # --- القراءة والكتابة بدون روابط يدوية ---
                    # المكتبة ستستخدم الرابط والمفتاح من Secrets تلقائياً
                    try:
                        # الأقواس فارغة لضمان استخدام الصلاحيات المؤمنة
                        existing_data = conn.read() 
                        existing_data = existing_data.dropna(how="all")
                        updated_df = pd.concat([existing_data, new_entries], ignore_index=True)
                    except:
                        updated_df = new_entries
                    
                    # التحديث بدون رابط أيضاً
                    conn.update(data=updated_df)
                    st.success("✅ تم الإرسال والمزامنة بنجاح!")
                except Exception as e:
                    st.error(f"خطأ في المزامنة: {e}")
            else:
                st.warning("برجاء اختيار مهام.")

# --- مراجعة السجل من جوجل ---
if st.sidebar.checkbox("مراجعة سجل جوجل شيت"):
    try:
        # قراءة آمنة بدون رابط يدوي
        live_data = conn.read()
        st.dataframe(live_data.tail(15))
    except Exception as e:
        st.sidebar.error(f"تعذر جلب البيانات: {e}")
if st.button("اختبار المزامنة الآن"):
    try:
        # جلب البيانات الحالية (بدون وضع رابط يدوي هنا)
        df = conn.read()
        st.write("تم الاتصال بنجاح! هذه هي آخر البيانات:")
        st.dataframe(df.tail(5))
    except Exception as e:
        st.error(f"فشل الاتصال: {e}")        
