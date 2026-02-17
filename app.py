import streamlit as st
from auth_db import csr, conn
import datetime
import pandas as pd
import io 
import pytz

# Page Configuration
st.set_page_config(page_title="Pro Task Manager", page_icon="✅", layout="centered")

st.title("✅ Pro Task Manager")

# -------------------------
# Session & Login Logic
# -------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "username" not in st.session_state:
    st.session_state.username = ""

# -------------------------
# LOGIN / SIGNUP SCREEN
# -------------------------
if not st.session_state.authenticated:
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])

    with tab1:
        st.subheader("Welcome Back")
        login_user = st.text_input("Username", key="login_user")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", type="primary"):
            from auth_db import verify_user
            if verify_user(login_user, login_pass):
                st.session_state.authenticated = True
                st.session_state.username = login_user
                st.toast(f"Welcome back, {login_user}!")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        st.subheader("New Account")
        new_user = st.text_input("New Username", key="new_user")
        new_pass = st.text_input("New Password", type="password", key="new_pass")
        if st.button("Create Account"):
            from auth_db import create_user
            if create_user(new_user, new_pass):
                st.success("Account created! Please login.")
            else:
                st.error("Username already taken!")

# -------------------------
# MAIN APP DASHBOARD
# -------------------------
else:
    # --- SIDEBAR ---
    with st.sidebar:
        st.write(f"👤 **{st.session_state.username}**")
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()
        
        st.divider()
        
        # --- EXCEL DOWNLOADER ---
        st.subheader("📥 Export Data")
        csr.execute("""
            SELECT todo_title, todo_desc, todo_done, due_date, due_time, priority 
            FROM mytodos WHERE todo_added=?
        """, (st.session_state.username,))
        rows = csr.fetchall()

        if rows:
            df = pd.DataFrame(rows, columns=["Task", "Description", "Done", "Date", "Time", "Priority"])
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Todos')
            
            st.download_button(
                label="Download Excel",
                data=buffer.getvalue(),
                file_name=f"{st.session_state.username}_todos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.caption("No tasks to export.")

    # --- ADD TASK SECTION (INTERACTIVE UI) ---
    with st.expander("➕ Add New Task", expanded=True):
        st.caption("📝 Task Details")
        title = st.text_input("Task Title", placeholder="What needs to be done?")
        desc = st.text_area("Description", placeholder="Add some details...", height=68)
        
        st.divider()
        st.caption("📅 Date & Time Machine")

        # --- CUSTOM DATE SELECTOR ---
        col_y, col_m, col_d = st.columns([1, 1, 1])
        ist = pytz.timezone('Asia/Kolkata')
        today = datetime.datetime.now(ist).date()
        
        with col_y:
            year = st.selectbox("Year", range(today.year, today.year + 5), index=0)
        
        with col_m:
            month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            month = st.selectbox("Month", month_names, index=today.month - 1)
        
        with col_d:
            day = st.selectbox("Day", range(1, 32), index=today.day - 1)

        # --- CUSTOM TIME SELECTOR ---
        col_h, col_min, col_ampm = st.columns([2, 2, 1])
        with col_h:
            hour_12 = st.slider("Hour", 1, 12, 12)
        with col_min:
            minute = st.slider("Minute", 0, 55, 0, step=5)
        with col_ampm:
            ampm = st.radio("Period", ["AM", "PM"], horizontal=True)

        st.divider()
        priority = st.select_slider("Priority Level", options=["Low 💤", "Medium ⚡", "High 🔥"], value="Medium ⚡")

        if st.button("Add Task", type="primary", use_container_width=True):
            if not title:
                st.warning("⚠️ Please enter a Task Title!")
            else:
                try:
                    # Date Handling
                    month_num = month_names.index(month) + 1
                    try:
                        selected_date = datetime.date(year, month_num, day)
                    except ValueError:
                        st.error(f"⚠️ Invalid Date: {month} {day} doesn't exist!")
                        st.stop()

                    # Time Handling (12h to 24h)
                    if ampm == "PM" and hour_12 != 12:
                        hour_24 = hour_12 + 12
                    elif ampm == "AM" and hour_12 == 12:
                        hour_24 = 0
                    else:
                        hour_24 = hour_12
                    final_time = datetime.time(hour_24, minute)

                    # Save
                    csr.execute(
                        """INSERT INTO mytodos 
                        (todo_added, todo_title, todo_desc, todo_done, due_date, due_time, priority) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (st.session_state.username, title, desc, False, str(selected_date), str(final_time), priority)
                    )
                    conn.commit()
                    st.balloons()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    st.divider()

    # --- TASK LIST ---
    filter_status = st.radio("Show:", ["All", "Pending", "Completed"], horizontal=True)
    query = "SELECT todo_id, todo_title, todo_desc, todo_done, due_date, due_time, priority FROM mytodos WHERE todo_added=?"
    params = [st.session_state.username]

    if filter_status == "Pending": query += " AND todo_done=0"
    elif filter_status == "Completed": query += " AND todo_done=1"
    query += " ORDER BY due_date ASC, due_time ASC"

    csr.execute(query, tuple(params))
    todos = csr.fetchall()

    if not todos:
        st.info("No tasks found. Relax! 🌴")
    
    for todo_id, t_title, t_desc, t_done, t_date, t_time, t_prio in todos:
        with st.container(border=True):
            c1, c2, c3 = st.columns([0.5, 4, 1])
            with c1:
                is_done = st.checkbox("", value=bool(t_done), key=f"check_{todo_id}")
                if is_done != bool(t_done):
                    csr.execute("UPDATE mytodos SET todo_done=? WHERE todo_id=?", (is_done, todo_id))
                    conn.commit()
                    st.rerun()
            with c2:
                if t_done: st.markdown(f"~~**{t_title}**~~")
                else: st.markdown(f"**{t_title}**")
                st.caption(f"📅 {t_date} at {t_time} | {t_prio}")
                if t_desc: st.text(t_desc)
            with c3:
                if st.button("🗑️", key=f"del_{todo_id}"):
                    csr.execute("DELETE FROM mytodos WHERE todo_id=?", (todo_id,))
                    conn.commit()
                    st.rerun()

    # --- DEBUG VIEW ---
    st.divider()
    with st.expander("🔍 View Database (Debug)"):
        csr.execute("SELECT * FROM mytodos")
        st.dataframe(pd.DataFrame(csr.fetchall()), hide_index=True)