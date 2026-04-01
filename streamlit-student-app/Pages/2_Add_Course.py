import streamlit as st
import psycopg2
import traceback

st.set_page_config(page_title="Add Course", page_icon="📚")

@st.cache_resource
def get_connection():
    return psycopg2.connect(st.secrets["DB_URL"])

st.title("📚 Add a New Course")

with st.form("add_course_form"):
    course_name = st.text_input("Course Name").strip()
    submitted = st.form_submit_button("Add Course")

    if submitted:
        if not course_name:
            st.warning("⚠️ Please enter a course name.")
        else:
            conn = None
            cur = None
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO courses10 (course_name) VALUES (%s);",
                    (course_name,)
                )
                conn.commit()
                st.success(f"✅ Course '{course_name}' added successfully!")
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                st.error("⚠️ A course with that name already exists.")
            except Exception as e:
                st.error(f"Error: {e}")
                st.code(traceback.format_exc())
            finally:
                if cur:
                    cur.close()

st.markdown("---")
st.subheader("Current Courses")

conn = None
cur = None
try:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, course_name FROM courses10 ORDER BY course_name;")
    courses = cur.fetchall()

    if courses:
        st.table([{"ID": c[0], "Course Name": c[1]} for c in courses])
    else:
        st.info("No courses yet.")
except Exception as e:
    st.error(f"Error: {e}")
    st.code(traceback.format_exc())
finally:
    if cur:
        cur.close()