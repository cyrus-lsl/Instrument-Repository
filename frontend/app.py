import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add parent directory
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from backend.outcome_repo_agent import MeasurementInstrumentAgent
import os


@st.cache_resource
def load_agent(path_or_buffer):
    """Load and cache the MeasurementInstrumentAgent.

    Accepts either a filesystem path (str/Path) or a file-like buffer
    returned by Streamlit's file_uploader.
    """
    agent = MeasurementInstrumentAgent(path_or_buffer, sheet_name='Measurement Instruments')
    return agent

st.set_page_config(page_title='Outcome Repo Agent', layout='wide')
st.title('Outcome Repository — Measurement Instrument Assistant')

if 'last_response' not in st.session_state:
    st.session_state['last_response'] = ''

excel_path = Path(__file__).resolve().parents[1] / "measurement_instruments.xlsx"

# Load agent
agent = None
try:
    agent = load_agent(str(excel_path))
except FileNotFoundError:
    st.error(f"Required data file not found at {excel_path}. Please add `measurement_instruments.xlsx` to the repo root.")
except Exception as e:
    st.error(f"Failed to load measurement instruments file: {e}")
# Page selector in the sidebar
page = st.sidebar.selectbox("Page", ["Ask", "Browse Instruments"])

if page == "Ask":
    # Chat interface
    st.header("Ask about measurement instruments")
    st.markdown("""
    Type your query about measurement instruments. Examples:
    - Search by purpose: "assessment tools for depression"
    - Search by group: "instruments for elderly patients"
    - Search by properties: "quick screening tools" or "validated in Hong Kong"
    """)

    # Chat input
    query = st.text_input('Enter your enquiry', key='user_input')

    # Send button
    if st.button('Send', key='send_button') and query.strip():
        if not agent:
            st.session_state['last_response'] = "Please upload or provide a valid Excel file before querying."
        else:
            results = agent.process_query(query)
            response = agent.format_response(results)
            st.session_state['last_response'] = response

    # Show response
    st.header("Agent Response")
    if st.session_state.get('last_response'):
        st.markdown(st.session_state['last_response'])
    else:
        st.info('No responses yet. Type a question and press Send.')

else:
    # Browse Instruments page
    st.header("Browse all instruments")
    if not agent:
        st.info('No data loaded. Add `measurement_instruments.xlsx` to the repo root so browsing is available.')
    else:
        df_display = agent.df.copy()
        if 'No. of Questions / Statements' in df_display.columns:
            df_display['No. of Questions / Statements'] = df_display['No. of Questions / Statements'].astype(str)
        for c in df_display.select_dtypes(include=['object']).columns:
            df_display[c] = df_display[c].astype(str)

        if not df_display.empty:
            last_row = df_display.iloc[-1].astype(str)
            if (last_row == 'combined_text').any():
                df_display = df_display.iloc[:-1]

        st.dataframe(df_display)

        st.subheader('Quick lookup')
        name = st.text_input('Get details for instrument', '')
        if st.button('Get Details') and name.strip():
            details = agent.get_instrument_details(name)
            if details:
                if isinstance(details, dict) and 'combined_text' in details:
                    details.pop('combined_text')
                try:
                    df_details = pd.DataFrame.from_dict(details, orient='index', columns=['Value'])
                    df_details.index.name = 'Field'
                    st.table(df_details)
                except Exception:
                    st.json(details)
            else:
                st.info('No instrument matched that name')
