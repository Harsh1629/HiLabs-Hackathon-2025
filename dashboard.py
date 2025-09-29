# dashboard.py

import streamlit as st
import pandas as pd
import json
from pathlib import Path

# --- Configuration ---
RESULTS_PATH = Path.cwd() / "classification_results.json"

def load_data():
    """Loads the final classification results from the JSON file."""
    if not RESULTS_PATH.exists():
        st.error("Error: classification_results.json file not found. Please run 'python main.py' first!")
        return None
    
    try:
        with open(RESULTS_PATH, 'r') as f:
            data = json.load(f)
        return data
    except Exception as e:
        st.error(f"Error loading JSON data: {e}")
        return None

def main():
    """Main function for the Streamlit Dashboard."""
    st.set_page_config(layout="wide", page_title="Contract Classification Dashboard")
    st.title("HiLabs Contract Negotiation Assist")
    st.subheader("Clause Classification and Risk Review")

    full_results = load_data()

    if full_results is None:
        return

    # Filter out the template documents, we only want to display contracts
    contract_keys = [k for k, v in full_results.items() if not v.get('is_template', True)]
    
    # --- Check for No Contracts ---
    if not contract_keys:
        st.warning("No contract results found in the JSON file. Ensure you have contracts in the 'Contracts' folder.")
        return

    # --- 1. Contract Selection Dropdown (st.selectbox) ---
    selected_contract_name = st.selectbox(
        "Select Contract to Review:",
        options=contract_keys,
        index=0,
        help="Choose any of the processed contracts to see its classified clauses."
    )

    if selected_contract_name:
        st.markdown("---")
        contract_data = full_results[selected_contract_name]
        
        # --- 2. Display Summary and Metrics ---
        st.header(f"Reviewing: {selected_contract_name} (State: {contract_data['state']})")
        
        attributes_data = contract_data['attributes']
        
        # Prepare data for a clean Streamlit DataFrame display
        df_rows = []
        for attr_name, attr_info in attributes_data.items():
            # Use color/emoji coding for visual clarity
            risk_flag = "❌ NON-STANDARD"
            if attr_info['classification'] == 'Standard':
                risk_flag = "✅ STANDARD"

            # Truncate text for easier viewing in the table
            extracted_snippet = attr_info['extracted_text']
            if extracted_snippet != "NOT FOUND":
                 extracted_snippet = extracted_snippet[:120].replace('\n', ' ') + "..."

            df_rows.append({
                "Attribute Name": attr_name,
                "Classification": risk_flag,
                "Semantic Score": f"{attr_info['score']:.4f}",
                "Key Deviation Reason": attr_info['reason'],
                "Extracted Clause (Snippet)": extracted_snippet,
            })

        df = pd.DataFrame(df_rows)

        # --- 3. Display Interactive Table ---
        st.markdown("### Clause-by-Clause Classification Results")
        
        # Use st.data_editor to display the table interactively
        st.data_editor(
            df,
            column_config={
                "Classification": st.column_config.Column(
                    "Classification",
                    help="Final result: Standard or Non-Standard",
                    width="small"
                ),
                "Extracted Clause (Snippet)": st.column_config.Column(
                    "Extracted Clause",
                    width="large"
                )
            },
            hide_index=True
        )

        st.markdown("---")
        # Optional: Display the full JSON data structure for debugging
        with st.expander("View Full Raw JSON Data for Selected Contract (For Debugging)"):
            st.json(contract_data, expanded=False)


if __name__ == "__main__":
    main()