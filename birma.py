import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. App Configuration ---
st.set_page_config(page_title="Factory Digital Log", layout="centered")
st.title("📲 Factory Operation & Maintenance")

# --- 2. Configuration & Paths ---
LOG_FILE = 'maintenance_logs.csv'
MACHINE_MAP = {
    "Blowing Machine": "blowing_machine.xlsx",
    "Labeling Machine": "labeling_machine.xlsx",
    "Conveyor System": "conveyor_machine.xlsx",
    "Packing Machine": "packing_machine.xlsx",
    "Palletizer Unit": "paletizer_machine.xlsx",
    "shrink Machine": "shrink_machine.xlsx"
}

# --- 3. Safety: Ensure Files Exist ---
def check_files():
    cols = ['Category', 'No', 'Name', 'Photo', 'Tools', 'Procedure', 'Freq', 'Status', 'Note', 'Staff']
    if not os.path.exists(LOG_FILE):
        pd.DataFrame(columns=['Date', 'Time', 'Machine', 'Task', 'Procedure', 'Status', 'Notes', 'Technician_Signature']).to_csv(LOG_FILE, index=False)
    
    # Create placeholder excels if missing
    for name, file in MACHINE_MAP.items():
        if not os.path.exists(file):
            empty_header = pd.DataFrame([[""]*10, [""]*10], columns=cols)
            sample_task = pd.DataFrame([['General', 1, 'Initial Check', '', 'Eyes', 'Verify machine stability', 'Daily', '', '', '']], columns=cols)
            pd.concat([empty_header, sample_task]).to_excel(file, index=False)

check_files()

# --- 4. Sidebar Control ---
st.sidebar.header("Control Panel")
selected_date = st.sidebar.date_input("Operation Date", datetime.now())
unit_name = st.sidebar.selectbox("Active Machine Unit", list(MACHINE_MAP.keys()))
active_file = MACHINE_MAP[unit_name]

# --- 5. Data Loading ---
@st.cache_data
def fetch_data(path):
    try:
        df = pd.read_excel(path, skiprows=2, engine='openpyxl')
        df.columns = ['Category', 'No', 'Name', 'Photo', 'Tools', 'Procedure', 'Freq', 'Status', 'Note', 'Staff']
        df['Category'] = df['Category'].ffill()
        return df
    except:
        return None

df_maint = fetch_data(active_file)

# --- 6. Technician Interface ---
st.header(f"🔧 {unit_name}")
st.write(f"Logged for: **{selected_date}**")

if df_maint is not None:
    with st.form("log_entry_form"):
        # Filter for Daily tasks to keep mobile view simple
        daily_tasks = df_maint[df_maint['Freq'].str.contains('Daily', na=False, case=False)]
        
        if daily_tasks.empty:
            st.info("No daily tasks found in the file. Displaying all tasks.")
            daily_tasks = df_maint.head(10)

        submission_data = []

        for idx, row in daily_tasks.iterrows():
            st.markdown(f"#### {row['Name']}")
            st.warning(f"📋 **Procedure:** {row['Procedure']}")
            
            c1, c2 = st.columns([1, 2])
            with c1:
                done = st.checkbox("Verified", key=f"check_{idx}")
            with c2:
                obs = st.text_input("Observations", key=f"obs_{idx}", placeholder="Optional notes...")

            if done:
                submission_data.append({
                    'Date': selected_date,
                    'Time': datetime.now().strftime("%H:%M:%S"),
                    'Machine': unit_name,
                    'Task': row['Name'],
                    'Procedure': row['Procedure'],
                    'Status': 'Completed',
                    'Notes': obs
                })
            st.divider()

        # --- SIGNATURE BLOCK ---
        st.subheader("✍️ Maintenance Signature")
        tech_name = st.text_input("Enter Technician Full Name:", placeholder="Signature required to save...")

        # --- SUBMIT LOGIC ---
        if st.form_submit_button("Save & Sign Report"):
            if not tech_name:
                st.error("❌ Signature Required: Please enter your name.")
            elif not submission_data:
                st.warning("⚠️ No tasks were marked as 'Verified'.")
            else:
                for entry in submission_data:
                    entry['Technician_Signature'] = tech_name
                
                # Append to CSV
                history = pd.read_csv(LOG_FILE)
                updated_history = pd.concat([history, pd.DataFrame(submission_data)], ignore_index=True)
                updated_history.to_csv(LOG_FILE, index=False)
                st.success(f"✅ Successfully Logged & Signed by {tech_name}")
else:
    st.error("Technical error loading machine file. Please check Excel formatting.")

# --- 7. History Quick View ---
if st.checkbox("Show Today's Activity Log"):
    if os.path.exists(LOG_FILE):
        logs = pd.read_csv(LOG_FILE)
        # Filter for today's logs to keep it clean
        today_logs = logs[logs['Date'] == str(selected_date)]
        st.dataframe(today_logs.tail(10), use_container_width=True)