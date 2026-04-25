import streamlit as st
import pandas as pd
import requests
import urllib.parse
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import plotly.graph_objects as go
import plotly.express as px
from sklearn.linear_model import LinearRegression

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="BIRMA Integrated System", page_icon="🏭", layout="wide")

# الربط بجوجل شيت (استخدام الحساب المؤمن للإنتاج الفعلي)
try:
    # يمكنك تبديل gsheets_secured بـ gsheets_testing إذا كنت ما زلت في مرحلة الاختبار
    URL_DATA = st.secrets["connections"]["gsheets_secured"]["spreadsheet"]
    conn = st.connection("gsheets_secured", type=GSheetsConnection)
except Exception as e:
    st.error("خطأ في الاتصال: تأكد من إعدادات Secrets في Streamlit Cloud")
    st.stop()

# --- 2. الإعدادات الديناميكية ---
CONFIG = {
    "Lines": ["Line 1", "Line 2"],
    "Products": {
        "Line 1": ["200 ml Carton", "200 ml Shrink", "600 ml Carton", "1.5 L Shrink"],
        "Line 2": ["200 ml Carton", "200 ml Shrink", "330 ml Carton", "331 ml Shrink"]
    },
    "Machines": ["Sidel Bloomer", "Krones Filler", "Labeler", "Shrink Wrapper", "Palletizer"]
}

# --- 3. الدوال المساعدة ---

def send_telegram_notification(msg):
    """إرسال إشعار فوري للتليجرام"""
    try:
        token = st.secrets["telegram"]["bot_token"]
        chat_id = st.secrets["telegram"]["chat_id"]
        safe_msg = urllib.parse.quote(msg)
        url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={safe_msg}&parse_mode=Markdown"
        requests.get(url)
    except:
        pass # لضمان عدم توقف التطبيق إذا فشل الإنترنت

def predict_waste(df, line, product, target_units):
    """التنبؤ بالهالك بناءً على العلاقة الخطية"""
    try:
        data = df[(df['Type'] == 'Production') & (df['Line'] == line) & (df['Product'] == product)]
        if len(data) < 3: return None
        X = data[['Output_Units']].values
        y = data['Waste_Bottles'].values
        model = LinearRegression().fit(X, y)
        return max(0, int(model.predict([[target_units]])[0]))
    except: return None

# --- 4. القائمة الجانبية (Sidebar) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/4300/4300058.png", width=100)
st.sidebar.title("نظام بيرما المتكامل")
menu = st.sidebar.selectbox("اختر القسم", ["📈 إدارة الإنتاج", "🔧 مركز الصيانة", "📊 التقارير الختامية"])
selected_line = st.sidebar.radio("خط العمل الحالي", CONFIG["Lines"])
pwd = st.sidebar.text_input("كلمة المرور", type="password")

# تحميل البيانات مرة واحدة
try:
    df_main = conn.read(spreadsheet=URL_DATA, ttl=0)
except:
    df_main = pd.DataFrame()

# التحقق من كلمة المرور
if pwd != "birma2026":
    st.warning("الرجاء إدخال كلمة المرور للوصول للنظام")
    st.stop()

# --- 5. قسم إدارة الإنتاج ---
if menu == "📈 إدارة الإنتاج":
    st.header(f"🚀 تسجيل إنتاج - {selected_line}")
    
    with st.form("prod_form"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("المشرف المسؤول")
            product = st.selectbox("الصنف المنتج", CONFIG["Products"][selected_line])
            target = st.number_input("كمية الإنتاج (وحدة)", min_value=0)
        with c2:
            preforms = st.number_input("البريفورم المستهلك (قطعة)", min_value=0)
            p_date = st.date_input("التاريخ", value=datetime.now())
        
        # توقع الذكاء الاصطناعي
        prediction = predict_waste(df_main, selected_line, product, target)
        if prediction:
            st.info(f"💡 توقع AI للهالك: {prediction} عبوة")

        if st.form_submit_button("حفظ وإرسال التقرير"):
            if name and target > 0:
                waste = preforms - (target * 20) # معادلة افتراضية
                eff = round(((target * 20) / (35000 * 15)) * 100, 1)
                
                new_data = pd.DataFrame([{
                    "Type": "Production", "Line": selected_line, "Date": str(p_date),
                    "Staff": name, "Product": product, "Output_Units": target,
                    "Waste_Bottles": waste, "Efficiency_%": eff, "Timestamp": datetime.now().strftime("%H:%M")
                }])
                
                updated_df = pd.concat([df_main, new_data], ignore_index=True)
                conn.update(spreadsheet=URL_DATA, data=updated_df)
                
                # إشعار تليجرام
                msg = f"✅ *إنتاج جديد*\nالخط: {selected_line}\nالصنف: {product}\nالكمية: {target}\nالهالك: {waste}\nالمشرف: {name}"
                send_telegram_notification(msg)
                st.success("تم التسجيل بنجاح")
                st.rerun()

# --- 6. قسم مركز الصيانة (الدمج الجديد) ---
elif menu == "🔧 مركز الصيانة":
    st.header(f"🛠 بلاغات صيانة - {selected_line}")
    
    with st.form("maint_form"):
        c1, c2 = st.columns(2)
        with c1:
            tech_name = st.text_input("الفني القائم بالإصلاح")
            machine = st.selectbox("المعدة المتأثرة", CONFIG["Machines"])
            issue = st.text_area("وصف العطل")
        with c2:
            action = st.text_area("الإجراء المتخذ")
            status = st.selectbox("حالة المعدة", ["جاهزة للعمل", "تحت الصيانة", "انتظار قطع غيار"])
            m_date = st.date_input("تاريخ العطل", value=datetime.now())

        if st.form_submit_button("تسجيل عطل وإرسال إشارة"):
            if tech_name and issue:
                new_maint = pd.DataFrame([{
                    "Type": "Maintenance", "Line": selected_line, "Date": str(m_date),
                    "Staff": tech_name, "Machine": machine, "Issue": issue,
                    "Action": action, "Status": status, "Timestamp": datetime.now().strftime("%H:%M")
                }])
                
                updated_df = pd.concat([df_main, new_maint], ignore_index=True)
                conn.update(spreadsheet=URL_DATA, data=updated_df)
                
                # إشعار تليجرام فوري للمهندسين
                m_msg = f"⚠️ *بلاغ صيانة*\nالمعدة: {machine}\nالعطل: {issue}\nالحالة: {status}\nالفني: {tech_name}"
                send_telegram_notification(m_msg)
                st.success("تم تسجيل بلاغ الصيانة وإخطار الفريق")
                st.rerun()

# --- 7. قسم التقارير ---
elif menu == "📊 التقارير الختامية":
    st.header("📊 مراجعة الأداء العام")
    if not df_main.empty:
        tab1, tab2 = st.tabs(["سجل الإنتاج", "سجل الأعطال"])
        
        with tab1:
            p_df = df_main[df_main['Type'] == 'Production'].copy()
            st.dataframe(p_df.tail(20)[::-1], use_container_width=True)
            fig = px.line(p_df, x='Date', y='Efficiency_%', color='Line', title="منحنى الكفاءة")
            st.plotly_chart(fig)
            
        with tab2:
            m_df = df_main[df_main['Type'] == 'Maintenance'].copy()
            st.dataframe(m_df.tail(20)[::-1], use_container_width=True)
            if not m_df.empty:
                fig2 = px.pie(m_df, names='Machine', title="توزيع الأعطال حسب المعدة")
                st.plotly_chart(fig2)