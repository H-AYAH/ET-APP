import streamlit as st
import pandas as pd
import math
from collections import Counter

# ======================
# Policy Parameters
# ======================
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

# ======================
# Helper Functions
# ======================
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

# ======================
# Subject Load Config
# ======================
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

# ======================
# Data Processing
# ======================
csv_url = "https://raw.githubusercontent.com/H-AYAH/Teachershortage-app/main/SchoolsSecondary_11.csv"
df = pd.read_csv(csv_url)
df = df.groupby('Institution_Name').agg(list).reset_index()

def calculate_subject_shortage_full_output(school_row):
    # Enrollment processing
    enrollment_list = school_row['TotalEnrolment']
    enrollment = enrollment_list[0][0] if isinstance(enrollment_list[0], list) else enrollment_list[0]
    enrollment = 0 if pd.isna(enrollment) else enrollment

    # Stream calculations
    streams = math.ceil(enrollment / 45)
    required_teachers = {subject: round(streams * load) for subject, load in subject_teacher_per_class.items()}

    # Subject processing
    major_subjects = [item for sublist in school_row['MajorSubject'] for item in (sublist if isinstance(sublist, list) else [sublist])]
    minor_subjects = [item for sublist in school_row['MinorSubject'] for item in (sublist if isinstance(sublist, list) else [sublist])]
    all_subjects = major_subjects + minor_subjects
    actual_counts = dict(Counter(all_subjects))

    # Shortage calculations
    shortages = {}
    recommendations = []
    for subject, required in required_teachers.items():
        actual = actual_counts.get(subject, 0)
        shortage = max(0, round(required - actual))
        if shortage > 0:
            recommendations.append(f"{shortage} {subject}")
        shortages[subject] = shortage

    # TOD processing
    tod_value = school_row.get("TOD", 0)
    if isinstance(tod_value, list):
        tod = int(tod_value[0]) if tod_value else 0
    else:
        tod = int(tod_value) if pd.notna(tod_value) else 0

    return pd.Series({
        "Institution_Name": school_row["Institution_Name"],
        "Enrollment": enrollment,
        "TOD": tod,
        "PolicyCBE": get_policy_cbe(enrollment),
        "LikelyStreams": calculate_likely_streams(get_policy_cbe(enrollment)),
        "ActualTeachers": actual_counts,
        "SubjectShortages": shortages,
        "Recommendation": "Recruit " + ", ".join(recommendations) if recommendations else "No recruitment needed"
    })

subject_shortages_df = df.apply(calculate_subject_shortage_full_output, axis=1)
subject_shortages_df = subject_shortages_df.set_index('Institution_Name')

# ======================
# Dashboard UI
# ======================
st.set_page_config(page_title="Teacher Shortage Recommender", layout="wide", page_icon="🏫")

# Custom CSS Styling
st.markdown("""
<style>
    .main {background-color: #f5f7fb;}
    .header {color: white; padding: 2rem; background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);}
    .metric-box {padding: 1.5rem; border-radius: 10px; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
    .highlight {color: #4b6cb7; font-weight: 700;}
    .recommendation {padding: 1.5rem; background: #e8f0fe; border-radius: 10px; margin-top: 1.5rem;}
</style>
""", unsafe_allow_html=True)

# Header Section
st.markdown('<div class="header"><h1>📚 Teacher Shortage Analysis Dashboard</h1></div>', unsafe_allow_html=True)

# School Selection
selected_school = st.selectbox(
    "🏫 Select School", 
    subject_shortages_df.index,
    help="Choose an institution to view detailed staffing analysis"
)
school_data = subject_shortages_df.loc[selected_school]

# Key Metrics
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f'<div class="metric-box"><h3>📊 Enrollment</h3><p class="highlight">{int(school_data["Enrollment"]):,}</p></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-box"><h3>📌 Policy CBE</h3><p class="highlight">{int(school_data["PolicyCBE"])}</p></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-box"><h3>🏫 Likely Streams</h3><p class="highlight">{int(school_data["LikelyStreams"])}</p></div>', unsafe_allow_html=True)

# Subject Data Display
st.markdown("---")
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("👨🏫 Current Teacher Allocation")
    actual_df = pd.DataFrame.from_dict(school_data['ActualTeachers'], orient='index', columns=['Teachers'])
    st.dataframe(
        actual_df.style.highlight_max(axis=0, color='#c8e6c9'),
        use_container_width=True,
        height=400
    )

with col_right:
    st.subheader("⚠️ Teacher Shortages")
    shortage_df = pd.DataFrame.from_dict(school_data['SubjectShortages'], orient='index', columns=['Shortage'])
    st.dataframe(
        shortage_df.style.applymap(lambda x: 'background-color: #ffcdd2' if x > 0 else ''),
        use_container_width=True,
        height=400
    )

# Recommendation Section
st.markdown("---")
st.markdown(f'<div class="recommendation"><h3>📋 Staffing Recommendation</h3><p>{school_data["Recommendation"]}</p></div>', unsafe_allow_html=True)
