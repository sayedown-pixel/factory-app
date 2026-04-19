import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. Master Configuration ---
st.set_page_config(page_title="Factory Production Pro", layout="centered")

# --- 2. Database & Auto-File Generator ---
LOG_FILE = 'maintenance_logs.csv'
MACHINE_MAP = {
    "Blowing Machine": "blowing_machine.xlsx",
    "Labeling Machine": "labeling_machine.xlsx",
    "Conveyor System": "conveyor_machine.xlsx",
    "Packing Machine": "packing_machine.xlsx",
    "Palletizer Unit": "paletizer_machine.xlsx",
    "shrink Machine": "shrink_machine.xlsx",
}

# Function to create dummy files if missing (So the app doesn't crash)
def ensure_files_exist():
    cols = ['Category', 'No', 'Name', 'Photo', 'Tools', 'Procedure', 'Freq', 'Status', 'Note', 'Staff']
    dummy_data = [['General', 1, 'Visual Inspection', '', 'Eyes', 'Check for leaks/noise', 'Daily', '', '', '']]
    
    for name, file in MACHINE_MAP.items():
        if not os.path.exists(file):
            # Create a basic template starting from row 3
            empty_rows = pd.DataFrame([[""]*10, [""]*10], columns=cols)
            data_rows = pd.DataFrame(dummy_data, columns=cols)
            pd.concat([empty_rows, data_rows]).to_excel(file, index=False)

ensure_files_exist()

if not os.path.exists(LOG_FILE):
    pd.DataFrame(columns=['Date', 'Time', 'Machine', 'Task', 'Procedure', 'Status', 'Notes', 'Technician_Signature']).to_csv(LOG_FILE, index=False)

# --- 3. Sidebar Selection ---
st.sidebar.title("🏭 Factory Operations")
target_date = st.sidebar.date_input("Log Date", datetime.now())
unit_name = st.sidebar.selectbox("Select Machine", list(MACHINE_MAP.keys()))
unit_file = MACHINE_MAP[unit_name]

# --- 4. Data Loading ---
@st.cache_data
def load_data(path):
    try:
        df = pd.read_excel(path, skiprows=2, engine='openpyxl')
        df.columns = ['Category', 'No', 'Name', 'Photo', 'Tools', 'Procedure', 'Freq', 'Status', 'Note', 'Staff']
        df['Category'] = df['Category'].ffill()
        return df
    except:
        return None

engine_data = load_data(unit_file)

# --- 5. Mobile Interface ---
st.header(f"⚙️ {unit_name}")
st.write(f"Logged at: **{target_date}**")

if engine_data is not None:
    with st.form("operation_form"):
        daily_list = engine_data[engine_data['Freq'] == 'Daily']
        submission_queue = []

        for i, row in daily_list.iterrows():
            st.markdown(f"**{row['Name']}**")
            st.info(f"📋 **Procedure:** {row['Procedure']}")
            
            c1, c2 = st.columns([1, 2])
            with c1:
                is_done = st.checkbox("Verified", key=f"c_{i}")
            with c2:
                comment = st.text_input("Note", key=f"n_{i}", placeholder="Observation...")

            if is_done:
                submission_queue.append({
                    'Date': target_date,
                    'Time': datetime.now().strftime("%H:%M:%S"), # Auto-Timestamp
                    'Machine': unit_name,
                    'Task': row['Name'],
                    'Procedure': row['Procedure'],
                    'Status': 'Completed',
                    'Notes': comment
                })
            st.divider()

        # --- SIGNATURE SECTION ---
        st.subheader("✍️ Technician Signature")
        signature = st.text_input("Full Name Required:", placeholder="Type your name to sign...")

        if st.form_submit_button("Submit & Sign Report"):
            if not signature:
                st.error("❌ Error: You must sign before submitting!")
            elif submission_queue:
                for entry in submission_queue:
                    entry['Technician_Signature'] = signature
                
                history = pd.read_csv(LOG_FILE)
                pd.concat([history, pd.DataFrame(submission_queue)], ignore_index=True).to_csv(LOG_FILE, index=False)
                st.success(f"✅ Report Signed by {signature} and saved!")
            else:
                st.warning("No tasks marked as done.")

# --- 6. Quick History Review ---
if st.checkbox("Show Today's Signed Logs"):
    if os.path.exists(LOG_FILE):
        logs = pd.read_csv(LOG_FILE)
        st.table(logs[logs['Date'] == str(target_date)].tail(5))