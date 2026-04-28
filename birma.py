import streamlit as st
import pandas as pd
import os
import requests
import urllib.parse
from datetime import datetime
from streamlit_gsheets import GSheetsConnection
import plotly.graph_objects as go
import plotly.express as px

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="BIRMA Integrated System", page_icon="🏭", layout="wide")

# --- 2. نظام اللغات ---
if 'lang' not in st.session_state:
    st.session_state.lang = 'ar'

ln = st.sidebar.selectbox("🌐 Language / اللغة", ["ar", "en"], index=0)

LANG = {
    "ar": {
        "designer": "م/ السيد عون",
        "menu": ["📈 إدارة الإنتاج", "🔧 مركز الصيانة المتكامل", "📊 السجلات والتقارير", "📦 إدارة المخازن"],
        "line_label": "خط العمل",
        "sup_label": "اسم المشرف المسؤول",
        "prod_label": "الصنف المنتج",
        "target_label": "الإنتاج الفعلي (وحدة)",
        "preform_label": "البريفورم المستخدم (قطعة)",
        "raw_label": "خامة التغليف المستخدمة",
        "date_label": "تاريخ الوردية",
        "maint_header": "🛠 مركز صيانة",
        "maint_types": ["صيانة دورية (Planned)", "بلاغ أعطال (Breakdown)"],
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
        "del_success": "🗑 تم حذف السجل بنجاح",
        "tools_label": "🔧 الأدوات:",
        "proc_label": "📜 معيار العمل/التنظيف:",
        "weekend_msg": "🏖 اليوم الجمعة عطلة نهاية الأسبوع - لا توجد صيانات دورية مجدولة.",
        "inventory_header": "📦 إدارة المخازن",
        "current_stock": "📋 المخزون الحالي",
        "receipt": "➕ استلام مشتريات",
        "alerts": "⚠️ تنبيهات المخزون",
        "material": "المادة",
        "quantity": "الكمية",
        "invoice": "رقم الفاتورة",
        "receipt_date": "تاريخ الاستلام",
        "register_receipt": "تسجيل الاستلام",
        "low_stock_alert": "⚠️ المواد التالية وصلت للحد الأدنى:",
        "all_good": "✅ جميع المواد فوق الحد الأدنى",
        "edit_stock": "✏️ تعديل الرصيد يدوياً (للمشرف فقط)",
        "new_stock": "الرصيد الجديد",
        "update": "تحديث",
        "password": "كلمة المرور",
        "shortage_error": "⚠️ عجز في المواد: ",
        "stock_updated": "تم تحديث الرصيد",
        "receipt_log": "سجل الاستلامات",
        "view_logs": "📋 سجل الحركات"
    },
    "en": {
        "designer": "Eng. Elsayed Aoun",
        "menu": ["📈 Production Management", "🔧 Maintenance Center", "📊 Records & Reports", "📦 Inventory Management"],
        "line_label": "Working Line",
        "sup_label": "Supervisor Name",
        "prod_label": "Product Type",
        "target_label": "Actual Output (Units)",
        "preform_label": "Preforms Used (pcs)",
        "raw_label": "Raw Packaging Used",
        "date_label": "Shift Date",
        "maint_header": "🛠 Maintenance Center",
        "maint_types": ["Planned Maintenance", "Breakdown"],
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
        "del_success": "🗑 Record Deleted Successfully",
        "tools_label": "🔧 Tools:",
        "proc_label": "📜 Cleaning/Work Standard:",
        "weekend_msg": "🏖 Today is Friday (Weekend) - No scheduled maintenance.",
        "inventory_header": "📦 Inventory Management",
        "current_stock": "📋 Current Stock",
        "receipt": "➕ Receive Materials",
        "alerts": "⚠️ Stock Alerts",
        "material": "Material",
        "quantity": "Quantity",
        "invoice": "Invoice Number",
        "receipt_date": "Receipt Date",
        "register_receipt": "Register Receipt",
        "low_stock_alert": "⚠️ Following materials are below minimum level:",
        "all_good": "✅ All materials above minimum level",
        "edit_stock": "✏️ Manual Stock Adjustment (Admin Only)",
        "new_stock": "New Stock Value",
        "update": "Update",
        "password": "Password",
        "shortage_error": "⚠️ Material shortage: ",
        "stock_updated": "Stock updated successfully",
        "receipt_log": "Receipt Log",
        "view_logs": "📋 Transaction Log"
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
def load_main_data():
    try:
        conn = st.connection("gsheets_testing", type=GSheetsConnection)
        df = conn.read(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], ttl=0)
        return conn, df
    except:
        return None, pd.DataFrame()

conn, df_main = load_main_data()

def send_telegram(msg):
    try:
        token = st.secrets["telegram"]["bot_token"]
        chat_id = st.secrets["telegram"]["chat_id"]
        requests.get(f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={urllib.parse.quote(msg)}&parse_mode=Markdown")
    except:
        pass

# --- 5. تحميل بيانات المخزون ---
def load_inventory():
    """تحميل بيانات المخزون من raw.xlsx"""
    if os.path.exists("raw.xlsx"):
        df_inv = pd.read_excel("raw.xlsx")
        # التأكد من وجود الأعمدة المطلوبة
        required_cols = ["Material_ID", "Material_Name_AR", "Material_Name_EN", "Unit", "Current_Stock", "Min_Stock", "Max_Stock", "Unit_Cost", "Last_Updated"]
        for col in required_cols:
            if col not in df_inv.columns:
                df_inv[col] = None
        return df_inv
    else:
        return pd.DataFrame(columns=["Material_ID", "Material_Name_AR", "Material_Name_EN", "Unit", "Current_Stock", "Min_Stock", "Max_Stock", "Unit_Cost", "Last_Updated"])

def update_inventory(df_inv):
    """تحديث بيانات المخزون في ملف raw.xlsx"""
    df_inv.to_excel("raw.xlsx", index=False)
    return True

# --- 6. تحميل BOM من ملف bom.xlsx ---
def load_bom_from_file():
    """تحميل قائمة المكونات من ملف bom.xlsx"""
    if os.path.exists("bom.xlsx"):
        df_bom = pd.read_excel("bom.xlsx")
        return df_bom
    else:
        # BOM افتراضية إذا لم يوجد الملف
        return pd.DataFrame(columns=["Product_Name", "Preform_Item", "Preform_Qty", "Cap_Item", "Cap_Qty", 
                                      "Label_Item", "Label_Qty", "Carton_Item", "Carton_Qty", "Shrink_Item", "Shrink_roll"])

def calculate_required_materials(product, quantity_produced, df_bom):
    """
    حساب كميات المواد المطلوبة للإنتاج بناءً على BOM
    الشرنك: يتم حسابه من قيمة Shrink_roll (نصيب الوحدة من قطعة الشرنك)
    """
    product_row = df_bom[df_bom["Product_Name"] == product]
    if product_row.empty:
        return None, f"المنتج {product} غير موجود في قائمة المكونات"
    
    required = {}
    
    # بريفورم
    preform_item = product_row["Preform_Item"].values[0]
    preform_qty = product_row["Preform_Qty"].values[0]
    if pd.notna(preform_item) and pd.notna(preform_qty) and preform_qty > 0:
        required[preform_item] = preform_qty * quantity_produced
    
    # غطاء
    cap_item = product_row["Cap_Item"].values[0]
    cap_qty = product_row["Cap_Qty"].values[0]
    if pd.notna(cap_item) and pd.notna(cap_qty) and cap_qty > 0:
        required[cap_item] = cap_qty * quantity_produced
    
    # ليبل
    label_item = product_row["Label_Item"].values[0]
    label_qty = product_row["Label_Qty"].values[0]
    if pd.notna(label_item) and pd.notna(label_qty) and label_qty > 0:
        required[label_item] = label_qty * quantity_produced
    
    # كرتون
    carton_item = product_row["Carton_Item"].values[0]
    carton_qty = product_row["Carton_Qty"].values[0]
    if pd.notna(carton_item) and pd.notna(carton_qty) and carton_qty > 0:
        required[carton_item] = carton_qty * quantity_produced
    
    # شرنك (معالجة خاصة: Shrink_roll هي نصيب الوحدة من قطعة الشرنك)
    shrink_item = product_row["Shrink_Item"].values[0]
    shrink_roll = product_row["Shrink_roll"].values[0]
    if pd.notna(shrink_item) and pd.notna(shrink_roll) and shrink_roll > 0:
        # shrink_roll تعني: كل وحدة تستهلك X من قطعة الشرنك
        # مثال: 0.0005 يعني أن قطعة الشرنك الواحدة تكفي لـ 2000 وحدة
        # عدد قطع الشرنك = الكمية المنتجة * shrink_roll (مع التقريب لأعلى)
        shrink_pieces = quantity_produced * shrink_roll
        # تقريب لأعلى لأن قطعة الشرنك لا تتجزأ
        import math
        shrink_pieces_rounded = math.ceil(shrink_pieces)
        required[shrink_item] = shrink_pieces_rounded
    
    return required, None

def consume_materials(product, quantity_produced, df_inv, df_bom):
    """صرف المواد الأولية من المخزون"""
    required, error = calculate_required_materials(product, quantity_produced, df_bom)
    
    if error:
        return df_inv, False, error
    
    # التحقق من توفر الرصيد
    shortages = []
    new_df = df_inv.copy()
    
    for idx, row in new_df.iterrows():
        mat_name_ar = row["Material_Name_AR"]
        if mat_name_ar in required:
            req_qty = required[mat_name_ar]
            current = row["Current_Stock"]
            unit = row.get("Unit", "قطعة")
            
            if pd.isna(current):
                current = 0
            
            if current < req_qty:
                shortages.append(f"{mat_name_ar} (المطلوب: {req_qty}، المتوفر: {current} {unit})")
            else:
                new_df.at[idx, "Current_Stock"] = current - req_qty
                new_df.at[idx, "Last_Updated"] = str(datetime.now())
    
    if shortages:
        return df_inv, False, f"{LANG[ln].get('shortage_error', 'Shortage:')} {', '.join(shortages)}"
    
    # رسالة تفصيلية عن المواد المنصرفة
    details = ", ".join([f"{k}: {v}" for k, v in required.items()])
    
    return new_df, True, f"✅ تم صرف {quantity_produced} وحدة من {product}\n📦 المواد: {details}"

def check_low_stock(df_inv):
    """فحص المواد التي وصلت للحد الأدنى"""
    low_stock = df_inv[df_inv["Current_Stock"] <= df_inv["Min_Stock"]]
    if not low_stock.empty:
        msg = "🚨 *تنبيه مخزون منخفض*\n"
        for _, row in low_stock.iterrows():
            unit = row.get("Unit", "")
            msg += f"- {row['Material_Name_AR']}: {row['Current_Stock']} {unit} (الحد الأدنى: {row['Min_Stock']})\n"
        send_telegram(msg)
    return low_stock

# --- 7. بيانات خطوط الإنتاج ---
CONFIG = {
    "الخط الأول(smi)": {
        "الأصناف": ["200 ml Carton", "200 ml Shrink", "600 ml Carton", "1.5 L Shrink"],
        "العبوات": {"200 ml Carton": 48, "200 ml Shrink": 20, "600 ml Carton": 30, "1.5 L Shrink": 6},
        "السرعة": {"200 ml Carton": 35000, "200 ml Shrink": 35000, "600 ml Carton": 20000, "1.5 L Shrink": 12000}
    },
    "الخط الثاني(welbing)": {
        "الأصناف": ["200 ml Carton", "200 ml Shrink", "330 ml Carton", "331 ml Shrink"],
        "العبوات": {"200 ml Carton": 48, "200 ml Shrink": 20, "330 ml Carton": 40, "331 ml Shrink": 20},
        "السرعة": {"200 ml Carton": 40000, "200 ml Shrink": 40000, "330 ml Carton": 40000, "331 ml Shrink": 40000}
    }
}

MACHINE_MAP = {
    "النفخ(blowing)": "blowing_machine.xlsx",
    "الليبل(labeling)": "labeling_machine.xlsx",
    "السيور(Conveyor)": "Conveyor_machine.xlsx",
    "الكرتون(packing)": "packing_machine.xlsx",
    "البالتايزر(paletizer)": "paletizer_machine.xlsx",
    "الشرنك(shrink)": "shrink_machine.xlsx",
    "التعبئة(filling)": "Filling_machine.xlsx"
}

# --- 8. فلترة مواعيد الصيانة ---
def get_scheduled_tasks(df_tasks):
    today = datetime.now()
    day_name = today.strftime('%A')
    is_first_of_month = (today.day == 1)
    
    if day_name == 'Friday':
        return pd.DataFrame()
    
    allowed_freqs = ['Daily']
    if day_name == 'Saturday':
        allowed_freqs.append('Weekly')
    if is_first_of_month:
        allowed_freqs.append('Monthly')
    
    if 'Freq' in df_tasks.columns:
        return df_tasks[df_tasks['Freq'].isin(allowed_freqs)]
    return pd.DataFrame()

# --- 9. واجهة المستخدم الرئيسية ---
selected_menu = st.sidebar.selectbox("Menu", LANG[ln]["menu"])
selected_line = st.sidebar.radio(LANG[ln]["line_label"], list(CONFIG.keys()))

# تحميل البيانات المشتركة
df_inv = load_inventory()
df_bom = load_bom_from_file()

# --- الإنتاج ---
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

        if st.form_submit_button(LANG[ln]["save_btn"]):
            b_per_u = CONFIG[selected_line]["العبوات"][product]
            total_b = target * b_per_u
            speed = CONFIG[selected_line]["السرعة"][product]
            if speed > 0:
                eff = round((total_b / (speed * 15)) * 100, 1)
            else:
                eff = 0
            
            # صرف المواد من المخزون
            df_inv_updated, success, msg = consume_materials(product, target, df_inv, df_bom)
            
            if not success:
                st.error(msg)
            else:
                # تحديث المخزون
                if update_inventory(df_inv_updated):
                    # حفظ سجل الإنتاج
                    new_row = pd.DataFrame([{
                        "Type": "Production",
                        "Line": selected_line,
                        "Date": str(p_date),
                        "Staff": name,
                        "Product": product,
                        "Output_Units": target,
                        "Waste_Bottles": preforms - total_b if preforms > 0 else 0,
                        "Waste_Raw": raw_val - target if raw_val > 0 else 0,
                        "Efficiency_%": eff,
                        "Timestamp": datetime.now().strftime("%H:%M")
                    }])
                    
                    if conn is not None and not df_main.empty:
                        conn.update(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], data=pd.concat([df_main, new_row], ignore_index=True))
                    elif conn is not None:
                        conn.update(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], data=new_row)
                    
                    # فحص المخزون المنخفض
                    check_low_stock(df_inv_updated)
                    
                    # إرسال إشعار تلغرام
                    send_telegram(f"🚀 *Production Update*\nLine: {selected_line}\nProduct: {product}\nOutput: {target}\nEff: {eff}%\n{msg.replace('✅', '')}")
                    
                    st.success(f"{LANG[ln]['success_msg']}\n{msg}")
                    st.rerun()
                else:
                    st.error("فشل في تحديث المخزون")

# --- الصيانة ---
elif selected_menu == LANG[ln]["menu"][1]:
    st.header(LANG[ln]["maint_header"])
    m_type = st.radio("Type", LANG[ln]["maint_types"], horizontal=True)
    machine = st.sidebar.selectbox("Machine", list(MACHINE_MAP.keys()))

    if m_type == LANG[ln]["maint_types"][0]:
        path = MACHINE_MAP[machine]
        if os.path.exists(path):
            df_raw = pd.read_excel(path, skiprows=2)
            df_raw.columns = ['Cat', 'No', 'Name', 'Photo', 'Tools', 'Proc', 'Freq', 'Stat', 'Note', 'Staff']
            scheduled_tasks = get_scheduled_tasks(df_raw)
            
            if scheduled_tasks.empty:
                st.warning(LANG[ln]["weekend_msg"])
            else:
                with st.form("m_form"):
                    tech = st.text_input(LANG[ln]["tech_label"])
                    recs = []
                    for i, r in scheduled_tasks.iterrows():
                        st.divider()
                        c_i, c_p = st.columns([2,1])
                        with c_i:
                            st.markdown(f"### 🔧 {r['Name']} ({r['Freq']})")
                            st.markdown(f"**{LANG[ln]['tools_label']}** `{r['Tools'] if pd.notna(r['Tools']) else 'N/A'}`")
                            st.info(f"**{LANG[ln]['proc_label']}**\n{r['Proc'] if pd.notna(r['Proc']) else 'N/A'}")
                            ok = st.checkbox(f"DONE - {r['Name']}", key=f"k{i}")
                            note = st.text_input(LANG[ln]["note_label"], key=f"n{i}")
                        with c_p:
                            img = os.path.join("images", str(r['Photo']).strip())
                            if os.path.exists(img):
                                st.image(img, use_container_width=True)
                        if ok:
                            recs.append({
                                "Type": "Maint_Daily",
                                "Line": selected_line,
                                "Date": str(datetime.now().date()),
                                "Machine": machine,
                                "Task": r['Name'],
                                "Staff": tech,
                                "Notes": note
                            })
                    
                    if st.form_submit_button(LANG[ln]["save_btn"]):
                        if conn is not None and recs:
                            new_df = pd.DataFrame(recs)
                            if not df_main.empty:
                                conn.update(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], data=pd.concat([df_main, new_df], ignore_index=True))
                            else:
                                conn.update(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], data=new_df)
                        st.success(LANG[ln]["success_msg"])
                        st.rerun()
    else:
        with st.form("break_form"):
            t_name = st.text_input(LANG[ln]["tech_label"])
            issue = st.text_area(LANG[ln]["issue_label"])
            col1, col2 = st.columns(2)
            t1 = col1.time_input(LANG[ln]["start_t"])
            t2 = col2.time_input(LANG[ln]["end_t"])
            m_note = st.text_area(LANG[ln]["note_label"])
            if st.form_submit_button(LANG[ln]["save_btn"]):
                new_b = pd.DataFrame([{
                    "Type": "Maint_Breakdown",
                    "Line": selected_line,
                    "Date": str(datetime.now().date()),
                    "Machine": machine,
                    "Staff": t_name,
                    "Notes": f"{t1}-{t2} | {issue} | {m_note}"
                }])
                if conn is not None:
                    if not df_main.empty:
                        conn.update(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], data=pd.concat([df_main, new_b], ignore_index=True))
                    else:
                        conn.update(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], data=new_b)
                send_telegram(f"⚠️ *Breakdown*\nMachine: {machine}\nTech: {t_name}\nIssue: {issue}")
                st.success(LANG[ln]["success_msg"])
                st.rerun()

# --- السجلات والتقارير ---
elif selected_menu == LANG[ln]["menu"][2]:
    st.header(LANG[ln]["menu"][2])
    if df_main is not None and not df_main.empty:
        prod_data = df_main[df_main['Type'] == 'Production'].tail(15)
        if not prod_data.empty and 'Efficiency_%' in prod_data.columns:
            g1, g2 = st.columns(2)
            with g1:
                eff_mean = prod_data['Efficiency_%'].mean() if not prod_data['Efficiency_%'].isna().all() else 0
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=eff_mean,
                    title={'text': LANG[ln]["eff_title"]}
                ))
                st.plotly_chart(fig_g, use_container_width=True)
            with g2:
                if 'Waste_Bottles' in prod_data.columns:
                    fig_b = px.bar(prod_data, x='Date', y='Waste_Bottles', color='Product', title=LANG[ln]["waste_title"])
                    st.plotly_chart(fig_b, use_container_width=True)
        tab1, tab2 = st.tabs([LANG[ln]["history_p"], LANG[ln]["history_m"]])
        with tab1:
            prod_logs = df_main[df_main['Type'] == 'Production'].tail(20)[::-1]
            if not prod_logs.empty:
                st.dataframe(prod_logs)
            else:
                st.info("لا توجد سجلات إنتاج")
        with tab2:
            maint_logs = df_main[df_main['Type'].str.contains('Maint', na=False)].tail(20)[::-1]
            if not maint_logs.empty:
                st.dataframe(maint_logs)
            else:
                st.info("لا توجد سجلات صيانة")
    else:
        st.info("لا توجد بيانات مسجلة حتى الآن")

# --- إدارة المخازن ---
elif selected_menu == LANG[ln]["menu"][3]:
    st.header(LANG[ln]["inventory_header"])
    
    # إعادة تحميل المخزون للتأكد من أحدث البيانات
    df_inv = load_inventory()
    
    if df_inv.empty:
        st.warning("لا توجد بيانات مخزون. يرجى التأكد من وجود ملف raw.xlsx")
    else:
        tab1, tab2, tab3 = st.tabs([LANG[ln]["current_stock"], LANG[ln]["receipt"], LANG[ln]["alerts"]])
        
        with tab1:
            # عرض المخزون
            display_cols = ["Material_ID", "Material_Name_AR", "Unit", "Current_Stock", "Min_Stock", "Max_Stock", "Last_Updated"]
            available_cols = [col for col in display_cols if col in df_inv.columns]
            st.dataframe(df_inv[available_cols], use_container_width=True)
            
            with st.expander(LANG[ln]["edit_stock"]):
                pw_inv = st.text_input(LANG[ln]["password"], type="password", key="inv_pw")
                if pw_inv == "admin123":
                    selected_material = st.selectbox(LANG[ln]["material"], df_inv["Material_Name_AR"])
                    new_stock = st.number_input(LANG[ln]["new_stock"], min_value=0.0, step=1.0)
                    if st.button(LANG[ln]["update"]):
                        idx = df_inv[df_inv["Material_Name_AR"] == selected_material].index[0]
                        df_inv.at[idx, "Current_Stock"] = new_stock
                        df_inv.at[idx, "Last_Updated"] = str(datetime.now())
                        if update_inventory(df_inv):
                            st.success(LANG[ln]["stock_updated"])
                            st.rerun()
        
        with tab2:
            st.subheader(LANG[ln]["receipt"])
            with st.form("receipt_form"):
                material = st.selectbox(LANG[ln]["material"], df_inv["Material_Name_AR"])
                qty_received = st.number_input(LANG[ln]["quantity"], min_value=0.0, step=1.0)
                invoice_no = st.text_input(LANG[ln]["invoice"])
                receipt_date = st.date_input(LANG[ln]["receipt_date"])
                notes = st.text_area("ملاحظات")
                
                if st.form_submit_button(LANG[ln]["register_receipt"]):
                    idx = df_inv[df_inv["Material_Name_AR"] == material].index[0]
                    df_inv.at[idx, "Current_Stock"] += qty_received
                    df_inv.at[idx, "Last_Updated"] = str(datetime.now())
                    
                    if update_inventory(df_inv):
                        send_telegram(f"📥 *استلام مخزون*\nمادة: {material}\nالكمية: {qty_received}\nفاتورة: {invoice_no}")
                        
                        # تسجيل حركة الاستلام في السجل الرئيسي (اختياري)
                        receipt_record = pd.DataFrame([{
                            "Type": "Inventory_Receipt",
                            "Date": str(receipt_date),
                            "Material": material,
                            "Quantity": qty_received,
                            "Invoice": invoice_no,
                            "Notes": notes,
                            "Timestamp": str(datetime.now())
                        }])
                        if conn is not None:
                            if not df_main.empty:
                                conn.update(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], data=pd.concat([df_main, receipt_record], ignore_index=True))
                            else:
                                conn.update(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], data=receipt_record)
                        
                        st.success(f"تم تسجيل استلام {qty_received} من {material}")
                        st.rerun()
        
        with tab3:
            low_stock = check_low_stock(df_inv)
            if not low_stock.empty:
                st.warning(LANG[ln]["low_stock_alert"])
                alert_cols = ["Material_Name_AR", "Current_Stock", "Min_Stock", "Unit"]
                available_alert_cols = [col for col in alert_cols if col in low_stock.columns]
                st.dataframe(low_stock[available_alert_cols])
            else:
                st.success(LANG[ln]["all_good"])

# --- 10. لوحة تحكم المشرف ---
st.sidebar.divider()
with st.sidebar.expander(LANG[ln]["admin_title"]):
    pw = st.text_input(LANG[ln]["password"], type="password", key="admin_pw")
    if pw == "admin123":
        if df_main is not None and not df_main.empty:
            # إنشاء قائمة للسجلات
            df_main_display = df_main.copy()
            if 'Type' in df_main_display.columns:
                df_main_display['Display'] = df_main_display['Type'].astype(str) + " - " + df_main_display.index.astype(str)
                row_to_del = st.selectbox("Select Record", df_main_display.index, format_func=lambda x: df_main_display.loc[x, 'Display'] if 'Display' in df_main_display.columns else str(x))
                if st.button(LANG[ln]["delete_btn"]):
                    df_updated = df_main.drop(row_to_del)
                    if conn is not None:
                        conn.update(spreadsheet=st.secrets["connections"]["gsheets_testing"]["spreadsheet"], data=df_updated)
                    st.success(LANG[ln]["del_success"])
                    st.rerun()

# --- تذييل الصفحة ---
st.markdown(f"<br><hr><center><p style='color: gray;'>BIRMA v7.0 | <b>Designed by: {LANG[ln]['designer']}</b></p></center>", unsafe_allow_html=True)