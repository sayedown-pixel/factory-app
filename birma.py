import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="BIRMA Maintenance System", layout="centered")

# --- 2. إنشاء الاتصال (تم تغيير الاسم لإجبار النظام على تحديث الصلاحيات) ---
# تأكد من تغيير الاسم في الـ Secrets إلى [connections.gsheets_secured]
conn = st.connection("gsheets_secured", type=GSheetsConnection)

# --- 3. خريطة الملفات المحلية ---
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
target_date = st.sidebar.date_input("تاريخ التقرير", datetime.now())
unit_name = st.sidebar.selectbox("اختر الماكينة", list(MACHINE_MAP.keys()))
unit_file = MACHINE_MAP[unit_name]

# --- 5. تحميل بيانات الماكينة المحلية ---
@st.cache_data
def load_local_machine_data(path):
    if os.path.exists(path):
        try:
            df = pd.read_excel(path, skiprows=2, engine='openpyxl')
            df.columns = ['Category', 'No', 'Name', 'Photo', 'Tools', 'Procedure', 'Freq', 'Status', 'Note', 'Staff']
            df['Category'] = df['Category'].ffill()
            return df
        except Exception: return None
    return None

engine_data = load_local_machine_data(unit_file)

# --- 6. واجهة الإدخال الرئيسية ---
st.header(f"⚙️ صيانة ومزامنة: {unit_name}")

if engine_data is not None:
    with st.form("main_form", clear_on_submit=True):
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
                is_done = st.checkbox("تم الفحص بنجاح", key=f"chk_{i}")
            with c2:
                comment = st.text_input("ملاحظات إضافية", key=f"txt_{i}")

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

        signature = st.text_input("توقيع الفني المسؤول:")

        # زر الإرسال والمزامنة
        if st.form_submit_button("إرسال البيانات إلى Google Sheets"):
            if not signature:
                st.error("❌ التوقيع مطلوب لإتمام العملية!")
            elif submission_queue:
                try:
                    # إضافة التوقيع لكل سجل
                    for entry in submission_queue:
                        entry['Technician_Signature'] = signature
                    
                    new_entries = pd.DataFrame(submission_queue)

                    # --- المزامنة الآمنة ---
                    # استدعاء الرابط من الأسرار لضمان تفعيل حساب الخدمة
                    sheet_url = st.secrets["connections"]["gsheets_secured"]["spreadsheet"]
                    
                    # 1. قراءة البيانات (تجاهل التخزين المؤقت ttl=0)
                    try:
                        existing_data = conn.read(spreadsheet=sheet_url, ttl=0)
                        existing_data = existing_data.dropna(how="all")
                        updated_df = pd.concat([existing_data, new_entries], ignore_index=True)
                    except:
                        updated_df = new_entries
                    
                    # 2. الكتابة في جوجل شيت
                    conn.update(spreadsheet=sheet_url, data=updated_df)
                    
                    st.success("✅ تم تحديث سجل جوجل شيت بنجاح!")
                    st.balloons()
                except Exception as e:
                    st.error(f"فشل المزامنة: {e}")
            else:
                st.warning("يرجى فحص المهام أولاً.")

# --- 7. قسم المراجعة الجانبي ---
if st.sidebar.checkbox("👁️ عرض آخر 10 سجلات من جوجل"):
    try:
        url = st.secrets["connections"]["gsheets_secured"]["spreadsheet"]
        st.dataframe(conn.read(spreadsheet=url, ttl=0).tail(10))
    except:
        st.sidebar.error("لا يمكن الوصول للبيانات أونلاين حالياً.")