import streamlit as st
import pandas as pd
from backend.outcome_repo_agent import MeasurementInstrumentAgent

@st.cache_resource
def load_agent(path):
    agent = MeasurementInstrumentAgent(path, sheet_name='Measurement Instruments')
    return agent

st.set_page_config(page_title='Outcome Repo Agent', layout='wide')
st.title('Outcome Repository — Measurement Instrument Assistant')

EXCEL_PATH = '/Users/cyrus_lsl/Documents/HKJC/Outcome Repo Agent/measurement_instruments.xlsx'
agent = load_agent(EXCEL_PATH)

st.sidebar.header('Actions')
if st.sidebar.button('Download parsed table (CSV)'):
    csv = agent.df.to_csv(index=False)
    st.sidebar.download_button('Download CSV', csv, file_name='instruments_parsed.csv')

query = st.text_input('Enter your enquiry or keywords', '')

col1, col2 = st.columns([2, 1])
with col1:
    if st.button('Search') and query.strip():
        results = agent.process_query(query)
        if isinstance(results, str):
            st.warning(results)
        else:
            st.markdown(agent.format_response(results))

    st.markdown('---')
    st.subheader('Browse instruments table')
    st.dataframe(agent.df)

with col2:
    st.subheader('Quick actions')
    if st.button('List top 20 instruments'):
        st.write(agent.df[['Measurement Instrument', 'Acronym']].head(20))

    name = st.text_input('Get details for instrument (name contains)', '')
    if st.button('Get Details') and name.strip():
        details = agent.get_instrument_details(name)
        if details:
            st.json(details)
        else:
            st.info('No instrument matched that name')
