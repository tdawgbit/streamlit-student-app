import re
import streamlit as st
import psycopg2
import traceback

st.set_page_config(page_title="Add Student", page_icon="👤")

@st.cache_resource
def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])

st.title("👤 Add a New Student")

EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

with st.form("add_student_form"):
    name = st.text_input("Student Name").strip()
    email = st.text_input("Student Email").strip()
    submitted = st.form_submit_button("Add Student")

    if submitted:
        if not name or not email:
            st.warning("⚠️ Please fill in both fields.")
        elif not re.match(EMAIL_PATTERN, email):
            st.warning("⚠️ Please enter a valid email address (e.g., student@example.com).")
        else:
            conn = None
            cur = None
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO students10 (name, email) VALUES (%s, %s);",
                    (name, email)
                )
                conn.commit()
                st.success(f"✅ Student '{name}' added successfully!")
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                st.error("⚠️ A student with that email already exists.")
            except Exception as e:
                st.error(f"Error: {e}")
                st.code(traceback.format_exc())
            finally:
                if cur:
                    cur.close()

st.markdown("---")
st.subheader("Current Students")

conn = None
cur = None
try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email FROM students10 ORDER BY name;")
    students = cur.fetchall()

    if students:
        st.table([{"ID": s[0], "Name": s[1], "Email": s[2]} for s in students])
    else:
        st.info("No students yet.")
except Exception as e:
    st.error(f"Error: {e}")
    st.code(traceback.format_exc())
finally:
    if cur:
        cur.close()
