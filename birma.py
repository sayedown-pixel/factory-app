import streamlit as st
import pandas as pd
import os
import requests
import urllib.parse
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import plotly.graph_objects as go
import plotly.express as px
from sklearn.linear_model import LinearRegression

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="BIRMA Integrated System", page_icon="🏭", layout="wide")

# --- 2. الشعار والهوية (Brand & Credit) ---
# تحديث الشعار ليقرأ ملف birma mark.png من مجلدك
st.sidebar.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
try:
    # محاولة عرض الشعار بالاسم الجديد
    if os.path.exists("birma mark.png"):
        st.sidebar.image("birma mark.png", use_container_width=True)
    else:
        st.sidebar.markdown("<h1 style='color: #0047AB;'>BIRMA</h1>", unsafe_allow_html=True)
except:
    st.sidebar.markdown("<h1 style='color: #0047AB;'>BIRMA</h1>", unsafe_allow_html=True)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.markdown("<p style='text-align: center; font-size: 12px; color: gray; margin-bottom: 0;'>Designed by:</p>", unsafe_allow_html=True)
st.sidebar.markdown("<h3 style='text-align: center; color: #2E8B57; margin-top: 0;'>م/ السيد عون</h3>", unsafe_allow_html=True)
st.sidebar.divider()

# --- 3. نظام اللغات ---
ln = st.sidebar.selectbox("🌐 Language / اللغة", ["ar", "en"], index=0)

LANG = {
    "ar": {
        "menu": ["📈 إدارة الإنتاج", "🔧 مركز الصيانة المتكامل", "📊 السجلات والتقارير"],
        "line_label": "خط العمل",
        "prod_header": "🚀 تسجيل إنتاج -",
        "maint_header": "🛠 مركز صيانة",
        "maint_types": ["صيانة دورية (Daily Check)", "بلاغ أعطال (Breakdown)"],
        "save_btn": "حفظ البيانات وإرسال إشعار",
        "success_msg": "✅ تم الحفظ وإرسال التنبيه بنجاح",
        "eff_title": "متوسط الكفاءة %",
        "waste_title": "تحليل الهالك تاريخياً",
        "start_t": "بداية التوقف",
        "end_t": "نهاية الإصلاح",
        "note_label": "ملاحظات إضافية"
    },
    "en": {
        "menu": ["📈 Production", "🔧 Maintenance", "📊 Records & Reports"],
        "line_label": "Working Line",
        "prod_header": "🚀 Production -",
        "maint_header": "🛠 Maintenance Center",
        "maint_types": ["Daily Maintenance", "Breakdown"],
        "save_btn": "Save & Send Alert",
        "success_msg": "✅ Saved & Notified Successfully",
        "eff_title": "Avg Efficiency %",
        "waste_title": "Waste Analysis",
        "start_t": "Downtime Start",
        "end_t": "Repair End",
        "note_label": "Additional Notes"
    }
}

# --- 4. دوال المساعدة ---
def send_telegram(msg):
    try:
        token = st.secrets["telegram"]["bot_token"]
        chat_id = st.secrets["telegram"]["chat_id"]
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={urllib.parse.quote(msg)}&parse_mode=Markdown"
        requests.get(url)
    except: pass

def predict_waste_ai(df, line, product, target):
    try:
        data = df[(df['Type'] == 'Production') & (df['Line'] == line) & (df['Product'] == product)]
        if len(data) < 3: return None
        model = LinearRegression().fit(data[['Output_Units']].values, data['Waste_Bottles'].values)
        return max(0, int(model.predict([[target]])[0]))
    except: return None

# --- 5. الربط والبيانات ---
try:
    conn = st.connection("gsheets_testing", type=GSheetsConnection)
    df_main = conn.read(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], ttl=0)
except:
    df_main = pd.DataFrame()

# الإعدادات الفنية
CONFIG = {
    "الخط الأول(smi)": {"الأصناف": ["200 ml Carton", "200 ml Shrink", "600 ml Carton", "1.5 L Shrink"],
                 "العبوات": {"200 ml Carton": 48, "200 ml Shrink": 20, "600 ml Carton": 30, "1.5 L Shrink": 6},
                 "السرعة": {"200 ml Carton": 35000, "200 ml Shrink": 35000, "600 ml Carton": 20000, "1.5 L Shrink": 12000}},
    "الخط الثاني(welbing)": {"الأصناف": ["200 ml Carton", "200 ml Shrink", "330 ml Carton", "331 ml Shrink"],
                  "العبوات": {"200 ml Carton": 48, "200 ml Shrink": 20, "330 ml Carton": 40, "331 ml Shrink": 20},
                  "السرعة": {"200 ml Carton": 40000, "200 ml Shrink": 40000, "330 ml Carton": 40000, "331 ml Shrink": 40000}}
}
MACHINE_MAP = {"النفخ(blowing)": "blowing_machine.xlsx", "الليبل(labeling)": "labeling_machine.xlsx", "السيور(Conveyor)": "Conveyor_machine.xlsx", 
               "الكرتون(packing)": "packing_machine.xlsx", "البالتايزر(paletizer)": "paletizer_machine.xlsx", "الشرنك(shrink)": "shrink_machine.xlsx", "التعبئة(Filling)": "Filling_machine.xlsx"}

# --- 6. واجهة المستخدم ---
menu = st.sidebar.selectbox("القائمة", LANG[ln]["menu"])
selected_line = st.sidebar.radio(LANG[ln]["line_label"], list(CONFIG.keys()))

# --- أ. قسم الإنتاج ---
if menu == LANG[ln]["menu"][0]:
    st.header(f"{LANG[ln]['prod_header']} {selected_line}")
    with st.form("prod_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("اسم المشرف المسؤول")
            product = st.selectbox("الصنف المنتج", CONFIG[selected_line]["الأصناف"])
            target = st.number_input("الإنتاج الفعلي (وحدة/كرتونة)", min_value=0)
        with c2:
            preforms = st.number_input("البريفورم المستخدم (قطعة)", min_value=0)
            raw_type = "Carton" if "Carton" in product else "Shrink"
            raw_val = st.number_input(f"خامة التغليف المستخدمة ({raw_type})", min_value=0)
            p_date = st.date_input("تاريخ الوردية")
        
        pred = predict_waste_ai(df_main, selected_line, product, target) if target > 0 else None
        if pred: st.info(f"🔮 التوقع الذكي للهالك لهذه الكمية: {pred} قطعة")

        if st.form_submit_button(LANG[ln]["save_btn"]):
            b_per_u = CONFIG[selected_line]["العبوات"][product]
            total_b = target * b_per_u
            eff = round((total_b / (CONFIG[selected_line]["السرعة"][product] * 15)) * 100, 1)
            
            new_row = pd.DataFrame([{"Type": "Production", "Line": selected_line, "Date": str(p_date), "Staff": name, 
                                     "Product": product, "Output_Units": target, "Waste_Bottles": preforms - total_b, 
                                     "Waste_Raw": raw_val - target, "Efficiency_%": eff, "Timestamp": datetime.now().strftime("%H:%M")}])
            conn.update(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], data=pd.concat([df_main, new_row], ignore_index=True))
            
            send_telegram(f"🚀 *إنتاج جديد*\nالخط: {selected_line}\nالصنف: {product}\nالكمية: {target}\nالكفاءة: {eff}%\nالهالك: {preforms - total_b}\nالمشرف: {name}")
            st.success(LANG[ln]["success_msg"])
            st.rerun()

    if not df_main.empty:
        st.divider()
        p_df = df_main[df_main['Type'] == 'Production'].tail(10)
        if not p_df.empty:
            v1, v2 = st.columns(2)
            with v1:
                fig1 = go.Figure(go.Indicator(mode="gauge+number", value=p_df['Efficiency_%'].mean(), title={'text': LANG[ln]["eff_title"]}))
                st.plotly_chart(fig1, use_container_width=True)
            with v2:
                fig2 = px.bar(p_df, x='Date', y='Waste_Bottles', color='Product', title=LANG[ln]["waste_title"])
                st.plotly_chart(fig2, use_container_width=True)

# --- ب. قسم الصيانة ---
elif menu == LANG[ln]["menu"][1]:
    st.header(LANG[ln]["maint_header"])
    m_type = st.radio("نوع العملية", LANG[ln]["maint_types"], horizontal=True)
    machine = st.sidebar.selectbox("المعدة", list(MACHINE_MAP.keys()))

    if m_type == LANG[ln]["maint_types"][0]: # صيانة دورية
        path = MACHINE_MAP[machine]
        if os.path.exists(path):
            df_t = pd.read_excel(path, skiprows=2)
            df_t.columns = ['Cat', 'No', 'Name', 'Photo', 'Tools', 'Proc', 'Freq', 'Stat', 'Note', 'Staff']
            daily = df_t[df_t['Freq'] == 'Daily']
            with st.form("m_form"):
                tech = st.text_input("الفني القائم بالعمل")
                recs = []
                for i, r in daily.iterrows():
                    c_i, c_p = st.columns([2,1])
                    with c_i: 
                        st.markdown(f"**🔧 {r['Name']}**")
                        ok = st.checkbox("تم الفحص بنجاح", key=f"k{i}")
                        task_note = st.text_input(f"ملاحظة المهمة - {r['Name']}", key=f"tn{i}") # خانة ملاحظة لكل مهمة
                    with c_p:
                        img = os.path.join("images", str(r['Photo']).strip())
                        if os.path.exists(img): st.image(img, width=150)
                    if ok: recs.append({"Type": "Maint_Daily", "Line": selected_line, "Date": str(datetime.now().date()), "Machine": machine, "Task": r['Name'], "Staff": tech, "Notes": task_note})
                
                if st.form_submit_button(LANG[ln]["save_btn"]):
                    conn.update(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], data=pd.concat([df_main, pd.DataFrame(recs)], ignore_index=True))
                    send_telegram(f"🔧 *صيانة دورية تمّت*\nالماكينة: {machine}\nالفني: {tech}")
                    st.success("تم الحفظ"); st.rerun()

    else: # بلاغ أعطال
        with st.form("break_form"):
            t_name = st.text_input("الفني المسؤول")
            issue = st.text_area("وصف العطل")
            col1, col2 = st.columns(2)
            t1 = col1.time_input(LANG[ln]["start_t"])
            t2 = col2.time_input(LANG[ln]["end_t"])
            maint_note = st.text_area(LANG[ln]["note_label"]) # خانة الملاحظات العامة للأعطال
            if st.form_submit_button(LANG[ln]["save_btn"]):
                new_b = pd.DataFrame([{"Type": "Maint_Breakdown", "Line": selected_line, "Date": str(datetime.now().date()), "Machine": machine, "Staff": t_name, "Notes": f"من {t1} إلى {t2} | {issue} | ملاحظة: {maint_note}"}])
                conn.update(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], data=pd.concat([df_main, new_b], ignore_index=True))
                send_telegram(f"⚠️ *بلاغ عطل*\nالماكينة: {machine}\nالفني: {t_name}")
                st.success("تم الإرسال"); st.rerun()

# --- ج. قسم السجلات والتقارير ---
elif menu == LANG[ln]["menu"][2]:
    st.header("📊 السجلات المركزية")
    t1, t2 = st.tabs(["سجل الإنتاج", "سجل الصيانة"])
    with t1: st.dataframe(df_main[df_main['Type'] == 'Production'].tail(15)[::-1], use_container_width=True)
    with t2: st.dataframe(df_main[df_main['Type'].str.contains('Maint', na=False)].tail(15)[::-1], use_container_width=True)

# --- تذييل الصفحة ---
st.markdown("<br><hr><center><p style='color: gray;'>BIRMA Integrated System v4.5 | <b>Design by: Eng. Elsayed Aoun</b></p></center>", unsafe_allow_html=True)