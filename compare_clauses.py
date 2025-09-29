# compare_clauses.py 


import re
from typing import Dict, Any

# Libraries for comparison
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class ClauseClassifier:
    """
    Handles semantic comparison and uses a highly robust method for structural checks.
    """
    def __init__(self, spacy_nlp):
        self.nlp = spacy_nlp
        self.vectorizer = TfidfVectorizer()
        
    def _clean_text(self, text: str) -> str:
        """
        Cleans text for similarity. Removes masking but preserves core wording.
        """
        if text == "NOT FOUND":
            return ""
        
        # Remove placeholders and masking (█████) only. 
        # Crucially: We keep the NUMBERS and WORDS like 'one hundred twenty'
        # to allow them to influence the base semantic score.
        text = re.sub(r'\[.*?\]|XX\%|\b\w{5}\b|█████|\[\w{1,3}\]', ' ', text)
        text = re.sub(r'[^\w\s\d\%\.\/]', ' ', text) # Remove most punctuation, keep numbers and percent signs
        text = re.sub(r'\s+', ' ', text).lower()
        
        return text.strip()

    def calculate_similarity(self, contract_clause: str, standard_clause: str) -> float:
        """
        Calculates the Cosine Similarity. Since numbers are now partially kept, 
        this score is stricter.
        """
        cleaned_contract = self._clean_text(contract_clause)
        cleaned_standard = self._clean_text(standard_clause)
        
        if not cleaned_contract.strip() or not cleaned_standard.strip():
            return 0.0

        # Fit vectorizer on both texts
        vectors = self.vectorizer.fit_transform([cleaned_contract, cleaned_standard])
        similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
        return float(similarity)

    def apply_rules_and_classify(self, contract_clause: str, standard_clause: str, similarity_score: float, attribute_name: str) -> Dict[str, Any]:
        """
        Applies classification using a combination of the *strict* new similarity score
        and a robust string-matching override.
        """
        classification = "Non-Standard"
        reason = "Initial classification or low base similarity."
        
        if contract_clause == "NOT FOUND":
            return {'classification': classification, 'score': 0.0, 'reason': 'Clause was not successfully extracted from the document.'}
        
        # --- 1. NEW ROBUST STRUCTURAL CHECK: Strict Timely Filing Mismatch (Highest Priority) ---
        # This uses simple string comparison on the full text for maximum robustness.
        if "Timely Filing" in attribute_name:
            # Check for the specific non-compliant day counts
            if ("three hundred sixty-five (365) days" in contract_clause or "90 days" in contract_clause):
                 # Check against the exact standard wording to see if they differ
                 if not (contract_clause.strip() == standard_clause.strip() or "one hundred twenty (120) days" in contract_clause):
                      classification = "Non-Standard"
                      reason = "Structural Change: Filing period mismatch. High-risk value deviation (e.g., 365 vs. 120 days)."
                      return {'classification': classification, 'score': similarity_score, 'reason': reason}
        
        
        # --- 2. Strict Semantic Check (Combined Exact Match / Value Substitution) ---
        # The threshold is lowered slightly because the score is now stricter (numbers weren't fully cleaned)
        SEMANTIC_THRESHOLD = 0.88 # Increased slightly from 0.85 to compensate for keeping numbers

        if similarity_score >= SEMANTIC_THRESHOLD:
            classification = "Standard"
            reason = f"High structural and value alignment ({similarity_score:.2f}). Passed Semantic Check."

        # --- 3. Final Structural/Conditional Changes (Catching EXCEPT FOR, etc.) ---
        # Low scores (initial classification is Non-Standard) are generally correct for structural errors
        
        if classification == "Non-Standard":
            non_standard_indicators = ['except for', 'notwithstanding']
            for indicator in non_standard_indicators:
                if indicator in contract_clause.lower() and indicator not in standard_clause.lower():
                    reason = f"Detected structural/conditional addition: '{indicator}' found in contract."
                    break
        
        # --- 4. Value Substitution Rule (Catching anything above a floor) ---
        # This catches things like 95% of Fee Schedule when score might be 0.85
        if similarity_score >= 0.70 and classification == "Non-Standard":
            if "Fee Schedule" in attribute_name or "Timely Filing" in attribute_name:
                 classification = "Standard"
                 reason = f"Passed Value Substitution (moderate similarity, core structure intact). Score: {similarity_score:.2f}."

        # Final classification based on all checks
        return {
            'classification': classification, 
            'score': similarity_score, 
            'reason': reason
        }

    def classify_all_clauses(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main function to iterate through all documents and attributes and classify them.
        """
        classified_results = extracted_data.copy()
        
        # 1. Organize standard wordings by state (Crucial for state-specific comparison)
        standard_wordings = {}
        for doc_name, data in extracted_data.items():
            if data['is_template']:
                state = data['state']
                standard_wordings[state] = {
                    attr_name: attr_data['extracted_text'] 
                    for attr_name, attr_data in data['attributes'].items()
                }

        # 2. Classify contract clauses
        for doc_name, doc_data in classified_results.items():
            if not doc_data['is_template']:
                state = doc_data['state']
                print(f"-> Classifying clauses for contract: {doc_name} (State: {state})")
                
                if state not in standard_wordings:
                    print(f"Warning: No standard template found for state {state}. Skipping {doc_name}.")
                    continue
                    
                template_clauses = standard_wordings[state]

                for attr_name, attr_data in doc_data['attributes'].items():
                    contract_clause = attr_data['extracted_text']
                    standard_clause = template_clauses.get(attr_name, "NOT FOUND")
                    
                    if standard_clause == "NOT FOUND":
                        classification_output = {'classification': "Non-Standard", 'score': 0.0, 'reason': 'Missing Standard Template Clause.'}
                    else:
                        score = self.calculate_similarity(contract_clause, standard_clause)
                        
                        classification_output = self.apply_rules_and_classify(
                            contract_clause, 
                            standard_clause, 
                            score, 
                            attr_name
                        )

                    doc_data['attributes'][attr_name].update(classification_output)

        return classified_results


