

import streamlit as st
import pandas as pd
import math
from collections import Counter

# --- Constants and Setup ---
CSV_URL = "https://raw.githubusercontent.com/H-AYAH/Teachershortage-app/main/SchoolsSecondary_11.csv"

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

TOTAL_WEEKLY_LESSONS_PER_CLASS = sum(subject_lessons.values()) + 1  # +1 for PPI
subject_teacher_per_class = {subject: lessons / 27 for subject, lessons in subject_lessons.items()}


# --- Utility Functions ---
def calculate_admin_count(num_classes):
    if num_classes <= 7:
        return {'DeputyPrincipals': 1, 'SeniorMasters': 1}
    elif 8 <= num_classes <= 11:
        return {'DeputyPrincipals': 1, 'SeniorMasters': 2}
    elif 12 <= num_classes <= 15:
        return {'DeputyPrincipals': 1, 'SeniorMasters': 4}
    elif 16 <= num_classes <= 23:
        return {'DeputyPrincipals': 2, 'SeniorMasters': 5}
    elif 24 <= num_classes <= 31:
        return {'DeputyPrincipals': 2, 'SeniorMasters': 6}
    elif 32 <= num_classes <= 43:
        return {'DeputyPrincipals': 2, 'SeniorMasters': 7}
    elif 44 <= num_classes <= 47:
        return {'DeputyPrincipals': 2, 'SeniorMasters': 8}
    else:
        return {'DeputyPrincipals': 2, 'SeniorMasters': 9}


def calculate_subject_shortage_full_output(school_row):
    enrollment_list = school_row['TotalEnrolment']
    if isinstance(enrollment_list, list):
        if isinstance(enrollment_list[0], list):
            enrollment = enrollment_list[0][0]
        else:
            enrollment = enrollment_list[0]
    else:
        enrollment = enrollment_list

    if pd.isna(enrollment):
        enrollment = 0

    streams = math.ceil(enrollment / 45)

    required_teachers = {
        subject: round(streams * load, 2)
        for subject, load in subject_teacher_per_class.items()
    }

    major_subjects = school_row['MajorSubject']
    minor_subjects = school_row['MinorSubject']

    if major_subjects and isinstance(major_subjects[0], list):
        major_subjects = [item for sublist in major_subjects for item in sublist]
    if minor_subjects and isinstance(minor_subjects[0], list):
        minor_subjects = [item for sublist in minor_subjects for item in sublist]

    major_counts = Counter(major_subjects)
    minor_counts = Counter(minor_subjects)
    actual_counts = dict(major_counts + minor_counts)

    shortages = {}
    recommendations = []

    for subject, required in required_teachers.items():
        actual = actual_counts.get(subject, 0)
        shortage = round(required - actual, 2)
        if shortage > 0:
            recommendations.append(f"{int(shortage)} {subject}")
        shortages[subject] = shortage

    output = {
        "TOD": int(school_row.get("TOD", [0])[0]) if isinstance(school_row.get("TOD"), list) else int(school_row.get("TOD", 0)),
        "PolicyCBE": sum(required_teachers.values()),
        "ActualTeachers": actual_counts,
        "SubjectShortages": shortages,
        "Recommendation": "Recruit " + ", ".join(recommendations) if recommendations else "No recruitment needed",
        "RequiredTeachers": required_teachers
    }

    return output


# --- Main App Logic ---
def main():
    st.set_page_config(page_title="Teacher Shortage Recommender", layout="wide")
    st.title("📚 Teacher Shortage Recommender System")
    st.write("Select an institution to view the current teaching status and recommendations based on the CBC policy.")

    @st.cache_data
    def load_data():
        df = pd.read_csv(CSV_URL)
        df = df.groupby('Institution_Name').agg(list).reset_index()
        return df

    df = load_data()
    institutions = df['Institution_Name'].tolist()
    selected_school = st.selectbox("🏫 Select Institution", institutions)
    school_row = df[df['Institution_Name'] == selected_school].iloc[0]
    school_data = calculate_subject_shortage_full_output(school_row)

    st.subheader(f"📌 Summary for: {selected_school}")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Teachers on Duty (TOD)", school_data["TOD"])
        st.metric("Policy CBE (Expected Total Teachers)", round(school_data["PolicyCBE"], 2))
    with col2:
        st.success(school_data["Recommendation"])

    # ✅ Styled Recommendation Box
    st.markdown(
        f"<div class='recommendation'>📌 <b>Recommendation:</b> {school_data['Recommendation']}</div>",
        unsafe_allow_html=True
    )

    # ✅ Subject-Specific Staffing Section
    st.subheader("📈 Subject-Specific Staffing")

    # Build subject-level DataFrame
    subject_data = []
    for subject, required in school_data["RequiredTeachers"].items():
        actual = school_data["ActualTeachers"].get(subject, 0)
        shortage = round(required - actual, 2)
        subject_data.append({
            "Subject": subject,
            "Actual Teachers": actual,
            "Required Teachers": required,
            "Shortage": shortage
        })

    subject_df = pd.DataFrame(subject_data)

    # Display with conditional formatting
    st.dataframe(
        subject_df.style.apply(
            lambda row: ['background-color: #ffcccc' if row['Shortage'] > 0 else '' for _ in row],
            axis=1
        ),
        hide_index=True,
        use_container_width=True
    )

    # Expanders
    with st.expander("📊 Actual Teachers per Subject"):
        st.json(school_data["ActualTeachers"])
    with st.expander("📉 Subject-Specific Shortages"):
        st.json(school_data["SubjectShortages"])


# ✅ Streamlit Entry Point
if __name__ == "__main__":
    main()
