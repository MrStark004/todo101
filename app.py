import streamlit as st
from auth_db import csr, conn

st.title("Welcome to my WebPage")
st.header("My Todo App")

# -------------------------
# Session defaults
# -------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "username" not in st.session_state:
    st.session_state.username = ""

# -------------------------
# If Logged In
# -------------------------
if st.session_state.authenticated:
    
    # Logout button (Optional helper)
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.rerun()

    st.subheader(f"Add Todo ({st.session_state.username})")

    title = st.text_input("Enter todo Title")
    desc = st.text_area("Brief about todo")

    if st.button("Add Todo"):
        if not title or not desc:
            st.warning("Please fill all fields")
        else:
            # FIXED: Used ? placeholders for SQLite
            csr.execute(
                """
                INSERT INTO mytodos (todo_added, todo_title, todo_desc, todo_done)
                VALUES (?, ?, ?, ?)
                """,
                (st.session_state.username, title, desc, False)
            )
            conn.commit()
            st.success("Todo added successfully!")
            st.rerun()

    # -------------------------
    # Show Todos
    # -------------------------
    st.header("My Todos")

    # FIXED: Used ? placeholder
    csr.execute(
        """
        SELECT todo_id, todo_title, todo_desc, todo_done
        FROM mytodos
        WHERE todo_added=?
        """,
        (st.session_state.username,)
    )

    todos = csr.fetchall()

    if not todos:
        st.info("No todos found. Add one above!")

    for todo_id, title, desc, done in todos:
        c1, c2, c3, c4 = st.columns([1, 2, 4, 1])

        # Done checkbox
        with c1:
            # We use key=f"..." so every checkbox has a unique ID
            is_done = st.checkbox("Done", value=bool(done), key=f"done_{todo_id}")

            if is_done != bool(done):
                # FIXED: Used ? placeholders
                csr.execute(
                    "UPDATE mytodos SET todo_done=? WHERE todo_id=?",
                    (is_done, todo_id)
                )
                conn.commit()
                st.rerun()

        # Title
        with c2:
            if done:
                st.write(f"~~{title}~~") # Strikethrough if done
            else:
                st.write(f"**{title}**")

        # Description
        with c3:
            st.write(desc)

        # Delete
        with c4:
            if st.button("⛔", key=f"del_{todo_id}"):
                # FIXED: Used ? placeholder
                csr.execute(
                    "DELETE FROM mytodos WHERE todo_id=?",
                    (todo_id,)
                )
                conn.commit()
                st.rerun()

        st.divider()

# ... (Keep all your existing code for "If Logged In" above this) ...

# -------------------------
# Not Logged In (The New Part)
# -------------------------
else:
    # Create two tabs for cleaner UI
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    # --- LOGIN TAB ---
    with tab1:
        st.header("Login")
        login_user = st.text_input("Username", key="login_user")
        login_pass = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            from auth_db import verify_user
            if verify_user(login_user, login_pass):
                st.session_state.authenticated = True
                st.session_state.username = login_user
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password")

    # --- SIGN UP TAB ---
    with tab2:
        st.header("Create Account")
        new_user = st.text_input("New Username", key="new_user")
        new_pass = st.text_input("New Password", type="password", key="new_pass")

        if st.button("Sign Up"):
            from auth_db import create_user
            if new_user and new_pass:
                if create_user(new_user, new_pass):
                    st.success("Account created! You can now login.")
                else:
                    st.error("Username already taken!")
            else:
                st.warning("Please fill both fields")