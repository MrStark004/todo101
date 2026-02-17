import streamlit as st
from auth_db import csr, conn
import datetime
import pandas as pd
import io

# Page Configuration (Browser Tab Title & Icon)
st.set_page_config(page_title="Pro Todo App", page_icon="✅", layout="centered")

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
    # Sidebar for User Info & Logout
    with st.sidebar:
        st.write(f"👤 **{st.session_state.username}**")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()
        st.divider()
        st.info("💡 Tip: Use the 'Priority' filter to focus on urgent tasks.")

    
    st.divider()
    
    # 1. Fetch all user data
    csr.execute("""
        SELECT todo_title, todo_desc, todo_done, due_date, due_time, priority 
        FROM mytodos WHERE todo_added=?
    """, (st.session_state.username,))
    data = csr.fetchall()

    # 2. Convert to DataFrame (Table)
    df = pd.DataFrame(data, columns=["Task", "Description", "Done", "Date", "Time", "Priority"])
    
    # 3. Create Excel file in memory
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='My Todos')
    
    # 4. Create the Download Button
    st.download_button(
        label="📥 Download Excel",
        data=buffer.getvalue(),
        file_name=f"{st.session_state.username}_todos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --- INPUT SECTION ---
    with st.expander("➕ Add New Task", expanded=True):
        col1, col2 = st.columns([2, 1])
        with col1:
            title = st.text_input("Task Title")
        with col2:
            priority = st.selectbox("Priority", ["🔥 High", "⚡ Medium", "💤 Low"])

        desc = st.text_area("Description (Optional)")

        # Date and Time Selection
        c1, c2 = st.columns(2)
        with c1:
            due_date = st.date_input("Due Date", datetime.date.today())
        with c2:
            due_time = st.time_input("Due Time", datetime.datetime.now().time())

        if st.button("Add Task", type="primary"):
            if title:
                csr.execute(
                    """INSERT INTO mytodos 
                    (todo_added, todo_title, todo_desc, todo_done, due_date, due_time, priority) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (st.session_state.username, title, desc, False, str(due_date), str(due_time), priority)
                )
                conn.commit()
                st.success("Task added!")
                st.rerun()
            else:
                st.warning("Please enter a task title.")

    st.divider()

    # --- FILTER SECTION ---
    filter_status = st.radio("Show:", ["All", "Pending", "Completed"], horizontal=True)

    # --- FETCH DATA ---
    query = "SELECT todo_id, todo_title, todo_desc, todo_done, due_date, due_time, priority FROM mytodos WHERE todo_added=?"
    params = [st.session_state.username]

    if filter_status == "Pending":
        query += " AND todo_done=0"
    elif filter_status == "Completed":
        query += " AND todo_done=1"
        
    # Sort by Date (So urgent stuff is at the top)
    query += " ORDER BY due_date ASC, due_time ASC"

    csr.execute(query, tuple(params))
    todos = csr.fetchall()

    # --- DISPLAY TASKS ---
    if not todos:
        st.info("No tasks found here. Relax! 🌴")
    
    for todo_id, t_title, t_desc, t_done, t_date, t_time, t_prio in todos:
        
        # Priority Color Coding
        border_color = "red" if "High" in t_prio else "orange" if "Medium" in t_prio else "blue"
        
        # Card-like layout using a container
        with st.container(border=True):
            c1, c2, c3 = st.columns([0.5, 4, 1])
            
            with c1:
                # Checkbox
                is_done = st.checkbox("", value=bool(t_done), key=f"check_{todo_id}")
                if is_done != bool(t_done):
                    csr.execute("UPDATE mytodos SET todo_done=? WHERE todo_id=?", (is_done, todo_id))
                    conn.commit()
                    st.rerun()

            with c2:
                # Title and Details
                if t_done:
                    st.markdown(f"~~**{t_title}**~~")
                else:
                    st.markdown(f"**{t_title}**")
                
                # Metadata line (Date | Time | Priority)
                st.caption(f"📅 {t_date} at {t_time} | {t_prio}")
                if t_desc:
                    st.text(t_desc)

            with c3:
                # Delete Button
                if st.button("🗑️", key=f"del_{todo_id}"):
                    csr.execute("DELETE FROM mytodos WHERE todo_id=?", (todo_id,))
                    conn.commit()
                    st.rerun()

# -------------------------
# DEBUG: Database Viewer
# -------------------------
st.divider()
with st.expander("🔍 View Database (Debug Mode)"):
    c1, c2 = st.tabs(["Tasks", "Users"])
    
    with c1:
        st.subheader("All Tasks Table")
        # Fetch raw data
        csr.execute("SELECT * FROM mytodos")
        data = csr.fetchall()
        
        # Display as a clean table
        if data:
            st.dataframe(data, column_config={
                0: "ID",
                1: "Owner",
                2: "Title",
                3: "Desc",
                4: "Done",
                5: "Date",
                6: "Time",
                7: "Priority"
            })
        else:
            st.write("Table is empty.")

    with c2:
        st.subheader("Registered Users")
        csr.execute("SELECT username, password FROM users")
        user_data = csr.fetchall()
        st.write(user_data)