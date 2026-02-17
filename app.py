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

# -------------------------
# Not Logged In
# -------------------------
else:
    st.warning("Please login first")
    
    # I added this button so you can test the app without building a full login page yet
    if st.button("Simulate Login as 'Rahul'"):
        st.session_state.authenticated = True
        st.session_state.username = "Rahul"
        st.rerun()
        
    st.markdown("[Go to Login Page](./login)")