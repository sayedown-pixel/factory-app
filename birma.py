import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="BIRMA Factory - Maintenance Pro", layout="centered")

# --- 2. إعدادات الملفات والمجلدات ---
LOG_FILE = 'maintenance_logs.csv'
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

# التأكد من وجود ملف السجل، وإذا لم يوجد يتم إنشاؤه بأعمدة صحيحة
if not os.path.exists(LOG_FILE):
    pd.DataFrame(columns=['Date', 'Time', 'Machine', 'Task', 'Procedure', 'Status', 'Notes', 'Technician_Signature']).to_csv(LOG_FILE, index=False)

# --- 3. القائمة الجانبية ---
st.sidebar.title("🏭 مصنع بيرما")
target_date = st.sidebar.date_input("تاريخ التقرير", datetime.now())
unit_name = st.sidebar.selectbox("اختر الماكينة", list(MACHINE_MAP.keys()))
unit_file = MACHINE_MAP[unit_name]

# --- 4. تحميل بيانات الماكينة ---
@st.cache_data
def load_machine_data(path):
    if os.path.exists(path):
        try:
            # قراءة الإكسيل مع تخطي أول سطرين كما في ملفاتك
            df = pd.read_excel(path, skiprows=2, engine='openpyxl')
            df.columns = ['Category', 'No', 'Name', 'Photo', 'Tools', 'Procedure', 'Freq', 'Status', 'Note', 'Staff']
            df['Category'] = df['Category'].ffill()
            return df
        except Exception as e:
            st.error(f"خطأ في قراءة ملف الماكينة: {e}")
            return None
    return None

engine_data = load_machine_data(unit_file)

# --- 5. واجهة الإدخال ---
st.header(f"⚙️ نموذج صيانة: {unit_name}")

if engine_data is not None:
    with st.form("maintenance_form", clear_on_submit=True):
        # فلترة المهام اليومية فقط
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
            
            st.info(f"📋 **الإجراء المطلوب:** {row['Procedure']}")
            
            col1, col2 = st.columns([1, 2])
            with col1:
                is_done = st.checkbox("تم الفحص بنجاح", key=f"chk_{i}")
            with col2:
                comment = st.text_input("ملاحظات إضافية", key=f"txt_{i}", placeholder="اكتب أي ملاحظة هنا...")

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

        # قسم التوقيع
        st.subheader("✍️ اعتماد التقرير")
        signature = st.text_input("اسم الفني القائم بالعمل (التوقيع):")

        if st.form_submit_button("إرسال التقرير وحفظ البيانات"):
            if not signature:
                st.error("❌ لا يمكن الإرسال بدون كتابة اسمك في خانة التوقيع!")
            elif submission_queue:
                # إضافة اسم الموقع لكل المهام المختارة
                for entry in submission_queue:
                    entry['Technician_Signature'] = signature
                
                # --- الجزء الأهم: الحفاظ على البيانات القديمة ---
                new_entries_df = pd.DataFrame(submission_queue)
                
                # قراءة الملف الحالي من السيرفر
                if os.path.exists(LOG_FILE):
                    current_log_df = pd.read_csv(LOG_FILE)
                    # دمج البيانات الجديدة مع القديمة
                    final_df = pd.concat([current_log_df, new_entries_df], ignore_index=True)
                else:
                    final_df = new_entries_df
                
                # حفظ الملف المدمج
                final_df.to_csv(LOG_FILE, index=False)
                st.success(f"✅ تم حفظ تقرير {unit_name} بنجاح يا {signature}")
            else:
                st.warning("برجاء تعليم المهام التي قمت بتنفيذها أولاً.")

# --- 6. عرض السجل وزر التحميل للمدير ---
st.sidebar.divider()
if st.sidebar.checkbox("📂 إدارة السجل (للمدير)"):
    if os.path.exists(LOG_FILE):
        logs = pd.read_csv(LOG_FILE)
        st.subheader("📋 مراجعة آخر العمليات المسجلة")
        st.dataframe(logs.tail(10)) # عرض آخر 10 عمليات
        
        # زر التحميل لضمان عدم ضياع البيانات
        with open(LOG_FILE, "rb") as f:
            st.sidebar.download_button(
                label="📥 تحميل سجل الصيانة كاملاً (CSV)",
                data=f,
                file_name=f"Birma_Maintenance_Log_{datetime.now().strftime('%Y-%m-%d')}.csv",
                mime="text/csv"
            )
    else:
        st.sidebar.info("لا توجد بيانات مسجلة بعد.")