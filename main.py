from collections import Counter
import streamlit as st
import pandas as pd
import numpy as np
import math

# [Keep all your existing data processing and calculation functions unchanged here...]

# ====================== ENHANCED UI COMPONENTS ======================
st.set_page_config(page_title="Teacher Shortage Dashboard", layout="wide", page_icon="🏫")

# Custom CSS Styling with Navy Blue, Gold, and White Theme
st.markdown("""
<style>
    :root {
        --navy: #000080;
        --gold: #FFD700;
        --white: #FFFFFF;
    }
    .main {background-color: var(--white);}
    .header {color: var(--white); padding: 2rem; background: var(--navy); 
             border-radius: 10px; margin-bottom: 1.5rem;}
    .metric-box {padding: 1rem; border-radius: 8px; background: var(--white);
                 border: 2px solid var(--navy); margin: 0.5rem;}
    .metric-title {color: var(--navy); font-weight: 700; font-size: 1.1rem;}
    .metric-value {color: var(--gold); font-weight: 800; font-size: 1.8rem;}
    .stDataFrame {border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}
    .recommendation {padding: 1.5rem; background: rgba(0,0,128,0.1); 
                     border-left: 4px solid var(--gold); border-radius: 8px;}
    th {background-color: var(--navy) !important; color: var(--white) !important;}
</style>
""", unsafe_allow_html=True)

# Header Section
st.markdown(f'''
    <div class="header">
        <h1 style='color: var(--gold); margin-bottom: 0;'>Teacher Shortage Dashboard</h1>
        <p style='color: var(--white); margin-top: 0.5rem;'>Comprehensive Staffing Analysis for Secondary Schools</p>
    </div>
''', unsafe_allow_html=True)

# School Selection
selected_school = st.selectbox(
    "🏫 Select School", 
    subject_shortages_df.index,
    help="Choose an institution to view detailed staffing analysis"
)
school_data = subject_shortages_df.loc[selected_school]

# Key Metrics
st.markdown("---")
cols = st.columns(3)
metric_config = [
    ("📊 Enrollment", "Enrollment"),
    ("📌 Policy CBE", "PolicyCBE"),
    ("🏫 Likely Streams", "LikelyStreams")
]

for col, (title, key) in zip(cols, metric_config):
    with col:
        value = int(school_data[key])
        st.markdown(f'''
            <div class="metric-box">
                <div class="metric-title">{title}</div>
                <div class="metric-value">{value:,}</div>
            </div>
        ''', unsafe_allow_html=True)

# ====================== NEW SUBJECT TABLE ======================
st.markdown("---")
st.subheader("📚 Subject-Specific Teacher Analysis")

# Calculate required teachers for table
streams = school_data["LikelyStreams"]
required_teachers = {
    subject: math.ceil(streams * load)
    for subject, load in subject_teacher_per_class.items()
}

# Create combined dataframe
subject_table = pd.DataFrame({
    'Subject': list(subject_lessons.keys()),
    'Actual Teachers': [school_data['ActualTeachers'].get(subj, 0) for subj in subject_lessons],
    'Required Teachers': [required_teachers[subj] for subj in subject_lessons],
    'Shortage': [school_data['SubjectShortages'][subj] for subj in subject_lessons]
})

# Style the dataframe
def style_shortage(val):
    color = 'gold' if val == 0 else 'red' if val > 0 else 'green'
    return f'color: {color}; font-weight: bold'

styled_table = subject_table.style.map(
    style_shortage, subset=['Shortage']
).set_properties(**{
    'background-color': 'white',
    'border': '1px solid navy'
}).hide_index()

# Display the styled table
st.dataframe(
    styled_table,
    use_container_width=True,
    height=600
)

# Recommendation Section
st.markdown("---")
st.markdown(f'''
    <div class="recommendation">
        <h3 style='color: var(--navy); margin-bottom: 0.5rem;'>📋 Staffing Recommendation</h3>
        <p style='font-size: 1.1rem;'>{school_data["Recommendation"]}</p>
    </div>
''', unsafe_allow_html=True)
