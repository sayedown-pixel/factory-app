import streamlit as st
import pandas as pd
import os
import traceback
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# -------------------------------------------------
# إعداد الصفحة
# -------------------------------------------------
st.set_page_config(
    page_title="BIRMA Maintenance System",
    layout="centered"
)

# -------------------------------------------------
# الاتصال بـ Google Sheets
# -------------------------------------------------
conn = st.connection(
    "gsheets_secured",
    type=GSheetsConnection
)

# -------------------------------------------------
# خريطة ملفات الماكينات
# -------------------------------------------------
MACHINE_MAP = {
    "النفخ": "blowing_machine.xlsx",
    "الليبل": "labeling_machine.xlsx",
    "السيور": "Conveyor_machine.xlsx",
    "الكرتون": "packing_machine.xlsx",
    "البالتايزر": "paletizer_machine.xlsx",
    "الشرنك": "shrink_machine.xlsx",
    "التعبئة": "Filling_machine.xlsx",
}

# -------------------------------------------------
# القائمة الجانبية
# -------------------------------------------------
st.sidebar.title("🏭 مصنع بيرما")

target_date = st.sidebar.date_input(
    "تاريخ التقرير",
    datetime.now()
)

unit_name = st.sidebar.selectbox(
    "اختر الماكينة",
    list(MACHINE_MAP.keys())
)

unit_file = MACHINE_MAP[unit_name]

# -------------------------------------------------
# تحميل بيانات الإكسيل المحلي
# -------------------------------------------------
@st.cache_data
def load_local_data(path):
    if os.path.exists(path):
        try:
            df = pd.read_excel(
                path,
                skiprows=2,
                engine="openpyxl"
            )

            df.columns = [
                "Category",
                "No",
                "Name",
                "Photo",
                "Tools",
                "Procedure",
                "Freq",
                "Status",
                "Note",
                "Staff"
            ]

            df["Category"] = df["Category"].ffill()

            return df

        except:
            return None

    return None


engine_data = load_local_data(unit_file)

# -------------------------------------------------
# الواجهة الرئيسية
# -------------------------------------------------
st.header(f"🔧 سجل صيانة: {unit_name}")

if engine_data is None:
    st.error("❌ لم يتم العثور على ملف بيانات الماكينة")
    st.stop()

# -------------------------------------------------
# الفورم
# -------------------------------------------------
with st.form("main_form", clear_on_submit=True):

    daily_tasks = engine_data[
        engine_data["Freq"] == "Daily"
    ]

    submission_queue = []

    for i, row in daily_tasks.iterrows():

        st.markdown(f"### {row['Name']}")
        st.info(f"📋 الإجراء: {row['Procedure']}")

        c1, c2 = st.columns([1, 2])

        with c1:
            is_done = st.checkbox(
                "تم الفحص",
                key=f"chk_{i}"
            )

        with c2:
            comment = st.text_input(
                "ملاحظات",
                key=f"txt_{i}"
            )

        if is_done:
            submission_queue.append({
                "Date": str(target_date),
                "Time": datetime.now().strftime("%H:%M:%S"),
                "Machine": unit_name,
                "Task": row["Name"],
                "Procedure": row["Procedure"],
                "Status": "Completed",
                "Notes": comment
            })

        st.divider()

    signature = st.text_input("توقيع الفني")

    submitted = st.form_submit_button("إرسال التقرير")

# -------------------------------------------------
# عند الضغط على الإرسال
# -------------------------------------------------
if submitted:

    if not signature:
        st.error("❌ التوقيع مطلوب")
        st.stop()

    if not submission_queue:
        st.warning("⚠️ اختر مهمة واحدة على الأقل")
        st.stop()

    try:
        # إضافة التوقيع
        for item in submission_queue:
            item["Technician_Signature"] = signature

        new_df = pd.DataFrame(submission_queue)

        # قراءة البيانات القديمة
        try:
            existing_df = conn.read(
                worksheet="Sheet1",
                ttl=0
            )

            if existing_df is None:
                existing_df = pd.DataFrame()

        except:
            existing_df = pd.DataFrame()

        # دمج البيانات
        final_df = pd.concat(
            [existing_df, new_df],
            ignore_index=True
        )

        # تحديث Google Sheet
        conn.update(
            worksheet="Sheet1",
            data=final_df
        )

        st.success("✅ تم حفظ سجل الصيانة بنجاح")

    except Exception as e:
        st.error("❌ حدث خطأ أثناء المزامنة")
        st.code(str(e))
        st.code(traceback.format_exc())
