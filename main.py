import streamlit as st
import pandas as pd
import math
from collections import Counter

# -----------------------------
# Policy Provision Parameters
# -----------------------------
policy_brackets = [
    {'streams': 1, 'enr_min': 0, 'enr_max': 180, 'cbe': 9},
    {'streams': 2, 'enr_min': 181, 'enr_max': 360, 'cbe': 19},
    {'streams': 3, 'enr_min': 361, 'enr_max': 540, 'cbe': 28},
    {'streams': 4, 'enr_min': 541, 'enr_max': 720, 'cbe': 38},
    {'streams': 5, 'enr_min': 721, 'enr_max': 900, 'cbe': 47},
    {'streams': 6, 'enr_min': 901, 'enr_max': 1080, 'cbe': 55},
    {'streams': 7, 'enr_min': 1081, 'enr_max': 1260, 'cbe': 63},
    {'streams': 8, 'enr_min': 1261, 'enr_max': 1440, 'cbe': 68},
    {'streams': 9, 'enr_min': 1441, 'enr_max': 1620, 'cbe': 76},
    {'streams': 10, 'enr_min': 1621, 'enr_max': 1800, 'cbe': 85},
    {'streams': 11, 'enr_min': 1801, 'enr_max': 1980, 'cbe': 93},
    {'streams': 12, 'enr_min': 1981, 'enr_max': 2160, 'cbe': 101},
]

def get_policy_cbe(enrollment):
    for bracket in policy_brackets:
        if bracket['enr_min'] <= enrollment <= bracket['enr_max']:
            return bracket['cbe']
    return 93 + 8 * (math.ceil(enrollment / 180) - 11)

def calculate_likely_streams(cbe_actual):
    for bracket in policy_brackets:
        if cbe_actual <= bracket['cbe']:
            return bracket['streams']
    return math.ceil((cbe_actual - 93) / 8) + 11

# -----------------------------
# Subject Load Per Week
# -----------------------------
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

TOTAL_WEEKLY_LESSONS_PER_CLASS = sum(subject_lessons.values()) + 1
subject_teacher_per_class = {subject: round(lessons / 27, 2) for subject, lessons in subject_lessons.items()}

# -----------------------------
# Load Data
# -----------------------------
CSV_URL = 'https://raw.githubusercontent.com/yourusername/yourrepo/main/teacher_data.csv'
df = pd.read_csv(CSV_URL)
df = df.groupby('Institution_Name').agg(list).reset_index()

# -----------------------------
# Subject Shortage Calculation
# -----------------------------
def calculate_subject_shortage_full_output(school_row):
    enrollment_list = school_row['TotalEnrolment']
    enrollment = enrollment_list[0][0] if isinstance(enrollment_list[0], list) else enrollment_list[0]
    enrollment = 0 if pd.isna(enrollment) else enrollment

    streams = math.ceil(enrollment / 45)
    required_teachers = {subject: round(streams * load) for subject, load in subject_teacher_per_class.items()}

    major_subjects = school_row['MajorSubject']
    minor_subjects = school_row['MinorSubject']

    major_subjects = [item for sublist in major_subjects for item in (sublist if isinstance(sublist, list) else [sublist])]
    minor_subjects = [item for sublist in minor_subjects for item in (sublist if isinstance(sublist, list) else [sublist])]

    all_subjects = major_subjects + minor_subjects
    actual_counts = dict(Counter(all_subjects))

    shortages = {}
    recommendations = []

    for subject, required in required_teachers.items():
        actual = actual_counts.get(subject, 0)
        shortage = round(required - actual)
        if shortage > 0:
            recommendations.append(f"{int(shortage)} {subject}")
        shortages[subject] = shortage

    output = {
        "Institution_Name": school_row["Institution_Name"],
        "Enrollment": enrollment,
        "TOD": int(school_row.get("TOD", [0])[0]) if isinstance(school_row.get("TOD"), list) else int(school_row.get("TOD", 0)),
        "PolicyCBE": get_policy_cbe(enrollment),
        "LikelyStreams": calculate_likely_streams(get_policy_cbe(enrollment)),
        "ActualTeachers": actual_counts,
        "SubjectShortages": shortages,
        "Recommendation": "Recruit " + ", ".join(recommendations) if recommendations else "No recruitment needed"
    }

    return pd.Series(output)

subject_shortages_df = df.apply(calculate_subject_shortage_full_output, axis=1)
subject_shortages_df = subject_shortages_df.set_index('Institution_Name')

# -----------------------------
# Streamlit Dashboard
# -----------------------------
st.set_page_config(page_title="Teacher Shortage Recommender", layout="wide")
st.title("📚 Teacher Shortage Recommender Dashboard")

school_selected = st.selectbox("Select a School", subject_shortages_df.index)
school_data = subject_shortages_df.loc[school_selected]

col1, col2, col3 = st.columns(3)
col1.metric("📊 Enrollment", int(school_data['Enrollment']))
col2.metric("📌 Policy CBE", int(school_data['PolicyCBE']))
col3.metric("🏫 Likely Streams", int(school_data['LikelyStreams']))

st.subheader("👨‍🏫 Subject-Specific Actual Teachers")
st.dataframe(pd.DataFrame.from_dict(school_data['ActualTeachers'], orient='index', columns=['Actual Teachers']))

st.subheader("⚠️ Subject Shortages")
st.dataframe(pd.DataFrame.from_dict(school_data['SubjectShortages'], orient='index', columns=['Shortage']))

st.subheader("📋 Recommendation")
st.success(school_data['Recommendation'])
