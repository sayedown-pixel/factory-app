import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. Master Configuration ---
st.set_page_config(page_title="Production Line Pro", layout="centered")

# --- 2. Dynamic Machine Directory ---
MACHINE_MAP = {
    "Blowing Machine": "blowing_machine.xlsx",
    "Labeling Machine": "labeling_machine.xlsx",
    "Conveyor System": "conveyor_machine.xlsx",
    "Packing Machine": "packing_machine.xlsx",
    "Palletizer Unit": "paletizer_machine.xlsx",
    "shrink Machine": "shrink_machine.xlsx"
}

# --- 3. Sidebar Setup ---
st.sidebar.title("Factory Control")
target_date = st.sidebar.date_input("Select Log Date", datetime.now())
unit_name = st.sidebar.selectbox("Active Unit", list(MACHINE_MAP.keys()))
unit_file = MACHINE_MAP[unit_name]

# --- 4. Database Persistence ---
LOG_FILE = 'maintenance_logs.csv'
if not os.path.exists(LOG_FILE):
    # Added 'Technician_Signature' to the permanent record
    pd.DataFrame(columns=['Date', 'Machine', 'Task', 'Procedure', 'Status', 'Notes', 'Technician_Signature']).to_csv(LOG_FILE, index=False)

# --- 5. Data Loader ---
def load_factory_data(path):
    if os.path.exists(path):
        try:
            df = pd.read_excel(path, skiprows=2, engine='openpyxl')
            df.columns = ['Category', 'No', 'Name', 'Photo', 'Tools', 'Procedure', 'Freq', 'Status', 'Note', 'Staff']
            df['Category'] = df['Category'].ffill()
            return df
        except:
            return None
    return None

engine_data = load_factory_data(unit_file)

# --- 6. Interface ---
st.header(f"⚙️ {unit_name}")
st.write(f"Technician Dashboard | **{target_date}**")

if engine_data is not None:
    with st.form("mobile_log_form"):
        # Focus on Daily tasks
        daily_list = engine_data[engine_data['Freq'] == 'Daily']
        submission_queue = []

        for i, row in daily_list.iterrows():
            st.markdown(f"**Task: {row['Name']}**")
            st.warning(f"💡 **Procedure:** {row['Procedure']}")
            
            c1, c2 = st.columns([1, 2])
            with c1:
                is_ok = st.checkbox("Done", key=f"check_{i}")
            with c2:
                comment = st.text_input("Observation", key=f"obs_{i}")

            if is_ok:
                submission_queue.append({
                    'Date': target_date,
                    'Machine': unit_name,
                    'Task': row['Name'],
                    'Procedure': row['Procedure'],
                    'Status': 'Verified',
                    'Notes': comment
                })
            st.divider()

        # --- SIGNATURE SECTION ---
        st.subheader("✍️ Final Validation")
        signature = st.text_input("Enter Technician Full Name (Signature):", placeholder="e.g. Ahmed Ali")

        if st.form_submit_button("Submit Unit Report"):
            if not signature:
                st.error("❌ Submission Failed: Technician signature is required!")
            elif submission_queue:
                # Add the signature to all completed tasks in this session
                for entry in submission_queue:
                    entry['Technician_Signature'] = signature
                
                history = pd.read_csv(LOG_FILE)
                pd.concat([history, pd.DataFrame(submission_queue)], ignore_index=True).to_csv(LOG_FILE, index=False)
                st.success(f"✅ Report for {unit_name} signed by {signature} and synced!")
            else:
                st.warning("No tasks were marked as completed.")
else:
    st.error(f"Waiting for {unit_file}. Please ensure file is in the directory.")

# --- 7. Manager View (Optional Check) ---
if st.checkbox("Show Recent Signed Logs"):
    if os.path.exists(LOG_FILE):
        st.dataframe(pd.read_csv(LOG_FILE).tail(10))
