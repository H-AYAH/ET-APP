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
    minor_subjects = [item for sublist in school_row['MinorSubject
