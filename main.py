import streamlit as st
import pandas as pd
import math
from collections import Counter

# --- Custom CSS ---
st.markdown("""
    <style>
    .main {background-color: #f9f9f9;}
    .header {padding: 20px; background: #00467F; color: white; border-radius: 10px;}
    .metric-box {padding: 15px; background: white; border-radius: 10px; margin: 10px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1);}
    .recommendation {background: #e8f4ff; padding: 15px; border-left: 4px solid #00467F; margin: 20px 0;}
    .shortage {color: #ff4444; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

# --- Constants ---
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

# --- Load Data ---
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/H-AYAH/Teachershortage-app/main/SchoolsSecondary_11.csv"
    df = pd.read_csv(url)
    return df.groupby('Institution_Name').agg(list).reset_index()

def normalize_subjects(subjects):
    normalized = []
    for subj in subjects:
        subj_clean = subj.strip().upper()
        mapped = subject_mapping.get(subj_clean)
        if mapped:
            normalized.append(mapped)
    return normalized

def get_first_valid_value(val):
    if isinstance(val, list):
        for v in val:
            if pd.notna(v):
                return v
    elif pd.notna(val):
        return val
    return 0

def calculate_school_metrics(row):
    enrollment = int(get_first_valid_value(row['TotalEnrolment']))
    tod = get_first_valid_value(row['TOD'])
    tod_str = str(tod)
    policy_cbe = 0

    # Streams
    streams = math.ceil(enrollment / 45)
    
    # Required teachers by subject
    required = {s: round(streams * l, 2) for s, l in subject_teacher_per_class.items()}
    policy_cbe = sum(required.values())
    
    # Actual teachers from major subject only
    major_subjects = normalize_subjects(row['MajorSubject'])
    actual_counter = Counter(major_subjects)
    
    # Subject shortages
    shortages = {}
    recommendations = []
    for subj in subject_lessons:
        req = required.get(subj, 0)
        act = actual_counter.get(subj, 0)
        shortage = round(req - act, 2)
        shortages[subj] = shortage
        if shortage > 0:
            recommendations.append(f"{int(shortage)} {subj}")

    return pd.Series({
        "Institution_Name": row["Institution_Name"],
        "TOD": tod_str,
        "Enrollment": enrollment,
        "PolicyCBE": round(policy_cbe, 2),
        "ActualTeachers": actual_counter,
        "RequiredTeachers": required,
        "Shortages": shortages,
        "Recommendation": "Recruit " + ", ".join(recommendations) if recommendations else "No recruitment needed"
    })

# --- Main App ---
def main():
    st.markdown("<div class='header'><h1>🏫 Teacher Shortage Recommender Dashboard</h1></div>", unsafe_allow_html=True)
    
    try:
        df = load_data()
        full_df = df.apply(calculate_school_metrics, axis=1)
        full_df = full_df.set_index("Institution_Name")
    except Exception as e:
        st.error(f"Data loading or processing failed: {e}")
        return

    selected_school = st.selectbox("📚 Select School", full_df.index)

    school = full_df.loc[selected_school]
    actuals = school["ActualTeachers"]
    required = school["RequiredTeachers"]
    shortages = school["Shortages"]

    # --- Metrics ---
    st.subheader("📊 School Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='metric-box'>🧑🎓 <b>Enrollment</b><br>{school['Enrollment']}</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-box'>📍 <b>D.O.D</b><br>{school['TOD']}</div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-box'>📜 <b>Policy CBE</b><br>{school['PolicyCBE']}</div>", unsafe_allow_html=True)

    # --- Subject Table ---
    st.subheader("📚 Subject-Specific Staffing")
    subject_df = pd.DataFrame([
        {
            "Subject": subj,
            "Actual": actuals.get(subj, 0),
            "Required": required.get(subj, 0),
            "Shortage": shortages.get(subj, 0)
        }
        for subj in subject_lessons
    ])

    st.dataframe(
        subject_df.style.apply(
            lambda x: ['background-color: #ffe6e6' if v > 0 else '' for v in x['Shortage']],
            axis=0
        ),
        use_container_width=True,
        hide_index=True
    )

    # --- Recommendation ---
    st.markdown(f"""
        <div class='recommendation'>
            📌 <b>Recommendation:</b><br>
            {school['Recommendation']}
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
