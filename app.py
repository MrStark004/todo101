import streamlit as st
from auth_db import csr, conn
import datetime
import pandas as pd
import io 
import pytz

# --- PAGE CONFIG & THEME ---
st.set_page_config(page_title="Pro Task Manager", page_icon="✨", layout="centered")

# --- CUSTOM CSS FOR COLORS & ANIMATIONS ---
st.markdown("""
    <style>
    /* Main Background Gradient */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Gradient Buttons */
    div.stButton > button {
        background: linear-gradient(to right, #6a11cb 0%, #2575fc 100%);
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 8px;
        transition: all 0.3s ease;
        font-weight: bold;
    }
    
    /* Click Animation */
    div.stButton > button:active {
        transform: scale(0.95);
        filter: brightness(1.2);
    }
    
    /* Card Hover Effect */
    [data-testid="stVerticalBlockBorderWrapper"] {
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        background-color: white;
        border-radius: 12px;
    }
    
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }

    /* Input focus colors */
    input:focus {
        border-color: #6a11cb !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("✨ Pro Task Manager")

# --- SESSION LOGIC ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --- AUTHENTICATION ---
if not st.session_state.authenticated:
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    with tab1:
        login_user = st.text_input("Username", key="login_user")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", type="primary"):
            from auth_db import verify_user
            if verify_user(login_user, login_pass):
                st.session_state.authenticated = True
                st.session_state.username = login_user
                st.rerun()
            else:
                st.error("Invalid credentials")
    with tab2:
        new_user = st.text_input("New Username", key="new_user")
        new_pass = st.text_input("New Password", type="password", key="new_pass")
        if st.button("Create Account"):
            from auth_db import create_user
            if create_user(new_user, new_pass):
                st.success("Account created!")
            else:
                st.error("Username taken!")

# --- MAIN APP ---
else:
    with st.sidebar:
        st.markdown(f"### Welcome, **{st.session_state.username}**")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()
        st.divider()
        st.subheader("📥 Data Export")
        csr.execute("SELECT todo_title, todo_desc, todo_done, due_date, due_time, priority FROM mytodos WHERE todo_added=?", (st.session_state.username,))
        rows = csr.fetchall()
        if rows:
            df = pd.DataFrame(rows, columns=["Task", "Description", "Done", "Date", "Time", "Priority"])
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            st.download_button("Download Excel", buffer.getvalue(), f"{st.session_state.username}_tasks.xlsx")

    # --- ADD TASK WITH AUTO-RESET ---
    with st.expander("➕ Create New Task", expanded=True):
        # Using st.form with clear_on_submit=True solves your reset issue
        with st.form("task_form", clear_on_submit=True):
            title = st.text_input("Task Title")
            desc = st.text_area("Description")
            
            c1, c2, c3 = st.columns(3)
            ist = pytz.timezone('Asia/Kolkata')
            now = datetime.datetime.now(ist)
            
            with c1:
                y = st.selectbox("Year", range(now.year, now.year+5))
            with c2:
                m_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                m = st.selectbox("Month", m_names, index=now.month-1)
            with c3:
                d = st.selectbox("Day", range(1, 32), index=now.day-1)

            ch, cm, cp = st.columns([2, 2, 1])
            with ch: h12 = st.slider("Hour", 1, 12, 12)
            with cm: mi = st.slider("Minute", 0, 55, 0, 5)
            with cp: ampm = st.radio("AM/PM", ["AM", "PM"], horizontal=True)
            
            prio = st.select_slider("Priority", ["Low 💤", "Medium ⚡", "High 🔥"], value="Medium ⚡")
            
            submit = st.form_submit_button("Add Task")
            
            if submit:
                if title:
                    m_num = m_names.index(m) + 1
                    h24 = (h12 % 12) + (12 if ampm == "PM" else 0)
                    try:
                        s_date = datetime.date(y, m_num, d)
                        s_time = datetime.time(h24, mi)
                        csr.execute("INSERT INTO mytodos (todo_added, todo_title, todo_desc, todo_done, due_date, due_time, priority) VALUES (?,?,?,?,?,?,?)",
                                    (st.session_state.username, title, desc, False, str(s_date), str(s_time), prio))
                        conn.commit()
                        st.toast("Task Saved!")
                        st.rerun()
                    except ValueError:
                        st.error("Invalid Date!")
                else:
                    st.warning("Title required!")

    st.divider()

    # --- TASK DISPLAY ---
    filt = st.radio("Filters", ["All", "Pending", "Completed"], horizontal=True)
    q = "SELECT todo_id, todo_title, todo_desc, todo_done, due_date, due_time, priority FROM mytodos WHERE todo_added=?"
    if filt == "Pending": q += " AND todo_done=0"
    elif filt == "Completed": q += " AND todo_done=1"
    q += " ORDER BY due_date ASC, due_time ASC"
    
    csr.execute(q, (st.session_state.username,))
    for tid, tt, td, tdone, tda, tti, tp in csr.fetchall():
        with st.container(border=True):
            col1, col2, col3 = st.columns([0.5, 4, 1])
            with col1:
                if st.checkbox("", value=bool(tdone), key=f"chk_{tid}"):
                    csr.execute("UPDATE mytodos SET todo_done=1 WHERE todo_id=?", (tid,))
                    conn.commit()
                    st.rerun()
                elif tdone:
                    csr.execute("UPDATE mytodos SET todo_done=0 WHERE todo_id=?", (tid,))
                    conn.commit()
                    st.rerun()
            with col2:
                st.markdown(f"### {tt}" if not tdone else f"### ~~{tt}~~")
                st.caption(f"📅 {tda} | ⏰ {tti} | 🏷️ {tp}")
                if td: st.text(td)
            with col3:
                if st.button("🗑️", key=f"del_{tid}"):
                    csr.execute("DELETE FROM mytodos WHERE todo_id=?", (tid,))
                    conn.commit()
                    st.rerun()