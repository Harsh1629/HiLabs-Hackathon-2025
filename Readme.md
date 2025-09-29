# HiLabs Hackathon: Intelligent Contract Classification System

### Project Overview

This solution addresses the HiLabs Hackathon challenge to build an AI-powered system that automates the review and classification of crucial clauses within healthcare provider contracts. The system processes masked contracts from two markets (TN and WA) and determines if key terms are **Standard** or **Non-Standard** based on organizational policies.

This project implements the mandatory **Three-Layer High-Level Architecture**

### 1\. Architectural Approach and Execution Strategy

Our solution is built on three modular Python files, ensuring clear separation of concerns, high maintainability, and fulfilling the modularity requirement

| Layer | Module | Core Functionality 
| :--- | :--- | :--- 
| **1. Data Processing** | `extract_clauses.py` | Handles **OCR** (for scanned PDFs) and uses **refined keywords** to find and extract the 5 required attributes from the contracts
| **2. Classification Engine** | `compare_clauses.py` | Calculates **Semantic Similarity** (TF-IDF/Cosine) and applies stringent **Business Rules** to assign the final Standard/Non-Standard classification
| **3. Reporting** | `main.py` / `dashboard.py` | Orchestrates the pipeline, generates summary metrics, and provides the interactive demo interface.

### 2\. Setup and Execution Instructions

#### A. Prerequisites (System Tools)

Due to the use of scanned PDFs, two tools must be installed on your operating system *before* Python packages:

1.  **Tesseract OCR Engine**
2.  **Poppler** (The PDF rendering utility required by `pdf2image`)

#### B. Python Environment Setup

1.  **Create and Activate Virtual Environment** (Highly Recommended).

2.  **Install Dependencies:** Save the following content as `requirements.txt` and run the installation command:

    ```bash
    # requirements.txt content
    pandas
    PyMuPDF
    pytesseract
    pdf2image
    Pillow
    scikit-learn
    streamlit
    ```

    ```bash
    pip install -r requirements.txt
    ```

3.  **Install spaCy Model:**

    ```bash
    python -m spacy download en_core_web_sm
    ```

#### C. Data Preparation

Place your contracts and templates into the root directory of the repository:

  * **`Contracts/` folder:** Place your 5 TN and 5 WA contract PDFs (`TN_Contract_1.pdf`,`WA_Contract_1.pdf`).
  * **`Standard Templates/` folder:** Place your 2 template PDFs (`TN_Standard_Template.pdf`,`WA_Standard_Template.pdf`).

#### D. Running the Solution End-to-End

1.  **Run the Backend Pipeline:** This step processes the PDFs, classifies all clauses, and generates the required JSON report and Summary Metrics.

    ```bash
    python main.py
    ```

2.  **Run the Interactive Dashboard (Demo):** This starts the Streamlit UI, allowing you to review the classification results for each of the 10 contracts

    ```bash
    streamlit run dashboard.py
    ```
### 3\. Analysis Results and Summary Metrics
The system successfully processed all 10 contracts from TN and WA, resulting in the following overall performance metrics:

Total Contracts Processed:  10

Total Clauses Classified:  50

Contracts with at least one Non-Standard Clause:  10

Classification Totals

    → Standard:  34

    → Non-Standard:  16
