import streamlit as st
import psycopg2

st.set_page_config(page_title="Add Student", page_icon="👤")

def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])

st.title("👤 Add a New Student")

with st.form("add_student_form"):
    name = st.text_input("Student Name")
    email = st.text_input("Student Email")
    submitted = st.form_submit_button("Add Student")

    if submitted:
        if name and email:
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO students10 (name, email) VALUES (%s, %s);",
                    (name, email)
                )
                conn.commit()
                cur.close()
                conn.close()
                st.success(f"✅ Student '{name}' added successfully!")
            except psycopg2.errors.UniqueViolation:
                st.error("⚠️ A student with that email already exists.")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.warning("Please fill in both fields.")

st.markdown("---")
st.subheader("Current Students")

try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email FROM students10 ORDER BY name;")
    students = cur.fetchall()
    cur.close()
    conn.close()

    if students:
        st.table([{"ID": s[0], "Name": s[1], "Email": s[2]} for s in students])
    else:
        st.info("No students yet.")
except Exception as e:
    st.error(f"Error: {e}")