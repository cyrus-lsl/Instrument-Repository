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

# Prefer an environment variable (useful for deployments). If not set, fall
# back to a repo-relative file named `measurement_instruments.xlsx` at the
# repository root. Finally, fall back to an uploader so demos still work.
EXCEL_PATH_ENV = os.environ.get('EXCEL_PATH')
if EXCEL_PATH_ENV:
    excel_path = Path(EXCEL_PATH_ENV)
else:
    excel_path = Path(__file__).resolve().parents[1] / "measurement_instruments.xlsx"

# Try to load the default file if it exists, otherwise prompt user to upload
agent = None
if excel_path.exists():
    try:
        agent = load_agent(str(excel_path))
    except Exception as e:
        st.error(f"Failed to load default data file: {e}")
else:
    st.warning(f"Default Excel file not found at {excel_path}. Please upload an Excel file or set the EXCEL_PATH environment variable.")

# Allow user to upload an excel file when the default path is not available
uploaded_file = st.file_uploader("Upload measurement instruments Excel", type=['xls', 'xlsx'])
if uploaded_file is not None:
    try:
        agent = load_agent(uploaded_file)
    except Exception as e:
        st.error(f"Failed to load uploaded file: {e}")

# Sidebar: download option and example queries
st.sidebar.header('Actions & Help')
if agent:
    if st.sidebar.button('Download parsed table (CSV)'):
        csv = agent.df.to_csv(index=False)
        st.sidebar.download_button('Download CSV', csv, file_name='instruments_parsed.csv')
else:
    st.sidebar.info('Upload or provide a valid Excel file to enable downloads and queries.')

st.sidebar.header('Example queries')
example_queries = [
    "physical function assessment for elderly",
    "quick depression screening tools",
    "cognitive assessment validated in Hong Kong",
    "free assessment tools for children",
]
if st.sidebar.button("Show example queries"):
    query = st.sidebar.radio(
        "Select a query to try:",
        example_queries
    )
    if st.sidebar.button("Use this query"):
        if not agent:
            st.sidebar.info('Please upload or provide the Excel file before running queries.')
        else:
            st.session_state.chat_history.append({"role": "user", "content": query})
            results = agent.process_query(query)
            st.session_state.chat_history.append(
                {"role": "assistant", "content": agent.format_response(results)}
            )

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
        

# Show chat history
st.header("Conversation History")
for message in st.session_state.chat_history:
    if message["role"] == "user":
        st.markdown(f"**You:** {message['content']}")
    else:
        st.markdown(f"**Assistant:** {message['content']}")
    st.markdown("---")

# Collapsible data explorer
with st.expander("Browse all instruments"):
    if not agent:
        st.info('No data loaded. Upload an Excel file to browse instruments.')
    else:
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
                st.json(details)
            else:
                st.info('No instrument matched that name')
