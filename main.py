# main.py

from pathlib import Path
import json
from collections import defaultdict
from typing import Dict, Any

# Import logic and shared resources from helper modules
from extract_clauses import (
    process_documents, 
    extract_clauses_for_attributes, 
    NLP, 
    CONTRACTS_DIR, 
    TEMPLATES_DIR
)
from compare_clauses import ClauseClassifier


# --- Reporting Functions (Documentation & Reporting Layer) ---

def calculate_summary_metrics(classified_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates the required summary metrics.
    """
    total_clauses_by_category = defaultdict(int)
    contracts_with_non_standard = set()
    total_contracts = 0
    
    for doc_name, data in classified_results.items():
        if not data['is_template']:
            total_contracts += 1
            has_non_standard = False
            
            for attr_name, attr_data in data['attributes'].items():
                classification = attr_data.get('classification', 'Non-Standard') 
                total_clauses_by_category[classification] += 1
                
                if classification == 'Non-Standard':
                    has_non_standard = True

            if has_non_standard:
                contracts_with_non_standard.add(doc_name)

    return {
        "Total Contracts Processed": total_contracts,
        "Total Clauses Classified": sum(total_clauses_by_category.values()),
        "Classification Totals": dict(total_clauses_by_category),
        "Contracts with at least one Non-Standard Clause": len(contracts_with_non_standard),
        "List of Non-Standard Contracts": sorted(list(contracts_with_non_standard))
    }

def generate_report(classified_results: Dict[str, Any], summary_metrics: Dict[str, Any]):
    """
    Outputs the final summary and saves the detailed classification results.
    """
    print("\n" + "="*70)
    print("=== FINAL CONTRACT CLASSIFICATION REPORT ===")
    print("="*70)
    
    # Print Summary Metrics
    print("\n[SUMMARY METRICS]")
    for key, value in summary_metrics.items():
        if isinstance(value, dict):
            print(f"  - {key}:")
            for sub_key, sub_value in value.items():
                 print(f"    -> {sub_key}: {sub_value}")
        elif isinstance(value, list):
            print(f"  - {key}: {len(value)} items")
        else:
            print(f"  - {key}: {value}")

    # Save detailed results to JSON
    output_path = Path.cwd() / "classification_results.json"
    with open(output_path, 'w') as f:
        json.dump(classified_results, f, indent=4)
    print(f"\n[DETAILED RESULTS SAVED] \nAll classification details saved to: {output_path}")

   


# --- Main Pipeline Execution ---

def run_pipeline():
    """
    Orchestrates the entire contract analysis pipeline.
    """
    print("--- 1. Data Processing Layer (Extraction) ---")
    
    # Initial Data Checks
    if not CONTRACTS_DIR.exists() or not TEMPLATES_DIR.exists():
        print("\nERROR: Please ensure 'Contracts' and 'Standard Templates' folders exist.")
        return
        
    # 1. Extract Text
    contract_texts = process_documents(CONTRACTS_DIR)
    template_texts = process_documents(TEMPLATES_DIR)
    all_texts = {**contract_texts, **template_texts}
    
    if not all_texts:
         print("\nERROR: No documents found. Extraction failed.")
         return

    # 2. Extract the 5 Key Clauses
    extracted_clauses = extract_clauses_for_attributes(all_texts)


    print("\n--- 2. Classification Engine (Comparison) ---")
    
    # 3. Initialize Classifier and Run Classification
    classifier = ClauseClassifier(spacy_nlp=NLP)
    classified_results = classifier.classify_all_clauses(extracted_clauses)
    
    
    print("\n--- 3. Documentation & Reporting ---")

    # 4. Calculate Summary Metrics and Generate Report
    summary_metrics = calculate_summary_metrics(classified_results)
    generate_report(classified_results, summary_metrics)

# Run the pipeline
if __name__ == "__main__":
    run_pipeline()