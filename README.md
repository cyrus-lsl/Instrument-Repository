Outcome Repo Agent

Quick start

1. Create a Python environment (recommended):

   python3 -m venv .venv
   source .venv/bin/activate

2. Install dependencies:

   pip install -r requirements.txt

3. Run the Streamlit UI (web):

   streamlit run frontend/app.py

4. Or run the CLI interactive mode:

   python run_agent_cli.py /path/to/measurement_instruments.xlsx --sheet "Measurement Instruments"

Notes

- The agent expects a sheet named "Measurement Instruments" by default. If your workbook has a different sheet name or header row, pass the `--sheet` option or modify the call in `backend/outcome_repo_agent.py`.
- The script includes fuzzy matching and header/table auto-detection to handle messy Excel exports.
