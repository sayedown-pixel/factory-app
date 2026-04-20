import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import streamlit as st
import pandas as pd
from datetime import datetime

# استيراد المكتبة مع معالجة الخطأ إذا لم تكن مثبتة
try:
    from streamlit_gsheets import GSheetsConnection
except ImportError:
    st.error("المكتبة st-gsheets-connection غير مثبتة. نفذ الأمر: pip install st-gsheets-connection")

# --- إعدادات الربط ---
# تأكد أنك تستخدم هذا الاسم 'gsheets' في الكود وفي ملف التكوين
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.warning("لم يتم إعداد اتصال Google Sheets بعد. سيعمل التطبيق للعرض فقط.")

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="BIRMA - Google Sheets Arabic Support", layout="centered")

# --- 2. إعدادات الربط ---
# تأكد من وضع الرابط الصحيح هنا
SHEET_URL = "https://docs.google.com/spreadsheets/d/1GyO_emKsSOS8birzvXAh8qN70YP1Sn794oxaHwaTH-I/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. إعدادات الماكينات ---
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

# --- 5. واجهة الإدخال ---
st.header(f"⚙️ صيانة: {unit_name}")

@st.cache_data
def load_data(path):
    if os.path.exists(path):
        try:
            df = pd.read_excel(path, skiprows=2, engine='openpyxl')
            df.columns = ['Category', 'No', 'Name', 'Photo', 'Tools', 'Procedure', 'Freq', 'Status', 'Note', 'Staff']
            df['Category'] = df['Category'].ffill()
            return df
        except: return None
    return None

engine_data = load_data(unit_file)

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
                try:
                    # إضافة التوقيع
                    for entry in submission_queue:
                        entry['Technician_Signature'] = signature
                    
                    # تحويل البيانات لـ DataFrame
                    new_data = pd.DataFrame(submission_queue)
                    
                    # --- حل مشكلة العربي (تأكيد الترميز) ---
                    # قراءة البيانات الحالية
                    try:
                        existing_data = conn.read(spreadsheet=SHEET_URL)
                        existing_data = existing_data.dropna(how="all")
                        updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                    except:
                        # في حال كان الملف فارغاً تماماً
                        updated_df = new_data
                    
                    # تحديث الشيت
                    conn.update(spreadsheet=SHEET_URL, data=updated_df)
                    st.success("✅ تم حفظ البيانات بنجاح في Google Sheets!")
                    
                except Exception as e:
                    # تحويل الخطأ لنص يدعم اليونيكود لتجنب كراش التطبيق
                    error_msg = str(e).encode('utf-8').decode('utf-8')
                    st.error(f"حدث خطأ في المزامنة: {error_msg}")
            else:
                st.warning("لم يتم اختيار مهام.")

# --- عرض السجل المباشر من جوجل ---
if st.sidebar.checkbox("مراجعة سجل جوجل شيت"):
    try:
        live_data = conn.read(spreadsheet=SHEET_URL)
        st.dataframe(live_data.tail(15))
    except:
        st.sidebar.error("فشل في جلب البيانات.")