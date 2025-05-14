import streamlit as st
import pandas as pd

# Custom CSS styling
st.markdown("""
    <style>
    .main {background-color: #f9f9f9;}
    .header {padding: 20px; background: #00467F; color: white; border-radius: 10px;}
    .metric-box {padding: 15px; background: white; border-radius: 10px; margin: 10px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1);}
    .recommendation {background: #e8f4ff; padding: 15px; border-left: 4px solid #00467F; margin: 20px 0;}
    .shortage {color: #ff4444; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and return processed data - REPLACE WITH YOUR ACTUAL DATA SOURCE"""
    data = pd.DataFrame({
        'School': ['City High School', 'Town Academy', 'Rural Prep', 'A.C.K Igangara Secondary School'],
        'TOD': ['Urban 1', 'Suburban 2', 'Rural 3', 'Rural 11'],
        'Enrollment': [1500, 800, 1200, 187],
        'PolicyCBE': ['Implemented', 'Partial', 'Not Implemented', 'Implemented'],
        'Math_Actual': [15, 8, 12, 5],
        'Math_Required': [20, 10, 15, 8],
        'Science_Actual': [10, 6, 9, 3],
        'Science_Required': [12, 8, 10, 6],
        'Recommendation': [
            'Urgent need for math teachers and classroom space',
            'Implement teacher sharing program with neighboring schools',
            'Prioritize hiring science specialists',
            'Recruit math and science teachers for immediate deployment'
        ]
    })
    return data

def safe_tod_conversion(tod_value):
    """Safely extract numeric district number from TOD field"""
    try:
        if pd.isna(tod_value):
            return 0
        parts = str(tod_value).split()
        return int(parts[-1]) if len(parts) > 1 else 0
    except (ValueError, IndexError):
        return 0

def calculate_subject_shortage_full_output(row):
    """Calculate shortage metrics for each school"""
    try:
        tod_number = safe_tod_conversion(row['TOD'])
        math_shortage = row['Math_Required'] - row['Math_Actual']
        science_shortage = row['Science_Required'] - row['Science_Actual']
        return {
            'School': row['School'],
            'TOD': row['TOD'],
            'TOD_Number': tod_number,
            'Enrollment': row['Enrollment'],
            'PolicyCBE': row['PolicyCBE'],
            'Math_Actual': row['Math_Actual'],
            'Math_Required': row['Math_Required'],
            'Math_Shortage': max(math_shortage, 0),
            'Science_Actual': row['Science_Actual'],
            'Science_Required': row['Science_Required'],
            'Science_Shortage': max(science_shortage, 0),
            'Recommendation': row['Recommendation']
        }
    except KeyError as e:
        st.error(f"Missing column in data: {e}")
        return {}
    except Exception as e:
        st.error(f"Error processing row: {e}")
        return {}

def main():
    st.markdown("<div class='header'><h1>🏫 Teacher Shortage Recommender Dashboard</h1></div>", unsafe_allow_html=True)

    try:
        df = load_data()
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return

    required_columns = ['School', 'TOD', 'Enrollment', 'Math_Actual', 'Math_Required']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        st.write("Available columns:", df.columns.tolist())
        return

    try:
        shortages_df = df.apply(calculate_subject_shortage_full_output, axis=1)
        shortages_df = pd.DataFrame(list(shortages_df))
    except Exception as e:
        st.error(f"Data processing failed: {e}")
        return

    selected_school = st.selectbox(
        "📚 Select School", 
        options=df['School'].unique(),
        help="Choose a school to view detailed staffing analysis"
    )

    school_data = shortages_df[shortages_df['School'] == selected_school].iloc[0]

    # School Overview
    st.subheader("📊 School Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
            <div class='metric-box'>
                🧑🎓 <b>Enrollment</b><br>
                {school_data['Enrollment']}
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class='metric-box'>
                📍 <b>T.O.D</b><br>
                {school_data['TOD']}
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class='metric-box'>
                📜 <b>Policy CBE</b><br>
                {school_data['PolicyCBE']}
            </div>
        """, unsafe_allow_html=True)

    # Subject Shortages Table
    st.subheader("📚 Subject-Specific Staffing")
    subject_df = pd.DataFrame({
        'Subject': ['Math', 'Science'],
        'Current Teachers': [
            school_data['Math_Actual'],
            school_data['Science_Actual']
        ],
        'Required Teachers': [
            school_data['Math_Required'],
            school_data['Science_Required']
        ],
        'Shortage': [
            school_data['Math_Shortage'],
            school_data['Science_Shortage']
        ]
    })

    st.dataframe(
        subject_df.style.applymap(
            lambda v: 'background-color: #ffe6e6' if isinstance(v, (int, float)) and v > 0 else '',
            subset=["Shortage"]
        ),
        use_container_width=True,
        hide_index=True
    )

    # Recommendation
    st.markdown(f"""
        <div class='recommendation'>
            📌 <b>Staffing Recommendation:</b><br>
            {school_data['Recommendation']}
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
