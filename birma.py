import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. App Configuration ---
st.set_page_config(page_title="Full Production Line Control", layout="centered")
st.title("📲 BIRMA Factory Operation Management")

# --- 2. Database (Log) Setup ---
LOG_FILE = 'maintenance_logs.csv'
if not os.path.exists(LOG_FILE):
    pd.DataFrame(columns=['Date', 'Machine', 'Task', 'Standards', 'Status', 'Technician_Note', 'Staff']).to_csv(LOG_FILE, index=False)

# --- 3. Sidebar: Full Line Machine Selection ---
st.sidebar.title("Line Control")
selected_date = st.sidebar.date_input("Operation Date", datetime.now())

# Added all the requested machines
machine_dict = {
    "Blowing Machine": "blowing_machine.xlsx",
    "Labeling Machine": "labeling_machine.xlsx",
    "Conveyor System": "conveyor_machine.xlsx",
    "Packing Machine": "packing_machine.xlsx",
    "Palletizer Machine": "paletizer_machine.xlsx",
    "Shrink Machine": "shrink_machine.xlsx"
}

selected_machine = st.sidebar.selectbox("Select Machine Unit", list(machine_dict.keys()))
active_file = machine_dict[selected_machine]

# --- 4. Data Loading Logic ---
@st.cache_data
def load_machine_data(file_path):
    if os.path.exists(file_path):
        try:
            # Consistent formatting for all excel files
            df = pd.read_excel(file_path, skiprows=2, engine='openpyxl')
            # Standardizing column names for the app logic
            df.columns = ['Category', 'No', 'Name', 'Photo', 'Tools', 'Standards', 'Freq', 'Status', 'Note', 'Staff']
            df['Category'] = df['Category'].ffill()
            return df
        except Exception as e:
            st.error(f"Error reading {file_path}: {e}")
            return None
    return None

df_maint = load_machine_data(active_file)

# --- 5. Execution Interface ---
st.header(f"🔧 {selected_machine}")
st.write(f"Maintenance Checklist for: **{selected_date}**")

if df_maint is not None:
    with st.form("operation_form"):
        # Filter for Daily tasks to keep the UI clean
        daily_tasks = df_maint[df_maint['Freq'] == 'Daily']
        
        if daily_tasks.empty:
            st.info("No daily tasks found for this machine. Check Weekly/Monthly schedules.")
        
        log_entries = []

        for idx, row in daily_tasks.iterrows():
            st.markdown(f"#### {row['Name']}")
            
            # Displaying the "Standards" as requested - The Procedure to follow
            st.warning(f"📋 **Action Required:** {row['Standards']}")
            
            col_img, col_inputs = st.columns([1, 2])
            
            with col_img:
                image_path = f"images/{row['Photo']}"
                if pd.notna(row['Photo']) and os.path.exists(image_path):
                    st.image(image_path, width=120)
                else:
                    st.caption("No image")

            with col_inputs:
                is_done = st.checkbox("Task Completed", key=f"check_{idx}")
                note = st.text_input("Tech Observation", key=f"note_{idx}", placeholder="Any issues?")
                
                if is_done:
                    log_entries.append({
                        'Date': selected_date,
                        'Machine': selected_machine,
                        'Task': row['Name'],
                        'Standards': row['Standards'],
                        'Status': 'Completed',
                        'Technician_Note': note,
                        'Staff': "Field Technician"
                    })
            st.divider()

        # Submit to Log
        if st.form_submit_button("Submit Unit Report"):
            if log_entries:
                current_log = pd.read_csv(LOG_FILE)
                new_data = pd.DataFrame(log_entries)
                pd.concat([current_log, new_data], ignore_index=True).to_csv(LOG_FILE, index=False)
                st.success(f"Log for {selected_machine} saved successfully!")
            else:
                st.error("Please mark tasks as completed before submitting.")
else:
    st.error(f"File '{active_file}' is missing. Please add the Excel file to the project folder.")

# --- 6. Manager View (Quick Check) ---
if st.checkbox("Show Recent Logs"):
    st.subheader("Last 10 Records")
    if os.path.exists(LOG_FILE):
        history = pd.read_csv(LOG_FILE)
        st.dataframe(history.tail(10))