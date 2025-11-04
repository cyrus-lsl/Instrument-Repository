import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to Python
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

# Initialize session state for chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Load the repo-bundled Excel file by default (no uploader). This expects
# `measurement_instruments.xlsx` to live at the repository root.
excel_path = Path(__file__).resolve().parents[1] / "measurement_instruments.xlsx"

agent = None
try:
    agent = load_agent(str(excel_path))
except FileNotFoundError:
    st.error(f"Required data file not found at {excel_path}. Please add `measurement_instruments.xlsx` to the repo root.")
except Exception as e:
    st.error(f"Failed to load measurement instruments file: {e}")

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
    # Add user message to chat
    st.session_state.chat_history.append({"role": "user", "content": query})
    
    # Get agent response
    if not agent:
        st.session_state.chat_history.append({"role": "assistant", "content": "Please upload or provide a valid Excel file before querying."})
    else:
        results = agent.process_query(query)
        response = agent.format_response(results)
        # Add assistant response
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        

# Collapsible data explorer
with st.expander("Browse all instruments"):
    df_display = agent.df.copy()
    if 'No. of Questions / Statements' in df_display.columns:
        df_display['No. of Questions / Statements'] = df_display['No. of Questions / Statements'].astype(str)
    for c in df_display.select_dtypes(include=['object']).columns:
        df_display[c] = df_display[c].astype(str)

    st.dataframe(df_display)
    
    st.subheader('Quick lookup')
    name = st.text_input('Get details for instrument (name contains)', '')
    if st.button('Get Details') and name.strip():
        details = agent.get_instrument_details(name)
        if details:
            st.table(details[-1])
        else:
            st.info('No instrument matched that name')
