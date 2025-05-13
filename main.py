import streamlit as st
import pandas as pd
from collections import Counter
import math

# --- Load & preprocess data ---
csv_url = "https://raw.githubusercontent.com/H-AYAH/Teachershortage-app/main/SchoolsSecondary_11.csv"
df = pd.read_csv(csv_url)
df = df.groupby('Institution_Name').agg(list).reset_index()

# --- Subject lesson policy setup ---
subject_lessons = {
    'English': 5,
    'Kiswahili/kenya sign language': 4,
    'Mathematic': 5,
    'Religious Education': 4,
    'Social Studies (including Life Skills Education)': 4,
    'Intergrated Science (including Health Education)': 5,
    'Pre-Technical Studies': 4,
    'Agriculture and Nutrition': 4,
    'Creative Arts and Sports': 5
}

subject_teacher_per_class = {subj: lessons / 27 for subj, lessons in subject_lessons.items()}
TOTAL_WEEKLY_LESSONS_PER_CLASS = sum(subject_lessons.values()) + 1  # +1 for PPI

# --- Subject name mapping ---
subject_mapping = {
    "ENGLISH": "English",
    "KISWAHILI/ KSL": "Kiswahili/kenya sign language",
    "CHRISTIAN RELIGIOUS": "Religious Education",
    "MATHEMATICS": "Mathematic",
    "SOCIAL STUDIES": "Social Studies (including Life Skills Education)",
    "SCIENCE": "Intergrated Science (including Health Education)",
    "INTEGRATED SCIENCE": "Intergrated Science (including Health Education)",
    "PRE-TECHNICAL STUDIES": "Pre-Technical Studies",
    "AGRICULTURE": "Agriculture and Nutrition",
    "CREATIVE ARTS": "Creative Arts and Sports",
    "ARTS": "Creative Arts and Sports",
    "NUTRITION": "Agriculture and Nutrition"
}

def normalize_subjects(subjects):
    normalized = []
    for subj in subjects:
        subj_clean = subj.strip().upper()
        mapped = subject_mapping.get(subj_clean)
        if mapped:
            normalized.append(mapped)
    return normalized

# --- Shortage Calculation ---
def calculate_subject_shortage_full_output(school_row):
    enrollment = school_row['TotalEnrolment'][0] if isinstance(school_row['TotalEnrolment'], list) else 0
    if pd.isna(enrollment): enrollment = 0
    streams = math.ceil(enrollment / 45)

    required_teachers = {
        subject: round(streams * load, 2)
        for subject, load in subject_teacher_per_class.items()
    }

    # Normalize major subjects only
    major_subjects = normalize_subjects(school_row['MajorSubject'])
    major_counts = Counter(major_subjects)
    actual_counts = dict(major_counts)  # Only major subjects count

    shortages = {}
    recommendations = []

    for subject, required in required_teachers.items():
        actual = actual_counts.get(subject, 0)
        shortage = round(required - actual, 2)
        if shortage > 0:
            recommendations.append(f"{int(shortage)} {subject}")
        shortages[subject] = shortage

    return pd.Series({
        "Institution_Name": school_row["Institution_Name"],
        "Enrollment": enrollment,
        "TOD": int(school_row.get("TOD", [0])[0]) if isinstance(school_row.get("TOD"), list) else int(school_row.get("TOD", 0)),
        "PolicyCBE": sum(required_teachers.values()),
        "ActualTeachers": actual_counts,
        "SubjectShortages": shortages,
        "Recommendation": "Recruit " + ", ".join(recommendations) if recommendations else "No recruitment needed",
        "RequiredTeachers": required_teachers
    })

# --- Apply to all schools ---
subject_shortages_df = df.apply(calculate_subject_shortage_full_output, axis=1)
subject_shortages_df = subject_shortages_df.set_index("Institution_Name")

# --- Streamlit UI ---
st.set_page_config(page_title="Teacher Shortage Recommender", layout="wide")
st.title("🎓 Teacher Shortage Recommendation System")

selected_school = st.selectbox("Select a School", subject_shortages_df.index)
school_data = subject_shortages_df.loc[selected_school]

# Summary Metrics
st.subheader(f"📌 Summary for: {selected_school}")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Enrollment", school_data["Enrollment"])
with col2:
    st.metric("Total Teachers on Duty (TOD)", school_data["TOD"])
with col3:
    st.metric("Policy CBE (Expected Total Teachers)", round(school_data["PolicyCBE"], 2))
with col4:
    st.success(school_data["Recommendation"])

# Recommendations Section
st.markdown(f"<div class='recommendation'>📌 <b>Recommendation:</b> {school_data['Recommendation']}</div>", 
            unsafe_allow_html=True)

# Subject-Level Analysis Section
st.subheader("📈 Subject-Specific Staffing")
subject_data = []
actuals = school_data["ActualTeachers"]
required = school_data["RequiredTeachers"]

for subject in subject_lessons:
    subject_data.append({
        "Subject": subject,
        "Actual Teachers": actuals.get(subject, 0),
        "Required Teachers": required.get(subject, 0),
        "Shortage": round(required.get(subject, 0) - actuals.get(subject, 0), 2)
    })

subject_df = pd.DataFrame(subject_data)

st.dataframe(
    subject_df.style.apply(
        lambda x: ['background-color: #ffcccc' if x["Shortage"] > 0 else '' for _ in x],
        axis=1
    ),
    hide_index=True,
    use_container_width=True
)

# Optional: View raw actuals
with st.expander("📊 View Raw Actual Teachers by Subject"):
    st.json(school_data["ActualTeachers"], expanded=False)

# Run app
if __name__ == "__main__":
    pass  # Streamlit runs from `streamlit run main.py`
