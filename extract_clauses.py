# extract_clauses.py

import fitz # PyMuPDF (Fallback for native text extraction)
from pathlib import Path
import spacy
import re
from typing import Dict, Any

# OCR Imports
import pytesseract
from pdf2image import convert_from_path # Requires Poppler utility
from PIL import Image # Used by pdf2image/pytesseract

# --- Configuration and Setup ---
BASE_DIR = Path.cwd()
CONTRACTS_DIR = BASE_DIR / "Contracts"
TEMPLATES_DIR = BASE_DIR / "Standard Templates"

# Load the spaCy model once
try:
    NLP = spacy.load("en_core_web_sm")
except OSError:
    print("ERROR: spaCy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm'")
    exit()

# Attributes to Extract
ATTRIBUTES_TO_EXTRACT = [
    {
        # Keywords refined to ensure correct submission clause is captured
        "name": "Medicaid Timely Filing", 
        "section_context": "Submission and Adjudication of Medicaid Claims", 
        "keywords_or_phrases": ["shall submit Claims", "Claims to using appropriate", "one hundred twenty (120) days"], 
        "standard_wording": "Unless otherwise instructed, or required by Regulatory Requirements, Provider shall submit Claims to using appropriate and current Coded Service Identifier(s), within one hundred twenty (120) days from the date the Health Services are rendered or may refuse payment. If is the secondary payor, the one hundred twenty (120) day period will not begin until Provider receives notification of primary payor's responsibility."
    },
    {
        # FIX: Keywords refined to target the correct 90-day claims clause consistently
        "name": "Medicare Timely Filing", 
        "section_context": "Submission and Adjudication of Medicare Advantage Claims", 
        "keywords_or_phrases": ["shall submit Claims to", "Coded Service Identifier", "ninety (90) days from the date"], 
        "standard_wording": "Unless otherwise instructed in the provider manual(s) or Policies applicable to Medicare Advantage Program, or unless required by Regulatory Requirements, Provider shall submit Claims to using appropriate and current Coded Service Identifier(s), within ninety (90) days from the date the Health Services are rendered or will refuse payment. If is the secondary payor, the ninety (90) day period will not begin until Provider receives notification of primary payor's responsibility."
    },
    {
        "name": "No Steerage/SOC", 
        "section_context": "Networks and Provider Panels", 
        "keywords_or_phrases": ["eligible to participate only in those Networks", "Participating Provider", "discontinue, or modify new or existing Networks"], 
        "standard_wording": "Provider shall be eligible to participate only in those Networks designated on the Provider Networks Attachment of this Agreement. Provider shall not be recognized as a Participating Provider in such Networks until the later of: 1) the Effective Date of this Agreement or; 2) as determined by in its sole discretion, the date Provider has met applicable credentialing requirements and accreditation requirements. Provider acknowledges that may develop,discontinue, or modify new or existing Networks, products and/or programs. In addition to those Networks designated on the Provider Networks Attachment, may also identify Provider as a Participating Provider in additional Networks, products and/or programs designated in writing from time to time by The terms and conditions of Provider's participation as a Participating Provider in such additional Networks, products and/or programs shall be on the terms and conditions as set forth in thisAgreement unless otherwise agreed to in writing by Provider and"
    },
    {
        "name": "Medicaid Fee Schedule", 
        "section_context": "Specific Reimbursement Terms", 
        "keywords_or_phrases": ["total reimbursement amount", "one hundred percent (100%)", "Fee Schedule A"], 
        "standard_wording": "For purposes of determining the █████ Rate, the total reimbursement amount that Provider and █████ have agreed upon for the applicable provider type(s) for Covered Services provided under this Agreement shall be one hundred percent (100%) of the █████ Professional Provider Market Master Fee Schedule A in effect on the date of service."
    },
    {
        "name": "Medicare Fee Schedule", 
        "section_context": "Specific Reimbursement Terms", 
        "keywords_or_phrases": ["Covered Services furnished", "Medicare Advantage Network", "lesser of Eligible Charges or the Medicare Advantage Rate"], 
        "standard_wording": "For Covered Services furnished by or on behalf of Provider for a Member enrolled in a Medicare Advantage Network, Provider agrees to accept an amount that is the lesser of Eligible Charges or the Medicare Advantage Rate, minus applicable Cost Shares, and modified before payment as described below. Provider agrees that this amount, plus applicable Cost Shares, is full compensation for Covered Services."
    }
]

# --- Core Utility Functions ---

def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extracts text from a single PDF file, prioritizing OCR (Tesseract) for scanned documents,
    with a fallback to PyMuPDF for native text extraction.
    """
    text = ""
    print(f"   -> Starting OCR/Extraction attempt for {pdf_path.name}...")
    
    # 1. OCR Attempt (Best for scanned/image-based PDFs)
    try:
        images = convert_from_path(pdf_path)
        for image in images:
            page_text = pytesseract.image_to_string(image) 
            text += page_text + " "
        
        if text.strip():
            print(f"   -> OCR Success.")
            return re.sub(r'\s+', ' ', text).strip()
        
    except pytesseract.TesseractNotFoundError:
        print("\nFATAL ERROR: Tesseract is not installed or not in your PATH. Trying PyMuPDF fallback.")
    except Exception as e:
        print(f"\nOCR ERROR ({type(e).__name__}): Trying PyMuPDF fallback. Ensure Poppler is installed.")
    
    # 2. Fallback to PyMuPDF (Best for native/searchable PDFs)
    try:
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        if text.strip():
            print("   -> PyMuPDF Fallback Success.")
            return re.sub(r'\s+', ' ', text).strip()
    except Exception as e:
        print(f"Error reading PDF {pdf_path.name} with PyMuPDF: {e}")
        return ""
    
    return ""


def process_documents(directory: Path) -> Dict[str, str]:
    """Processes all PDF and text files in a given directory."""
    all_document_texts = {}
    
    for file_path in directory.glob("*.pdf"):
        doc_text = extract_text_from_pdf(file_path)
        if doc_text:
            all_document_texts[file_path.stem] = doc_text
            
    for file_path in directory.glob("*.txt"):
        print(f"-> Reading Text: {file_path.name}")
        try:
            doc_text = file_path.read_text(encoding='utf-8')
            all_document_texts[file_path.stem] = re.sub(r'\s+', ' ', doc_text).strip()
        except Exception as e:
            print(f"Error reading TXT {file_path.name}: {e}")

    return all_document_texts

def extract_clauses_for_attributes(document_texts: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
    """
    Implements the core Clause Extraction logic using spaCy for sentence segmentation
    and regex for keyword matching.
    """
    extracted_data = {}
    
    for doc_name, full_text in document_texts.items():
        doc_data = {
            'state': doc_name.split('_')[0], 
            'is_template': 'Template' in doc_name, 
            'attributes': {}
        }
        
        # Use spaCy for reliable sentence segmentation
        doc = NLP(full_text)
        sentences = [sent.text.strip() for sent in doc.sents]
        
        for attr in ATTRIBUTES_TO_EXTRACT:
            attribute_name = attr['name']
            
            # Create a regex pattern to find any of the keywords
            keywords = [re.escape(k) for k in attr['keywords_or_phrases']]
            combined_pattern = f"({'|'.join(keywords)})"
            
            found_clause = "NOT FOUND"
            
            # Search for the first sentence containing the core keywords
            for sentence in sentences:
                if re.search(combined_pattern, sentence, re.IGNORECASE):
                    found_clause = sentence
                    break # Stop at the first relevant sentence/clause
                    
            doc_data['attributes'][attribute_name] = {
                'extracted_text': found_clause,
                'standard_wording': attr['standard_wording'] 
            }

        extracted_data[doc_name] = doc_data

    return extracted_data