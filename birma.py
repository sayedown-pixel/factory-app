import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="BIRMA - Secured Maintenance System", layout="centered")

# --- 2. إنشاء الاتصال بـ Google Sheets ---
# سيقوم هذا السطر بالبحث عن [connections.gsheets] في Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. إعدادات الماكينات والمجلدات ---
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

# --- 5. دالة تحميل بيانات الماكينة من ملف Excel المحلي ---
@st.cache_data
def load_local_machine_data(path):
    if os.path.exists(path):
        try:
            # قراءة الإكسيل مع تخطي أول سطرين (حسب تنسيق ملفاتك)
            df = pd.read_excel(path, skiprows=2, engine='openpyxl')
            df.columns = ['Category', 'No', 'Name', 'Photo', 'Tools', 'Procedure', 'Freq', 'Status', 'Note', 'Staff']
            df['Category'] = df['Category'].ffill()
            return df
        except Exception as e:
            st.error(f"خطأ في قراءة ملف الماكينة المحلي: {e}")
            return None
    return None

engine_data = load_local_machine_data(unit_file)

# --- 6. واجهة إدخال البيانات ---
st.header(f"⚙️ صيانة ومزامنة: {unit_name}")

if engine_data is not None:
    with st.form("maintenance_form", clear_on_submit=True):
        # تصفية المهام اليومية
        daily_tasks = engine_data[engine_data['Freq'] == 'Daily']
        submission_queue = []

        for i, row in daily_tasks.iterrows():
            st.markdown(f"### {row['Name']}")
            
            # عرض الصورة التوضيحية من مجلد images
            image_name = str(row['Photo']).strip()
            if image_name and image_name != 'nan':
                image_path = os.path.join(os.getcwd(), IMAGE_FOLDER, image_name)
                if os.path.exists(image_path):
                    st.image(image_path, width=250)
            
            st.info(f"📋 **الإجراء المطلوب:** {row['Procedure']}")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                is_done = st.checkbox("تم الفحص بنجاح", key=f"chk_{i}")
            with col2:
                comment = st.text_input("ملاحظات إضافية", key=f"txt_{i}", placeholder="اكتب ملاحظاتك هنا...")

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

        # قسم الاعتماد
        st.subheader("✍️ اعتماد التقرير")
        signature = st.text_input("اسم الفني (التوقيع):")

        # زر الإرسال والمزامنة مع Google Sheets
        if st.form_submit_button("إرسال التقرير إلى Google Sheets"):
            if not signature:
                st.error("❌ خطأ: يجب كتابة اسم الفني قبل الإرسال!")
            elif submission_queue:
                try:
                    # إضافة التوقيع لكل سجل
                    for entry in submission_queue:
                        entry['Technician_Signature'] = signature
                    
                    new_data = pd.DataFrame(submission_queue)

                    # --- الربط الآمن باستخدام Secrets ---
                    # استدعاء الرابط مباشرة من st.secrets لضمان استخدام حساب الخدمة
                    sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
                    
                    # 1. قراءة البيانات الحالية من جوجل شيت
                    try:
                        existing_data = conn.read(spreadsheet=sheet_url, ttl=0)
                        existing_data = existing_data.dropna(how="all")
                        updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                    except:
                        # في حال كان الملف فارغاً أو أول مرة يتم استخدامه
                        updated_df = new_data
                    
                    # 2. تحديث ملف جوجل شيت (الكتابة)
                    conn.update(spreadsheet=sheet_url, data=updated_df)
                    
                    st.success(f"✅ تم حفظ تقرير {unit_name} بنجاح في Google Sheets!")
                    st.balloons()
                except Exception as e:
                    st.error(f"حدث خطأ أثناء المزامنة: {e}")
            else:
                st.warning("برجاء اختيار مهمة واحدة على الأقل تم تنفيذها.")

# --- 7. قسم إدارة البيانات للمدير في القائمة الجانبية ---
st.sidebar.divider()
if st.sidebar.checkbox("📊 عرض السجل المباشر (Google)"):
    try:
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        live_data = conn.read(spreadsheet=sheet_url, ttl=0)
        st.subheader("📋 آخر البيانات المسجلة أونلاين")
        st.dataframe(live_data.tail(20))
    except Exception as e:
        st.sidebar.error(f"تعذر جلب البيانات من Google: {e}")