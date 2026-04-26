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

# --- 2. نظام اللغات ---
if 'lang' not in st.session_state:
    st.session_state.lang = 'ar'

ln = st.sidebar.selectbox("🌐 Language / اللغة", ["ar", "en"], index=0)

LANG = {
    "ar": {
        "designer": "م/ السيد عون",
        "menu": ["📈 إدارة الإنتاج", "🔧 مركز الصيانة المتكامل", "📊 السجلات والتقارير"],
        "line_label": "خط العمل",
        "sup_label": "اسم المشرف المسؤول",
        "prod_label": "الصنف المنتج",
        "target_label": "الإنتاج الفعلي (وحدة)",
        "preform_label": "البريفورم المستخدم (قطعة)",
        "raw_label": "خامة التغليف المستخدمة",
        "date_label": "تاريخ الوردية",
        "maint_header": "🛠 مركز صيانة",
        "maint_types": ["صيانة دورية (Daily Check)", "بلاغ أعطال (Breakdown)"],
        "tech_label": "الفني المسؤول",
        "issue_label": "وصف العطل",
        "start_t": "بداية التوقف",
        "end_t": "نهاية الإصلاح",
        "note_label": "ملاحظات إضافية",
        "save_btn": "حفظ البيانات وإرسال إشعار",
        "success_msg": "✅ تم الحفظ وإرسال التنبيه بنجاح",
        "eff_title": "متوسط الكفاءة %",
        "waste_title": "تحليل الهالك تاريخياً",
        "history_p": "سجل الإنتاج",
        "history_m": "سجل الصيانة",
        "admin_title": "🔒 لوحة التحكم (للمشرف)",
        "delete_btn": "حذف السجل المختار",
        "del_success": "🗑 تم حذف السجل بنجاح"
    },
    "en": {
        "designer": "Eng. Elsayed Oun",
        "menu": ["📈 Production Management", "🔧 Maintenance Center", "📊 Records & Reports"],
        "line_label": "Working Line",
        "sup_label": "Supervisor Name",
        "prod_label": "Product Type",
        "target_label": "Actual Output (Units)",
        "preform_label": "Preforms Used (pcs)",
        "raw_label": "Raw Packaging Used",
        "date_label": "Shift Date",
        "maint_header": "🛠 Maintenance Center",
        "maint_types": ["Daily Maintenance", "Breakdown"],
        "tech_label": "Technician Name",
        "issue_label": "Issue Description",
        "start_t": "Downtime Start",
        "end_t": "Repair End",
        "note_label": "Additional Notes",
        "save_btn": "Save & Send Alert",
        "success_msg": "✅ Saved & Notified Successfully",
        "eff_title": "Average Efficiency %",
        "waste_title": "Historical Waste Analysis",
        "history_p": "Production Logs",
        "history_m": "Maintenance Logs",
        "admin_title": "🔒 Admin Panel",
        "delete_btn": "Delete Selected Record",
        "del_success": "🗑 Record Deleted Successfully"
    }
}

# --- 3. الهوية والشعار ---
st.sidebar.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
if os.path.exists("birma mark.png"):
    st.sidebar.image("birma mark.png", use_container_width=True)
else:
    st.sidebar.markdown("<h1 style='color: #0047AB;'>BIRMA</h1>", unsafe_allow_html=True)
st.sidebar.markdown("</div>", unsafe_allow_html=True)

st.sidebar.divider()
st.sidebar.markdown(f"<p style='text-align: center; font-size: 12px; color: gray; margin-bottom:0;'>Designed by:</p>", unsafe_allow_html=True)
st.sidebar.markdown(f"<h3 style='text-align: center; color: #2E8B57; margin-top:0;'>{LANG[ln]['designer']}</h3>", unsafe_allow_html=True)
st.sidebar.divider()

# --- 4. الربط والخدمات ---
try:
    conn = st.connection("gsheets_testing", type=GSheetsConnection)
    df_main = conn.read(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], ttl=0)
except:
    df_main = pd.DataFrame()

def send_telegram(msg):
    try:
        token = st.secrets["telegram"]["bot_token"]
        chat_id = st.secrets["telegram"]["chat_id"]
        requests.get(f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={urllib.parse.quote(msg)}&parse_mode=Markdown")
    except: pass

def predict_waste_ai(df, line, product, target):
    try:
        data = df[(df['Type'] == 'Production') & (df['Line'] == line) & (df['Product'] == product)]
        if len(data) < 3: return None
        model = LinearRegression().fit(data[['Output_Units']].values, data['Waste_Bottles'].values)
        return max(0, int(model.predict([[target]])[0]))
    except: return None

CONFIG = {
    "الخط الأول": {"الأصناف": ["200 ml Carton", "200 ml Shrink", "600 ml Carton", "1.5 L Shrink"],
                 "العبوات": {"200 ml Carton": 48, "200 ml Shrink": 20, "600 ml Carton": 30, "1.5 L Shrink": 6},
                 "السرعة": {"200 ml Carton": 35000, "200 ml Shrink": 35000, "600 ml Carton": 20000, "1.5 L Shrink": 12000}},
    "الخط الثاني": {"الأصناف": ["200 ml Carton", "200 ml Shrink", "330 ml Carton", "331 ml Shrink"],
                  "العبوات": {"200 ml Carton": 48, "200 ml Shrink": 20, "330 ml Carton": 40, "331 ml Shrink": 20},
                  "السرعة": {"200 ml Carton": 40000, "200 ml Shrink": 40000, "330 ml Carton": 40000, "331 ml Shrink": 40000}}
}
MACHINE_MAP = {"(blowing)النفخ": "blowing_machine.xlsx", "(label)الليبل": "labeling_machine.xlsx", "(conveyor)السيور": "Conveyor_machine.xlsx", 
               "(carton)الكرتون": "packing_machine.xlsx", "(palitizer)البالتايزر": "paletizer_machine.xlsx", "(shrink)الشرنك": "shrink_machine.xlsx", "(filler)التعبئة": "Filling_machine.xlsx"}

# --- 5. واجهة المستخدم ---
selected_menu = st.sidebar.selectbox("Menu", LANG[ln]["menu"])
selected_line = st.sidebar.radio(LANG[ln]["line_label"], list(CONFIG.keys()))

# أ. الإنتاج
if selected_menu == LANG[ln]["menu"][0]:
    st.header(f"{LANG[ln]['menu'][0]} - {selected_line}")
    with st.form("prod_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input(LANG[ln]["sup_label"])
            product = st.selectbox(LANG[ln]["prod_label"], CONFIG[selected_line]["الأصناف"])
            target = st.number_input(LANG[ln]["target_label"], min_value=0)
        with c2:
            preforms = st.number_input(LANG[ln]["preform_label"], min_value=0)
            raw_type = "Carton" if "Carton" in product else "Shrink"
            raw_val = st.number_input(f"{LANG[ln]['raw_label']} ({raw_type})", min_value=0)
            p_date = st.date_input(LANG[ln]["date_label"])
        
        ai_pred = predict_waste_ai(df_main, selected_line, product, target) if target > 0 else None
        if ai_pred: st.info(f"🔮 AI Waste Prediction: {ai_pred} pcs")

        if st.form_submit_button(LANG[ln]["save_btn"]):
            b_per_u = CONFIG[selected_line]["العبوات"][product]
            total_b = target * b_per_u
            eff = round((total_b / (CONFIG[selected_line]["السرعة"][product] * 15)) * 100, 1)
            new_row = pd.DataFrame([{"Type": "Production", "Line": selected_line, "Date": str(p_date), "Staff": name, 
                                     "Product": product, "Output_Units": target, "Waste_Bottles": preforms - total_b, 
                                     "Waste_Raw": raw_val - target, "Efficiency_%": eff, "Timestamp": datetime.now().strftime("%H:%M")}])
            conn.update(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], data=pd.concat([df_main, new_row], ignore_index=True))
            send_telegram(f"🚀 *Production Update*\nLine: {selected_line}\nProduct: {product}\nOutput: {target}\nEff: {eff}%\nSup: {name}")
            st.success(LANG[ln]["success_msg"]); st.rerun()

# ب. الصيانة
elif selected_menu == LANG[ln]["menu"][1]:
    st.header(LANG[ln]["maint_header"])
    m_type = st.radio("Type", LANG[ln]["maint_types"], horizontal=True)
    machine = st.sidebar.selectbox("Machine", list(MACHINE_MAP.keys()))

    if m_type == LANG[ln]["maint_types"][0]: # دورية
        path = MACHINE_MAP[machine]
        if os.path.exists(path):
            df_t = pd.read_excel(path, skiprows=2)
            df_t.columns = ['Cat', 'No', 'Name', 'Photo', 'Tools', 'Proc', 'Freq', 'Stat', 'Note', 'Staff']
            daily = df_t[df_t['Freq'] == 'Daily']
            with st.form("m_form"):
                tech = st.text_input(LANG[ln]["tech_label"])
                recs = []
                for i, r in daily.iterrows():
                    c_i, c_p = st.columns([2,1])
                    with c_i:
                        st.markdown(f"**🔧 {r['Name']}**")
                        ok = st.checkbox("OK", key=f"k{i}")
                        note = st.text_input(LANG[ln]["note_label"], key=f"n{i}")
                    with c_p:
                        img = os.path.join("images", str(r['Photo']).strip())
                        if os.path.exists(img): st.image(img, width=150)
                    if ok: recs.append({"Type": "Maint_Daily", "Line": selected_line, "Date": str(datetime.now().date()), "Machine": machine, "Task": r['Name'], "Staff": tech, "Notes": note})
                if st.form_submit_button(LANG[ln]["save_btn"]):
                    conn.update(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], data=pd.concat([df_main, pd.DataFrame(recs)], ignore_index=True))
                    st.success(LANG[ln]["success_msg"]); st.rerun()
    else: # أعطال
        with st.form("break_form"):
            t_name = st.text_input(LANG[ln]["tech_label"])
            issue = st.text_area(LANG[ln]["issue_label"])
            col1, col2 = st.columns(2)
            t1 = col1.time_input(LANG[ln]["start_t"])
            t2 = col2.time_input(LANG[ln]["end_t"])
            m_note = st.text_area(LANG[ln]["note_label"])
            if st.form_submit_button(LANG[ln]["save_btn"]):
                new_b = pd.DataFrame([{"Type": "Maint_Breakdown", "Line": selected_line, "Date": str(datetime.now().date()), "Machine": machine, "Staff": t_name, "Notes": f"{t1}-{t2} | {issue} | {m_note}"}])
                conn.update(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], data=pd.concat([df_main, new_b], ignore_index=True))
                send_telegram(f"⚠️ *Breakdown*\nMachine: {machine}\nTech: {t_name}\nIssue: {issue}")
                st.success(LANG[ln]["success_msg"]); st.rerun()

# ج. السجلات
elif selected_menu == LANG[ln]["menu"][2]:
    st.header(LANG[ln]["menu"][2])
    if not df_main.empty:
        prod_data = df_main[df_main['Type'] == 'Production'].tail(15)
        if not prod_data.empty:
            g1, g2 = st.columns(2)
            with g1:
                fig_g = go.Figure(go.Indicator(mode="gauge+number", value=prod_data['Efficiency_%'].mean(), title={'text': LANG[ln]["eff_title"]}))
                st.plotly_chart(fig_g, use_container_width=True)
            with g2:
                fig_b = px.bar(prod_data, x='Date', y='Waste_Bottles', color='Product', title=LANG[ln]["waste_title"])
                st.plotly_chart(fig_b, use_container_width=True)

        tab1, tab2 = st.tabs([LANG[ln]["history_p"], LANG[ln]["history_m"]])
        with tab1: st.dataframe(df_main[df_main['Type'] == 'Production'].tail(20)[::-1])
        with tab2: st.dataframe(df_main[df_main['Type'].str.contains('Maint', na=False)].tail(20)[::-1])

# --- 6. لوحة تحكم المشرف (جديد) ---
st.sidebar.divider()
with st.sidebar.expander(LANG[ln]["admin_title"]):
    pw = st.text_input("Password", type="password")
    if pw == "admin123": # يمكنك تغيير كلمة المرور هنا
        if not df_main.empty:
            row_to_del = st.selectbox("Select Row ID", df_main.index)
            if st.button(LANG[ln]["delete_btn"]):
                df_updated = df_main.drop(row_to_del)
                conn.update(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], data=df_updated)
                st.success(LANG[ln]["del_success"])
                st.rerun()

st.markdown(f"<br><hr><center><p style='color: gray;'>BIRMA v5.8 | <b>Designed by: {LANG[ln]['designer']}</b></p></center>", unsafe_allow_html=True)
