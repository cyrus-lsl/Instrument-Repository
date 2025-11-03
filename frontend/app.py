import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to Python path so we can import backend
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from backend.outcome_repo_agent import MeasurementInstrumentAgent

@st.cache_resource
def load_agent(path):
    agent = MeasurementInstrumentAgent(path, sheet_name='Measurement Instruments')
    return agent

st.set_page_config(page_title='Outcome Repo Agent', layout='wide')
st.title('Outcome Repository — Measurement Instrument Assistant')

# Initialize session state for chat history if it doesn't exist
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

EXCEL_PATH = '/Users/cyrus_lsl/Documents/HKJC/Outcome Repo Agent/measurement_instruments.xlsx'
agent = load_agent(EXCEL_PATH)

# Sidebar with download option and example queries
st.sidebar.header('Actions & Help')
if st.sidebar.button('Download parsed table (CSV)'):
    csv = agent.df.to_csv(index=False)
    st.sidebar.download_button('Download CSV', csv, file_name='instruments_parsed.csv')

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
        st.session_state.chat_history.append({"role": "user", "content": query})
        results = agent.process_query(query)
        st.session_state.chat_history.append(
            {"role": "assistant", "content": agent.format_response(results)}
        )

# Main chat interface
st.header("Ask about measurement instruments")
st.markdown("""
Type your query about measurement instruments. Examples:
- Search by purpose: "assessment tools for depression"
- Search by group: "instruments for elderly patients"
- Search by properties: "quick screening tools" or "validated in Hong Kong"
""")

# Chat input at the bottom
query = st.text_input('Enter your enquiry', key='user_input')

# Add send button
if st.button('Send', key='send_button') and query.strip():
    # Add user message to chat
    st.session_state.chat_history.append({"role": "user", "content": query})
    
    # Get agent response
    results = agent.process_query(query)
    response = agent.format_response(results)
    
    # Add assistant response to chat
    st.session_state.chat_history.append({"role": "assistant", "content": response})

# Display chat history
st.header("Conversation History")
for message in st.session_state.chat_history:
    if message["role"] == "user":
        st.markdown(f"**You:** {message['content']}")
    else:
        st.markdown(f"**Assistant:** {message['content']}")
    st.markdown("---")

# Collapsible data explorer
with st.expander("Browse all instruments"):
    # Convert potentially mixed-type columns to string to avoid pyarrow conversion
    df_display = agent.df.copy()
    if 'No. of Questions / Statements' in df_display.columns:
        df_display['No. of Questions / Statements'] = df_display['No. of Questions / Statements'].astype(str)
    # Ensure all columns are arrow-compatible by casting object columns to string
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
