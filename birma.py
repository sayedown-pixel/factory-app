import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. إعدادات الصفحة ---
st.set_page_config(
    page_title=" صيانة بيرما - Birma Maintenance",
    page_icon="🏭",
    layout="centered"
)

# --- 2. إنشاء الاتصال بجوجل ---
conn = st.connection("gsheets_secured", type=GSheetsConnection)

# --- 3. الإعدادات العامة للمجلدات ---
IMAGE_FOLDER = 'images'
MACHINE_MAP = {
    "النفخ(blowing machine)": "blowing_machine.xlsx",
    "الليبل(labeling machine)": "labeling_machine.xlsx",
    "السيور(conveyor)": "Conveyor_machine.xlsx",
    "الكرتون(carton machine )": "packing_machine.xlsx",
    "البالتايزر(paletizer machine)": "paletizer_machine.xlsx",
    "الشرنك(shrink machine)": "shrink_machine.xlsx",
    "التعبئة(filling machine)": "Filling_machine.xlsx",
}

# --- 4. القائمة الجانبية (الاختيار الأساسي) ---
st.sidebar.markdown("### 🛠 إعدادات التشغيل")
# إضافة اختيار الخط كأول خطوة للمشغل
production_line = st.sidebar.selectbox("🚩 اختر خط الإنتاج(choose the line)", ["الخط الأول(line 1 smi)", "(line 2 welbing)الخط الثاني"])
target_date = st.sidebar.date_input("📅 تاريخ التقرير", datetime.now())
unit_name = st.sidebar.selectbox("🔍 choose machine اختر الماكينة", list(MACHINE_MAP.keys()))
unit_file = MACHINE_MAP[unit_name]

# --- 5. دالة تحميل البيانات ---
@st.cache_data
def load_machine_data(path):
    if os.path.exists(path):
        try:
            df = pd.read_excel(path, skiprows=2, engine='openpyxl')
            df.columns = ['Category', 'No', 'Name', 'Photo', 'Tools', 'Procedure', 'Freq', 'Status', 'Note', 'Staff']
            df['Category'] = df['Category'].ffill()
            return df
        except Exception as e:
            st.error(f" error خطأ في الملف: {e}")
            return None
    return None

engine_data = load_machine_data(unit_file)

# --- 6. الواجهة الرئيسية ---
# تمييز بصري لكل خط
line_color = "blue" if production_line == "الخط الأول(line 1 smi)" else "green"
st.markdown(f"<h1 style='text-align: center; color: {line_color};'>{production_line}</h1>", unsafe_allow_html=True)
st.subheader(f"📋log file سجل صيانة: {unit_name}")

if engine_data is not None:
    with st.form("unified_form", clear_on_submit=True):
        daily_tasks = engine_data[engine_data['Freq'] == 'Daily']
        submission_queue = []

        for i, row in daily_tasks.iterrows():
            with st.container():
                st.markdown(f"#### {row['Name']}")
                
                # عرض الصور
                image_name = str(row['Photo']).strip()
                if image_name and image_name.lower() != 'nan':
                    base_path = os.path.dirname(__file__)
                    full_image_path = os.path.join(base_path, IMAGE_FOLDER, image_name)
                    if os.path.exists(full_image_path):
                        st.image(full_image_path, use_container_width=True)
                    else:
                        st.caption(f"📸 صورة مفقودة: {image_name}")

                st.info(f"🛠 action الإجراء: {row['Procedure']}")
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    # إضافة اسم الخط للمفتاح لضمان عدم حدوث تضارب في الذاكرة
                    is_done = st.checkbox("تم الفحص (task completed)", key=f"chk_{i}_{production_line}")
                with col2:
                    comment = st.text_input("ملاحظات (notes)", key=f"txt_{i}_{production_line}")

                if is_done:
                    submission_queue.append({
                        'Line': production_line,  # تحديد الخط في الداتا
                        'Date': str(target_date),
                        'Time': datetime.now().strftime("%H:%M:%S"),
                        'Machine': unit_name,
                        'Task': row['Name'],
                        'Procedure': row['Procedure'],
                        'Status': 'Completed',
                        'Notes': comment
                    })
                st.markdown("---")

        signature = st.text_input("✍️ signature توقيع المشغل المسؤول:")

        if st.form_submit_button(f"إرسال تقرير (send report){production_line}", use_container_width=True):
            if not signature:
                st.error("❌ please write you name يرجى كتابة الاسم قبل الإرسال")
            elif submission_queue:
                try:
                    for entry in submission_queue:
                        entry['Technician_Signature'] = signature
                    
                    new_df = pd.DataFrame(submission_queue)
                    sheet_url = st.secrets["connections"]["gsheets_secured"]["spreadsheet"]
                    
                    # المزامنة
                    try:
                        existing_df = conn.read(spreadsheet=sheet_url, ttl=0)
                        final_df = pd.concat([existing_df, new_df], ignore_index=True)
                    except:
                        final_df = new_df
                    
                    conn.update(spreadsheet=sheet_url, data=final_df)
                    st.success(f"✅ تم حفظ بيانات {production_line} بنجاح!")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ فشل الإرسال: {e}")
            else:
                st.warning("⚠️ choose task لم يتم اختيار أي مهام.")

# عرض السجل المباشر في الأسفل
if st.sidebar.checkbox("👁 perview log file عرض السجل الأخير"):
    try:
        url = st.secrets["connections"]["gsheets_secured"]["spreadsheet"]
        data = conn.read(spreadsheet=url, ttl=0)
        st.write("آخر 10 عمليات تسجيل:")
        st.dataframe(data.tail(10))
    except:
        st.sidebar.error("لا يمكن الوصول لجوجل حالياً.")