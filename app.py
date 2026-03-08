import streamlit as st
from db.database import initialize_database, get_connection
from ai.client import tutor_explain, generate_quiz
from datetime import datetime, timedelta


#Initialize database (creates table if not exists)
initialize_database()
# -----------------------------
# SECTION: Dashboard Metrics
# -----------------------------

st.markdown("## Dashboard Overview")

conn = get_connection()
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM subjects")
total_subjects = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM subjects WHERE status = 'Completed'")
completed_subjects = cursor.fetchone()[0]

conn.close()

if total_subjects > 0:
    progress_percentage = (completed_subjects / total_subjects) * 100
else:
    progress_percentage = 0

col1, col2, col3 = st.columns(3)

col1.metric("Total Subjects", total_subjects)
col2.metric("Completed Subjects", completed_subjects)
col3.metric("Progress %", f"{progress_percentage:.1f}%")

st.progress(progress_percentage / 100)
# -----------------------------
# SECTION: Total Study Hours
# -----------------------------

conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT SUM(minutes) FROM study_logs")
total_minutes = cursor.fetchone()[0]
conn.close()

if total_minutes:
    total_hours = total_minutes / 60
else:
    total_hours = 0

st.metric("Total Study Hours", f"{total_hours:.2f} hrs")

#Configure page
st.set_page_config(
    page_title="AI Study OS",
    layout="wide"
)

#Title
st.title("AI Study Operating System")

st.subheader("Subject Management")
#----------------------------------------
#SECTION 1: Add New Subject
#---------------------------------------------



st.markdown("### Add New Subject")
subject_name = st.text_input("Subject Name")
semester = st.text_input("Semester")

          
#Button
if st.button("Add Subject"):
    if subject_name:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO subjects (name, semester) VALUES (? , ?)",(subject_name, semester)
        )
        conn.commit()
        conn.close()
        st.success("Subject added successfully.")
    else:
        st.error("Subject name cannot be empty.")



# -----------------------------
# SECTION 2: Show Subjects
# -----------------------------

st.markdown("### All Subjects")

conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT * FROM subjects")
subjects = cursor.fetchall()

if subjects:
    for subject in subjects:
        col1, col2, col3, col4 = st.columns([1, 3, 2, 2])

        with col1:
            st.write(subject[0])  # ID

        with col2:
            st.write(subject[1])  # Name

        with col3:
            new_status = st.selectbox(
                "Status",
                ["Not Started", "In Progress", "Completed"],
                index=["Not Started", "In Progress", "Completed"].index(subject[3]),
                key=f"status_{subject[0]}"
            )

        with col4:
            if st.button("Update", key=f"update_{subject[0]}"):
                cursor.execute(
                    "UPDATE subjects SET status = ? WHERE id = ?",
                    (new_status, subject[0])
                )
                conn.commit()
                st.success("Status updated.")
                st.rerun()
else:
    st.write("No subjects added yet.")

conn.close()

# -----------------------------
# SECTION: Log Study Time
# -----------------------------

st.markdown("## Log Study Time")

conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT id, name FROM subjects")
subject_list = cursor.fetchall()
conn.close()

if subject_list:

    subject_dict = {name: sid for sid, name in subject_list}

    selected_subject = st.selectbox("Select Subject", list(subject_dict.keys()))
    study_minutes = st.number_input("Minutes Studied", min_value=1, step=5)

    if st.button("Log Study Time"):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO study_logs (subject_id, study_date, minutes) VALUES (?, date('now'), ?)",
            (subject_dict[selected_subject], study_minutes)
        )
        conn.commit()
        conn.close()
        st.success("Study time logged successfully.")
        st.rerun()

else:
    st.write("Add subjects first before logging study time.")

# -----------------------------
# SECTION: Per-Subject Analytics
# -----------------------------

st.markdown("## Subject Study Analytics")

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT s.name, 
           IFNULL(SUM(l.minutes), 0) as total_minutes,
           s.status
    FROM subjects s
    LEFT JOIN study_logs l ON s.id = l.subject_id
    GROUP BY s.id
""")

data = cursor.fetchall()
conn.close()

if data:
    import pandas as pd

    df = pd.DataFrame(data, columns=["Subject", "Total Minutes", "Status"])
    df["Total Hours"] = df["Total Minutes"] / 60

    st.dataframe(df[["Subject", "Total Hours", "Status"]])

    st.bar_chart(df.set_index("Subject")["Total Hours"])

else:
    st.write("No data available yet.")


# -----------------------------
# SECTION: Weak Subject Detection
# -----------------------------

st.markdown("## AI Focus Recommendations")

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT s.name, 
           IFNULL(SUM(l.minutes), 0) as total_minutes,
           s.status
    FROM subjects s
    LEFT JOIN study_logs l ON s.id = l.subject_id
    GROUP BY s.id
""")

subjects_data = cursor.fetchall()
conn.close()

weak_subjects = []

for name, minutes, status in subjects_data:
    hours = minutes / 60
    if status != "Completed" and hours < 5:
        weak_subjects.append((name, hours))

if weak_subjects:
    st.warning("Focus Needed On These Subjects:")

    for subject, hours in weak_subjects:
        st.write(f"- {subject} ({hours:.2f} hrs studied)")
else:
    st.success("All subjects are progressing well.")


# -----------------------------
# SECTION: Auto Daily Study Plan
# -----------------------------

st.markdown("## AI Generated Daily Study Plan")

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT s.name, 
           IFNULL(SUM(l.minutes), 0) as total_minutes,
           s.status
    FROM subjects s
    LEFT JOIN study_logs l ON s.id = l.subject_id
    GROUP BY s.id
""")

subjects_data = cursor.fetchall()
conn.close()

priority_list = []

for name, minutes, status in subjects_data:
    hours = minutes / 60
    score = 0
        # Fetch latest mastery score
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT score FROM mastery
        WHERE subject_id = (
            SELECT id FROM subjects WHERE name = ?
        )
        ORDER BY last_updated DESC
        LIMIT 1
    """, (name,))
    mastery_result = cursor.fetchone()
    conn.close()

    mastery_score = mastery_result[0] if mastery_result else None
        # Mastery scoring
    if mastery_score is not None:
        if mastery_score < 50:
            score += 3
        elif mastery_score < 70:
            score += 2
        elif mastery_score < 85:
            score += 1

    # Status scoring
    if status == "Not Started":
        score += 3
    elif status == "In Progress":
        score += 2

    # Effort scoring
    if hours < 3:
        score += 2
    elif hours < 5:
        score += 1

    if status != "Completed":
        priority_list.append((name, score))

# Sort by highest priority
priority_list.sort(key=lambda x: x[1], reverse=True)

if priority_list:

  total_daily_minutes = 180  # You can later make this user adjustable

active_subjects = priority_list

if active_subjects:
    st.info("Recommended 3-Hour Weighted Study Plan")

    total_score = sum(score for _, score in active_subjects)

    for subject, score in active_subjects:
        if total_score > 0:
            allocated = int((score / total_score) * total_daily_minutes)
        else:
            allocated = 0

        if allocated > 0:
            st.write(f"- {subject}: {allocated} minutes (Priority Score: {score})")

else:
    st.success("All subjects completed. No study required today.")

st.markdown("## AI Tutor")

topic = st.text_input("Enter a topic (e.g., Gradient Descent, Bayes Rule, Linear Regression)")
context = st.text_area("Optional context (what you studied / where you’re stuck)", height=120)

if st.button("Explain with AI"):
    if topic.strip():
        with st.spinner("Generating explanation..."):
            answer = tutor_explain(topic=topic.strip(), context=context.strip())
        st.markdown(answer)
    else:
        st.error("Enter a topic first.")

st.markdown("## AI Quiz Generator")

quiz_topic = st.text_input("Quiz topic", key="quiz_topic")
difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])

if st.button("Generate Quiz"):
    if quiz_topic.strip():
        with st.spinner("Generating quiz..."):
            quiz = generate_quiz(topic=quiz_topic.strip(), difficulty=difficulty)
        st.markdown(quiz)
    else:
        st.error("Enter a quiz topic first.")
        

# -----------------------------
# SECTION: Mastery Update
# -----------------------------

st.markdown("## Update Mastery Score")

conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT id, name FROM subjects")
subjects = cursor.fetchall()
conn.close()

if subjects:
    subject_map = {name: sid for sid, name in subjects}
    selected = st.selectbox("Select Subject for Mastery Update", list(subject_map.keys()))
    score = st.slider("Quiz Score (%)", 0, 100, 50)

    if st.button("Save Mastery Score"):

    # Determine review interval based on mastery score
        if score < 50:
            interval = 1
        elif score < 70:
            interval = 3
        elif score < 85:
            interval = 7
        else:
            interval = 14

        next_review_date = (datetime.now() + timedelta(days=interval)).strftime("%Y-%m-%d")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO mastery (subject_id, score, last_updated, next_review)
            VALUES (?, ?, datetime('now'), ?)
        """, (subject_map[selected], score, next_review_date))

        conn.commit()
        conn.close()

        st.success("Mastery score saved and review scheduled.")
        st.rerun()

# -----------------------------
# SECTION: Review Due Today
# -----------------------------

st.markdown("## Subjects Due for Review")

today = datetime.now().strftime("%Y-%m-%d")

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT s.name, m.next_review
    FROM mastery m
    JOIN subjects s ON s.id = m.subject_id
    WHERE m.next_review <= ?
""", (today,))

due_subjects = cursor.fetchall()
conn.close()

if due_subjects:
    for name, review_date in due_subjects:
        st.warning(f"{name} is due for review (Scheduled: {review_date})")
else:
    st.success("No reviews due today.")


# -----------------------------
# SECTION: Review Overview
# -----------------------------

st.markdown("## Review Schedule Overview")

from datetime import datetime
import pandas as pd

today = datetime.now().strftime("%Y-%m-%d")

conn = get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT s.name,
           m.score,
           m.next_review
    FROM mastery m
    JOIN subjects s ON s.id = m.subject_id
    WHERE m.id IN (
        SELECT MAX(id)
        FROM mastery
        GROUP BY subject_id
    )
""")

review_data = cursor.fetchall()
conn.close()

if review_data:

    df = pd.DataFrame(review_data, columns=["Subject", "Mastery Score", "Next Review"])

    # Determine status
    def review_status(row):
        if row["Next Review"] <= today:
            return "Due"
        else:
            return "Upcoming"

    df["Review Status"] = df.apply(review_status, axis=1)

    st.dataframe(df)

else:
    st.write("No mastery records available yet.")